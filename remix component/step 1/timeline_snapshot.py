"""
Timeline Snapshot Model

Stores saved "what if" scenarios when users modify template timelines.
Allows comparison between original template and modified versions.
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class TimelineSnapshot(Base):
    """
    Saved timeline modification scenarios for remix feature.
    
    When user modifies a template timeline (adds/removes experiences or interventions),
    this model stores the modified version for comparison with original.
    
    Enables "what if" analysis:
    - Original template timeline
    - "What if early intervention?"
    - "What if no family conflict?"
    - "What if supportive teacher added?"
    """
    __tablename__ = "timeline_snapshots"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    persona = relationship("Persona", back_populates="timeline_snapshots")
    
    template_id = Column(String, ForeignKey("clinical_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    template = relationship("ClinicalTemplate")
    
    # Snapshot identification
    label = Column(String, nullable=False)
    # e.g., "Original", "With Early DBT", "Without Family Conflict"
    
    description = Column(Text, nullable=True)
    # Optional user description of what was changed
    
    # Timeline modifications
    modified_experiences = Column(JSON, nullable=False)
    # Array of experience modifications:
    # [{
    #   "action": "add" | "remove" | "modify",
    #   "age": 10,
    #   "description": "...",
    #   "original_index": 2  # If removing/modifying
    # }, ...]
    
    modified_interventions = Column(JSON, nullable=True)
    # Array of intervention modifications:
    # [{
    #   "action": "add" | "remove" | "modify",
    #   "age": 13,
    #   "therapy_type": "DBT",
    #   "duration": "12_months",
    #   "original_index": 1
    # }, ...]
    
    # Resulting state
    personality_snapshot = Column(JSON, nullable=False)
    # Big Five personality after modifications:
    # {
    #   "openness": 0.5,
    #   "conscientiousness": 0.5,
    #   "extraversion": 0.4,
    #   "agreeableness": 0.5,
    #   "neuroticism": 0.68
    # }
    
    trauma_markers_snapshot = Column(JSON, nullable=True)
    # List of symptoms present: ["anxiety", "hypervigilance", ...]
    
    symptom_severity_snapshot = Column(JSON, nullable=True)
    # Symptom severity ratings: {"anxiety": 7, "hypervigilance": 6}
    
    # Comparison data
    personality_difference = Column(JSON, nullable=True)
    # Difference from baseline or original template:
    # {
    #   "neuroticism": -0.15,  # Improved
    #   "extraversion": 0.10    # Increased
    # }
    
    symptom_difference = Column(JSON, nullable=True)
    # Changes in symptom severity
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TimelineSnapshot '{self.label}' for persona {self.persona_id}>"
