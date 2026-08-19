"""
Functional observation model.

Covers two of the evidence channels from docs/MIGRATION_MAP.md's "Evidence &
Source Model" that had no home until now: Behavior ("Timmy avoids physical
contact and becomes visibly tense when his father is mentioned") and Known
Outcomes (relationships, work, substance use, functioning). Both are
observations about CURRENT or ONGOING functioning, distinct from
DevelopmentalExposure (a dated historical event) and from NarrationRecord
(linguistic/narrative analysis of the persona's own words).

Unlike self-narration, functional observations are NOT gated by speaker_role
- a behavioral pattern is a fact-claim like an exposure, not evidence about
the persona's internal narrative, so anyone can validly report one (the
persona, a case author, a third party, source material). speaker_role is
still tracked for provenance/audit, matching DevelopmentalExposure and
ProtectiveFactor.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class FunctionalObservation(Base):
    __tablename__ = "functional_observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_event_id = Column(String, nullable=True)  # Experience.id, if tied to a specific point in the timeline

    speaker_role = Column(String(30), nullable=False, default="case_author")

    observation_type = Column(String(50), nullable=False)  # controlled vocab, see functional_observation_engine.py
    description = Column(Text, nullable=False)

    developmental_domains = Column(JSON, nullable=False, default=[])
    # Patterns (app/utils/symptom_taxonomy.py keys) this observation is candidate
    # evidence FOR - only populated for "concerning" valence. A "protective"
    # valence observation contradicts by domain overlap instead, the same
    # mechanism as ProtectiveFactor - see evidence_accumulator.py.
    candidate_pattern_keys = Column(JSON, nullable=False, default=[])
    valence = Column(String(20), nullable=False, default="neutral")  # "concerning" | "protective" | "neutral"

    age_observed = Column(Integer, nullable=True)  # nullable - many functional observations describe "currently"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="functional_observations")
