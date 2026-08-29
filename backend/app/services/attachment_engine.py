"""Deterministic developmental attachment projection from persisted State proposals."""
from typing import Dict, Optional

from app.services.state_trait_engine import STATE_STEP


STYLE_BASELINES = {
    "secure": {"attachment_anxiety": 0.2, "attachment_avoidance": 0.2, "relational_security": 0.8},
    "anxious": {"attachment_anxiety": 0.8, "attachment_avoidance": 0.25, "relational_security": 0.3},
    "insecure-anxious": {"attachment_anxiety": 0.8, "attachment_avoidance": 0.25, "relational_security": 0.3},
    "avoidant": {"attachment_anxiety": 0.25, "attachment_avoidance": 0.8, "relational_security": 0.3},
    "insecure-avoidant": {"attachment_anxiety": 0.25, "attachment_avoidance": 0.8, "relational_security": 0.3},
    "fearful-avoidant": {"attachment_anxiety": 0.8, "attachment_avoidance": 0.8, "relational_security": 0.15},
    "disorganized": {"attachment_anxiety": 0.8, "attachment_avoidance": 0.8, "relational_security": 0.15},
}


def dimensions_for_style(style: Optional[str]) -> Dict[str, float]:
    return dict(STYLE_BASELINES.get((style or "secure").lower(), STYLE_BASELINES["secure"]))


def derive_attachment_style(dimensions: Optional[Dict[str, float]]) -> str:
    values = dimensions or STYLE_BASELINES["secure"]
    anxious = values.get("attachment_anxiety", 0.2) >= 0.55
    avoidant = values.get("attachment_avoidance", 0.2) >= 0.55
    if anxious and avoidant:
        return "fearful-avoidant"
    if anxious:
        return "anxious"
    if avoidant:
        return "avoidant"
    return "secure"


def _move(value: float, direction: str, magnitude: str, invert: bool = False) -> float:
    if invert:
        direction = {"increase": "decrease", "decrease": "increase"}.get(direction, direction)
    step = STATE_STEP.get(magnitude, STATE_STEP["mild"])
    if direction == "increase":
        value += step
    elif direction == "decrease":
        value -= step
    return round(max(0.0, min(1.0, value)), 4)


def apply_attachment_update(current: Optional[Dict[str, float]], state_changes: Optional[Dict]) -> Dict[str, float]:
    """Apply only attachment-relevant interpreted State movement; unrelated events are no-ops."""
    updated = dict(current or STYLE_BASELINES["secure"])
    for variable, implication in (state_changes or {}).items():
        direction = implication.get("direction", "no_change")
        magnitude = implication.get("magnitude", "mild")
        if variable in ("trust", "relational_security"):
            updated["relational_security"] = _move(updated["relational_security"], direction, magnitude)
            updated["attachment_anxiety"] = _move(updated["attachment_anxiety"], direction, magnitude, invert=True)
        elif variable == "avoidance":
            updated["attachment_avoidance"] = _move(updated["attachment_avoidance"], direction, magnitude)
        elif variable == "threat_sensitivity":
            updated["attachment_anxiety"] = _move(updated["attachment_anxiety"], direction, magnitude)
    return updated
