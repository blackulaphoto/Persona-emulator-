"""
Functional Observation Engine.

Extracts Behavior and Known-Outcome evidence per docs/MIGRATION_MAP.md's
"Evidence & Source Model": current or ongoing functioning ("Timmy avoids
physical contact and becomes visibly tense when his father is mentioned"),
as opposed to DevelopmentalExposure's dated historical events, and distinct
from self-narration's analysis of the persona's own words. Not gated by
speaker_role - a behavioral observation is a fact-claim like an exposure,
not evidence about the persona's internal narrative, so anyone can validly
report one.

Two extraction paths, same shape as every other engine in this rebuild:
AI primary (controlled vocabulary, validated output), keyword fallback for
when the AI is unavailable.
"""
import logging
from typing import Dict, List, Optional

from app.services.openai_service import OpenAIService
from app.services.self_narration_engine import _enforce_subject_attribution

logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=None,
    model="gpt-4o"
)


# ============================================================
# Controlled vocabulary
# ============================================================
OBSERVATION_TYPES = (
    "behavioral_pattern",           # e.g. avoids physical contact, becomes tense at a trigger
    "relationship_functioning",     # quality/stability of relationships
    "occupational_functioning",     # work or school functioning
    "substance_use_pattern",
    "symptom_manifestation",        # an observed pattern that looks symptom-like, not itself a diagnosis
    "social_functioning",           # broader social engagement/isolation
    "self_care_functioning",        # daily functioning, self-care
    "emotional_expression_pattern",  # how affect currently shows up
)

VALENCES = ("concerning", "protective", "neutral")

# Modest keyword fallback. observation_type/domains/valence only - no
# candidate_pattern_keys, since guessing which specific clinical pattern a
# keyword match implies is exactly the kind of judgment call this fallback
# isn't equipped to approximate (matches the same restraint used elsewhere,
# e.g. self_narration_engine's heuristic path producing no hypotheses).
_KEYWORD_RULES: List[Dict] = [
    {"keywords": ["avoids physical contact", "becomes tense", "hypervigilant", "flinches"],
     "observation_type": "behavioral_pattern", "domains": ["emotional_safety", "attachment_security"], "valence": "concerning"},
    {"keywords": ["withdrawn", "isolates", "stopped seeing friends", "avoids social"],
     "observation_type": "social_functioning", "domains": ["social_belonging"], "valence": "concerning"},
    {"keywords": ["drinking heavily", "using substances", "relapsed", "drinks daily"],
     "observation_type": "substance_use_pattern", "domains": ["emotional_regulation"], "valence": "concerning"},
    {"keywords": ["unstable relationships", "idealizes then devalues", "intense and unstable"],
     "observation_type": "relationship_functioning", "domains": ["intimacy", "attachment_security"], "valence": "concerning"},
    {"keywords": ["struggling at work", "missed deadlines", "can't hold a job", "lost his job", "lost her job"],
     "observation_type": "occupational_functioning", "domains": ["competence"], "valence": "concerning"},
    {"keywords": ["close, trusting relationships", "maintains strong friendships", "secure relationships"],
     "observation_type": "relationship_functioning", "domains": ["intimacy", "social_belonging"], "valence": "protective"},
    {"keywords": ["excels at work", "thriving professionally", "doing well at school"],
     "observation_type": "occupational_functioning", "domains": ["competence"], "valence": "protective"},
    {"keywords": ["sober", "in recovery", "no longer drinking"],
     "observation_type": "substance_use_pattern", "domains": ["emotional_regulation"], "valence": "protective"},
]


# ============================================================
# AI extraction path
# ============================================================

def _build_extraction_prompt(text: str, persona_name: str) -> str:
    type_list = "\n".join(f'- "{t}"' for t in OBSERVATION_TYPES)
    return f"""You are extracting Behavior and Known-Outcome evidence about {persona_name}: observations about CURRENT or ONGOING functioning, not dated historical events.

TEXT TO ANALYZE:
{text}

Examples of what belongs here: "Timmy avoids physical contact and becomes visibly tense when his father is mentioned" (behavior), "maintains a stable long-term relationship" (relationship functioning), "missed several deadlines at work this year" (occupational functioning).

Examples of what does NOT belong here: a dated historical event like "was abused at 17" (that's an exposure, not a functional observation) - do not extract those here.

For each observation found, determine:
- observation_type: from the allowed list
- developmental_domains: which domains this touches (attachment_security, emotional_safety, stability, autonomy, identity, social_belonging, emotional_regulation, sexuality, competence, intimacy)
- valence: "concerning" if this signals difficulty/dysfunction, "protective" if it signals health/resilience, "neutral" if it's descriptive without a clear direction
- candidate_pattern_keys: ONLY if valence is "concerning" - real DSM-5/ICD-11-style disorder or pattern keys this observation could be evidence for (e.g. "ptsd", "depression", "social_anxiety", "borderline_personality"). Leave empty for "protective" or "neutral" valence.

ALLOWED observation_type values (use ONLY these):
{type_list}

Do not diagnose - candidate_pattern_keys are patterns worth considering as evidence accumulates, not a diagnosis. Phrase descriptions about {persona_name} by name, never "you" or "the user."

OUTPUT FORMAT (valid JSON only):
{{
  "observations": [
    {{"observation_type": "behavioral_pattern", "description": "...", "developmental_domains": ["emotional_safety"], "valence": "concerning", "candidate_pattern_keys": ["ptsd"]}}
  ]
}}

If nothing in the text describes current/ongoing functioning, return {{"observations": []}}. Respond with ONLY the JSON object."""


