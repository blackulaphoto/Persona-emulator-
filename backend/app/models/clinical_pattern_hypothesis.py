"""
Clinical pattern hypothesis model.

The evidence accumulator's canonical state: for each pattern worth
investigating, tracks supporting and contradicting evidence over time and
can revise its own confidence as new information arrives. This is the single
writer for symptom/pattern state - Persona.current_trauma_markers becomes a
read-only projection derived from hypotheses above a tier threshold, and no
other module writes to it directly.

Evidence strength must be earned from persistence, corroborating symptoms,
narrative signals, and functional impact - never seeded at creation from a
static exposure->disorder lookup table. Those tables (see
app/utils/symptom_assessment_engine.py) only decide which hypotheses are
worth opening; they never set how strongly to believe them.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


# Tier progression as evidence accumulates. Neither tier implies a clinical
# diagnosis.
#   "developmental_pattern"        - earliest evidence, purely descriptive
#   "clinical_pattern_resemblance" - meaningful evidence accumulated
TIERS = ("developmental_pattern", "clinical_pattern_resemblance")


class ClinicalPatternHypothesis(Base):
    __tablename__ = "clinical_pattern_hypotheses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)

    pattern_key = Column(String(100), nullable=False)  # references app/utils/symptom_taxonomy.py keys where applicable
    tier = Column(String(30), nullable=False, default="developmental_pattern")

    # Each entry: {"type": "symptom"|"narrative"|"persistence"|"functional_impact",
    #              "description": ..., "source_id": ..., "age": ...}
    supporting_evidence = Column(JSON, nullable=False, default=[])
    contradicting_evidence = Column(JSON, nullable=False, default=[])

    developmental_precursors = Column(JSON, nullable=False, default=[])
    current_manifestations = Column(JSON, nullable=False, default=[])

    # Null at hypothesis creation - populated only once real evidence accumulates.
    evidence_strength = Column(Float, nullable=True)

    # Step 12: the value evidence_strength held before the most recent
    # recomputation, so the board can show a hypothesis STRENGTHENING or
    # WEAKENING rather than just its current number. `status`
    # (open/revised/dismissed) tracks whether the hypothesis has been revisited
    # at all, not which way it moved - these are different questions. Null
    # until a hypothesis has been recomputed at least once.
    previous_evidence_strength = Column(Float, nullable=True)

    opened_at_age = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="open")  # open | revised | resolved | dismissed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="clinical_pattern_hypotheses")
