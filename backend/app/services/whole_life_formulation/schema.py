"""
WholeLifeFormulation structured output schema - v2.1 SEMANTIC STABILITY PASS.

Two schemas live here now, and that split IS the v2.1 architecture change:

- The "Model*" types (ModelPatternCandidate, ModelAttachmentDimensions,
  ModelWholeLifeFormulation) are what the LLM actually emits. The model
  scores psychological RELEVANCE quantitatively; it no longer asserts a
  categorical pattern status or an attachment style directly.
- WholeLifeFormulation (and DevelopmentalPattern / AttachmentProfile within
  it) is the FINAL, derived object every other module (validators,
  render_report, the harness metrics) consumes - unchanged in shape from
  Phase 0 except DevelopmentalPattern gaining `relevance_score` and
  `reinforcing_events`/`current_manifestations` collapsing into
  `supporting_evidence` (the exact field list v2.1 specifies). Everything
  else in WholeLifeFormulation (Big Five, beliefs, protective factors,
  causal chains, hypotheses, current state, contradictions, unresolved
  questions, change points) is byte-for-byte unchanged from Phase 0.

See derivation.py for the deterministic code that turns Model* output into
the final object - pattern status from relevance_score via documented
thresholds, attachment style from the anxiety/avoidance/relational_security
dimensions via a documented quadrant rule. Both derivations use only
numbers the model already produced (plus, for pattern status, the real
ages already on file) - never keywords, never event counting.

Design corrections applied (per the locked Phase 0 spec, still in force):

A. No full per-event snapshots. `change_points` is SPARSE - the model only
   emits an entry for an experience_id that produced a real personality,
   attachment, or state change. An experience with nothing meaningful to
   report is simply absent from the list, not present with empty/zero
   fields. Software can later carry values forward to reconstruct a full
   snapshot at persistence time - that reconstruction is explicitly out of
   scope for this prototype.

B. No naked numbers. Every baseline/current Big Five score and every
   baseline/current attachment score carries its own `evidence` (Citation
   list) and `confidence` - there is no float anywhere in this schema that
   isn't paired with a citation trail and a confidence value.

D. IDs (`DevelopmentalPattern.id`, `Belief.id`, `ProtectiveFactorClaim.id`,
   `CausalChain.id`, `Hypothesis.id`, `Contradiction.id`) only need to be
   unique WITHIN one formulation - used for `Contradiction.involved_claim_ids`
   cross-references inside the same object. Stable cross-generation IDs are
   an explicitly deferred persistence problem, not solved here.

Every field is either required-and-non-null or required-and-nullable
(`Optional[X]` with no default) - never omittable - to stay compatible with
OpenAI Structured Outputs strict mode, which requires every property to
appear in `required` and expresses "optional" as a nullable type instead.

Enums (`PatternFamily`, `HypothesisFamily`, etc.) are intentionally
family-level, not event-level or diagnosis-level - see the design doc's
"ontology drift" risk. None of them contain a formal DSM/ICD diagnosis name;
that is the mechanism behind validator #7 (no-diagnosis guard) being a
structural impossibility rather than a post-hoc string filter.
"""
from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Closed canonical vocabularies (hybrid ontology - decision #6)
# ---------------------------------------------------------------------------

BigFiveTrait = Literal[
    "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"
]

AttachmentStyle = Literal[
    "secure", "anxious", "avoidant", "fearful_avoidant", "disorganized"
]

DevelopmentalDomain = Literal[
    "attachment_security", "emotional_safety", "stability", "emotional_regulation",
    "identity", "competence", "autonomy", "social_belonging", "intimacy", "sexuality",
]

# Family-level, not event-level (fixes the closed-taxonomy coverage gap that
# caused v1's near-empty output) and not diagnosis-level (fixes the RAD-style
# false-positive class structurally, not via a filter).
PatternFamily = Literal[
    "loss_and_bereavement",
    "identity_reconstruction",
    "relational_repair",
    "avoidant_withdrawal",
    "risk_seeking_dysregulation",
    "caregiving_role_reversal",
    "achievement_or_competence_compensation",
    "hypervigilant_monitoring",
    "prosocial_reinvention",
    "substance_coping",
    "other",
]

ProtectiveFactorFamily = Literal[
    "reliable_relationship",
    "mentor_or_role_model",
    "community_or_belonging",
    "mastery_or_competence",
    "spirituality_or_meaning",
    "corrective_experience",
    "temperament_resource",
    "other",
]

# Developmental/clinical-PATTERN-level constructs only. Never a formal
# diagnosis name - the enum itself is the no-diagnosis guard.
HypothesisFamily = Literal[
    "adjustment_reaction",
    "complicated_grief_pattern",
    "attachment_insecurity_pattern",
    "substance_use_vulnerability",
    "identity_disruption_pattern",
    "resilient_trajectory",
    "other",
]

HypothesisStatus = Literal["candidate", "supported", "contradicted", "resolved"]
PatternStatus = Literal["emerging", "established", "historically_weakened", "resolved"]

# The model's own tag of who a cited span's grammatical/narrative subject is.
# Code can check this tag for internal consistency against a claim's family
# (validator D.2) but cannot independently derive it - see correction E.
SubjectRole = Literal["self", "caregiver", "other", "unspecified"]

# Schema-level 0.0-1.0 bound (belt) PLUS the deterministic validator re-checks it (suspenders) -
# the validator is the source of truth for rejection, this is just to steer the model's own
# token distribution away from producing whole-number (0-100 scale) scores in the first place.
ConfidenceFloat = Annotated[float, Field(ge=0.0, le=1.0)]
UnitFloat = Annotated[float, Field(ge=0.0, le=1.0)]


# ---------------------------------------------------------------------------
# Shared primitive
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """
    Exactly one of experience_id / intervention_id / background_span should
    be non-null - enforced by the deterministic validator (not the JSON
    schema itself, to stay strict-mode compatible without a discriminated
    union). subject_role is the model's own claim about whose experience
    this citation describes.
    """
    experience_id: Optional[str]
    intervention_id: Optional[str]
    background_span: Optional[str]
    subject_role: SubjectRole


# ---------------------------------------------------------------------------
# Big Five (correction B: evidence + confidence on every score, no exceptions)
# ---------------------------------------------------------------------------

class BigFiveScore(BaseModel):
    value: UnitFloat
    evidence: List[Citation]
    confidence: ConfidenceFloat
    reasoning: str


class BigFiveProfile(BaseModel):
    openness: BigFiveScore
    conscientiousness: BigFiveScore
    extraversion: BigFiveScore
    agreeableness: BigFiveScore
    neuroticism: BigFiveScore


class PersonalityDelta(BaseModel):
    trait: BigFiveTrait
    from_value: UnitFloat
    to_value: UnitFloat
    direction: Literal["increase", "decrease", "no_change"]
    magnitude: Literal["none", "mild", "moderate", "substantial"]
    evidence: List[Citation]
    reasoning: str


# ---------------------------------------------------------------------------
# Attachment (correction B applies here too)
# ---------------------------------------------------------------------------

class AttachmentDimensionScore(BaseModel):
    value: UnitFloat
    evidence: List[Citation]
    confidence: ConfidenceFloat


class ModelAttachmentDimensions(BaseModel):
    """
    What the model actually emits for baseline/current attachment - v2.1.
    Dimensions ONLY. No style field: the model no longer independently
    chooses a categorical style that could contradict its own dimension
    scores. See derivation.derive_attachment_profile for the deterministic
    style rule.
    """
    attachment_anxiety: AttachmentDimensionScore
    attachment_avoidance: AttachmentDimensionScore
    relational_security: AttachmentDimensionScore


class AttachmentProfile(BaseModel):
    """
    The FINAL, post-derivation shape. `style`/`style_evidence`/
    `style_confidence` are code-derived (derivation.py) from the dimensions
    below, which are passed through unchanged from the model's
    ModelAttachmentDimensions - never asserted by the model directly.
    """
    style: AttachmentStyle
    style_evidence: List[Citation]
    style_confidence: ConfidenceFloat
    attachment_anxiety: AttachmentDimensionScore
    attachment_avoidance: AttachmentDimensionScore
    relational_security: AttachmentDimensionScore


class AttachmentTrajectoryPoint(BaseModel):
    period_label: str
    direction: Literal["toward_security", "toward_insecurity", "stable"]
    evidence: List[Citation]
    reasoning: str


# ---------------------------------------------------------------------------
# State (all six dimensions, every one cited - fixes v1's 4-of-6 gap)
# ---------------------------------------------------------------------------

class StateDimensionScore(BaseModel):
    value: UnitFloat
    evidence: List[Citation]
    confidence: ConfidenceFloat


class CurrentState(BaseModel):
    trust: StateDimensionScore
    threat_sensitivity: StateDimensionScore
    mood: StateDimensionScore
    regulation: StateDimensionScore
    avoidance: StateDimensionScore
    relational_security: StateDimensionScore


# ---------------------------------------------------------------------------
# Patterns - v2.2: the model scores EVERY canonical family, structurally.
#
# v2.1 let the model choose which families to even generate a candidate
# for; that "candidate-generation completeness" choice turned out to be the
# dominant remaining source of run-to-run instability, MORE than the
# relevance scoring itself (which was already tight, ~0.03-0.05 stdev).
# v2.2's fix is structural, not a prompt nudge: PatternScorecard has one
# NAMED field per canonical family (excluding "other", which has no fixed
# slot to occupy), so OpenAI Structured Outputs strict mode makes every
# family's presence in the model's output a schema requirement, not a
# request the model can partially comply with. canonical_family is
# therefore implicit in which named field a score lives under, rather than
# repeated as a string inside the object - derivation.py reattaches it when
# building the final, variable-length, post-threshold list.
# ---------------------------------------------------------------------------

class PatternFamilyScore(BaseModel):
    """
    One mandatory entry per canonical pattern family. supporting_evidence
    MAY legitimately be empty - a family that genuinely doesn't apply
    should score low with no manufactured evidence, not be omitted (there's
    nowhere to omit it TO anymore) and not be padded with invented support.
    """
    relevance_score: UnitFloat
    confidence: ConfidenceFloat
    human_label: str
    reasoning: str
    supporting_evidence: List[Citation]
    contradicting_evidence: List[Citation]


class PatternScorecard(BaseModel):
    """All ten non-'other' PatternFamily values, one PatternFamilyScore each."""
    loss_and_bereavement: PatternFamilyScore
    identity_reconstruction: PatternFamilyScore
    relational_repair: PatternFamilyScore
    avoidant_withdrawal: PatternFamilyScore
    risk_seeking_dysregulation: PatternFamilyScore
    caregiving_role_reversal: PatternFamilyScore
    achievement_or_competence_compensation: PatternFamilyScore
    hypervigilant_monitoring: PatternFamilyScore
    prosocial_reinvention: PatternFamilyScore
    substance_coping: PatternFamilyScore


class DevelopmentalPattern(BaseModel):
    """
    FINAL, post-derivation shape (derivation.py). `status`, `first_emerged`,
    and `canonical_family` itself are all code-derived/reattached from the
    PatternScorecard - never asserted by the model as a combined object. A
    family scoring below PATTERN_NOT_SHOWN_THRESHOLD never becomes one of
    these at all - that's the "low-scoring families can disappear from
    customer-facing output" requirement; the complete scorecard (all ten,
    every run) is retained separately as internal formulation data.
    """
    id: str
    canonical_family: PatternFamily
    human_label: str
    status: PatternStatus
    relevance_score: UnitFloat
    first_emerged: Optional[Citation]
    supporting_evidence: List[Citation]
    contradicting_evidence: List[Citation]
    confidence: ConfidenceFloat
    reasoning: str


class Belief(BaseModel):
    id: str
    human_label: str
    belief_statement: str
    formed_from: List[Citation]
    restated_by: List[Citation]
    confidence: ConfidenceFloat


class ProtectiveFactorClaim(BaseModel):
    id: str
    canonical_family: ProtectiveFactorFamily
    human_label: str
    domains_buffered: List[DevelopmentalDomain]
    active_from: Citation
    active_to: Optional[Citation]
    confidence: ConfidenceFloat


class CausalChainStep(BaseModel):
    event_citation: Citation
    mechanism: str


class CausalChain(BaseModel):
    id: str
    description: str
    steps: List[CausalChainStep]
    confidence: ConfidenceFloat


# ---------------------------------------------------------------------------
# Hypotheses - v2.2: same structural fix as patterns above. HypothesisFamily
# has one fewer field than the pattern list asked for (no separate
# human_label/reasoning per the locked field list for this section - see
# derivation.py for how the final object's human_label/reasoning get filled
# in deterministically from the family name and evidence counts instead).
# age_applicability is dropped entirely - it had no slot in the locked
# per-family field list, so nothing populates it anymore; a hypothesis
# family with an age-inapplicable premise should simply score low for
# personas outside that range, via ordinary evidence-strength reasoning,
# not a separate mechanism.
# ---------------------------------------------------------------------------

class HypothesisFamilyScore(BaseModel):
    evidence_strength: UnitFloat
    confidence: ConfidenceFloat
    supporting_evidence: List[Citation]
    contradicting_evidence: List[Citation]
    competing_explanations: List[str]


class HypothesisScorecard(BaseModel):
    """All six non-'other' HypothesisFamily values, one HypothesisFamilyScore each."""
    adjustment_reaction: HypothesisFamilyScore
    complicated_grief_pattern: HypothesisFamilyScore
    attachment_insecurity_pattern: HypothesisFamilyScore
    substance_use_vulnerability: HypothesisFamilyScore
    identity_disruption_pattern: HypothesisFamilyScore
    resilient_trajectory: HypothesisFamilyScore


class Hypothesis(BaseModel):
    """FINAL, post-derivation shape. canonical_family/status/human_label/
    reasoning are all code-derived/reattached - see derivation.py."""
    id: str
    canonical_family: HypothesisFamily
    human_label: str
    status: HypothesisStatus
    evidence_strength: UnitFloat
    supporting_evidence: List[Citation]
    contradicting_evidence: List[Citation]
    competing_explanations: List[str]
    reasoning: str


class Contradiction(BaseModel):
    id: str
    description: str
    involved_claim_ids: List[str]


# ---------------------------------------------------------------------------
# Sparse change points (correction A)
# ---------------------------------------------------------------------------

class PersonalityChangeAtEvent(BaseModel):
    trait: BigFiveTrait
    direction: Literal["increase", "decrease"]
    magnitude: Literal["mild", "moderate", "substantial"]


class AttachmentChangeAtEvent(BaseModel):
    """
    v2.1: dimension-only, "style" removed as a change_point target - style
    is now purely code-derived (see AttachmentProfile), so the model
    asserting a style shift here could contradict the derived style
    elsewhere. A style shift is still fully visible to a downstream reader:
    it falls out of re-deriving style from the dimensions at each change
    point, mechanically, not from a second model-asserted signal.
    """
    dimension: Literal["attachment_anxiety", "attachment_avoidance", "relational_security"]
    direction: Literal["increase", "decrease"]
    magnitude: Literal["mild", "moderate", "substantial"]


class StateChangeAtEvent(BaseModel):
    dimension: Literal["trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security"]
    direction: Literal["increase", "decrease"]
    magnitude: Literal["mild", "moderate", "substantial"]


class ChangePoint(BaseModel):
    """
    One entry per experience that produced a REAL change. The prompt
    instructs the model to omit experiences with nothing meaningful to
    report entirely, rather than emit an all-empty entry - this is what
    makes the list sparse rather than a disguised full snapshot.
    """
    experience_id: str
    age: int
    personality_changes: List[PersonalityChangeAtEvent]
    attachment_changes: List[AttachmentChangeAtEvent]
    state_changes: List[StateChangeAtEvent]
    reasoning: str
    evidence: List[Citation]


# ---------------------------------------------------------------------------
# Top-level objects: what the model emits (Model*) vs. the final derived
# object everything else consumes (WholeLifeFormulation).
# ---------------------------------------------------------------------------

class ModelWholeLifeFormulation(BaseModel):
    """
    The actual structured-output contract sent to the LLM in v2.2.
    `developmental_patterns` is `pattern_scorecard: PatternScorecard` (all
    ten families, structurally mandatory); `hypotheses` is
    `hypothesis_scorecard: HypothesisScorecard` (all six families,
    structurally mandatory); `baseline_attachment`/`current_attachment` are
    `ModelAttachmentDimensions` (dimensions only, no style - unchanged from
    v2.1). Every other field - Big Five, beliefs, protective factors,
    causal chains, current state, contradictions, unresolved questions,
    change points - is untouched from Phase 0, per the "do not change" list.
    """
    schema_version: str
    baseline_personality: BigFiveProfile
    current_personality: BigFiveProfile
    personality_deltas: List[PersonalityDelta]
    baseline_attachment: ModelAttachmentDimensions
    current_attachment: ModelAttachmentDimensions
    attachment_trajectory: List[AttachmentTrajectoryPoint]
    current_state: CurrentState
    pattern_scorecard: PatternScorecard
    beliefs: List[Belief]
    protective_factors: List[ProtectiveFactorClaim]
    causal_chains: List[CausalChain]
    hypothesis_scorecard: HypothesisScorecard
    contradictions: List[Contradiction]
    unresolved_questions: List[str]
    change_points: List[ChangePoint]
    overall_confidence: ConfidenceFloat


class WholeLifeFormulation(BaseModel):
    """
    FINAL, post-derivation object. See derivation.py for how this gets built
    from a ModelWholeLifeFormulation - every field here is either passed
    through unchanged from the model's output, or (developmental_patterns,
    baseline_attachment.style/current_attachment.style) deterministically
    derived from it.
    """
    schema_version: str
    baseline_personality: BigFiveProfile
    current_personality: BigFiveProfile
    personality_deltas: List[PersonalityDelta]
    baseline_attachment: AttachmentProfile
    current_attachment: AttachmentProfile
    attachment_trajectory: List[AttachmentTrajectoryPoint]
    current_state: CurrentState
    developmental_patterns: List[DevelopmentalPattern]
    beliefs: List[Belief]
    protective_factors: List[ProtectiveFactorClaim]
    causal_chains: List[CausalChain]
    hypotheses: List[Hypothesis]
    contradictions: List[Contradiction]
    unresolved_questions: List[str]
    change_points: List[ChangePoint]
    overall_confidence: ConfidenceFloat
