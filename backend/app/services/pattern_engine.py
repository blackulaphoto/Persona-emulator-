"""
Pattern/Adaptation Engine.

Implements the core developmental chain from docs/MIGRATION_MAP.md:

    Exposure -> Interpretation -> Adaptation -> Pattern -> Reinforcement -> Current Behavior

This replaces psychology_engine.py's flat event -> disorder -> severity
analysis. For a single experience, interpret_experience() reasons jointly
over:
  - the exposure(s) extracted for this event (step 2)
  - which developmental domains are actually live tasks at this age (a
    replacement for developmental_stages.py's old scalar trauma_impact_
    multiplier - age changes WHAT is vulnerable, not just how much)
  - the persona's existing psychological state (prior AdaptationPatterns)
  - narration signals for how the event was told (step 3)
  - protective factors active at the time (joint input, not a discount)

...and produces an Interpretation: what the event appears to have meant,
and what adaptive strategy it produced or reinforced.

accumulate_patterns() then groups a persona's full history of
Interpretations into named AdaptationPattern state, recomputed from the
whole timeline each call - same philosophy as
evidence_accumulator.accumulate_evidence(): a single interpretation opens a
pattern candidate as "emerging" with no earned strength; only recurrence
across the timeline (reinforcement) earns real evidence_strength. This is
deliberate and mirrors step 4: an inference from one event is not yet a
pattern.
"""
import re
import logging
from typing import Dict, List, Optional

from app.services.openai_service import OpenAIService
from app.utils.developmental_stages import get_developmental_stage
from app.services.self_narration_engine import _enforce_subject_attribution

logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=None,
    model="gpt-4o"
)


# ============================================================
# Controlled vocabulary
# ============================================================
ADAPTATION_STRATEGIES = (
    "hypervigilance",
    "emotional_distancing",
    "people_pleasing",
    "control_seeking",
    "aggression",
    "avoidance",
    "self_reliance",
    "perfectionism",
    "humor",
    "caretaking",
    "substance_use",
    "intellectualization",
)

# Bridges app/utils/developmental_stages.py's key_tasks vocabulary (real,
# existing content) to app/services/developmental_exposure_engine.py's
# DEVELOPMENTAL_DOMAINS vocabulary (step 2), so age-appropriate salience can
# be computed from developmental_stages.py's actual per-stage content
# instead of duplicating it or falling back to a scalar multiplier.
STAGE_TASK_TO_DOMAIN: Dict[str, str] = {
    "attachment_formation": "attachment_security",
    "basic_trust_development": "attachment_security",
    "emotional_regulation_foundation": "emotional_regulation",
    "sense_of_safety": "emotional_safety",
    "identity_formation": "identity",
    "self_concept_development": "identity",
    "peer_relationships": "social_belonging",
    "academic_competence": "competence",
    "social_skills": "social_belonging",
    "identity_consolidation": "identity",
    "autonomy_development": "autonomy",
    "peer_belonging": "social_belonging",
    "sexual_identity": "sexuality",
    "separation_from_parents": "autonomy",
    "attachment_style_crystallization": "attachment_security",
    "career_identity": "competence",
    "intimate_relationships": "intimacy",
    "independence_consolidation": "autonomy",
    "life_direction_setting": "identity",
    "pattern_maintenance_or_change": "stability",
    "generativity": "competence",
    "relationship_maintenance": "intimacy",
    "career_advancement": "competence",
    "meaning_making": "identity",
}

# Modest rule-based fallback: exposure_type -> default (belief, adaptation).
# Used only when the AI path is unavailable. Genuinely lower fidelity than
# the AI path by design - interpretation is inherently a judgment call, and
# this fallback exists so the app degrades gracefully, not as a credible
# substitute for reasoning over the full context.
EXPOSURE_INTERPRETATION_DEFAULTS: Dict[str, Dict] = {
    "caregiver_absence": {"belief": "People leave.", "adaptation": "self_reliance"},
    "caregiver_substance_use": {"belief": "I can't count on my caregivers to be present.", "adaptation": "hypervigilance"},
    "caregiver_emotional_unavailability": {"belief": "My feelings are a burden to others.", "adaptation": "emotional_distancing"},
    "caregiver_mental_illness": {"belief": "I have to manage things others can't.", "adaptation": "caretaking"},
    "household_unpredictability": {"belief": "I need to stay alert to stay safe.", "adaptation": "hypervigilance"},
    "physical_discipline_or_violence": {"belief": "I have to be careful or I'll be hurt.", "adaptation": "hypervigilance"},
    "domestic_violence_witnessed": {"belief": "Conflict is dangerous.", "adaptation": "avoidance"},
    "sexual_boundary_violation": {"belief": "My boundaries aren't respected.", "adaptation": "emotional_distancing"},
    "emotional_abuse_or_humiliation": {"belief": "I have to earn approval.", "adaptation": "perfectionism"},
    "neglect_of_basic_needs": {"belief": "I have to take care of myself.", "adaptation": "self_reliance"},
    "caregiver_incarceration": {"belief": "People I need can be taken away.", "adaptation": "self_reliance"},
    "separation_or_divorce": {"belief": "Relationships don't last.", "adaptation": "control_seeking"},
    "death_of_caregiver_or_family": {"belief": "People I depend on can disappear.", "adaptation": "self_reliance"},
    "frequent_relocation": {"belief": "Nothing stays the same for long.", "adaptation": "self_reliance"},
    "financial_instability": {"belief": "Resources can't be counted on.", "adaptation": "control_seeking"},
    "peer_rejection_or_bullying": {"belief": "I don't fit in.", "adaptation": "avoidance"},
    "high_achievement_pressure": {"belief": "I have to stay useful to be valued.", "adaptation": "perfectionism"},
    "chronic_illness_self": {"belief": "My body gets in the way of what I need.", "adaptation": "intellectualization"},
    "chronic_illness_family_member": {"belief": "I have to hold things together.", "adaptation": "caretaking"},
}

