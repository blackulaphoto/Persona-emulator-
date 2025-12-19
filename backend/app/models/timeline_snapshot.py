"""
Timeline Snapshot Model - FIXED VERSION

Corrected schema to match remix_service.py usage exactly.
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class TimelineSnapshot(Base):
    """
    Timeline snapshots for comparison.
    
    Saves persona state at a specific point for "what if" comparisons.
    Field names match remix_service.py usage exactly.
    """
    __tablename__ = "timeline_snapshots"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    template_id = Column(String, nullable=True)  # Optional: if created from template
    
    # Snapshot metadata
    label = Column(String, nullable=False)  # e.g., "Original", "With Early DBT"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Modified timeline data
    modified_experiences = Column(JSON, nullable=False, default=list)
    modified_interventions = Column(JSON, nullable=True)
    
    # Snapshot state - CORRECTED FIELD NAMES to match service
    personality_snapshot = Column(JSON, nullable=False)  # Was: snapshot_personality
    trauma_markers_snapshot = Column(JSON, nullable=True)  # Was: snapshot_symptoms
    symptom_severity_snapshot = Column(JSON, nullable=True)  # Was: snapshot_symptom_severity
    
    # Difference calculations - NEW FIELDS to match service
    personality_difference = Column(JSON, nullable=True)  # Difference from baseline
    symptom_difference = Column(JSON, nullable=True)  # Symptom changes
    
    # Relationships
    persona = relationship("Persona", back_populates="timeline_snapshots")

    def __repr__(self):
        return f"<TimelineSnapshot(id={self.id}, persona_id={self.persona_id}, label={self.label})>"

