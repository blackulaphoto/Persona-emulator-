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
    StateImplication,
    TraitImplication,
    STATE_VARIABLES,
    STATE_VARIABLE_DEFINITIONS,
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

# Provisional (pre-establishment) Trait movement - Step 12.
#
# The original Step 11 gate was binary: until an adaptation reached
# "established", Big Five did not move at all. That correctly killed
# "one bad day moves neuroticism 20 points", but overcorrected into "major
# experiences happen and the dials look frozen" - confirmed on a real
# six-event run where a sexual assault at 20 produced zero Big Five movement.
#
# A meaningful event now produces a small, immediate, provisional trait
# adjustment; crossing the establishment gate still produces the larger
# TRAIT_STEP movement above. Roughly half of TRAIT_STEP, and still far below
# STATE_STEP - so the tier ordering the whole architecture rests on holds:
# State reacts hardest, Trait provisionally nudges, established patterns move
# Trait properly. A "high" provisional nudge is 0.035 (3.5 display points):
# visible, not a videogame stat.
PROVISIONAL_TRAIT_STEP: Dict[str, float] = {"mild": 0.01, "moderate": 0.02, "high": 0.035}

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
    state_list = "\n".join(f'- "{v}": {STATE_VARIABLE_DEFINITIONS[v]}' for v in STATE_VARIABLES)
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
1. STATE (fast-moving, reactive) - can shift meaningfully from ONE event. This is where a single event leaves its clearest mark. Allowed variables (use ONLY these EXACT names):
{state_list}
2. TRAIT (slow-moving, enduring personality - the Big Five) - moves far less per event than State. Allowed traits (use ONLY these EXACT names):
{trait_list}

This adaptation is {'ESTABLISHED - repeated reinforcement has earned durable trait movement.' if established else 'NOT yet established - any trait movement here is provisional, reflecting a real but not-yet-enduring shift.'}

INSTRUCTIONS:
1. For state_changes: propose direction ("increase"/"decrease"/"no_change") and magnitude ("mild"/"moderate"/"high") for whichever State variables this event plausibly moves. Do not force an entry for every variable - only the ones this event actually implicates.
2. For trait_changes: propose direction, magnitude, and your own evidence_strength ("low"/"moderate"/"high") for whichever Big Five traits this event plausibly shifts, using the SAME mild/moderate/high magnitude scale. Code applies a much smaller step to traits than to state, and a smaller step again when the pattern is not yet established - so propose the psychologically honest direction and relative magnitude and let the code scale it. Only include a trait this event genuinely implicates; an event with no real personality implication should return an empty trait_changes object. Never use a State variable name as a trait, or a trait name as a State variable - they are separate vocabularies listed above.
3. Never invent a raw score. Never address "you" or "the user" - reason about {persona_name} by name.

