"""
Tests for the Pattern/Adaptation Engine (app/services/pattern_engine.py).

Key invariants:
  - Age changes WHICH domains are implicated, not a scalar multiplier
    (salient_domains_for_age uses real app/utils/developmental_stages.py
    content, not a duplicated table).
  - A single interpretation opens a pattern candidate as "emerging" with
    evidence_strength None - recurrence is what makes something a pattern,
    mirroring evidence_accumulator's "opening is not believing" invariant.
  - "established" requires crossing the strength threshold, not merely being
    reinforced more than once.
  - Protective factors change a reinforcement's effect (weakened vs.
    strengthened), not just a severity discount.
  - The subject-attribution guard (from self_narration_engine) applies here
    too, since interpretation prose is a second place this could slip.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.pattern_engine import (
    salient_domains_for_age,
    interpret_experience_heuristic,
    interpret_experience_async,
    interpret_reparative_experience_heuristic,
    _validate_interpretation,
    _validate_reparative_interpretation,
    _build_interpretation_prompt,
    _build_reparative_prompt,
    accumulate_patterns,
    build_verdict,
    name_pattern_heuristic,
    ADAPTATION_STRATEGIES,
    EXPOSURE_INTERPRETATION_DEFAULTS,
    STAGE_TASK_TO_DOMAIN,
    ESTABLISHED_THRESHOLD,
)
from app.services.evidence_accumulator import evidence_strength_label


class TestSalientDomainsForAge:
    def test_early_childhood_narrows_to_stage_relevant_domains(self):
        # early_childhood key_tasks map to attachment_security, emotional_regulation, emotional_safety
        result = salient_domains_for_age(3, ["attachment_security", "competence", "sexuality"])
        assert result == ["attachment_security"]

    def test_no_intersection_falls_back_to_exposure_domains(self):
        # "sexuality" isn't a live task at early_childhood ages, and nothing else matches either
        result = salient_domains_for_age(3, ["sexuality"])
        assert result == ["sexuality"]

    def test_none_age_returns_domains_unchanged(self):
        domains = ["attachment_security", "stability"]
        assert salient_domains_for_age(None, domains) == domains

    def test_adolescence_surfaces_autonomy_and_identity(self):
        result = salient_domains_for_age(15, ["autonomy", "identity", "attachment_security"])
        assert "autonomy" in result
        assert "identity" in result


class TestHeuristicInterpretation:
    def test_known_exposure_type_returns_default(self):
        exposures = [{"exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security", "stability"]}]
        result = interpret_experience_heuristic(age=6, exposures=exposures)
        assert result["belief_statement"] == "People leave."
        assert result["adaptation_strategy"] == "self_reliance"

    def test_no_exposures_returns_nulls(self):
        result = interpret_experience_heuristic(age=6, exposures=[])
        assert result["belief_statement"] is None
        assert result["adaptation_strategy"] is None

    def test_domains_narrowed_by_age(self):
        exposures = [{"exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security", "stability"]}]
        result = interpret_experience_heuristic(age=3, exposures=exposures)
        assert result["developmental_domains"] == ["attachment_security"]


class TestValidateInterpretation:
    def test_rejects_unknown_adaptation_strategy(self):
        assert _validate_interpretation({
            "belief_statement": "People leave.",
            "adaptation_strategy": "made_up_strategy",
            "reasoning": "...",
        }) is None

    def test_rejects_attribution_violation_in_belief(self):
        assert _validate_interpretation({
            "belief_statement": "You believe people leave.",
            "adaptation_strategy": "self_reliance",
            "reasoning": "...",
        }) is None

    def test_accepts_well_formed_response(self):
        result = _validate_interpretation({
            "belief_statement": "Michael believes people leave.",
            "adaptation_strategy": "self_reliance",
            "reasoning": "Repeated caregiver absence.",
        })
        assert result["adaptation_strategy"] == "self_reliance"

    def test_empty_response(self):
        assert _validate_interpretation(None) is None
        assert _validate_interpretation({}) is None


def _interp(id_, age, strategy, belief="People leave.", domains=None):
    return {
        "id": id_,
        "source_event_id": f"exp-{id_}",
        "age_at_event": age,
        "adaptation_strategy": strategy,
        "belief_statement": belief,
        "developmental_domains": domains or ["attachment_security"],
    }


class TestAccumulatePatternsOpeningInvariant:
    """Mirrors evidence_accumulator's core rule: one instance opens a candidate, doesn't establish it."""

    def test_single_interpretation_is_emerging_with_null_strength(self):
        result = accumulate_patterns([_interp("i1", 6, "self_reliance")])
        pattern = result["self_reliance"]
        assert pattern["status"] == "emerging"
        assert pattern["evidence_strength"] is None
        assert pattern["reinforcement_history"] == [{
            "interpretation_id": "i1", "experience_id": "exp-i1", "age": 6, "effect": "originated",
        }]

    def test_no_interpretations_produces_no_patterns(self):
        assert accumulate_patterns([]) == {}

    def test_interpretations_without_strategy_are_ignored(self):
        assert accumulate_patterns([{"id": "i1", "adaptation_strategy": None, "age_at_event": 5}]) == {}


class TestAccumulatePatternsReinforcement:
    def test_two_weak_reinforcements_stay_emerging_not_established(self):
        # REINFORCE_INCREMENT is 0.2, ESTABLISHED_THRESHOLD is 0.5 - two
        # reinforcements alone (0.2) must not cross into "established".
        interpretations = [_interp("i1", 5, "hypervigilance"), _interp("i2", 9, "hypervigilance")]
        result = accumulate_patterns(interpretations)
        pattern = result["hypervigilance"]
        assert pattern["evidence_strength"] < ESTABLISHED_THRESHOLD
        assert pattern["status"] == "emerging"
        assert pattern["reinforcement_history"][1]["effect"] == "strengthened"

    def test_enough_reinforcement_crosses_into_established(self):
        interpretations = [
            _interp("i1", 5, "hypervigilance"),
            _interp("i2", 8, "hypervigilance"),
            _interp("i3", 11, "hypervigilance"),
            _interp("i4", 14, "hypervigilance"),
        ]
        result = accumulate_patterns(interpretations)
        pattern = result["hypervigilance"]
        assert pattern["evidence_strength"] >= ESTABLISHED_THRESHOLD
        assert pattern["status"] == "established"

    def test_different_strategies_form_separate_patterns(self):
        interpretations = [_interp("i1", 5, "hypervigilance"), _interp("i2", 9, "avoidance")]
        result = accumulate_patterns(interpretations)
        assert set(result.keys()) == {"hypervigilance", "avoidance"}
        assert result["hypervigilance"]["evidence_strength"] is None
        assert result["avoidance"]["evidence_strength"] is None


class TestProtectiveFactorsWeakenReinforcement:
    def test_overlapping_protective_factor_weakens_instead_of_strengthens(self):
        interpretations = [
            _interp("i1", 4, "self_reliance", domains=["attachment_security"]),
            _interp("i2", 8, "self_reliance", domains=["attachment_security"]),
        ]
        protective = [{"factor_type": "stable_alternate_caregiver", "domains_buffered": ["attachment_security"], "active_from_age": 5}]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        pattern = result["self_reliance"]
        assert pattern["reinforcement_history"][1]["effect"] == "weakened"
        assert pattern["evidence_strength"] == 0.0
        assert pattern["status"] == "resolved"

    def test_weakening_status_when_strength_positive_but_declining(self):
        interpretations = [
            _interp("i1", 4, "self_reliance", domains=["attachment_security"]),
            _interp("i2", 7, "self_reliance", domains=["attachment_security"]),
            _interp("i3", 10, "self_reliance", domains=["attachment_security"]),
            _interp("i4", 13, "self_reliance", domains=["attachment_security"]),
        ]
        protective = [{"factor_type": "stable_alternate_caregiver", "domains_buffered": ["attachment_security"], "active_from_age": 12}]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        pattern = result["self_reliance"]
        assert pattern["reinforcement_history"][-1]["effect"] == "weakened"
        assert pattern["evidence_strength"] > 0.0
        assert pattern["status"] == "weakening"

    def test_protective_factor_before_active_from_age_does_not_apply(self):
        interpretations = [
            _interp("i1", 4, "self_reliance", domains=["attachment_security"]),
            _interp("i2", 6, "self_reliance", domains=["attachment_security"]),
        ]
        # Protective factor doesn't become active until age 10 - shouldn't buffer an event at age 6.
        protective = [{"factor_type": "stable_alternate_caregiver", "domains_buffered": ["attachment_security"], "active_from_age": 10}]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        assert result["self_reliance"]["reinforcement_history"][1]["effect"] == "strengthened"

    def test_protective_factor_sourced_from_this_patterns_own_event_does_not_buffer_it(self):
        # Real bug, confirmed against a live GPT-4-interpreted persona: a
        # "friendship" protective factor extracted FROM the very event where
        # that friendship betrayed the persona must not retroactively cancel
        # reinforcement from that event or a later one of the same pattern -
        # otherwise a pattern can perpetually buffer its own evidence, since
        # protective factors get extracted from most events (even adverse
        # ones) and domains are a small, constantly-reused vocabulary.
        interpretations = [
            _interp("i1", 10, "hypervigilance", domains=["social_belonging"]),
            _interp("i2", 14, "hypervigilance", domains=["social_belonging"]),
        ]
        # Sourced from i1's own experience (exp-i1) - must not buffer i2.
        protective = [{"factor_type": "friendship", "domains_buffered": ["social_belonging"], "active_from_age": 10, "source_event_id": "exp-i1"}]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        pattern = result["hypervigilance"]
        assert pattern["reinforcement_history"][1]["effect"] == "strengthened"
        assert pattern["evidence_strength"] == 0.2
        assert pattern["status"] == "emerging"

    def test_protective_factor_sourced_from_an_unrelated_event_still_buffers(self):
        # The exclusion is specific to THIS pattern's own supporting events -
        # a protective factor from a genuinely different, unrelated event
        # (or the baseline, source_event_id=None) still buffers normally.
        interpretations = [
            _interp("i1", 10, "hypervigilance", domains=["social_belonging"]),
            _interp("i2", 14, "hypervigilance", domains=["social_belonging"]),
        ]
        protective = [{"factor_type": "friendship", "domains_buffered": ["social_belonging"], "active_from_age": 10, "source_event_id": "some-other-experience"}]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        assert result["hypervigilance"]["reinforcement_history"][1]["effect"] == "weakened"

    def test_five_real_reinforcements_reach_established_despite_self_sourced_protective_factors(self):
        # The full Emma-shaped regression: repeated reinforcement of the
        # same strategy, each event ALSO producing its own protective factor
        # (as real GPT-4 calls did) - must still be able to reach
        # "established" once enough real, unbuffered reinforcement
        # accumulates, not get stuck at status=resolved/evidence_strength=0.0
        # forever the moment one baseline protective factor happens to
        # overlap a single early event's domain.
        interpretations = [
            _interp("i1", 10, "hypervigilance", domains=["social_belonging"]),
            _interp("i2", 12, "hypervigilance", domains=["emotional_safety", "stability"]),
            _interp("i3", 14, "hypervigilance", domains=["identity", "social_belonging"]),
            _interp("i4", 16, "hypervigilance", domains=["identity"]),
            _interp("i5", 18, "hypervigilance", domains=["identity"]),
        ]
        protective = [
            {"factor_type": "temperament", "domains_buffered": ["attachment_security", "emotional_safety"], "active_from_age": 10, "source_event_id": None},
            {"factor_type": "friendship", "domains_buffered": ["social_belonging"], "active_from_age": 10, "source_event_id": "exp-i1"},
            {"factor_type": "temperament", "domains_buffered": ["identity", "emotional_regulation"], "active_from_age": 14, "source_event_id": "exp-i3"},
        ]
        result = accumulate_patterns(interpretations, protective_factors=protective)
        pattern = result["hypervigilance"]
        # i1 originated; i2 genuinely buffered by the baseline temperament
        # factor (0.0); i3/i4/i5 unbuffered once same-group sourcing is
        # excluded (0.2, 0.4, 0.6) - crossing ESTABLISHED_THRESHOLD.
        assert pattern["status"] == "established"
        assert pattern["evidence_strength"] >= ESTABLISHED_THRESHOLD


class TestCurrentManifestationsFromObservations:
    def test_overlapping_concerning_observation_populates_manifestations(self):
        interpretations = [_interp("i1", 6, "hypervigilance", domains=["emotional_safety"])]
        observations = [{
            "valence": "concerning", "description": "becomes visibly tense when his father is mentioned",
            "developmental_domains": ["emotional_safety"],
        }]
        result = accumulate_patterns(interpretations, functional_observations=observations)
        assert "becomes visibly tense when his father is mentioned" in result["hypervigilance"]["current_manifestations"]

    def test_non_overlapping_observation_excluded(self):
        interpretations = [_interp("i1", 6, "hypervigilance", domains=["emotional_safety"])]
        observations = [{
            "valence": "concerning", "description": "struggles to hold down a job",
            "developmental_domains": ["competence"],
        }]
        result = accumulate_patterns(interpretations, functional_observations=observations)
        assert result["hypervigilance"]["current_manifestations"] == []

    def test_protective_observation_never_appears_in_manifestations(self):
        interpretations = [_interp("i1", 6, "hypervigilance", domains=["emotional_safety"])]
        observations = [{
            "valence": "protective", "description": "feels safe at home now",
            "developmental_domains": ["emotional_safety"],
        }]
        result = accumulate_patterns(interpretations, functional_observations=observations)
        assert result["hypervigilance"]["current_manifestations"] == []

    def test_no_observations_leaves_manifestations_empty(self):
        interpretations = [_interp("i1", 6, "hypervigilance")]
        result = accumulate_patterns(interpretations)
        assert result["hypervigilance"]["current_manifestations"] == []


class TestVerdictAssembly:
    def test_build_verdict_uses_shared_evidence_strength_label(self):
        interpretation = {
            "belief_statement": "People leave.",
            "reasoning": "Repeated caregiver absence.",
            "adaptation_strategy": "self_reliance",
            "developmental_domains": ["attachment_security"],
        }
        pattern_state = {
            "supporting_interpretation_ids": ["i1", "i2", "i3", "i4"],
            "status": "established",
            "evidence_strength": 0.6,
        }
        verdict = build_verdict(interpretation, pattern_state, evidence_strength_label)
        assert verdict["verdict"] == "People leave."
        assert verdict["evidence_strength"] == evidence_strength_label(0.6) == "moderate"
        assert verdict["pattern_status"] == "established"

    def test_build_verdict_with_no_pattern_state(self):
        interpretation = {"belief_statement": "X", "reasoning": "Y", "adaptation_strategy": "avoidance", "developmental_domains": []}
        verdict = build_verdict(interpretation, None, evidence_strength_label)
        assert verdict["evidence_strength"] == "no_evidence_yet"
        assert verdict["pattern_status"] == "emerging"
        assert verdict["connects_to"] == []


class TestNamingFallback:
    def test_heuristic_name_is_readable(self):
        assert name_pattern_heuristic("self_reliance") == "Self Reliance Response"


class TestTaxonomyIntegrity:
    def test_all_default_adaptations_are_valid(self):
        for exposure_type, default in EXPOSURE_INTERPRETATION_DEFAULTS.items():
            assert default["adaptation"] in ADAPTATION_STRATEGIES, f"{exposure_type} -> unknown adaptation {default['adaptation']}"

    def test_all_exposure_types_in_defaults_are_real(self):
        from app.services.developmental_exposure_engine import EXPOSURE_TAXONOMY
        missing = set(EXPOSURE_INTERPRETATION_DEFAULTS.keys()) - set(EXPOSURE_TAXONOMY.keys())
        assert not missing, f"EXPOSURE_INTERPRETATION_DEFAULTS references unknown exposure_types: {missing}"

    def test_every_exposure_type_has_a_default(self):
        # Every exposure_type the extractor can produce should have an interpretation fallback.
        from app.services.developmental_exposure_engine import EXPOSURE_TAXONOMY
        missing = set(EXPOSURE_TAXONOMY.keys()) - set(EXPOSURE_INTERPRETATION_DEFAULTS.keys())
        assert not missing, f"exposure_types with no interpretation default: {missing}"

    def test_stage_task_domains_are_real(self):
        from app.services.developmental_exposure_engine import DEVELOPMENTAL_DOMAINS
        missing = set(STAGE_TASK_TO_DOMAIN.values()) - set(DEVELOPMENTAL_DOMAINS)
        assert not missing, f"STAGE_TASK_TO_DOMAIN maps to unknown domains: {missing}"

    def test_stage_task_keys_cover_all_real_developmental_stage_tasks(self):
        from app.utils.developmental_stages import DEVELOPMENTAL_STAGES
        all_tasks = {task for stage in DEVELOPMENTAL_STAGES.values() for task in stage["key_tasks"]}
        missing = all_tasks - set(STAGE_TASK_TO_DOMAIN.keys())
        assert not missing, f"developmental_stages.py key_tasks not bridged to a domain: {missing}"


# ============================================================
# P0-2 correction: reparative-interpretation path
# (RELEASE_READINESS_2026-08-30.md)
# ============================================================
class TestReparativeInterpretationHeuristic:
    def test_known_factor_type_returns_a_real_belief_no_adaptation_strategy(self):
        result = interpret_reparative_experience_heuristic(
            [{"factor_type": "corrective_emotional_experience", "domains_buffered": ["attachment_security"]}]
        )
        assert result["belief_statement"] is not None
        assert result["adaptation_strategy"] is None
        assert result["developmental_domains"] == ["attachment_security"]

    def test_no_protective_factors_returns_nulls(self):
        result = interpret_reparative_experience_heuristic([])
        assert result["belief_statement"] is None
        assert result["adaptation_strategy"] is None


class TestValidateReparativeInterpretation:
    def test_rejects_missing_belief(self):
        assert _validate_reparative_interpretation({"reasoning": "..."}, set()) is None

    def test_rejects_attribution_violation(self):
        assert _validate_reparative_interpretation(
            {"belief_statement": "You can trust again.", "reasoning": "..."}, set()
        ) is None

    def test_accepts_well_formed_response_with_null_contradicts(self):
        result = _validate_reparative_interpretation(
            {"belief_statement": "Michael believes trust can be rebuilt.", "reasoning": "A real repair occurred.",
             "contradicts_pattern": None},
            valid_prior_strategies={"self_reliance"},
        )
        assert result["adaptation_strategy"] is None
        assert result["contradicts_pattern"] is None

    def test_contradicts_pattern_must_be_one_of_the_valid_prior_strategies(self):
        # A hallucinated/unknown strategy name is dropped, not trusted -
        # same defensive posture as _validate_interpretation's adaptation_strategy check.
        result = _validate_reparative_interpretation(
            {"belief_statement": "X", "reasoning": "Y", "contradicts_pattern": "made_up_strategy"},
            valid_prior_strategies={"self_reliance"},
        )
        assert result["contradicts_pattern"] is None

    def test_contradicts_pattern_kept_when_valid(self):
        result = _validate_reparative_interpretation(
            {"belief_statement": "X", "reasoning": "Y", "contradicts_pattern": "self_reliance"},
            valid_prior_strategies={"self_reliance"},
        )
        assert result["contradicts_pattern"] == "self_reliance"

    def test_empty_response(self):
        assert _validate_reparative_interpretation(None, set()) is None


class TestInterpretExperienceAsyncDispatch:
    """The single entry point developmental_pipeline.py calls - proves it
    routes to the right path based on what's actually present, not just on
    whether exposures happen to be empty."""

    @pytest.mark.asyncio
    async def test_exposures_present_takes_adverse_path_even_with_protective_factors_also_present(self):
        with patch("app.services.pattern_engine.openai_service.analyze", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("forces heuristic fallback")
            result = await interpret_experience_async(
                "Sam", 6,
                exposures=[{"exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security"]}],
                protective_factors_this_batch=[{"factor_type": "friendship", "domains_buffered": ["social_belonging"]}],
            )
        assert result["adaptation_strategy"] == "self_reliance"  # the adverse heuristic default, not the reparative path

    @pytest.mark.asyncio
    async def test_no_exposures_but_protective_factors_takes_reparative_path(self):
        with patch("app.services.pattern_engine.openai_service.analyze", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("forces heuristic fallback")
            result = await interpret_experience_async(
                "Sam", 9, exposures=[],
                protective_factors_this_batch=[{"factor_type": "corrective_emotional_experience", "domains_buffered": ["attachment_security"]}],
            )
        assert result["belief_statement"] is not None
        assert result["adaptation_strategy"] is None

    @pytest.mark.asyncio
    async def test_neither_exposures_nor_protective_factors_returns_null_interpretation(self):
        result = await interpret_experience_async("Sam", 10, exposures=[], protective_factors_this_batch=[])
        assert result["belief_statement"] is None
        assert result["adaptation_strategy"] is None


class TestGroundingInstructionPresent:
    """P1 correction: the generated 'reasoning' field previously described
    events that were never supplied (RELEASE_READINESS_2026-08-30.md,
    P1-1) - e.g. describing 'reliable close relationships and explicit
    reassurance' for a betrayal experience where none were given. Both
    interpretation prompts must carry an explicit, strict instruction
    forbidding that. A prompt-text assertion is a deliberately narrow,
    deterministic proxy for "the contract is asserted" - it cannot prove the
    model obeys it on every call; that's verified separately against a real
    running persona (see RELEASE_READINESS_2026-08-30.md's Reasoning
    Grounding Re-Test)."""

    def test_adverse_prompt_forbids_inventing_ungiven_evidence(self):
        prompt = _build_interpretation_prompt(
            "Sam", 8, exposures=[{"exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security"]}],
            salient_domains=["attachment_security"], narration_signals=[], protective_factors=[], prior_patterns=[],
        )
        assert "GROUNDING RULE" in prompt
        assert "none active" in prompt  # confirms protective factors are explicitly told to be absent, not just omitted

    def test_reparative_prompt_forbids_inventing_ungiven_evidence(self):
        prompt = _build_reparative_prompt(
            "Sam", 9, protective_factors_this_batch=[{"factor_type": "friendship", "domains_buffered": ["social_belonging"], "raw_text": "her friend"}],
            narration_signals=[], prior_patterns=[],
        )
        assert "GROUNDING RULE" in prompt
        assert "Do NOT invent" in prompt
