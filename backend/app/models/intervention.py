"""Intervention model for therapeutic treatments."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Intervention(Base):
    """
    Represents a therapeutic intervention applied to persona.
    """

    __tablename__ = "interventions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)  # Firebase UID
    
    # Sequencing
    sequence_number = Column(Integer, nullable=False)
    age_at_intervention = Column(Integer, nullable=False)
    
    # User-selected therapy
    therapy_type = Column(String, nullable=False)  # "CBT", "ACT", "EMDR", etc.
    duration = Column(String, nullable=False)  # "3 months", "1 year"
    intensity = Column(String, nullable=False)  # "weekly", "intensive", "as-needed"
    
    # Optional context
    user_notes = Column(Text, nullable=True)
    
    # AI-generated efficacy analysis
    target_symptoms = Column(JSON, nullable=True)  # What this therapy SHOULD help with
    actual_symptoms_targeted = Column(JSON, nullable=True)  # What persona has
    efficacy_match = Column(Float, nullable=True)  # 0.0-1.0 score
    
    # Outcome analysis
    immediate_effects = Column(JSON, nullable=True)  # Changes during treatment
    sustained_effects = Column(JSON, nullable=True)  # What persists after
    limitations = Column(JSON, nullable=True)  # What therapy can't address
    
    # Symptom changes
    symptom_changes = Column(JSON, nullable=True)  # {"hoarding": {"before": 8, "after": 4}}
    # Step 11e: no longer the AI's raw, independently-decided Big Five
    # values applied unconditionally - now set to a snapshot of
    # persona.current_personality AFTER state_trait_engine's gated update
    # (see app/api/routes/interventions.py). Real, honest, but usually
    # unchanged from before this intervention, since Trait movement from
    # therapy requires the sustained-improvement gate to be open - see
    # app/services/state_trait_engine.py's intervention_trait_gate_open.
    personality_changes = Column(JSON, nullable=True)  # Big Five shifts
    coping_skills_gained = Column(JSON, nullable=True)  # New tools learned

    # Step 11e (docs/MIGRATION_MAP.md): the AdaptationPattern.adaptation_strategy
    # this intervention was matched against at write time (see
    # intervention_engine._select_targeted_pattern), if any established
    # pattern existed for this persona. Null when no established pattern was
    # eligible - most importantly, for every intervention created before this
    # step. Used to look up this persona's prior interventions targeting the
    # same pattern, which is what state_trait_engine.intervention_trait_gate_
    # open checks for "sustained" improvement.
    targeted_adaptation_strategy = Column(String(50), nullable=True)
    # State/Trait proposal actually produced for this intervention (mirrors
    # Interpretation.state_implications/trait_implications from Step 11a) -
    # trait_implications is the proposal regardless of whether the gate was
    # open; what was actually APPLIED is only inferable via personality_
    # changes / the persona's snapshot, same convention as the developmental
    # engine.
    state_implications = Column(JSON, nullable=True)
    trait_implications = Column(JSON, nullable=True)

    # Full reasoning
    ai_reasoning = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona = relationship("Persona", back_populates="interventions")