OUTPUT FORMAT (valid JSON only):
{{
  "state_changes": {{"trust": {{"direction": "decrease", "magnitude": "moderate"}}}},
  "trait_changes": {{"neuroticism": {{"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}}}}
}}

Respond with ONLY the JSON object."""


def _validate_proposal(response: Dict) -> Optional[Dict]:
    """
    Per-field validation with partial salvage (Step 12).

    Previously all-or-nothing: one bad key threw away the whole proposal and
    dropped the caller onto the much coarser heuristic table. That fired for
    real - the model repeatedly proposed "self_reliance" as a STATE variable
    (confusing STATE_VARIABLES with pattern_engine's adaptation_strategy
    vocabulary), and each time it also discarded the perfectly valid `trust`
    and `threat_sensitivity` movements in the same response.

    Now: keep every field that validates, drop only the ones that don't, and
    log what was dropped so prompt/schema drift stays visible. Returns None
    only when nothing at all could be salvaged AND something was actually
    proposed - so a genuinely empty proposal still reads as "no change"
    rather than as a failure needing fallback.
    """
    if not response:
        return None

    raw_state = response.get("state_changes") or {}
    raw_trait = response.get("trait_changes") or {}

    state_changes: Dict[str, Dict] = {}
    trait_changes: Dict[str, Dict] = {}
    dropped: List[str] = []

    for key, value in raw_state.items():
        if key not in STATE_VARIABLES:
            dropped.append(f"state.{key} (not a State variable)")
            continue
        try:
            state_changes[key] = StateImplication(**value).model_dump()
        except (ValidationError, TypeError) as e:
            dropped.append(f"state.{key} ({e.__class__.__name__})")

    for key, value in raw_trait.items():
        if key not in TRAIT_NAMES:
            dropped.append(f"trait.{key} (not a Big Five trait)")
            continue
        try:
            trait_changes[key] = TraitImplication(**value).model_dump()
        except (ValidationError, TypeError) as e:
            dropped.append(f"trait.{key} ({e.__class__.__name__})")

    if dropped:
        logger.warning(
            "State/trait proposal partially salvaged - kept %d state / %d trait, dropped: %s",
            len(state_changes), len(trait_changes), "; ".join(dropped),
        )

    if not state_changes and not trait_changes and (raw_state or raw_trait):
        return None

    return {"state_changes": state_changes, "trait_changes": trait_changes}


async def propose_state_trait_implications_ai(
    persona_name: str,
    age: Optional[int],
    interpretation: Dict,
    pattern_status: Optional[str] = None,
) -> Optional[Dict]:
    """
    AI proposal path. Returns None on failure so the caller can fall back.

    Gated on belief_statement, not adaptation_strategy - a reparative
    interpretation (pattern_engine.interpret_reparative_experience_async)
    deliberately never sets adaptation_strategy (see that module's docstring
    for why), but it still forms a real, grounded belief about the event and
    is just as entitled to propose State movement as an adverse one. Trait
    movement stays correctly conservative either way: trait_gate_open()
    requires status == "established", which only ever comes from
    accumulate_patterns() grouping by adaptation_strategy, so a reparative
    interpretation can still only ever earn the small provisional Trait step,
    never the full established-pattern one.
    """
    if not interpretation or not interpretation.get("belief_statement"):
        return {"state_changes": {}, "trait_changes": {}}

    try:
        response = await openai_service.analyze(
            prompt=_build_state_trait_prompt(persona_name, age, interpretation, pattern_status),
            system_message=(
                "You propose bounded, direction-and-magnitude-only psychological state movement "
                "across two distinct tiers - fast State and slow, evidence-gated Trait. You never "
                "output a raw score and you never address 'the user'. Respond ONLY with valid JSON."
            ),
            temperature=0.0,
            max_tokens=400
        )
        return _validate_proposal(response)
    except Exception as e:
        logger.warning(f"AI state/trait proposal failed, will fall back to heuristic: {e}")
        return None


def propose_state_trait_implications_heuristic(interpretation: Dict, pattern_status: Optional[str] = None) -> Dict:
    """
    Modest rule-based fallback keyed on adaptation_strategy.

    Trait implications are now proposed regardless of pattern_status (Step
    12) - apply_trait_update is the single place that decides HOW MUCH that
    proposal moves the dial (full TRAIT_STEP once established, the much
    smaller PROVISIONAL_TRAIT_STEP before then). Suppressing the proposal
    here as well was double-gating: it made "not established" mean "no trait
    signal exists at all" rather than "this signal has not earned durable
    movement yet", which is exactly the frozen-dials behavior Step 12 fixes.
    """
    if not interpretation or not interpretation.get("belief_statement"):
        return {"state_changes": {}, "trait_changes": {}}

    strategy = interpretation.get("adaptation_strategy")
    if not strategy:
        # Reparative interpretation (no adaptation_strategy by design - see
        # pattern_engine.interpret_reparative_experience_async). Genuinely
        # lower fidelity than the AI path, same as every other heuristic
        # fallback in this rebuild: a small, generic, direction-only nudge
        # rather than an attempt to approximate what a real reasoning pass
        # over the specific reparative factor would conclude.
        return {
            "state_changes": {
                "trust": {"direction": "increase", "magnitude": "mild"},
                "threat_sensitivity": {"direction": "decrease", "magnitude": "mild"},
            },
            "trait_changes": {},
        }

    default = ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS.get(strategy)
    if not default:
        return {"state_changes": {}, "trait_changes": {}}

    return {
        "state_changes": dict(default.get("state", {})),
        "trait_changes": dict(default.get("trait", {})),
    }


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

# Below this much remaining headroom, steps start shrinking proportionally.
# Above it, the full step applies - so ordinary mid-range movement is
# completely unaffected by the taper.
HEADROOM_TAPER_START = 0.5


def _stepped_value(current: Optional[float], direction: Optional[str], magnitude: Optional[str], step_table: Dict[str, float]) -> float:
    """
    Direction + magnitude -> a bounded score, with diminishing returns near
    the rails (Step 12).

    A flat step plus a hard clamp meant a persona with a heavy history pegged
    at exactly 0.00 / 1.00 and then stopped responding entirely - on a real
    six-event run, trust and threat_sensitivity were already railed by age 20,
    so a seventh event would have produced no visible change at all. That is
    the same frozen-dial failure this step exists to fix, just relocated into
    the State tier.

    Steps now shrink in proportion to the headroom remaining in the direction
    of travel, so values approach 0.0/1.0 asymptotically instead of hitting
    them: there is always room for the next event to register, and the engine
    never claims a person has *exactly* zero trust. Movement in the ordinary
    mid-range is unchanged - the taper only engages within
    HEADROOM_TAPER_START of a rail.
    """
    baseline = UNOBSERVED_BASELINE if current is None else current
    step = step_table.get(magnitude, step_table["mild"])

    if direction == "increase":
        headroom = 1.0 - baseline
    elif direction == "decrease":
        headroom = baseline
    else:
        return round(max(0.0, min(1.0, baseline)), 4)

    step *= min(1.0, max(0.0, headroom) / HEADROOM_TAPER_START)
    new_value = baseline + step if direction == "increase" else baseline - step
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


def apply_trait_update(
    current_personality: Optional[Dict[str, float]],
    trait_changes: Optional[Dict[str, Dict]],
    gate_open: bool,
    allow_provisional: bool = True,
) -> Dict[str, float]:
    """
    Returns a NEW dict.

    Two movement sizes, by design (Step 12):
      - gate_open (the adaptation reached "established"): full TRAIT_STEP.
      - gate closed, allow_provisional: the much smaller
        PROVISIONAL_TRAIT_STEP - a meaningful event is allowed to nudge the
        slow tier immediately, without claiming the pattern is enduring yet.

    allow_provisional=False restores the strict Step 11 behavior (no movement
    at all unless established). Interventions pass False: therapy has its own
    sustained-improvement gate (intervention_trait_gate_open), and letting a
    single course of treatment provisionally move Big Five would bypass the
    "one good round is a data point, not proof" rule that gate exists to
    enforce.

    Still does not trust the caller's gate_open blindly - the step table is
    chosen here, so an upstream bug proposing trait movement too early gets
    the provisional step, never the established one.
    """
    updated = dict(current_personality or {})
    if not gate_open and not allow_provisional:
        return updated
    step_table = TRAIT_STEP if gate_open else PROVISIONAL_TRAIT_STEP
    for trait, implication in (trait_changes or {}).items():
        if trait not in TRAIT_NAMES:
            continue
        updated[trait] = _stepped_value(updated.get(trait), implication.get("direction"), implication.get("magnitude"), step_table)
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
    state_list = "\n".join(f'- "{v}": {STATE_VARIABLE_DEFINITIONS[v]}' for v in STATE_VARIABLES)
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
            temperature=0.0,
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
