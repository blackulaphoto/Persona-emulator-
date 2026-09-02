"""
PersonalitySnapshot rebuild from V2 sparse change points - PERSISTENCE PHASE.

Correction A never asked the model for a full state at every event - only
direction+magnitude at the events that actually moved something. This module
is the "software can later carry forward values to reconstruct snapshots"
half of that design: a documented, approximate, deterministic reconstruction,
not a request for more precision from the model.

Algorithm: starting from the known baseline value for each trait/dimension,
walk change_points in chronological order and apply a fixed magnitude-to-
delta convention (mild=0.05, moderate=0.10, substantial=0.20 on the 0-1
scale), clamped to [0,1]. This is necessarily an approximation between
events - the model was never asked for exact intermediate values, only the
direction and rough size of each real movement. To guarantee the timeline
ends in agreement with what Persona.current_* actually holds (what Dashboard
reads), the LAST snapshot (by age) is hard-set to the known exact current_*
values rather than left to the running approximation - only points strictly
before the most recent one are approximate.

Only writes personality_snapshots. timeline_snapshots was examined and found
to be a different feature entirely (remix.py's hypothetical "what-if" branch
snapshots, gated behind its own require_remix_feature dependency) - see
persistence_service.py's module docstring for why V2 does not write there.
"""
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import PersonalitySnapshot
from app.services.whole_life_formulation.request_assembler import LifeSourceData
from app.services.whole_life_formulation.schema import WholeLifeFormulation

MAGNITUDE_DELTA = {"mild": 0.05, "moderate": 0.10, "substantial": 0.20}

BIG_FIVE_TRAITS = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
ATTACHMENT_DIMS = ("attachment_anxiety", "attachment_avoidance", "relational_security")
STATE_DIMS = ("trust", "threat_sensitivity", "mood", "regulation", "avoidance", "relational_security")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _running_values(
    baseline: Dict[str, float],
    ordered_experience_ids: List[str],
    events_by_experience: Dict[str, List[tuple]],  # experience_id -> [(field, signed_delta), ...]
) -> Dict[str, Dict[str, float]]:
    """Returns {experience_id: {field: value}} for every experience_id in ordered_experience_ids,
    carrying the running value forward across experiences with no event for a given field."""
    running = dict(baseline)
    out: Dict[str, Dict[str, float]] = {}
    for exp_id in ordered_experience_ids:
        for field, delta in events_by_experience.get(exp_id, []):
            running[field] = _clamp(running.get(field, baseline.get(field, 0.5)) + delta)
        out[exp_id] = dict(running)
    return out


def rebuild_personality_snapshots(db: Session, persona_id: str, formulation: WholeLifeFormulation, life: LifeSourceData) -> None:
    """Replaces (not duplicates) this persona's personality_snapshots with a fresh
    rebuild from the accepted formulation's sparse change_points."""
    db.query(PersonalitySnapshot).filter(PersonalitySnapshot.persona_id == persona_id).delete(synchronize_session=False)

    ordered_experience_ids = [e.id for e in sorted(life.experiences, key=lambda e: (e.age_at_event, e.sequence_index))]
    if not ordered_experience_ids:
        return

    baseline_personality = {t: getattr(formulation.baseline_personality, t).value for t in BIG_FIVE_TRAITS}
    baseline_attachment_dims = {d: getattr(formulation.baseline_attachment, d).value for d in ATTACHMENT_DIMS}
    # State has no baseline concept in this schema (current_state only) - start
    # flat at the current value's... actually start undefined (None) and only
    # populate once a change_point first touches a dimension, matching the
    # rest of this codebase's "state starts empty, not seeded" convention
    # (see Persona.current_state's own docstring in app/models/persona.py).
    baseline_state = {d: None for d in STATE_DIMS}

    personality_events: Dict[str, List[tuple]] = {}
    attachment_events: Dict[str, List[tuple]] = {}
    state_events: Dict[str, List[tuple]] = {}

    for cp in sorted(formulation.change_points, key=lambda c: c.age):
        for pc in cp.personality_changes:
            delta = MAGNITUDE_DELTA[pc.magnitude] * (1 if pc.direction == "increase" else -1)
            personality_events.setdefault(cp.experience_id, []).append((pc.trait, delta))
        for ac in cp.attachment_changes:
            delta = MAGNITUDE_DELTA[ac.magnitude] * (1 if ac.direction == "increase" else -1)
            attachment_events.setdefault(cp.experience_id, []).append((ac.dimension, delta))
        for sc in cp.state_changes:
            delta = MAGNITUDE_DELTA[sc.magnitude] * (1 if sc.direction == "increase" else -1)
            state_events.setdefault(cp.experience_id, []).append((sc.dimension, delta))

    personality_by_exp = _running_values(baseline_personality, ordered_experience_ids, personality_events)

    # For attachment/state, running values start at baseline/None and only
    # move at an actual event - _running_values needs a real starting dict
    # for state too, so seed missing dims at 0.5 (neutral) only for the
    # purpose of computing deltas; a dimension never touched by any event
    # stays out of the persisted snapshot's state_profile entirely (see
    # below) rather than reporting a fabricated neutral value.
    attachment_by_exp = _running_values(baseline_attachment_dims, ordered_experience_ids, attachment_events)
    state_seed = {d: 0.5 for d in STATE_DIMS}
    state_by_exp_raw = _running_values(state_seed, ordered_experience_ids, state_events)
    touched_state_dims = set()
    for events in state_events.values():
        for field, _ in events:
            touched_state_dims.add(field)

    current_personality = {t: getattr(formulation.current_personality, t).value for t in BIG_FIVE_TRAITS}
    current_attachment_dims = {d: getattr(formulation.current_attachment, d).value for d in ATTACHMENT_DIMS}
    current_state = {d: getattr(formulation.current_state, d).value for d in STATE_DIMS}
    last_experience_id = ordered_experience_ids[-1]

    for exp in sorted(life.experiences, key=lambda e: (e.age_at_event, e.sequence_index)):
        is_last = exp.id == last_experience_id
        personality_profile = current_personality if is_last else personality_by_exp.get(exp.id, baseline_personality)
        attachment_dims = current_attachment_dims if is_last else attachment_by_exp.get(exp.id, baseline_attachment_dims)
        if is_last:
            state_profile = current_state
        else:
            raw = state_by_exp_raw.get(exp.id, {})
            state_profile = {d: raw[d] for d in touched_state_dims if d in raw} or None

        db.add(PersonalitySnapshot(
            persona_id=persona_id,
            experience_id=exp.id,
            age=exp.age_at_event,
            personality_profile=personality_profile,
            attachment_style=formulation.current_attachment.style if is_last else formulation.baseline_attachment.style,
            attachment_dimensions=attachment_dims,
            trauma_markers=[],  # V2 does not populate the legacy trauma_markers projection
            symptom_severity={},
            state_profile=state_profile,
        ))
