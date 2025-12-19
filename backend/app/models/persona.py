"""Persona model representing a simulated person."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Persona(Base):
    """
    Represents a simulated person with baseline personality and evolving traits.
    """

    __tablename__ = "personas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)  # Nullable for MVP (no auth)
    
    # Basic info
    name = Column(String, nullable=False)
    baseline_age = Column(Integer, nullable=False)
    baseline_gender = Column(String, nullable=True)
    baseline_background = Column(Text, nullable=True)  # Family context, early life
    
    # Current personality state (Big Five: 0.0 - 1.0 scale)
    current_personality = Column(JSON, nullable=False, default={
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5
    })
    
    # Current psychological state
    current_attachment_style = Column(String, nullable=False, default="secure")
    current_trauma_markers = Column(JSON, nullable=False, default=[])
    current_age = Column(Integer, nullable=False)  # Updates as experiences added
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Sharing (for future feature)
    is_public = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="personas")
    experiences = relationship("Experience", back_populates="persona", cascade="all, delete-orphan", order_by="Experience.sequence_number")
    interventions = relationship("Intervention", back_populates="persona", cascade="all, delete-orphan", order_by="Intervention.sequence_number")
    snapshots = relationship("PersonalitySnapshot", back_populates="persona", cascade="all, delete-orphan")
    timeline_snapshots = relationship("TimelineSnapshot", back_populates="persona", cascade="all, delete-orphan")
    narratives = relationship("PersonaNarrative", back_populates="persona", cascade="all, delete-orphan")
