"""
State/Trait Engine (docs/MIGRATION_MAP.md, Step 11).

Converts one Interpretation's belief/adaptation/reasoning into proposed
movement on the two tiers introduced in Step 11a:
  - State (Persona.current_state) - fast-moving, can shift after a single
    event: trust, threat_sensitivity, mood, regulation, avoidance,
    relational_security.
  - Trait (Persona.current_personality, the existing Big Five) - slow-moving.
    Movement is only ever APPLIED (see apply_trait_update) when the
    interpretation's adaptation_strategy has reached AdaptationPattern.
    status == "established" in pattern_engine.accumulate_patterns() - the
    same evidence bar step 5 already requires to call something a real
    pattern, not a reaction to one event. A single interpretation, however
    dramatic, proposes a trait_implication but it is never applied until
    that bar is crossed - this is the literal fix for "one bad day moves
    neuroticism."

Same AI-primary + heuristic-fallback shape as every other engine in this
rebuild. The AI (and the heuristic) only ever propose a direction and a
3-tier magnitude (mild | moderate | high) - never a raw number. Code (see
apply_state_update / apply_trait_update) converts that into a small, fixed,
bounded score change. This is deliberately NOT a per-exposure or per-event
coefficient table - the only hardcoded numbers are the two step-size maps
below, sized the same way REINFORCE_INCREMENT/WEAKEN_DECREMENT are in
pattern_engine.py: simple and transparent, not a formula dressed up as
precision.

A dedicated second AI call per event (conditioned on the interpretation
already produced by pattern_engine.interpret_experience_ai), rather than
folding these fields into that function's own prompt/output - interpret_
experience_ai's contract already has 28 passing tests and is used to open
the Interpretation row itself; splitting this into its own call keeps that
contract untouched and keeps this proposal independently testable.
"""
import logging
from typing import Dict, List, Optional

from pydantic import ValidationError

from app.services.openai_service import OpenAIService
from app.schemas.developmental_analysis_schemas import (
    DevelopmentalAnalysisResult,
    STATE_VARIABLES,
    TRAIT_NAMES,
)

logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=None,
    model="gpt-4o"
)


# ============================================================
# Bounded, deterministic step sizes (0.0-1.0 scale, matching Persona.
# current_personality's existing convention - current_state adopts the same
# scale for consistency, not a 0-100 scale, so both tiers compose cleanly).
# State moves relatively freely per event; Trait moves in much smaller steps
# and only when gated open.
# ============================================================
STATE_STEP: Dict[str, float] = {"mild": 0.05, "moderate": 0.12, "high": 0.22}
TRAIT_STEP: Dict[str, float] = {"mild": 0.02, "moderate": 0.04, "high": 0.07}

# Neutral starting point the first time a State variable is ever touched -
# current_state starts at {} (Step 11a), same "unearned defaults are what
# this rebuild removed elsewhere" reasoning as current_trauma_markers.
UNOBSERVED_BASELINE = 0.5