# Same reasoning as evidence_accumulator.py's SUPPORT_INCREMENT /
# CONTRADICT_DECREMENT: simple and transparent, not a formula dressed up as
# precision. A pattern with a single supporting interpretation stays at
# evidence_strength None - recurrence is what makes something a pattern
# rather than a single reaction.
REINFORCE_INCREMENT = 0.2
WEAKEN_DECREMENT = 0.2
ESTABLISHED_THRESHOLD = 0.5


def salient_domains_for_age(age: Optional[int], exposure_domains: List[str]) -> List[str]:
    """
    Which of an exposure's own tagged domains are also live developmental
    tasks at this age - the replacement for a scalar age multiplier. Falls
    back to the exposure's own domains unchanged if nothing intersects (age
    context doesn't narrow it further, but never invents a match either).
    """
    if age is None:
        return exposure_domains
    stage = get_developmental_stage(age)
    stage_domains = {STAGE_TASK_TO_DOMAIN[task] for task in stage["key_tasks"] if task in STAGE_TASK_TO_DOMAIN}
    intersection = [d for d in exposure_domains if d in stage_domains]
    return intersection or exposure_domains


# ============================================================
# AI interpretation path
# ============================================================

def _build_interpretation_prompt(
    persona_name: str,
    age: Optional[int],
    exposures: List[Dict],
    salient_domains: List[str],
    narration_signals: List[Dict],
    protective_factors: List[Dict],
    prior_patterns: List[Dict],
) -> str:
    exposure_desc = "\n".join(f"- {e['exposure_type']} (domains: {', '.join(e.get('developmental_domains', []))})" for e in exposures)
    signal_desc = (
        "\n".join(f"- {s['signal_type']}: {s.get('evidence_text', '')}" for s in narration_signals)
        or "(none available - this case was built from objective history/case facts, not the persona's own words. This is normal, not a gap to apologize for.)"
    )
    protective_desc = "\n".join(f"- {p['factor_type']} (buffers: {', '.join(p.get('domains_buffered', []))})" for p in protective_factors) or "(none active)"
    prior_desc = "\n".join(f"- {p['pattern_name']} ({p['adaptation_strategy']})" for p in prior_patterns) or "(none yet established)"
    adaptation_list = "\n".join(f'- "{a}"' for a in ADAPTATION_STRATEGIES)

    return f"""You are inferring what a developmental event appears to have meant to {persona_name}, and what adaptive strategy it produced or reinforced. You are not diagnosing. You are forming a grounded psychological interpretation, the kind a thoughtful clinician would form - specific and confident where the evidence supports it, not hedged into meaninglessness.

PERSONA: {persona_name}, age {age if age is not None else 'unknown'} at this event

EXPOSURE(S) FOR THIS EVENT:
{exposure_desc}

DEVELOPMENTAL DOMAINS SALIENT AT THIS AGE (what's actually vulnerable right now, not just "younger = worse"):
{', '.join(salient_domains) if salient_domains else '(none specifically salient)'}

HOW {persona_name.upper()} TALKS ABOUT THIS (narration signals, if any):
{signal_desc}

PROTECTIVE FACTORS ACTIVE AT THE TIME (these can change what the event MEANS, not just soften its severity):
{protective_desc}

{persona_name}'S EXISTING PATTERNS (for continuity - does this event plausibly reinforce an existing pattern, or is it new?):
{prior_desc}

INSTRUCTIONS:
1. Infer ONE belief_statement: a short sentence capturing what {persona_name} appears to have concluded from this event (e.g. "People leave.", "I have to earn my place.", "I cannot depend on anyone."). Be specific and direct - this is the engine's own working hypothesis, not a hedge, and not a claim that these are {persona_name}'s verbatim words. It is equally valid to phrase it as an inferred formulation (e.g. "{persona_name} plausibly holds diminished trust in relational stability") when there is no self-report evidence to draw a first-person voice from - do NOT invent a quote or claim direct access to {persona_name}'s subjective experience they haven't actually expressed.
2. Select exactly ONE adaptation_strategy from the allowed list that best fits the psychological strategy this event produced or reinforced.
3. If a protective factor is present and its buffered domains overlap this event's domains, let it actually change the belief_statement (e.g. toward a less totalizing conclusion) rather than just noting it exists.
4. Give a short reasoning (1-2 sentences) explaining the interpretation in developmental terms.
5. Phrase everything about {persona_name} by name. Never address "you" or "the user."
6. Absence of narration signals is NOT a reason to hedge into "there isn't enough information." Form the strongest interpretation the exposure and developmental context actually support - just don't fabricate direct self-report evidence that isn't there.
7. GROUNDING RULE (STRICT): your reasoning may reference ONLY the specific exposure(s), protective factor(s), and prior pattern(s) explicitly listed above. Do NOT reference, imply, or invent any other event, relationship, caregiver behavior, or life history not explicitly given to you in this prompt - even if it would be a plausible-sounding explanation. If a section above says "(none active)" or "(none yet established)", your reasoning must NOT describe that kind of circumstance as being present. When you want to express uncertainty, say so directly ("it's unclear whether...") rather than filling the gap with an invented fact.

ALLOWED adaptation_strategy values (use ONLY these):
{adaptation_list}

OUTPUT FORMAT (valid JSON only):
{{
  "belief_statement": "...",
  "adaptation_strategy": "...",
  "reasoning": "..."
}}

Respond with ONLY the JSON object."""


