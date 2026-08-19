"""
Chat context builder - the "Human-model context builder" step in the
safety-router architecture (docs/MIGRATION_MAP.md step 10).

Replaces chat.py's old detect_trauma_type() / build_trauma_behavioral_
profile() / build_age_appropriate_trauma_expression() entirely - not just
refactored, retired. That code matched raw keywords in a free-text
experience description ("coach", "teacher", "adult", "touched") straight to
scripted, age-specific dialogue lines, including explicit child-sexual-
abuse-specific scripts for personas as young as 8. It ran regardless of
confidence or evidence, exactly the "neuroticism > .7 = anxious" crude-
mapping problem the product spec calls out, at its highest-stakes point in
the whole app. There is no fallback-preserving version of that function
worth keeping - it is removed outright, not softened.

Behavior should emerge from the full model: temperament (Big Five, kept),
developmental adaptations (AdaptationPattern), narrative identity
(Interpretation, NarrationRecord), and clinical hypotheses
(ClinicalPatternHypothesis) - see product spec section 15. When those
tables are populated (once steps 2-5 are wired into a creation route),
build_pattern_aware_behaviors() below translates a persona's earned,
evidence-backed patterns into general behavioral guidance through a small
controlled vocabulary (ADAPTATION_STRATEGY_GUIDANCE), not a raw-keyword
scripted line. When they're empty (the current production reality), this
degrades to the existing Big Five trait-threshold guidance alone - a
plainer, less specific persona, which is the honest state when no
developmental evidence has accumulated yet, not a gap to paper over with
invented specifics.
"""
from typing import Dict, List, Optional


# Maps app/services/pattern_engine.py's ADAPTATION_STRATEGIES to general,
# clinically-grounded in-character behavioral guidance - deliberately less
# specific and less scripted than the old file's dialogue lines, and driven
# by an earned pattern (with evidence_strength) rather than a raw keyword
# hit on unrelated text.
ADAPTATION_STRATEGY_GUIDANCE: Dict[str, str] = {
    "hypervigilance": "Notices small details others miss, gets startled easily, may ask about safety or exits, mentions feeling on edge.",
    "emotional_distancing": "Keeps emotional topics at arm's length, answers personal questions briefly, redirects toward safer topics.",
    "people_pleasing": "Quick to agree, checks how others feel before sharing an opinion, apologizes often.",
    "control_seeking": "Prefers plans over spontaneity, uneasy with uncertainty, tries to manage outcomes.",
    "aggression": "Short temper when pushed, defensive under perceived criticism, may snap before calming down.",
    "avoidance": "Changes the subject away from difficult topics, gives vague answers, finds reasons not to engage.",
    "self_reliance": "Reluctant to ask for help, downplays needing anything from others, handles things alone by default.",
    "perfectionism": "Self-critical about small mistakes, holds high personal standards, uncomfortable being average at something.",
    "humor": "Deflects difficult moments with a joke, uses humor to soften or avoid heavier feelings.",
    "caretaking": "Redirects focus to how others are doing, comfortable giving support, uncomfortable receiving it.",
    "substance_use": "May reference using substances to cope, avoidant if asked directly about it.",
    "intellectualization": "Explains feelings analytically rather than experiencing them, prefers reasoning about a topic to feeling it.",
}


def build_age_language_guidance(age: int) -> str:
    """Age-appropriate language register - kept from the original chat.py, unchanged in spirit. Not scripted trauma content, just vocabulary/topic register."""
    if age <= 8:
        return "Use VERY simple words. Short sentences (5-10 words). Talk about toys, games, friends, family, school."
    elif age <= 12:
        return "Use simple language. Short to medium sentences. Talk about school, friends, hobbies, family, games."
    elif age <= 16:
        return "Use teen vocabulary. Talk about friends, school, social stuff, relationships, hobbies. Can use some slang naturally."
    elif age <= 21:
        return "Use young adult language. Talk about college, work, relationships, future plans, social life."
    else:
        return "Use adult language. Talk about work, relationships, life experiences, responsibilities."


