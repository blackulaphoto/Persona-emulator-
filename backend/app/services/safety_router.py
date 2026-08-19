"""
Safety Router for the persona chat feature.

Architecture (product spec section 14, docs/MIGRATION_MAP.md step 10):

    User -> Safety/crisis router -> Human-model context builder ->
    Character simulation -> Output safety review -> Response

This module is the first and last thing that touches a chat turn. It does
not evaluate psychological plausibility - that's the rest of this
rebuild's job (app/services/pattern_engine.py, evidence_accumulator.py,
etc). Its only question is: does this turn require the platform to
interrupt, regardless of character immersion?

Per the product spec: "the platform itself must retain the ability to
interrupt where serious safety conditions require it," but "do not force
the simulated person to suddenly announce 'I am an AI.'" A crisis response
here is framed as the PLATFORM stepping in ("This app pauses here..."),
not a broken-character non-sequitur from the persona - the interruption is
allowed to break immersion because real safety requires it, but it doesn't
pretend the persona said it.

Deliberately keyword-based, unlike almost every other keyword fallback in
this rebuild. Everywhere else, a keyword fallback exists as a lower-
fidelity approximation of an AI path, documented as "modest" because false
positives were the concern (fabricating psychology that isn't there). Here
the tradeoff is inverted on purpose: a false positive costs one interrupted
roleplay turn; a false negative could cost missing a real crisis. Recall is
prioritized over precision here, deliberately - this is not a place to wait
for a slower, less reliable AI classifier when a fast, deterministic check
can run on every single message.

Two tiers, asymmetric on purpose:
  - INPUT review (check_input) is broad/high-recall - it runs on the live
    human operator's real-time typed message, which is always real text
    from a real person at that moment, not case-authored simulation
    content. Any crisis-indicating language here short-circuits straight to
    a resource message, bypassing the character simulation entirely.
  - OUTPUT review (check_output) is deliberately narrower - it must NOT
    block ordinary in-character distress (a persona voicing hopelessness or
    suicidal ideation as a portrayed symptom is legitimate clinical
    simulation content, not a safety violation - see PersonaSymptom /
    ClinicalPatternHypothesis elsewhere in this codebase). It only catches
    the model generating specific means/method content, which would be
    inappropriate regardless of character.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


CRISIS_CATEGORIES = ("suicide", "self_harm", "violence_to_others", "abuse_in_progress")

_SUICIDE_PHRASES = (
    "kill myself", "want to die", "wanna die", "end my life", "ending my life",
    "suicidal", "better off dead", "no reason to live", "don't want to live",
    "dont want to live", "wish i was dead", "wish i were dead",
    "going to kill myself", "planning to kill myself", "take my own life",
    "thinking about suicide", "thoughts of suicide",
)
_SELF_HARM_PHRASES = (
    "hurt myself", "hurting myself", "cutting myself", "cut myself",
    "self harm", "self-harm", "want to cut", "burn myself", "starve myself",
    "harming myself",
)
_VIOLENCE_TO_OTHERS_PHRASES = (
    "going to hurt", "want to hurt someone", "kill him", "kill her", "kill them",
    "going to kill", "want to kill",
)
_ABUSE_IN_PROGRESS_PHRASES = (
    "he's hitting me", "hes hitting me", "she's hitting me", "shes hitting me",
    "being abused right now", "hit me tonight", "i'm scared he'll hurt me",
    "im scared hell hurt me", "i'm scared she'll hurt me", "im scared shell hurt me",
    "not safe at home right now", "not safe right now",
)

# Output-side review: narrower on purpose - method/means content only, never
# general distress/hopelessness language, which is legitimate in-character
# symptom portrayal (see module docstring).
_OUTPUT_METHOD_PHRASES = (
    "here's how you", "heres how you", "you could use a", "the best way to end",
    "how many pills", "lethal dose",
)


def _match(text_lower: str, phrases: tuple) -> bool:
    return any(p in text_lower for p in phrases)


def check_input(message: str) -> Optional[str]:
    """
    Broad, high-recall check on the live operator's message. Returns a
    CRISIS_CATEGORIES value if a match is found, else None. Priority order:
    suicide > self_harm > violence_to_others > abuse_in_progress - checked
    in that order so the most severe applicable category wins when a
    message could match more than one.
    """
    if not message:
        return None
    text_lower = message.lower()

    if _match(text_lower, _SUICIDE_PHRASES):
        return "suicide"
    if _match(text_lower, _SELF_HARM_PHRASES):
        return "self_harm"
    if _match(text_lower, _VIOLENCE_TO_OTHERS_PHRASES):
        return "violence_to_others"
    if _match(text_lower, _ABUSE_IN_PROGRESS_PHRASES):
        return "abuse_in_progress"
    return None


def check_output(generated_text: str) -> bool:
    """
    Narrow backstop on the model's generated in-character response. Only
    flags specific means/method content - NOT general sadness, hopelessness,
    or suicidal-ideation language, which is legitimate portrayed symptom
    content elsewhere in this app. Returns True if the output should be
    replaced with a safety note instead of shown as-is.
    """
    if not generated_text:
        return False
    return _match(generated_text.lower(), _OUTPUT_METHOD_PHRASES)


_CRISIS_RESPONSES = {
    "suicide": (
        "This app pauses here. What you've shared sounds serious, and this simulation isn't "
        "equipped to support you with it. If you're thinking about suicide, please reach out to "
        "the 988 Suicide & Crisis Lifeline (call or text 988 in the US) or your local emergency "
        "number right now. You don't have to go through this alone."
    ),
    "self_harm": (
        "This app pauses here. What you've shared about hurting yourself is serious and deserves "
        "real support, not a simulation. Please reach out to the 988 Suicide & Crisis Lifeline "
        "(call or text 988 in the US) or a trusted person right now."
    ),
    "violence_to_others": (
        "This app pauses here. If you or someone else is in immediate danger, please contact "
        "emergency services (911 in the US) right now."
    ),
    "abuse_in_progress": (
        "This app pauses here. If you're describing something happening to you right now, please "
        "reach out to the National Domestic Violence Hotline (1-800-799-7233), or emergency "
        "services if you're in immediate danger."
    ),
}

_OUTPUT_SAFETY_NOTE = (
    "This app pauses here rather than continuing that response. If you're in crisis, please reach "
    "out to the 988 Suicide & Crisis Lifeline (call or text 988 in the US)."
)


def build_crisis_response(category: str) -> str:
    """category should be a value from check_input(); falls back to the suicide message if unrecognized."""
    return _CRISIS_RESPONSES.get(category, _CRISIS_RESPONSES["suicide"])


def build_output_safety_note() -> str:
    return _OUTPUT_SAFETY_NOTE
