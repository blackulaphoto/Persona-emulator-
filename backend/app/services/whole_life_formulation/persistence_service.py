"""
Analyze Life V2 - the atomic persistence orchestrator. PERSISTENCE PHASE.

    assemble factual input
        -> model call
        -> parse                              (formulation_service.py)
        -> validate/enforce                   (enforcement.py)
        -> create formulation/version
        -> reconcile projections               (projections.py)
        -> rewrite snapshots                   (snapshots.py)
        -> update Persona current state
        -> commit

Only the LAST five steps touch the database, and they're wrapped in one
transaction: if any of them raises, everything rolls back and the persona's
previous accepted formulation (if any) and current_* fields are untouched.
The model call and enforcement happen before any of that, outside a
transaction, so a rejected attempt (case B) costs nothing to roll back - it
never wrote anything in the first place, only its own diagnostic
FormulationValidationReport rows (formulation_id=null, its own mini-commit,
independent of the main transaction) get persisted, then the caller retries
the whole model call once (case B -> retry). If retry ALSO ends in
rejection, or the model call itself fails twice, Analyze Life V2 fails
visibly (AnalyzeLifeV2Result.status == "failed") and nothing about the
persona changes (case C).

timeline_snapshots is deliberately NOT written here - see snapshots.py's
module docstring for why (it's the remix/what-if feature's table, not the
real per-experience history table V2's sparse change points naturally map
onto).
"""
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import FormulationValidationReport, Persona, WholeLifeFormulation
from app.services.whole_life_formulation.db_request_assembler import build_life_source_data
from app.services.whole_life_formulation.enforcement import EnforcementAction, enforce_validation
from app.services.whole_life_formulation.formulation_service import (
    FormulationCallError,
    generate_whole_life_formulation,
)
from app.services.whole_life_formulation.projections import reconcile_all_projections
from app.services.whole_life_formulation.request_assembler import assemble_request
from app.services.whole_life_formulation.snapshots import (
    ATTACHMENT_DIMS,
    BIG_FIVE_TRAITS,
    STATE_DIMS,
    rebuild_personality_snapshots,
)

logger = logging.getLogger(__name__)

MAX_MODEL_RETRIES = 1  # one clean retry on a rejected formulation, per the locked spec


@dataclass
class AnalyzeLifeV2Result:
    status: str  # "accepted" | "failed"
    formulation_id: Optional[str] = None
    generation_number: Optional[int] = None
    error: Optional[str] = None
    action_counts: dict = field(default_factory=dict)


def _persist_validation_report(db: Session, persona_id: str, attempted_generation_id: str,
                                formulation_id: Optional[str], actions: List[EnforcementAction]) -> None:
    for action in actions:
        db.add(FormulationValidationReport(
            formulation_id=formulation_id,
            attempted_generation_id=attempted_generation_id,
            persona_id=persona_id,
            claim_type=action.claim_type,
            claim_ref=action.claim_ref,
            rule_violated=action.rule_violated,
            action_taken=action.action_taken,
            rejection_reason=action.rejection_reason,
            raw_claim_json=action.raw_claim_json,
        ))


def analyze_life_v2(db: Session, persona: Persona) -> AnalyzeLifeV2Result:
    life = build_life_source_data(db, persona)
    if not life.experiences:
        return AnalyzeLifeV2Result(status="failed", error="Persona has no experiences to analyze.")

    request = assemble_request(life)
    input_fingerprint = hashlib.sha256(request.prompt_input.encode("utf-8")).hexdigest()

    last_error_summary = None
    for attempt in range(MAX_MODEL_RETRIES + 1):
        attempted_generation_id = str(uuid.uuid4())

        try:
            result = generate_whole_life_formulation(request)
        except FormulationCallError as exc:
            last_error_summary = f"model call failed: {exc.message}"
            logger.warning("Analyze Life V2 attempt %s failed for persona %s: %s", attempt, persona.id, last_error_summary)
            continue

        enforcement = enforce_validation(result.final, life)

        if enforcement.status == "rejected":
            last_error_summary = enforcement.rejection_summary
            logger.warning(
                "Analyze Life V2 attempt %s rejected for persona %s: %s",
                attempt, persona.id, last_error_summary,
            )
            # Record the rejected attempt's diagnostics in their own small
            # transaction - this must survive even if we go on to fail
            # entirely, and must never touch persona/projection state.
            try:
                _persist_validation_report(db, persona.id, attempted_generation_id, None, enforcement.actions)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to persist validation report for rejected attempt %s", attempted_generation_id)
            continue

        # --- accepted: one atomic write ---
        f = enforcement.accepted_formulation
        try:
            next_generation = (
                db.query(func.max(WholeLifeFormulation.generation_number))
                .filter(WholeLifeFormulation.persona_id == persona.id)
                .scalar() or 0
            ) + 1

            db.query(WholeLifeFormulation).filter(
                WholeLifeFormulation.persona_id == persona.id,
                WholeLifeFormulation.status == "accepted",
            ).update({"status": "superseded"}, synchronize_session=False)

            formulation_row = WholeLifeFormulation(
                persona_id=persona.id,
                engine_version=f.schema_version,
                schema_version=f.schema_version,
                generation_number=next_generation,
                generated_at=datetime.utcnow(),
                input_fingerprint=input_fingerprint,
                model_id=result.model_id,
                formulation_json=f.model_dump(),
                status="accepted",
            )
            db.add(formulation_row)
            db.flush()  # need formulation_row.id for the validation report rows below

            _persist_validation_report(db, persona.id, attempted_generation_id, formulation_row.id, enforcement.actions)

            reconcile_all_projections(db, persona.id, f, life)
            rebuild_personality_snapshots(db, persona.id, f, life)

            persona.current_personality = {t: getattr(f.current_personality, t).value for t in BIG_FIVE_TRAITS}
            persona.current_attachment_style = f.current_attachment.style
            persona.current_attachment_dimensions = {d: getattr(f.current_attachment, d).value for d in ATTACHMENT_DIMS}
            persona.current_state = {d: getattr(f.current_state, d).value for d in STATE_DIMS}
            persona.formulation_engine_version = "v2"
            flag_modified(persona, "current_personality")
            flag_modified(persona, "current_attachment_dimensions")
            flag_modified(persona, "current_state")

            db.commit()
            db.refresh(persona)
            action_counts = {}
            for a in enforcement.actions:
                action_counts[a.action_taken] = action_counts.get(a.action_taken, 0) + 1
            return AnalyzeLifeV2Result(
                status="accepted",
                formulation_id=formulation_row.id,
                generation_number=next_generation,
                action_counts=action_counts,
            )
        except Exception as exc:  # noqa: BLE001 - any DB step failing rolls back EVERYTHING
            db.rollback()
            logger.exception("Analyze Life V2 persistence failed for persona %s - rolled back, no state changed", persona.id)
            return AnalyzeLifeV2Result(status="failed", error=f"Persistence failed and was rolled back: {exc}")

    return AnalyzeLifeV2Result(
        status="failed",
        error=f"Analyze Life V2 failed after {MAX_MODEL_RETRIES + 1} attempt(s): {last_error_summary}. "
              f"Previous formulation (if any) is unchanged.",
    )
