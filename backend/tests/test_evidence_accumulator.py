"""
Tests for the Evidence Accumulator (app/services/evidence_accumulator.py).

The invariant that matters most here is Revision 3 from docs/MIGRATION_MAP.md:
a single exposure opens a hypothesis worth investigating, but must NEVER seed
a starting evidence_strength. Strength has to be earned from persistence,
corroborating narrative signals, or reduced by protective factors - and a
hypothesis with zero evidence stays at strength None, not 0.0 and not the old
system's hardcoded 0.8.
"""
from app.services.evidence_accumulator import (
    accumulate_evidence,
    project_current_trauma_markers,
    evidence_strength_label,
    EXPOSURE_HYPOTHESIS_PRIORS,
    SIGNAL_HYPOTHESIS_SUPPORT,
    ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT,
    build_clinical_pattern_hypothesis_rows,
    DISPLAY_THRESHOLD,
)


def _exposure(exposure_type, age, domains=None, id_="exp-1"):
    return {
        "id": id_,
        "exposure_type": exposure_type,
        "developmental_domains": domains or EXPOSURE_HYPOTHESIS_PRIORS.get(exposure_type, []) and ["attachment_security"],
        "age_at_exposure": age,
        # source/source_event_id default to distinct-per-call (keyed on id_) so
        # existing "two occurrences" test intent maps directly onto
        # _persistence_evidence's real distinctness key without touching every
        # call site - see that function's docstring for why raw row count
        # alone isn't the right signal anymore.
        "source": "experience",
        "source_event_id": id_,
    }


class TestHypothesisOpeningNeverSeedsStrength:
    """The headline invariant: opening a hypothesis is not the same as believing it."""

    def test_single_exposure_opens_hypothesis_with_null_strength(self):
        exposures = [_exposure("sexual_boundary_violation", age=9, id_="exp-1")]
        result = accumulate_evidence(exposures)

        assert "ptsd" in result
        assert result["ptsd"]["evidence_strength"] is None
        assert result["ptsd"]["tier"] == "developmental_pattern"
        assert result["ptsd"]["supporting_evidence"] == []

    def test_single_exposure_is_not_itself_supporting_evidence(self):
        # The exposure that opens the hypothesis must not also count as its own evidence.
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        result = accumulate_evidence(exposures)
        assert result["ptsd"]["supporting_evidence"] == []
        assert result["ptsd"]["evidence_strength"] is None

    def test_no_exposures_produces_no_hypotheses(self):
        assert accumulate_evidence([]) == {}


