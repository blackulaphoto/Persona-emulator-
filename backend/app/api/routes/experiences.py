"""
Experience API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona, Experience, PersonalitySnapshot
from app.schemas import ExperienceCreate, ExperienceResponse
from app.services.psychology_engine import analyze_experience


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
        raise HTTPException(status_code=404, detail="Persona not found")

    # Validate age - allow any age from 0 to 120 to support adding childhood experiences
    if experience_data.age_at_event < 0 or experience_data.age_at_event > 120:
        raise HTTPException(
            status_code=400,
            detail=f"Experience age must be between 0 and 120"
        )

    # Get previous experiences for context
    previous_experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()
    
    # Calculate sequence number
    sequence_number = len(previous_experiences) + 1
    
    # Run AI analysis (pass persona_id, not ORM object)
    try:
        analysis = await analyze_experience(
            persona_id=persona_id,
            experience_description=experience_data.user_description,
            age_at_event=experience_data.age_at_event,
            db=db,
            previous_experiences=previous_experiences
        )
    except Exception as e:
        logger.exception("Experience analysis failed for persona %s", persona_id)
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    
    # Create experience record
    experience = Experience(
        user_id=user_id,
        persona_id=persona_id,
        sequence_number=sequence_number,
        age_at_event=experience_data.age_at_event,
        user_description=experience_data.user_description,
        immediate_effects=analysis.get("immediate_effects"),
        long_term_patterns=analysis.get("long_term_patterns"),
        symptoms_developed=analysis.get("symptoms_developed"),
        symptom_severity=analysis.get("symptom_severity"),
        coping_mechanisms=analysis.get("coping_mechanisms"),
        worldview_shifts=analysis.get("worldview_shifts"),
        cross_experience_triggers=analysis.get("cross_experience_triggers"),
        recommended_therapies=analysis.get("recommended_therapies")
    )
    
    db.add(experience)
    db.flush()  # Flush to generate experience.id
    
    # Update persona's current state
    immediate_effects = analysis.get("immediate_effects", {})
    
    # Apply personality changes
    if immediate_effects:
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            if trait in immediate_effects:
                persona.current_personality[trait] = immediate_effects[trait]
        
        # Mark as modified for SQLAlchemy to detect JSON change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(persona, "current_personality")
    
    # Update current age
    if experience_data.age_at_event > persona.current_age:
        persona.current_age = experience_data.age_at_event
    
    # Add symptoms to trauma markers
    symptoms = analysis.get("symptoms_developed", [])
    if symptoms:
        current_markers = persona.current_trauma_markers or []
        persona.current_trauma_markers = list(set(current_markers + symptoms))
        flag_modified(persona, "current_trauma_markers")
    
    # Create personality snapshot (now experience.id exists)
    snapshot = PersonalitySnapshot(
        persona_id=persona_id,
        experience_id=experience.id,
        age=experience_data.age_at_event,
        personality_profile=dict(persona.current_personality),
        attachment_style=persona.current_attachment_style,
        trauma_markers=list(persona.current_trauma_markers),
        symptom_severity=analysis.get("symptom_severity", {})
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
