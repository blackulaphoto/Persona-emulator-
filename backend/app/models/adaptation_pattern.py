"""
Adaptation pattern model.

Output of the Pattern/Adaptation engine: a named developmental pattern
(e.g. "Leave Before You're Left") built from the Exposure -> Interpretation
-> Adaptation -> Pattern -> Reinforcement chain. Descriptive developmental
pattern labels, not diagnoses.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class AdaptationPattern(Base):
    __tablename__ = "adaptation_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)

    pattern_name = Column(String(150), nullable=False)  # e.g. "Leave Before You're Left"
    description = Column(Text, nullable=True)
    # The grouping key pattern_engine.accumulate_patterns() uses (see
    # app/services/pattern_engine.py ADAPTATION_STRATEGIES) - e.g. "avoidance".
    # pattern_name is the evocative label; this is the underlying controlled-
    # vocabulary strategy it was built from.
    adaptation_strategy = Column(String(50), nullable=True)

    supporting_experience_ids = Column(JSON, nullable=False, default=[])
    first_emerged_age = Column(Integer, nullable=True)

    # Each entry: {"experience_id": ..., "age": ..., "effect": "strengthened" | "weakened"}
    reinforcement_history = Column(JSON, nullable=False, default=[])

    status = Column(String(30), nullable=False, default="emerging")  # emerging | established | weakening | resolved
    evidence_strength = Column(Float, nullable=True)  # 0.0-1.0, null until evidence exists

    current_manifestations = Column(JSON, nullable=False, default=[])  # relationships, work, coping, worldview

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="adaptation_patterns")