def _validate_interpretation(response: Dict) -> Optional[Dict]:
    if not response:
        return None
    adaptation = response.get("adaptation_strategy")
    if adaptation not in ADAPTATION_STRATEGIES:
        return None
    belief = _enforce_subject_attribution(response.get("belief_statement"))
    reasoning = _enforce_subject_attribution(response.get("reasoning"))
    if belief is None or reasoning is None:
        return None
    return {"belief_statement": belief, "adaptation_strategy": adaptation, "reasoning": reasoning}


async def interpret_experience_ai(
    persona_name: str,
    age: Optional[int],
    exposures: List[Dict],
    narration_signals: Optional[List[Dict]] = None,
    protective_factors: Optional[List[Dict]] = None,
    prior_patterns: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """AI interpretation path. Returns None on failure so the caller can fall back."""
    if not exposures:
        return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None}

    salient = salient_domains_for_age(
        age, sorted({d for e in exposures for d in e.get("developmental_domains", [])})
    )

    try:
        response = await openai_service.analyze(
            prompt=_build_interpretation_prompt(
                persona_name, age, exposures, salient,
                narration_signals or [], protective_factors or [], prior_patterns or [],
            ),
            system_message=(
                "You form grounded, specific psychological interpretations of developmental "
                "events. You are confident where evidence supports it, you take protective "
                "factors seriously as changing meaning rather than just softening severity, "
                "and you never address 'the user'. You never invent a concrete event, "
                "relationship, or circumstance that was not given to you in the prompt - "
                "confidence comes from reasoning harder about the evidence you do have, not "
                "from filling gaps with plausible-sounding fiction. Respond ONLY with valid JSON."
            ),
            temperature=0.0,
            max_tokens=600
        )
        validated = _validate_interpretation(response)
        if validated:
            validated["developmental_domains"] = salient
        return validated
    except Exception as e:
        logger.warning(f"AI interpretation failed, will fall back to heuristic pass: {e}")
        return None


def interpret_experience_heuristic(age: Optional[int], exposures: List[Dict]) -> Dict:
    """
    Modest rule-based fallback: takes the first exposure with a known
    default and returns it, narrowed to age-salient domains. Does not
    attempt to synthesize across multiple exposures or factor in narration/
    protective factors - that synthesis is exactly the judgment call this
    fallback isn't equipped to approximate.
    """
    if not exposures:
        return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None, "developmental_domains": []}

    for exposure in exposures:
        default = EXPOSURE_INTERPRETATION_DEFAULTS.get(exposure["exposure_type"])
        if default:
            domains = salient_domains_for_age(age, exposure.get("developmental_domains", []))
            return {
                "belief_statement": default["belief"],
                "adaptation_strategy": default["adaptation"],
                "reasoning": f"Heuristic fallback default for {exposure['exposure_type']}.",
                "developmental_domains": domains,
            }

    return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None, "developmental_domains": []}


