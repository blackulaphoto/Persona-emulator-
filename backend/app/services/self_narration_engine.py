"""
Self-Narration Engine.

Analyzes not just WHAT a piece of text says happened, but HOW it is told -
minimization, contradiction, normalization, agency language, omission, and
so on. Per docs/MIGRATION_MAP.md, this runs before the Pattern/Adaptation
engine: narration signals are evidence feeding interpretation, not a layer
added after the fact.

Hard rule (see docs/MIGRATION_MAP.md, "Operator vs. subject vs. source"):
every finding this module produces attaches to a persona (subject_id), never
to whoever is operating the app. Prose output must read "Michael's account
minimizes..." and never "you are minimizing..." unless the persona's
narrative_mode has been explicitly set to self_authored. That attribution is
enforced in code here, not left to the model's judgment - see
_enforce_subject_attribution and the way speaker_role/attributed_to_persona
are set by the caller, never inferred from the AI's output.

These signals are evidence about defenses, narrative identity, internal
schemas, emotional access, attribution style, attachment representations,
coping, and self-concept. They are NOT diagnoses, and a single input
producing a hypothesis (e.g. "protective narrative") does not make that
hypothesis true - the evidence accumulator (step 4) is what earns or revises
confidence in it as more of the timeline arrives.
"""
import re
import logging
from typing import Dict, List, Optional

from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=None,
    model="gpt-4o"
)


# ============================================================
# Controlled vocabulary - mirrors the language-as-data list in the product
# spec almost 1:1, so downstream consumers (evidence accumulator, narrative
# presentation) can rely on consistent keys.
# ============================================================
SIGNAL_TYPES = (
    "minimization",
    "magnification",
    "normalization",
    "absolutist_language",
    "idealization",
    "devaluation",
    "self_blame",
    "other_blame",
    "diagnostic_identification",
    "causal_compression",
    "contradiction",
    "excessive_justification",
    "emotional_vocabulary_richness",
    "emotional_vocabulary_absence",
    "pronoun_shift",
    "passive_agency_language",
    "active_agency_language",
    "vague_chronology",
    "detail_loss_near_intense_material",
    "detached_description_of_severe_content",
    "repeated_metaphor",
    "repeated_explanatory_narrative",
    "unprompted_defensiveness",
    "over_explanation",
    "notable_omission",
    "caregiver_framing",
    "affect_content_mismatch",
)

# Speaker roles - shared with app/models/narration.py's SPEAKER_ROLES.
SPEAKER_ROLES = ("persona_voice", "case_author", "third_party_report", "source_material")

# Prose fields must never slip into addressing whoever is operating the app.
# This is enforced in code (_enforce_subject_attribution), not just prompted.
# Matches any standalone "you"/"your"/"you're"/"yours" - there is no
# legitimate reason for second-person address in text that's supposed to be
# about the persona, by name, in the third person, so this is intentionally
# broad rather than an enumerated list of specific phrasings (which an
# earlier version of this guard used, and which "you believe..." slipped
# past - caught by tests/test_pattern_engine.py).
_FORBIDDEN_ADDRESS_PATTERN = re.compile(
    r"\b(you|your|you're|yours|yourself|the user|the operator)\b",
    re.IGNORECASE,
)


# ============================================================
# AI extraction path
# ============================================================

_WORKED_EXAMPLE = """WORKED EXAMPLE

Persona name: Michael
Speaker role: persona_voice
Text: "My childhood was perfect. My dad beat me sometimes but it was normal. I'm fine."

Correct signals to find:
- contradiction: "perfect" directly conflicts with describing being beaten
- normalization: "it was normal" applied to physical violence
- minimization: "sometimes" / rapid closure downplaying severity
- detached_description_of_severe_content / emotional_vocabulary_absence: "I'm fine" closes the topic with no emotional language attached to the violence
- caregiver_framing: violence attributed to the father is immediately reframed as unremarkable, preserving a positive image of him

Correct candidate hypothesis (note: a hypothesis, not a diagnosis, and phrased about Michael, never about "you"):
{
  "hypothesis": "Michael's account may function as a protective narrative - 'it wasn't that bad.'",
  "likely_function": "Allows Michael to maintain a positive view of his father while separating the violence from his own self-story.",
  "potential_later_cost": "May make it harder for Michael to recognize similar behavior as harmful later, since instability or violence appears to have been folded into his definition of normal.",
  "supporting_signals": ["contradiction", "normalization", "minimization"]
}

WRONG (never do this): "You are minimizing your father's abuse." - this misattributes the analysis to whoever is operating the app instead of the persona, and states a hypothesis as settled fact. Do not do either."""


