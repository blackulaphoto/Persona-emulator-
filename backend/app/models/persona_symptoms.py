"""
Persona Symptoms Models

Track comprehensive mental health symptoms based on DSM-5/ICD-11 taxonomy.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, JSON, ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class PersonaSymptom(Base):
    """
    Track multiple symptoms and their severity over time for each persona.

    This allows tracking:
    - Multiple concurrent disorders (e.g., depression AND anxiety AND PTSD)
    - Symptom severity on 0-1 scale
    - Change over time as experiences/interventions are added
    """
    __tablename__ = "persona_symptoms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)

    # Symptom tracking
    symptom_name = Column(String(100), nullable=False)  # e.g., "depression", "narcissistic_personality"
    severity = Column(Float, nullable=False)  # 0.0 to 1.0
    category = Column(String(100))  # e.g., "Mood Disorders", "Personality Disorders"

    # Context
    first_onset_age = Column(Integer)  # Age when symptoms first appeared
    current_status = Column(String(50), default="active")  # "active", "in_remission", "resolved"

    # Detailed symptom breakdown (JSON for flexibility)
    symptom_details = Column(JSON, default={})  # e.g., {"suicidal_ideation": 0.3, "anhedonia": 0.7}

    # Contributing experiences
    contributing_experience_ids = Column(JSON, default=[])  # List of experience IDs that caused this

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    persona = relationship("Persona", back_populates="detailed_symptoms")
    history = relationship("SymptomHistory", back_populates="symptom", cascade="all, delete-orphan")


class SymptomHistory(Base):
    """
    Track how symptoms change over time.

    Creates a timeline of symptom severity changes as experiences
    and interventions are added.
    """
    __tablename__ = "symptom_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    symptom_id = Column(String, ForeignKey("persona_symptoms.id"), nullable=False, index=True)
    symptom_name = Column(String(100), nullable=False)

    # Snapshot
    severity_before = Column(Float)
    severity_after = Column(Float)
    age_at_change = Column(Integer)

    # What caused the change
    trigger_type = Column(String(50))  # "experience", "intervention", "time"
    trigger_id = Column(String)  # ID of the experience or intervention

    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symptom = relationship("PersonaSymptom", back_populates="history")
