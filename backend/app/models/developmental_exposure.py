"""
Developmental exposure model.

Output of the Developmental Exposure Extractor: what a persona was exposed
to, and which developmental domains that exposure implicates. Deliberately
carries no disorder or diagnosis - that judgment belongs to the evidence
accumulator, built from many exposures, protective factors, and narration
signals accumulated over the timeline, never from a single exposure alone.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class DevelopmentalExposure(Base):
    """
    A single developmental exposure extracted from backstory text or an
    experience description.

    Example: "My father drank constantly and disappeared for days." produces
    exposures like "caregiver_substance_use", "caregiver_absence",
    "household_unpredictability", mapped to developmental_domains like
    "attachment_security", "emotional_safety", "stability".
    """
    __tablename__ = "developmental_exposures"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_event_id = Column(String, nullable=True)  # Experience.id, null if extracted from backstory

    source = Column(String(20), nullable=False)  # "backstory" | "experience" - WHICH pipeline stage this came from
    # WHO reported it - persona_voice | case_author | third_party_report | source_material
    # (app/models/narration.py's SPEAKER_ROLES). Unlike self-narration, exposure
    # extraction is NOT gated by speaker_role - a fact is a fact regardless of who
    # states it. This column exists for provenance/audit, not eligibility.
    speaker_role = Column(String(30), nullable=False, default="case_author")
    age_at_exposure = Column(Integer, nullable=True)

    exposure_type = Column(String(100), nullable=False)  # e.g. "caregiver_substance_use"
    developmental_domains = Column(JSON, nullable=False, default=[])  # e.g. ["attachment_security", "stability"]

    raw_text = Column(String, nullable=True)  # the phrase this was extracted from

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="exposures")
