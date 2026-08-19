"""
Tests for the Self-Narration Engine (app/services/self_narration_engine.py).

The critical invariant here is the operator/subject/source boundary from
docs/MIGRATION_MAP.md: nothing this module produces may address "the user"
or "you" - every finding attaches to the persona by name. That's enforced in
code (_enforce_subject_attribution, build_narration_record), not just
prompted, and is tested directly below without needing a network call.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.self_narration_engine import (
    analyze_narration_heuristic,
    analyze_narration_ai,
    analyze_narration_async,
    analyze_narration,
    is_self_narration_eligible,
    _validate_and_filter,
    _enforce_subject_attribution,
    build_narration_record,
    SIGNAL_TYPES,
    SPEAKER_ROLES,
)


class TestSubjectAttributionGuard:
    """The hard rule: findings attach to the persona, never to the operator."""

    def test_rejects_you_are_phrasing(self):
        assert _enforce_subject_attribution("You are minimizing your father's abuse.") is None

    def test_rejects_the_user_phrasing(self):
        assert _enforce_subject_attribution("The user appears to be minimizing this.") is None

    def test_allows_persona_named_phrasing(self):
        text = "Michael's account minimizes the violence he describes."
        assert _enforce_subject_attribution(text) == text

    def test_allows_empty_text(self):
        assert _enforce_subject_attribution("") == ""
        assert _enforce_subject_attribution(None) is None


class TestValidateAndFilter:
    def test_drops_hallucinated_signal_type(self):
        raw = {
            "linguistic_signals": [
                {"signal_type": "minimization", "evidence_text": "it was normal", "note": "downplays severity"},
                {"signal_type": "made_up_signal_xyz", "evidence_text": "nonsense", "note": "n/a"},
            ],
            "candidate_hypotheses": [],
        }
        result = _validate_and_filter(raw)
        types = {s["signal_type"] for s in result["linguistic_signals"]}
        assert types == {"minimization"}

    def test_drops_signal_note_that_violates_attribution(self):
        raw = {
            "linguistic_signals": [
                {"signal_type": "self_blame", "evidence_text": "my fault", "note": "You are blaming yourself here."},
            ],
            "candidate_hypotheses": [],
        }
        result = _validate_and_filter(raw)
        assert result["linguistic_signals"] == []

    def test_drops_hypothesis_that_violates_attribution(self):
        raw = {
            "linguistic_signals": [],
            "candidate_hypotheses": [
                {
                    "hypothesis": "You are protecting your father's image.",
                    "likely_function": "Keeps things comfortable.",
                    "potential_later_cost": "Harder to see harm later.",
                    "supporting_signals": ["normalization"],
                },
            ],
        }
        result = _validate_and_filter(raw)
        assert result["candidate_hypotheses"] == []

    def test_keeps_well_formed_persona_named_hypothesis(self):
        raw = {
            "linguistic_signals": [],
            "candidate_hypotheses": [
                {
                    "hypothesis": "Michael's account may function as a protective narrative.",
                    "likely_function": "Lets Michael keep a positive view of his father.",
                    "potential_later_cost": "May obscure similar harm later.",
                    "supporting_signals": ["normalization", "not_a_real_signal"],
                },
            ],
        }
        result = _validate_and_filter(raw)
        assert len(result["candidate_hypotheses"]) == 1
        assert result["candidate_hypotheses"][0]["supporting_signals"] == ["normalization"]

    def test_empty_response(self):
        assert _validate_and_filter({}) == {"linguistic_signals": [], "candidate_hypotheses": []}
        assert _validate_and_filter(None) == {"linguistic_signals": [], "candidate_hypotheses": []}


class TestHeuristicFallback:
    def test_detects_absolutist_language(self):
        result = analyze_narration_heuristic("Nobody ever helped me, everyone always let me down.")
        types = {s["signal_type"] for s in result["linguistic_signals"]}
        assert "absolutist_language" in types

    def test_detects_self_blame(self):
        result = analyze_narration_heuristic("It was my fault he left.")
        types = {s["signal_type"] for s in result["linguistic_signals"]}
        assert "self_blame" in types

    def test_detects_rapid_closure_minimization(self):
        result = analyze_narration_heuristic("He hit me sometimes but I'm fine.")
        types = {s["signal_type"] for s in result["linguistic_signals"]}
        assert "minimization" in types

    def test_produces_no_hypotheses(self):
        # The fallback path deliberately does not attempt interpretive hypotheses.
        result = analyze_narration_heuristic("He hit me sometimes but I'm fine, nobody ever noticed.")
        assert result["candidate_hypotheses"] == []

    def test_neutral_text_produces_no_signals(self):
        result = analyze_narration_heuristic("We went to the park on Saturday and had lunch.")
        assert result["linguistic_signals"] == []


class TestBuildNarrationRecord:
    def test_persona_voice_sets_attributed_true(self):
        record = build_narration_record(
            subject_id="persona-1",
            text="My dad beat me sometimes but it was normal.",
            speaker_role="persona_voice",
            analysis={"linguistic_signals": [], "candidate_hypotheses": []},
        )
        assert record.subject_id == "persona-1"
        assert record.speaker_role == "persona_voice"
        assert record.attributed_to_persona is True

    def test_case_author_sets_attributed_false(self):
        record = build_narration_record(
            subject_id="persona-1",
            text="Michael's father was physically violent throughout his childhood.",
            speaker_role="case_author",
            analysis={"linguistic_signals": [], "candidate_hypotheses": []},
        )
        assert record.attributed_to_persona is False

    def test_third_party_report_sets_attributed_false(self):
        record = build_narration_record(
            subject_id="persona-1",
            text="His mother reports he was always withdrawn.",
            speaker_role="third_party_report",
            analysis={"linguistic_signals": [], "candidate_hypotheses": []},
        )
        assert record.attributed_to_persona is False

    def test_rejects_unknown_speaker_role(self):
        with pytest.raises(ValueError):
            build_narration_record(
                subject_id="persona-1",
                text="...",
                speaker_role="omniscient_narrator",
                analysis={"linguistic_signals": [], "candidate_hypotheses": []},
            )


class TestConditionalGate:
    """
    The core correction: self-narration is not a mandatory stage applied to
    everything typed about a persona. "Timmy was abused at 17" is a case
    fact, written by whoever is authoring the case - it says nothing about
    Timmy's own beliefs, defenses, or narrative identity, and must never be
    analyzed as if it were his self-report.
    """

    def test_is_eligible_only_for_persona_voice(self):
        assert is_self_narration_eligible("persona_voice") is True
        assert is_self_narration_eligible("case_author") is False
        assert is_self_narration_eligible("third_party_report") is False
        assert is_self_narration_eligible("source_material") is False

    def test_is_eligible_raises_on_unknown_role(self):
        with pytest.raises(ValueError):
            is_self_narration_eligible("omniscient_narrator")

    @pytest.mark.asyncio
    async def test_case_author_text_never_reaches_the_ai(self):
        with patch("app.services.self_narration_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            result = await analyze_narration_ai(
                "Timmy was abused at 17.", persona_name="Timmy", speaker_role="case_author"
            )
            mock_analyze.assert_not_called()
            assert result["linguistic_signals"] == []
            assert result["candidate_hypotheses"] == []
            assert "skipped_reason" in result

    @pytest.mark.asyncio
    async def test_case_author_text_never_reaches_ai_via_orchestrator(self):
        with patch("app.services.self_narration_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            result = await analyze_narration_async(
                "Timmy was abused at 17.", persona_name="Timmy", speaker_role="case_author"
            )
            mock_analyze.assert_not_called()
            assert result["linguistic_signals"] == []

    def test_sync_wrapper_gates_before_any_processing(self):
        # No mocking needed - if this reached the AI or heuristic path it
        # would either hang on a real network call or return heuristic
        # signals; a correctly gated call returns instantly with none.
        result = analyze_narration("Timmy was abused at 17.", persona_name="Timmy", speaker_role="case_author")
        assert result["linguistic_signals"] == []
        assert result["candidate_hypotheses"] == []
        assert result["skipped_reason"]

    def test_terse_case_fact_produces_no_spurious_signals_even_via_heuristic_directly(self):
        # Confirms the underlying failure mode is real: calling the raw
        # heuristic on case-author prose WOULD have produced a signal here
        # (absolutist-language false positive on none, but demonstrates the
        # heuristic itself has no awareness of provenance - the gate has to
        # live above it, which is exactly what this module now does).
        raw = analyze_narration_heuristic("Timmy was never given an explanation and nobody checked on him.")
        assert len(raw["linguistic_signals"]) > 0  # the heuristic alone WOULD flag this
        # ...which is exactly why analyze_narration/analyze_narration_async must gate first:
        gated = analyze_narration("Timmy was never given an explanation and nobody checked on him.", "Timmy", "case_author")
        assert gated["linguistic_signals"] == []

    def test_third_party_report_also_gated(self):
        result = analyze_narration(
            "His mother reports he became withdrawn after the incident.",
            persona_name="Timmy",
            speaker_role="third_party_report",
        )
        assert result["linguistic_signals"] == []
        assert result["candidate_hypotheses"] == []

    def test_persona_voice_still_reaches_heuristic_fallback(self):
        # The gate must not accidentally block the legitimate case. Mocks
        # the AI call to fail fast rather than hitting the live API and
        # sitting through its real exponential-backoff retries.
        with patch("app.services.self_narration_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            result = analyze_narration(
                "It wasn't really abuse. My dad just lost his temper sometimes.",
                persona_name="Timmy",
                speaker_role="persona_voice",
            )
        assert "skipped_reason" not in result


class TestTaxonomyIntegrity:
    def test_signal_types_nonempty_and_unique(self):
        assert len(SIGNAL_TYPES) == len(set(SIGNAL_TYPES))
        assert len(SIGNAL_TYPES) > 0

    def test_speaker_roles_match_model(self):
        from app.models.narration import SPEAKER_ROLES as MODEL_SPEAKER_ROLES
        assert set(SPEAKER_ROLES) == set(MODEL_SPEAKER_ROLES)
