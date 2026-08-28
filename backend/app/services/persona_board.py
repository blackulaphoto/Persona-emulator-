"""
Persona board projection (docs/MIGRATION_MAP.md, Step 12).

Read-only view layer: turns the adaptation/hypothesis rows the pipeline
already persists into the shape PersonaResponse exposes. No psychological
analysis happens here - it re-presents state the engine already computed.
That separation is the point: the Step 12 audit found that the engine's
inferences were correct and simply had no API surface, so the board could
only ever render Big Five plus a threshold-gated trauma-marker list. A
persona whose own generated narrative described heightened threat
sensitivity, avoidance and relational insecurity still displayed "All is
well right now", because none of the reasoning behind that narrative could
reach the client.

Confidence numbers here are deliberately NOT presented as diagnostic
certainty anywhere they surface - they are "how strongly does this persona's
currently-known history match this pattern", and they are expected to move
down as well as up.
"""
from typing import Dict, List, Optional

from app.models import AdaptationPattern, ClinicalPatternHypothesis


def _confidence(strength: Optional[float]) -> Optional[int]:
    """evidence_strength (0.0-1.0) -> whole-percent display value."""
    if strength is None:
        return None
    return int(round(strength * 100))


def _direction(current: Optional[float], previous: Optional[float]) -> Optional[str]:
    """
    Direction of travel for a hypothesis, from its own previous value.

    Returns None when there is no prior value to compare against - a
    hypothesis that has only been computed once is "emerging", not
    "stable", and claiming otherwise would overstate what we know.
    """
    if current is None or previous is None:
        return None
    if current > previous:
        return "strengthening"
    if current < previous:
        return "weakening"
    return "stable"


def adaptation_pattern_summaries(db, persona_id: str) -> List[Dict]:
    """
    The persona's adaptations, strongest first. Patterns with no earned
    strength yet still appear - watching an adaptation emerge is the point,
    and status already communicates how provisional it is.
    """
    rows = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona_id).all()
    summaries = [
        {
            "adaptation_strategy": row.adaptation_strategy,
            "pattern_name": row.pattern_name,
            "status": row.status,
            "evidence_strength": row.evidence_strength,
            "confidence": _confidence(row.evidence_strength),
            "first_emerged_age": row.first_emerged_age,
        }
        for row in rows
    ]
    return sorted(summaries, key=lambda s: (s["evidence_strength"] or 0), reverse=True)


def clinical_pattern_hypothesis_summaries(db, persona_id: str) -> List[Dict]:
    """
    Evolving clinical-pattern hypotheses, strongest first.

    Deliberately NOT filtered by evidence_accumulator.DISPLAY_THRESHOLD, which
    still gates current_trauma_markers. A user watching the engine consider
    and revise a hypothesis at 28% is the product's original strength; hiding
    everything until it crosses a confidence floor is what made the board feel
    inert. Hypotheses with literally no evidence yet (strength None or 0) are
    excluded - "opened for investigation" is not the same as "we have
    something to say", and showing every prior would bury the real signal.
    Dismissed hypotheses are excluded outright.
    """
    rows = db.query(ClinicalPatternHypothesis).filter(
        ClinicalPatternHypothesis.persona_id == persona_id
    ).all()

    summaries = [
        {
            "pattern_key": row.pattern_key,
            "tier": row.tier,
            "status": row.status,
            "evidence_strength": row.evidence_strength,
            "confidence": _confidence(row.evidence_strength),
            "direction": _direction(row.evidence_strength, row.previous_evidence_strength),
            "opened_at_age": row.opened_at_age,
            "developmental_precursors": row.developmental_precursors or [],
        }
        for row in rows
        if row.status != "dismissed" and (row.evidence_strength or 0) > 0
    ]
    return sorted(summaries, key=lambda s: (s["evidence_strength"] or 0), reverse=True)


def board_sections_for_persona(db, persona_id: str) -> Dict[str, List[Dict]]:
    """Both board sections in one call - what the persona routes actually need."""
    return {
        "adaptation_patterns": adaptation_pattern_summaries(db, persona_id),
        "clinical_pattern_hypotheses": clinical_pattern_hypothesis_summaries(db, persona_id),
    }
