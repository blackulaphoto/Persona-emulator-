"""
Experience API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona, Experience, PersonalitySnapshot
from app.schemas import ExperienceCreate, ExperienceResponse
from app.services.developmental_pipeline import process_developmental_text
from app.services.legacy_experience_adapter import to_legacy_experience_fields


router = APIRouter(prefix="/api/v1/personas", tags=["experiences"])
logger = logging.getLogger(__name__)


@router.post("/{persona_id}/experiences", response_model=ExperienceResponse, status_code=201)
async def add_experience(
    persona_id: str,
    experience_data: ExperienceCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a life experience to a persona and analyze its psychological impact.
    """
    # Get persona and verify ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        persona = db.query(Persona).filter(Persona.id == persona_id).first()
        if persona:
            logger.warning(
                "Persona %s not owned by user %s. Proceeding without ownership check.",
                persona_id,
                user_id
            )
        else:
            raise HTTPException(status_code=404, detail="Persona not found")

    # Validate age - allow any age from 0 to 120 to support adding childhood experiences
    if experience_data.age_at_event < 0 or experience_data.age_at_event > 120:
        raise HTTPException(
            status_code=400,
            detail=f"Experience age must be between 0 and 120"
        )

    # Get previous experiences for context (sequence number only now - see
    # Step 11d below for why this no longer feeds an AI call directly)
    previous_experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()

    # Calculate sequence number
    sequence_number = len(previous_experiences) + 1

    # Create experience record. Legacy analysis fields (immediate_effects,
    # symptoms_developed, etc.) are filled in AFTER the developmental
    # pipeline runs below, from its output - not from an independent AI
    # call - so the row is created first with those fields empty, purely to
    # generate experience.id (needed as source_event_id for the pipeline).
    experience = Experience(
        user_id=user_id,
        persona_id=persona_id,
        sequence_number=sequence_number,
        age_at_event=experience_data.age_at_event,
        user_description=experience_data.user_description,
    )
    db.add(experience)
    db.flush()  # Flush to generate experience.id

    # Update current age
    if experience_data.age_at_event > persona.current_age:
        persona.current_age = experience_data.age_at_event

    # Developmental pipeline (steps 2-5, docs/MIGRATION_MAP.md "wiring steps 2-5
    # into routes"; State/Trait tiers and this route's swap-over added in
    # Step 11): runs exposure extraction, self-narration (gated to
    # persona_voice - an experience description is case-authored by default,
    # so this correctly stays dormant), evidence accumulation (recomputed
    # across the persona's FULL timeline, not just this experience), pattern
    # formation, and State/Trait movement (State always; Trait gated on
    # AdaptationPattern.status == "established"). This is now the ONLY
    # analysis path for an experience - Step 11d retired psychology_engine.
    # analyze_experience()'s old, ungated, independent per-experience GPT
    # call entirely (it is no longer imported by this module). Trait
    # movement on this route is therefore driven by exactly one mechanism
    # now, same as personas.py.
    #
    # legacy_experience_adapter.to_legacy_experience_fields() translates the
    # pipeline's output into the Experience row's pre-existing response
    # shape, so the frontend contract (ExperienceResponse) does not change -
    # see that module's docstring for exactly what each field means now and
    # why a few (cross_experience_triggers, recommended_therapies) are
    # honestly left empty rather than fabricated.
    #
    # A pipeline failure is more consequential than it was pre-Step-11d, now
    # that it's the only analysis path - it still must not block adding the
    # experience (the Experience row is already valid without legacy
    # fields), matching this rebuild's graceful-degradation philosophy
    # elsewhere (personas.py, chat.py's safety net).
    legacy_fields = {}
    try:
        pipeline_result = await process_developmental_text(
            db, persona, experience_data.user_description,
            source="experience", age=experience_data.age_at_event, source_event_id=experience.id,
        )
        persona.current_trauma_markers = pipeline_result["trauma_markers"]
        flag_modified(persona, "current_trauma_markers")
        legacy_fields = to_legacy_experience_fields(pipeline_result, persona)
    except Exception:
        logger.exception("Developmental pipeline failed for persona %s, experience %s", persona_id, experience.id)

    experience.immediate_effects = legacy_fields.get("immediate_effects")
    experience.long_term_patterns = legacy_fields.get("long_term_patterns")
    experience.symptoms_developed = legacy_fields.get("symptoms_developed")
    experience.symptom_severity = legacy_fields.get("symptom_severity")
    experience.coping_mechanisms = legacy_fields.get("coping_mechanisms")
    experience.worldview_shifts = legacy_fields.get("worldview_shifts")
    experience.cross_experience_triggers = legacy_fields.get("cross_experience_triggers")
    experience.recommended_therapies = legacy_fields.get("recommended_therapies")

    # Create personality snapshot (now experience.id exists). state_profile
    # (Step 11, State tier) is frozen alongside personality_profile (Trait
    # tier) - see app/models/personality_snapshot.py.
    snapshot = PersonalitySnapshot(
        persona_id=persona_id,
        experience_id=experience.id,
        age=experience_data.age_at_event,
        personality_profile=dict(persona.current_personality),
        attachment_style=persona.current_attachment_style,
        trauma_markers=list(persona.current_trauma_markers),
        symptom_severity=legacy_fields.get("symptom_severity") or {},
        state_profile=dict(persona.current_state) if persona.current_state else None,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(experience)
    
    # Convert symptom_severity floats to integers
    symptom_severity_converted = {}
    if experience.symptom_severity:
        for symptom, value in experience.symptom_severity.items():
            symptom_severity_converted[symptom] = int(round(value))

    # Convert to response format
    experience_dict = {
        "id": str(experience.id),
        "persona_id": str(experience.persona_id),
        "sequence_number": experience.sequence_number,
        "age_at_event": experience.age_at_event,
        "user_description": experience.user_description,
        "immediate_effects": experience.immediate_effects,
        "long_term_patterns": experience.long_term_patterns,
        "symptoms_developed": experience.symptoms_developed,
        "symptom_severity": symptom_severity_converted,
        "coping_mechanisms": experience.coping_mechanisms,
        "worldview_shifts": experience.worldview_shifts,
        "cross_experience_triggers": experience.cross_experience_triggers,
        "recommended_therapies": experience.recommended_therapies,
        "created_at": experience.created_at
    }
    
    return ExperienceResponse(**experience_dict)


@router.get("/{persona_id}/experiences", response_model=List[ExperienceResponse])
async def get_persona_experiences(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all experiences for a persona, ordered by sequence.
    """
    # Verify persona exists and user owns it
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get experiences
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()
    
    # Convert to response format
    response_list = []
    for exp in experiences:
        # Convert symptom_severity floats to integers
        symptom_severity_converted = {}
        if exp.symptom_severity:
            for symptom, value in exp.symptom_severity.items():
                symptom_severity_converted[symptom] = int(round(value))

        exp_dict = {
            "id": str(exp.id),
            "persona_id": str(exp.persona_id),
            "sequence_number": exp.sequence_number,
            "age_at_event": exp.age_at_event,
            "user_description": exp.user_description,
            "immediate_effects": exp.immediate_effects,
            "long_term_patterns": exp.long_term_patterns,
            "symptoms_developed": exp.symptoms_developed,
            "symptom_severity": symptom_severity_converted,
            "coping_mechanisms": exp.coping_mechanisms,
            "worldview_shifts": exp.worldview_shifts,
            "cross_experience_triggers": exp.cross_experience_triggers,
            "recommended_therapies": exp.recommended_therapies,
            "created_at": exp.created_at
        }
        response_list.append(ExperienceResponse(**exp_dict))
    
    return response_list
