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
    # Family context, early life situation
    
    baseline_personality = Column(JSON, nullable=False)
    # Big Five traits as dict: {"openness": 0.5, ...}
    
    baseline_attachment_style = Column(String, nullable=False, default="secure")
    
    # Predefined experiences (JSON array)
    predefined_experiences = Column(JSON, nullable=False)
    # Array of experience objects:
    # [{
    #   "age": 7,
    #   "category": "family_conflict",
    #   "valence": "negative",
    #   "intensity": "severe",
    #   "description": "Parents divorce with high conflict...",
    #   "clinical_note": "Attachment disruption key factor"
    # }, ...]
    
    # Suggested interventions
    predefined_interventions = Column(JSON, nullable=True)
    # Optional array of intervention suggestions:
    # [{
    #   "age": 14,
    #   "therapy_type": "DBT",
    #   "duration": "1_year",
    #   "intensity": "weekly",
    #   "rationale": "Early intervention reduces symptom severity by 60%"
    # }, ...]
    
    # Expected outcomes
    expected_outcomes = Column(JSON, nullable=False)
    # Dict with expected final state:
    # {
    #   "personality_changes": {"neuroticism": 0.9, ...},
    #   "symptoms_developed": ["self-harm", "emotional_dysregulation", ...],
    #   "attachment_changes": "disorganized",
    #   "trauma_markers": ["trust_issues", "hypervigilance", ...]
    # }
    
    # Research citations
    citations = Column(JSON, nullable=True)
    # Array of citation strings:
    # ["Linehan (1993) - Biosocial theory of BPD", ...]
    
    # Remix suggestions (optional)
    remix_suggestions = Column(JSON, nullable=True)
    # Array of "what if" scenario suggestions:
    # [{
    #   "title": "Early DBT Intervention",
    #   "changes": ["Add DBT at age 14", "Remove 2 trauma experiences"],
    #   "hypothesis": "Early intervention reduces symptom severity by 60%"
    # }, ...]
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


