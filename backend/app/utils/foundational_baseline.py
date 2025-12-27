"""
Foundational baseline utilities for persona creation.

Applies a one-time, bounded baseline bias from early environment signals.
"""
import re
import os
import logging
from typing import Dict, List, Tuple
from app.services.openai_service import OpenAIService


# Initialize OpenAI service for baseline analysis
logger = logging.getLogger(__name__)

openai_service = OpenAIService(
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY"),
    model="gpt-4"
)

BASELINE_SCORE = 50
TRAIT_MIN = 20  # Expanded from 40 to allow more variation
TRAIT_MAX = 80  # Expanded from 60 to allow more variation

SIGNAL_MIN = -2
SIGNAL_MAX = 2


def _clamp_int(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def _clamp_float(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _keyword_hits(text: str, keywords: List[str]) -> int:
    hits = 0
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text):
            hits += 1
    return hits


def infer_foundational_signals(early_environment: str) -> Dict[str, int]:
    """
    Infer minimal foundational environment signals from text.

    Signals are conservative and bounded to avoid overfitting.
    threatExposure uses positive values for low threat and negative for high threat.
    """
    text = (early_environment or "").lower()

    signals = {
        "emotionalSafety": 0,
        "stability": 0,
        "caregiverReliability": 0,
        "attachmentConsistency": 0,
        "threatExposure": 0,
        "socialSafety": 0,
        "explorationSupport": 0
    }

    mapping = {
        "emotionalSafety": {
            "positive": ["loving", "supportive", "nurturing", "warm", "safe"],
            "negative": ["abusive", "neglectful", "cold", "hostile", "unsafe"]
        },
        "stability": {
            "positive": ["stable", "predictable", "routine", "steady"],
            "negative": ["chaotic", "unstable", "unpredictable", "frequent", "evicted"]
        },
        "caregiverReliability": {
            "positive": ["reliable", "present", "available", "attentive", "dependable", "caring"],
            "negative": ["absent", "unavailable", "addicted", "incarcerated", "unreliable"]
        },
        "attachmentConsistency": {
            "positive": ["secure", "close bond"],
            "negative": ["inconsistent", "on and off", "hot and cold"]
        },
        "threatExposure": {
            "positive": ["protected", "peaceful", "low crime"],
            "negative": ["violence", "violent", "crime", "danger", "threatening"]
        },
        "socialSafety": {
            "positive": ["friendly", "included", "accepted", "safe school"],
            "negative": ["bullied", "bullying", "isolated", "rejected"]
        },
        "explorationSupport": {
            "positive": ["encouraged", "curious", "creative", "explore", "adventurous"],
            "negative": ["restricted", "controlled", "strict", "discouraged", "sheltered"]
        }
    }

    for signal, keywords in mapping.items():
        positive_hits = _keyword_hits(text, keywords["positive"])
        negative_hits = _keyword_hits(text, keywords["negative"])
        delta = positive_hits - negative_hits
        signals[signal] = _clamp_int(delta, SIGNAL_MIN, SIGNAL_MAX)

    return signals


def _calculate_trait_deltas(signals: Dict[str, int]) -> Dict[str, int]:
    neuroticism_delta = (
        (-signals["emotionalSafety"] * 4) +
        (-signals["stability"] * 3) +
        (-signals["threatExposure"] * 4)
    )
    neuroticism_delta = _clamp_int(neuroticism_delta, -12, 12)

    agreeableness_delta = (
        (signals["caregiverReliability"] * 3) +
        (signals["attachmentConsistency"] * 3)
    )
    agreeableness_delta = _clamp_int(agreeableness_delta, -8, 8)

    extraversion_delta = (
        (signals["socialSafety"] * 2) +
        (signals["stability"] * 2)
    )
    extraversion_delta = _clamp_int(extraversion_delta, -6, 6)

    conscientiousness_delta = (signals["stability"] * 2)
    conscientiousness_delta = _clamp_int(conscientiousness_delta, -4, 4)

    openness_delta = (signals["explorationSupport"] * 2)
    openness_delta = _clamp_int(openness_delta, -4, 4)

    return {
        "openness": openness_delta,
        "conscientiousness": conscientiousness_delta,
        "extraversion": extraversion_delta,
        "agreeableness": agreeableness_delta,
        "neuroticism": neuroticism_delta
    }


def clamp_personality_range(personality: Dict[str, float]) -> Dict[str, float]:
    """
    Clamp traits to the 40-60 range (0.4-0.6).
    """
    return {
        trait: _clamp_float(value, TRAIT_MIN / 100.0, TRAIT_MAX / 100.0)
        for trait, value in personality.items()
    }


async def analyze_baseline_personality_ai(
    early_environment: str,
    baseline_age: int,
    gender: str
) -> Dict[str, float]:
    """
    Use AI to analyze early environment and derive realistic baseline personality.

    Args:
        early_environment: User's description of childhood background
        baseline_age: Starting age of persona
        gender: Gender of persona

    Returns:
        Dict with Big Five personality traits (0.0-1.0 scale)
    """
    prompt = f"""You are a developmental psychologist analyzing how early childhood environment shapes baseline personality.

PERSON CONTEXT:
Age: {baseline_age}
Gender: {gender}

EARLY ENVIRONMENT / CHILDHOOD BACKGROUND:
{early_environment}

ANALYSIS TASK:
Based on this early environment, determine the person's baseline personality using the Big Five model.

IMPORTANT GUIDELINES:
1. **Be realistic and nuanced** - Not all difficult childhoods produce extreme traits
2. **Consider protective factors** - Resilience, supportive relationships, natural temperament
3. **Age matters** - At age {baseline_age}, some personality traits are still developing
4. **Avoid stereotypes** - Abuse doesn't automatically mean neuroticism = 0.9
5. **Use full range** - Traits can realistically range from 0.2 to 0.8
6. **Context is key** - A loving but strict household is different from an abusive one

TRAIT DEFINITIONS:
- **Openness** (0.0-1.0): Imagination, curiosity, creativity, openness to new experiences
- **Conscientiousness** (0.0-1.0): Organization, responsibility, self-discipline, goal-directed behavior
- **Extraversion** (0.0-1.0): Sociability, assertiveness, energy, positive emotions
- **Agreeableness** (0.0-1.0): Compassion, cooperation, trust, kindness
- **Neuroticism** (0.0-1.0): Anxiety, emotional instability, vulnerability to stress

EXAMPLES OF REALISTIC SCORING:
- Loving, stable home → Neuroticism: 0.3-0.4, Agreeableness: 0.6-0.7
- Severe abuse/neglect → Neuroticism: 0.7-0.8, Agreeableness: 0.3-0.4, but Openness could still be 0.5
- Strict but caring → Conscientiousness: 0.6-0.7, Agreeableness: 0.5-0.6
- Chaotic but loving → Neuroticism: 0.5-0.6, Extraversion: 0.5-0.6

OUTPUT FORMAT (valid JSON only):
{{
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
    "reasoning": "Brief explanation of why these baseline traits make sense given the early environment."
}}

Respond ONLY with valid JSON."""

    try:
        response = await openai_service.analyze(
            prompt=prompt,
            system_message="You are a developmental psychologist specializing in personality formation and early childhood development. Respond ONLY with valid JSON.",
            temperature=0.7,
            max_tokens=800
        )

        # Extract traits
        baseline_personality = {
            "openness": _clamp_float(response.get("openness", 0.5), 0.0, 1.0),
            "conscientiousness": _clamp_float(response.get("conscientiousness", 0.5), 0.0, 1.0),
            "extraversion": _clamp_float(response.get("extraversion", 0.5), 0.0, 1.0),
            "agreeableness": _clamp_float(response.get("agreeableness", 0.5), 0.0, 1.0),
            "neuroticism": _clamp_float(response.get("neuroticism", 0.5), 0.0, 1.0)
        }

        logger.info(f"AI baseline analysis: {response.get('reasoning', 'No reasoning provided')}")

        return baseline_personality

    except Exception as e:
        logger.exception(f"AI baseline analysis failed: {e}")
        # Fallback to keyword-based analysis
        return None


def derive_foundational_baseline(early_environment: str, baseline_age: int = 10, gender: str = "unknown") -> Tuple[Dict[str, float], Dict[str, int]]:
    """
    Derive baseline personality from early environment signals.

    First attempts AI analysis, falls back to keyword-based if AI fails.
    """
    # Try AI analysis first (async, so we need to handle it carefully)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        ai_baseline = loop.run_until_complete(
            analyze_baseline_personality_ai(early_environment, baseline_age, gender)
        )
        if ai_baseline:
            # Still infer signals for tracking purposes
            signals = infer_foundational_signals(early_environment)
            return ai_baseline, signals
    except Exception as e:
        logger.warning(f"AI baseline analysis failed, using keyword fallback: {e}")

    # Fallback to keyword-based analysis
    signals = infer_foundational_signals(early_environment)
    deltas = _calculate_trait_deltas(signals)

    baseline_scores = {}
    for trait, delta in deltas.items():
        score = _clamp_int(BASELINE_SCORE + delta, TRAIT_MIN, TRAIT_MAX)
        baseline_scores[trait] = score / 100.0

    return baseline_scores, signals
