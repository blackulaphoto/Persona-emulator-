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

    def test_reliable_close_relationship_detected(self):
        result = extract_exposures_keyword(
            "In adulthood I found a reliable partner and we repaired conflicts together."
        )
        factor_types = {f["factor_type"] for f in result["protective_factors"]}
        assert "reliable_close_relationship" in factor_types

    def test_corrective_emotional_experience_detected(self):
        # P0-2 correction: developmental significance isn't adversity-only -
        # a genuine repair/reconciliation event has its own taxonomy entry,
        # distinct from an ongoing relationship-quality factor.
        result = extract_exposures_keyword(
            "He took responsibility and repaired the relationship, and she trusted him again."
        )
        factor_types = {f["factor_type"] for f in result["protective_factors"]}
        assert "corrective_emotional_experience" in factor_types

    def test_corrective_emotional_experience_includes_attachment_security_domain(self):
        # Deliberately tagged with attachment_security so a real repair also
        # engages attachment_engine.apply_attachment_protection, not just the
        # interpretation pipeline - see developmental_exposure_engine.py's
        # comment on this entry.
        result = extract_exposures_keyword("She trusted them again after they proved them wrong.")
        factor = next(f for f in result["protective_factors"] if f["factor_type"] == "corrective_emotional_experience")
        assert "attachment_security" in factor["domains_buffered"]


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


class TestCaregiverContextRequiredForCaregiverExposures:
    """
    Canonical grounding fix: production regression on a real persona
    ("Brandon"). "Brandon enters rehab..." (the subject's own recovery,
    described decades into adulthood) was classified as
    caregiver_substance_use purely because "rehab" is one of that exposure
    type's keywords - the extractor never checked whether a caregiver was
    actually the one who entered rehab. That produced a fabricated
    "Hypervigilance" pattern and adaptation history dated to an event that
    never happened, which then propagated into the narrative as fact.

    Every exposure_type literally named caregiver_* requires a caregiver
    word (mother/father/parent/guardian/etc.) in the SAME SENTENCE as the
    matched keyword - not merely anywhere in a (possibly long, multi-topic)
    text, which is exactly the failure mode of a whole-text check: a
    caregiver mentioned in one sentence must not attribute an unrelated
    keyword match in a completely different sentence to that caregiver.
    """

    def test_subjects_own_rehab_does_not_produce_caregiver_substance_use(self):
        # The exact production sentence from the Brandon regression.
        result = extract_exposures_keyword(
            "After another prolonged period of drug use, Brandon enters rehab, earns his RADT, "
            "becomes a case manager in substance-use treatment, and begins developing AI applications."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" not in types

    def test_caregivers_rehab_still_produces_caregiver_substance_use(self):
        result = extract_exposures_keyword(
            "My father struggled with alcohol and eventually went to rehab when I was twelve."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" in types

    def test_caregiver_mentioned_in_an_unrelated_sentence_does_not_attribute_a_later_match(self):
        # The precise cross-sentence contamination a whole-text check would
        # have missed even after requiring *some* caregiver word to be
        # present in the document: a caregiver mentioned in one sentence,
        # the subject's own rehab entry in a completely different one.
        result = extract_exposures_keyword(
            "My mother struggled her whole life with her own issues. Years later, after another "
            "prolonged period of drug use, I entered rehab myself and turned things around."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" not in types

    def test_caregiver_absence_requires_caregiver_context(self):
        result = extract_exposures_keyword("Brandon disappeared for a few days during a rough patch.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_absence" not in types
        result = extract_exposures_keyword("My father disappeared for days at a time.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_absence" in types

    def test_caregiver_incarceration_requires_caregiver_context(self):
        # Second real instance of the same bug class, found empirically via
        # the Brandon fixture: "While incarcerated, Brandon meets a man..."
        # describes Brandon's OWN incarceration and was misclassified as
        # caregiver_incarceration before this fix.
        result = extract_exposures_keyword(
            "While incarcerated, Brandon meets a man who teaches him event promotion."
        )
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_incarceration" not in types
        result = extract_exposures_keyword("My father was incarcerated for most of my childhood.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_incarceration" in types

    def test_caregiver_emotional_unavailability_requires_caregiver_context(self):
        result = extract_exposures_keyword("He became emotionally distant after the divorce.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_emotional_unavailability" not in types
        result = extract_exposures_keyword("My mother was emotionally unavailable throughout my childhood.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_emotional_unavailability" in types

    def test_caregiver_mental_illness_requires_caregiver_context(self):
        result = extract_exposures_keyword("She was diagnosed as bipolar in her twenties.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_mental_illness" not in types
        result = extract_exposures_keyword("My father was bipolar and often had unstable moods.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_mental_illness" in types

    def test_negation_still_applies_within_the_caregiver_sentence(self):
        # The caregiver-context gate and negation must compose, not bypass
        # each other.
        result = extract_exposures_keyword("My father never drank, not once in his life.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" not in types

    def test_single_sentence_multiple_caregiver_exposures_still_both_detected(self):
        # Regression guard for TestKeywordFallbackDetectsExposures's own
        # test_single_sentence_supports_multiple_exposures - the caregiver-
        # context gate must not break same-sentence, same-caregiver
        # multi-exposure detection.
        result = extract_exposures_keyword("My father drank constantly and disappeared for days.")
        types = {e["exposure_type"] for e in result["exposures"]}
        assert "caregiver_substance_use" in types
        assert "caregiver_absence" in types


class TestTaxonomyCaregiverContextCoverage:
    def test_every_caregiver_named_exposure_type_requires_caregiver_context(self):
        # Every exposure_type whose NAME claims a caregiver did something
        # (as opposed to types like death_of_caregiver_or_family or
        # chronic_illness_family_member, whose keywords are already
        # inherently self-scoping, e.g. "lost my mother") must actually
        # enforce that attribution - this is the exact class of bug the
        # Brandon regression exposed, generalized into a taxonomy-wide
        # integrity check so a future caregiver_* addition can't reintroduce
        # it silently.
        self_scoping_keyword_types = {"death_of_caregiver_or_family", "chronic_illness_family_member"}
        for exposure_type, meta in EXPOSURE_TAXONOMY.items():
            if exposure_type.startswith("caregiver_") and exposure_type not in self_scoping_keyword_types:
                assert meta.get("requires_caregiver_context") is True, (
                    f"{exposure_type} is caregiver-attributed but does not require caregiver context"
                )
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
