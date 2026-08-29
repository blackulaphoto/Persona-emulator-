"""
Developmental Exposure Extractor.

Replaces the role of app/utils/backstory_symptom_mapper.py. Reads raw text
(backstory or a single experience description) and extracts what the text
describes as having happened - exposures and protective factors - mapped to
developmental domains. It does not assign disorders, severities, or
diagnoses; that judgment belongs to the evidence accumulator, built from many
exposures, protective factors, and narration signals accumulated across the
whole timeline (see docs/MIGRATION_MAP.md).

Two extraction paths:
  - AI path (primary): an LLM reads the text with instructions to respect
    negation, hedging, and denial, and to extract only what the text
    affirmatively describes - not what it merely mentions or explicitly
    rules out.
  - Keyword fallback: used only if the AI call fails. Includes a simple
    negation-window check (looks for a negation cue shortly before a matched
    keyword) - a real mitigation over the old backstory_symptom_mapper.py,
    but still an approximation, not real language understanding. It exists
    so the app degrades gracefully, not as the primary source of truth.

This module does not write to the database. Callers are responsible for
persisting results as DevelopmentalExposure / ProtectiveFactor rows.
"""
import re
import logging
from typing import Dict, List, Optional, TypedDict

from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=None,  # resolved from settings/env inside OpenAIService, matching foundational_baseline.py
    model="gpt-4o"
)


# ============================================================
# Controlled vocabulary
# ============================================================
# Kept small and stable so the evidence accumulator (step 4) can rely on
# consistent keys across personas instead of matching freeform strings a
# model might invent differently each time.
DEVELOPMENTAL_DOMAINS = (
    "attachment_security",
    "emotional_safety",
    "stability",
    "autonomy",
    "identity",
    "social_belonging",
    "emotional_regulation",
    "sexuality",
    "competence",
    "intimacy",
)

# exposure_type -> {domains, keywords}. "keywords" is used ONLY by the
# keyword fallback path - the AI path reasons over the text directly and
# picks exposure_type values from this dict's keys.
EXPOSURE_TAXONOMY: Dict[str, Dict] = {
    "caregiver_substance_use": {
        "domains": ["attachment_security", "emotional_safety", "stability"],
        "keywords": ["drank", "drinking", "alcoholic", "addicted", "meth", "heroin", "overdose", "rehab"],
    },
    "caregiver_absence": {
        "domains": ["attachment_security", "stability"],
        "keywords": ["disappeared", "absent", "gone for days", "never around", "abandoned"],
    },
    "caregiver_emotional_unavailability": {
        "domains": ["attachment_security", "emotional_regulation", "identity"],
        "keywords": ["emotionally unavailable", "emotionally distant", "cold and dismissive", "never affectionate"],
    },
    "caregiver_mental_illness": {
        "domains": ["attachment_security", "stability", "emotional_safety"],
        "keywords": ["bipolar", "mentally ill", "psychiatric hospital", "unstable moods", "manic"],
    },
    "household_unpredictability": {
        "domains": ["stability", "emotional_safety"],
        "keywords": ["chaotic", "unpredictable", "walking on eggshells", "never knew what mood"],
    },
    "physical_discipline_or_violence": {
        "domains": ["emotional_safety", "attachment_security", "emotional_regulation"],
        "keywords": ["beaten", "spanked", "whipped", "bruises", "choked", "slapped", "hit me",
                     "physically abused", "abused by", "was abused"],
    },
    "domestic_violence_witnessed": {
        "domains": ["emotional_safety", "stability", "emotional_regulation"],
        "keywords": ["parents fighting", "hit my mother", "domestic violence", "police were called"],
    },
    "sexual_boundary_violation": {
        "domains": ["emotional_safety", "sexuality", "intimacy", "attachment_security"],
        "keywords": ["molested", "sexual abuse", "raped", "inappropriate touching", "fondled"],
    },
    "emotional_abuse_or_humiliation": {
        "domains": ["identity", "emotional_regulation", "emotional_safety"],
        "keywords": ["humiliated", "belittled", "called stupid", "constant criticism"],
    },
    "neglect_of_basic_needs": {
        "domains": ["emotional_safety", "stability", "attachment_security"],
        "keywords": ["no food", "starving", "left alone", "no one noticed", "forgotten about"],
    },
    "caregiver_incarceration": {
        "domains": ["attachment_security", "stability"],
        "keywords": ["prison", "incarcerated", "locked up"],
    },
    "separation_or_divorce": {
        "domains": ["stability", "attachment_security"],
        "keywords": ["divorced", "separated", "custody battle"],
    },
    "death_of_caregiver_or_family": {
        "domains": ["attachment_security", "stability", "emotional_safety"],
        "keywords": ["passed away", "died when i was", "funeral", "lost my mother", "lost my father"],
    },
    "frequent_relocation": {
        "domains": ["stability", "social_belonging"],
        "keywords": ["moved constantly", "new school every year", "never stayed in one place"],
    },
    "financial_instability": {
        "domains": ["stability", "emotional_safety"],
        "keywords": ["poverty", "evicted", "homeless", "couldn't afford"],
    },
    "peer_rejection_or_bullying": {
        "domains": ["social_belonging", "identity", "emotional_regulation"],
        "keywords": ["bullied", "picked on", "excluded", "made fun of"],
    },
    "high_achievement_pressure": {
        "domains": ["identity", "competence", "autonomy"],
        "keywords": ["had to be the best", "only as were acceptable", "pressure to succeed"],
    },
    "chronic_illness_self": {
        "domains": ["autonomy", "competence", "emotional_safety"],
        "keywords": ["chronically ill", "hospitalized", "in and out of hospitals"],
    },
    "chronic_illness_family_member": {
        "domains": ["stability", "emotional_safety"],
        "keywords": ["mother was sick", "father had cancer", "sibling was ill"],
    },
}

