"""Canonical deterministic replay of persisted psychological proposals."""
from app.models import (
    AdaptationPattern, ClinicalPatternHypothesis, DevelopmentalExposure, Experience,
    FunctionalObservation, Interpretation, Intervention, NarrationRecord,
    PersonalitySnapshot, ProtectiveFactor,
)
from app.services.attachment_engine import dimensions_for_style, apply_attachment_update, derive_attachment_style
from app.services.developmental_pipeline import _exposure_dict, _protective_dict, _narration_dict, _functional_dict
from app.services.evidence_accumulator import accumulate_evidence, project_current_trauma_markers
from app.services.pattern_engine import accumulate_patterns, name_pattern_heuristic
from app.services.state_trait_engine import apply_state_update, apply_trait_update, trait_gate_open, intervention_trait_gate_open


def _interpretation_dict(row):
    return {"id": row.id, "source_event_id": row.source_event_id, "age_at_event": row.age_at_event,
            "adaptation_strategy": row.adaptation_strategy, "belief_statement": row.belief_statement,
            "developmental_domains": row.developmental_domains}


def _reconcile_patterns(db, persona, accumulated):
    existing = {row.adaptation_strategy: row for row in db.query(AdaptationPattern).filter_by(persona_id=persona.id).all()}
    for strategy, row in list(existing.items()):
        if strategy not in accumulated:
            db.delete(row)
    for strategy, state in accumulated.items():
        row = existing.get(strategy)
        if row is None:
            row = AdaptationPattern(persona_id=persona.id, adaptation_strategy=strategy,
                                    pattern_name=name_pattern_heuristic(strategy))
            db.add(row)
        row.description = state.get("representative_belief")
        row.first_emerged_age = state["first_emerged_age"]
        row.reinforcement_history = state["reinforcement_history"]
        row.supporting_experience_ids = [e["experience_id"] for e in state["reinforcement_history"] if e.get("experience_id")]
        row.status = state["status"]
        row.evidence_strength = state["evidence_strength"]
        row.current_manifestations = state.get("current_manifestations", [])


def _reconcile_hypotheses(db, persona, accumulated):
    existing = {row.pattern_key: row for row in db.query(ClinicalPatternHypothesis).filter_by(persona_id=persona.id).all()}
    for key, row in list(existing.items()):
        if key not in accumulated:
            db.delete(row)
    for key, state in accumulated.items():
        row = existing.get(key)
        if row is None:
            row = ClinicalPatternHypothesis(persona_id=persona.id, pattern_key=key)
            db.add(row)
        row.tier = state["tier"]
        row.supporting_evidence = state["supporting_evidence"]
        row.contradicting_evidence = state["contradicting_evidence"]
        row.developmental_precursors = state["developmental_precursors"]
        row.current_manifestations = state["current_manifestations"]
        row.previous_evidence_strength = None
        row.evidence_strength = state["evidence_strength"]
        row.opened_at_age = state["opened_at_age"]
        row.status = state["status"]