# ============================================================
# Reparative/protective interpretation path
# ============================================================
# Developmental significance is not the same thing as adversity. A batch of
# text can fail to match anything in EXPOSURE_TAXONOMY and still matter -
# trust repaired after a betrayal, a conflict actually resolved, sustained
# support during vulnerability, a real achievement. developmental_exposure_
# engine.py already extracts these as ProtectiveFactor findings; this is the
# parallel interpretation path for THIS BATCH's protective factors, mirroring
# interpret_experience_ai/interpret_experience_heuristic above in shape.
#
# Deliberately does NOT set adaptation_strategy. ADAPTATION_STRATEGIES is a
# controlled vocabulary of coping/adaptive strategies a person forms in
# response to something - a reparative event isn't producing a new one of
# those, so grouping it into that vocabulary via accumulate_patterns() would
# either misrepresent it as a new coping strategy or spuriously "reinforce"
# an existing adverse one. Leaving adaptation_strategy unset means:
#   - accumulate_patterns() correctly does not open a new pattern for it
#   - state_trait_engine's attachment-dimension update (apply_attachment_
#     update) is NOT skipped for a trust/relational_security increase the
#     way it deliberately is for adaptation_strategy-driven state changes
#     (see attachment_engine.py) - so real attachment-security movement
#     from a genuine repair isn't confused with a coping strategy's side
#     effect (e.g. people_pleasing also raises relational_security, but
#     that isn't becoming more securely attached)
# A pre-existing adverse pattern this event actually contradicts is instead
# weakened automatically, later, the same way it already was before this
# path existed: accumulate_patterns() checks every protective factor's
# domains_buffered against each future same-strategy reinforcement and marks
# it "weakened" instead of "strengthened" when they overlap. This event's
# own ProtectiveFactor row (persisted unconditionally, independent of this
# interpretation path) is enough to participate in that - no extra wiring
# needed here.

def _build_reparative_prompt(
    persona_name: str,
    age: Optional[int],
    protective_factors_this_batch: List[Dict],
    narration_signals: List[Dict],
    prior_patterns: List[Dict],
) -> str:
    factor_desc = "\n".join(
        f"- {p['factor_type']} (domains: {', '.join(p.get('domains_buffered', []))}): \"{p.get('raw_text', '')}\""
        for p in protective_factors_this_batch
    )
    signal_desc = (
        "\n".join(f"- {s['signal_type']}: {s.get('evidence_text', '')}" for s in narration_signals)
        or "(none available - this case was built from objective history/case facts, not the persona's own words. This is normal, not a gap to apologize for.)"
    )
    prior_desc = "\n".join(f"- {p['pattern_name']} ({p['adaptation_strategy']})" for p in prior_patterns) or "(none yet established)"

    return f"""You are inferring what a POSITIVE or REPARATIVE developmental event appears to have meant to {persona_name}. You are not diagnosing, and you are not manufacturing significance that isn't there - it is entirely valid to conclude an event is real but developmentally minor.

PERSONA: {persona_name}, age {age if age is not None else 'unknown'} at this event

PROTECTIVE/REPARATIVE FACTOR(S) FOR THIS EVENT (this is the ONLY evidence for this event - do not draw on anything else):
{factor_desc}

HOW {persona_name.upper()} TALKS ABOUT THIS (narration signals, if any):
{signal_desc}

{persona_name}'S EXISTING ADAPTIVE PATTERNS (for continuity only - does this event plausibly speak to one of these, e.g. by contradicting the belief behind it? It does NOT need to. Do not force a connection.):
{prior_desc}

INSTRUCTIONS:
1. Infer ONE belief_statement: a short sentence capturing what this event plausibly means to {persona_name} - e.g. "Trust, once broken, can still be rebuilt.", "Support can arrive without her having to ask for it.", or, if the event is real but not developmentally significant on its own, something like "A genuinely positive moment, but not yet enough on its own to shift an established pattern." Both kinds of conclusion are valid outputs - do not inflate a minor event into a turning point it isn't.
2. Give a short reasoning (1-2 sentences) explaining that conclusion in developmental terms, including WHY you judged it significant or not.
3. If (and only if) this event plausibly contradicts the belief behind one of {persona_name}'s existing adaptive patterns listed above, name that pattern in contradicts_pattern (use its exact adaptation_strategy value). Otherwise leave contradicts_pattern null. Do not force a match - most reparative events don't contradict anything and that's fine.
4. Phrase everything about {persona_name} by name. Never address "you" or "the user."
5. GROUNDING RULE (STRICT): reference ONLY the protective/reparative factor(s) and prior pattern(s) explicitly listed above. Do NOT invent, imply, or reference any other event, relationship, or circumstance not given to you here - not a childhood detail, not a caregiver, not a diagnosis, nothing. If narration signals say "(none available)", do not describe {persona_name} as having said or expressed anything.

OUTPUT FORMAT (valid JSON only):
{{
  "belief_statement": "...",
  "reasoning": "...",
  "contradicts_pattern": null
}}

Respond with ONLY the JSON object."""


def _validate_reparative_interpretation(response: Dict, valid_prior_strategies: set) -> Optional[Dict]:
    if not response:
        return None
    belief = _enforce_subject_attribution(response.get("belief_statement"))
    reasoning = _enforce_subject_attribution(response.get("reasoning"))
    if belief is None or reasoning is None:
        return None
    contradicts = response.get("contradicts_pattern")
    if contradicts not in valid_prior_strategies:
        contradicts = None
    return {
        "belief_statement": belief,
        "adaptation_strategy": None,
        "reasoning": reasoning,
        "contradicts_pattern": contradicts,
    }