def _build_prompt(text: str, persona_name: str, speaker_role: str) -> str:
    signal_list = "\n".join(f'- "{s}"' for s in SIGNAL_TYPES)

    role_guidance = {
        "persona_voice": (
            f"This text is {persona_name}'s own words about their own life. Analyze it as "
            f"self-narration - how {persona_name} frames, defends, minimizes, or organizes their own account."
        ),
        "case_author": (
            f"This text is written by the person operating the application, describing {persona_name} "
            f"in the third person. Analyze the narrative choices in how {persona_name} is being described, "
            f"but do not treat this as {persona_name}'s own self-narrative - it is someone else's framing of them."
        ),
        "third_party_report": (
            f"This text is a report from someone else (e.g. a family member) about {persona_name}. "
            f"Analyze it as an outside account of {persona_name}, not as {persona_name}'s self-narrative."
        ),
        "source_material": (
            f"This text is source material (e.g. clinical notes or records) about {persona_name}. "
            f"Analyze the framing present in the document, not as {persona_name}'s self-narrative."
        ),
    }.get(speaker_role, f"Analyze how this text describes {persona_name}.")

    return f"""You analyze HOW something is said, not just what happened. You are looking for narrative and linguistic signals - never assigning a diagnosis, and never addressing or describing whoever is operating this application. Every finding is about {persona_name}, the case subject, never about "the user" or "you."

{role_guidance}

TEXT TO ANALYZE:
{text}

{_WORKED_EXAMPLE}

ALLOWED signal_type values (use ONLY these, do not invent new ones):
{signal_list}

INSTRUCTIONS:
1. Identify which signals are actually present in THIS text, with a short quoted evidence_text for each. Do not force signals that aren't there - an empty or short list is a valid, honest result.
2. Optionally propose 0-2 candidate_hypotheses grounded in the signals you found - each MUST be phrased about {persona_name} by name, framed as a hypothesis ("may function as...", "appears to..."), never as settled fact, and never phrased as "you..."
3. Do not diagnose. Do not use clinical disorder names as if confirmed. Do not tell {persona_name} (or the operator) what they are doing - describe what the text shows.

OUTPUT FORMAT (valid JSON only, no other text):
{{
  "linguistic_signals": [
    {{"signal_type": "contradiction", "evidence_text": "the exact quoted phrase", "note": "brief note on what the contradiction is"}}
  ],
  "candidate_hypotheses": [
    {{"hypothesis": "...", "likely_function": "...", "potential_later_cost": "...", "supporting_signals": ["contradiction", "normalization"]}}
  ]
}}

Respond with ONLY the JSON object."""


def _enforce_subject_attribution(text: Optional[str]) -> str:
    """
    Code-level guard against the model addressing whoever is operating the
    app instead of the persona. This is the hard rule from
    docs/MIGRATION_MAP.md - prompting for it is not enough on its own.
    """
    if not text:
        return text
    if _FORBIDDEN_ADDRESS_PATTERN.search(text):
        logger.warning(f"Self-narration output violated subject attribution, dropped: {text[:120]!r}")
        return None
    return text