# factor_type -> {domains, keywords}, drawn from the spec's own protective-factor list.
PROTECTIVE_FACTOR_TAXONOMY: Dict[str, Dict] = {
    "reliable_close_relationship": {
        "domains": ["attachment_security", "intimacy", "stability"],
        "keywords": ["reliable partner", "secure relationship", "consistently offered support", "repaired conflicts"],
    },
    "stable_alternate_caregiver": {
        "domains": ["attachment_security", "stability"],
        "keywords": ["grandmother raised", "stepped in", "aunt took care of", "stable second parent"],
    },
    "mentor": {
        "domains": ["identity", "competence"],
        "keywords": ["mentor", "coach believed in", "teacher who saw something in me"],
    },
    "sibling_bond": {
        "domains": ["attachment_security", "social_belonging"],
        "keywords": ["close with my sister", "brother protected me", "we had each other"],
    },
    "temperament": {
        "domains": ["emotional_regulation", "identity"],
        "keywords": ["naturally resilient", "easygoing", "even-tempered", "adaptable"],
    },
    "community": {
        "domains": ["social_belonging", "emotional_safety"],
        "keywords": ["church community", "close-knit neighborhood", "community center"],
    },
    "financial_security": {
        "domains": ["stability"],
        "keywords": ["financially stable", "comfortable growing up", "never worried about money"],
    },
    "therapy_or_professional_support": {
        "domains": ["emotional_regulation", "identity"],
        "keywords": ["saw a therapist", "started counseling", "started therapy"],
    },
    "friendship": {
        "domains": ["social_belonging", "identity"],
        "keywords": ["best friend", "close friends", "always had someone"],
    },
    "intelligence_or_giftedness": {
        "domains": ["competence", "identity"],
        "keywords": ["gifted program", "highly intelligent", "academically talented"],
    },
    "spirituality": {
        "domains": ["identity", "stability"],
        "keywords": ["faith helped", "church community gave", "spirituality helped"],
    },
    "mastery_experience": {
        "domains": ["competence", "autonomy"],
        "keywords": ["won a competition", "excelled at", "proud accomplishment"],
    },
    "explicit_reassurance_from_caregiver": {
        "domains": ["attachment_security", "identity"],
        "keywords": ["told me it wasn't my fault", "reassured me", "said i was safe"],
    },
}