async def interpret_reparative_experience_ai(
    persona_name: str,
    age: Optional[int],
    protective_factors_this_batch: List[Dict],
    narration_signals: Optional[List[Dict]] = None,
    prior_patterns: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """AI path for a batch with no adverse exposures but a real protective/
    reparative factor. Mirrors interpret_experience_ai's shape and failure
    handling (returns None on failure so the caller falls back)."""
    if not protective_factors_this_batch:
        return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None}

    prior_patterns = prior_patterns or []
    valid_prior_strategies = {p["adaptation_strategy"] for p in prior_patterns if p.get("adaptation_strategy")}

    try:
        response = await openai_service.analyze(
            prompt=_build_reparative_prompt(
                persona_name, age, protective_factors_this_batch, narration_signals or [], prior_patterns,
            ),
            system_message=(
                "You form grounded, specific psychological interpretations of positive and "
                "reparative developmental events. You take real repair and support seriously "
                "without inflating minor events into turning points, you never address 'the "
                "user', and you never invent a concrete event, relationship, or circumstance "
                "that was not given to you in the prompt. Respond ONLY with valid JSON."
            ),
            temperature=0.0,
            max_tokens=400,
        )
        validated = _validate_reparative_interpretation(response, valid_prior_strategies)
        if validated:
            domains = sorted({d for p in protective_factors_this_batch for d in p.get("domains_buffered", [])})
            validated["developmental_domains"] = salient_domains_for_age(age, domains)
        return validated
    except Exception as e:
        logger.warning(f"AI reparative interpretation failed, will fall back to heuristic pass: {e}")
        return None


def interpret_reparative_experience_heuristic(protective_factors_this_batch: List[Dict]) -> Dict:
    """
    Modest rule-based fallback, same spirit as interpret_experience_heuristic:
    genuinely lower fidelity by design, exists so the app degrades
    gracefully rather than silently dropping the event back into "not
    analyzed" when the AI path is unavailable.
    """
    if not protective_factors_this_batch:
        return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None, "developmental_domains": []}

    factor = protective_factors_this_batch[0]
    label = factor["factor_type"].replace("_", " ")
    return {
        "belief_statement": f"A {label} experience registers as developmentally relevant.",
        "adaptation_strategy": None,
        "reasoning": f"Heuristic fallback default for protective factor '{factor['factor_type']}'.",
        "developmental_domains": factor.get("domains_buffered", []),
    }


async def interpret_reparative_experience_async(
    persona_name: str,
    age: Optional[int],
    protective_factors_this_batch: List[Dict],
    narration_signals: Optional[List[Dict]] = None,
    prior_patterns: Optional[List[Dict]] = None,
) -> Dict:
    # Canonical reparative evidence must not vary with model sampling. Freeform
    # narrative generation can still explain this persisted result downstream.
    return interpret_reparative_experience_heuristic(protective_factors_this_batch)


async def interpret_experience_async(
    persona_name: str,
    age: Optional[int],
    exposures: List[Dict],
    narration_signals: Optional[List[Dict]] = None,
    protective_factors: Optional[List[Dict]] = None,
    prior_patterns: Optional[List[Dict]] = None,
    protective_factors_this_batch: Optional[List[Dict]] = None,
) -> Dict:
    """
    Single entry point for "does this batch warrant an Interpretation row",
    dispatching on developmental significance rather than on adversity
    specifically:
      - exposures present -> adverse-interpretation path (unchanged)
      - no exposures but this batch's OWN protective/reparative factor(s)
        present -> reparative-interpretation path
      - neither -> no interpretation (extraction genuinely found nothing
        developmentally recognizable in this text; not a taxonomy gap)
    """
    if exposures:
        # adaptation_strategy is a canonical identity key used by patterns,
        # evidence and replay, so select it only from the deterministic map.
        return interpret_experience_heuristic(age, exposures)

    if protective_factors_this_batch:
        return await interpret_reparative_experience_async(
            persona_name, age, protective_factors_this_batch, narration_signals, prior_patterns
        )

    return {"belief_statement": None, "adaptation_strategy": None, "reasoning": None, "developmental_domains": []}


def interpret_experience(
    persona_name: str,
    age: Optional[int],
    exposures: List[Dict],
    narration_signals: Optional[List[Dict]] = None,
    protective_factors: Optional[List[Dict]] = None,
    prior_patterns: Optional[List[Dict]] = None,
    protective_factors_this_batch: Optional[List[Dict]] = None,
) -> Dict:
    """Sync wrapper, mirroring the pattern used by every prior engine in this rebuild."""
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("interpret_experience called in async context; using heuristic fallback.")
            if exposures:
                return interpret_experience_heuristic(age, exposures)
            return interpret_reparative_experience_heuristic(protective_factors_this_batch or [])
    except RuntimeError:
        pass

    try:
        return asyncio.run(interpret_experience_async(
            persona_name, age, exposures, narration_signals, protective_factors, prior_patterns,
            protective_factors_this_batch,
        ))
    except Exception as e:
        logger.warning(f"Interpretation failed entirely, using heuristic fallback: {e}")
        if exposures:
            return interpret_experience_heuristic(age, exposures)
        return interpret_reparative_experience_heuristic(protective_factors_this_batch or [])


