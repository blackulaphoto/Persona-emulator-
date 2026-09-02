"""
Deterministic derivation - v2.2 FINAL SHADOW STABILITY PASS.

Three derivations, all pure code, all using only numbers the model already
produced (plus, for pattern/hypothesis status, the real experience ages
already on file). Never keywords, never event counting.

v2.2 change: derive_pattern_projection and derive_hypothesis_projection now
consume a fixed PatternScorecard/HypothesisScorecard (every canonical family
present, structurally guaranteed by the schema) instead of a variable-length
list the model could partially populate. canonical_family, id, human_label,
and status are all reattached/derived here from the scorecard's field names -
the model's per-family objects no longer carry a canonical_family field at
all, since which field they live under already says which family they are.
"""
from typing import List, Optional

from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import (
    AttachmentProfile,
    AttachmentStyle,
    Citation,
    DevelopmentalPattern,
    Hypothesis,
    HypothesisFamilyScore,
    HypothesisScorecard,
    ModelAttachmentDimensions,
    PatternFamilyScore,
    PatternScorecard,
)

# ---------------------------------------------------------------------------
# Pattern status thresholds (documented, fixed - not tuned per-fixture, and
# unchanged from v2.1 - this pass did not touch the threshold values, only
# how the scored families reach this function)
# ---------------------------------------------------------------------------

PATTERN_NOT_SHOWN_THRESHOLD = 0.35
PATTERN_ESTABLISHED_THRESHOLD = 0.60
PATTERN_RECENCY_WINDOW_YEARS = 12

# The ten field names on PatternScorecard, in the order the model sees them -
# this list IS the "score every canonical family" guarantee: iterating it
# and reading getattr(scorecard, name) can never skip a family, because a
# strict-mode schema response can't omit a required field.
PATTERN_FAMILY_FIELDS = (
    "loss_and_bereavement", "identity_reconstruction", "relational_repair",
    "avoidant_withdrawal", "risk_seeking_dysregulation", "caregiving_role_reversal",
    "achievement_or_competence_compensation", "hypervigilant_monitoring",
    "prosocial_reinvention", "substance_coping",
)

HYPOTHESIS_FAMILY_FIELDS = (
    "adjustment_reaction", "complicated_grief_pattern", "attachment_insecurity_pattern",
    "substance_use_vulnerability", "identity_disruption_pattern", "resilient_trajectory",
)

# Deterministic, human-readable label for a family - used since the model no
# longer supplies human_label/reasoning per family (see schema.py's
# HypothesisFamilyScore docstring for why the locked field list omits them).
_FAMILY_DISPLAY_NAMES = {
    "loss_and_bereavement": "Loss and bereavement",
    "identity_reconstruction": "Identity reconstruction",
    "relational_repair": "Relational repair",
    "avoidant_withdrawal": "Avoidant withdrawal",
    "risk_seeking_dysregulation": "Risk-seeking dysregulation",
    "caregiving_role_reversal": "Caregiving role reversal",
    "achievement_or_competence_compensation": "Achievement/competence compensation",
    "hypervigilant_monitoring": "Hypervigilant monitoring",
    "prosocial_reinvention": "Prosocial reinvention",
    "substance_coping": "Substance coping",
    "adjustment_reaction": "Adjustment reaction",
    "complicated_grief_pattern": "Complicated grief pattern",
    "attachment_insecurity_pattern": "Attachment insecurity pattern",
    "substance_use_vulnerability": "Substance use vulnerability",
    "identity_disruption_pattern": "Identity disruption pattern",
    "resilient_trajectory": "Resilient trajectory",
}


def _most_recent_supporting_age(evidence: List[Citation], life: LifeSourceData) -> Optional[int]:
    ages = life.experience_age_by_id()
    cited_ages = [ages[c.experience_id] for c in evidence if c.experience_id in ages]
    return max(cited_ages) if cited_ages else None


def _earliest_supporting_citation(evidence: List[Citation], life: LifeSourceData) -> Optional[Citation]:
    ages = life.experience_age_by_id()
    dated = [(ages[c.experience_id], c) for c in evidence if c.experience_id in ages]
    if not dated:
        return evidence[0] if evidence else None
    dated.sort(key=lambda pair: pair[0])
    return dated[0][1]


def derive_pattern_status(score: PatternFamilyScore, life: LifeSourceData) -> Optional[str]:
    """Returns None if the family should not be shown at all."""
    if score.relevance_score < PATTERN_NOT_SHOWN_THRESHOLD:
        return None
    if score.relevance_score < PATTERN_ESTABLISHED_THRESHOLD:
        return "emerging"
    most_recent_age = _most_recent_supporting_age(score.supporting_evidence, life)
    if most_recent_age is None:
        return "established"
    if (life.current_age - most_recent_age) <= PATTERN_RECENCY_WINDOW_YEARS:
        return "established"
    return "historically_weakened"
    # "resolved" is still never derived - same documented limitation as v2.1.


