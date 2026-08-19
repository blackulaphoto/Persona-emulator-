"""
Legacy Experience Adapter (docs/MIGRATION_MAP.md, Step 11d).

Translates developmental_pipeline.process_developmental_text()'s output
into the exact dict shape app/api/routes/experiences.py has always built
an Experience row from (immediate_effects, long_term_patterns,
symptoms_developed, symptom_severity, coping_mechanisms, worldview_shifts,
cross_experience_triggers, recommended_therapies) - the response shape
ExperienceResponse enforces and the frontend already renders. This is what
lets experiences.py stop calling psychology_engine.analyze_experience()'s
independent per-experience GPT call without touching the frontend contract.

Confirmed via a repo-wide check of frontend/ before writing this: only
immediate_effects (indirectly, via current_personality) and symptom_severity
are actually rendered anywhere in the UI (frontend/app/persona/[id]/page.tsx)
- long_term_patterns, coping_mechanisms, worldview_shifts, cross_experience_
triggers, and recommended_therapies are declared in the TypeScript API type
(frontend/lib/api.ts) but never read by any component. That materially
lowers the risk of this swap and is why several fields below are populated
with an honest best-effort translation rather than a byte-for-byte replica
of psychology_engine's old shape - there is no display contract to match
for them, only a type contract.

immediate_effects specifically changes meaning here: it no longer means
"the AI's independently-decided new Big Five values" (the old, ungated
behavior this rebuild is retiring). It now means "current_personality as of
right after this call" - the Trait tier's real value, already updated (or
correctly left untouched) by state_trait_engine's gate. The field name is
kept for response-shape compatibility; what it represents is not the same
claim anymore.

cross_experience_triggers and recommended_therapies are left as [] -
building them honestly would mean either using Interpretation.pattern_id/
reinforcement_effect (not currently populated by any writer - a separate,
un-flagged gap, not something to paper over here) or duplicating
intervention_engine.py's PATTERN_KEY_THERAPY_ALIASES cross-engine coupling
for a field nothing renders. Left empty and documented rather than
fabricated.
"""
from typing import Dict, Optional

# Direction+magnitude -> a bounded float in the old worldview_shifts shape
# (-1.0 to +1.0). Purely a display-shape translation for a field nothing in
# the frontend actually reads - not reused as input to any other
# computation. Not the same table as state_trait_engine.STATE_STEP, which
# governs the real bounded score movement.
_WORLDVIEW_MAGNITUDE = {"mild": 0.15, "moderate": 0.35, "high": 0.6}


def _worldview_shifts_from_state_changes(state_changes: Optional[Dict]) -> Dict[str, float]:
    shifts = {}
    for variable, implication in (state_changes or {}).items():
        magnitude = _WORLDVIEW_MAGNITUDE.get(implication.get("magnitude"), _WORLDVIEW_MAGNITUDE["mild"])
        direction = implication.get("direction")
        if direction == "increase":
            shifts[variable] = magnitude
        elif direction == "decrease":
            shifts[variable] = -magnitude
    return shifts


def to_legacy_experience_fields(pipeline_result: Dict, persona) -> Dict:
    """
    Args:
        pipeline_result: process_developmental_text()'s return dict.
        persona: the Persona ORM row, AFTER process_developmental_text() has
            already applied this call's State/Trait movement to it -
            current_personality reflects the real, gated post-update value.

    Returns a dict with exactly the keys app/api/routes/experiences.py has
    always read via analysis.get(...) - safe to use as a drop-in
    replacement for psychology_engine.analyze_experience()'s return value.
    """
    interpretation = pipeline_result.get("interpretation")
    trauma_markers = pipeline_result.get("trauma_markers") or []
    hypotheses = pipeline_result.get("clinical_pattern_hypotheses") or {}

    # symptoms_developed IS trauma_markers - both are "the same real,
    # evidence-earned display list," no reason to maintain two names for
    # one concept just because the old field existed first.
    symptoms_developed = list(trauma_markers)
    symptom_severity = {
        pattern_key: round((hypotheses[pattern_key].get("evidence_strength") or 0) * 10)
        for pattern_key in trauma_markers
        if pattern_key in hypotheses
    }

    long_term_patterns = [interpretation.belief_statement] if (interpretation and interpretation.belief_statement) else []
    coping_mechanisms = [interpretation.adaptation_strategy] if (interpretation and interpretation.adaptation_strategy) else []

    return {
        "immediate_effects": dict(persona.current_personality) if persona.current_personality else {},
        "long_term_patterns": long_term_patterns,
        "symptoms_developed": symptoms_developed,
        "symptom_severity": symptom_severity,
        "coping_mechanisms": coping_mechanisms,
        "worldview_shifts": _worldview_shifts_from_state_changes(pipeline_result.get("state_changes")),
        "cross_experience_triggers": [],
        "recommended_therapies": [],
    }
