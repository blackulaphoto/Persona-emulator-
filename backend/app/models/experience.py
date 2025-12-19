"""Experience model representing life events."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Experience(Base):
    """
    Represents a life event that impacts the persona's development.
    """

    __tablename__ = "experiences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    
    # Sequencing
    sequence_number = Column(Integer, nullable=False)  # Order of events
    age_at_event = Column(Integer, nullable=False)
    
    # User input
    user_description = Column(Text, nullable=False)
    
    # AI-extracted metadata
    event_type = Column(String, nullable=True)  # "trauma", "loss", "achievement", "relationship"
    severity = Column(Integer, nullable=True)  # 1-10 AI-estimated
    support_available = Column(Boolean, nullable=True)
    
    # AI-generated analysis
    immediate_effects = Column(JSON, nullable=True)  # Personality changes right after
    long_term_patterns = Column(JSON, nullable=True)  # Predicted future impacts
    cross_experience_triggers = Column(JSON, nullable=True)  # Links to previous experiences
    coping_mechanisms = Column(JSON, nullable=True)  # New strategies developed
    worldview_shifts = Column(JSON, nullable=True)  # Trust, safety, self-worth changes
    
    # NEW: Symptom tracking
    symptoms_developed = Column(JSON, nullable=True, default=[])  # ["hoarding", "hypervigilance"]
    symptom_severity = Column(JSON, nullable=True, default={})  # {"hoarding": 8, "hypervigilance": 6}
    
    # NEW: Treatment recommendations
    recommended_therapies = Column(JSON, nullable=True, default=[])
    
    # Full AI reasoning
    ai_reasoning = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona = relationship("Persona", back_populates="experiences")
