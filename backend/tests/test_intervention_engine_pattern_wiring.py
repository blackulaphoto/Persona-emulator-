"""
Tests for step 7 of docs/MIGRATION_MAP.md: intervention_engine.py's
optional pattern-aware wiring (adaptation_patterns / clinical_pattern_
hypotheses) and the PATTERN_KEY_THERAPY_ALIASES bridge.

Not yet called by any live route with pattern data - app/api/routes/
interventions.py still calls analyze_intervention() with just a persona
object, exactly as before. These tests cover the new optional behavior in
isolation and confirm the old call shape is completely unaffected.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.intervention_engine import (
    generate_intervention_prompt,
    _aliased_pattern_symptoms,
    PATTERN_KEY_THERAPY_ALIASES,
    select_targeted_pattern,
)
from app.utils.therapy_database import calculate_therapy_match_score, THERAPY_MODALITIES


@pytest.fixture
def persona():
    from app.models import Persona
    return Persona(
        name="Michael",
        baseline_age=25,
        current_age=30,
        baseline_gender="male",
        baseline_background="...",
        current_personality={
            "openness": 0.5, "conscientiousness": 0.4, "extraversion": 0.4,
            "agreeableness": 0.5, "neuroticism": 0.7,
        },
        current_attachment_style="insecure-anxious",
        current_trauma_markers=[],
    )


class TestAliasBridge:
    def test_bpd_pattern_key_matches_dbt_only_through_alias(self):
        # Unaliased, the taxonomy key doesn't match DBT's best_for at all.
        unaliased_score = calculate_therapy_match_score("DBT", ["borderline_personality"])
        assert unaliased_score == 0.0

        aliased_symptoms = _aliased_pattern_symptoms(["borderline_personality"])
        aliased_score = calculate_therapy_match_score("DBT", aliased_symptoms)
        assert aliased_score > 0.0

    def test_ptsd_matches_directly_without_needing_an_alias(self):
        # "ptsd" already matches EMDR's best_for verbatim - confirms the
        # bridge doesn't need to (and shouldn't) cover every pattern_key.
        assert "ptsd" not in PATTERN_KEY_THERAPY_ALIASES
        score = calculate_therapy_match_score("EMDR", _aliased_pattern_symptoms(["ptsd"]))
        assert score > 0.0

    def test_original_key_preserved_alongside_aliases(self):
        # Even for a pattern_key that needs aliasing, the original key is
        # kept in the expansion (harmless, and correct in case some future
        # therapy's best_for is updated to use the taxonomy key directly).
        expanded = _aliased_pattern_symptoms(["borderline_personality"])
        assert "borderline_personality" in expanded
        assert "bpd" in expanded

    def test_ocpd_is_not_wrongly_aliased_to_ocd_treatment(self):
        # obsessive_compulsive_personality (a personality disorder) must not
        # be bridged to ERP's "compulsive_behaviors" target, which is meant
        # for OCD (a different disorder) - a clinically wrong match would be
        # worse than no match.
        assert "obsessive_compulsive_personality" not in PATTERN_KEY_THERAPY_ALIASES

    def test_every_alias_target_is_real_best_for_vocabulary(self):
        all_best_for = set()
        for t in THERAPY_MODALITIES.values():
            all_best_for.update(t["best_for"])
        for pattern_key, aliases in PATTERN_KEY_THERAPY_ALIASES.items():
            for alias in aliases:
                assert alias in all_best_for, f"{pattern_key} -> {alias} does not match any therapy's best_for"


class TestPromptBackwardCompatibility:
    def test_no_pattern_data_omits_new_sections(self, persona):
        prompt = generate_intervention_prompt(
            persona=persona, therapy_type="CBT", duration=12, intensity="weekly", age_at_intervention=30,
        )
        assert "ESTABLISHED DEVELOPMENTAL PATTERNS" not in prompt
        assert "CLINICAL PATTERN HYPOTHESES" not in prompt

    def test_still_works_with_only_positional_legacy_args(self, persona):
        # The exact call shape app/api/routes/interventions.py uses today.
        prompt = generate_intervention_prompt(
            persona=persona, therapy_type="ACT", duration=16, intensity="weekly", age_at_intervention=28,
        )
        assert "Michael" in prompt
        assert "Acceptance & Commitment Therapy" in prompt


class TestPromptWithPatternData:
    def test_adaptation_patterns_section_included(self, persona):
        patterns = [{
            "pattern_name": "Leave Before You're Left",
            "adaptation_strategy": "avoidance",
            "status": "established",
            "evidence_strength": 0.6,
            "current_manifestations": [],
        }]
        prompt = generate_intervention_prompt(
            persona=persona, therapy_type="DBT", duration=24, intensity="weekly",
            age_at_intervention=30, adaptation_patterns=patterns,
        )
        assert "ESTABLISHED DEVELOPMENTAL PATTERNS" in prompt
        assert "Leave Before You're Left" in prompt
        assert "substantially improves" in prompt  # the standard-setting example from the spec

    def test_clinical_pattern_hypotheses_section_included(self, persona):
        hypotheses = [{"pattern_key": "borderline_personality", "tier": "clinical_pattern_resemblance", "evidence_strength": 0.7}]
        prompt = generate_intervention_prompt(
            persona=persona, therapy_type="DBT", duration=24, intensity="weekly",
            age_at_intervention=30, clinical_pattern_hypotheses=hypotheses,
        )
        assert "CLINICAL PATTERN HYPOTHESES" in prompt
        assert "borderline_personality" in prompt

    def test_pattern_data_raises_the_match_score_for_dbt_and_bpd(self, persona):
        # The whole point of step 7: DBT's match for a borderline_personality
        # pattern should be substantive, not near-zero because of a naming
        # mismatch between the taxonomy and therapy_database.py.
        hypotheses = [{"pattern_key": "borderline_personality", "tier": "developmental_pattern", "evidence_strength": None}]
        prompt = generate_intervention_prompt(
            persona=persona, therapy_type="DBT", duration=24, intensity="weekly",
            age_at_intervention=30, clinical_pattern_hypotheses=hypotheses,
        )
        # BASELINE EFFICACY MATCH: X.XX - extract and check it's a real match, not near-zero.
        line = next(l for l in prompt.splitlines() if l.startswith("BASELINE EFFICACY MATCH"))
        score = float(line.split(":")[1].strip().split(" ")[0])
        assert score > 0.3


class TestAnalyzeInterventionStillAcceptsLegacyCall:
    @pytest.mark.asyncio
    async def test_legacy_call_shape_unaffected(self, persona):
        from app.services.intervention_engine import analyze_intervention

        with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"efficacy_match": 0.5, "reasoning": "ok"}
            result = await analyze_intervention(
                persona=persona, therapy_type="CBT", duration=12, intensity="weekly", age_at_intervention=30,
            )
        assert result["efficacy_match"] == 0.5


class TestSelectTargetedPattern:
    """Step 11e: which AdaptationPattern a course of therapy is presumed aimed at."""

    def test_no_patterns_returns_none(self):
        assert select_targeted_pattern([]) is None
        assert select_targeted_pattern(None) is None

    def test_only_emerging_patterns_returns_none(self):
        patterns = [{"adaptation_strategy": "avoidance", "status": "emerging", "evidence_strength": 0.9}]
        assert select_targeted_pattern(patterns) is None

    def test_single_established_pattern_selected(self):
        patterns = [{"adaptation_strategy": "avoidance", "status": "established", "evidence_strength": 0.6}]
        result = select_targeted_pattern(patterns)
        assert result["adaptation_strategy"] == "avoidance"

    def test_established_pattern_preferred_over_higher_evidence_emerging_one(self):
        patterns = [
            {"adaptation_strategy": "hypervigilance", "status": "emerging", "evidence_strength": 0.9},
            {"adaptation_strategy": "avoidance", "status": "established", "evidence_strength": 0.5},
        ]
        result = select_targeted_pattern(patterns)
        assert result["adaptation_strategy"] == "avoidance"

    def test_highest_evidence_strength_established_pattern_wins(self):
        patterns = [
            {"adaptation_strategy": "avoidance", "status": "established", "evidence_strength": 0.5},
            {"adaptation_strategy": "hypervigilance", "status": "established", "evidence_strength": 0.8},
        ]
        result = select_targeted_pattern(patterns)
        assert result["adaptation_strategy"] == "hypervigilance"

    def test_null_evidence_strength_treated_as_zero_not_a_crash(self):
        patterns = [
            {"adaptation_strategy": "avoidance", "status": "established", "evidence_strength": None},
            {"adaptation_strategy": "hypervigilance", "status": "established", "evidence_strength": 0.1},
        ]
        result = select_targeted_pattern(patterns)
        assert result["adaptation_strategy"] == "hypervigilance"
