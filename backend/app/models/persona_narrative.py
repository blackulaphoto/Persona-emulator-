"""
Persona Narrative Model

Stores AI-generated comprehensive narratives about a persona's psychological journey.
Each generation creates a new record, allowing history tracking.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class PersonaNarrative(Base):
    """
    AI-generated narrative summaries of a persona's psychological development.
    
    Captures:
    - Life story and developmental timeline
    - Impact of experiences and traumas
    - Current behavioral patterns
    - Treatment effects and responses
    - Prognosis and recommendations
    """
    __tablename__ = "persona_narratives"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)  # Firebase UID
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_number = Column(Integer, nullable=False)  # 1st, 2nd, 3rd generation
    
    # Persona state at time of generation
    persona_age_at_generation = Column(Integer, nullable=False)
    total_experiences_count = Column(Integer, nullable=False)
    total_interventions_count = Column(Integer, nullable=False)
    
    # Narrative content (structured sections)
    executive_summary = Column(Text, nullable=False)  # 2-3 paragraph overview
    developmental_timeline = Column(Text, nullable=False)  # Chronological life story
    current_presentation = Column(Text, nullable=False)  # How they navigate the world
    treatment_response = Column(Text, nullable=True)  # Impact of interventions (if any)
    prognosis = Column(Text, nullable=False)  # Future outlook and recommendations
    
    # Full narrative (all sections combined)
    full_narrative = Column(Text, nullable=False)  # Complete markdown text
    
    # Generation metadata
    word_count = Column(Integer, nullable=False)
    generation_time_seconds = Column(Integer, nullable=True)  # Time to generate
    
    # Relationships
    persona = relationship("Persona", back_populates="narratives")

    def __repr__(self):
        return f"<PersonaNarrative(id={self.id}, persona_id={self.persona_id}, gen={self.generation_number})>"