# ============================================================
# Modest rule-based fallback, keyed on adaptation_strategy (the same 12-
# value controlled vocabulary pattern_engine.py already groups Interpretations
# by) rather than a much larger per-exposure-type or per-event table. Sized
# like the other fallback tables in this rebuild (EXPOSURE_INTERPRETATION_
# DEFAULTS: 18 entries, PATTERN_KEY_THERAPY_ALIASES: 6) - genuinely lower
# fidelity than the AI path by design, not a credible substitute for
# reasoning over the specific event. Several strategies deliberately have no
# trait_changes entry at all (self_reliance, humor, intellectualization) -
# a strategy with no clear single-trait implication is left unmapped rather
# than forced into a guess, same principle as PATTERN_KEY_THERAPY_ALIASES's
# non-exhaustiveness.
# ============================================================
ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS: Dict[str, Dict] = {
    "hypervigilance": {
        "state": {"threat_sensitivity": {"direction": "increase", "magnitude": "moderate"},
                   "regulation": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {"neuroticism": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "emotional_distancing": {
        "state": {"relational_security": {"direction": "decrease", "magnitude": "moderate"}},
        "trait": {"extraversion": {"direction": "decrease", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "people_pleasing": {
        "state": {"regulation": {"direction": "decrease", "magnitude": "mild"},
                   "relational_security": {"direction": "increase", "magnitude": "mild"}},
        "trait": {"agreeableness": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "control_seeking": {
        "state": {"threat_sensitivity": {"direction": "increase", "magnitude": "mild"}},
        "trait": {"conscientiousness": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "aggression": {
        "state": {"regulation": {"direction": "decrease", "magnitude": "moderate"},
                   "mood": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {"agreeableness": {"direction": "decrease", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "avoidance": {
        "state": {"avoidance": {"direction": "increase", "magnitude": "high"},
                   "relational_security": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {"extraversion": {"direction": "decrease", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "self_reliance": {
        "state": {"trust": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {},
    },
    "perfectionism": {
        "state": {"regulation": {"direction": "decrease", "magnitude": "mild"},
                   "threat_sensitivity": {"direction": "increase", "magnitude": "mild"}},
        "trait": {"conscientiousness": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "humor": {
        "state": {"mood": {"direction": "increase", "magnitude": "mild"}},
        "trait": {},
    },
    "caretaking": {
        "state": {"relational_security": {"direction": "increase", "magnitude": "mild"},
                   "regulation": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {"agreeableness": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
    },
    "substance_use": {
        "state": {"regulation": {"direction": "decrease", "magnitude": "high"},
                   "mood": {"direction": "decrease", "magnitude": "mild"}},
        "trait": {"neuroticism": {"direction": "increase", "magnitude": "moderate", "evidence_strength": "low"}},
    },
    "intellectualization": {
        "state": {"regulation": {"direction": "increase", "magnitude": "mild"}},
        "trait": {},
    },
}


# ============================================================
# AI proposal path
# ============================================================

def _build_state_trait_prompt(
    persona_name: str,
    age: Optional[int],
    interpretation: Dict,
    pattern_status: Optional[str],
) -> str:
    state_list = "\n".join(f'- "{v}"' for v in STATE_VARIABLES)
    trait_list = "\n".join(f'- "{t}"' for t in TRAIT_NAMES)
    established = pattern_status == "established"

    return f"""You are proposing how a single developmental event moves {persona_name}'s psychological state, on two distinct tiers. You never output a number - only a direction and a magnitude. Code applies the actual bounded movement.

PERSONA: {persona_name}, age {age if age is not None else 'unknown'}

THIS EVENT'S INTERPRETATION:
- Belief formed/reinforced: {interpretation.get('belief_statement') or '(none)'}
- Adaptation strategy: {interpretation.get('adaptation_strategy') or '(none)'}
- Reasoning: {interpretation.get('reasoning') or '(none)'}

THIS ADAPTATION STRATEGY'S PATTERN STATUS: {pattern_status or 'not yet a pattern'}

TWO TIERS - DO NOT CONFUSE THEM:
1. STATE (fast-moving, reactive) - can shift meaningfully from ONE event. Allowed variables (use ONLY these):
{state_list}
2. TRAIT (slow-moving, enduring personality) - {persona_name} has NOT earned trait movement from a single event. Only propose trait_changes if the pattern status above is exactly "established" ({'it IS established for this event' if established else 'it is NOT established for this event - return an empty trait_changes object'}). Allowed traits (use ONLY these):
{trait_list}

INSTRUCTIONS:
1. For state_changes: propose direction ("increase"/"decrease"/"no_change") and magnitude ("mild"/"moderate"/"high") for whichever State variables this event plausibly moves. Do not force an entry for every variable - only the ones this event actually implicates.
2. For trait_changes: {'propose direction, magnitude, and your own evidence_strength ("low"/"moderate"/"high") for whichever traits this established pattern plausibly shifts.' if established else 'return {} (empty object) - this pattern has not earned trait movement yet.'}
3. Never invent a raw score. Never address "you" or "the user" - reason about {persona_name} by name.

OUTPUT FORMAT (valid JSON only):
{{
  "state_changes": {{"trust": {{"direction": "decrease", "magnitude": "moderate"}}}},
  "trait_changes": {{}}
}}

Respond with ONLY the JSON object."""


def _validate_proposal(response: Dict) -> Optional[Dict]:
    """Reuses DevelopmentalAnalysisResult's own field validation rather than duplicating it."""
    if not response:
        return None
    try:
        validated = DevelopmentalAnalysisResult(
            state_changes=response.get("state_changes") or {},
            trait_changes=response.get("trait_changes") or {},
        )
    except ValidationError as e:
        logger.warning(f"State/trait proposal failed validation: {e}")
        return None
    return {
        "state_changes": {k: v.model_dump() for k, v in validated.state_changes.items()},
        "trait_changes": {k: v.model_dump() for k, v in validated.trait_changes.items()},
    }


async def propose_state_trait_implications_ai(
    persona_name: str,
    age: Optional[int],
    interpretation: Dict,
    pattern_status: Optional[str] = None,
) -> Optional[Dict]:
    """AI proposal path. Returns None on failure so the caller can fall back."""
    if not interpretation or not interpretation.get("adaptation_strategy"):
        return {"state_changes": {}, "trait_changes": {}}

    try:
        response = await openai_service.analyze(
            prompt=_build_state_trait_prompt(persona_name, age, interpretation, pattern_status),
            system_message=(
                "You propose bounded, direction-and-magnitude-only psychological state movement "
                "across two distinct tiers - fast State and slow, evidence-gated Trait. You never "
                "output a raw score and you never address 'the user'. Respond ONLY with valid JSON."
            ),
            temperature=0.4,
            max_tokens=400
        )
        return _validate_proposal(response)
    except Exception as e:
        logger.warning(f"AI state/trait proposal failed, will fall back to heuristic: {e}")
        return None


def propose_state_trait_implications_heuristic(interpretation: Dict, pattern_status: Optional[str] = None) -> Dict:
    """
    Modest rule-based fallback keyed on adaptation_strategy. Trait movement
    is only ever proposed here when pattern_status == "established" - the
    same gate the AI prompt is instructed to honor, enforced again at the
    fallback level as defense in depth (the real enforcement is apply_
    trait_update, which does not trust either path's trait_changes without
    re-checking the gate itself).
    """
    if not interpretation or not interpretation.get("adaptation_strategy"):
        return {"state_changes": {}, "trait_changes": {}}

    default = ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS.get(interpretation["adaptation_strategy"])
    if not default:
        return {"state_changes": {}, "trait_changes": {}}

    state_changes = dict(default.get("state", {}))
    trait_changes = dict(default.get("trait", {})) if pattern_status == "established" else {}
    return {"state_changes": state_changes, "trait_changes": trait_changes}


async def propose_state_trait_implications_async(
    persona_name: str,
    age: Optional[int],
    interpretation: Dict,
    pattern_status: Optional[str] = None,
) -> Dict:
    result = await propose_state_trait_implications_ai(persona_name, age, interpretation, pattern_status)
    if result is not None:
        return result
    logger.info("Using heuristic fallback for state/trait proposal")
    return propose_state_trait_implications_heuristic(interpretation, pattern_status)


def propose_state_trait_implications(
    persona_name: str,
    age: Optional[int],
    interpretation: Dict,
    pattern_status: Optional[str] = None,
) -> Dict:
    """Sync wrapper, mirroring the pattern used by every prior engine in this rebuild."""
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("propose_state_trait_implications called in async context; using heuristic fallback.")
            return propose_state_trait_implications_heuristic(interpretation, pattern_status)
    except RuntimeError:
        pass

    try:
        return asyncio.run(propose_state_trait_implications_async(persona_name, age, interpretation, pattern_status))
    except Exception as e:
        logger.warning(f"State/trait proposal failed entirely, using heuristic fallback: {e}")
        return propose_state_trait_implications_heuristic(interpretation, pattern_status)


# ============================================================
# Deterministic, bounded apply functions - the only place any number is
# actually computed. Direction/magnitude in, a small fixed-step, 0.0-1.0-
# clamped score out. No event-type or age coefficient anywhere here.
# ============================================================

def _stepped_value(current: Optional[float], direction: Optional[str], magnitude: Optional[str], step_table: Dict[str, float]) -> float:
    baseline = UNOBSERVED_BASELINE if current is None else current
    step = step_table.get(magnitude, step_table["mild"])
    if direction == "increase":
        new_value = baseline + step
    elif direction == "decrease":
        new_value = baseline - step
    else:
        new_value = baseline
    return round(max(0.0, min(1.0, new_value)), 4)


def apply_state_update(current_state: Optional[Dict[str, float]], state_changes: Optional[Dict[str, Dict]]) -> Dict[str, float]:
    """Returns a NEW dict - callers reassign persona.current_state to it (plain attribute reassignment, no flag_modified needed)."""
    updated = dict(current_state or {})
    for variable, implication in (state_changes or {}).items():
        if variable not in STATE_VARIABLES:
            continue
        updated[variable] = _stepped_value(updated.get(variable), implication.get("direction"), implication.get("magnitude"), STATE_STEP)
    return updated


def trait_gate_open(pattern_state: Optional[Dict]) -> bool:
    """
    The single place trait-movement eligibility is decided: status must be
    exactly "established" (pattern_engine.accumulate_patterns()'s highest
    evidence bar - requires real recurrence, not one interpretation).
    "weakening"/"resolved"/"emerging" all stay closed - trait recovery on a
    weakening pattern is a real future question, deliberately not decided
    here rather than silently guessed at.
    """
    return bool(pattern_state) and pattern_state.get("status") == "established"


def apply_trait_update(current_personality: Optional[Dict[str, float]], trait_changes: Optional[Dict[str, Dict]], gate_open: bool) -> Dict[str, float]:
    """
    Returns a NEW dict. Does not trust the caller's trait_changes without
    re-checking gate_open itself - if the gate is closed, returns the
    personality dict unchanged regardless of what trait_changes contains,
    so a bug upstream that proposes trait movement too early cannot apply
    it silently.
    """
    updated = dict(current_personality or {})
    if not gate_open:
        return updated
    for trait, implication in (trait_changes or {}).items():
        if trait not in TRAIT_NAMES:
            continue
        updated[trait] = _stepped_value(updated.get(trait), implication.get("direction"), implication.get("magnitude"), TRAIT_STEP)
    return updated


# ============================================================
# Intervention state/trait proposal (Step 11e, docs/MIGRATION_MAP.md).
#
# Therapy is a different kind of input than a developmental event: it's a
# deliberate, bounded course of treatment with its own AI-assessed efficacy_
# match (intervention_engine.analyze_intervention), not a single interpreted
# exposure. Two things follow:
#
# 1. There is no single "adaptation_strategy" this call produced - instead
#    intervention_engine._select_targeted_pattern() picks the established
#    AdaptationPattern this course of therapy is presumed aimed at (or None,
#    if the persona has no established pattern yet). The heuristic fallback
#    below reuses ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS for that pattern's
#    strategy and proposes the INVERSE direction - therapy is presumed to
#    work against whatever the original adaptation strategy did, at a
#    magnitude tied to this intervention's own real efficacy_match rather
#    than a new coefficient table.
#
# 2. Trait movement from therapy is gated on MORE than one course of
#    treatment - one good round of therapy is a data point, not evidence
#    that the underlying pattern has actually shifted. intervention_trait_
#    gate_open() requires BOTH the targeted pattern to be a real, established
#    one (reuses trait_gate_open - not duplicated) AND documented improvement
#    (efficacy_match at/above INTERVENTION_IMPROVEMENT_THRESHOLD) recorded on
#    at least INTERVENTION_SUSTAINED_COUNT interventions that targeted that
#    same pattern, this one included.
# ============================================================

INTERVENTION_IMPROVEMENT_THRESHOLD = 0.5  # matches analyze_intervention's own "0.5-0.8 = Moderate match" framing
INTERVENTION_SUSTAINED_COUNT = 2  # documented-improvement interventions (incl. this one) required before Trait can move

_INVERT_DIRECTION: Dict[str, str] = {"increase": "decrease", "decrease": "increase", "no_change": "no_change"}


def _efficacy_magnitude(efficacy_match: Optional[float]) -> str:
    """Efficacy match -> STATE_STEP/TRAIT_STEP tier. Mirrors the prompt's own 0.5/0.8 efficacy bands."""
    if efficacy_match is None:
        return "mild"
    if efficacy_match >= 0.75:
        return "high"
    if efficacy_match >= 0.5:
        return "moderate"
    return "mild"


def intervention_trait_gate_open(
    pattern_state: Optional[Dict],
    prior_documented_efficacy: Optional[List[Optional[float]]],
    this_efficacy_match: Optional[float],
) -> bool:
    """
    The single place intervention-driven Trait eligibility is decided.
    prior_documented_efficacy: efficacy_match values from this persona's
    OTHER interventions that targeted the same pattern (any value, not
    pre-filtered) - filtering for "documented improvement" happens here, not
    in the caller, for the same defense-in-depth reason apply_trait_update
    re-checks gate_open itself rather than trusting it.
    """
    if not trait_gate_open(pattern_state):
        return False
    documented = [
        e for e in (prior_documented_efficacy or [])
        if e is not None and e >= INTERVENTION_IMPROVEMENT_THRESHOLD
    ]
    if this_efficacy_match is not None and this_efficacy_match >= INTERVENTION_IMPROVEMENT_THRESHOLD:
        documented.append(this_efficacy_match)
    return len(documented) >= INTERVENTION_SUSTAINED_COUNT


def _build_intervention_state_trait_prompt(
    persona_name: str,
    age: Optional[int],
    therapy_type: str,
    targeted_adaptation_strategy: Optional[str],
    efficacy_match: Optional[float],
    trait_eligible: bool,
) -> str:
    state_list = "\n".join(f'- "{v}"' for v in STATE_VARIABLES)
    trait_list = "\n".join(f'- "{t}"' for t in TRAIT_NAMES)

    return f"""You are proposing how a completed course of therapy moves {persona_name}'s psychological state, on two distinct tiers. You never output a number - only a direction and a magnitude. Code applies the actual bounded movement.

PERSONA: {persona_name}, age {age if age is not None else 'unknown'}

THERAPY: {therapy_type}
TARGETED PATTERN (adaptation strategy this course of treatment is presumed aimed at): {targeted_adaptation_strategy or '(none - persona has no established pattern yet)'}
EFFICACY MATCH (0.0-1.0, already assessed): {efficacy_match if efficacy_match is not None else 'unknown'}

TWO TIERS - DO NOT CONFUSE THEM:
1. STATE (fast-moving, reactive) - therapy can shift this meaningfully within one course of treatment. Allowed variables (use ONLY these):
{state_list}
2. TRAIT (slow-moving, enduring personality) - {persona_name} has NOT earned trait movement from a single course of therapy. Only propose trait_changes if told below that trait movement is eligible this call ({'it IS eligible - sustained, documented improvement on this pattern has been recorded' if trait_eligible else 'it is NOT eligible this call - return an empty trait_changes object'}). Allowed traits (use ONLY these):
{trait_list}

INSTRUCTIONS:
1. For state_changes: propose direction ("increase"/"decrease"/"no_change") and magnitude ("mild"/"moderate"/"high") for whichever State variables this therapy plausibly moves, consistent with the efficacy match above (a poor match should propose smaller or no state movement). Do not force an entry for every variable.
2. For trait_changes: {'propose direction, magnitude, and your own evidence_strength ("low"/"moderate"/"high") for whichever traits this sustained improvement plausibly shifts.' if trait_eligible else 'return {} (empty object) - trait movement has not been earned yet.'}
3. Never invent a raw score. Never address "you" or "the user" - reason about {persona_name} by name.

OUTPUT FORMAT (valid JSON only):
{{
  "state_changes": {{"regulation": {{"direction": "increase", "magnitude": "moderate"}}}},
  "trait_changes": {{}}
}}

Respond with ONLY the JSON object."""


async def propose_intervention_state_trait_implications_ai(
    persona_name: str,
    age: Optional[int],
    therapy_type: str,
    targeted_adaptation_strategy: Optional[str],
    efficacy_match: Optional[float],
    trait_eligible: bool,
) -> Optional[Dict]:
    """AI proposal path. Returns None on failure so the caller can fall back."""
    if not targeted_adaptation_strategy:
        # No established pattern to anchor a proposal against - see module
        # docstring section above; left empty rather than guessed, same
        # principle as the developmental engine's own short-circuit.
        return {"state_changes": {}, "trait_changes": {}}

    try:
        response = await openai_service.analyze(
            prompt=_build_intervention_state_trait_prompt(
                persona_name, age, therapy_type, targeted_adaptation_strategy, efficacy_match, trait_eligible
            ),
            system_message=(
                "You propose bounded, direction-and-magnitude-only psychological state movement "
                "from a completed course of therapy, across two distinct tiers - fast State and "
                "slow, evidence-gated Trait. You never output a raw score and you never address "
                "'the user'. Respond ONLY with valid JSON."
            ),
            temperature=0.4,
            max_tokens=400
        )
        return _validate_proposal(response)
    except Exception as e:
        logger.warning(f"AI intervention state/trait proposal failed, will fall back to heuristic: {e}")
        return None


def propose_intervention_state_trait_implications_heuristic(
    targeted_adaptation_strategy: Optional[str],
    efficacy_match: Optional[float],
    trait_eligible: bool,
) -> Dict:
    """
    Reuses ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS (the same table the
    developmental engine's heuristic uses) and proposes the INVERSE
    direction for the targeted pattern's strategy - therapy is presumed to
    work against whatever that strategy originally did. Magnitude comes from
    efficacy_match, not a new coefficient. A strategy with no trait_changes
    entry in the table (self_reliance, humor, intellectualization) stays
    empty here too, same non-exhaustiveness principle.
    """
    if not targeted_adaptation_strategy:
        return {"state_changes": {}, "trait_changes": {}}

    default = ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS.get(targeted_adaptation_strategy)
    if not default:
        return {"state_changes": {}, "trait_changes": {}}

    magnitude = _efficacy_magnitude(efficacy_match)
    state_changes = {
        variable: {"direction": _INVERT_DIRECTION.get(implication["direction"], "no_change"), "magnitude": magnitude}
        for variable, implication in default.get("state", {}).items()
    }
    trait_changes = {}
    if trait_eligible:
        trait_changes = {
            trait: {
                "direction": _INVERT_DIRECTION.get(implication["direction"], "no_change"),
                "magnitude": magnitude,
                "evidence_strength": "low",
            }
            for trait, implication in default.get("trait", {}).items()
        }
    return {"state_changes": state_changes, "trait_changes": trait_changes}


async def propose_intervention_state_trait_implications_async(
    persona_name: str,
    age: Optional[int],
    therapy_type: str,
    targeted_adaptation_strategy: Optional[str],
    efficacy_match: Optional[float],
    trait_eligible: bool,
) -> Dict:
    result = await propose_intervention_state_trait_implications_ai(
        persona_name, age, therapy_type, targeted_adaptation_strategy, efficacy_match, trait_eligible
    )
    if result is not None:
        return result
    logger.info("Using heuristic fallback for intervention state/trait proposal")
    return propose_intervention_state_trait_implications_heuristic(targeted_adaptation_strategy, efficacy_match, trait_eligible)


def propose_intervention_state_trait_implications(
    persona_name: str,
    age: Optional[int],
    therapy_type: str,
    targeted_adaptation_strategy: Optional[str],
    efficacy_match: Optional[float],
    trait_eligible: bool,
) -> Dict:
    """Sync wrapper, mirroring propose_state_trait_implications's shape."""
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("propose_intervention_state_trait_implications called in async context; using heuristic fallback.")
            return propose_intervention_state_trait_implications_heuristic(targeted_adaptation_strategy, efficacy_match, trait_eligible)
    except RuntimeError:
        pass

    try:
        return asyncio.run(propose_intervention_state_trait_implications_async(
            persona_name, age, therapy_type, targeted_adaptation_strategy, efficacy_match, trait_eligible
        ))
    except Exception as e:
        logger.warning(f"Intervention state/trait proposal failed entirely, using heuristic fallback: {e}")
        return propose_intervention_state_trait_implications_heuristic(targeted_adaptation_strategy, efficacy_match, trait_eligible)
