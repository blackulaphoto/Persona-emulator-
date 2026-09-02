"""
Whole-Life Formulation V2 persistence models.

`WholeLifeFormulation` is the canonical source of truth for a V2-analyzed
persona's psychology - once a persona has one, existing tables
(adaptation_patterns, clinical_pattern_hypotheses, protective_factors,
persona_beliefs, personality_snapshots) become compatibility/serving-layer
projections of the latest ACCEPTED row here, not independently authoritative
(see app/services/whole_life_formulation/persistence_service.py).

`formulation_json` on that row contains ONLY the validated, enforcement-
passed formulation - every claim in it has already cleared
enforcement.enforce_validation(). Rejected/quarantined claims never appear
here; they're recorded separately in FormulationValidationReport, which is
internal-only and never serialized into any customer-facing API response.

Additive only - no existing table is touched, no existing table is dropped.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class WholeLifeFormulation(Base):
    __tablename__ = "whole_life_formulations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)

    engine_version = Column(String(30), nullable=False)  # persistence_service.WHOLE_LIFE_FORMULATION_ENGINE_VERSION, e.g. "v2" - independent of schema_version below
    schema_version = Column(String(30), nullable=False)  # WholeLifeFormulation.schema_version from the model call, e.g. "v2.2-final-stability-pass"
    generation_number = Column(Integer, nullable=False)  # 1, 2, 3... per persona, monotonically increasing
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_fingerprint = Column(String(64), nullable=False)  # sha256 of the exact assembled input bundle

    model_id = Column(String(100), nullable=False)  # the actual model string the API reported (response.model)

    # ACCEPTED formulation only - the full WholeLifeFormulation.model_dump(),
    # post-enforcement. Never contains a claim that failed enforcement.
    formulation_json = Column(JSON, nullable=False)

    # "accepted" | "superseded" - a persona's prior generations stay in this
    # table as history once a newer one is accepted; only the latest
    # "accepted" row per persona is what projections/current state reflect.
    status = Column(String(20), nullable=False, default="accepted")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    persona = relationship("Persona", back_populates="whole_life_formulations")


class FormulationValidationReport(Base):
    """
    Internal-only record of what enforcement did to one formulation attempt -
    every citation removed, every claim rejected, and (if the whole attempt
    was rejected) why. Never exposed through any customer-facing API
    response; exists purely for observability into the enforcement pipeline.
    """
    __tablename__ = "formulation_validation_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Set when the formulation was ultimately accepted (points at the row in
    # whole_life_formulations); null when the whole attempt was rejected and
    # no formulation row was ever created for it.
    formulation_id = Column(String, ForeignKey("whole_life_formulations.id", ondelete="CASCADE"), nullable=True, index=True)
    # Always set, even for a fully-rejected attempt that has no formulation_id -
    # this is what lets a rejected attempt still be traced to a persona.
    attempted_generation_id = Column(String(64), nullable=False, index=True)
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)

    claim_type = Column(String(30), nullable=False)  # "big_five" | "attachment" | "state" | "pattern" | "belief" | ...
    claim_ref = Column(String(150), nullable=False)  # claim id or "profile.field" path
    rule_violated = Column(String(50), nullable=False)
    action_taken = Column(String(30), nullable=False)  # "citation_removed" | "claim_rejected" | "formulation_rejected"
    rejection_reason = Column(String, nullable=False)
    raw_claim_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
