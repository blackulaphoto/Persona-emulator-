"""
Symptom tracking API routes.

Endpoints for comprehensive DSM-5/ICD-11 symptom assessment and tracking.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models import Persona, Experience, PersonaSymptom, SymptomHistory
from app.services.psychology_engine import assess_comprehensive_symptoms
from app.utils.symptom_taxonomy import (
    get_all_disorders,
    get_disorders_by_category,
    get_disorder_symptoms,
    get_all_categories,
    SYMPTOM_TAXONOMY
)
from app.utils.symptom_assessment_engine import SymptomAssessmentEngine
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1", tags=["symptoms"])
symptom_engine = SymptomAssessmentEngine()


# Pydantic schemas
class SymptomResponse(BaseModel):
    id: str
    symptom_name: str
    severity: float
    category: str
    first_onset_age: Optional[int]
    current_status: str
    symptom_details: Dict
    contributing_experience_ids: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SymptomHistoryResponse(BaseModel):
    id: str
    symptom_name: str
    severity_before: Optional[float]
    severity_after: Optional[float]
    age_at_change: Optional[int]
    trigger_type: Optional[str]
    trigger_id: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True


class DisorderInfoResponse(BaseModel):
    disorder_name: str
    full_name: str
    category: str
    dsm_code: str
    symptoms: List[str]
    severity_levels: Optional[List[str]] = None
    subtypes: Optional[List[str]] = None
    common_comorbidities: Optional[List[str]] = None


class AssessmentResponse(BaseModel):
    disorder_name: str
    severity: float
    onset_age: int
    category: str
    symptoms: Dict[str, float]
    contributing_experiences: List[str]


# ============================================
# SYMPTOM TRACKING ENDPOINTS
# ============================================

@router.get("/personas/{persona_id}/symptoms", response_model=List[SymptomResponse])
async def get_persona_symptoms(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all current symptoms for a persona.

    Returns list of disorders with severity, onset age, and detailed symptom breakdown.
    """
    # Verify persona ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get all symptoms
    symptoms = db.query(PersonaSymptom).filter(
        PersonaSymptom.persona_id == persona_id
    ).all()

    return symptoms


