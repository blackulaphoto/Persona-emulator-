"""
Tests for app/utils/foundational_baseline.py after the step-6 baseline
redesign (see docs/MIGRATION_MAP.md).

Unlike the other engines built in this rebuild, this module is already
wired into the live POST /api/v1/personas route (app/api/routes/personas.py)
via derive_foundational_baseline_async, so these tests cover an actual
behavior change, not just new dormant code. The core invariant: a flat AI
response must be returned as-is, never force-nudged toward more spread.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.utils.foundational_baseline import (
    analyze_baseline_personality_ai,
    derive_foundational_baseline_async,
    derive_foundational_baseline,
    infer_foundational_signals,
    _calculate_trait_deltas,
    clamp_personality_range,
    TRAIT_MIN,
    TRAIT_MAX,
)
from app.utils import foundational_baseline


FLAT_RESPONSE = {
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
    "reasoning": "The described environment is genuinely ambiguous and doesn't push in any direction.",
}


class TestNudgeRemoved:
    """The core fix: a flat AI response is returned unchanged, not nudged."""

    def test_no_longer_has_flat_profile_helpers(self):
        import app.utils.foundational_baseline as module
        assert not hasattr(module, "_is_flat_profile")
        assert not hasattr(module, "_apply_signal_nudge")

    def test_baseline_uses_stable_current_analysis_model(self):
        assert foundational_baseline.openai_service.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_flat_ai_response_returned_exactly_unchanged(self):
        with patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = FLAT_RESPONSE
            result = await analyze_baseline_personality_ai("A fairly ordinary, mixed childhood.", 10, "female")

        assert result == {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        }

    @pytest.mark.asyncio
    async def test_prompt_no_longer_forces_deviation(self):
        with patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = FLAT_RESPONSE
            await analyze_baseline_personality_ai("text", 10, "female")
            prompt_used = mock_analyze.call_args.kwargs["prompt"]

        assert "at least two traits should deviate" not in prompt_used
        assert "legitimate answer" in prompt_used or "legitimate result" in prompt_used


class TestPlausibilityClamp:
    """The clamp still exists, but only as a degenerate-extreme guard, and is wider than before."""

    @pytest.mark.asyncio
    async def test_extreme_ai_values_clamped_to_new_bounds(self):
        extreme_response = {
            "openness": 0.99, "conscientiousness": 0.01, "extraversion": 0.5,
            "agreeableness": 0.99, "neuroticism": 0.01, "reasoning": "...",
        }
        with patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = extreme_response
            result = await analyze_baseline_personality_ai("text", 10, "female")

        assert result["openness"] == TRAIT_MAX / 100.0
        assert result["conscientiousness"] == TRAIT_MIN / 100.0

    def test_bounds_are_wider_than_the_old_20_80(self):
        # The old bound (20-80) was documented as tuned for "more variation."
        # The new one exists only to block literal 0/1 extremes.
        assert TRAIT_MIN < 20
        assert TRAIT_MAX > 80

    def test_clamp_personality_range_uses_current_bounds(self):
        result = clamp_personality_range({"openness": 0.99, "neuroticism": 0.01})
        assert result["openness"] == TRAIT_MAX / 100.0
        assert result["neuroticism"] == TRAIT_MIN / 100.0


class TestFallbackPathUnaffected:
    """The keyword fallback (used only if the AI call fails) never used the nudge mechanism - confirm it still works standalone."""

    def test_signals_inferred_from_adverse_text(self):
        signals = infer_foundational_signals("The home was chaotic and abusive, with frequent violence.")
        assert signals["stability"] < 0
        assert signals["emotionalSafety"] < 0
        assert signals["adversityIntensity"] > 0

    def test_signals_flat_for_neutral_text(self):
        signals = infer_foundational_signals("They lived in a house and went to school.")
        assert all(v == 0 for v in signals.values())

    def test_deltas_bounded_within_plausibility_range(self):
        signals = infer_foundational_signals(
            "Severe chronic violence, abuse, neglect, instability, danger, terrifying, relentless."
        )
        deltas = _calculate_trait_deltas(signals)
        # Even worst-case deltas must stay within the module's own clamp bounds
        # once added to BASELINE_SCORE=50.
        for trait, delta in deltas.items():
            score = 50 + delta
            assert TRAIT_MIN <= score <= TRAIT_MAX or abs(delta) <= 24  # deltas self-clamp before this bound applies

    @pytest.mark.asyncio
    async def test_derive_async_falls_back_cleanly_on_ai_failure(self):
        with patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            baseline, signals = await derive_foundational_baseline_async(
                "A chaotic and neglectful household.", baseline_age=8, gender="male"
            )

        assert set(baseline.keys()) == {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
        for value in baseline.values():
            assert (TRAIT_MIN / 100.0) <= value <= (TRAIT_MAX / 100.0)

    def test_derive_sync_falls_back_cleanly_on_ai_failure(self):
        with patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            baseline, signals = derive_foundational_baseline(
                "A chaotic and neglectful household.", baseline_age=8, gender="male"
            )

        assert set(baseline.keys()) == {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