# ============================================================
# Pattern accumulation - recomputed from the full timeline, same philosophy
# as evidence_accumulator.accumulate_evidence()
# ============================================================

def _current_manifestations_from_observations(pattern_domains: set, functional_observations: List[Dict]) -> List[str]:
    """
    Descriptive, not evidentiary - same principle as evidence_accumulator's
    identically-named helper. A concerning functional observation whose
    domains overlap this pattern's implicated domains describes how the
    pattern shows up now; it does not feed evidence_strength math here
    (reinforcement/strength is earned from recurrence across the timeline,
    a different question from "how does this currently manifest").
    """
    return [
        obs["description"]
        for obs in functional_observations
        if obs.get("valence") == "concerning" and set(obs.get("developmental_domains", [])) & pattern_domains
    ]


def accumulate_patterns(
    interpretations: List[Dict],
    protective_factors: Optional[List[Dict]] = None,
    functional_observations: Optional[List[Dict]] = None,
) -> Dict[str, Dict]:
    """
    Groups a persona's Interpretation rows by adaptation_strategy - the
    controlled vocabulary makes this a reliable, inspectable grouping key
    rather than fuzzy text matching. A single interpretation opens a pattern
    candidate as "emerging" with evidence_strength None; only a second
    interpretation sharing the same strategy earns real strength through
    reinforcement. A protective factor active at the time of a later
    interpretation, whose buffered domains overlap that interpretation's
    domains, counts as a "weakened" reinforcement instead of "strengthened" -
    UNLESS that protective factor's own source_event_id is one of this same
    pattern's own supporting events (a protective factor extracted from an
    event cannot retroactively buffer reinforcement from that event or a
    later one of the same pattern - it would otherwise let a pattern
    perpetually cancel its own evidence, since protective factors get
    extracted from most events, adverse ones included, and domains are a
    small reused vocabulary).

    Args:
        interpretations: [{id, source_event_id, age_at_event, adaptation_strategy,
                            belief_statement, developmental_domains}, ...],
                          in chronological order (by age_at_event)
        protective_factors: [{factor_type, domains_buffered, active_from_age}, ...]
        functional_observations: [{valence, description, developmental_domains}, ...]
            - see app/services/functional_observation_engine.py. Populates
            current_manifestations only; does not affect evidence_strength.

    Returns:
        {adaptation_strategy: {pattern_name, status, evidence_strength,
                                first_emerged_age, reinforcement_history,
                                supporting_interpretation_ids, current_manifestations}}
    """
    protective_factors = protective_factors or []
    functional_observations = functional_observations or []
    groups: Dict[str, List[Dict]] = {}
    for interp in interpretations:
        strategy = interp.get("adaptation_strategy")
        if not strategy:
            continue
        groups.setdefault(strategy, []).append(interp)

    result: Dict[str, Dict] = {}
    for strategy, group in groups.items():
        group_sorted = sorted(group, key=lambda i: (i.get("age_at_event") is None, i.get("age_at_event")))
        # A protective factor extracted from one of THIS pattern's own
        # supporting events cannot count as buffering it - e.g. a
        # "friendship" protective factor pulled from the very event where
        # that friendship betrayed the persona must not retroactively cancel
        # reinforcement from that event or any later one. Without this
        # exclusion, since protective factors are extracted from almost
        # every event (even adverse ones - most real narratives contain some
        # genuinely protective detail) and developmental domains are a small
        # controlled vocabulary that gets reused constantly, a pattern's own
        # evidence ends up perpetually "buffered" by itself and can never
        # reach "established" no matter how many real occurrences pile up -
        # confirmed empirically: a strategy reinforced 4 times by a real
        # GPT-4 interpretation still landed on status=resolved,
        # evidence_strength=0.0.
        group_source_event_ids = {
            i.get("source_event_id") for i in group_sorted if i.get("source_event_id") is not None
        }
        reinforcement_history = []
        strength = None

        for i, interp in enumerate(group_sorted):
            age = interp.get("age_at_event")
            domains = set(interp.get("developmental_domains", []))

            if i == 0:
                effect = "originated"
            else:
                buffered = any(
                    set(pf.get("domains_buffered", [])) & domains
                    and (pf.get("active_from_age") is None or age is None or pf["active_from_age"] <= age)
                    and pf.get("source_event_id") not in group_source_event_ids
                    for pf in protective_factors
                )
                effect = "weakened" if buffered else "strengthened"
                strength = (strength or 0.0) + (REINFORCE_INCREMENT if effect == "strengthened" else -WEAKEN_DECREMENT)
                strength = round(max(0.0, min(1.0, strength)), 2)

            reinforcement_history.append({
                "interpretation_id": interp.get("id"),
                "experience_id": interp.get("source_event_id"),
                "age": age,
                "effect": effect,
            })

        # Order matters: "established" requires crossing the threshold, not
        # merely being reinforced more than once - two weak reinforcements
        # (e.g. 0.2, 0.2) stay "emerging", not "established", until strength
        # actually earns it.
        status = "emerging"
        if strength is not None:
            last_effect = reinforcement_history[-1]["effect"]
            if last_effect == "weakened" and strength == 0.0:
                status = "resolved"
            elif last_effect == "weakened":
                status = "weakening"
            elif strength >= ESTABLISHED_THRESHOLD:
                status = "established"
            else:
                status = "emerging"

        pattern_domains = set()
        for interp in group_sorted:
            pattern_domains.update(interp.get("developmental_domains", []))

        result[strategy] = {
            "adaptation_strategy": strategy,
            "status": status,
            "evidence_strength": strength,
            "first_emerged_age": group_sorted[0].get("age_at_event"),
            "reinforcement_history": reinforcement_history,
            "supporting_interpretation_ids": [i.get("id") for i in group_sorted],
            "representative_belief": group_sorted[0].get("belief_statement"),
            "current_manifestations": _current_manifestations_from_observations(pattern_domains, functional_observations),
        }

    return result