def build_personality_behaviors(personality: Dict[str, float]) -> List[str]:
    """
    The Big Five trait-threshold guidance from the original chat.py, kept -
    temperament is a legitimate, real input per the product spec ("Keep Big
    Five influence"). Only the trauma-keyword scripting is retired, not this.
    """
    openness = personality.get("openness", 0.5)
    conscientiousness = personality.get("conscientiousness", 0.5)
    extraversion = personality.get("extraversion", 0.5)
    agreeableness = personality.get("agreeableness", 0.5)
    neuroticism = personality.get("neuroticism", 0.5)

    behaviors = []

    if neuroticism >= 0.7:
        behaviors.append("Anxious and prone to worry; mentions feeling on edge or overwhelmed.")
    elif neuroticism >= 0.5:
        behaviors.append("Sometimes anxious or stressed, especially when things are uncertain.")
    else:
        behaviors.append("Generally calm; handles stress well.")

    if extraversion <= 0.3:
        behaviors.append("Quiet and reserved - SHORT answers (1-2 sentences), doesn't elaborate unless asked directly.")
    elif extraversion <= 0.5:
        behaviors.append("Somewhat reserved - not very talkative but will share if asked directly.")
    else:
        behaviors.append("Outgoing and talkative; enjoys sharing and connecting.")

    if openness >= 0.7:
        behaviors.append("Creative and curious; enjoys new ideas and exploring possibilities.")
    elif openness <= 0.3:
        behaviors.append("Prefers familiar, practical matters over abstract ideas.")

    if agreeableness <= 0.3:
        behaviors.append("Skeptical, doesn't trust easily; may be defensive or guarded.")
    elif agreeableness >= 0.7:
        behaviors.append("Warm and trusting; wants to help others.")

    if conscientiousness >= 0.7:
        behaviors.append("Organized and responsible; cares about doing things right.")
    elif conscientiousness <= 0.3:
        behaviors.append("Spontaneous; doesn't worry much about planning.")

    return behaviors


# Short, general behavioral tendencies keyed to substrings of
# Persona.current_trauma_markers - kept as a bridge because, as of this
# rewrite, current_trauma_markers is still the ONLY symptom signal the live
# system populates (it's produced by the old backstory_symptom_mapper.py;
# steps 2-5's exposure/pattern pipeline isn't wired into personas.py yet -
# see docs/MIGRATION_MAP.md). Removing this without the new pipeline in
# place would silently strip all symptom-driven roleplay from the live
# product today. Deliberately shorter and less prescriptive than the old
# per-marker multi-line scripted-dialogue blocks it replaces - general
# behavioral tendency, not a list of lines the character should say.
SYMPTOM_MARKER_GUIDANCE: Dict[str, str] = {
    "hypervigilance": "Notices small details, startles easily, may mention feeling unsafe or scanning surroundings.",
    "anxiety": "Prone to worry spirals and physical tension; may seek reassurance.",
    "trust": "Hesitant with personal questions, may deflect or test whether someone means what they say.",
    "depression": "Low energy, reduced interest in things they used to enjoy, self-critical.",
    "flashback": "May go quiet or vague when a topic gets too close to something painful.",
    "nightmare": "May mention sleep trouble or being tired without wanting to explain why.",
    "avoidance": "Steers away from difficult topics, gives vague answers, changes the subject.",
    "anger": "Short-tempered when pushed, defensive under perceived criticism.",
    "irritability": "Short-tempered when pushed, defensive under perceived criticism.",
    "shame": "Self-blaming, downplays their own needs, quick to apologize.",
    "dissociation": "May give vague or spacey answers, describe feeling disconnected or numb.",
}


def build_symptom_marker_behaviors(trauma_markers: Optional[List[str]]) -> List[str]:
    """General behavioral tendencies from Persona.current_trauma_markers - see SYMPTOM_MARKER_GUIDANCE docstring."""
    if not trauma_markers:
        return []
    behaviors = []
    seen_guidance = set()
    for marker in trauma_markers:
        marker_lower = marker.lower().replace("_", " ")
        for key, guidance in SYMPTOM_MARKER_GUIDANCE.items():
            if key in marker_lower and guidance not in seen_guidance:
                behaviors.append(guidance)
                seen_guidance.add(guidance)
    return behaviors


# Step 11f (docs/MIGRATION_MAP.md): translates the fast-moving State tier
# (app/services/state_trait_engine.py's STATE_VARIABLES: trust,
# threat_sensitivity, mood, regulation, avoidance, relational_security) into
# behavioral guidance, alongside the slow Trait tier already handled by
# build_personality_behaviors above and the earned-pattern guidance below.
# Unlike current_personality (which always carries all five Big Five keys),
# current_state starts at {} and only gains a key once state_trait_engine
# has actually proposed movement on it - a key that has never been touched
# produces no guidance line here, rather than assuming an unearned 0.5
# baseline for it (same "opening != believing" principle used throughout
# this rebuild). Thresholds intentionally mirror build_personality_behaviors'
# >=0.7/<=0.3 bands for consistency, not a new calibration.
STATE_VARIABLE_GUIDANCE: Dict[str, Dict[str, str]] = {
    "threat_sensitivity": {
        "high": "Right now, on edge - scanning for danger, quick to startle or brace for the worst.",
        "low": "Right now, feels safe enough to let their guard down.",
    },
    "trust": {
        "low": "Right now, wary of others' intentions - slow to open up, testing before believing.",
        "high": "Right now, open and willing to take people at their word.",
    },
    "mood": {
        "low": "Right now, low - flat energy, less interested in things that usually engage them.",
        "high": "Right now, in a good place - more energy and warmth than usual.",
    },
    "regulation": {
        "low": "Right now, dysregulated - reactions come faster and bigger than they intend.",
        "high": "Right now, steady - able to pause and respond rather than react.",
    },
    "avoidance": {
        "high": "Right now, actively steering away from anything that feels too close or exposing.",
        "low": "Right now, more willing than usual to stay present in a difficult moment.",
    },
    "relational_security": {
        "low": "Right now, uneasy in this connection - unsure where they stand with the other person.",
        "high": "Right now, feels solid in this connection.",
    },
}


