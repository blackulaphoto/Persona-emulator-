"""
Tests for the Developmental Exposure Extractor
(app/services/developmental_exposure_engine.py).

These are the psychological-invariant tests called for in
docs/MIGRATION_MAP.md - most importantly, that negated/denied content does
NOT produce an exposure. This was the headline failure of the old
app/utils/backstory_symptom_mapper.py.

The keyword-fallback path is tested directly since it's deterministic and
needs no network access. The AI path's output validation is tested via
_validate_and_filter with a hand-built response, so no OpenAI call is made.
"""
from app.services.developmental_exposure_engine import (
    extract_exposures_keyword,
    _validate_and_filter,
    EXPOSURE_TAXONOMY,
    PROTECTIVE_FACTOR_TAXONOMY,
    DEVELOPMENTAL_DOMAINS,
)


class TestKeywordFallbackDetectsExposures:
    def test_single_sentence_supports_multiple_exposures(self):
        result = extract_exposures_keyword(
            "My father drank constantly and disappeared for days."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" in types
        assert "caregiver_absence" in types

    def test_domains_come_from_taxonomy(self):
        result = extract_exposures_keyword("My father was an alcoholic.")
        exposure = next(e for e in result["exposures"] if e["exposure_type"] == "caregiver_substance_use")
        assert set(exposure["developmental_domains"]) <= set(DEVELOPMENTAL_DOMAINS)
        assert "attachment_security" in exposure["developmental_domains"]

    def test_generic_abused_phrasing_is_detected(self):
        # Regression: found while wiring the end-to-end chain - bare "abused"
        # (the single most common word a case author would actually use)
        # matched nothing at all until this was added.
        result = extract_exposures_keyword("Timmy was physically abused by his father at 17.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "physical_discipline_or_violence" in types

    def test_generic_abused_still_respects_negation(self):
        result = extract_exposures_keyword("Timmy was not abused as a child.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "physical_discipline_or_violence" not in types

    def test_no_disorder_or_severity_in_output(self):
        result = extract_exposures_keyword("I was beaten regularly as a child.")
        for exposure in result["exposures"]:
            assert "severity" not in exposure
            assert "disorder_name" not in exposure
            assert set(exposure.keys()) == {"exposure_type", "developmental_domains", "raw_text", "age_hint"}


class TestNegationInvariant:
    """The core failure being fixed: 'I was not abused' must not fire."""

    def test_explicit_denial_of_physical_abuse_produces_no_exposure(self):
        result = extract_exposures_keyword("I was not abused as a child. Nobody ever hit me.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "physical_discipline_or_violence" not in types

    def test_explicit_denial_of_substance_use_produces_no_exposure(self):
        result = extract_exposures_keyword("My father never drank, not once in his life.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" not in types

    def test_denial_does_not_suppress_unrelated_affirmed_exposure(self):
        # Negation should be local to what it negates, not blank out the whole text.
        result = extract_exposures_keyword(
            "I was never hit. But my parents divorced and it was chaotic at home."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "physical_discipline_or_violence" not in types
        assert "separation_or_divorce" in types
        assert "household_unpredictability" in types


class TestProtectiveFactors:
    def test_stable_alternate_caregiver_detected(self):
        result = extract_exposures_keyword(
            "My grandmother stepped in and raised me when things got hard at home."
        )
        factor_types = {f["factor_type"] for f in result["protective_factors"]}
        assert "stable_alternate_caregiver" in factor_types

    def test_denied_protective_factor_not_extracted(self):
        result = extract_exposures_keyword("I never had a mentor or anyone like that.")
        factor_types = {f["factor_type"] for f in result["protective_factors"]}
        assert "mentor" not in factor_types


class TestValidateAndFilter:
    """Defense against the AI path inventing types outside the controlled vocabulary."""

    def test_drops_hallucinated_exposure_type(self):
        raw = {
            "exposures": [
                {"exposure_type": "caregiver_substance_use", "developmental_domains": ["attachment_security"], "raw_text": "he drank"},
                {"exposure_type": "made_up_disorder_xyz", "developmental_domains": ["identity"], "raw_text": "nonsense"},
            ],
            "protective_factors": [],
        }
        result = _validate_and_filter(raw)
        types = {e["exposure_type"] for e in result["exposures"]}
        assert types == {"caregiver_substance_use"}

    def test_drops_hallucinated_domain_but_keeps_exposure(self):
        raw = {
            "exposures": [
                {"exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security", "made_up_domain"], "raw_text": "gone for weeks"},
            ],
            "protective_factors": [],
        }
        result = _validate_and_filter(raw)
        assert result["exposures"][0]["developmental_domains"] == ["attachment_security"]

    def test_falls_back_to_taxonomy_domains_if_all_invalid(self):
        raw = {
            "exposures": [
                {"exposure_type": "caregiver_absence", "developmental_domains": ["bogus"], "raw_text": "gone"},
            ],
            "protective_factors": [],
        }
        result = _validate_and_filter(raw)
        assert result["exposures"][0]["developmental_domains"] == EXPOSURE_TAXONOMY["caregiver_absence"]["domains"]

    def test_empty_response_produces_empty_lists(self):
        assert _validate_and_filter({}) == {"exposures": [], "protective_factors": []}
        assert _validate_and_filter(None) == {"exposures": [], "protective_factors": []}


class TestTaxonomyIntegrity:
    def test_every_exposure_domain_is_allowed(self):
        for exposure_type, meta in EXPOSURE_TAXONOMY.items():
            for domain in meta["domains"]:
                assert domain in DEVELOPMENTAL_DOMAINS, f"{exposure_type} references unknown domain {domain}"

    def test_every_protective_domain_is_allowed(self):
        for factor_type, meta in PROTECTIVE_FACTOR_TAXONOMY.items():
            for domain in meta["domains"]:
                assert domain in DEVELOPMENTAL_DOMAINS, f"{factor_type} references unknown domain {domain}"
