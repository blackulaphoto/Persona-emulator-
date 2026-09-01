"""
Scoped, transactional repair for already-persisted canonical evidence rows
whose provenance predates the caregiver-context and undated-background
grounding fixes (see app/services/developmental_exposure_engine.py's
requires_caregiver_context and app/services/canonical_provenance.py).

This does NOT touch every persona in the database. It targets exactly the
persona(s) you name, re-runs the current (corrected, deterministic) taxonomy
matcher against that persona's own raw stored text - the baseline_background
and every real Experience.user_description - and reports where the
currently-persisted DevelopmentalExposure/ProtectiveFactor rows for a given
source no longer match what the corrected matcher would produce for that
same text today.

Dry run by default. Nothing is written unless you pass --apply. Even with
--apply, everything happens inside one transaction per persona: either the
whole repair for that persona commits, or none of it does.

What --apply actually does, per persona:
  1. For each source (the backstory, or one specific Experience) whose
     current DevelopmentalExposure/ProtectiveFactor set no longer matches a
     fresh deterministic extraction of that exact text:
       - delete the stale DevelopmentalExposure/ProtectiveFactor rows for
         that source
       - delete any Interpretation row for that same source (its
         belief/adaptation/reasoning was built from the now-removed
         evidence and is no longer grounded)
  2. Call app.services.timeline_replay.rebuild_persona_from_timeline(), the
     same deterministic "recompute everything from the persisted timeline"
     function every other part of this codebase already trusts, so
     patterns, hypotheses, current_state, current_personality, attachment,
     and current_trauma_markers are all re-derived from the corrected
     remaining evidence - not hand-patched.

Deliberately does NOT call any AI to regenerate a fresh interpretation for
a source whose evidence was removed - that would be non-deterministic and
this repair's job is narrowly to remove ungrounded evidence, not to
reinterpret an event from scratch. An affected experience will correctly
show "not yet analyzed"-equivalent status afterward unless the corrected
extractor found something else in the same text - exactly what a fresh
add of that same experience text would produce today.

Usage:
    # Dry run - report what's stale, change nothing:
    python scripts/repair_canonical_grounding.py --persona-id <id>

    # Apply the repair for real, inside one transaction:
    python scripts/repair_canonical_grounding.py --persona-id <id> --apply

    # Multiple personas in one run (each gets its own transaction):
    python scripts/repair_canonical_grounding.py --persona-id <id1> --persona-id <id2> --apply
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    DevelopmentalExposure, Experience, Interpretation, Persona, ProtectiveFactor,
)
from app.services.developmental_exposure_engine import extract_developmental_exposures_async
from app.services.timeline_replay import rebuild_persona_from_timeline


def _persisted_sets(db: Session, persona_id: str, source_event_id: str | None) -> tuple[set, set]:
    exposures = db.query(DevelopmentalExposure).filter_by(
        persona_id=persona_id, source_event_id=source_event_id,
    ).all()
    protective = db.query(ProtectiveFactor).filter_by(
        persona_id=persona_id, source_event_id=source_event_id,
    ).all()
    return {e.exposure_type for e in exposures}, {p.factor_type for p in protective}


async def _fresh_sets(text: str) -> tuple[set, set]:
    extraction = await extract_developmental_exposures_async(text)
    return (
        {item["exposure_type"] for item in extraction.get("exposures", [])},
        {item["factor_type"] for item in extraction.get("protective_factors", [])},
    )


def _delete_source(db: Session, persona_id: str, source_event_id: str | None) -> None:
    db.query(DevelopmentalExposure).filter_by(persona_id=persona_id, source_event_id=source_event_id).delete()
    db.query(ProtectiveFactor).filter_by(persona_id=persona_id, source_event_id=source_event_id).delete()
    db.query(Interpretation).filter_by(persona_id=persona_id, source_event_id=source_event_id).delete()


async def check_persona(db: Session, persona: Persona, apply: bool) -> list[str]:
    """Returns a list of human-readable report lines for this persona."""
    lines: list[str] = []
    sources: list[tuple[str | None, str, str]] = []  # (source_event_id, text, label)

    if persona.baseline_background:
        sources.append((None, persona.baseline_background, "backstory"))
    experiences = db.query(Experience).filter_by(persona_id=persona.id).order_by(Experience.age_at_event).all()
    for exp in experiences:
        sources.append((exp.id, exp.user_description, f"experience age {exp.age_at_event} ({exp.id})"))

    stale_sources: list[str | None] = []
    for source_event_id, text, label in sources:
        persisted_exposures, persisted_protective = _persisted_sets(db, persona.id, source_event_id)
        if not persisted_exposures and not persisted_protective:
            continue  # nothing recorded for this source - nothing to repair
        fresh_exposures, fresh_protective = await _fresh_sets(text)
        if persisted_exposures != fresh_exposures or persisted_protective != fresh_protective:
            stale_sources.append(source_event_id)
            lines.append(f"  STALE - {label}")
            lines.append(f"    text: {text[:120]!r}")
            lines.append(f"    persisted exposures={sorted(persisted_exposures)} protective={sorted(persisted_protective)}")
            lines.append(f"    corrected  exposures={sorted(fresh_exposures)} protective={sorted(fresh_protective)}")

    if not stale_sources:
        lines.insert(0, f"Persona {persona.id} ({persona.name}): no stale canonical evidence found - nothing to repair.")
        return lines

    lines.insert(0, f"Persona {persona.id} ({persona.name}): {len(stale_sources)} source(s) with stale canonical evidence.")

    if apply:
        for source_event_id in stale_sources:
            _delete_source(db, persona.id, source_event_id)
        db.flush()
        rebuild_persona_from_timeline(db, persona.id)
        db.commit()
        lines.append("  APPLIED - stale rows removed, persona rebuilt from corrected timeline, committed.")
    else:
        lines.append("  DRY RUN - no changes made. Re-run with --apply to fix.")
        db.rollback()

    return lines


async def main(persona_ids: list[str], apply: bool) -> int:
    db = SessionLocal()
    exit_code = 0
    try:
        for persona_id in persona_ids:
            persona = db.query(Persona).filter(Persona.id == persona_id).first()
            if persona is None:
                print(f"Persona {persona_id}: NOT FOUND - skipped.")
                exit_code = 1
                continue
            for line in await check_persona(db, persona, apply):
                print(line)
            print()
    finally:
        db.close()
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--persona-id", action="append", required=True, dest="persona_ids",
                        help="Persona ID to check/repair. Repeatable.")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write the repair. Without this, dry-run only.")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.persona_ids, args.apply)))
