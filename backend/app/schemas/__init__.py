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


class AdaptationPatternSummary(BaseModel):
    """
    One earned developmental adaptation, as surfaced on the persona board
    (Step 12). status moves emerging -> established (or weakening/resolved)
    as evidence accumulates; confidence is the same evidence_strength the
    engine reasons with, expressed 0-100 for display.
    """
    adaptation_strategy: Optional[str] = None
    pattern_name: str
    status: str
    evidence_strength: Optional[float] = None
    confidence: Optional[int] = None
    first_emerged_age: Optional[int] = None
    reinforcement_history: List[Dict] = Field(default_factory=list)


class ClinicalPatternHypothesisSummary(BaseModel):
    """
    One evolving clinical-pattern hypothesis (Step 12).

    Explicitly NOT a diagnosis and never presented as one - `confidence` is
    how strongly the persona's currently-known history matches this pattern,
    and it is expected to move both up and down as evidence arrives. Unlike
    current_trauma_markers (which stays gated behind DISPLAY_THRESHOLD),
    these surface as soon as there is any real evidence, so the user can
    watch the engine form and revise a hypothesis instead of only seeing
    conclusions it already considers settled.
    """
    pattern_key: str
    tier: str
    status: str
    evidence_strength: Optional[float] = None
    confidence: Optional[int] = None
    direction: Optional[str] = None
    opened_at_age: Optional[int] = None
    developmental_precursors: List[str] = Field(default_factory=list)
    supporting_evidence: List[Dict] = Field(default_factory=list)
    contradicting_evidence: List[Dict] = Field(default_factory=list)
    evidence_count: int = 0


class InterpretationResponse(BaseModel):
    id: str
    source_event_id: Optional[str] = None
    belief_statement: Optional[str] = None
    adaptation_strategy: Optional[str] = None
    reasoning: Optional[str] = None
    state_implications: Optional[Dict] = None
    trait_implications: Optional[Dict] = None


class ExperiencePatternLink(BaseModel):
    pattern_id: str
    pattern_name: str
    adaptation_strategy: Optional[str] = None
    effect: str
    age: Optional[int] = None
    current_status: str
    current_evidence_strength: Optional[float] = None


class ExperienceHypothesisLink(BaseModel):
    hypothesis_id: str
    pattern_key: str
    evidence_role: str
    evidence: List[Dict] = Field(default_factory=list)
    current_strength: Optional[float] = None
    direction: Optional[str] = None
    evidence_count: int = 0


class PersonaResponse(BaseModel):
    """Schema for persona response."""
    id: str
    name: str
    baseline_age: int
    current_age: int
    baseline_gender: str
    baseline_background: str
    baseline_personality: Optional[Dict[str, float]] = None
    current_personality: Dict[str, float]
    personality_delta: Optional[Dict[str, float]] = None
    current_attachment_style: str
    baseline_attachment_style: Optional[str] = None
    baseline_attachment_dimensions: Dict[str, float] = Field(default_factory=dict)
    current_attachment_dimensions: Dict[str, float] = Field(default_factory=dict)
    attachment_delta: Dict[str, float] = Field(default_factory=dict)
    attachment_style_semantics: str = "derived_from_developmental_dimensions"
    current_trauma_markers: List[str]
    # Step 11f (docs/MIGRATION_MAP.md): the State tier (app/services/
    # state_trait_engine.py) - fast-moving, reactive psychological state,
    # distinct from current_personality (the slow, gated Trait tier). Has
    # been written to the DB since Step 11c; this is the first route that
    # actually exposes it. Optional/nullable because current_state starts
    # at {} and a persona with no earned State movement yet has nothing to
    # show - not the same as an unearned 0.5 baseline for every variable.
    current_state: Optional[Dict[str, float]] = None
    foundational_environment_signals: Dict = Field(default_factory=dict)
    narrative_mode: str = "case_subject"
    # Step 12: the adaptation/hypothesis layers were computed and persisted
    # since Step 11c but had no API surface at all, so the board could only
    # ever render Big Five + current_trauma_markers - which is why a persona
    # whose narrative described heightened threat sensitivity and avoidance
    # still displayed "All is well right now". Exposed here as evolving,
    # confidence-carrying hypotheses rather than gated-until-certain labels.
    adaptation_patterns: List["AdaptationPatternSummary"] = Field(default_factory=list)
    clinical_pattern_hypotheses: List["ClinicalPatternHypothesisSummary"] = Field(default_factory=list)
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
    sequence_index: Optional[int] = Field(None, ge=1)


class ExperienceUpdate(BaseModel):
    user_description: Optional[str] = Field(None, min_length=1, max_length=2000)
    age_at_event: Optional[int] = Field(None, ge=0, le=120)
    sequence_index: Optional[int] = Field(None, ge=1)


class BatchExperienceItem(BaseModel):
    age_at_event: int = Field(ge=0, le=120)
    sequence_index: Optional[int] = Field(None, ge=1)
    description: str = Field(min_length=1, max_length=2000)


class BatchExperienceCreate(BaseModel):
    experiences: List[BatchExperienceItem] = Field(min_length=1, max_length=100)


class BatchExperienceItemResult(BaseModel):
    input_index: int
    status: str
    result: Optional["ExperienceResponse"] = None
    error: Optional[str] = None


class BatchExperienceResponse(BaseModel):
    results: List[BatchExperienceItemResult]
    processed_count: int
    failed_count: int


class ExperienceResponse(BaseModel):
    """Schema for experience response."""
    id: str
    persona_id: str
    sequence_number: int
    sequence_index: int
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
    interpretation: Optional[InterpretationResponse] = None
    pattern_connections: List[ExperiencePatternLink] = Field(default_factory=list)
    hypothesis_connections: List[ExperienceHypothesisLink] = Field(default_factory=list)
    protective_factors: List["ProtectiveFactorResponse"] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProtectiveFactorResponse(BaseModel):
    id: str
    factor_type: str
    description: Optional[str] = None
    domains_buffered: List[str] = Field(default_factory=list)
    source_event_id: Optional[str] = None
    active_from_age: Optional[int] = None
    active_to_age: Optional[int] = None
    speaker_role: str


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
    attachment_dimensions: Optional[Dict[str, float]] = None
    trauma_markers: List[str]
    symptom_severity: Optional[Dict[str, int]] = None
    state_profile: Optional[Dict[str, float]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    """Schema for persona timeline response."""
    persona: PersonaResponse
    experiences: List[ExperienceResponse]
    interventions: List[InterventionResponse]
    snapshots: List[PersonalitySnapshotResponse]