class ExposureFinding(TypedDict, total=False):
    exposure_type: str
    developmental_domains: List[str]
    raw_text: str
    age_hint: Optional[int]


class ProtectiveFinding(TypedDict, total=False):
    factor_type: str
    domains_buffered: List[str]
    raw_text: str
    age_hint: Optional[int]


# ============================================================
# AI extraction path
# ============================================================

def _build_extraction_prompt(text: str) -> str:
    exposure_list = "\n".join(f'- "{k}"' for k in EXPOSURE_TAXONOMY.keys())
    protective_list = "\n".join(f'- "{k}"' for k in PROTECTIVE_FACTOR_TAXONOMY.keys())
    domain_list = "\n".join(f'- "{d}"' for d in DEVELOPMENTAL_DOMAINS)

    return f"""You are extracting developmental exposures from a text description of someone's life. You are NOT diagnosing, and you are NOT assigning symptoms or disorders. You are identifying what the text objectively describes as having happened or being present.

TEXT TO ANALYZE:
{text}

CRITICAL RULES ON NEGATION AND CONTEXT (READ CAREFULLY):
1. If the text explicitly DENIES, NEGATES, or RULES OUT something ("I was not abused", "there was no violence", "nothing like that ever happened"), do NOT extract that as an exposure. A denied event is not an exposure.
2. If the text mentions something only hypothetically, as someone else's experience, or as a comparison ("unlike my friend who was neglected, I..."), do NOT extract it as this person's exposure.
3. Hedged or minimized language ("kind of chaotic sometimes", "he drank a little") still counts as an exposure if the underlying event is affirmed - hedging affects how it's described, not whether it happened. Only a genuine denial removes it.
4. Extract only what this specific text affirmatively describes. Do not infer exposures the text doesn't actually support.
5. The same sentence can support MULTIPLE exposures (e.g. one sentence about a drinking, absent father supports both caregiver_substance_use and caregiver_absence).
6. Also extract PROTECTIVE FACTORS the text describes - people, resources, or qualities that appear to have buffered or supported the person. Absence of anything protective is not itself a finding - only extract what's actually described.

ALLOWED exposure_type values (use ONLY these, do not invent new ones):
{exposure_list}

ALLOWED factor_type values for protective factors (use ONLY these):
{protective_list}

ALLOWED developmental_domains values (use ONLY these):
{domain_list}

For each exposure you extract, select developmental_domains from the allowed list that THIS specific exposure plausibly implicates for this person given the text's context (age, description) - don't just copy a generic default if the text gives you a reason to be more specific. If nothing in the text matches any allowed exposure_type or factor_type, return empty arrays. Do not force a match.

OUTPUT FORMAT (valid JSON only, no other text):
{{
  "exposures": [
    {{"exposure_type": "caregiver_substance_use", "developmental_domains": ["attachment_security", "emotional_safety"], "raw_text": "the exact phrase this was extracted from", "age_hint": null}}
  ],
  "protective_factors": [
    {{"factor_type": "stable_alternate_caregiver", "domains_buffered": ["attachment_security"], "raw_text": "the exact phrase this was extracted from", "age_hint": null}}
  ]
}}

age_hint should be an integer ONLY if the text explicitly states an age for that specific exposure/factor (e.g. "when I was 8"); otherwise null. Respond with ONLY the JSON object."""


