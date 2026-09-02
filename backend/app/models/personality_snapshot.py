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
    # ondelete='CASCADE' on these two: Persona.experiences and Persona.snapshots
    # are independent cascade="all, delete-orphan" relationships on Persona, with
    # no ORM relationship() connecting Experience/Intervention to
    # PersonalitySnapshot - so SQLAlchemy's unit-of-work has no way to order a
    # delete-persona flush so snapshot rows go first. SQLite never enforced the
    # FK, so this was silently fine there; Postgres enforces it strictly and
    # rejected every persona delete with ForeignKeyViolation once a persona
    # had any snapshots - confirmed live. Cascading at the DB level removes the
    # ordering dependency entirely. See migration that adds these ondeletes.
    experience_id = Column(String, ForeignKey("experiences.id", ondelete="CASCADE"), nullable=True)
    intervention_id = Column(String, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=True)
    
    age = Column(Integer, nullable=False)
    
    # State at this point in time
    personality_profile = Column(JSON, nullable=False)  # Big Five (Trait tier)
    attachment_style = Column(String, nullable=False)
    attachment_dimensions = Column(JSON, nullable=True)
    trauma_markers = Column(JSON, nullable=False, default=[])
    symptom_severity = Column(JSON, nullable=False, default={})
    # Frozen copy of Persona.current_state (State tier) at snapshot time -
    # nullable like adaptation_patterns_snapshot/clinical_pattern_hypotheses_
    # snapshot (docs/MIGRATION_MAP.md, step 9) since old snapshots predate
    # this column and Step 11c hasn't wired a writer yet.
    state_profile = Column(JSON, nullable=True)
    
    # AI-generated summary
    narrative_summary = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona = relationship("Persona", back_populates="snapshots")
