"""
Narrative Schemas

Pydantic models for narrative API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenerateNarrativeRequest(BaseModel):
    """Request to generate a narrative (currently no body needed)"""
    pass


class NarrativeResponse(BaseModel):
    """Full narrative response with all sections"""
    id: str
    persona_id: str
    generated_at: datetime
    generation_number: int
    
    # Persona state at generation
    persona_age_at_generation: int
    total_experiences_count: int
    total_interventions_count: int
    
    # Narrative sections
    executive_summary: str
    developmental_timeline: str
    current_presentation: str
    treatment_response: Optional[str]
    prognosis: str
    
    # Full narrative
    full_narrative: str
    
    # Metadata
    word_count: int
    generation_time_seconds: Optional[int]
    
    class Config:
        from_attributes = True


class NarrativeListResponse(BaseModel):
    """Simplified narrative for list views"""
    id: str
    persona_id: str
    generated_at: datetime
    generation_number: int
    persona_age_at_generation: int
    total_experiences_count: int
    total_interventions_count: int
    executive_summary: str
    developmental_timeline: str
    current_presentation: str
    treatment_response: Optional[str]
    prognosis: str
    full_narrative: str
    word_count: int
    generation_time_seconds: Optional[int]

    class Config:
        from_attributes = True