def _validate_and_filter(response: Dict) -> Dict[str, List[Dict]]:
    """
    Defense against the model inventing types outside the controlled
    vocabulary, or dropping required fields. Silently drops anything that
    doesn't validate rather than raising - a partially-useful extraction is
    better than none.
    """
    exposures = []
    for item in (response or {}).get("exposures", []) or []:
        exposure_type = item.get("exposure_type")
        if exposure_type not in EXPOSURE_TAXONOMY:
            continue
        domains = [d for d in (item.get("developmental_domains") or []) if d in DEVELOPMENTAL_DOMAINS]
        if not domains:
            domains = EXPOSURE_TAXONOMY[exposure_type]["domains"]
        exposures.append({
            "exposure_type": exposure_type,
            "developmental_domains": domains,
            "raw_text": item.get("raw_text", ""),
            "age_hint": item.get("age_hint"),
        })

    protective_factors = []
    for item in (response or {}).get("protective_factors", []) or []:
        factor_type = item.get("factor_type")
        if factor_type not in PROTECTIVE_FACTOR_TAXONOMY:
            continue
        domains = [d for d in (item.get("domains_buffered") or []) if d in DEVELOPMENTAL_DOMAINS]
        if not domains:
            domains = PROTECTIVE_FACTOR_TAXONOMY[factor_type]["domains"]
        protective_factors.append({
            "factor_type": factor_type,
            "domains_buffered": domains,
            "raw_text": item.get("raw_text", ""),
            "age_hint": item.get("age_hint"),
        })

    return {"exposures": exposures, "protective_factors": protective_factors}


async def extract_exposures_ai(text: str) -> Optional[Dict[str, List[Dict]]]:
    """AI extraction path. Returns None on failure so the caller can fall back."""
    if not text or not text.strip():
        return {"exposures": [], "protective_factors": []}

    try:
        response = await openai_service.analyze(
            prompt=_build_extraction_prompt(text),
            system_message=(
                "You are a careful developmental-history annotator. You extract only what "
                "text affirmatively describes, respect negation and denial, and never invent "
                "exposures the text doesn't support. Respond ONLY with valid JSON."
            ),
            temperature=0.2,  # extraction, not creative generation
            max_tokens=1200
        )
        return _validate_and_filter(response)
    except Exception as e:
        logger.warning(f"AI exposure extraction failed, will fall back to keyword pass: {e}")
        return None


# ============================================================
# Keyword fallback path (AI unavailable only)
# ============================================================

NEGATION_CUES = (
    "not", "never", "no", "nt", "wasnt", "isnt", "werent", "didnt",
    "doesnt", "dont", "without", "none", "nothing", "far",
    "nobody", "noone",
)
NEGATION_WINDOW = 4  # words to look back from a matched keyword


def _is_negated(text_lower: str, match_start: int) -> bool:
    """
    Approximate negation check for the keyword fallback path only. Looks a
    short window of words back from the match for a negation cue. This is
    NOT real NLP negation-scope detection - it's a cheap mitigation for when
    the AI path is unavailable, not a substitute for it.
    """
    preceding = re.sub(r"[^a-z' ]", " ", text_lower[:match_start])
    preceding_words = [w.replace("'", "") for w in preceding.split()][-NEGATION_WINDOW:]
    return any(cue in preceding_words for cue in NEGATION_CUES)


def extract_exposures_keyword(text: str) -> Dict[str, List[Dict]]:
    """
    Keyword-matching fallback, used only if the AI path fails. Includes a
    negation-window check so "I was not abused" does not fire the same false
    positive the old backstory_symptom_mapper.py had - but this is still an
    approximation, not real language understanding.
    """
    if not text:
        return {"exposures": [], "protective_factors": []}

    text_lower = text.lower()

    exposures = []
    for exposure_type, meta in EXPOSURE_TAXONOMY.items():
        for keyword in meta["keywords"]:
            idx = text_lower.find(keyword)
            if idx == -1 or _is_negated(text_lower, idx):
                continue
            exposures.append({
                "exposure_type": exposure_type,
                "developmental_domains": meta["domains"],
                "raw_text": keyword,
                "age_hint": None,
            })
            break  # one hit per exposure_type is enough for the fallback path

    protective_factors = []
    for factor_type, meta in PROTECTIVE_FACTOR_TAXONOMY.items():
        for keyword in meta["keywords"]:
            idx = text_lower.find(keyword)
            if idx == -1 or _is_negated(text_lower, idx):
                continue
            protective_factors.append({
                "factor_type": factor_type,
                "domains_buffered": meta["domains"],
                "raw_text": keyword,
                "age_hint": None,
            })
            break

    return {"exposures": exposures, "protective_factors": protective_factors}