# ============================================================
# Pattern naming
# ============================================================

def _build_naming_prompt(persona_name: str, adaptation_strategy: str, belief_statements: List[str]) -> str:
    beliefs = "\n".join(f'- "{b}"' for b in belief_statements if b)
    return f"""Name a developmental pattern for {persona_name}, based on repeated adaptive strategy "{adaptation_strategy}" and these beliefs {persona_name} appears to hold:
{beliefs}

Give a short (2-5 word), evocative, descriptive label - NOT a diagnosis. Examples of the style: "Leave Before You're Left", "Earn Your Place", "Stay Useful, Stay Safe", "Control Before Chaos".

OUTPUT FORMAT (valid JSON only): {{"pattern_name": "..."}}
Respond with ONLY the JSON object."""


async def name_pattern_ai(persona_name: str, adaptation_strategy: str, belief_statements: List[str]) -> Optional[str]:
    try:
        response = await openai_service.analyze(
            prompt=_build_naming_prompt(persona_name, adaptation_strategy, belief_statements),
            system_message="You name developmental patterns concisely and evocatively, never as a diagnosis. Respond ONLY with valid JSON.",
            temperature=0.7,
            max_tokens=100
        )
        name = response.get("pattern_name") if response else None
        return _enforce_subject_attribution(name) if name else None
    except Exception as e:
        logger.warning(f"AI pattern naming failed, using heuristic fallback: {e}")
        return None


def name_pattern_heuristic(adaptation_strategy: str) -> str:
    return f"{adaptation_strategy.replace('_', ' ').title()} Response"


def name_pattern(persona_name: str, adaptation_strategy: str, belief_statements: List[str]) -> str:
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            return name_pattern_heuristic(adaptation_strategy)
    except RuntimeError:
        pass

    try:
        name = asyncio.run(name_pattern_ai(persona_name, adaptation_strategy, belief_statements))
        return name or name_pattern_heuristic(adaptation_strategy)
    except Exception as e:
        logger.warning(f"Pattern naming failed entirely, using heuristic fallback: {e}")
        return name_pattern_heuristic(adaptation_strategy)


# ============================================================
# Per-event verdict (spec section 17's output shape) - assembled from data
# already computed above, not a separate AI call.
# ============================================================

def build_verdict(interpretation: Dict, pattern_state: Optional[Dict], evidence_strength_label_fn) -> Dict:
    """
    Assembles the structured per-event output: VERDICT / WHY / WHAT CHANGED /
    WHAT IT CONNECTS TO / THE PATTERN / EVIDENCE STRENGTH. evidence_strength_
    label_fn is passed in (from evidence_accumulator.evidence_strength_label)
    rather than duplicated, since the High/Moderate/Low framing is shared
    across the whole app.
    """
    return {
        "verdict": interpretation.get("belief_statement"),
        "why": interpretation.get("reasoning"),
        "what_changed": {
            "adaptation_strategy": interpretation.get("adaptation_strategy"),
            "developmental_domains": interpretation.get("developmental_domains", []),
        },
        "connects_to": pattern_state.get("supporting_interpretation_ids", []) if pattern_state else [],
        "pattern_status": pattern_state.get("status") if pattern_state else "emerging",
        "evidence_strength": evidence_strength_label_fn(pattern_state.get("evidence_strength") if pattern_state else None),
    }


# ============================================================
# Persistence helpers (not wired into any route yet - see docs/MIGRATION_MAP.md)
# ============================================================

