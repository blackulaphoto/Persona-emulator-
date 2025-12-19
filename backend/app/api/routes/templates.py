"""
Template API Routes

Endpoints for clinical templates feature.
Protected by FEATURE_CLINICAL_TEMPLATES flag.

Following patterns from personas, experiences, interventions routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.feature_flags import FeatureFlags
from app.models.clinical_template import ClinicalTemplate
from app.models.persona import Persona
from app.models.experience import Experience
from app.models.personality_snapshot import PersonalitySnapshot
from app.schemas.template_schemas import (
    ClinicalTemplateResponse,
    ClinicalTemplateListResponse,
    CreatePersonaFromTemplateRequest,
    CreatePersonaFromTemplateResponse,
    ApplyExperienceSetRequest,
    ApplyExperienceSetResponse,
)
from app.services.template_service import (
    create_persona_from_template,
    get_template_experiences,
    get_template_interventions,
    populate_templates_database,
    get_all_disorder_types,
)
from app.services.psychology_engine import analyze_experience
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


def require_templates_feature():
    """Dependency to check if clinical templates feature is enabled"""
    if not FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinical templates feature is not enabled. Contact administrator."
        )


# Debug endpoint to check feature flag status
@router.get("/debug/feature-flags")
async def debug_feature_flags():
    """Debug endpoint to check feature flag status (no feature flag check)"""
    import os
    from pathlib import Path
    from app.core.config import settings
    
    env_path = Path(".env")
    env_file_contents = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.split('=', 1)
                    env_file_contents[key.strip()] = val.strip()
    
    return {
        "env_file_path": str(env_path.absolute()),
        "env_file_exists": env_path.exists(),
        "env_file_feature_flags": {
            k: v for k, v in env_file_contents.items() if 'FEATURE' in k
        },
        "os_getenv_values": {
            "FEATURE_CLINICAL_TEMPLATES": os.getenv("FEATURE_CLINICAL_TEMPLATES"),
            "FEATURE_REMIX_TIMELINE": os.getenv("FEATURE_REMIX_TIMELINE"),
        },
        "settings_object_values": {
            "feature_clinical_templates": settings.feature_clinical_templates,
            "feature_remix_timeline": settings.feature_remix_timeline,
        },
        "feature_flags_check": {
            "CLINICAL_TEMPLATES": FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES),
            "REMIX_TIMELINE": FeatureFlags.is_enabled(FeatureFlags.REMIX_TIMELINE),
        },
        "feature_flags_raw_attr": {
            "has_feature_clinical_templates": hasattr(settings, "feature_clinical_templates"),
            "feature_clinical_templates_type": type(settings.feature_clinical_templates).__name__ if hasattr(settings, "feature_clinical_templates") else None,
        }
    }


# Endpoint 1: List all available templates
@router.get("", response_model=List[ClinicalTemplateListResponse], dependencies=[Depends(require_templates_feature)])
async def list_templates(
    disorder_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all available clinical templates.
    
    Query params:
    - disorder_type: Filter by disorder type (e.g., "BPD", "C-PTSD")
    """
    # Ensure templates are loaded in database
    template_count = db.query(ClinicalTemplate).count()
    if template_count == 0:
        # First time - populate database from JSON files
        populate_templates_database(db)
    
    # Query templates
    query = db.query(ClinicalTemplate)
    if disorder_type:
        query = query.filter(ClinicalTemplate.disorder_type == disorder_type)
    
    templates = query.all()
    
    # Format response
    response = []
    for template in templates:
        response.append({
            "id": template.id,
            "name": template.name,
            "disorder_type": template.disorder_type,
            "description": template.description,
            "baseline_age": template.baseline_age,
            "experience_count": len(template.predefined_experiences) if template.predefined_experiences else 0,
            "intervention_count": len(template.predefined_interventions) if template.predefined_interventions else 0,
            "remix_suggestion_count": len(template.remix_suggestions) if template.remix_suggestions else 0,
        })
    
    return response


