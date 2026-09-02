"""
Deterministic validator - PHASE 0 PROTOTYPE.

Pure code. No LLM calls, no re-derivation of psychology - only lookups,
comparisons, and membership checks against what the model already produced,
per the locked "model reasons, code validates" split.

Correction C: validators check INTERNAL consistency within one freshly
generated formulation only. Nothing here compares against a prior run's
persisted values - full re-derivation means there is no "prior" to validate
against in this design.

Correction E: this module does NOT attempt to independently verify
grammatical subject. Validator `actor_tag_consistency` only checks that the
model's own subject_role tag is internally coherent with the family it's
attached to (e.g. a caregiver-flavored claim citing an exposure the model
itself tagged subject_role="self" is a real red flag worth surfacing) - it
is explicitly a LOWER-CONFIDENCE signal than the hard regression checks in
regression_checks.py, and is reported as such, never merged into the same
pass/fail bucket.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import Citation, WholeLifeFormulation

# Pattern/hypothesis families whose whole point is caregiver behavior - if a
# claim in one of these families cites only self-tagged evidence, that's
# worth flagging even though we can't independently prove it (correction E).
CAREGIVER_FLAVORED_FAMILIES = {"caregiving_role_reversal"}

# v2.2: mirrors derivation.py's HYPOTHESIS_SUPPORTED_THRESHOLD/
# HYPOTHESIS_SUPPORTED_MIN_EVIDENCE_COUNT exactly - status="supported" is
# now derived to already satisfy this, so this check should be structurally
# unreachable; kept as a defensive regression guard on the derivation code
# itself, not because the model can violate it directly anymore.
HYPOTHESIS_EVIDENCE_MIN_COUNT = 2
HYPOTHESIS_EVIDENCE_MIN_STRENGTH = 0.6


@dataclass
class ValidationFinding:
    claim_type: str
    claim_id: str
    rule_violated: str
    detail: str
    severity: str  # "reject" | "quarantine" | "flag" (flag = correction-E lower-confidence signal)


@dataclass
class ValidationReport:
    findings: List[ValidationFinding] = field(default_factory=list)

    def add(self, claim_type: str, claim_id: str, rule: str, detail: str, severity: str = "reject"):
        self.findings.append(ValidationFinding(claim_type, claim_id, rule, detail, severity))

    @property
    def rejections(self) -> List[ValidationFinding]:
        return [f for f in self.findings if f.severity == "reject"]

    @property
    def quarantines(self) -> List[ValidationFinding]:
        return [f for f in self.findings if f.severity == "quarantine"]

    @property
    def flags(self) -> List[ValidationFinding]:
        return [f for f in self.findings if f.severity == "flag"]


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _background_corpus(life: LifeSourceData) -> str:
    return _norm(f"{life.background} {life.caregiver_history} {life.temperament_self_description}")


def _validate_citation(
    citation: Citation, life: LifeSourceData, report: ValidationReport, claim_type: str, claim_id: str
) -> None:
    non_null = [v for v in (citation.experience_id, citation.intervention_id, citation.background_span) if v]
    if len(non_null) != 1:
        report.add(claim_type, claim_id, "citation_shape",
                    f"citation must set exactly one of experience_id/intervention_id/background_span, got {non_null}")
        return

    if citation.experience_id is not None:
        if citation.experience_id not in life.all_valid_experience_ids():
            report.add(claim_type, claim_id, "citation_existence",
                        f"experience_id {citation.experience_id!r} does not exist on this persona")
    elif citation.intervention_id is not None:
        if citation.intervention_id not in life.all_valid_intervention_ids():
            report.add(claim_type, claim_id, "citation_existence",
                        f"intervention_id {citation.intervention_id!r} does not exist on this persona")
    elif citation.background_span is not None:
        if _norm(citation.background_span) not in _background_corpus(life):
            report.add(claim_type, claim_id, "background_span_existence",
                        f"background_span not found verbatim in source text: {citation.background_span[:80]!r}")


def _validate_score_range(value: float, claim_type: str, claim_id: str, field_name: str, report: ValidationReport):
    if not (0.0 <= value <= 1.0):
        report.add(claim_type, claim_id, "score_range", f"{field_name}={value} out of [0,1]")


def _validate_age(age: int, life: LifeSourceData, claim_type: str, claim_id: str, report: ValidationReport):
    ages = {e.age_at_event for e in life.experiences}
    if age not in ages:
        report.add(claim_type, claim_id, "age_match", f"age={age} does not match any real experience age")


def validate_formulation(formulation: WholeLifeFormulation, life: LifeSourceData) -> ValidationReport:
    report = ValidationReport()

    # --- Big Five ---
    for trait_name in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        for profile_name in ("baseline_personality", "current_personality"):
            score = getattr(getattr(formulation, profile_name), trait_name)
            claim_id = f"{profile_name}.{trait_name}"
            _validate_score_range(score.value, "big_five", claim_id, "value", report)
            _validate_score_range(score.confidence, "big_five", claim_id, "confidence", report)
            if not score.evidence:
                report.add("big_five", claim_id, "evidence_count", "no evidence attached to a scored trait")
            for c in score.evidence:
                _validate_citation(c, life, report, "big_five", claim_id)

    for delta in formulation.personality_deltas:
        claim_id = f"delta.{delta.trait}"
        _validate_score_range(delta.from_value, "personality_delta", claim_id, "from_value", report)
        _validate_score_range(delta.to_value, "personality_delta", claim_id, "to_value", report)
        for c in delta.evidence:
            _validate_citation(c, life, report, "personality_delta", claim_id)

    # --- Attachment ---
    for profile_name in ("baseline_attachment", "current_attachment"):
        profile = getattr(formulation, profile_name)
        _validate_score_range(profile.style_confidence, "attachment", profile_name, "style_confidence", report)
        for c in profile.style_evidence:
            _validate_citation(c, life, report, "attachment", f"{profile_name}.style")
        for dim_name in ("attachment_anxiety", "attachment_avoidance", "relational_security"):
            dim = getattr(profile, dim_name)
            claim_id = f"{profile_name}.{dim_name}"
            _validate_score_range(dim.value, "attachment", claim_id, "value", report)
            _validate_score_range(dim.confidence, "attachment", claim_id, "confidence", report)
            if not dim.evidence:
                report.add("attachment", claim_id, "evidence_count", "no evidence attached to a scored dimension")
            for c in dim.evidence:
                _validate_citation(c, life, report, "attachment", claim_id)

    for i, point in enumerate(formulation.attachment_trajectory):
        claim_id = f"attachment_trajectory[{i}]"
        for c in point.evidence:
            _validate_citation(c, life, report, "attachment_trajectory", claim_id)

    # --- Current state (all six dimensions) ---
    for dim_name in ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security"):
        dim = getattr(formulation.current_state, dim_name)
        claim_id = f"current_state.{dim_name}"
        _validate_score_range(dim.value, "state", claim_id, "value", report)
        _validate_score_range(dim.confidence, "state", claim_id, "confidence", report)
        if not dim.evidence:
            report.add("state", claim_id, "evidence_count", "no evidence attached to a state dimension")
        for c in dim.evidence:
            _validate_citation(c, life, report, "state", claim_id)

    # --- Developmental patterns (v2.1: relevance_score + supporting_evidence,
    # status/first_emerged are code-derived by derivation.py, not the model -
    # validated here for shape/range only, not re-derived) ---
    for pattern in formulation.developmental_patterns:
        _validate_score_range(pattern.confidence, "pattern", pattern.id, "confidence", report)
        _validate_score_range(pattern.relevance_score, "pattern", pattern.id, "relevance_score", report)
        if pattern.first_emerged is not None:
            _validate_citation(pattern.first_emerged, life, report, "pattern", pattern.id)
        if not pattern.supporting_evidence:
            report.add("pattern", pattern.id, "evidence_count", "pattern has no supporting_evidence")
        for c in pattern.supporting_evidence:
            _validate_citation(c, life, report, "pattern", pattern.id)
        for c in pattern.contradicting_evidence:
            _validate_citation(c, life, report, "pattern", pattern.id)
        if pattern.canonical_family in CAREGIVER_FLAVORED_FAMILIES:
            cites = pattern.supporting_evidence + ([pattern.first_emerged] if pattern.first_emerged else [])
            if cites and all(c.subject_role == "self" for c in cites if c.experience_id or c.intervention_id):
                report.add("pattern", pattern.id, "actor_tag_consistency",
                            "caregiving_role_reversal pattern grounded only in self-tagged citations", severity="flag")

    # --- Beliefs ---
    for belief in formulation.beliefs:
        _validate_score_range(belief.confidence, "belief", belief.id, "confidence", report)
        if not belief.formed_from:
            report.add("belief", belief.id, "evidence_count", "belief has no formed_from citation")
        for c in belief.formed_from + belief.restated_by:
            _validate_citation(c, life, report, "belief", belief.id)

    # --- Protective factors ---
    for pf in formulation.protective_factors:
        _validate_score_range(pf.confidence, "protective_factor", pf.id, "confidence", report)
        _validate_citation(pf.active_from, life, report, "protective_factor", pf.id)
        if pf.active_to is not None:
            _validate_citation(pf.active_to, life, report, "protective_factor", pf.id)

    # --- Causal chains ---
    for chain in formulation.causal_chains:
        _validate_score_range(chain.confidence, "causal_chain", chain.id, "confidence", report)
        if not chain.steps:
            report.add("causal_chain", chain.id, "evidence_count", "causal chain has no steps")
        for step in chain.steps:
            _validate_citation(step.event_citation, life, report, "causal_chain", chain.id)

    # --- Hypotheses ---
    for hyp in formulation.hypotheses:
        _validate_score_range(hyp.evidence_strength, "hypothesis", hyp.id, "evidence_strength", report)
        independent_experience_ids = {
            c.experience_id for c in hyp.supporting_evidence if c.experience_id
        } | {
            c.intervention_id for c in hyp.supporting_evidence if c.intervention_id
        }
        if hyp.status in ("supported",):
            if len(independent_experience_ids) < HYPOTHESIS_EVIDENCE_MIN_COUNT or hyp.evidence_strength < HYPOTHESIS_EVIDENCE_MIN_STRENGTH:
                report.add("hypothesis", hyp.id, "hypothesis_evidence_minimum",
                            f"status=supported requires >={HYPOTHESIS_EVIDENCE_MIN_COUNT} independent citations "
                            f"and evidence_strength>={HYPOTHESIS_EVIDENCE_MIN_STRENGTH}; got "
                            f"{len(independent_experience_ids)} citations, strength={hyp.evidence_strength}",
                            severity="quarantine")
        for c in hyp.supporting_evidence + hyp.contradicting_evidence:
            _validate_citation(c, life, report, "hypothesis", hyp.id)
        # age_applicability removed in v2.2 - no field to validate anymore
        # (see schema.py's Hypothesis docstring for why).

    # --- Contradictions: internal reference consistency ---
    # A contradiction can legitimately be "between the baseline and current
    # personality/attachment picture," at either the whole-profile level
    # ("current_attachment") or a specific trait/dimension level
    # ("current_attachment_avoidance", "baseline_extraversion") - none of
    # those are id-bearing claims elsewhere in the schema, so a generated
    # allowlist covers both granularities rather than forcing the model to
    # invent an id for something that isn't a discrete claim object.
    PROFILE_PSEUDO_IDS = {"baseline_personality", "current_personality", "baseline_attachment", "current_attachment"}
    for prefix in ("baseline", "current"):
        for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
            PROFILE_PSEUDO_IDS.add(f"{prefix}_{trait}")
            PROFILE_PSEUDO_IDS.add(f"{prefix}_personality_{trait}")  # tolerate a doubled "personality_" prefix too
        for dim in ("attachment_anxiety", "attachment_avoidance", "relational_security"):
            PROFILE_PSEUDO_IDS.add(f"{prefix}_{dim}")
            PROFILE_PSEUDO_IDS.add(f"{prefix}_attachment_{dim}")  # tolerate a doubled "attachment_" prefix too
    for dim in ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security"):
        PROFILE_PSEUDO_IDS.add(f"current_state_{dim}")
        PROFILE_PSEUDO_IDS.add(f"state_{dim}")
    all_claim_ids = (
        {p.id for p in formulation.developmental_patterns}
        | {b.id for b in formulation.beliefs}
        | {p.id for p in formulation.protective_factors}
        | {c.id for c in formulation.causal_chains}
        | {h.id for h in formulation.hypotheses}
        | PROFILE_PSEUDO_IDS
    )
    for contradiction in formulation.contradictions:
        for ref in contradiction.involved_claim_ids:
            if ref not in all_claim_ids:
                report.add("contradiction", contradiction.id, "internal_reference",
                            f"involved_claim_ids references unknown claim id {ref!r}")

    # --- Change points ---
    for point in formulation.change_points:
        claim_id = f"change_point.{point.experience_id}"
        if point.experience_id not in life.all_valid_experience_ids():
            report.add("change_point", claim_id, "citation_existence",
                        f"experience_id {point.experience_id!r} does not exist on this persona")
        else:
            _validate_age(point.age, life, "change_point", claim_id, report)
        if not (point.personality_changes or point.attachment_changes or point.state_changes):
            report.add("change_point", claim_id, "sparse_change_point_empty",
                        "change_point entry has no actual changes attached (violates sparsity rule)")
        for c in point.evidence:
            _validate_citation(c, life, report, "change_point", claim_id)

    _validate_score_range(formulation.overall_confidence, "formulation", "overall", "overall_confidence", report)

    return report