def build_interpretation_row(
    persona_id: str,
    interpretation: Dict,
    exposure_ids: List[str],
    protective_factor_ids: Optional[List[str]] = None,
    source_event_id: Optional[str] = None,
    age_at_event: Optional[int] = None,
):
    from app.models.interpretation import Interpretation

    return Interpretation(
        persona_id=persona_id,
        source_event_id=source_event_id,
        age_at_event=age_at_event,
        exposure_ids=exposure_ids,
        developmental_domains=interpretation.get("developmental_domains", []),
        belief_statement=interpretation.get("belief_statement"),
        adaptation_strategy=interpretation.get("adaptation_strategy"),
        reasoning=interpretation.get("reasoning"),
        protective_factor_ids=protective_factor_ids or [],
        # State/trait proposals (docs/MIGRATION_MAP.md, Step 11) are computed
        # after pattern accumulation - see developmental_pipeline.py, which
        # sets these two columns directly on the row once built, since the
        # trait proposal needs this event's own pattern status and isn't
        # known yet at row-construction time.
        state_implications=interpretation.get("state_implications"),
        trait_implications=interpretation.get("trait_implications"),
    )


def build_adaptation_pattern_rows(persona_id: str, accumulated: Dict[str, Dict], persona_name: str = "The persona"):
    """
    Converts accumulate_patterns()'s output into unsaved AdaptationPattern
    ORM instances, naming each one. Caller is responsible for db.add()/
    commit() and for reconciling against already-persisted rows for an
    existing persona (upsert-by-adaptation_strategy), same caveat as
    evidence_accumulator.build_clinical_pattern_hypothesis_rows.
    """
    from app.models.adaptation_pattern import AdaptationPattern

    rows = []
    for strategy, state in accumulated.items():
        belief_statements = [state.get("representative_belief")] if state.get("representative_belief") else []
        pattern_name = name_pattern(persona_name, strategy, belief_statements)
        rows.append(AdaptationPattern(
            persona_id=persona_id,
            pattern_name=pattern_name,
            adaptation_strategy=strategy,
            description=state.get("representative_belief"),
            supporting_experience_ids=[
                e["experience_id"] for e in state["reinforcement_history"] if e.get("experience_id")
            ],
            first_emerged_age=state["first_emerged_age"],
            reinforcement_history=state["reinforcement_history"],
            status=state["status"],
            evidence_strength=state["evidence_strength"],
            current_manifestations=state.get("current_manifestations", []),
        ))
    return rows


async def upsert_adaptation_pattern_rows(db, persona_id: str, accumulated: Dict[str, Dict], persona_name: str = "The persona"):
    """
    The actual wiring entry point (docs/MIGRATION_MAP.md, "wiring steps 2-5
    into routes") - mirrors evidence_accumulator.upsert_clinical_pattern_
    hypothesis_rows exactly. accumulate_patterns() recomputes from the
    persona's complete Interpretation history on every call, so this updates
    existing AdaptationPattern rows in place by adaptation_strategy (the
    controlled-vocabulary grouping key) rather than inserting duplicates.
    Renaming only happens if the pattern is still "emerging" - once a
    pattern is established, keep its name stable rather than letting a
    fresh AI naming call quietly relabel it on every new experience.

    async, and calls name_pattern_ai directly (with a heuristic fallback on
    failure) rather than the sync name_pattern wrapper - name_pattern
    detects a running event loop and silently degrades to the heuristic
    namer to stay safe when misused, but this function IS meant to run
    inside an async route, so taking that safety fallback unconditionally
    would mean production never gets an AI-generated name at all.

    Does not commit - caller controls the transaction.
    """
    from app.models.adaptation_pattern import AdaptationPattern

    existing = {
        row.adaptation_strategy: row
        for row in db.query(AdaptationPattern).filter(
            AdaptationPattern.persona_id == persona_id
        ).all()
    }

    for strategy, state in accumulated.items():
        if strategy in existing:
            row = existing[strategy]
            row.status = state["status"]
            row.evidence_strength = state["evidence_strength"]
            row.reinforcement_history = state["reinforcement_history"]
            row.supporting_experience_ids = [
                e["experience_id"] for e in state["reinforcement_history"] if e.get("experience_id")
            ]
            row.current_manifestations = state.get("current_manifestations", [])
            if row.status == "emerging" and state.get("representative_belief"):
                row.description = state["representative_belief"]
        else:
            belief_statements = [state.get("representative_belief")] if state.get("representative_belief") else []
            pattern_name = await name_pattern_ai(persona_name, strategy, belief_statements)
            if not pattern_name:
                pattern_name = name_pattern_heuristic(strategy)
            db.add(AdaptationPattern(
                persona_id=persona_id,
                pattern_name=pattern_name,
                adaptation_strategy=strategy,
                description=state.get("representative_belief"),
                supporting_experience_ids=[
                    e["experience_id"] for e in state["reinforcement_history"] if e.get("experience_id")
                ],
                first_emerged_age=state["first_emerged_age"],
                reinforcement_history=state["reinforcement_history"],
                status=state["status"],
                evidence_strength=state["evidence_strength"],
                current_manifestations=state.get("current_manifestations", []),
            ))