def derive_pattern_projection(scorecard: PatternScorecard, life: LifeSourceData) -> List[DevelopmentalPattern]:
    patterns: List[DevelopmentalPattern] = []
    for family in PATTERN_FAMILY_FIELDS:
        score: PatternFamilyScore = getattr(scorecard, family)
        status = derive_pattern_status(score, life)
        if status is None:
            continue
        patterns.append(DevelopmentalPattern(
            id=f"pattern_{family}",
            canonical_family=family,
            human_label=score.human_label,
            status=status,
            relevance_score=score.relevance_score,
            first_emerged=_earliest_supporting_citation(score.supporting_evidence, life),
            supporting_evidence=score.supporting_evidence,
            contradicting_evidence=score.contradicting_evidence,
            confidence=score.confidence,
            reasoning=score.reasoning,
        ))
    return patterns


# ---------------------------------------------------------------------------
# Hypothesis status thresholds - mirrors the pattern thresholds for
# consistency (same PATTERN_NOT_SHOWN_THRESHOLD-equivalent value), plus a
# minimum independent-evidence-count rule carried over from validators.py's
# pre-existing "supported" quarantine check, now applied at derivation time
# instead of as a post-hoc downgrade.
# ---------------------------------------------------------------------------

HYPOTHESIS_NOT_SHOWN_THRESHOLD = 0.35
HYPOTHESIS_SUPPORTED_THRESHOLD = 0.60
HYPOTHESIS_SUPPORTED_MIN_EVIDENCE_COUNT = 2


def derive_hypothesis_status(score: HypothesisFamilyScore) -> Optional[str]:
    """Returns None if the family should not be shown at all."""
    if score.evidence_strength < HYPOTHESIS_NOT_SHOWN_THRESHOLD:
        return None
    if score.contradicting_evidence and len(score.contradicting_evidence) > len(score.supporting_evidence):
        return "contradicted"
    independent_ids = {c.experience_id or c.intervention_id for c in score.supporting_evidence if c.experience_id or c.intervention_id}
    if score.evidence_strength >= HYPOTHESIS_SUPPORTED_THRESHOLD and len(independent_ids) >= HYPOTHESIS_SUPPORTED_MIN_EVIDENCE_COUNT:
        return "supported"
    return "candidate"
    # "resolved" is never derived - same documented limitation as patterns.


def _derive_hypothesis_reasoning(family: str, score: HypothesisFamilyScore, status: str) -> str:
    """
    Deterministic reasoning summary - the model no longer supplies
    human_label/reasoning per hypothesis family (locked field list for this
    section omits them). This is intentionally a plain factual restatement
    of the score, not a synthesized clinical narrative - genuine narrative
    interpretation still happens in Narrative generation downstream, from
    the full formulation, not invented here as a substitute.
    """
    n_support = len(score.supporting_evidence)
    n_contra = len(score.contradicting_evidence)
    return (
        f"Derived status '{status}' from evidence_strength={score.evidence_strength:.2f} "
        f"with {n_support} supporting and {n_contra} contradicting citation(s)."
    )


def derive_hypothesis_projection(scorecard: HypothesisScorecard) -> List[Hypothesis]:
    hypotheses: List[Hypothesis] = []
    for family in HYPOTHESIS_FAMILY_FIELDS:
        score: HypothesisFamilyScore = getattr(scorecard, family)
        status = derive_hypothesis_status(score)
        if status is None:
            continue
        hypotheses.append(Hypothesis(
            id=f"hypothesis_{family}",
            canonical_family=family,
            human_label=_FAMILY_DISPLAY_NAMES[family],
            status=status,
            evidence_strength=score.evidence_strength,
            supporting_evidence=score.supporting_evidence,
            contradicting_evidence=score.contradicting_evidence,
            competing_explanations=score.competing_explanations,
            reasoning=_derive_hypothesis_reasoning(family, score, status),
        ))
    return hypotheses


# ---------------------------------------------------------------------------
# Attachment style derivation - v2.2: four-way quadrant only.
# `disorganized` derivation is removed/deferred per the locked spec ("do not
# invent a fifth categorical style from an unvalidated threshold") - it
# never actually fired in any of v2.1's 20 runs anyway. relational_security
# remains a fully separate, model-scored dimension; it just no longer
# participates in style derivation.
# ---------------------------------------------------------------------------

ATTACHMENT_MIDPOINT = 0.5


def derive_attachment_style(dims: ModelAttachmentDimensions) -> AttachmentStyle:
    """
    Standard two-dimensional (anxiety x avoidance) attachment quadrant,
    thresholded at the midpoint of each 0-1 dimension - both scored by the
    model, evidence-bound, never asserted categorically by it. Only ever
    returns secure / anxious / avoidant / fearful_avoidant.
    """
    anxious = dims.attachment_anxiety.value >= ATTACHMENT_MIDPOINT
    avoidant = dims.attachment_avoidance.value >= ATTACHMENT_MIDPOINT
    if not anxious and not avoidant:
        return "secure"
    if anxious and not avoidant:
        return "anxious"
    if not anxious and avoidant:
        return "avoidant"
    return "fearful_avoidant"


def derive_attachment_profile(dims: ModelAttachmentDimensions) -> AttachmentProfile:
    style = derive_attachment_style(dims)
    style_evidence = dims.attachment_anxiety.evidence + dims.attachment_avoidance.evidence
    style_confidence = min(dims.attachment_anxiety.confidence, dims.attachment_avoidance.confidence)
    return AttachmentProfile(
        style=style,
        style_evidence=style_evidence,
        style_confidence=style_confidence,
        attachment_anxiety=dims.attachment_anxiety,
        attachment_avoidance=dims.attachment_avoidance,
        relational_security=dims.relational_security,
    )
