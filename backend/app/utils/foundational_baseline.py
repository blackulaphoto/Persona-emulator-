"""
Foundational baseline utilities for persona creation.

Applies a one-time, bounded baseline bias from early environment signals.
"""
import re
from typing import Dict, List, Tuple


BASELINE_SCORE = 50
TRAIT_MIN = 40
TRAIT_MAX = 60

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


def derive_foundational_baseline(early_environment: str) -> Tuple[Dict[str, float], Dict[str, int]]:
    """
    Derive baseline personality from early environment signals.
    """
    signals = infer_foundational_signals(early_environment)
    deltas = _calculate_trait_deltas(signals)

    baseline_scores = {}
    for trait, delta in deltas.items():
        score = _clamp_int(BASELINE_SCORE + delta, TRAIT_MIN, TRAIT_MAX)
        baseline_scores[trait] = score / 100.0

    return baseline_scores, signals
