"""
Pydantic Schemas for Clinical Templates

Following the pattern from app/schemas/__init__.py (T7)
Add these to your existing schemas file or create templates_schemas.py
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from datetime import datetime


# Template Schemas

class TemplateExperienceSchema(BaseModel):
    """Schema for predefined experience in template"""
    age: int
    category: str
    valence: str  # "negative", "positive", "neutral"
    intensity: str  # "mild", "moderate", "severe"
    description: str
    clinical_note: Optional[str] = None


class TemplateInterventionSchema(BaseModel):
    """Schema for suggested intervention in template"""
    age: int
    therapy_type: str
    duration: str
    intensity: str
    rationale: str


class RemixSuggestionSchema(BaseModel):
    """Schema for 'what if' remix suggestion"""
    title: str
    changes: List[str]
    hypothesis: str


class ExpectedOutcomeSchema(BaseModel):
    """Schema for expected outcome scenario"""
    personality: Dict[str, float]
    symptoms: List[str]
    symptom_severity: Optional[Dict[str, int]] = None
    dsm_criteria_met: Optional[int] = None
    note: str


class ClinicalTemplateResponse(BaseModel):
    """Response schema for clinical template"""
    id: str
    name: str
    disorder_type: str
    description: str
    clinical_rationale: str
    
    baseline_age: int
    baseline_gender: Optional[str] = None
    baseline_background: str
    baseline_personality: Dict[str, float]
    baseline_attachment_style: str
    
    predefined_experiences: List[Dict]
    predefined_interventions: Optional[List[Dict]] = None
    expected_outcomes: Dict[str, Dict]
    
    citations: Optional[List[str]] = None
    remix_suggestions: Optional[List[Dict]] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ClinicalTemplateListResponse(BaseModel):
    """Simplified schema for template list view"""
    id: str
    name: str
    disorder_type: str
    description: str
    baseline_age: int
    experience_count: int
    intervention_count: int
    remix_suggestion_count: int
    
    model_config = {"from_attributes": True}


class CreatePersonaFromTemplateRequest(BaseModel):
    """Request to create persona from template"""
    template_id: str = Field(..., description="ID of template to use")
    custom_name: Optional[str] = Field(None, description="Custom name for persona (overrides template default)")
    owner_id: Optional[str] = Field(None, description="Owner ID if using auth")


class CreatePersonaFromTemplateResponse(BaseModel):
    """Response after creating persona from template"""
    persona_id: str
    template_id: str
    template_name: str
    persona_name: str
    baseline_age: int
    baseline_personality: Dict[str, float]
    predefined_experiences_available: int
    suggested_interventions_available: int
    message: str = "Persona created from template. Use experience and intervention APIs to add events."


class ApplyExperienceSetRequest(BaseModel):
    """Request to apply multiple predefined experiences"""
    template_id: str = Field(..., description="Template ID to get experiences from")
    experience_indices: Optional[List[int]] = Field(
        None, 
        description="Indices of experiences to apply (0-based). If None, applies all."
    )
    
    @field_validator('experience_indices')
    @classmethod
    def validate_indices(cls, v):
        if v is not None and any(i < 0 for i in v):
            raise ValueError("Experience indices must be non-negative")
        return v


class ApplyExperienceSetResponse(BaseModel):
    """Response after applying experience set"""
    persona_id: str
    experiences_applied: int
    experience_ids: List[str]
    personality_before: Dict[str, float]
    personality_after: Dict[str, float]
    symptoms_developed: List[str]
    current_age: int


class ApplyInterventionSetRequest(BaseModel):
    """Request to apply suggested interventions"""
    template_id: str
    intervention_indices: Optional[List[int]] = Field(
        None,
        description="Indices of interventions to apply. If None, applies all."
    )
    
    @field_validator('intervention_indices')
    @classmethod
    def validate_indices(cls, v):
        if v is not None and any(i < 0 for i in v):
            raise ValueError("Intervention indices must be non-negative")
        return v


class ApplyInterventionSetResponse(BaseModel):
    """Response after applying intervention set"""
    persona_id: str
    interventions_applied: int
    intervention_ids: List[str]
    symptom_changes: Dict[str, int]
    personality_changes: Dict[str, float]


# Timeline Snapshot Schemas

class TimelineModification(BaseModel):
    """Schema for a single timeline modification"""
    action: str = Field(..., description="add|remove|modify")
    event_type: str = Field(..., description="experience|intervention")
    age: int
    description: Optional[str] = None
    original_index: Optional[int] = Field(None, description="Index if removing/modifying existing")


class CreateTimelineSnapshotRequest(BaseModel):
    """Request to save a timeline remix scenario"""
    persona_id: str
    template_id: Optional[str] = None
    label: str = Field(..., description="Label for this scenario (e.g., 'Original', 'With Early DBT')")
    description: Optional[str] = Field(None, description="Optional description of changes")
    modifications: List[TimelineModification] = Field(
        ..., 
        description="List of modifications made to timeline"
    )


class TimelineSnapshotResponse(BaseModel):
    """Response schema for timeline snapshot"""
    id: str
    persona_id: str
    template_id: Optional[str] = None
    label: str
    description: Optional[str] = None
    
    modified_experiences: List[Dict]
    modified_interventions: Optional[List[Dict]] = None
    
    personality_snapshot: Dict[str, float]
    trauma_markers_snapshot: Optional[List[str]] = None
    symptom_severity_snapshot: Optional[Dict[str, int]] = None
    
    personality_difference: Optional[Dict[str, float]] = None
    symptom_difference: Optional[Dict[str, int]] = None
    
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CompareSnapshotsRequest(BaseModel):
    """Request to compare two timeline snapshots"""
    snapshot_id_1: str
    snapshot_id_2: str


class CompareSnapshotsResponse(BaseModel):
    """Response comparing two timeline snapshots"""
    snapshot_1: TimelineSnapshotResponse
    snapshot_2: TimelineSnapshotResponse
    
    personality_differences: Dict[str, Dict[str, float]]  # {"trait": {"snapshot_1": 0.5, "snapshot_2": 0.7, "difference": 0.2}}
    symptom_differences: Dict[str, Dict[str, int]]
    
    summary: str  # Plain-English comparison summary


