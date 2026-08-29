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

    # Step 9 (docs/MIGRATION_MAP.md): frozen copies of pattern/hypothesis
    # state at snapshot time, the same way personality_snapshot freezes Big
    # Five at that moment - compare_snapshots() needs a point-in-time copy
    # to diff against, not a live reference that would change out from under
    # an old snapshot as new evidence accumulates.
    # Each entry: {"pattern_name", "adaptation_strategy", "status", "evidence_strength"}
    adaptation_patterns_snapshot = Column(JSON, nullable=True)
    # Each entry: {"pattern_key", "tier", "evidence_strength"}
    clinical_pattern_hypotheses_snapshot = Column(JSON, nullable=True)

    # Step 11f (docs/MIGRATION_MAP.md): frozen copy of Persona.current_state
    # (the fast-moving State tier - app/services/state_trait_engine.py) at
    # snapshot time, the same "point-in-time copy, not a live reference"
    # reasoning as adaptation_patterns_snapshot above. Nullable/omitted when
    # current_state was {} at snapshot time (no State movement earned yet).
    state_profile_snapshot = Column(JSON, nullable=True)

    # Frozen copy of Persona.current_attachment_style/current_attachment_
    # dimensions at snapshot time - same point-in-time-copy reasoning as
    # state_profile_snapshot above. Attachment was tracked live on Persona
    # since the attachment engine shipped but was never captured here, so
    # Compare could show State/Trait movement between two points in a life
    # but never attachment movement. Mirrors the Step 11f precedent.
    attachment_style_snapshot = Column(String, nullable=True)
    attachment_dimensions_snapshot = Column(JSON, nullable=True)

    # Difference calculations - NEW FIELDS to match service
    personality_difference = Column(JSON, nullable=True)  # Difference from baseline
    symptom_difference = Column(JSON, nullable=True)  # Symptom changes
    
    # Relationships
    persona = relationship("Persona", back_populates="timeline_snapshots")

    def __repr__(self):
        return f"<TimelineSnapshot(id={self.id}, persona_id={self.persona_id}, label={self.label})>"

