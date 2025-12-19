"""Personality snapshot model for comparison over time."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class PersonalitySnapshot(Base):
    """
    Stores personality state after each experience/intervention for comparison.
    """

    __tablename__ = "personality_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    experience_id = Column(String, ForeignKey("experiences.id"), nullable=True)
    intervention_id = Column(String, ForeignKey("interventions.id"), nullable=True)
    
    age = Column(Integer, nullable=False)
    
    # State at this point in time
    personality_profile = Column(JSON, nullable=False)  # Big Five
    attachment_style = Column(String, nullable=False)
    trauma_markers = Column(JSON, nullable=False, default=[])
    symptom_severity = Column(JSON, nullable=False, default={})
    
    # AI-generated summary
    narrative_summary = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona = relationship("Persona", back_populates="snapshots")