def rebuild_persona_from_timeline(db, persona_id: str):
    """Restore baseline, then deterministically reapply stored event/intervention proposals."""
    from app.models import Persona
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if persona is None:
        raise ValueError("Persona not found")
    if not persona.baseline_personality:
        raise ValueError("Persona has no immutable baseline personality")

    persona.current_personality = dict(persona.baseline_personality)
    persona.current_state = {}
    baseline_style = persona.baseline_attachment_style or persona.current_attachment_style or "secure"
    persona.current_attachment_dimensions = dict(persona.baseline_attachment_dimensions or dimensions_for_style(baseline_style))
    persona.current_attachment_style = derive_attachment_style(persona.current_attachment_dimensions)

    exposures = db.query(DevelopmentalExposure).filter_by(persona_id=persona.id).all()
    protective = db.query(ProtectiveFactor).filter_by(persona_id=persona.id).all()
    narration = db.query(NarrationRecord).filter_by(subject_id=persona.id).all()
    functional = db.query(FunctionalObservation).filter_by(persona_id=persona.id).all()
    interpretations = db.query(Interpretation).filter_by(persona_id=persona.id).all()
    experiences = db.query(Experience).filter_by(persona_id=persona.id).all()
    interventions = db.query(Intervention).filter_by(persona_id=persona.id).all()
    experience_by_id = {str(row.id): row for row in experiences}

    all_protective = [_protective_dict(row) for row in protective]
    all_functional = [_functional_dict(row) for row in functional]
    prefix_interpretations = []
    applied_interventions = []
    snapshots = []
    current_pattern_state = {}

    items = []
    for row in interpretations:
        source = experience_by_id.get(str(row.source_event_id)) if row.source_event_id else None
        items.append((row.age_at_event if row.age_at_event is not None else persona.baseline_age,
                      source.created_at if source else row.created_at, 0, "interpretation", row))
    for row in interventions:
        items.append((row.age_at_intervention, row.created_at, 1, "intervention", row))
    items.sort(key=lambda item: (item[0], item[1], item[2]))

    for age, _, _, kind, row in items:
        if kind == "interpretation":
            prefix_interpretations.append(_interpretation_dict(row))
            current_pattern_state = accumulate_patterns(prefix_interpretations, all_protective, all_functional)
            strategy_state = current_pattern_state.get(row.adaptation_strategy)
            persona.current_state = apply_state_update(persona.current_state, row.state_implications)
            persona.current_personality = apply_trait_update(persona.current_personality, row.trait_implications,
                                                              gate_open=trait_gate_open(strategy_state))
            persona.current_attachment_dimensions = apply_attachment_update(persona.current_attachment_dimensions, row.state_implications)
            source_id = row.source_event_id
            snapshot_kind = "experience"
        else:
            strategy_state = current_pattern_state.get(row.targeted_adaptation_strategy)
            prior = [i.efficacy_match for i in applied_interventions if i.targeted_adaptation_strategy == row.targeted_adaptation_strategy]
            gate = intervention_trait_gate_open(strategy_state, prior, row.efficacy_match)
            persona.current_state = apply_state_update(persona.current_state, row.state_implications)
            persona.current_personality = apply_trait_update(persona.current_personality, row.trait_implications,
                                                              gate_open=gate, allow_provisional=False)
            persona.current_attachment_dimensions = apply_attachment_update(persona.current_attachment_dimensions, row.state_implications)
            applied_interventions.append(row)
            source_id = row.id
            snapshot_kind = "intervention"
        persona.current_attachment_style = derive_attachment_style(persona.current_attachment_dimensions)
        snapshots.append((snapshot_kind, source_id, age, dict(persona.current_personality), dict(persona.current_state),
                          persona.current_attachment_style, dict(persona.current_attachment_dimensions)))

    final_patterns = accumulate_patterns(prefix_interpretations, all_protective, all_functional)
    _reconcile_patterns(db, persona, final_patterns)
    db.flush()
    adaptation_dicts = [{"id": p.id, "adaptation_strategy": p.adaptation_strategy, "pattern_name": p.pattern_name,
                         "status": p.status, "evidence_strength": p.evidence_strength,
                         "first_emerged_age": p.first_emerged_age}
                        for p in db.query(AdaptationPattern).filter_by(persona_id=persona.id).all()]
    evidence = accumulate_evidence([_exposure_dict(e) for e in exposures], all_protective,
                                   [_narration_dict(n) for n in narration], all_functional,
                                   adaptation_patterns=adaptation_dicts)
    _reconcile_hypotheses(db, persona, evidence)
    persona.current_trauma_markers = project_current_trauma_markers(evidence)
    persona.current_age = max([persona.baseline_age] + [e.age_at_event for e in experiences] + [i.age_at_intervention for i in interventions])

    db.query(PersonalitySnapshot).filter_by(persona_id=persona.id).delete(synchronize_session=False)
    for kind, source_id, age, personality, state, style, dimensions in snapshots:
        if kind == "interpretation" or source_id is None:
            continue
        db.add(PersonalitySnapshot(persona_id=persona.id,
            experience_id=source_id if kind == "experience" else None,
            intervention_id=source_id if kind == "intervention" else None,
            age=age, personality_profile=personality, state_profile=state or None,
            attachment_style=style, attachment_dimensions=dimensions,
            trauma_markers=list(persona.current_trauma_markers), symptom_severity={}))
    db.flush()
    return persona
