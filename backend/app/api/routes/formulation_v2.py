"""
Whole-Life Formulation V2 API routes - PERSISTENCE PHASE.

Deliberately a separate endpoint from experiences.py's existing "Analyze
Life" batch route, not a flag-branch inside it - this keeps V1's routes
(add_experience / add_experiences_batch / update_experience /
delete_experience) completely untouched, satisfying "V1 production behavior
remains untouched when false" trivially, since those routes aren't touched
regardless of the flag's value. Experiences themselves are just factual
source data either way - V1's per-experience pipeline continues to run
unchanged on every experience add, for every persona, V2-eligible or not;
its writes to shared projection tables are simply superseded the next time
Analyze Life V2 is explicitly run for a V2-eligible persona (see
projections.py's module docstring).

Not wired into the frontend "Analyze Life" button in this phase - "prove
data plumbing only." Exercised directly (QA script / API client) against the
allowlist while WHOLE_LIFE_FORMULATION_V2 is enabled.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Persona
from app.schemas import PersonaResponse
from app.services.api_projection import persona_projection
from app.services.whole_life_formulation.persistence_service import analyze_life_v2

router = APIRouter(prefix="/api/v1/personas", tags=["formulation-v2"])
logger = logging.getLogger(__name__)


def _require_v2_eligible(persona: Persona, user_id: str) -> None:
    if not settings.whole_life_formulation_v2_enabled_for(persona.id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Whole-Life Formulation V2 is not enabled for this persona. "
                   "It is currently allowlist-only.",
        )


@router.post("/{persona_id}/analyze-v2", response_model=PersonaResponse)
async def analyze_life_v2_route(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    persona = db.query(Persona).filter(Persona.id == persona_id, Persona.user_id == user_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    _require_v2_eligible(persona, user_id)

    result = analyze_life_v2(db, persona)
    if result.status != "accepted":
        raise HTTPException(status_code=422, detail=result.error or "Analyze Life V2 failed.")

    logger.info(
        "Analyze Life V2 accepted for persona %s: formulation_id=%s generation=%s actions=%s",
        persona_id, result.formulation_id, result.generation_number, result.action_counts,
    )
    db.refresh(persona)
    return PersonaResponse(**persona_projection(db, persona))
