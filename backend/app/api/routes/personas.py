"""
Persona API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona
from app.utils.foundational_baseline import (
    clamp_personality_range,
    derive_foundational_baseline
)
from app.schemas import PersonaCreate, PersonaUpdate, PersonaResponse


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
    # Check persona count for user (research preview limit: 3)
    persona_count = db.query(Persona).filter(Persona.user_id == user_id).count()
    if persona_count >= 3:
        raise HTTPException(
            status_code=403,
            detail="Persona limit reached. Maximum 3 personas allowed in research preview."
        )

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
        baseline_personality, foundational_signals = derive_foundational_baseline(early_environment)
    
    # Create persona
    persona = Persona(
        user_id=user_id,  # Add Firebase UID
        name=persona_data.name,
        baseline_age=persona_data.baseline_age,
        current_age=persona_data.baseline_age,  # Starts at baseline
        baseline_gender=persona_data.baseline_gender,
        baseline_background=persona_data.baseline_background,
        current_personality=baseline_personality,
        current_attachment_style=persona_data.baseline_attachment_style or "secure",
        current_trauma_markers=[],
        foundational_environment_signals=foundational_signals,
        baseline_initialized=True
    )
    
    db.add(persona)
    db.commit()
    db.refresh(persona)
    
    # Convert to dict and add counts
    persona_dict = {
        "id": str(persona.id),
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        "current_age": persona.current_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "current_personality": persona.current_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_trauma_markers": persona.current_trauma_markers,
        "experiences_count": 0,
        "interventions_count": 0,
        "created_at": persona.created_at,
        "updated_at": persona.updated_at
    }
    
    return PersonaResponse(**persona_dict)


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
        persona_dict = {
            "id": str(persona.id),
            "name": persona.name,
            "baseline_age": persona.baseline_age,
            "current_age": persona.current_age,
            "baseline_gender": persona.baseline_gender,
            "baseline_background": persona.baseline_background,
            "current_personality": persona.current_personality,
            "current_attachment_style": persona.current_attachment_style,
            "current_trauma_markers": persona.current_trauma_markers,
            "experiences_count": len(persona.experiences),
            "interventions_count": len(persona.interventions),
            "created_at": persona.created_at,
            "updated_at": persona.updated_at
        }
        response_list.append(PersonaResponse(**persona_dict))
    
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
    
    # Convert to response format
    persona_dict = {
        "id": str(persona.id),
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        "current_age": persona.current_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "current_personality": persona.current_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_trauma_markers": persona.current_trauma_markers,
        "experiences_count": len(persona.experiences),
        "interventions_count": len(persona.interventions),
        "created_at": persona.created_at,
        "updated_at": persona.updated_at
    }
    
    return PersonaResponse(**persona_dict)


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
    
    # Convert to response format
    persona_dict = {
        "id": str(persona.id),
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        "current_age": persona.current_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "current_personality": persona.current_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_trauma_markers": persona.current_trauma_markers,
        "experiences_count": len(persona.experiences),
        "interventions_count": len(persona.interventions),
        "created_at": persona.created_at,
        "updated_at": persona.updated_at
    }
    
    return PersonaResponse(**persona_dict)


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