class TestPersistenceEvidence:
    def test_recurring_exposure_type_produces_persistence_evidence(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, id_="exp-1"),
            _exposure("caregiver_substance_use", age=9, id_="exp-2"),
        ]
        result = accumulate_evidence(exposures)
        pattern = result["reactive_attachment_disorder"]
        types = {e["type"] for e in pattern["supporting_evidence"]}
        assert "persistence" in types
        assert pattern["evidence_strength"] is not None
        assert pattern["evidence_strength"] > 0

    def test_single_occurrence_does_not_trigger_persistence(self):
        exposures = [_exposure("caregiver_substance_use", age=5, id_="exp-1")]
        result = accumulate_evidence(exposures)
        pattern = result["reactive_attachment_disorder"]
        assert pattern["supporting_evidence"] == []

    def test_persistence_scales_with_recurrence_count_not_capped_at_one(self):
        """
        Regression: exposures are the only evidence source wired into a live
        route so far (narration/functional observations aren't). If
        persistence contributed at most one fixed-weight entry regardless of
        how many times something recurred, evidence_strength could never
        exceed 0.15 from exposures alone - permanently below
        DISPLAY_THRESHOLD (0.4), meaning current_trauma_markers could never
        populate in practice. Found via tests/test_developmental_pipeline.py.
        """
        two_occurrences = [
            _exposure("caregiver_substance_use", age=5, id_="exp-1"),
            _exposure("caregiver_substance_use", age=9, id_="exp-2"),
        ]
        four_occurrences = two_occurrences + [
            _exposure("caregiver_substance_use", age=12, id_="exp-3"),
            _exposure("caregiver_substance_use", age=15, id_="exp-4"),
        ]
        strength_at_two = accumulate_evidence(two_occurrences)["reactive_attachment_disorder"]["evidence_strength"]
        strength_at_four = accumulate_evidence(four_occurrences)["reactive_attachment_disorder"]["evidence_strength"]
        assert strength_at_four > strength_at_two
        assert strength_at_four >= DISPLAY_THRESHOLD

    def test_two_exposure_types_from_one_input_do_not_false_positive_as_persistence(self):
        """
        Regression: "My father drank constantly and disappeared for days" is
        ONE sentence that produces TWO exposure_types (caregiver_substance_use,
        caregiver_absence), both implicating reactive_attachment_disorder. That
        must not read as "recurred twice" - it's one situation described two
        ways, not genuine recurrence over time. Found via
        tests/test_developmental_pipeline.py's end-to-end run.
        """
        exposures = [
            {"id": "e1", "exposure_type": "caregiver_substance_use", "developmental_domains": ["attachment_security"],
             "age_at_exposure": 6, "source": "backstory", "source_event_id": None},
            {"id": "e2", "exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security"],
             "age_at_exposure": 6, "source": "backstory", "source_event_id": None},
        ]
        result = accumulate_evidence(exposures)
        pattern = result["reactive_attachment_disorder"]
        types = {e["type"] for e in pattern["supporting_evidence"]}
        assert "persistence" not in types
        assert pattern["evidence_strength"] is None

    def test_same_pattern_from_backstory_and_a_later_experience_is_genuine_persistence(self):
        exposures = [
            {"id": "e1", "exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security"],
             "age_at_exposure": 6, "source": "backstory", "source_event_id": None},
            {"id": "e2", "exposure_type": "caregiver_absence", "developmental_domains": ["attachment_security"],
             "age_at_exposure": 10, "source": "experience", "source_event_id": "exp-1"},
        ]
        result = accumulate_evidence(exposures)
        pattern = result["reactive_attachment_disorder"]
        types = {e["type"] for e in pattern["supporting_evidence"]}
        assert "persistence" in types


