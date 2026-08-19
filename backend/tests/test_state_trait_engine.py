"""
Tests for Step 11b of docs/MIGRATION_MAP.md: state_trait_engine.py, in
isolation - AI proposal path, heuristic fallback, and the deterministic
bounded apply functions. Not wired into any route yet (see
test_developmental_pipeline_state_trait.py for the Step 11c wiring tests).

Also covers Step 11e's intervention-specific extension (intervention_trait_
gate_open and the propose_intervention_state_trait_implications_* quad) - see
test_interventions_route_wiring.py for that step's route-level wiring tests.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.services.state_trait_engine import (
    propose_state_trait_implications_ai,
    propose_state_trait_implications_async,
    propose_state_trait_implications,
    propose_state_trait_implications_heuristic,
    apply_state_update,
    apply_trait_update,
    trait_gate_open,
    ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS,
    STATE_STEP,
    TRAIT_STEP,
    intervention_trait_gate_open,
    propose_intervention_state_trait_implications_ai,
    propose_intervention_state_trait_implications_async,
    propose_intervention_state_trait_implications,
    propose_intervention_state_trait_implications_heuristic,
    INTERVENTION_IMPROVEMENT_THRESHOLD,
    INTERVENTION_SUSTAINED_COUNT,
)
from app.schemas.developmental_analysis_schemas import STATE_VARIABLES, TRAIT_NAMES


INTERPRETATION = {
    "belief_statement": "People leave.",
    "adaptation_strategy": "hypervigilance",
    "reasoning": "Repeated caregiver absence.",
}


class TestHeuristicFallback:
    def test_known_strategy_returns_state_changes(self):
        result = propose_state_trait_implications_heuristic(INTERPRETATION, pattern_status="emerging")
        assert "threat_sensitivity" in result["state_changes"]

    def test_trait_changes_empty_unless_established(self):
        result = propose_state_trait_implications_heuristic(INTERPRETATION, pattern_status="emerging")
        assert result["trait_changes"] == {}

    def test_trait_changes_populated_when_established(self):
        result = propose_state_trait_implications_heuristic(INTERPRETATION, pattern_status="established")
        assert "neuroticism" in result["trait_changes"]
        assert result["trait_changes"]["neuroticism"]["evidence_strength"] == "low"

    def test_strategy_with_no_trait_mapping_stays_empty_even_when_established(self):
        interp = dict(INTERPRETATION, adaptation_strategy="humor")
        result = propose_state_trait_implications_heuristic(interp, pattern_status="established")
        assert result["trait_changes"] == {}

    def test_unknown_or_missing_strategy_returns_empty(self):
        assert propose_state_trait_implications_heuristic({"adaptation_strategy": None}) == {"state_changes": {}, "trait_changes": {}}
        assert propose_state_trait_implications_heuristic({}) == {"state_changes": {}, "trait_changes": {}}

    def test_every_mapped_strategy_only_uses_controlled_vocab_keys(self):
        for strategy, default in ADAPTATION_STRATEGY_STATE_TRAIT_DEFAULTS.items():
            for var in default.get("state", {}):
                assert var in STATE_VARIABLES, f"{strategy} state key {var} not in STATE_VARIABLES"
            for trait in default.get("trait", {}):
                assert trait in TRAIT_NAMES, f"{strategy} trait key {trait} not in TRAIT_NAMES"


class TestAIProposalPath:
    @pytest.mark.asyncio
    async def test_valid_ai_response_used(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state_changes": {"trust": {"direction": "decrease", "magnitude": "high"}},
                "trait_changes": {},
            }
            result = await propose_state_trait_implications_ai("Michael", 14, INTERPRETATION, "emerging")
        assert result["state_changes"]["trust"]["direction"] == "decrease"

    @pytest.mark.asyncio
    async def test_invalid_state_key_falls_back_to_none(self):
        # AI hallucinating a key outside STATE_VARIABLES must not silently pass through.
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state_changes": {"extraversion": {"direction": "decrease", "magnitude": "high"}},
                "trait_changes": {},
            }
            result = await propose_state_trait_implications_ai("Michael", 14, INTERPRETATION, "emerging")
        assert result is None

    @pytest.mark.asyncio
    async def test_ai_exception_returns_none(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            result = await propose_state_trait_implications_ai("Michael", 14, INTERPRETATION, "emerging")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_wrapper_falls_back_on_failure(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            result = await propose_state_trait_implications_async("Michael", 14, INTERPRETATION, "established")
        # Falls back to heuristic, which DOES propose a trait change once established.
        assert "neuroticism" in result["trait_changes"]

    @pytest.mark.asyncio
    async def test_no_adaptation_strategy_short_circuits_without_calling_ai(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            result = await propose_state_trait_implications_ai("Michael", 14, {"adaptation_strategy": None}, "established")
        mock_analyze.assert_not_called()
        assert result == {"state_changes": {}, "trait_changes": {}}


class TestSyncWrapperDegradesInAsyncContext:
    @pytest.mark.asyncio
    async def test_called_inside_running_loop_uses_heuristic(self):
        # propose_state_trait_implications is the sync wrapper; calling it from
        # within an already-running event loop must not attempt asyncio.run().
        loop = asyncio.get_running_loop()
        assert loop.is_running()
        result = propose_state_trait_implications("Michael", 14, INTERPRETATION, "established")
        assert "neuroticism" in result["trait_changes"]


class TestApplyStateUpdate:
    def test_unobserved_variable_starts_from_neutral_baseline(self):
        updated = apply_state_update({}, {"trust": {"direction": "decrease", "magnitude": "mild"}})
        assert updated["trust"] == round(0.5 - STATE_STEP["mild"], 4)

    def test_moves_by_correct_step_size_per_magnitude(self):
        for magnitude in ("mild", "moderate", "high"):
            updated = apply_state_update({"mood": 0.5}, {"mood": {"direction": "increase", "magnitude": magnitude}})
            assert updated["mood"] == round(0.5 + STATE_STEP[magnitude], 4)

    def test_clamps_at_upper_bound(self):
        updated = apply_state_update({"trust": 0.95}, {"trust": {"direction": "increase", "magnitude": "high"}})
        assert updated["trust"] == 1.0

    def test_clamps_at_lower_bound(self):
        updated = apply_state_update({"trust": 0.05}, {"trust": {"direction": "decrease", "magnitude": "high"}})
        assert updated["trust"] == 0.0

    def test_unknown_variable_key_ignored(self):
        updated = apply_state_update({}, {"not_a_real_variable": {"direction": "increase", "magnitude": "mild"}})
        assert updated == {}

    def test_existing_unrelated_variables_untouched(self):
        updated = apply_state_update({"trust": 0.7, "mood": 0.4}, {"trust": {"direction": "decrease", "magnitude": "mild"}})
        assert updated["mood"] == 0.4

    def test_returns_new_dict_not_mutated_input(self):
        original = {"trust": 0.7}
        updated = apply_state_update(original, {"trust": {"direction": "decrease", "magnitude": "mild"}})
        assert original["trust"] == 0.7
        assert updated is not original


class TestTraitGateOpen:
    def test_open_only_when_established(self):
        assert trait_gate_open({"status": "established"}) is True

    def test_closed_for_emerging(self):
        assert trait_gate_open({"status": "emerging"}) is False

    def test_closed_for_weakening_and_resolved(self):
        assert trait_gate_open({"status": "weakening"}) is False
        assert trait_gate_open({"status": "resolved"}) is False

    def test_closed_for_none(self):
        assert trait_gate_open(None) is False


class TestApplyTraitUpdate:
    def test_gate_closed_returns_unchanged_regardless_of_trait_changes(self):
        current = {"neuroticism": 0.5}
        updated = apply_trait_update(current, {"neuroticism": {"direction": "increase", "magnitude": "high"}}, gate_open=False)
        assert updated == {"neuroticism": 0.5}

    def test_gate_open_applies_bounded_step(self):
        current = {"neuroticism": 0.5}
        updated = apply_trait_update(current, {"neuroticism": {"direction": "increase", "magnitude": "moderate"}}, gate_open=True)
        assert updated["neuroticism"] == round(0.5 + TRAIT_STEP["moderate"], 4)

    def test_trait_step_is_smaller_than_state_step_for_same_magnitude(self):
        # The literal "no videogame-stat psychology" requirement: Trait must
        # move less per event than State does, at every magnitude tier.
        for magnitude in ("mild", "moderate", "high"):
            assert TRAIT_STEP[magnitude] < STATE_STEP[magnitude]

    def test_unknown_trait_key_ignored(self):
        updated = apply_trait_update({}, {"not_a_real_trait": {"direction": "increase", "magnitude": "mild"}}, gate_open=True)
        assert updated == {}

    def test_a_single_established_pattern_reinforcement_never_maxes_out_a_trait(self):
        # One gated application from a neutral baseline should stay far from
        # the extremes - trait movement is supposed to be modest per event.
        updated = apply_trait_update({"neuroticism": 0.5}, {"neuroticism": {"direction": "increase", "magnitude": "high"}}, gate_open=True)
        assert 0.5 < updated["neuroticism"] < 0.65


# ============================================================
# Step 11e: intervention-specific gate and proposal quad
# ============================================================

ESTABLISHED_AVOIDANCE = {"status": "established", "adaptation_strategy": "avoidance", "evidence_strength": 0.6}
EMERGING_AVOIDANCE = {"status": "emerging", "adaptation_strategy": "avoidance", "evidence_strength": 0.2}


class TestInterventionTraitGateOpen:
    def test_closed_when_pattern_not_established(self):
        assert intervention_trait_gate_open(EMERGING_AVOIDANCE, [], 0.9) is False

    def test_closed_when_pattern_none(self):
        assert intervention_trait_gate_open(None, [0.9, 0.9], 0.9) is False

    def test_closed_on_first_documented_improvement_even_if_established(self):
        # One good round is a data point, not "sustained" - the literal
        # point of this gate per the Step 11e design.
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [], 0.9) is False

    def test_open_on_second_documented_improvement(self):
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [0.8], 0.9) is True

    def test_prior_efficacy_below_threshold_does_not_count(self):
        # A prior intervention that didn't actually show improvement
        # shouldn't count toward "sustained" just because it happened.
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [0.2], 0.9) is False

    def test_this_call_below_threshold_does_not_count_even_with_prior_success(self):
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [0.9], 0.3) is False

    def test_none_efficacy_values_are_ignored_not_crash(self):
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [None, None], None) is False

    def test_exactly_at_threshold_counts(self):
        assert intervention_trait_gate_open(ESTABLISHED_AVOIDANCE, [INTERVENTION_IMPROVEMENT_THRESHOLD], INTERVENTION_IMPROVEMENT_THRESHOLD) is True

    def test_sustained_count_constant_is_two(self):
        # Documents the current bar explicitly, so a change to this constant
        # is a deliberate, visible diff rather than a silent behavior shift.
        assert INTERVENTION_SUSTAINED_COUNT == 2


class TestInterventionHeuristicFallback:
    def test_no_targeted_strategy_returns_empty(self):
        result = propose_intervention_state_trait_implications_heuristic(None, 0.9, True)
        assert result == {"state_changes": {}, "trait_changes": {}}

    def test_unmapped_strategy_returns_empty(self):
        result = propose_intervention_state_trait_implications_heuristic("humor", 0.9, True)
        # humor has a state entry but no trait entry - trait_changes should
        # still be empty even though trait_eligible=True and state non-empty.
        assert result["trait_changes"] == {}
        assert result["state_changes"] != {}

    def test_state_direction_is_inverse_of_the_original_adaptation_default(self):
        # avoidance's own default increases "avoidance" state - therapy
        # targeting it should propose the opposite direction.
        result = propose_intervention_state_trait_implications_heuristic("avoidance", 0.9, False)
        assert result["state_changes"]["avoidance"]["direction"] == "decrease"

    def test_trait_direction_is_inverse_when_eligible(self):
        # avoidance's own default decreases extraversion - therapy should
        # propose increasing it, once eligible.
        result = propose_intervention_state_trait_implications_heuristic("avoidance", 0.9, True)
        assert result["trait_changes"]["extraversion"]["direction"] == "increase"
        assert result["trait_changes"]["extraversion"]["evidence_strength"] == "low"

    def test_trait_changes_empty_when_not_eligible_even_for_a_mapped_strategy(self):
        result = propose_intervention_state_trait_implications_heuristic("avoidance", 0.9, False)
        assert result["trait_changes"] == {}

    def test_magnitude_scales_with_efficacy_match(self):
        low = propose_intervention_state_trait_implications_heuristic("avoidance", 0.2, False)
        high = propose_intervention_state_trait_implications_heuristic("avoidance", 0.9, False)
        assert low["state_changes"]["avoidance"]["magnitude"] == "mild"
        assert high["state_changes"]["avoidance"]["magnitude"] == "high"

    def test_none_efficacy_defaults_to_mild_magnitude(self):
        result = propose_intervention_state_trait_implications_heuristic("avoidance", None, False)
        assert result["state_changes"]["avoidance"]["magnitude"] == "mild"


class TestInterventionAIProposalPath:
    @pytest.mark.asyncio
    async def test_no_targeted_strategy_short_circuits_without_calling_ai(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            result = await propose_intervention_state_trait_implications_ai("Michael", 30, "DBT", None, 0.9, True)
        mock_analyze.assert_not_called()
        assert result == {"state_changes": {}, "trait_changes": {}}

    @pytest.mark.asyncio
    async def test_valid_ai_response_used(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state_changes": {"regulation": {"direction": "increase", "magnitude": "moderate"}},
                "trait_changes": {},
            }
            result = await propose_intervention_state_trait_implications_ai("Michael", 30, "DBT", "avoidance", 0.9, True)
        assert result["state_changes"]["regulation"]["direction"] == "increase"

    @pytest.mark.asyncio
    async def test_invalid_state_key_falls_back_to_none(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "state_changes": {"conscientiousness": {"direction": "increase", "magnitude": "high"}},
                "trait_changes": {},
            }
            result = await propose_intervention_state_trait_implications_ai("Michael", 30, "DBT", "avoidance", 0.9, True)
        assert result is None

    @pytest.mark.asyncio
    async def test_ai_exception_returns_none(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            result = await propose_intervention_state_trait_implications_ai("Michael", 30, "DBT", "avoidance", 0.9, True)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_wrapper_falls_back_on_failure(self):
        with patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.side_effect = Exception("simulated API failure")
            result = await propose_intervention_state_trait_implications_async("Michael", 30, "DBT", "avoidance", 0.9, True)
        # Falls back to heuristic, which DOES propose a trait change once eligible.
        assert "extraversion" in result["trait_changes"]


class TestInterventionSyncWrapperDegradesInAsyncContext:
    @pytest.mark.asyncio
    async def test_called_inside_running_loop_uses_heuristic(self):
        loop = asyncio.get_running_loop()
        assert loop.is_running()
        result = propose_intervention_state_trait_implications("Michael", 30, "DBT", "avoidance", 0.9, True)
        assert "extraversion" in result["trait_changes"]