def _validate_and_filter(response: Dict) -> List[Dict]:
    observations = []
    for item in (response or {}).get("observations", []) or []:
        obs_type = item.get("observation_type")
        if obs_type not in OBSERVATION_TYPES:
            continue
        valence = item.get("valence")
        if valence not in VALENCES:
            valence = "neutral"
        description = _enforce_subject_attribution(item.get("description", ""))
        if description is None:
            continue
        domains = item.get("developmental_domains") or []
        from app.services.developmental_exposure_engine import DEVELOPMENTAL_DOMAINS
        domains = [d for d in domains if d in DEVELOPMENTAL_DOMAINS]

        candidate_patterns = []
        if valence == "concerning":
            from app.utils.symptom_taxonomy import SYMPTOM_TAXONOMY
            candidate_patterns = [p for p in (item.get("candidate_pattern_keys") or []) if p in SYMPTOM_TAXONOMY]

        observations.append({
            "observation_type": obs_type,
            "description": description,
            "developmental_domains": domains,
            "valence": valence,
            "candidate_pattern_keys": candidate_patterns,
        })
    return observations


async def extract_observations_ai(text: str, persona_name: str) -> Optional[List[Dict]]:
    """AI extraction path. Returns None on failure so the caller can fall back."""
    if not text or not text.strip():
        return []

    try:
        response = await openai_service.analyze(
            prompt=_build_extraction_prompt(text, persona_name),
            system_message=(
                "You extract current-functioning observations about a named person - behavior, "
                "relationships, work, substance use - distinct from dated historical events. "
                "You never diagnose and never address 'the user'. Respond ONLY with valid JSON."
            ),
            temperature=0.0,
            max_tokens=1000
        )
        return _validate_and_filter(response)
    except Exception as e:
        logger.warning(f"AI functional-observation extraction failed, will fall back to keyword pass: {e}")
        return None


# ============================================================
# Keyword fallback path (AI unavailable only)
# ============================================================

def extract_observations_keyword(text: str) -> List[Dict]:
    """
    Modest keyword fallback. No candidate_pattern_keys - see _KEYWORD_RULES'
    docstring note above for why that's deliberate.
    """
    if not text:
        return []

    text_lower = text.lower()
    observations = []
    for rule in _KEYWORD_RULES:
        for keyword in rule["keywords"]:
            if keyword in text_lower:
                observations.append({
                    "observation_type": rule["observation_type"],
                    "description": keyword,
                    "developmental_domains": rule["domains"],
                    "valence": rule["valence"],
                    "candidate_pattern_keys": [],
                })
                break
    return observations


# ============================================================
# Orchestration
# ============================================================

async def extract_observations_async(text: str, persona_name: str) -> List[Dict]:
    result = await extract_observations_ai(text, persona_name)
    if result is not None:
        return result
    logger.info("Using keyword fallback for functional observation extraction")
    return extract_observations_keyword(text)


def extract_observations(text: str, persona_name: str) -> List[Dict]:
    """Sync wrapper, mirroring every other engine in this rebuild."""
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("extract_observations called in async context; using keyword fallback.")
            return extract_observations_keyword(text)
    except RuntimeError:
        pass

    try:
        return asyncio.run(extract_observations_async(text, persona_name))
    except Exception as e:
        logger.warning(f"Functional observation extraction failed entirely, using keyword fallback: {e}")
        return extract_observations_keyword(text)


# ============================================================
# Persistence helper (not wired into any route yet - see docs/MIGRATION_MAP.md)
# ============================================================

def build_functional_observation_rows(
    persona_id: str,
    observations: List[Dict],
    speaker_role: str = "case_author",
    source_event_id: Optional[str] = None,
    age_observed: Optional[int] = None,
):
    from app.models.functional_observation import FunctionalObservation

    return [
        FunctionalObservation(
            persona_id=persona_id,
            source_event_id=source_event_id,
            speaker_role=speaker_role,
            observation_type=obs["observation_type"],
            description=obs["description"],
            developmental_domains=obs["developmental_domains"],
            candidate_pattern_keys=obs["candidate_pattern_keys"],
            valence=obs["valence"],
            age_observed=age_observed,
        )
        for obs in observations
    ]
