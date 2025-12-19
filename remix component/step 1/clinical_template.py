"""
Clinical Template Model

Stores pre-built clinical case templates demonstrating how specific personality disorders
or psychological conditions develop from particular combinations of experiences and
developmental timing.

Templates can be loaded to create personas with evidence-based developmental pathways.
"""
from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, ARRAY
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ClinicalTemplate(Base):
    """
    Pre-built clinical case templates showing disorder development pathways.
    
    Templates include:
    - Baseline personality configuration
    - Predefined experiences with timing
    - Suggested interventions
    - Expected outcomes
    - Clinical rationale and research citations
    
    Used for:
    - Educational demonstrations
    - Research simulations
    - Clinical training scenarios
    - "What if" analysis
    """
    __tablename__ = "clinical_templates"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template identification
    name = Column(String, nullable=False, index=True)
    # e.g., "Borderline Personality Disorder - Classic Development Pathway"
    
    disorder_type = Column(String, nullable=False, index=True)
    # e.g., "BPD", "C-PTSD", "DID", "Social_Anxiety", "MDD"
    
    description = Column(Text, nullable=False)
    # User-facing description of what this template demonstrates
    
    clinical_rationale = Column(Text, nullable=False)
    # Evidence-based explanation of why this pattern creates this disorder
    
    # Baseline configuration
    baseline_age = Column(Integer, nullable=False)
    baseline_gender = Column(String, nullable=True)
    baseline_background = Column(Text, nullable=False)
    baseline_personality = Column(JSON, nullable=False)
    # Big Five personality traits (0.0-1.0)
    
    baseline_attachment_style = Column(String, default="secure")
    
    # Predefined experiences
    predefined_experiences = Column(JSON, nullable=False)
    # Array of experience objects:
    # [{
    #   "age": 6,
    #   "category": "family",
    #   "valence": "negative",
    #   "intensity": "severe",
    #   "description": "...",
    #   "clinical_note": "Why this matters developmentally"
    # }, ...]
    
    # Suggested interventions
    predefined_interventions = Column(JSON, nullable=True)
    # Array of intervention suggestions:
    # [{
    #   "age": 16,
    #   "therapy_type": "DBT",
    #   "duration": "12_months",
    #   "rationale": "Why this therapy at this time"
    # }, ...]
    
    # Expected outcomes
    expected_outcomes = Column(JSON, nullable=False)
    # Predictions for different scenarios:
    # {
    #   "age_16_untreated": {
    #     "personality": {...},
    #     "symptoms": [...],
    #     "dsm_criteria_met": 7
    #   },
    #   "age_18_with_dbt": {
    #     "personality": {...},
    #     "symptoms": [...],
    #     "note": "Partial symptom relief expected"
    #   }
    # }
    
    # Research backing
    citations = Column(ARRAY(Text), nullable=True)
    # Array of research citations supporting this template
    
    # Remix suggestions
    remix_suggestions = Column(JSON, nullable=True)
    # Array of "what if" scenarios users can try:
    # [{
    #   "title": "Early Intervention",
    #   "changes": ["Add DBT at age 13 instead of 16"],
    #   "hypothesis": "Earlier intervention may prevent severe symptoms"
    # }, ...]
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ClinicalTemplate {self.name} ({self.disorder_type})>"
