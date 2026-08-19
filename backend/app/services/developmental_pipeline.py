"""
Developmental pipeline orchestrator - the actual wiring of steps 2-5 into
live routes (docs/MIGRATION_MAP.md).

Runs the full Exposure -> Narration -> Evidence -> Interpretation -> Pattern
chain for one piece of developmental text (a persona's backstory, or a
single experience description) and persists everything. Both
personas.py::create_persona and experiences.py::add_experience call
process_developmental_text() - the orchestration is identical in shape for
either source, just different context (source="backstory" vs "experience",
source_event_id=None vs the new Experience's id).

Does not commit - the caller controls the transaction, consistent with
every other write path in these routes.

Deliberately does NOT write to the legacy Experience.immediate_effects/
symptoms_developed/etc fields - that remains app/services/psychology_
engine.py's job for now. Retiring that engine and its response-shape
contract (which the frontend renders directly) is a separate, larger
decision than "wire the new engines in" - see docs/MIGRATION_MAP.md's note
on this (Step 11d, not yet done).

What this function DOES own: Persona.current_trauma_markers (sourced
exclusively from evidence_accumulator.project_current_trauma_markers()),
Persona.current_state (Step 11, State tier - applied every call this
produces a meaningful proposal), and, GATED, Persona.current_personality
(Step 11, Trait tier - only moves when this event's adaptation_strategy has
reached AdaptationPattern.status == "established"; see state_trait_engine.
trait_gate_open). Nothing else should assign to current_trauma_markers.
current_personality is, for now, STILL also written unconditionally by
psychology_engine.analyze_experience() inside experiences.py::add_experience
for every experience (that call happens before this pipeline runs, in the
route, not in this function) - this is the known, previously-flagged
transitional state, not a bug: until Step 11d retires that call, Trait
movement on the experience path is driven by both the old ungated engine
and this new gated one in the same request. On the backstory/persona-
creation path (personas.py::create_persona), this function is the ONLY
thing that touches current_personality after the one-time foundational
baseline is set at creation - that path is already clean.
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models import (
    DevelopmentalExposure, ProtectiveFactor, NarrationRecord,
    FunctionalObservation, ClinicalPatternHypothesis, AdaptationPattern, Interpretation,
)
from app.services.developmental_exposure_engine import (
    extract_developmental_exposures_async, build_exposure_and_protective_rows,
)
from app.services.self_narration_engine import analyze_narration_async, build_narration_record
from app.services.evidence_accumulator import (
    accumulate_evidence, upsert_clinical_pattern_hypothesis_rows, project_current_trauma_markers,
)
from app.services.pattern_engine import (
    interpret_experience_async, build_interpretation_row, accumulate_patterns, upsert_adaptation_pattern_rows,
)
from app.services.state_trait_engine import (
    propose_state_trait_implications_async, apply_state_update, apply_trait_update, trait_gate_open,
)


def _exposure_dict(e: DevelopmentalExposure) -> Dict:
    return {
        "id": e.id, "exposure_type": e.exposure_type, "developmental_domains": e.developmental_domains,
        "age_at_exposure": e.age_at_exposure, "source": e.source, "source_event_id": e.source_event_id,
    }


def _protective_dict(p: ProtectiveFactor) -> Dict:
    return {"id": p.id, "factor_type": p.factor_type, "domains_buffered": p.domains_buffered, "active_from_age": p.active_from_age}


def _narration_dict(n: NarrationRecord) -> Dict:
    # NarrationRecord doesn't track an age directly (it's tied to source_event_id,
    # not a standalone age column) - evidence_accumulator's narrative-evidence
    # entries just carry age=None here, which is a display-only field on those entries.
    return {"id": n.id, "attributed_to_persona": n.attributed_to_persona, "linguistic_signals": n.linguistic_signals, "age": None}


def _functional_dict(f: FunctionalObservation) -> Dict:
    return {
        "id": f.id, "valence": f.valence, "observation_type": f.observation_type,
        "description": f.description, "developmental_domains": f.developmental_domains,
        "candidate_pattern_keys": f.candidate_pattern_keys, "age_observed": f.age_observed,
    }


async def process_developmental_text(
    db: Session,
    persona,
    text: str,
    source: str,
    age: int,
    source_event_id: Optional[str] = None,
    speaker_role: str = "case_author",
) -> Dict:
    """
    Args:
        db: active session; caller commits
        persona: the Persona ORM row (already added/flushed, has an id)
        text: backstory text or a single experience description
        source: "backstory" | "experience"
        age: age this text describes (baseline_age for backstory, age_at_event for an experience)
        source_event_id: Experience.id if source == "experience", else None
        speaker_role: who wrote this text - "case_author" for the current UI (both the
            backstory field and experience descriptions are case-authored, not the
            persona's own first-person voice - see docs/MIGRATION_MAP.md's Evidence &
            Source Model). Self-narration analysis is gated to "persona_voice" and
            will correctly stay dormant with the current UI's default.

    Returns:
        {"exposures": [...], "protective_factors": [...], "trauma_markers": [...],
         "interpretation": Interpretation | None, "state_changes": {...}, "trait_changes": {...},
         "clinical_pattern_hypotheses": {pattern_key: {evidence_strength, status, tier, ...}}}
        state_changes/trait_changes are the proposal actually applied this call
        (trait_changes is {} whenever the trait gate was closed, even if the
        engine proposed something - see state_trait_engine.trait_gate_open).
        clinical_pattern_hypotheses is accumulate_evidence()'s full output
        (already computed in step 3, not re-queried) - exposed so callers
        like legacy_experience_adapter.py (Step 11d) can build a display
        value from real evidence_strength without a second DB round trip.
    """
    # 1. Exposure extraction (step 2)
    extraction = await extract_developmental_exposures_async(text)
    exposure_rows, protective_rows = build_exposure_and_protective_rows(
        persona.id, extraction, source=source, source_event_id=source_event_id,
        age_at_exposure=age, speaker_role=speaker_role,
    )
    for row in exposure_rows:
        db.add(row)
    for row in protective_rows:
        db.add(row)
    db.flush()

    # 2. Self-narration (step 3) - gated internally to speaker_role == "persona_voice";
    # a case_author call correctly produces an empty, skipped result. Still recorded
    # for provenance either way.
    narration_analysis = await analyze_narration_async(text, persona.name, speaker_role)
    narration_row = build_narration_record(
        persona.id, text, speaker_role, narration_analysis, source_event_id=source_event_id,
    )
    db.add(narration_row)
    db.flush()

    # 3. Evidence accumulation (step 4) - recomputed from the persona's COMPLETE
    # timeline every call, not just this batch, per accumulate_evidence's own
    # recompute-from-scratch philosophy.
    all_exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
    all_protective = db.query(ProtectiveFactor).filter(ProtectiveFactor.persona_id == persona.id).all()
    all_narration = db.query(NarrationRecord).filter(NarrationRecord.subject_id == persona.id).all()
    all_functional = db.query(FunctionalObservation).filter(FunctionalObservation.persona_id == persona.id).all()

    exposure_dicts_all = [_exposure_dict(e) for e in all_exposures]
    protective_dicts_all = [_protective_dict(p) for p in all_protective]
    narration_dicts_all = [_narration_dict(n) for n in all_narration]
    functional_dicts_all = [_functional_dict(f) for f in all_functional]

    existing_status = {
        h.pattern_key: h.status
        for h in db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
    }
    accumulated_evidence = accumulate_evidence(
        exposure_dicts_all, protective_dicts_all, narration_dicts_all, functional_dicts_all,
        existing_status=existing_status,
    )
    upsert_clinical_pattern_hypothesis_rows(db, persona.id, accumulated_evidence)
    db.flush()

    # 4. Interpretation (step 5) - only for exposures extracted from THIS text,
    # not the whole timeline; one interpretation per meaningful input, matching
    # "every meaningfully analyzed event" from the product spec.
    interpretation_row = None
    this_batch_exposures = [_exposure_dict(e) for e in exposure_rows]
    if this_batch_exposures:
        prior_patterns = [
            {"pattern_name": p.pattern_name, "adaptation_strategy": p.adaptation_strategy}
            for p in db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        ]
        narration_signals_this = narration_analysis.get("linguistic_signals") or []
        interpretation_result = await interpret_experience_async(
            persona.name, age, this_batch_exposures,
            narration_signals=narration_signals_this,
            protective_factors=protective_dicts_all,
            prior_patterns=prior_patterns,
        )
        interpretation_row = build_interpretation_row(
            persona.id, interpretation_result,
            exposure_ids=[e["id"] for e in this_batch_exposures],
            protective_factor_ids=[p["id"] for p in protective_dicts_all],
            source_event_id=source_event_id,
            age_at_event=age,
        )
        db.add(interpretation_row)
        db.flush()

    # 5. Pattern accumulation (step 5) - recomputed from ALL of the persona's
    # interpretations, same recompute-from-scratch philosophy as step 4.
    all_interpretations = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).all()
    interpretation_dicts = [
        {
            "id": i.id, "source_event_id": i.source_event_id, "age_at_event": i.age_at_event,
            "adaptation_strategy": i.adaptation_strategy, "belief_statement": i.belief_statement,
            "developmental_domains": i.developmental_domains,
        }
        for i in all_interpretations
    ]
    accumulated_patterns = accumulate_patterns(interpretation_dicts, protective_dicts_all, functional_dicts_all)
    await upsert_adaptation_pattern_rows(db, persona.id, accumulated_patterns, persona_name=persona.name)
    db.flush()

    # 6. State/Trait proposal + apply (Step 11) - only runs when this batch
    # actually produced an interpretation. Uses THIS interpretation's own
    # adaptation_strategy's freshly-recomputed pattern status (from step 5,
    # above) as the trait gate - so a strategy that just crossed into
    # "established" on this very call is correctly eligible, not one call
    # behind.
    state_changes: Dict = {}
    trait_changes: Dict = {}
    if interpretation_row is not None:
        strategy = interpretation_row.adaptation_strategy
        pattern_state = accumulated_patterns.get(strategy) if strategy else None
        pattern_status = pattern_state.get("status") if pattern_state else None

        proposal = await propose_state_trait_implications_async(
            persona.name, age,
            {
                "belief_statement": interpretation_row.belief_statement,
                "adaptation_strategy": strategy,
                "reasoning": interpretation_row.reasoning,
            },
            pattern_status=pattern_status,
        )
        state_changes = proposal.get("state_changes", {})
        trait_changes = proposal.get("trait_changes", {})

        interpretation_row.state_implications = state_changes or None
        interpretation_row.trait_implications = trait_changes or None

        persona.current_state = apply_state_update(persona.current_state, state_changes)
        persona.current_personality = apply_trait_update(
            persona.current_personality, trait_changes, gate_open=trait_gate_open(pattern_state)
        )
        db.flush()

    # 7. Project the display list - the single writer to current_trauma_markers.
    trauma_markers = project_current_trauma_markers(accumulated_evidence)

    return {
        "exposures": this_batch_exposures,
        "protective_factors": [_protective_dict(p) for p in protective_rows],
        "trauma_markers": trauma_markers,
        "interpretation": interpretation_row,
        "state_changes": state_changes,
        "trait_changes": trait_changes,
        "clinical_pattern_hypotheses": accumulated_evidence,
    }
