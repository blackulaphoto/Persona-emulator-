"""
Tests for app/services/safety_router.py (docs/MIGRATION_MAP.md step 10).

This is the highest-stakes module in the whole rebuild, so these tests are
the most important in this codebase: real crisis language in a live
message must always be caught (check_input is deliberately high-recall),
and legitimate in-character distress must never be silently blocked
(check_output is deliberately narrow).
"""
from app.services.safety_router import (
    check_input,
    check_output,
    build_crisis_response,
    build_output_safety_note,
    CRISIS_CATEGORIES,
)


class TestInputDetectionCatchesRealCrisisLanguage:
    def test_suicide_language_detected(self):
        assert check_input("I want to kill myself") == "suicide"
        assert check_input("honestly I just want to die") == "suicide"
        assert check_input("there's no reason to live anymore") == "suicide"

    def test_self_harm_language_detected(self):
        assert check_input("I've been cutting myself") == "self_harm"
        assert check_input("I want to hurt myself tonight") == "self_harm"

    def test_violence_to_others_detected(self):
        assert check_input("I'm going to kill him") == "violence_to_others"

    def test_abuse_in_progress_detected(self):
        assert check_input("he's hitting me right now") == "abuse_in_progress"

    def test_case_insensitive(self):
        assert check_input("I WANT TO KILL MYSELF") == "suicide"

    def test_suicide_takes_priority_when_multiple_match(self):
        # Both self-harm and suicide phrasing present - the more severe category wins.
        result = check_input("I want to hurt myself and honestly I want to die")
        assert result == "suicide"


class TestInputDetectionDoesNotFalsePositiveOnOrdinaryChat:
    def test_ordinary_message_returns_none(self):
        assert check_input("Hey, how was your day?") is None

    def test_persona_backstory_style_text_without_crisis_phrasing(self):
        assert check_input("My dad was pretty tough on me growing up.") is None

    def test_empty_and_none_input(self):
        assert check_input("") is None
        assert check_input(None) is None

    def test_word_kill_alone_does_not_trigger(self):
        # "kill" appears in lots of harmless phrasing - only full crisis phrases should match.
        assert check_input("that movie killed it, so good") is None


class TestOutputReviewIsNarrow:
    """
    The critical distinction: legitimate in-character distress (a persona
    portraying hopelessness or suicidal ideation as a clinical symptom, per
    PersonaSymptom/ClinicalPatternHypothesis elsewhere in this app) must
    NEVER be blocked. Only specific means/method content should be.
    """

    def test_ordinary_sad_in_character_response_not_flagged(self):
        assert check_output("I don't know, things have been really hard lately. I feel kind of empty.") is False

    def test_portrayed_suicidal_ideation_as_symptom_not_flagged(self):
        # This is exactly the kind of clinically-realistic content the app
        # is supposed to be able to portray - it must not be censored.
        assert check_output("Sometimes I think about not being here anymore, like what's the point.") is False

    def test_method_content_is_flagged(self):
        assert check_output("Here's how you could do it: take a lethal dose of...") is True

    def test_empty_output(self):
        assert check_output("") is False
        assert check_output(None) is False


class TestCrisisResponseMessages:
    def test_every_category_has_a_response(self):
        for category in CRISIS_CATEGORIES:
            message = build_crisis_response(category)
            assert isinstance(message, str)
            assert len(message) > 20

    def test_unknown_category_falls_back_to_suicide_message(self):
        assert build_crisis_response("not_a_real_category") == build_crisis_response("suicide")

    def test_suicide_response_includes_988(self):
        assert "988" in build_crisis_response("suicide")

    def test_responses_frame_platform_pausing_not_persona_speaking(self):
        # The persona must never appear to say this - it's the platform interrupting.
        for category in CRISIS_CATEGORIES:
            assert "this app" in build_crisis_response(category).lower()

    def test_output_safety_note_is_nonempty(self):
        assert len(build_output_safety_note()) > 10
