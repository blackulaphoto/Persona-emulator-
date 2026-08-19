"""
Interpretation model.

The per-event output of the core developmental chain: Exposure ->
Interpretation -> Adaptation -> Pattern -> Reinforcement -> Current
Behavior (see docs/MIGRATION_MAP.md). One row per meaningfully analyzed
experience, capturing what the engine infers the event meant to the persona
and what adaptive strategy it produced or reinforced - reasoned jointly from
the exposure (step 2), developmental context at that age, narration signals
(step 3), and any protective factors active at the time. Protective factors
are joint input here, not a discount applied after the fact.

Distinct from PersonaBelief (app/models/narration.py), which stores an
explicit causal claim the persona voices ("the divorce caused my BPD").
Interpretation is the engine's own inferred meaning-making, produced for
every meaningfully analyzed event whether or not the persona ever states a
belief about it. The gap between the two - what the persona believes vs.
what the engine infers from the full timeline - is deliberately preserved,
not collapsed.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Interpretation(Base):
    __tablename__ = "interpretations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False, index=True)
    source_event_id = Column(String, nullable=True)  # Experience.id; nullable for backstory-level interpretations
    age_at_event = Column(Integer, nullable=True)

    exposure_ids = Column(JSON, nullable=False, default=[])  # DevelopmentalExposure.id list this responds to
    developmental_domains = Column(JSON, nullable=False, default=[])  # domains judged salient at this age

    belief_statement = Column(Text, nullable=True)  # e.g. "People leave."
    adaptation_strategy = Column(String(50), nullable=True)  # controlled vocab, see pattern_engine.py
    reasoning = Column(Text, nullable=True)  # short developmental reasoning - the "WHY"

    protective_factor_ids = Column(JSON, nullable=False, default=[])  # ProtectiveFactor.id active at the time

    # Set once accumulate_patterns() groups this interpretation with others
    # sharing an adaptation_strategy. Null until a pattern exists to belong to.
    pattern_id = Column(String, ForeignKey("adaptation_patterns.id"), nullable=True)
    reinforcement_effect = Column(String(20), nullable=True)  # "originated" | "strengthened" | "weakened"

    # State/Trait proposals (docs/MIGRATION_MAP.md, Step 11) - the AI's per-event
    # reasoning about which fast-moving State variables and slow-moving Trait
    # (Big Five) dimensions this event implicates, as {direction, magnitude}
    # (Trait entries also carry evidence_strength). Never a raw number - see
    # app/schemas/developmental_analysis_schemas.py. Code applies bounded,
    # gated movement from these; the AI never states the new value directly.
    # Nullable/unpopulated until Step 11b's engine exists.
    state_implications = Column(JSON, nullable=True)
    trait_implications = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="interpretations")
    pattern = relationship("AdaptationPattern")
