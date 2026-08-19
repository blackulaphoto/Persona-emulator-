"""
Tests for the Functional Observation Engine
(app/services/functional_observation_engine.py) - the Behavior / Known
Outcomes evidence channel from docs/MIGRATION_MAP.md's Evidence & Source
Model.
"""
from app.services.functional_observation_engine import (
    extract_observations_keyword,
    _validate_and_filter,
    OBSERVATION_TYPES,
    VALENCES,
    _KEYWORD_RULES,
)
from app.services.developmental_exposure_engine import DEVELOPMENTAL_DOMAINS


class TestKeywordFallback:
    def test_detects_concerning_behavioral_pattern(self):
        result = extract_observations_keyword(
            "Timmy avoids physical contact and becomes tense when his father is mentioned."
        )
        types = {o["observation_type"] for o in result}
        assert "behavioral_pattern" in types
        obs = next(o for o in result if o["observation_type"] == "behavioral_pattern")
        assert obs["valence"] == "concerning"

    def test_detects_protective_relationship_functioning(self):
        result = extract_observations_keyword("Timmy maintains close, trusting relationships with several friends.")
        types = {o["observation_type"] for o in result}
        assert "relationship_functioning" in types
        obs = next(o for o in result if o["observation_type"] == "relationship_functioning")
        assert obs["valence"] == "protective"

    def test_detects_substance_use_pattern(self):
        result = extract_observations_keyword("He has been drinking heavily since the breakup.")
        types = {o["observation_type"] for o in result}
        assert "substance_use_pattern" in types

    def test_keyword_fallback_never_produces_candidate_patterns(self):
        result = extract_observations_keyword("Timmy avoids physical contact and becomes tense.")
        for obs in result:
            assert obs["candidate_pattern_keys"] == []

    def test_no_match_produces_empty_list(self):
        assert extract_observations_keyword("Timmy went to the store on Tuesday.") == []

    def test_empty_text(self):
        assert extract_observations_keyword("") == []


class TestValidateAndFilter:
    def test_drops_unknown_observation_type(self):
        raw = {"observations": [
            {"observation_type": "made_up_type", "description": "x", "developmental_domains": [], "valence": "neutral", "candidate_pattern_keys": []},
        ]}
        assert _validate_and_filter(raw) == []

    def test_drops_attribution_violation(self):
        raw = {"observations": [
            {"observation_type": "behavioral_pattern", "description": "You avoid contact.", "developmental_domains": [], "valence": "concerning", "candidate_pattern_keys": []},
        ]}
        assert _validate_and_filter(raw) == []

    def test_defaults_invalid_valence_to_neutral(self):
        raw = {"observations": [
            {"observation_type": "behavioral_pattern", "description": "Timmy avoids contact.", "developmental_domains": [], "valence": "bogus", "candidate_pattern_keys": []},
        ]}
        result = _validate_and_filter(raw)
        assert result[0]["valence"] == "neutral"

    def test_drops_invalid_domains(self):
        raw = {"observations": [
            {"observation_type": "behavioral_pattern", "description": "Timmy avoids contact.", "developmental_domains": ["emotional_safety", "made_up_domain"], "valence": "concerning", "candidate_pattern_keys": []},
        ]}
        result = _validate_and_filter(raw)
        assert result[0]["developmental_domains"] == ["emotional_safety"]

    def test_drops_invalid_candidate_pattern_keys(self):
        raw = {"observations": [
            {"observation_type": "behavioral_pattern", "description": "Timmy avoids contact.", "developmental_domains": [], "valence": "concerning", "candidate_pattern_keys": ["ptsd", "not_a_real_disorder"]},
        ]}
        result = _validate_and_filter(raw)
        assert result[0]["candidate_pattern_keys"] == ["ptsd"]

    def test_protective_valence_never_keeps_candidate_pattern_keys_even_if_ai_provides_them(self):
        # Defense in depth: the prompt tells the model not to populate
        # candidate_pattern_keys for protective observations, but the code
        # doesn't trust that - only "concerning" observations look them up
        # against symptom_taxonomy at all.
        raw = {"observations": [
            {"observation_type": "relationship_functioning", "description": "Timmy has close friends.", "developmental_domains": [], "valence": "protective", "candidate_pattern_keys": ["ptsd"]},
        ]}
        result = _validate_and_filter(raw)
        assert result[0]["candidate_pattern_keys"] == []

    def test_empty_response(self):
        assert _validate_and_filter({}) == []
        assert _validate_and_filter(None) == []


class TestTaxonomyIntegrity:
    def test_all_rule_domains_are_real(self):
        for rule in _KEYWORD_RULES:
            for domain in rule["domains"]:
                assert domain in DEVELOPMENTAL_DOMAINS, f"unknown domain {domain} in rule {rule['keywords']}"

    def test_all_rule_observation_types_are_real(self):
        for rule in _KEYWORD_RULES:
            assert rule["observation_type"] in OBSERVATION_TYPES

    def test_all_rule_valences_are_real(self):
        for rule in _KEYWORD_RULES:
            assert rule["valence"] in VALENCES