class TestNarrativeEvidence:
    def test_persona_voice_narrative_signal_supports_matching_pattern(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        narration = [{
            "id": "narr-1",
            "attributed_to_persona": True,
            "linguistic_signals": [{"signal_type": "normalization", "evidence_text": "it was normal"}],
            "age": 7,
        }]
        result = accumulate_evidence(exposures, narration_records=narration)
        pattern = result["complex_ptsd"]
        narrative_entries = [e for e in pattern["supporting_evidence"] if e["type"] == "narrative"]
        assert len(narrative_entries) == 1
        assert pattern["evidence_strength"] is not None

    def test_third_party_narrative_does_not_count_as_evidence(self):
        # Per the operator/subject/source rule: only persona_voice narration
        # is evidence of the persona's own psychology.
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        narration = [{
            "id": "narr-1",
            "attributed_to_persona": False,
            "linguistic_signals": [{"signal_type": "normalization", "evidence_text": "it was normal"}],
            "age": 7,
        }]
        result = accumulate_evidence(exposures, narration_records=narration)
        pattern = result["complex_ptsd"]
        assert pattern["supporting_evidence"] == []
        assert pattern["evidence_strength"] is None

    def test_unmapped_signal_type_contributes_nothing(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        narration = [{
            "id": "narr-1",
            "attributed_to_persona": True,
            "linguistic_signals": [{"signal_type": "pronoun_shift", "evidence_text": "..."}],
            "age": 7,
        }]
        result = accumulate_evidence(exposures, narration_records=narration)
        assert result["complex_ptsd"]["supporting_evidence"] == []


class TestProtectiveFactorsAsContradiction:
    def test_overlapping_protective_factor_produces_contradicting_evidence(self):
        exposures = [_exposure("caregiver_absence", age=6, domains=["attachment_security", "stability"], id_="exp-1")]
        protective = [{
            "id": "pf-1",
            "factor_type": "stable_alternate_caregiver",
            "domains_buffered": ["attachment_security", "stability"],
            "active_from_age": 7,
        }]
        result = accumulate_evidence(exposures, protective_factors=protective)
        pattern = result["reactive_attachment_disorder"]
        assert len(pattern["contradicting_evidence"]) == 1
        assert pattern["contradicting_evidence"][0]["type"] == "protective_factor"

    def test_non_overlapping_protective_factor_does_not_contradict(self):
        exposures = [_exposure("caregiver_absence", age=6, domains=["attachment_security"], id_="exp-1")]
        protective = [{
            "id": "pf-1",
            "factor_type": "mastery_experience",
            "domains_buffered": ["competence"],
            "active_from_age": 10,
        }]
        result = accumulate_evidence(exposures, protective_factors=protective)
        assert result["reactive_attachment_disorder"]["contradicting_evidence"] == []

    def test_protective_factor_can_pull_net_strength_to_zero(self):
        exposures = [
            _exposure("caregiver_absence", age=4, domains=["attachment_security"], id_="exp-1"),
            _exposure("caregiver_absence", age=8, domains=["attachment_security"], id_="exp-2"),
        ]
        # One persistence entry of supporting evidence...
        protective = [
            {"id": "pf-1", "factor_type": "stable_alternate_caregiver", "domains_buffered": ["attachment_security"], "active_from_age": 5},
        ]
        result = accumulate_evidence(exposures, protective_factors=protective)
        pattern = result["reactive_attachment_disorder"]
        # 1 supporting (persistence) - 1 contradicting = net 0 at these increments
        assert pattern["evidence_strength"] == 0.0


class TestFunctionalObservationEvidence:
    """
    The Behavior / Known Outcomes channel from docs/MIGRATION_MAP.md's
    Evidence & Source Model, finally wired into the slot left stubbed in
    step 4 ("functional-impact evidence... has no data source yet").
    """

    def test_concerning_observation_matching_pattern_key_supports(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        observations = [{
            "id": "obs-1", "valence": "concerning", "observation_type": "behavioral_pattern",
            "description": "avoids physical contact and becomes tense around his father",
            "developmental_domains": ["emotional_safety"], "candidate_pattern_keys": ["ptsd"],
            "age_observed": 12,
        }]
        result = accumulate_evidence(exposures, functional_observations=observations)
        pattern = result["ptsd"]
        types = {e["type"] for e in pattern["supporting_evidence"]}
        assert "functional_impact" in types
        assert pattern["evidence_strength"] is not None

    def test_concerning_observation_not_matching_pattern_key_has_no_effect(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        observations = [{
            "id": "obs-1", "valence": "concerning", "observation_type": "substance_use_pattern",
            "description": "drinking heavily", "developmental_domains": ["emotional_regulation"],
            "candidate_pattern_keys": ["alcohol_use_disorder"], "age_observed": 20,
        }]
        result = accumulate_evidence(exposures, functional_observations=observations)
        assert result["ptsd"]["supporting_evidence"] == []

    def test_protective_observation_contradicts_by_domain_overlap(self):
        exposures = [_exposure("caregiver_absence", age=6, domains=["attachment_security"], id_="exp-1")]
        observations = [{
            "id": "obs-1", "valence": "protective", "observation_type": "relationship_functioning",
            "description": "maintains close, trusting relationships",
            "developmental_domains": ["attachment_security"], "candidate_pattern_keys": [],
            "age_observed": 20,
        }]
        result = accumulate_evidence(exposures, functional_observations=observations)
        pattern = result["reactive_attachment_disorder"]
        types = {e["type"] for e in pattern["contradicting_evidence"]}
        assert "functional_impact" in types

    def test_current_manifestations_populated_from_concerning_observations(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        observations = [{
            "id": "obs-1", "valence": "concerning", "observation_type": "behavioral_pattern",
            "description": "becomes visibly tense when his father is mentioned",
            "developmental_domains": ["emotional_safety"], "candidate_pattern_keys": ["ptsd"],
            "age_observed": 12,
        }]
        result = accumulate_evidence(exposures, functional_observations=observations)
        assert "becomes visibly tense when his father is mentioned" in result["ptsd"]["current_manifestations"]

    def test_no_observations_leaves_manifestations_empty(self):
        exposures = [_exposure("physical_discipline_or_violence", age=7, id_="exp-1")]
        result = accumulate_evidence(exposures)
        assert result["ptsd"]["current_manifestations"] == []


class TestTierProgression:
    def test_low_evidence_stays_developmental_pattern_tier(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, id_="exp-1"),
            _exposure("caregiver_substance_use", age=9, id_="exp-2"),
        ]
        result = accumulate_evidence(exposures)
        pattern = result["reactive_attachment_disorder"]
        assert pattern["tier"] == "developmental_pattern"

    def test_never_implies_diagnosis_in_tier_naming(self):
        for tier in ("developmental_pattern", "clinical_pattern_resemblance"):
            assert "diagnos" not in tier


class TestProjection:
    def test_null_strength_hypothesis_never_appears_in_projection(self):
        accumulated = {
            "ptsd": {"evidence_strength": None},
            "depression": {"evidence_strength": 0.6},
        }
        markers = project_current_trauma_markers(accumulated)
        assert "ptsd" not in markers
        assert "depression" in markers

    def test_below_threshold_excluded(self):
        accumulated = {"depression": {"evidence_strength": DISPLAY_THRESHOLD - 0.01}}
        assert project_current_trauma_markers(accumulated) == []

    def test_at_threshold_included(self):
        accumulated = {"depression": {"evidence_strength": DISPLAY_THRESHOLD}}
        assert project_current_trauma_markers(accumulated) == ["depression"]

    def test_age_inapplicable_hypothesis_excluded_for_an_adult_even_with_strong_evidence(self):
        # Canonical grounding fix: current_trauma_markers is the third read
        # path (alongside persona_board.py and narrative_service.py) that
        # must never show reactive_attachment_disorder as a live marker for
        # an adult persona - this one feeds Talk's chat context and the
        # narrative's separate trauma_text field, both of which would
        # otherwise still see it even with the other two fixed.
        accumulated = {"reactive_attachment_disorder": {"evidence_strength": 1.0}}
        assert project_current_trauma_markers(accumulated, current_age=40) == []

    def test_age_inapplicable_hypothesis_still_included_for_a_child(self):
        accumulated = {"reactive_attachment_disorder": {"evidence_strength": 1.0}}
        assert project_current_trauma_markers(accumulated, current_age=8) == ["reactive_attachment_disorder"]

    def test_no_current_age_argument_preserves_prior_unfiltered_behavior(self):
        # A caller that hasn't been updated to pass current_age (there
        # should be none left after this fix, but the default itself must
        # not silently change behavior for anything that slips through).
        accumulated = {"reactive_attachment_disorder": {"evidence_strength": 1.0}}
        assert project_current_trauma_markers(accumulated) == ["reactive_attachment_disorder"]

    def test_min_age_scoped_hypothesis_excluded_for_a_child(self):
        accumulated = {"avoidant_personality": {"evidence_strength": 1.0}}
        assert project_current_trauma_markers(accumulated, current_age=10) == []
        assert project_current_trauma_markers(accumulated, current_age=25) == ["avoidant_personality"]


class TestEvidenceStrengthLabel:
    def test_none_is_no_evidence_yet(self):
        assert evidence_strength_label(None) == "no_evidence_yet"

    def test_high_moderate_low_thresholds(self):
        assert evidence_strength_label(0.75) == "high"
        assert evidence_strength_label(0.5) == "moderate"
        assert evidence_strength_label(0.1) == "low"


class TestPersistenceHelper:
    def test_builds_one_row_per_pattern(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, id_="exp-1"),
            _exposure("caregiver_substance_use", age=9, id_="exp-2"),
        ]
        accumulated = accumulate_evidence(exposures)
        rows = build_clinical_pattern_hypothesis_rows("persona-1", accumulated)
        assert len(rows) == len(accumulated)
        assert all(r.persona_id == "persona-1" for r in rows)
        pattern_keys = {r.pattern_key for r in rows}
        assert pattern_keys == set(accumulated.keys())


def _adaptation(strategy, strength, status="emerging", id_="ap-1", first_emerged_age=10):
    return {
        "id": id_,
        "adaptation_strategy": strategy,
        "pattern_name": f"Pattern for {strategy}",
        "status": status,
        "evidence_strength": strength,
        "first_emerged_age": first_emerged_age,
    }


class TestAdaptationPatternEvidencePath:
    """
    Step 12: a varied life history must be able to converge on one clinical
    hypothesis through the adaptation it reinforced, without the same literal
    exposure_type ever recurring. This is the fix for the Emma audit finding.
    """

    def test_adaptation_with_no_earned_strength_does_not_open_a_hypothesis(self):
        # Same "opening is not believing" rule as exposures: one interpretation
        # (strength None) is not enough to put a clinical pattern on the board.
        result = accumulate_evidence([], adaptation_patterns=[_adaptation("self_reliance", None)])
        assert result == {}

    def test_reinforced_adaptation_opens_and_supports_its_linked_hypotheses(self):
        result = accumulate_evidence([], adaptation_patterns=[_adaptation("self_reliance", 0.6)])
        for pattern_key in ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT["self_reliance"]:
            assert pattern_key in result
            assert result[pattern_key]["evidence_strength"] > 0

    def test_stronger_adaptation_yields_stronger_hypothesis_evidence(self):
        weak = accumulate_evidence([], adaptation_patterns=[_adaptation("avoidance", 0.2)])
        strong = accumulate_evidence([], adaptation_patterns=[_adaptation("avoidance", 1.0)])
        assert strong["avoidant_personality"]["evidence_strength"] > weak["avoidant_personality"]["evidence_strength"]

    def test_varied_exposures_converge_via_shared_adaptation(self):
        # The literal Emma shape: every exposure is a DIFFERENT type, so
        # exposure-recurrence alone yields nothing - but they all reinforced
        # one adaptation, and that must be able to carry a hypothesis.
        exposures = [
            _exposure("peer_rejection_or_bullying", age=10, id_="e1"),
            _exposure("separation_or_divorce", age=12, id_="e2"),
            _exposure("emotional_abuse_or_humiliation", age=14, id_="e3"),
        ]
        without = accumulate_evidence(exposures)
        with_adaptation = accumulate_evidence(
            exposures, adaptation_patterns=[_adaptation("avoidance", 0.8, status="established")]
        )
        assert (without.get("avoidant_personality", {}).get("evidence_strength") or 0) < DISPLAY_THRESHOLD
        assert with_adaptation["avoidant_personality"]["evidence_strength"] >= DISPLAY_THRESHOLD

    def test_unmapped_strategy_opens_nothing(self):
        # "humor" is deliberately mapped to no clinical pattern.
        assert ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT["humor"] == []
        assert accumulate_evidence([], adaptation_patterns=[_adaptation("humor", 1.0)]) == {}

    def test_adaptation_opened_hypothesis_records_its_strategy_as_a_precursor(self):
        result = accumulate_evidence([], adaptation_patterns=[_adaptation("perfectionism", 0.6, first_emerged_age=7)])
        state = result["obsessive_compulsive_personality"]
        assert "perfectionism" in state["developmental_precursors"]
        assert state["opened_at_age"] == 7


class TestProtectiveFactorCannotBufferItsOwnEvent:
    """
    Step 12: the same self-buffering bug already fixed in pattern_engine,
    found to exist independently here. A protective factor extracted FROM an
    event must not count as contradicting a hypothesis that same event opened.
    """

    def test_same_event_protective_factor_is_ignored(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, domains=["attachment_security"], id_="e1"),
            _exposure("caregiver_substance_use", age=9, domains=["attachment_security"], id_="e2"),
        ]
        protective = [{
            "id": "pf-1", "factor_type": "friendship",
            "domains_buffered": ["attachment_security"],
            "active_from_age": 5, "source_event_id": "e1",
        }]
        result = accumulate_evidence(exposures, protective_factors=protective)
        assert result["complex_ptsd"]["contradicting_evidence"] == []

    def test_unrelated_event_protective_factor_still_contradicts(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, domains=["attachment_security"], id_="e1"),
            _exposure("caregiver_substance_use", age=9, domains=["attachment_security"], id_="e2"),
        ]
        protective = [{
            "id": "pf-1", "factor_type": "stable_alternate_caregiver",
            "domains_buffered": ["attachment_security"],
            "active_from_age": 6, "source_event_id": "some-other-event",
        }]
        result = accumulate_evidence(exposures, protective_factors=protective)
        assert result["complex_ptsd"]["contradicting_evidence"]

    def test_baseline_protective_factor_with_no_source_still_contradicts(self):
        exposures = [
            _exposure("caregiver_substance_use", age=5, domains=["attachment_security"], id_="e1"),
            _exposure("caregiver_substance_use", age=9, domains=["attachment_security"], id_="e2"),
        ]
        protective = [{
            "id": "pf-1", "factor_type": "temperament",
            "domains_buffered": ["attachment_security"],
            "active_from_age": None, "source_event_id": None,
        }]
        result = accumulate_evidence(exposures, protective_factors=protective)
        assert result["complex_ptsd"]["contradicting_evidence"]


class TestTaxonomyIntegrity:
    def test_all_prior_pattern_keys_exist_in_real_symptom_taxonomy(self):
        from app.utils.symptom_taxonomy import SYMPTOM_TAXONOMY
        referenced = set()
        for patterns in EXPOSURE_HYPOTHESIS_PRIORS.values():
            referenced.update(patterns)
        for patterns in SIGNAL_HYPOTHESIS_SUPPORT.values():
            referenced.update(patterns)
        for patterns in ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT.values():
            referenced.update(patterns)
        missing = referenced - set(SYMPTOM_TAXONOMY.keys())
        assert not missing, f"pattern_keys referenced but not in symptom_taxonomy.py: {missing}"

    def test_every_adaptation_strategy_is_a_real_one(self):
        from app.services.pattern_engine import ADAPTATION_STRATEGIES
        missing = set(ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT.keys()) - set(ADAPTATION_STRATEGIES)
        assert not missing, f"unknown adaptation_strategies referenced: {missing}"

    def test_every_adaptation_strategy_is_covered(self):
        # Every strategy must be an explicit decision - mapped, or explicitly
        # mapped to [] like "humor" - so a newly added strategy can't silently
        # contribute nothing.
        from app.services.pattern_engine import ADAPTATION_STRATEGIES
        uncovered = set(ADAPTATION_STRATEGIES) - set(ADAPTATION_STRATEGY_HYPOTHESIS_SUPPORT.keys())
        assert not uncovered, f"adaptation_strategies with no explicit hypothesis decision: {uncovered}"

    def test_all_exposure_types_referenced_are_real(self):
        from app.services.developmental_exposure_engine import EXPOSURE_TAXONOMY
        missing = set(EXPOSURE_HYPOTHESIS_PRIORS.keys()) - set(EXPOSURE_TAXONOMY.keys())
        assert not missing, f"EXPOSURE_HYPOTHESIS_PRIORS references unknown exposure_types: {missing}"

    def test_all_signal_types_referenced_are_real(self):
        from app.services.self_narration_engine import SIGNAL_TYPES
        missing = set(SIGNAL_HYPOTHESIS_SUPPORT.keys()) - set(SIGNAL_TYPES)
        assert not missing, f"SIGNAL_HYPOTHESIS_SUPPORT references unknown signal_types: {missing}"