def build_state_aware_behaviors(current_state: Optional[Dict[str, float]]) -> List[str]:
    """
    Current-State behavioral guidance - see STATE_VARIABLE_GUIDANCE docstring
    above. Framed as "right now" (temporary, reactive) rather than the
    "generally"/always framing build_personality_behaviors uses for Trait,
    so a roleplaying model doesn't conflate a passing reaction with fixed
    personality.
    """
    if not current_state:
        return []

    behaviors = []
    for variable, bands in STATE_VARIABLE_GUIDANCE.items():
        if variable not in current_state:
            continue
        value = current_state[variable]
        if value >= 0.7 and "high" in bands:
            behaviors.append(bands["high"])
        elif value <= 0.3 and "low" in bands:
            behaviors.append(bands["low"])
    return behaviors


def build_pattern_aware_behaviors(
    adaptation_patterns: Optional[List[Dict]] = None,
    interpretations: Optional[List[Dict]] = None,
    clinical_pattern_hypotheses: Optional[List[Dict]] = None,
) -> List[str]:
    """
    Translates earned developmental patterns into behavioral guidance.
    Empty inputs (the current production default, since nothing populates
    these tables yet) produce an empty list - callers should treat that as
    "no accumulated pattern evidence" and rely on build_personality_behaviors
    alone, not as an error.

    Args:
        adaptation_patterns: [{pattern_name, adaptation_strategy, status, evidence_strength}, ...]
        interpretations: [{belief_statement}, ...] - representative beliefs, most recent first
        clinical_pattern_hypotheses: [{pattern_key, tier, evidence_strength}, ...]
    """
    adaptation_patterns = adaptation_patterns or []
    interpretations = interpretations or []
    clinical_pattern_hypotheses = clinical_pattern_hypotheses or []

    behaviors = []

    for pattern in adaptation_patterns:
        strategy = pattern.get("adaptation_strategy")
        guidance = ADAPTATION_STRATEGY_GUIDANCE.get(strategy)
        if not guidance:
            continue
        status = pattern.get("status", "emerging")
        name = pattern.get("pattern_name", strategy)
        behaviors.append(f'Pattern "{name}" ({status}): {guidance}')

    if interpretations:
        beliefs = [i["belief_statement"] for i in interpretations if i.get("belief_statement")]
        if beliefs:
            behaviors.append(
                "Underlying beliefs shaped by their history (let these color reactions, don't state them outright): "
                + "; ".join(beliefs[:3])
            )

    # Clinical pattern hypotheses deliberately do NOT produce behavioral
    # scripting here - they inform the persona's internal state (already
    # surfaced via current_trauma_markers elsewhere in the context), but
    # translating a tiered clinical hypothesis directly into roleplay
    # instructions risks performing a diagnosis rather than a person.

    return behaviors


def build_full_persona_context(
    persona_name: str,
    age: int,
    personality: Dict[str, float],
    trauma_markers: Optional[List[str]] = None,
    adaptation_patterns: Optional[List[Dict]] = None,
    interpretations: Optional[List[Dict]] = None,
    clinical_pattern_hypotheses: Optional[List[Dict]] = None,
    current_state: Optional[Dict[str, float]] = None,
) -> str:
    """
    Assembles the full behavioral-guidance block for the chat system prompt.
    Always includes personality-based guidance. State-aware guidance (Step
    11f), symptom-marker guidance (the current live signal), and
    pattern-aware guidance (the developmental-pipeline signal) are all
    appended when evidence exists for them - not mutually exclusive, since
    the live system draws on all of them together (see docs/MIGRATION_MAP.md).
    """
    lines = build_personality_behaviors(personality)

    state_behaviors = build_state_aware_behaviors(current_state)
    if state_behaviors:
        lines.append("")
        lines.append("CURRENT STATE (fast-moving, may shift with context - not fixed personality):")
        lines.extend(state_behaviors)

    symptom_behaviors = build_symptom_marker_behaviors(trauma_markers)
    if symptom_behaviors:
        lines.append("")
        lines.append("CURRENT SYMPTOM TENDENCIES:")
        lines.extend(symptom_behaviors)

    pattern_behaviors = build_pattern_aware_behaviors(
        adaptation_patterns, interpretations, clinical_pattern_hypotheses
    )
    if pattern_behaviors:
        lines.append("")
        lines.append(f"DEVELOPMENTAL PATTERNS (earned from {persona_name}'s full timeline):")
        lines.extend(pattern_behaviors)

    return "\n".join(lines)