def _validate_and_filter(response: Dict) -> Dict[str, List[Dict]]:
    """
    Drops signal types outside the controlled vocabulary and any prose that
    violates subject attribution, rather than trusting the model's output
    directly.
    """
    signals = []
    for item in (response or {}).get("linguistic_signals", []) or []:
        signal_type = item.get("signal_type")
        if signal_type not in SIGNAL_TYPES:
            continue
        note = _enforce_subject_attribution(item.get("note", ""))
        if note is None:
            continue
        signals.append({
            "signal_type": signal_type,
            "evidence_text": item.get("evidence_text", ""),
            "note": note,
        })

    hypotheses = []
    for item in (response or {}).get("candidate_hypotheses", []) or []:
        hypothesis = _enforce_subject_attribution(item.get("hypothesis"))
        likely_function = _enforce_subject_attribution(item.get("likely_function"))
        potential_cost = _enforce_subject_attribution(item.get("potential_later_cost"))
        if hypothesis is None or likely_function is None or potential_cost is None:
            continue
        supporting = [s for s in (item.get("supporting_signals") or []) if s in SIGNAL_TYPES]
        hypotheses.append({
            "hypothesis": hypothesis,
            "likely_function": likely_function,
            "potential_later_cost": potential_cost,
            "supporting_signals": supporting,
        })

    return {"linguistic_signals": signals, "candidate_hypotheses": hypotheses}


def _skipped_result(reason: str) -> Dict[str, List]:
    return {"linguistic_signals": [], "candidate_hypotheses": [], "skipped_reason": reason}


def is_self_narration_eligible(speaker_role: str) -> bool:
    """
    The hard gate: self-narration analysis is conditional, not a mandatory
    pipeline stage applied to everything a case author types (see
    docs/MIGRATION_MAP.md, "Evidence & Source Model"). "Timmy was abused at
    17" written by whoever is building the case tells us nothing about
    Timmy's own beliefs, defenses, or narrative identity - it's a case fact,
    handled by the exposure extractor (step 2), not this engine. Only text
    explicitly attributed to the persona's own voice - their beliefs,
    memories, feelings, or speech - is eligible for this analysis.
    """
    if speaker_role not in SPEAKER_ROLES:
        raise ValueError(f"Unknown speaker_role: {speaker_role!r}")
    return speaker_role == "persona_voice"


async def analyze_narration_ai(text: str, persona_name: str, speaker_role: str) -> Optional[Dict[str, List[Dict]]]:
    """AI analysis path. Returns None on failure so the caller can fall back."""
    if not is_self_narration_eligible(speaker_role):
        return _skipped_result(
            f"speaker_role={speaker_role!r} is not the persona's own voice - "
            "self-narration analysis only runs on persona_voice text."
        )
    if not text or not text.strip():
        return {"linguistic_signals": [], "candidate_hypotheses": []}

    try:
        response = await openai_service.analyze(
            prompt=_build_prompt(text, persona_name, speaker_role),
            system_message=(
                "You analyze narrative and linguistic patterns in text about a specific named "
                "person. You never diagnose, never address 'the user', and never state a "
                "hypothesis as settled fact. Respond ONLY with valid JSON."
            ),
            temperature=0.3,
            max_tokens=1200
        )
        return _validate_and_filter(response)
    except Exception as e:
        logger.warning(f"AI self-narration analysis failed, will fall back to heuristic pass: {e}")
        return None


# ============================================================
# Heuristic fallback path (AI unavailable only)
# ============================================================
# Narrative analysis is fundamentally harder to approximate with rules than
# exposure keyword-matching is - this fallback is intentionally modest. It
# exists so the app degrades gracefully, not as a credible substitute for
# the AI path. It only detects a handful of the most mechanically detectable
# signals; most of SIGNAL_TYPES requires real language understanding and is
# left empty when this path is used.

_ABSOLUTIST_WORDS = re.compile(r"\b(always|never|everyone|everybody|nobody|no one|everything|nothing)\b", re.IGNORECASE)
_SELF_BLAME_PHRASES = ("my fault", "i deserved", "i caused", "i made him", "i made her", "because of me")
_RAPID_CLOSURE_PHRASES = ("i'm fine", "i am fine", "no big deal", "it was fine", "it wasn't a big deal", "anyway")


