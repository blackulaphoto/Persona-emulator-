"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator


class PersonalityTraits(BaseModel):
    """Big Five personality traits (0.0-1.0 scale)."""
    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)


class PersonaCreate(BaseModel):
    """Schema for creating a new persona."""
    name: str = Field(min_length=1, max_length=100)
    baseline_age: int = Field(ge=0, le=120)
    baseline_gender: str = Field(min_length=1, max_length=50)
    baseline_background: str = Field(min_length=1, max_length=1000)
    baseline_personality: Optional[PersonalityTraits] = None
    baseline_attachment_style: Optional[str] = Field(default="secure")


class PersonaUpdate(BaseModel):
    """Schema for updating persona details."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    baseline_background: Optional[str] = Field(None, min_length=1, max_length=1000)


class PersonaResponse(BaseModel):
    """Schema for persona response."""
    id: str
    name: str
    baseline_age: int
    current_age: int
    baseline_gender: str
    baseline_background: str
    current_personality: Dict[str, float]
    current_attachment_style: str
    current_trauma_markers: List[str]
    experiences_count: int
    interventions_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExperienceCreate(BaseModel):
    """Schema for creating a new experience."""
    user_description: str = Field(min_length=1, max_length=2000)
    age_at_event: int = Field(ge=0, le=120)


class ExperienceResponse(BaseModel):
    """Schema for experience response."""
    id: str
    persona_id: str
    sequence_number: int
    age_at_event: int
    user_description: str
    immediate_effects: Optional[Dict] = None
    long_term_patterns: Optional[List[str]] = None
    symptoms_developed: Optional[List[str]] = None
    symptom_severity: Optional[Dict[str, int]] = None
    coping_mechanisms: Optional[List[str]] = None
    worldview_shifts: Optional[Dict[str, float]] = None
    cross_experience_triggers: Optional[List[str]] = None
    recommended_therapies: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterventionCreate(BaseModel):
    """Schema for creating a new intervention."""
    therapy_type: str = Field(pattern="^(CBT|ACT|EMDR|IFS|DBT|Somatic_Experiencing|Psychodynamic|ERP)$")
    duration: str = Field(pattern="^(3_months|6_months|1_year|2_years)$", description="Duration of therapy")
    intensity: str = Field(pattern="^(weekly|twice_weekly|monthly)$")
    age_at_intervention: int = Field(ge=0, le=120)
    user_notes: Optional[str] = None


class InterventionResponse(BaseModel):
    """Schema for intervention response."""
    id: str
    persona_id: str
    sequence_number: int
    therapy_type: str
    duration: str
    intensity: str
    age_at_intervention: int
    user_notes: Optional[str] = None
    actual_symptoms_targeted: Optional[List[str]] = None
    efficacy_match: Optional[float] = None
    immediate_effects: Optional[Dict] = None
    sustained_effects: Optional[Dict] = None
    limitations: Optional[List[str]] = None
    symptom_changes: Optional[Dict[str, int]] = None
    personality_changes: Optional[Dict[str, float]] = None
    coping_skills_gained: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PersonalitySnapshotResponse(BaseModel):
    """Schema for personality snapshot response."""
    id: str
    persona_id: str
    age: int
    personality_profile: Dict[str, float]
    attachment_style: str
    trauma_markers: List[str]
    symptom_severity: Optional[Dict[str, int]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    """Schema for persona timeline response."""
    persona: PersonaResponse
    experiences: List[ExperienceResponse]
    interventions: List[InterventionResponse]
    snapshots: List[PersonalitySnapshotResponse]
