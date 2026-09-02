"""
Hard regression checks - PHASE 0 PROTOTYPE.

Correction E: the deterministic validator cannot independently prove
grammatical subject (it can only check the model's own subject_role tag for
internal consistency - see validators.py's `actor_tag_consistency` flag).
These checks are the separate, hardcoded, fixture-specific safety net for
the exact two historical production bugs (caregiver_substance_use and
caregiver_incarceration false-attributed from Brandon's OWN rehab/
incarceration experiences), plus a blunt diagnosis-language scan across
every freeform field in the formulation. Reported separately from the
generic validator's pass/fail, never merged into the same bucket.
"""
import re
from dataclasses import dataclass, field
from typing import List

from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import Citation, WholeLifeFormulation

# Freeform-text scan for diagnosis-shaped language leaking into human_label /
# reasoning / belief_statement / description fields, even though the
# canonical_family enum structurally can't contain one (schema.py's
# HypothesisFamily has no diagnosis entries). Deliberately blunt/substring -
# a false positive here just means "a human should look," never an auto-fail.
DIAGNOSIS_LANGUAGE_PATTERN = re.compile(
    r"reactive attachment disorder|\brad\b|ptsd|post-?traumatic stress disorder|"
    r"major depressive disorder|borderline personality disorder|\bbpd\b|"
    r"generalized anxiety disorder|conduct disorder|oppositional defiant disorder|"
    r"antisocial personality disorder",
    re.IGNORECASE,
)


@dataclass
class RegressionFinding:
    check: str
    detail: str


@dataclass
class RegressionReport:
    findings: List[RegressionFinding] = field(default_factory=list)

    def add(self, check: str, detail: str):
        self.findings.append(RegressionFinding(check, detail))

    @property
    def passed(self) -> bool:
        return not self.findings


def _citations_all_self(citations: List[Citation], self_ids: set) -> bool:
    real = [c for c in citations if c.experience_id or c.intervention_id]
    if not real:
        return False
    ids = {c.experience_id or c.intervention_id for c in real}
    # Every real citation is one of the persona's own self-events AND every
    # citation the model itself tagged is subject_role == "self".
    return ids.issubset(self_ids) and all(c.subject_role == "self" for c in real)


def check_caregiver_self_confusion(formulation: WholeLifeFormulation, self_event_ids: set) -> List[RegressionFinding]:
    """
    Flags any pattern/hypothesis/belief whose family or human_label reads as
    caregiver-attributed (substance use, incarceration, absence, etc.) but is
    grounded ONLY in citations to the persona's own self-event experience ids
    - i.e. the exact production bug class, generalized past the two original
    hardcoded cases.
    """
    findings: List[RegressionFinding] = []
    caregiver_keywords = ("caregiver", "parent", "mother", "father", "guardian")

    for pattern in formulation.developmental_patterns:
        label = pattern.human_label.lower()
        if any(k in label for k in caregiver_keywords):
            cites = pattern.supporting_evidence + ([pattern.first_emerged] if pattern.first_emerged else [])
            if _citations_all_self(cites, self_event_ids):
                findings.append(RegressionFinding(
                    "caregiver_self_confusion_pattern",
                    f"pattern {pattern.id!r} ({pattern.human_label!r}) reads caregiver-attributed but is "
                    f"grounded only in self-tagged citations to {self_event_ids}",
                ))

    for hyp in formulation.hypotheses:
        label = hyp.human_label.lower()
        if any(k in label for k in caregiver_keywords):
            if _citations_all_self(hyp.supporting_evidence, self_event_ids):
                findings.append(RegressionFinding(
                    "caregiver_self_confusion_hypothesis",
                    f"hypothesis {hyp.id!r} ({hyp.human_label!r}) reads caregiver-attributed but is "
                    f"grounded only in self-tagged citations to {self_event_ids}",
                ))

    for belief in formulation.beliefs:
        label = belief.human_label.lower()
        if any(k in label for k in caregiver_keywords):
            if _citations_all_self(belief.formed_from, self_event_ids):
                findings.append(RegressionFinding(
                    "caregiver_self_confusion_belief",
                    f"belief {belief.id!r} ({belief.human_label!r}) reads caregiver-attributed but is "
                    f"grounded only in self-tagged citations to {self_event_ids}",
                ))

    return findings


def check_no_diagnosis_language(formulation: WholeLifeFormulation) -> List[RegressionFinding]:
    findings: List[RegressionFinding] = []
    texts = []
    for h in formulation.hypotheses:
        texts.append(("hypothesis", h.id, h.human_label))
        texts.append(("hypothesis.reasoning", h.id, h.reasoning))
    for p in formulation.developmental_patterns:
        texts.append(("pattern", p.id, p.human_label))
        texts.append(("pattern.reasoning", p.id, p.reasoning))
    for b in formulation.beliefs:
        texts.append(("belief", b.id, b.human_label))
        texts.append(("belief.statement", b.id, b.belief_statement))

    for field_name, claim_id, text in texts:
        match = DIAGNOSIS_LANGUAGE_PATTERN.search(text)
        if match:
            findings.append(RegressionFinding(
                "diagnosis_language_leak",
                f"{field_name} on {claim_id!r} contains diagnosis-shaped language: {match.group(0)!r} "
                f"in {text[:120]!r}",
            ))
    return findings


def run_regression_checks(formulation: WholeLifeFormulation, life: LifeSourceData, self_event_ids: set) -> RegressionReport:
    report = RegressionReport()
    for f in check_caregiver_self_confusion(formulation, self_event_ids):
        report.add(f.check, f.detail)
    for f in check_no_diagnosis_language(formulation):
        report.add(f.check, f.detail)
    return report