def analyze_narration_heuristic(text: str) -> Dict[str, List[Dict]]:
    """
    Minimal rule-based fallback. Only flags what's mechanically detectable:
    absolutist language, explicit self-blame phrasing, and rapid-closure
    minimization phrases. Produces no candidate_hypotheses - forming an
    interpretive hypothesis from raw text is exactly the kind of judgment
    this fallback path cannot respons­ibly approximate.
    """
    if not text:
        return {"linguistic_signals": [], "candidate_hypotheses": []}

    text_lower = text.lower()
    signals = []

    absolutist_hits = _ABSOLUTIST_WORDS.findall(text)
    if absolutist_hits:
        signals.append({
            "signal_type": "absolutist_language",
            "evidence_text": absolutist_hits[0],
            "note": "Heuristic fallback: absolutist word detected.",
        })

    for phrase in _SELF_BLAME_PHRASES:
        if phrase in text_lower:
            signals.append({
                "signal_type": "self_blame",
                "evidence_text": phrase,
                "note": "Heuristic fallback: explicit self-blame phrase detected.",
            })
            break

    for phrase in _RAPID_CLOSURE_PHRASES:
        if phrase in text_lower:
            signals.append({
                "signal_type": "minimization",
                "evidence_text": phrase,
                "note": "Heuristic fallback: rapid-closure/minimizing phrase detected.",
            })
            break

    return {"linguistic_signals": signals, "candidate_hypotheses": []}


# ============================================================
# Orchestration
# ============================================================

async def analyze_narration_async(text: str, persona_name: str, speaker_role: str) -> Dict[str, List[Dict]]:
    """
    Primary entry point. Gates on speaker_role before doing anything else -
    case-author prose, third-party reports, and source material never reach
    the AI or heuristic path, regardless of how they're phrased.
    """
    if not is_self_narration_eligible(speaker_role):
        return _skipped_result(
            f"speaker_role={speaker_role!r} is not the persona's own voice - "
            "self-narration analysis only runs on persona_voice text."
        )

    result = await analyze_narration_ai(text, persona_name, speaker_role)
    if result is not None:
        return result

    logger.info("Using heuristic fallback for self-narration analysis")
    return analyze_narration_heuristic(text)


def analyze_narration(text: str, persona_name: str, speaker_role: str) -> Dict[str, List[Dict]]:
    """
    Sync wrapper, mirroring app/services/developmental_exposure_engine.py's
    pattern. Gates on speaker_role first, before any async-loop handling or
    fallback logic - every path through this function respects the same
    rule as analyze_narration_async.
    """
    if not is_self_narration_eligible(speaker_role):
        return _skipped_result(
            f"speaker_role={speaker_role!r} is not the persona's own voice - "
            "self-narration analysis only runs on persona_voice text."
        )

    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("analyze_narration called in async context; using heuristic fallback.")
            return analyze_narration_heuristic(text)
    except RuntimeError:
        pass

    try:
        return asyncio.run(analyze_narration_async(text, persona_name, speaker_role))
    except Exception as e:
        logger.warning(f"Self-narration analysis failed entirely, using heuristic fallback: {e}")
        return analyze_narration_heuristic(text)


# ============================================================
# Persistence helper (not wired into any route yet - see docs/MIGRATION_MAP.md)
# ============================================================

def build_narration_record(
    subject_id: str,
    text: str,
    speaker_role: str,
    analysis: Dict[str, List[Dict]],
    source_event_id: Optional[str] = None,
):
    """
    Converts an analysis result into an unsaved NarrationRecord ORM instance.
    attributed_to_persona is set here in code from speaker_role - never
    trusted from the AI's output - per the hard attribution rule in
    docs/MIGRATION_MAP.md. Caller is responsible for db.add()/commit().
    """
    from app.models.narration import NarrationRecord

    if speaker_role not in SPEAKER_ROLES:
        raise ValueError(f"Unknown speaker_role: {speaker_role!r}")

    return NarrationRecord(
        subject_id=subject_id,
        source_event_id=source_event_id,
        speaker_role=speaker_role,
        attributed_to_persona=(speaker_role == "persona_voice"),
        raw_text=text,
        linguistic_signals=analysis.get("linguistic_signals", []),
        candidate_hypotheses=analysis.get("candidate_hypotheses", []),
    )
