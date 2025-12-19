"""
Persona API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import Persona
from app.schemas import PersonaCreate, PersonaUpdate, PersonaResponse


router = APIRouter(prefix="/api/v1/personas", tags=["personas"])


@router.post("", response_model=PersonaResponse, status_code=201)
def create_persona(persona_data: PersonaCreate, db: Session = Depends(get_db)):
    """
    Create a new persona with baseline personality.
    """
    # Set baseline personality (default to 0.5 for all traits if not provided)
    if persona_data.baseline_personality:
        baseline_personality = {
            "openness": persona_data.baseline_personality.openness,
            "conscientiousness": persona_data.baseline_personality.conscientiousness,
            "extraversion": persona_data.baseline_personality.extraversion,
            "agreeableness": persona_data.baseline_personality.agreeableness,
            "neuroticism": persona_data.baseline_personality.neuroticism
        }
    else:
        baseline_personality = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        }
    
    # Create persona
    persona = Persona(
        name=persona_data.name,
        baseline_age=persona_data.baseline_age,
        current_age=persona_data.baseline_age,  # Starts at baseline
        baseline_gender=persona_data.baseline_gender,
        baseline_background=persona_data.baseline_background,
        current_personality=baseline_personality,
        current_attachment_style=persona_data.baseline_attachment_style or "secure",
        current_trauma_markers=[]
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
def list_personas(db: Session = Depends(get_db)):
    """
    List all personas.
    """
    personas = db.query(Persona).all()
    
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
def get_persona(persona_id: str, db: Session = Depends(get_db)):
    """
    Get a specific persona by ID.
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    
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
def update_persona(
    persona_id: str,
    persona_update: PersonaUpdate,
    db: Session = Depends(get_db)
):
    """
    Update persona details (name, background).
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    
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
def delete_persona(persona_id: str, db: Session = Depends(get_db)):
    """
    Delete a persona and all associated data.
    """
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    db.delete(persona)
    db.commit()
    
    return None
