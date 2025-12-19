"""
Timeline API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.models import Persona, Experience, Intervention, PersonalitySnapshot
from app.schemas import (
    PersonaResponse, 
    ExperienceResponse, 
    InterventionResponse,
    PersonalitySnapshotResponse,
    TimelineResponse
)


router = APIRouter(prefix="/api/v1/personas", tags=["timeline"])


def convert_persona_to_response(persona: Persona) -> Dict[str, Any]:
    """Convert Persona model to response dict."""
    return {
        "id": str(persona.id),
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "baseline_personality": persona.current_personality,  # Initially same as baseline
        "baseline_attachment_style": persona.current_attachment_style,
        "current_personality": persona.current_personality,
        "current_attachment_style": persona.current_attachment_style,
        "current_trauma_markers": persona.current_trauma_markers,
        "current_age": persona.current_age,
        "experiences_count": len(persona.experiences),
        "interventions_count": len(persona.interventions),
        "created_at": persona.created_at,
        "updated_at": persona.updated_at
    }


def convert_experience_to_response(exp: Experience) -> Dict[str, Any]:
    """Convert Experience model to response dict."""
    return {
        "id": str(exp.id),
        "persona_id": str(exp.persona_id),
        "sequence_number": exp.sequence_number,
        "age_at_event": exp.age_at_event,
        "user_description": exp.user_description,
        "immediate_effects": exp.immediate_effects,
        "long_term_patterns": exp.long_term_patterns,
        "symptoms_developed": exp.symptoms_developed,
        "symptom_severity": exp.symptom_severity,
        "coping_mechanisms": exp.coping_mechanisms,
        "worldview_shifts": exp.worldview_shifts,
        "cross_experience_triggers": exp.cross_experience_triggers,
        "recommended_therapies": exp.recommended_therapies,
        "created_at": exp.created_at
    }


def convert_intervention_to_response(interv: Intervention) -> Dict[str, Any]:
    """Convert Intervention model to response dict."""
    return {
        "id": str(interv.id),
        "persona_id": str(interv.persona_id),
        "sequence_number": interv.sequence_number,
        "therapy_type": interv.therapy_type,
        "duration": interv.duration,
        "intensity": interv.intensity,
        "age_at_intervention": interv.age_at_intervention,
        "user_notes": interv.user_notes,
        "actual_symptoms_targeted": interv.actual_symptoms_targeted,
        "efficacy_match": interv.efficacy_match,
        "immediate_effects": interv.immediate_effects,
        "sustained_effects": interv.sustained_effects,
        "limitations": interv.limitations,
        "symptom_changes": interv.symptom_changes,
        "personality_changes": interv.personality_changes,
        "coping_skills_gained": interv.coping_skills_gained,
        "created_at": interv.created_at
    }


def convert_snapshot_to_response(snapshot: PersonalitySnapshot) -> Dict[str, Any]:
    """Convert PersonalitySnapshot model to response dict."""
    return {
        "id": str(snapshot.id),
        "persona_id": str(snapshot.persona_id),
        "age": snapshot.age,
        "personality_profile": snapshot.personality_profile,
        "attachment_style": snapshot.attachment_style,
        "trauma_markers": snapshot.trauma_markers,
        "symptom_severity": snapshot.symptom_severity,
        "created_at": snapshot.created_at
    }


@router.get("/{persona_id}/timeline")
def get_persona_timeline(persona_id: str, db: Session = Depends(get_db)):
    """
    Get complete timeline for a persona including experiences, interventions, and snapshots.
    Returns chronologically ordered events showing personality evolution over time.
    """
    # Get persona with all relationships
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get experiences
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.age_at_event).all()

    # Get interventions
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.age_at_intervention).all()

    # Get snapshots
    snapshots = db.query(PersonalitySnapshot).filter(
        PersonalitySnapshot.persona_id == persona_id
    ).order_by(PersonalitySnapshot.age).all()
    
    # Build timeline events (combined experiences and interventions)
    timeline_events = []
    
    # Add experiences to timeline
    for exp in experiences:
        # Find corresponding snapshot
        snapshot = next(
            (s for s in snapshots if s.experience_id == exp.id),
            None
        )
        
        event = {
            "type": "experience",
            "age": exp.age_at_event,
            "sequence_number": exp.sequence_number,
            "description": exp.user_description,
            "symptoms_developed": exp.symptoms_developed,
            "symptom_severity": exp.symptom_severity,
            "long_term_patterns": exp.long_term_patterns,
            "recommended_therapies": exp.recommended_therapies,
            "personality_snapshot": convert_snapshot_to_response(snapshot) if snapshot else None
        }
        timeline_events.append(event)
    
    # Add interventions to timeline
    for interv in interventions:
        # Find corresponding snapshot
        snapshot = next(
            (s for s in snapshots if s.intervention_id == interv.id),
            None
        )
        
        event = {
            "type": "intervention",
            "age": interv.age_at_intervention,
            "sequence_number": interv.sequence_number,
            "therapy_type": interv.therapy_type,
            "duration": interv.duration,
            "intensity": interv.intensity,
            "actual_symptoms_targeted": interv.actual_symptoms_targeted,
            "efficacy_match": interv.efficacy_match,
            "symptom_changes": interv.symptom_changes,
            "personality_changes": interv.personality_changes,
            "coping_skills_gained": interv.coping_skills_gained,
            "limitations": interv.limitations,
            "personality_snapshot": convert_snapshot_to_response(snapshot) if snapshot else None
        }
        timeline_events.append(event)
    
    # Sort timeline by age
    timeline_events.sort(key=lambda x: x["age"])
    
    # Convert to response format
    response = {
        "persona": convert_persona_to_response(persona),
        "experiences": [convert_experience_to_response(exp) for exp in experiences],
        "interventions": [convert_intervention_to_response(interv) for interv in interventions],
        "snapshots": [convert_snapshot_to_response(snap) for snap in snapshots],
        "timeline_events": timeline_events
    }
    
    return response
