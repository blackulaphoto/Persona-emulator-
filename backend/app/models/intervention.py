"""Intervention model for therapeutic treatments."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Intervention(Base):
    """
    Represents a therapeutic intervention applied to persona.
    """

    __tablename__ = "interventions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    
    # Sequencing
    sequence_number = Column(Integer, nullable=False)
    age_at_intervention = Column(Integer, nullable=False)
    
    # User-selected therapy
    therapy_type = Column(String, nullable=False)  # "CBT", "ACT", "EMDR", etc.
    duration = Column(String, nullable=False)  # "3 months", "1 year"
    intensity = Column(String, nullable=False)  # "weekly", "intensive", "as-needed"
    
    # Optional context
    user_notes = Column(Text, nullable=True)
    
    # AI-generated efficacy analysis
    target_symptoms = Column(JSON, nullable=True)  # What this therapy SHOULD help with
    actual_symptoms_targeted = Column(JSON, nullable=True)  # What persona has
    efficacy_match = Column(Float, nullable=True)  # 0.0-1.0 score
    
    # Outcome analysis
    immediate_effects = Column(JSON, nullable=True)  # Changes during treatment
    sustained_effects = Column(JSON, nullable=True)  # What persists after
    limitations = Column(JSON, nullable=True)  # What therapy can't address
    
    # Symptom changes
    symptom_changes = Column(JSON, nullable=True)  # {"hoarding": {"before": 8, "after": 4}}
    personality_changes = Column(JSON, nullable=True)  # Big Five shifts
    coping_skills_gained = Column(JSON, nullable=True)  # New tools learned
    
    # Full reasoning
    ai_reasoning = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona = relationship("Persona", back_populates="interventions")
