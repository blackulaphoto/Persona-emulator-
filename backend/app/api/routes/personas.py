"""
Persona API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona
from app.utils.foundational_baseline import (
    clamp_personality_range,
    derive_foundational_baseline_async,
    infer_foundational_signals
)
from app.services.developmental_pipeline import process_developmental_text
from app.services.developmental_exposure_engine import extract_developmental_exposures_async
from app.services.api_projection import persona_projection
from app.services.attachment_engine import derive_baseline_attachment, dimensions_for_style
from app.schemas import PersonaCreate, PersonaUpdate, PersonaResponse
from app.services.preview_access import enforce_preview_persona_limit

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


@router.post("", response_model=PersonaResponse, status_code=201)
async def create_persona(
    persona_data: PersonaCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new persona with baseline personality.

    Enforces 3-persona limit for research preview.
    """
    enforce_preview_persona_limit(db, user_id)

    # Set baseline personality (default to foundational baseline if not provided)
    early_environment = persona_data.baseline_background
    foundational_signals = {}

    if persona_data.baseline_personality:
        baseline_personality = {
            "openness": persona_data.baseline_personality.openness,
            "conscientiousness": persona_data.baseline_personality.conscientiousness,
            "extraversion": persona_data.baseline_personality.extraversion,
            "agreeableness": persona_data.baseline_personality.agreeableness,
            "neuroticism": persona_data.baseline_personality.neuroticism
        }
        baseline_personality = clamp_personality_range(baseline_personality)
    else:
        baseline_personality, foundational_signals = await derive_foundational_baseline_async(
            early_environment,
            baseline_age=persona_data.baseline_age,
            gender=persona_data.baseline_gender
        )
    
    # Derive attachment from the same canonical background features when the
    # case author did not explicitly supply a starting style.
    background_extraction = await extract_developmental_exposures_async(early_environment)
    if persona_data.baseline_attachment_style:
        baseline_attachment_style = persona_data.baseline_attachment_style
        baseline_attachment_dimensions = dimensions_for_style(baseline_attachment_style)
    else:
        baseline_attachment = derive_baseline_attachment(background_extraction)
        baseline_attachment_style = baseline_attachment["style"]
        baseline_attachment_dimensions = baseline_attachment["dimensions"]
    persona = Persona(
        user_id=user_id,  # Add Firebase UID
        name=persona_data.name,
        baseline_age=persona_data.baseline_age,
        current_age=persona_data.baseline_age,  # Starts at baseline
        baseline_gender=persona_data.baseline_gender,
        baseline_background=persona_data.baseline_background,
        current_personality=baseline_personality,
        baseline_personality=dict(baseline_personality),
        current_attachment_style=baseline_attachment_style,
        baseline_attachment_style=baseline_attachment_style,
        baseline_attachment_dimensions=baseline_attachment_dimensions,
        current_attachment_dimensions=dict(baseline_attachment_dimensions),
        current_trauma_markers=[],
        foundational_environment_signals=foundational_signals,
        baseline_initialized=True
    )
    
    db.add(persona)
    db.commit()
    db.refresh(persona)

    # Developmental pipeline (steps 2-5, docs/MIGRATION_MAP.md "wiring steps 2-5
    # into routes"; State/Trait tiers added in Step 11): replaces the old
    # backstory_symptom_mapper.py direct keyword-to-disorder assignment. Runs
    # exposure extraction, self-narration (gated to persona_voice - a
    # backstory field is case-authored, so this correctly stays dormant),
    # evidence accumulation, interpretation, and pattern formation, then
    # projects current_trauma_markers from earned evidence instead of a
    # keyword hit. Also proposes and applies State movement (always) and
    # Trait movement (gated on AdaptationPattern.status == "established") -
    # on THIS route, unlike experiences.py, this pipeline is the only thing
    # that touches current_personality after the one-time foundational
    # baseline set just above, so Trait movement here is already fully
    # gated/clean, not a transitional double-write. Failure here must not
    # block persona creation - the persona and its baseline personality
    # already exist and are valid without it.
    if persona.baseline_background:
        try:
            pipeline_result = await process_developmental_text(
                db, persona, persona.baseline_background,
                source="backstory", age=persona.baseline_age,
                canonical_extraction=background_extraction,
                update_attachment=False,
            )
            persona.current_trauma_markers = pipeline_result["trauma_markers"]
            db.commit()
        except Exception:
            logger.exception("Developmental pipeline failed for persona %s during creation", persona.id)
            db.rollback()

    return PersonaResponse(**persona_projection(db, persona))


@router.get("", response_model=List[PersonaResponse])
async def list_personas(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all personas for the current user.
    """
    personas = db.query(Persona).filter(Persona.user_id == user_id).all()
    
    # Convert to response format
    response_list = []
    for persona in personas:
        response_list.append(PersonaResponse(**persona_projection(db, persona)))
    
    return response_list


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific persona by ID.
    """
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id  # Verify ownership
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    return PersonaResponse(**persona_projection(db, persona))


@router.put("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: str,
    persona_update: PersonaUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update persona details (name, background).
    """
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id  # Verify ownership
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Update fields
    if persona_update.name is not None:
        persona.name = persona_update.name
    if persona_update.baseline_background is not None:
        persona.baseline_background = persona_update.baseline_background
    
    db.commit()
    db.refresh(persona)
    
    return PersonaResponse(**persona_projection(db, persona))


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a persona and all associated data.
    """
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id  # Verify ownership
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    db.delete(persona)
    db.commit()
    
    return None
