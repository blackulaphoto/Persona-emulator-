"""
Tests for app/services/chat_context_builder.py (docs/MIGRATION_MAP.md step 10).

Confirms: personality/symptom-marker guidance still works (the live signal
today), pattern-aware guidance degrades gracefully when empty (the current
production reality) and activates correctly when populated, and - most
importantly - that the retired keyword-scripted trauma functions
(detect_trauma_type, build_trauma_behavioral_profile,
build_age_appropriate_trauma_expression, including their child-sexual-
abuse-specific scripted dialogue) are actually gone from the codebase, not
just unused.
"""
import subprocess
import sys

from app.services.chat_context_builder import (
    build_personality_behaviors,
    build_symptom_marker_behaviors,
    build_pattern_aware_behaviors,
    build_state_aware_behaviors,
    build_full_persona_context,
    build_age_language_guidance,
    ADAPTATION_STRATEGY_GUIDANCE,
    STATE_VARIABLE_GUIDANCE,
)
from app.services.pattern_engine import ADAPTATION_STRATEGIES
from app.schemas.developmental_analysis_schemas import STATE_VARIABLES


class TestPersonalityBehaviors:
    def test_high_neuroticism_produces_anxious_guidance(self):
        behaviors = build_personality_behaviors({"neuroticism": 0.8, "openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5})
        assert any("anxious" in b.lower() for b in behaviors)

    def test_low_extraversion_produces_short_answer_guidance(self):
        behaviors = build_personality_behaviors({"extraversion": 0.2, "neuroticism": 0.5, "openness": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5})
        assert any("SHORT" in b for b in behaviors)

    def test_missing_traits_default_gracefully(self):
        behaviors = build_personality_behaviors({})
        assert len(behaviors) >= 2


class TestSymptomMarkerBehaviors:
    def test_known_marker_produces_guidance(self):
        behaviors = build_symptom_marker_behaviors(["hypervigilance"])
        assert len(behaviors) == 1
        assert "notices" in behaviors[0].lower() or "startles" in behaviors[0].lower()

    def test_multiple_markers_deduped(self):
        # "anger" and "irritability" map to the identical guidance string - should only appear once.
        behaviors = build_symptom_marker_behaviors(["anger", "irritability"])
        assert len(behaviors) == 1

    def test_unknown_marker_produces_nothing(self):
        assert build_symptom_marker_behaviors(["some_made_up_marker"]) == []

    def test_empty_or_none_markers(self):
        assert build_symptom_marker_behaviors([]) == []
        assert build_symptom_marker_behaviors(None) == []


class TestPatternAwareBehaviorsGracefulDegradation:
    def test_all_empty_produces_empty_list(self):
        # The current live-system default.
        assert build_pattern_aware_behaviors() == []
        assert build_pattern_aware_behaviors([], [], []) == []

    def test_adaptation_pattern_produces_guidance(self):
        patterns = [{"pattern_name": "Leave Before You're Left", "adaptation_strategy": "avoidance", "status": "established", "evidence_strength": 0.7}]
        behaviors = build_pattern_aware_behaviors(adaptation_patterns=patterns)
        assert any("Leave Before You're Left" in b for b in behaviors)

    def test_unknown_adaptation_strategy_skipped_gracefully(self):
        patterns = [{"pattern_name": "X", "adaptation_strategy": "made_up_strategy", "status": "emerging", "evidence_strength": None}]
        assert build_pattern_aware_behaviors(adaptation_patterns=patterns) == []

    def test_interpretations_produce_belief_guidance(self):
        interpretations = [{"belief_statement": "People leave."}]
        behaviors = build_pattern_aware_behaviors(interpretations=interpretations)
        assert any("People leave." in b for b in behaviors)

    def test_all_adaptation_strategies_have_guidance(self):
        # Regression guard: every controlled-vocab strategy from pattern_engine.py
        # must have real behavioral guidance here, not a silent gap.
        for strategy in ADAPTATION_STRATEGIES:
            assert strategy in ADAPTATION_STRATEGY_GUIDANCE, f"no guidance for adaptation_strategy {strategy!r}"


class TestStateAwareBehaviors:
    """Step 11f: chat_context_builder.py's State-tier guidance."""

    def test_empty_or_none_state_produces_nothing(self):
        assert build_state_aware_behaviors(None) == []
        assert build_state_aware_behaviors({}) == []

    def test_untouched_variable_produces_no_guidance(self):
        # Only trust has been touched - threat_sensitivity absent entirely,
        # not assumed at an unearned 0.5 baseline.
        behaviors = build_state_aware_behaviors({"trust": 0.5})
        assert behaviors == []  # 0.5 is the middle band - no guidance either way

    def test_high_threat_sensitivity_produces_on_edge_guidance(self):
        behaviors = build_state_aware_behaviors({"threat_sensitivity": 0.8})
        assert any("on edge" in b.lower() for b in behaviors)

    def test_low_trust_produces_wary_guidance(self):
        behaviors = build_state_aware_behaviors({"trust": 0.2})
        assert any("wary" in b.lower() for b in behaviors)

    def test_multiple_variables_each_produce_a_line(self):
        behaviors = build_state_aware_behaviors({"trust": 0.2, "mood": 0.8, "regulation": 0.1})
        assert len(behaviors) == 3

    def test_every_state_variable_has_guidance_coverage(self):
        # Regression guard: every controlled-vocab State variable from
        # developmental_analysis_schemas.py must have guidance here.
        for variable in STATE_VARIABLES:
            assert variable in STATE_VARIABLE_GUIDANCE, f"no guidance for state variable {variable!r}"

    def test_unknown_key_in_current_state_ignored(self):
        # Defensive - a key outside STATE_VARIABLES should never reach here
        # in practice (state_trait_engine validates first), but shouldn't crash if it does.
        behaviors = build_state_aware_behaviors({"not_a_real_variable": 0.9})
        assert behaviors == []


class TestFullPersonaContext:
    def test_degrades_to_personality_and_symptoms_only_when_patterns_empty(self):
        context = build_full_persona_context(
            persona_name="Michael", age=30,
            personality={"neuroticism": 0.7, "openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5},
            trauma_markers=["hypervigilance"],
        )
        assert "DEVELOPMENTAL PATTERNS" not in context
        assert "CURRENT SYMPTOM TENDENCIES" in context
        assert "CURRENT STATE" not in context

    def test_includes_pattern_section_when_populated(self):
        context = build_full_persona_context(
            persona_name="Michael", age=30,
            personality={"neuroticism": 0.5, "openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5},
            adaptation_patterns=[{"pattern_name": "X", "adaptation_strategy": "avoidance", "status": "established", "evidence_strength": 0.6}],
        )
        assert "DEVELOPMENTAL PATTERNS" in context
        assert "Michael" in context

    def test_includes_state_section_when_populated(self):
        context = build_full_persona_context(
            persona_name="Michael", age=30,
            personality={"neuroticism": 0.5, "openness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "conscientiousness": 0.5},
            current_state={"threat_sensitivity": 0.8},
        )
        assert "CURRENT STATE" in context
        assert "on edge" in context.lower()


class TestAgeLanguageGuidance:
    def test_young_child_gets_simple_guidance(self):
        assert "VERY simple" in build_age_language_guidance(6)

    def test_adult_gets_adult_guidance(self):
        assert "adult language" in build_age_language_guidance(35).lower()


class TestScriptedTraumaFunctionsAreActuallyGone:
    """
    Not just unused - actually removed from the codebase, including the
    child-sexual-abuse-specific scripted dialogue lines that were the most
    concerning finding in the original audit.
    """

    def test_functions_not_importable_from_chat(self):
        import app.api.routes.chat as chat_module
        assert not hasattr(chat_module, "detect_trauma_type")
        assert not hasattr(chat_module, "build_trauma_behavioral_profile")
        assert not hasattr(chat_module, "build_age_appropriate_trauma_expression")

    def test_scripted_child_abuse_dialogue_strings_not_in_repo(self):
        # Grep the actual chat.py source for the literal scripted lines that
        # used to be there - confirms the content itself is gone, not just
        # the function names.
        result = subprocess.run(
            [sys.executable, "-c", "print(open('app/api/routes/chat.py').read())"],
            capture_output=True, text=True, cwd="."
        )
        source = result.stdout
        assert "I don't want to go to PE" not in source
        assert "My tummy hurts" not in source
        assert "molest" not in source.lower()
