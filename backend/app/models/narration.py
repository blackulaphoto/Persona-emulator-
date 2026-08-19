"""
Narration models.

Separates WHAT happened (developmental history) from WHO is describing it and
HOW. Every narration-derived record must declare its speaker_role and the
persona it attaches to (subject_id) - the schema has no slot for "the user"
as a psychological subject, only for the persona. Interpretations attach to
subject_id; they are never inferred to describe whoever is operating the app.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


# Valid speaker_role values:
#   "persona_voice"       - the case subject's own words / self-report
#   "case_author"         - the operator describing the persona in third person
#   "third_party_report"  - e.g. "his mother reports he was always withdrawn"
#   "source_material"     - clinical notes, records, or other documents fed in
SPEAKER_ROLES = ("persona_voice", "case_author", "third_party_report", "source_material")


class NarrationRecord(Base):
    """
    A piece of text attributed to a specific speaker, analyzed for narrative/
    linguistic signals (minimization, contradiction, normalization, agency
    language, idealization/devaluation, omissions, etc). These signals are
    evidence about defenses, schemas, and attribution style - never
    conclusions or diagnoses on their own.
    """
    __tablename__ = "narration_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_event_id = Column(String, nullable=True)  # Experience.id this text came from, if any

    speaker_role = Column(String(30), nullable=False)  # one of SPEAKER_ROLES
    attributed_to_persona = Column(Boolean, nullable=False, default=False)  # speaker_role == "persona_voice"

    raw_text = Column(Text, nullable=False)

    # Structured findings only - minimization, magnification, normalization,
    # absolutist language, idealization/devaluation, self-blame/other-blame,
    # contradictions, emotional vocabulary richness/absence, agency language
    # ("I chose" vs "it happened to me"), vague chronology, omissions, etc.
    # Each entry: {"signal_type": ..., "evidence_text": ..., "note": ...}
    linguistic_signals = Column(JSON, nullable=False, default=[])

    # Higher-level interpretive hypotheses built from the signals above, e.g.
    # {"hypothesis": "Protective narrative: 'it wasn't that bad'",
    #  "likely_function": ..., "potential_later_cost": ..., "supporting_signals": [...]}
    # Explicitly hypotheses, not conclusions - the evidence accumulator (step 4)
    # is what earns or revises confidence in these over time, not this record.
    candidate_hypotheses = Column(JSON, nullable=False, default=[])

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="narration_records")


class PersonaBelief(Base):
    """
    A belief the persona holds about their own history, distinct from what the
    timeline actually shows. Always derived from a persona_voice NarrationRecord
    unless the persona's narrative_mode is explicitly self-authored.

    Stores three realities side by side:
      1. What happened      -> DevelopmentalExposure / Experience timeline
      2. What persona believes happened -> this record (belief_text)
      3. What the engine infers -> engine_interpretation
    """
    __tablename__ = "persona_beliefs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_narration_id = Column(String, ForeignKey("narration_records.id"), nullable=True)

    speaker_role = Column(String(30), nullable=False, default="persona_voice")
    attributed_to_persona = Column(Boolean, nullable=False, default=True)

    belief_text = Column(Text, nullable=False)  # "The divorce caused my BPD"
    narrative_theme = Column(String(100), nullable=True)  # e.g. "single-event causal explanation"

    # strongly_supported | supported | plausible | partially_supported |
    # weakly_supported | contradicted
    timeline_evaluation = Column(String(30), nullable=True)
    engine_interpretation = Column(Text, nullable=True)  # e.g. "instability predates divorce"
    related_event_ids = Column(JSON, nullable=False, default=[])

    # Persistence of the explanation itself is developmental data - a belief
    # restated at 14, 22, and 31 is a different fact than one stated once.
    restated_count = Column(Integer, nullable=False, default=1)
    last_restated_age = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="beliefs")
