"""
Protective factor model.

First-class developmental state, not a severity discount. A protective
factor can change what interpretation an exposure produces - a caregiver who
names what happened and reassures a child changes the meaning of the event,
not just its aftermath. Protective factors are joint input to the
Interpretation step alongside exposures, developmental context, and
narration signals - never applied afterward as `severity - protection`.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProtectiveFactor(Base):
    """
    A protective process or resource present during a persona's development.

    e.g. stable_alternate_caregiver, mentor, sibling_bond, temperament,
    community, financial_security, therapy, friendship, intelligence,
    spirituality, mastery_experience.
    """
    __tablename__ = "protective_factors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_event_id = Column(String, nullable=True)  # Experience.id this was described in, if any

    factor_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    # WHO reported it - see developmental_exposure.py's identical field for rationale.
    speaker_role = Column(String(30), nullable=False, default="case_author")

    active_from_age = Column(Integer, nullable=True)
    active_to_age = Column(Integer, nullable=True)  # null = ongoing

    domains_buffered = Column(JSON, nullable=False, default=[])  # developmental domains this touches

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="protective_factors")