# ============================================================
# Orchestration
# ============================================================

async def extract_developmental_exposures_async(text: str) -> Dict[str, List[Dict]]:
    """Primary entry point. Tries the AI path; falls back to keyword-only on failure."""
    result = await extract_exposures_ai(text)
    if result is not None:
        return result

    logger.info("Using keyword fallback for exposure extraction")
    return extract_exposures_keyword(text)


def extract_developmental_exposures(text: str) -> Dict[str, List[Dict]]:
    """
    Sync wrapper, mirroring app/utils/foundational_baseline.py's pattern.
    Falls back to the keyword-only path if called inside a running event loop.
    """
    import asyncio

    try:
        running_loop = asyncio.get_running_loop()
        if running_loop.is_running():
            logger.warning("extract_developmental_exposures called in async context; using keyword fallback.")
            return extract_exposures_keyword(text)
    except RuntimeError:
        pass

    try:
        return asyncio.run(extract_developmental_exposures_async(text))
    except Exception as e:
        logger.warning(f"Exposure extraction failed entirely, using keyword fallback: {e}")
        return extract_exposures_keyword(text)


# ============================================================
# Persistence helper (not wired into any route yet - see docs/MIGRATION_MAP.md)
# ============================================================

def build_exposure_and_protective_rows(
    persona_id: str,
    extraction: Dict[str, List[Dict]],
    source: str,
    source_event_id: Optional[str] = None,
    age_at_exposure: Optional[int] = None,
    speaker_role: str = "case_author",
):
    """
    Converts an extraction result into unsaved DevelopmentalExposure /
    ProtectiveFactor ORM instances. Caller is responsible for db.add()/commit().
    Deliberately not called from any route yet - wiring this into
    personas.py/experiences.py to replace backstory_symptom_mapper.py is a
    separate, explicit next step, not a silent swap.

    Args:
        persona_id: the persona these rows attach to
        extraction: output of extract_developmental_exposures[_async]
        source: "backstory" | "experience"
        source_event_id: Experience.id, if extraction came from an experience
        age_at_exposure: fallback age if a finding has no explicit age_hint
        speaker_role: who reported this - persona_voice | case_author |
            third_party_report | source_material. Provenance only, not a
            gate - see DevelopmentalExposure's model docstring.
    """
    from app.models.developmental_exposure import DevelopmentalExposure
    from app.models.protective_factor import ProtectiveFactor

    exposure_rows = [
        DevelopmentalExposure(
            persona_id=persona_id,
            source_event_id=source_event_id,
            source=source,
            speaker_role=speaker_role,
            age_at_exposure=finding.get("age_hint") or age_at_exposure,
            exposure_type=finding["exposure_type"],
            developmental_domains=finding["developmental_domains"],
            raw_text=finding.get("raw_text"),
        )
        for finding in extraction.get("exposures", [])
    ]

    protective_rows = [
        ProtectiveFactor(
            persona_id=persona_id,
            source_event_id=source_event_id,
            speaker_role=speaker_role,
            factor_type=finding["factor_type"],
            description=finding.get("raw_text"),
            active_from_age=finding.get("age_hint") or age_at_exposure,
            domains_buffered=finding["domains_buffered"],
        )
        for finding in extraction.get("protective_factors", [])
    ]

    return exposure_rows, protective_rows
