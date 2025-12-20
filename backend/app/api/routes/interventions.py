"""
Intervention API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona, Intervention, Experience, PersonalitySnapshot
from app.schemas import InterventionCreate, InterventionResponse
from app.services.intervention_engine import analyze_intervention


router = APIRouter(prefix="/api/v1/personas", tags=["interventions"])


@router.post("/{persona_id}/interventions", response_model=InterventionResponse, status_code=201)
async def add_intervention(
    persona_id: str,
    intervention_data: InterventionCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a therapeutic intervention to a persona and analyze its efficacy.
    """
    # Get persona and verify ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Validate age - allow any age from 0 to 120 to support adding childhood interventions
    if intervention_data.age_at_intervention < 0 or intervention_data.age_at_intervention > 120:
        raise HTTPException(
            status_code=400,
            detail=f"Intervention age must be between 0 and 120"
        )

    # Get previous experiences and interventions for context
    previous_experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()

    previous_interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.sequence_number).all()
    
    # Calculate sequence number
    sequence_number = len(previous_interventions) + 1
    
    # Convert duration string to weeks for analysis
    duration_map = {
        "3_months": 12,
        "6_months": 24,
        "1_year": 52,
        "2_years": 104
    }
    duration_weeks = duration_map.get(intervention_data.duration, 24)
    
    # Run AI analysis
    try:
        analysis = await analyze_intervention(
            persona=persona,
            therapy_type=intervention_data.therapy_type,
            duration=duration_weeks,
            intensity=intervention_data.intensity,
            age_at_intervention=intervention_data.age_at_intervention
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Intervention analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )
    
    # Create intervention record
    intervention = Intervention(
        user_id=user_id,
        persona_id=persona_id,
        sequence_number=sequence_number,
        age_at_intervention=intervention_data.age_at_intervention,
        therapy_type=intervention_data.therapy_type,
        duration=intervention_data.duration,
        intensity=intervention_data.intensity,
        user_notes=intervention_data.user_notes,
        actual_symptoms_targeted=analysis.get("actual_symptoms_targeted"),
        efficacy_match=analysis.get("efficacy_match"),
        immediate_effects=analysis.get("immediate_effects"),
        sustained_effects=analysis.get("sustained_effects"),
        limitations=analysis.get("limitations"),
        symptom_changes=analysis.get("symptom_changes"),
        personality_changes=analysis.get("personality_changes"),
        coping_skills_gained=analysis.get("coping_skills_gained")
    )
    
    db.add(intervention)
    db.flush()  # Flush to generate intervention.id
    
    # Update persona's current state
    personality_changes = analysis.get("personality_changes", {})
    
    # Apply personality changes
    if personality_changes:
        for trait, new_value in personality_changes.items():
            if trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
                persona.current_personality[trait] = new_value
        
        # Mark as modified for SQLAlchemy to detect JSON change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(persona, "current_personality")
    
    # Update current age
    if intervention_data.age_at_intervention > persona.current_age:
        persona.current_age = intervention_data.age_at_intervention
    
    # Create personality snapshot (now intervention.id exists)
    # Extract "after" values from symptom_changes if it has that structure
    symptom_changes_data = analysis.get("symptom_changes", {})
    if isinstance(symptom_changes_data, dict) and "after" in symptom_changes_data:
        # symptom_changes has structure: {before: {...}, after: {...}, percentage_improvement: {...}}
        # Extract just the "after" values for symptom_severity
        symptom_severity_value = symptom_changes_data.get("after", {})
    else:
        # symptom_changes is already in the format {symptom: severity}
        symptom_severity_value = symptom_changes_data
    
    snapshot = PersonalitySnapshot(
        persona_id=persona_id,
        intervention_id=intervention.id,
        age=intervention_data.age_at_intervention,
        personality_profile=dict(persona.current_personality),
        attachment_style=persona.current_attachment_style,
        trauma_markers=list(persona.current_trauma_markers),
        symptom_severity=symptom_severity_value
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(intervention)
    
    # Convert to response format
    # Handle symptom_changes - schema expects Dict[str, int] but analysis returns nested structure
    symptom_changes_for_response = intervention.symptom_changes
    if isinstance(symptom_changes_for_response, dict) and "after" in symptom_changes_for_response:
        # Extract "after" values for response (schema expects Dict[str, int])
        symptom_changes_for_response = symptom_changes_for_response.get("after", {})
    
    # Handle immediate_effects and sustained_effects - schema expects Dict but may receive List
    # Convert list to dict if needed, or pass as-is if already dict/None
    immediate_effects_for_response = intervention.immediate_effects
    if isinstance(immediate_effects_for_response, list):
        # Convert list to dict format for schema compatibility
        immediate_effects_for_response = {"effects": immediate_effects_for_response}
    
    sustained_effects_for_response = intervention.sustained_effects
    if isinstance(sustained_effects_for_response, list):
        # Convert list to dict format for schema compatibility
        sustained_effects_for_response = {"effects": sustained_effects_for_response}
    
    # Build response dict with proper type handling
    intervention_dict = {
        "id": str(intervention.id),
        "persona_id": str(intervention.persona_id),
        "sequence_number": intervention.sequence_number,
        "therapy_type": intervention.therapy_type,
        "duration": intervention.duration,
        "intensity": intervention.intensity,
        "age_at_intervention": intervention.age_at_intervention,
        "user_notes": intervention.user_notes,
        "actual_symptoms_targeted": intervention.actual_symptoms_targeted,
        "efficacy_match": intervention.efficacy_match,
        "immediate_effects": immediate_effects_for_response,
        "sustained_effects": sustained_effects_for_response,
        "limitations": intervention.limitations,
        "symptom_changes": symptom_changes_for_response,
        "personality_changes": intervention.personality_changes,
        "coping_skills_gained": intervention.coping_skills_gained,
        "created_at": intervention.created_at
    }
    
    try:
        return InterventionResponse(**intervention_dict)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Response serialization error: {str(e)}", exc_info=True)
        logger.error(f"intervention_dict keys: {list(intervention_dict.keys())}")
        logger.error(f"symptom_changes type: {type(symptom_changes_for_response)}, value: {symptom_changes_for_response}")
        logger.error(f"immediate_effects type: {type(immediate_effects_for_response)}, value: {immediate_effects_for_response}")
        logger.error(f"sustained_effects type: {type(sustained_effects_for_response)}, value: {sustained_effects_for_response}")
        raise HTTPException(
            status_code=500,
            detail=f"Response serialization failed: {str(e)}"
        )


@router.get("/{persona_id}/interventions", response_model=List[InterventionResponse])
async def get_persona_interventions(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all interventions for a persona, ordered by sequence.
    """
    # Verify persona exists and user owns it
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get interventions
    interventions = db.query(Intervention).filter(
        Intervention.persona_id == persona_id
    ).order_by(Intervention.sequence_number).all()
    
    # Convert to response format
    response_list = []
    for interv in interventions:
        interv_dict = {
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
        response_list.append(InterventionResponse(**interv_dict))
    
    return response_list
