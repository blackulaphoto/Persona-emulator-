"""Persona model representing a simulated person."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Persona(Base):
    """
    Represents a simulated person with baseline personality and evolving traits.
    """

    __tablename__ = "personas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Firebase UID, not a relational FK - there is no local `users` row per
    # Firebase user (auth is verified against Firebase on every request,
    # see app/core/auth.py; nothing in this app ever writes to the `users`
    # table). A ForeignKey("users.id") was here previously; harmless under
    # SQLite (which doesn't enforce FKs by default) but Postgres enforces
    # them strictly, and rejected every real persona create with
    # ForeignKeyViolation once Postgres was actually connected - confirmed
    # live. See migration that drops fk_personas_user_id.
    user_id = Column(String, nullable=False, index=True)
    
    # Basic info
    name = Column(String, nullable=False)
    baseline_age = Column(Integer, nullable=False)
    baseline_gender = Column(String, nullable=True)
    baseline_background = Column(Text, nullable=True)  # Early environment context
    
    # Current personality state (Big Five: 0.0 - 1.0 scale)
    # Immutable creation-time profile. Nullable for legacy rows because their
    # true baseline cannot be reconstructed once current_personality evolved.
    baseline_personality = Column(JSON, nullable=True)
    current_personality = Column(JSON, nullable=False, default={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5
    })
    
    # Current psychological state
    current_attachment_style = Column(String, nullable=False, default="secure")
    baseline_attachment_style = Column(String, nullable=True)
    baseline_attachment_dimensions = Column(JSON, nullable=True)
    current_attachment_dimensions = Column(JSON, nullable=False, default={})
    # Projection derived from ClinicalPatternHypothesis rows above the display
    # threshold. No module should write to this directly - see
    # clinical_pattern_hypothesis.py.
    current_trauma_markers = Column(JSON, nullable=False, default=[])
    # Fast-moving State tier (docs/MIGRATION_MAP.md, Step 11) - distinct from
    # current_personality (Trait, slow-moving). Keys are STATE_VARIABLES from
    # app/schemas/developmental_analysis_schemas.py: trust, threat_sensitivity,
    # mood, regulation, avoidance, relational_security. Starts empty, same as
    # current_trauma_markers, rather than seeded with a neutral baseline -
    # unearned defaults are exactly what this rebuild has removed elsewhere.
    # Not yet written by any pipeline - schema only until Step 11c.
    current_state = Column(JSON, nullable=False, default={})
    current_age = Column(Integer, nullable=False)  # Updates as experiences added
    foundational_environment_signals = Column(JSON, nullable=False, default={})
    baseline_initialized = Column(Boolean, nullable=False, default=False)

    # "case_subject" (default): interpretations describe the persona, never the
    # operator. "self_authored": explicitly-confirmed autobiographical mode -
    # must be set deliberately, never inferred from who is typing.
    narrative_mode = Column(String, nullable=False, default="case_subject")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Sharing (for future feature)
    is_public = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)
    
    # Relationships
    experiences = relationship("Experience", back_populates="persona", cascade="all, delete-orphan", order_by="Experience.sequence_number")
    interventions = relationship("Intervention", back_populates="persona", cascade="all, delete-orphan", order_by="Intervention.sequence_number")
    snapshots = relationship("PersonalitySnapshot", back_populates="persona", cascade="all, delete-orphan")
    timeline_snapshots = relationship("TimelineSnapshot", back_populates="persona", cascade="all, delete-orphan")
    narratives = relationship("PersonaNarrative", back_populates="persona", cascade="all, delete-orphan")
    detailed_symptoms = relationship("PersonaSymptom", back_populates="persona", cascade="all, delete-orphan")

    # Human Development Engine (see docs/MIGRATION_MAP.md)
    narration_records = relationship("NarrationRecord", back_populates="persona", cascade="all, delete-orphan")
    beliefs = relationship("PersonaBelief", back_populates="persona", cascade="all, delete-orphan")
    exposures = relationship("DevelopmentalExposure", back_populates="persona", cascade="all, delete-orphan")
    protective_factors = relationship("ProtectiveFactor", back_populates="persona", cascade="all, delete-orphan")
    adaptation_patterns = relationship("AdaptationPattern", back_populates="persona", cascade="all, delete-orphan")
    clinical_pattern_hypotheses = relationship("ClinicalPatternHypothesis", back_populates="persona", cascade="all, delete-orphan")
    interpretations = relationship("Interpretation", back_populates="persona", cascade="all, delete-orphan", foreign_keys="Interpretation.persona_id")
    functional_observations = relationship("FunctionalObservation", back_populates="persona", cascade="all, delete-orphan")
