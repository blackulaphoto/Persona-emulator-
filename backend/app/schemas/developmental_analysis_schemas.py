"""
Developmental Analysis Schemas (docs/MIGRATION_MAP.md, Step 11).

Canonical internal output shape for the developmental pipeline, and the
controlled vocabularies for the new State/Trait split. Not yet produced by
process_developmental_text() - that wiring is Step 11c/11d. Defined now
(Step 11a, schema only) so the vocabulary is fixed once, in one place,
before any engine or route depends on it.

State vs. Trait, per the architectural decision this implements: State is
the fast-moving tier (reactive, can move after a single event). Trait is
Persona.current_personality (Big Five) - slow-moving, only earns movement
once a pattern reaches AdaptationPattern.status == "established" or a
sustained-treatment gate is met (see pattern_engine.py, step 5). Neither
tier is ever assigned a raw number by the AI - only a direction and a
3-tier magnitude (mild | moderate | high). Bounded, deterministic code
converts that into an actual score change.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# Fast-moving State tier. Mirrors Persona.current_state's key vocabulary.
STATE_VARIABLES = (
    "trust",
    "threat_sensitivity",
    "mood",
    "regulation",
    "avoidance",
    "relational_security",
)

# Slow-moving Trait tier - the existing Big Five vocabulary already used by
# PersonalityTraits/Persona.current_personality (app/schemas/__init__.py).
TRAIT_NAMES = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)

DIRECTIONS = ("increase", "decrease", "no_change")
MAGNITUDES = ("mild", "moderate", "high")
EVIDENCE_STRENGTHS = ("low", "moderate", "high")


class StateImplication(BaseModel):
    """One State variable's proposed movement from a single event or intervention."""
    direction: str = Field(pattern="^(increase|decrease|no_change)$")
    magnitude: str = Field(pattern="^(mild|moderate|high)$")


class TraitImplication(BaseModel):
    """
    One Trait's proposed movement. evidence_strength is the AI's own read of
    how well-earned this implication is; it does NOT by itself authorize
    movement - the pattern-status/sustained-treatment gate still applies.
    """
    direction: str = Field(pattern="^(increase|decrease|no_change)$")
    magnitude: str = Field(pattern="^(mild|moderate|high)$")
    evidence_strength: Optional[str] = Field(default=None, pattern="^(low|moderate|high)$")


class DevelopmentalImpact(BaseModel):
    domains: List[str] = Field(default_factory=list)
    magnitude: Optional[str] = Field(default=None, pattern="^(mild|moderate|high)$")


class DevelopmentalAnalysisResult(BaseModel):
    """
    Canonical internal output of the developmental pipeline for one piece of
    text (a backstory or an experience). app/services/legacy_experience_
    adapter.py (Step 11d) translates this into the existing Experience
    response shape for frontend compatibility - this schema itself is never
    returned directly from a route today.
    """
    verdict: Optional[str] = None
    developmental_impact: Optional[DevelopmentalImpact] = None

    exposures: List[Dict] = Field(default_factory=list)
    interpretations: List[Dict] = Field(default_factory=list)
    adaptations: List[Dict] = Field(default_factory=list)
    patterns_reinforced: List[Dict] = Field(default_factory=list)
    protective_factors: List[Dict] = Field(default_factory=list)
    clinical_pattern_changes: List[Dict] = Field(default_factory=list)

    state_changes: Dict[str, StateImplication] = Field(default_factory=dict)
    trait_changes: Dict[str, TraitImplication] = Field(default_factory=dict)

    evidence_strength: Optional[str] = Field(default=None, pattern="^(low|moderate|high)$")
    reasoning: Optional[str] = None

    @field_validator("state_changes")
    @classmethod
    def _validate_state_keys(cls, v):
        unknown = set(v.keys()) - set(STATE_VARIABLES)
        if unknown:
            raise ValueError(f"Unknown state variable(s): {sorted(unknown)}. Must be one of {STATE_VARIABLES}")
        return v

    @field_validator("trait_changes")
    @classmethod
    def _validate_trait_keys(cls, v):
        unknown = set(v.keys()) - set(TRAIT_NAMES)
        if unknown:
            raise ValueError(f"Unknown trait(s): {sorted(unknown)}. Must be one of {TRAIT_NAMES}")
        return v