# Endpoint 2: Get template details by ID
@router.get("/{template_id}", response_model=ClinicalTemplateResponse, dependencies=[Depends(require_templates_feature)])
async def get_template_details(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific template.
    
    Includes:
    - Full clinical rationale
    - All predefined experiences
    - Suggested interventions
    - Expected outcomes
    - Remix suggestions
    - Research citations
    """
    template = db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    
    return template


# Endpoint 3: Get disorder types
@router.get("/meta/disorder-types", response_model=List[str], dependencies=[Depends(require_templates_feature)])
async def get_disorder_types(db: Session = Depends(get_db)):
    """
    Get list of all available disorder types.
    
    Returns: ["BPD", "C-PTSD", "Social_Anxiety", ...]
    """
    # Ensure templates loaded
    template_count = db.query(ClinicalTemplate).count()
    if template_count == 0:
        populate_templates_database(db)
    
    disorder_types = get_all_disorder_types(db)
    return disorder_types


# Endpoint 4: Create persona from template
@router.post("/create-persona", response_model=CreatePersonaFromTemplateResponse, dependencies=[Depends(require_templates_feature)])
async def create_persona_from_template_endpoint(
    request: CreatePersonaFromTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new persona from a clinical template.
    
    This creates the base persona with template's baseline configuration.
    User can then add experiences and interventions via standard APIs.
    
    Request:
    - template_id: ID of template to use
    - custom_name: Optional custom name (default: "Case Study: {disorder}")
    - owner_id: Optional owner ID (for multi-user systems)
    """
    # Verify template exists
    template = db.query(ClinicalTemplate).filter(
        ClinicalTemplate.id == request.template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{request.template_id}' not found"
        )
    
    # Create persona from template
    try:
        persona = create_persona_from_template(
            db=db,
            template_id=request.template_id,
            owner_id=request.owner_id,
            custom_name=request.custom_name
        )
    except Exception as e:
        logger.error(f"Error creating persona from template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create persona from template: {str(e)}"
        )
    
    # Get template data for response
    experiences = get_template_experiences(request.template_id, db)
    interventions = get_template_interventions(request.template_id, db)
    
    return CreatePersonaFromTemplateResponse(
        persona_id=str(persona.id),
        template_id=request.template_id,
        template_name=template.name,
        persona_name=persona.name,
        baseline_age=persona.baseline_age,
        baseline_personality=template.baseline_personality,  # Use template's baseline
        predefined_experiences_available=len(experiences),
        suggested_interventions_available=len(interventions),
        message=f"Persona '{persona.name}' created from template '{template.name}'. Use /personas/{persona.id}/experiences to add events."
    )


# Endpoint 5: Apply predefined experience set
@router.post("/personas/{persona_id}/apply-experiences", response_model=ApplyExperienceSetResponse, dependencies=[Depends(require_templates_feature)])
async def apply_experience_set(
    persona_id: str,
    request: ApplyExperienceSetRequest,
    db: Session = Depends(get_db)
):
    """
    Apply multiple predefined experiences from a template to a persona.
    
    This is a convenience endpoint that:
    1. Gets predefined experiences from template
    2. Applies each via AI analysis (using psychology engine)
    3. Updates persona state progressively
    
    Request:
    - template_id: Template to get experiences from
    - experience_indices: Optional list of indices to apply (default: all)
    """
    # Validate persona exists (persona.id is String, not UUID)
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found"
        )
    
    # Get template experiences
    try:
        experiences = get_template_experiences(request.template_id, db)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{request.template_id}' not found"
        )
    
    # Determine which experiences to apply
    if request.experience_indices is None:
        # Apply all experiences
        indices_to_apply = list(range(len(experiences)))
    else:
        # Validate indices
        if any(i >= len(experiences) for i in request.experience_indices):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Experience index out of range. Template has {len(experiences)} experiences."
            )
        indices_to_apply = request.experience_indices
    
    # Store baseline personality
    personality_before = persona.current_personality.copy()
    
    # Apply experiences sequentially
    experience_ids = []
    for idx in indices_to_apply:
        exp_data = experiences[idx]

        logger.error(f"DEBUG TEMPLATES: About to query experiences. persona_id type: {type(persona_id)}, value: {persona_id}")
        logger.error(f"DEBUG TEMPLATES: persona object type: {type(persona)}")

        # Get previous experiences for context
        previous_experiences = db.query(Experience).filter(
            Experience.persona_id == persona_id
        ).order_by(Experience.sequence_number).all()

        logger.error(f"DEBUG TEMPLATES: About to call analyze_experience with persona_id type: {type(persona_id)}")

        # Analyze experience using psychology engine (pass persona_id, not ORM object)
        try:
            analysis = await analyze_experience(
                persona_id=persona_id,
                experience_description=exp_data["description"],
                age_at_event=exp_data["age"],
                db=db,
                previous_experiences=previous_experiences
            )
            
            sequence_number = len(previous_experiences) + 1
            
            experience = Experience(
                persona_id=persona_id,
                sequence_number=sequence_number,
                age_at_event=exp_data["age"],
                user_description=exp_data["description"],
                immediate_effects=analysis.get("immediate_effects", {}),
                long_term_patterns=analysis.get("long_term_patterns", []),
                symptoms_developed=analysis.get("symptoms_developed", []),
                symptom_severity=analysis.get("symptom_severity", {}),
                coping_mechanisms=analysis.get("coping_mechanisms", []),
                worldview_shifts=analysis.get("worldview_shifts", {}),
                cross_experience_triggers=analysis.get("cross_experience_triggers", []),
                recommended_therapies=analysis.get("recommended_therapies", [])
            )
            
            db.add(experience)
            db.flush()  # Get experience ID
            
            # Update persona state
            immediate_effects = analysis.get("immediate_effects", {})
            for trait, new_value in immediate_effects.items():
                if trait in persona.current_personality:
                    persona.current_personality[trait] = new_value
            
            flag_modified(persona, "current_personality")
            
            # Update age
            persona.current_age = max(persona.current_age, exp_data["age"])
            
            # Update trauma markers
            new_symptoms = analysis.get("symptoms_developed", [])
            current_markers = set(persona.current_trauma_markers or [])
            current_markers.update(new_symptoms)
            persona.current_trauma_markers = list(current_markers)
            flag_modified(persona, "current_trauma_markers")
            
            # Create personality snapshot
            snapshot = PersonalitySnapshot(
                persona_id=persona_id,
                experience_id=experience.id,
                age=exp_data["age"],
                personality_profile=dict(persona.current_personality),
                attachment_style=persona.current_attachment_style,
                trauma_markers=list(persona.current_trauma_markers),
                symptom_severity=analysis.get("symptom_severity", {})
            )
            
            db.add(snapshot)
            experience_ids.append(str(experience.id))
            
        except Exception as e:
            logger.error(f"Error analyzing experience at index {idx}: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze experience at index {idx}: {str(e)}"
            )
    
    # Commit all changes
    db.commit()
    db.refresh(persona)
    
    return ApplyExperienceSetResponse(
        persona_id=persona_id,
        experiences_applied=len(experience_ids),
        experience_ids=experience_ids,
        personality_before=personality_before,
        personality_after=dict(persona.current_personality),
        symptoms_developed=list(persona.current_trauma_markers),
        current_age=persona.current_age
    )

