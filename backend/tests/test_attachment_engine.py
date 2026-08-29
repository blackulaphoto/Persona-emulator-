from app.services.attachment_engine import (
    apply_attachment_update, apply_attachment_protection, apply_attachment_exposure,
    derive_attachment_style, dimensions_for_style,
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


def test_maladaptive_strategy_cannot_claim_positive_security():
    dimensions = dimensions_for_style("secure")
    changed = apply_attachment_update(dimensions,
        {"relational_security": {"direction": "increase", "magnitude": "high"}}, "people_pleasing")
    assert changed["relational_security"] == dimensions["relational_security"]
    assert changed["attachment_anxiety"] > dimensions["attachment_anxiety"]


def test_attachment_protective_factor_supports_recovery():
    dimensions = dimensions_for_style("fearful-avoidant")
    changed = apply_attachment_protection(dimensions,
        [{"domains_buffered": ["attachment_security"], "factor_type": "reliable_relationship"}])
    assert changed["relational_security"] > dimensions["relational_security"]
    assert changed["attachment_anxiety"] < dimensions["attachment_anxiety"]
    assert changed["attachment_avoidance"] < dimensions["attachment_avoidance"]


def test_attachment_domain_exposure_has_deterministic_adverse_effect():
    dimensions = dimensions_for_style("secure")
    changed = apply_attachment_exposure(dimensions,
        [{"developmental_domains": ["attachment_security"], "exposure_type": "peer_rejection"}])
    assert changed["relational_security"] < dimensions["relational_security"]
    assert changed["attachment_anxiety"] > dimensions["attachment_anxiety"]
    assert changed["attachment_avoidance"] > dimensions["attachment_avoidance"]
