"""Canonical read-only API projections for persisted psychological data."""
from typing import Dict, Optional

from app.models import AdaptationPattern, ClinicalPatternHypothesis, Interpretation, ProtectiveFactor
from app.services.persona_board import board_sections_for_persona, _direction


def baseline_for_persona(persona) -> Optional[Dict[str, float]]:
    if persona.baseline_personality:
        return dict(persona.baseline_personality)
    if not persona.experiences and not persona.interventions:
        return dict(persona.current_personality)
    return None


def persona_projection(db, persona) -> Dict:
    baseline = baseline_for_persona(persona)
    delta = None
    if baseline is not None:
        delta = {
            trait: round(persona.current_personality.get(trait, value) - value, 6)
            for trait, value in baseline.items()
        }
    baseline_attachment = dict(persona.baseline_attachment_dimensions or {})
    current_attachment = dict(persona.current_attachment_dimensions or {})
    attachment_delta = {
        dimension: round(current_attachment.get(dimension, value) - value, 6)
        for dimension, value in baseline_attachment.items()
    }
    return {
        "id": str(persona.id), "name": persona.name,
        "baseline_age": persona.baseline_age, "current_age": persona.current_age,
        "baseline_gender": persona.baseline_gender,
        "baseline_background": persona.baseline_background,
        "baseline_personality": baseline,
        "current_personality": persona.current_personality,
        "personality_delta": delta,
        "current_attachment_style": persona.current_attachment_style,
        "baseline_attachment_style": persona.baseline_attachment_style or persona.current_attachment_style,
        "baseline_attachment_dimensions": baseline_attachment,
        "current_attachment_dimensions": current_attachment,
        "attachment_delta": attachment_delta,
        "attachment_style_semantics": "derived_from_developmental_dimensions",
        "current_trauma_markers": persona.current_trauma_markers,
        "current_state": persona.current_state,
        "foundational_environment_signals": persona.foundational_environment_signals or {},
        "narrative_mode": persona.narrative_mode,
        **board_sections_for_persona(db, persona.id, persona.current_age),
        "experiences_count": len(persona.experiences),
        "interventions_count": len(persona.interventions),
        "created_at": persona.created_at, "updated_at": persona.updated_at,
    }


def _evidence_for_event(items, event_id):
    event_id = str(event_id)
    return [item for item in (items or []) if str(item.get("source_id") or item.get("experience_id") or "") == event_id]


def experience_psychology_projection(db, experience) -> Dict:
    event_id = str(experience.id)
    interpretation = db.query(Interpretation).filter(
        Interpretation.source_event_id == event_id
    ).order_by(Interpretation.created_at.desc()).first()
    interpretation_data = None
    if interpretation:
        interpretation_data = {
            "id": str(interpretation.id), "source_event_id": interpretation.source_event_id,
            "belief_statement": interpretation.belief_statement,
            "adaptation_strategy": interpretation.adaptation_strategy,
            "reasoning": interpretation.reasoning,
            "state_implications": interpretation.state_implications,
            "trait_implications": interpretation.trait_implications,
        }

    pattern_links = []
    for pattern in db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == experience.persona_id).all():
        for entry in pattern.reinforcement_history or []:
            if str(entry.get("experience_id") or "") == event_id:
                pattern_links.append({
                    "pattern_id": str(pattern.id), "pattern_name": pattern.pattern_name,
                    "adaptation_strategy": pattern.adaptation_strategy, "effect": entry.get("effect"),
                    "age": entry.get("age"), "current_status": pattern.status,
                    "current_evidence_strength": pattern.evidence_strength,
                })

    hypothesis_links = []
    for hypothesis in db.query(ClinicalPatternHypothesis).filter(
        ClinicalPatternHypothesis.persona_id == experience.persona_id
    ).all():
        supporting = _evidence_for_event(hypothesis.supporting_evidence, event_id)
        contradicting = _evidence_for_event(hypothesis.contradicting_evidence, event_id)
        for role, evidence in (("supporting", supporting), ("contradicting", contradicting)):
            if evidence:
                hypothesis_links.append({
                    "hypothesis_id": str(hypothesis.id), "pattern_key": hypothesis.pattern_key,
                    "evidence_role": role, "evidence": evidence,
                    "current_strength": hypothesis.evidence_strength,
                    "direction": _direction(hypothesis.evidence_strength, hypothesis.previous_evidence_strength),
                    "evidence_count": len(hypothesis.supporting_evidence or []) + len(hypothesis.contradicting_evidence or []),
                })
    protective_factors = [
        {
            "id": str(factor.id), "factor_type": factor.factor_type,
            "description": factor.description,
            "domains_buffered": list(factor.domains_buffered or []),
            "source_event_id": factor.source_event_id,
            "active_from_age": factor.active_from_age,
            "active_to_age": factor.active_to_age,
            "speaker_role": factor.speaker_role,
        }
        for factor in db.query(ProtectiveFactor).filter(
            ProtectiveFactor.source_event_id == event_id
        ).order_by(ProtectiveFactor.created_at, ProtectiveFactor.id).all()
    ]
    return {
        "interpretation": interpretation_data,
        "pattern_connections": pattern_links,
        "hypothesis_connections": hypothesis_links,
        "protective_factors": protective_factors,
    }
