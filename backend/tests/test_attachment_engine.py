from app.services.attachment_engine import (
    apply_attachment_update, derive_attachment_style, dimensions_for_style,
)


def test_style_baselines_round_trip():
    for style in ("secure", "anxious", "avoidant", "fearful-avoidant"):
        assert derive_attachment_style(dimensions_for_style(style)) == style


def test_rejection_relevant_state_accumulates_attachment_insecurity():
    dimensions = dimensions_for_style("secure")
    proposal = {
        "trust": {"direction": "decrease", "magnitude": "high"},
        "avoidance": {"direction": "increase", "magnitude": "high"},
        "threat_sensitivity": {"direction": "increase", "magnitude": "high"},
    }
    dimensions = apply_attachment_update(dimensions, proposal)
    dimensions = apply_attachment_update(dimensions, proposal)
    assert derive_attachment_style(dimensions) == "fearful-avoidant"


def test_secure_relationship_can_reduce_anxiety_and_avoidance():
    dimensions = dimensions_for_style("fearful-avoidant")
    proposal = {
        "trust": {"direction": "increase", "magnitude": "high"},
        "avoidance": {"direction": "decrease", "magnitude": "high"},
        "threat_sensitivity": {"direction": "decrease", "magnitude": "high"},
    }
    dimensions = apply_attachment_update(dimensions, proposal)
    dimensions = apply_attachment_update(dimensions, proposal)
    assert derive_attachment_style(dimensions) == "secure"


def test_unrelated_state_change_leaves_attachment_unchanged():
    dimensions = dimensions_for_style("secure")
    assert apply_attachment_update(dimensions, {"mood": {"direction": "decrease", "magnitude": "high"}}) == dimensions
