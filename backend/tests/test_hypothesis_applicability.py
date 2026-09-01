"""
Tests for app/services/hypothesis_applicability.py - current-age
applicability policy for canonical clinical hypotheses.

Two directions:
  - max_current_age (reactive_attachment_disorder): a childhood-only
    clinical presentation. An adult persona's accumulated RAD evidence is
    real developmental history, not a live current condition - it must not
    appear as an active/current hypothesis on a 40-year-old persona's
    dashboard, chat context, or narrative "current hypotheses" section.
  - min_current_age (the personality-disorder pattern_keys): DSM-5 does not
    diagnose a personality disorder before a stable, long-duration pattern
    can be established, conventionally not before adulthood - a child
    persona's evidence for one of these is a real emerging pattern, not yet
    a diagnosable personality disorder.

In both directions, persisted evidence is never deleted by this module -
only current-hypothesis PRESENTATION is filtered. That's enforced by the
callers (persona_board.py, narrative_service.py, evidence_accumulator.
project_current_trauma_markers), not here; this file tests the pure
decision function only.
"""
from app.services.hypothesis_applicability import (
    is_currently_applicable,
    applicability_for,
    HYPOTHESIS_APPLICABILITY,
)


class TestReactiveAttachmentDisorderMaxAge:
    def test_applicable_for_a_child_persona(self):
        assert is_currently_applicable("reactive_attachment_disorder", 8) is True

    def test_applicable_at_the_boundary_age(self):
        assert is_currently_applicable("reactive_attachment_disorder", 17) is True

    def test_not_applicable_just_past_the_boundary(self):
        assert is_currently_applicable("reactive_attachment_disorder", 18) is False

    def test_not_applicable_for_a_real_production_adult_age(self):
        # The exact production regression: a 40-year-old persona.
        assert is_currently_applicable("reactive_attachment_disorder", 40) is False

    def test_applicability_for_returns_historical_framing_when_inapplicable(self):
        result = applicability_for("reactive_attachment_disorder", 40)
        assert result["currently_applicable"] is False
        assert result["historical_developmental_only"] is True
        assert result["historical_label"]
        assert result["reason"]

    def test_applicability_for_marks_currently_applicable_for_a_child(self):
        result = applicability_for("reactive_attachment_disorder", 8)
        assert result["currently_applicable"] is True
        assert result["historical_developmental_only"] is False


class TestPersonalityDisorderMinAge:
    def test_not_applicable_for_a_child_persona(self):
        assert is_currently_applicable("avoidant_personality", 8) is False

    def test_applicable_at_adulthood(self):
        assert is_currently_applicable("avoidant_personality", 18) is True

    def test_applicable_at_the_boundary_age(self):
        assert is_currently_applicable("borderline_personality", 18) is True

    def test_not_applicable_just_before_the_boundary(self):
        assert is_currently_applicable("borderline_personality", 17) is False

    def test_every_personality_disorder_key_has_a_min_age_rule(self):
        for key in (
            "avoidant_personality", "borderline_personality", "obsessive_compulsive_personality",
            "schizoid_personality", "dependent_personality", "paranoid_personality",
        ):
            assert HYPOTHESIS_APPLICABILITY[key].get("min_current_age") == 18, key

    def test_applicability_for_a_child_gives_historical_framing_not_diagnosis(self):
        result = applicability_for("obsessive_compulsive_personality", 10)
        assert result["currently_applicable"] is False
        assert result["historical_label"]


class TestUnscopedHypothesesAreAlwaysApplicable:
    """
    Deliberately conservative: pattern_keys with no clear, defensible age
    boundary (mood/anxiety/trauma/adjustment/grief/substance-use - all of
    which have real documented presentations across childhood, adolescence,
    and adulthood) are NOT scoped here, matching evidence_accumulator.py's
    own "a strategy with no defensible single-pattern link is left unmapped
    rather than forced into a clinically wrong one" philosophy.
    """

    def test_generalized_anxiety_applicable_at_any_age(self):
        assert is_currently_applicable("generalized_anxiety", 5) is True
        assert is_currently_applicable("generalized_anxiety", 80) is True

    def test_ptsd_and_complex_ptsd_applicable_at_any_age(self):
        assert is_currently_applicable("ptsd", 6) is True
        assert is_currently_applicable("complex_ptsd", 90) is True

    def test_unknown_pattern_key_defaults_to_applicable(self):
        assert is_currently_applicable("some_future_pattern_key", 5) is True
        assert applicability_for("some_future_pattern_key", 5) == {
            "currently_applicable": True,
            "historical_developmental_only": False,
            "historical_label": None,
            "reason": None,
        }
