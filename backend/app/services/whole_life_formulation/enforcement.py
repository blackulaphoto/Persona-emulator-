"""
Validator enforcement - PERSISTENCE PHASE.

Transforms a freshly-derived WholeLifeFormulation plus its ValidationReport
(validators.py) into a decision: an accepted_formulation ready to persist,
or a signal that the whole attempt must be rejected. This is the piece that
was explicitly deferred in every prior shadow pass - validate_formulation()
only ever produced a report before; nothing consumed it to actually change
what would be persisted, because nothing was being persisted yet.

Two different enforcement postures, per the locked spec:

OPTIONAL claims (pattern, belief, protective_factor, causal_chain,
hypothesis, contradiction): any "reject"-severity finding against that claim
removes the WHOLE claim from the formulation. There is no partial version of
a pattern or a hypothesis - it's either evidence-bound as generated, or it
doesn't get to exist in canonical output at all.

REQUIRED CORE claims (baseline/current Big Five, baseline/current attachment
dimensions, current state dimensions): a citation-level finding
(citation_existence / background_span_existence / citation_shape) against
one citation removes just that citation, keeping the claim if valid
evidence remains. If stripping leaves a required core claim with zero valid
evidence, the ENTIRE formulation is rejected - never partially persisted -
so the caller can retry the whole model call once.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import WholeLifeFormulation
from app.services.whole_life_formulation.validators import (
    ValidationFinding,
    ValidationReport,
    _validate_citation,  # re-validating one citation in isolation - see _citation_still_valid
    validate_formulation,
)

REQUIRED_CORE_CLAIM_TYPES = {"big_five", "attachment", "state"}
OPTIONAL_CLAIM_TYPES = {"pattern", "belief", "protective_factor", "causal_chain", "hypothesis", "contradiction"}
CITATION_LEVEL_RULES = {"citation_existence", "background_span_existence", "citation_shape"}

# Pseudo-ids a Contradiction may legitimately reference that aren't discrete
# claim objects - mirrors validators.py's own allowlist so enforcement's
# post-cleanup dangling-reference pass doesn't treat these as "removed
# claims" and drop every contradiction that mentions a trait/dimension.
_PROFILE_PSEUDO_ID_PREFIXES = ("baseline_", "current_")


@dataclass
class EnforcementAction:
    claim_type: str
    claim_ref: str
    action_taken: str  # "citation_removed" | "claim_rejected" | "formulation_rejected"
    rule_violated: str
    rejection_reason: str
    raw_claim_json: Optional[dict] = None


@dataclass
class EnforcementResult:
    status: str  # "accepted" | "rejected"
    accepted_formulation: Optional[WholeLifeFormulation]
    actions: List[EnforcementAction] = field(default_factory=list)
    rejection_summary: Optional[str] = None


def _citation_still_valid(citation, life: LifeSourceData, claim_type: str, claim_id: str) -> Tuple[bool, Optional[ValidationFinding]]:
    probe = ValidationReport()
    _validate_citation(citation, life, probe, claim_type, claim_id)
    citation_findings = [f for f in probe.findings if f.rule_violated in CITATION_LEVEL_RULES]
    if citation_findings:
        return False, citation_findings[0]
    return True, None


def _is_likely_pseudo_id(claim_id: str) -> bool:
    return claim_id.startswith(_PROFILE_PSEUDO_ID_PREFIXES)


def enforce_validation(formulation: WholeLifeFormulation, life: LifeSourceData) -> EnforcementResult:
    validation = validate_formulation(formulation, life)
    actions: List[EnforcementAction] = []

    findings_by_claim: Dict[Tuple[str, str], List[ValidationFinding]] = {}
    for f in validation.findings:
        if f.severity != "reject":
            continue  # "quarantine"/"flag" findings are informational only, not enforcement triggers
        findings_by_claim.setdefault((f.claim_type, f.claim_id), []).append(f)

    working = formulation.model_copy(deep=True)

    # --- 1. OPTIONAL claims: any reject finding drops the whole claim ---
    rejected_ids: Dict[str, set] = {t: set() for t in OPTIONAL_CLAIM_TYPES}
    for (claim_type, claim_id), findings in findings_by_claim.items():
        if claim_type not in OPTIONAL_CLAIM_TYPES:
            continue
        rejected_ids[claim_type].add(claim_id)
        for f in findings:
            actions.append(EnforcementAction(
                claim_type=claim_type, claim_ref=claim_id, action_taken="claim_rejected",
                rule_violated=f.rule_violated, rejection_reason=f.detail,
            ))

    working.developmental_patterns = [p for p in working.developmental_patterns if p.id not in rejected_ids["pattern"]]
    working.beliefs = [b for b in working.beliefs if b.id not in rejected_ids["belief"]]
    working.protective_factors = [p for p in working.protective_factors if p.id not in rejected_ids["protective_factor"]]
    working.causal_chains = [c for c in working.causal_chains if c.id not in rejected_ids["causal_chain"]]
    working.hypotheses = [h for h in working.hypotheses if h.id not in rejected_ids["hypothesis"]]
    working.contradictions = [c for c in working.contradictions if c.id not in rejected_ids["contradiction"]]

    # Drop any contradiction that (directly, or now transitively after the
    # removals above) references a claim id that no longer exists - internal
    # consistency, same posture as validators.py's own dangling-reference check.
    remaining_ids = (
        {p.id for p in working.developmental_patterns}
        | {b.id for b in working.beliefs}
        | {p.id for p in working.protective_factors}
        | {c.id for c in working.causal_chains}
        | {h.id for h in working.hypotheses}
    )
    kept_contradictions = []
    for c in working.contradictions:
        dangling = [
            ref for ref in c.involved_claim_ids
            if ref not in remaining_ids and not _is_likely_pseudo_id(ref)
        ]
        if dangling:
            actions.append(EnforcementAction(
                claim_type="contradiction", claim_ref=c.id, action_taken="claim_rejected",
                rule_violated="dangling_reference_after_enforcement",
                rejection_reason=f"referenced claim(s) {dangling} removed during enforcement",
            ))
            continue
        kept_contradictions.append(c)
    working.contradictions = kept_contradictions

    # --- 2. REQUIRED CORE claims: strip invalid citations, escalate to full
    # rejection if a claim loses all valid evidence ---
    formulation_must_be_rejected = False
    rejection_reasons: List[str] = []

    def _strip(score_obj, claim_type: str, claim_id: str):
        nonlocal formulation_must_be_rejected
        findings = findings_by_claim.get((claim_type, claim_id), [])
        non_citation_findings = [f for f in findings if f.rule_violated not in CITATION_LEVEL_RULES]
        if non_citation_findings:
            # score_range or evidence_count on a required core claim - not
            # fixable by removing one citation, so the whole formulation is
            # invalid (case B).
            formulation_must_be_rejected = True
            for f in non_citation_findings:
                rejection_reasons.append(f"{claim_type}.{claim_id}: {f.rule_violated} - {f.detail}")
                actions.append(EnforcementAction(
                    claim_type=claim_type, claim_ref=claim_id, action_taken="formulation_rejected",
                    rule_violated=f.rule_violated, rejection_reason=f.detail,
                ))
            return
        valid_evidence = []
        for citation in score_obj.evidence:
            ok, bad_finding = _citation_still_valid(citation, life, claim_type, claim_id)
            if ok:
                valid_evidence.append(citation)
            else:
                actions.append(EnforcementAction(
                    claim_type=claim_type, claim_ref=claim_id, action_taken="citation_removed",
                    rule_violated=bad_finding.rule_violated, rejection_reason=bad_finding.detail,
                ))
        if not valid_evidence:
            formulation_must_be_rejected = True
            reason = f"{claim_type}.{claim_id}: no valid evidence remains after citation removal"
            rejection_reasons.append(reason)
            actions.append(EnforcementAction(
                claim_type=claim_type, claim_ref=claim_id, action_taken="formulation_rejected",
                rule_violated="insufficient_grounding", rejection_reason=reason,
            ))
        score_obj.evidence = valid_evidence

    for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        for profile_name in ("baseline_personality", "current_personality"):
            _strip(getattr(getattr(working, profile_name), trait), "big_five", f"{profile_name}.{trait}")

    for profile_name in ("baseline_attachment", "current_attachment"):
        for dim in ("attachment_anxiety", "attachment_avoidance", "relational_security"):
            _strip(getattr(getattr(working, profile_name), dim), "attachment", f"{profile_name}.{dim}")

    for dim in ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security"):
        _strip(getattr(working.current_state, dim), "state", f"current_state.{dim}")

    if formulation_must_be_rejected:
        return EnforcementResult(
            status="rejected",
            accepted_formulation=None,
            actions=actions,
            rejection_summary="; ".join(rejection_reasons),
        )

    return EnforcementResult(status="accepted", accepted_formulation=working, actions=actions)
