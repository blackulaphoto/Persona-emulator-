"""
Database Schema for Expanded Symptom Tracking

Add these tables/columns to support comprehensive mental health mapping
"""

from sqlalchemy import Column, String, Float, JSON, ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class PersonaSymptoms(Base):
    """
    Track multiple symptoms and their severity over time for each persona.
    
    This allows tracking:
    - Depression AND anxiety AND PTSD simultaneously
    - Symptom severity on 0-1 scale
    - Change over time as experiences/interventions are added
    """
    __tablename__ = "persona_symptoms"
    
    id = Column(String, primary_key=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    
    # Symptom tracking
    symptom_name = Column(String(100), nullable=False)  # e.g., "depression", "narcissistic_personality"
    severity = Column(Float, nullable=False)  # 0.0 to 1.0
    category = Column(String(100))  # e.g., "Mood Disorders", "Personality Disorders"
    
    # Context
    first_onset_age = Column(Integer)  # Age when symptoms first appeared
    current_status = Column(String(50))  # "active", "in_remission", "resolved"
    
    # Detailed symptom breakdown (JSON for flexibility)
    symptom_details = Column(JSON)  # e.g., {"suicidal_ideation": 0.3, "anhedonia": 0.7}
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    persona = relationship("Persona", back_populates="symptoms")


class SymptomHistory(Base):
    """
    Track how symptoms change over time.
    
    Creates a timeline of symptom severity changes as experiences
    and interventions are added.
    """
    __tablename__ = "symptom_history"
    
    id = Column(String, primary_key=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
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


class DisorderComorbidities(Base):
    """
    Track common comorbidities between disorders.
    
    e.g., Depression + Anxiety occur together
    """
    __tablename__ = "disorder_comorbidities"
    
    id = Column(String, primary_key=True)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    
    # Comorbid disorders
    primary_disorder = Column(String(100), nullable=False)
    comorbid_disorder = Column(String(100), nullable=False)
    
    # Relationship strength
    comorbidity_strength = Column(Float)  # How strongly they co-occur (0-1)
    
    # Clinical notes
    notes = Column(Text)


# Update Persona model to include relationship
"""
Add to backend/app/models/persona.py:

class Persona(Base):
    # ... existing fields ...
    
    # Add this relationship
    symptoms = relationship("PersonaSymptoms", back_populates="persona", cascade="all, delete-orphan")
"""
