"""
Projection reconciliation - PERSISTENCE PHASE.

Maps an accepted WholeLifeFormulation into the existing tables the current
UI already reads (adaptation_patterns, clinical_pattern_hypotheses,
protective_factors, persona_beliefs). These are compatibility/serving-layer
views, not authoritative - see whole_life_formulation.py's module docstring.
Each function does a full replace for the persona (delete what's no longer
present, upsert what's there) rather than an additive merge, so re-analysis
never leaves stale rows behind - the same "recompute from scratch" posture
app/services/timeline_replay.py already uses for V1.

Vocabulary note: these tables were designed around V1's concepts (tier,
open/revised/dismissed status, speaker_role) which don't map 1:1 onto V2's
(relevance_score, candidate/supported/contradicted). The mappings below are
documented, best-effort SEMANTIC translations for UI compatibility, not a
lossless round-trip - the full-fidelity V2 record is formulation_json on the
whole_life_formulations row, which is what anything V2-aware should actually
read.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import AdaptationPattern, ClinicalPatternHypothesis, PersonaBelief, ProtectiveFactor
from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import (
    Belief,
    Citation,
    DevelopmentalPattern,
    Hypothesis,
    ProtectiveFactorClaim,
    WholeLifeFormulation,
)

# V2 hypothesis.status -> legacy ClinicalPatternHypothesis.status vocabulary.
_HYPOTHESIS_STATUS_MAP = {
    "candidate": "open",
    "supported": "open",
    "contradicted": "dismissed",
    "resolved": "resolved",
}

# V2 belief.confidence bucketed into PersonaBelief.timeline_evaluation's fixed
# vocabulary - a deterministic bucketing of a real number, not fabrication.
_TIMELINE_EVALUATION_BUCKETS = (
    (0.8, "strongly_supported"),
    (0.6, "supported"),
    (0.4, "plausible"),
    (0.25, "partially_supported"),
)


def _confidence_to_timeline_evaluation(confidence: float) -> str:
    for threshold, label in _TIMELINE_EVALUATION_BUCKETS:
        if confidence >= threshold:
            return label
    return "weakly_supported"


def _citation_experience_ids(citations: List[Citation]) -> List[str]:
    return [c.experience_id for c in citations if c.experience_id]


def _citation_ages(citations: List[Citation], life: LifeSourceData) -> List[int]:
    ages = life.experience_age_by_id()
    return sorted({ages[c.experience_id] for c in citations if c.experience_id in ages})


def reconcile_adaptation_patterns(db: Session, persona_id: str, patterns: List[DevelopmentalPattern], life: LifeSourceData) -> None:
    existing = {row.adaptation_strategy: row for row in db.query(AdaptationPattern).filter_by(persona_id=persona_id).all()}
    seen_strategies = set()
    for p in patterns:
        seen_strategies.add(p.canonical_family)
        row = existing.get(p.canonical_family)
        if row is None:
            row = AdaptationPattern(persona_id=persona_id, adaptation_strategy=p.canonical_family)
            db.add(row)
        row.pattern_name = p.human_label
        row.description = p.reasoning
        support_ids = _citation_experience_ids(p.supporting_evidence)
        row.supporting_experience_ids = support_ids
        ages = _citation_ages(p.supporting_evidence, life)
        row.first_emerged_age = ages[0] if ages else None
        row.reinforcement_history = [
            {"experience_id": eid, "age": life.experience_age_by_id().get(eid), "effect": "strengthened"}
            for eid in support_ids
        ]
        # V2's "historically_weakened" maps directly; V1's vocabulary also has
        # "weakening" (not "historically_weakened") for the same concept.
        row.status = "weakening" if p.status == "historically_weakened" else p.status
        row.evidence_strength = p.relevance_score
        row.current_manifestations = []  # not carried in V2's per-family field list - see schema.py
    for strategy, row in existing.items():
        if strategy not in seen_strategies:
            db.delete(row)


def reconcile_clinical_pattern_hypotheses(db: Session, persona_id: str, hypotheses: List[Hypothesis], life: LifeSourceData) -> None:
    existing = {row.pattern_key: row for row in db.query(ClinicalPatternHypothesis).filter_by(persona_id=persona_id).all()}
    seen_keys = set()
    for h in hypotheses:
        seen_keys.add(h.canonical_family)
        row = existing.get(h.canonical_family)
        previous_strength = row.evidence_strength if row is not None else None
        if row is None:
            row = ClinicalPatternHypothesis(persona_id=persona_id, pattern_key=h.canonical_family)
            db.add(row)
        row.tier = "clinical_pattern_resemblance" if h.status == "supported" else "developmental_pattern"
        row.supporting_evidence = [
            {"type": "citation", "description": h.reasoning, "source_id": c.experience_id or c.intervention_id or c.background_span,
             "age": life.experience_age_by_id().get(c.experience_id)}
            for c in h.supporting_evidence
        ]
        row.contradicting_evidence = [
            {"type": "citation", "description": h.reasoning, "source_id": c.experience_id or c.intervention_id or c.background_span,
             "age": life.experience_age_by_id().get(c.experience_id)}
            for c in h.contradicting_evidence
        ]
        row.developmental_precursors = []
        row.current_manifestations = []
        row.previous_evidence_strength = previous_strength
        row.evidence_strength = h.evidence_strength
        ages = _citation_ages(h.supporting_evidence, life)
        row.opened_at_age = ages[0] if ages else (row.opened_at_age if row else None)
        row.status = _HYPOTHESIS_STATUS_MAP.get(h.status, "open")
    for key, row in existing.items():
        if key not in seen_keys:
            db.delete(row)


def reconcile_protective_factors(db: Session, persona_id: str, factors: List[ProtectiveFactorClaim], life: LifeSourceData) -> None:
    # No stable natural key across generations for protective factors (no
    # canonical_family-per-slot guarantee like patterns/hypotheses have) -
    # full delete-and-recreate per reconciliation, same net effect as
    # upsert-by-key for a persona that only ever has one active V2
    # generation's projection live at a time.
    db.query(ProtectiveFactor).filter_by(persona_id=persona_id).delete(synchronize_session=False)
    for f in factors:
        from_ages = _citation_ages([f.active_from], life)
        to_ages = _citation_ages([f.active_to], life) if f.active_to else []
        db.add(ProtectiveFactor(
            persona_id=persona_id,
            source_event_id=f.active_from.experience_id,
            factor_type=f.canonical_family,
            description=f.human_label,
            speaker_role="case_author",
            active_from_age=from_ages[0] if from_ages else None,
            active_to_age=to_ages[0] if to_ages else None,
            domains_buffered=list(f.domains_buffered),
        ))


def reconcile_persona_beliefs(db: Session, persona_id: str, beliefs: List[Belief], life: LifeSourceData) -> None:
    db.query(PersonaBelief).filter_by(subject_id=persona_id).delete(synchronize_session=False)
    for b in beliefs:
        related_ids = _citation_experience_ids(b.formed_from) + _citation_experience_ids(b.restated_by)
        restated_ages = _citation_ages(b.restated_by, life) or _citation_ages(b.formed_from, life)
        db.add(PersonaBelief(
            subject_id=persona_id,
            source_narration_id=None,  # V2 doesn't write narration_records - see module docstring
            speaker_role="case_author",  # engine-inferred, not a literal persona_voice quote
            attributed_to_persona=True,
            belief_text=b.belief_statement,
            narrative_theme=b.human_label,
            timeline_evaluation=_confidence_to_timeline_evaluation(b.confidence),
            engine_interpretation=b.human_label,
            related_event_ids=related_ids,
            restated_count=1 + len(b.restated_by),
            last_restated_age=restated_ages[-1] if restated_ages else None,
        ))


def reconcile_all_projections(db: Session, persona_id: str, formulation: WholeLifeFormulation, life: LifeSourceData) -> None:
    reconcile_adaptation_patterns(db, persona_id, formulation.developmental_patterns, life)
    reconcile_clinical_pattern_hypotheses(db, persona_id, formulation.hypotheses, life)
    reconcile_protective_factors(db, persona_id, formulation.protective_factors, life)
    reconcile_persona_beliefs(db, persona_id, formulation.beliefs, life)