@router.get("/personas/{persona_id}/symptoms/{symptom_name}/history", response_model=List[SymptomHistoryResponse])
async def get_symptom_history(
    persona_id: str,
    symptom_name: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get timeline of symptom changes for a specific disorder.

    Shows how severity changed over time due to experiences and interventions.
    """
    # Verify persona ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get symptom history
    history = db.query(SymptomHistory).filter(
        SymptomHistory.persona_id == persona_id,
        SymptomHistory.symptom_name == symptom_name
    ).order_by(SymptomHistory.age_at_change).all()

    return history


@router.post("/personas/{persona_id}/symptoms/assess", response_model=List[AssessmentResponse])
async def assess_persona_symptoms(
    persona_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger comprehensive symptom assessment based on all experiences.

    Uses DSM-5/ICD-11 taxonomy to assess disorders and creates/updates
    PersonaSymptom records.

    Returns list of assessed disorders with severity and symptom breakdown.
    """
    # Verify persona ownership
    persona = db.query(Persona).filter(
        Persona.id == persona_id,
        Persona.user_id == user_id
    ).first()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get all experiences
    experiences = db.query(Experience).filter(
        Experience.persona_id == persona_id
    ).order_by(Experience.sequence_number).all()

    if not experiences:
        return []

    # Assess comprehensive symptoms
    assessment = assess_comprehensive_symptoms(
        experiences=experiences,
        current_age=persona.current_age,
        baseline_age=persona.baseline_age
    )

    # Update or create PersonaSymptom records
    results = []
    for disorder_name, details in assessment.items():
        # Check if symptom already exists
        existing_symptom = db.query(PersonaSymptom).filter(
            PersonaSymptom.persona_id == persona_id,
            PersonaSymptom.symptom_name == disorder_name
        ).first()

        if existing_symptom:
            # Record history before updating
            history_entry = SymptomHistory(
                persona_id=persona_id,
                symptom_id=existing_symptom.id,
                symptom_name=disorder_name,
                severity_before=existing_symptom.severity,
                severity_after=details["severity"],
                age_at_change=persona.current_age,
                trigger_type="assessment",
                trigger_id=None
            )
            db.add(history_entry)

            # Update existing
            existing_symptom.severity = details["severity"]
            existing_symptom.symptom_details = details["symptoms"]
            existing_symptom.contributing_experience_ids = details["contributing_experiences"]
            existing_symptom.updated_at = datetime.utcnow()
        else:
            # Create new symptom record
            new_symptom = PersonaSymptom(
                persona_id=persona_id,
                symptom_name=disorder_name,
                severity=details["severity"],
                category=details["category"],
                first_onset_age=details["onset_age"],
                current_status="active",
                symptom_details=details["symptoms"],
                contributing_experience_ids=details["contributing_experiences"]
            )
            db.add(new_symptom)

        results.append(AssessmentResponse(
            disorder_name=disorder_name,
            severity=details["severity"],
            onset_age=details["onset_age"],
            category=details["category"],
            symptoms=details["symptoms"],
            contributing_experiences=details["contributing_experiences"]
        ))

    db.commit()

    return results


# ============================================
# DISORDER TAXONOMY ENDPOINTS
# ============================================

@router.get("/disorders", response_model=List[str])
async def get_disorders():
    """
    Get list of all disorder names in the taxonomy.

    Returns list of disorder identifiers (e.g., 'depression', 'ptsd').
    """
    return get_all_disorders()


@router.get("/disorders/categories", response_model=List[str])
async def get_categories():
    """
    Get list of all disorder categories.

    Returns categories like 'Mood Disorders', 'Anxiety Disorders', etc.
    """
    return get_all_categories()


@router.get("/disorders/category/{category_name}", response_model=Dict[str, DisorderInfoResponse])
async def get_disorders_in_category(category_name: str):
    """
    Get all disorders in a specific category.

    Returns detailed information for each disorder in the category.
    """
    disorders = get_disorders_by_category(category_name)

    if not disorders:
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' not found")

    # Format response
    result = {}
    for disorder_name, info in disorders.items():
        result[disorder_name] = DisorderInfoResponse(
            disorder_name=disorder_name,
            full_name=info.get("full_name", disorder_name),
            category=info.get("category", ""),
            dsm_code=info.get("dsm_code", ""),
            symptoms=info.get("symptoms", []),
            severity_levels=info.get("severity_levels"),
            subtypes=info.get("subtypes"),
            common_comorbidities=info.get("common_comorbidities")
        )

    return result


@router.get("/disorders/{disorder_name}", response_model=DisorderInfoResponse)
async def get_disorder_info(disorder_name: str):
    """
    Get detailed information about a specific disorder.

    Returns DSM code, symptoms, subtypes, and comorbidities.
    """
    if disorder_name not in SYMPTOM_TAXONOMY:
        raise HTTPException(status_code=404, detail=f"Disorder '{disorder_name}' not found")

    info = SYMPTOM_TAXONOMY[disorder_name]

    return DisorderInfoResponse(
        disorder_name=disorder_name,
        full_name=info.get("full_name", disorder_name),
        category=info.get("category", ""),
        dsm_code=info.get("dsm_code", ""),
        symptoms=info.get("symptoms", []),
        severity_levels=info.get("severity_levels"),
        subtypes=info.get("subtypes"),
        common_comorbidities=info.get("common_comorbidities")
    )


@router.get("/disorders/{disorder_name}/symptoms", response_model=List[str])
async def get_disorder_symptom_list(disorder_name: str):
    """
    Get list of symptoms for a specific disorder.

    Returns list of symptom identifiers.
    """
    symptoms = get_disorder_symptoms(disorder_name)

    if not symptoms:
        raise HTTPException(status_code=404, detail=f"Disorder '{disorder_name}' not found")

    return symptoms


# ============================================
# INTERVENTION EFFECTIVENESS ENDPOINTS
# ============================================

class InterventionEffectivenessRequest(BaseModel):
    disorder: str
    intervention_type: str
    duration_weeks: int
    adherence: float = 0.8


class InterventionEffectivenessResponse(BaseModel):
    disorder: str
    intervention_type: str
    duration_weeks: int
    adherence: float
    expected_reduction: float
    reduction_percentage: str


@router.post("/interventions/effectiveness", response_model=InterventionEffectivenessResponse)
async def calculate_intervention_effectiveness(
    request: InterventionEffectivenessRequest
):
    """
    Calculate expected symptom reduction from a therapeutic intervention.

    Uses evidence-based effectiveness scores for different therapy types.
    """
    reduction = symptom_engine.calculate_intervention_effect(
        disorder=request.disorder,
        intervention_type=request.intervention_type,
        duration_weeks=request.duration_weeks,
        adherence=request.adherence
    )

    return InterventionEffectivenessResponse(
        disorder=request.disorder,
        intervention_type=request.intervention_type,
        duration_weeks=request.duration_weeks,
        adherence=request.adherence,
        expected_reduction=reduction,
        reduction_percentage=f"{int(reduction * 100)}%"
    )
