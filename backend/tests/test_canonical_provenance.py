"""
Tests for app/services/canonical_provenance.py - the eligibility rules that
decide whether an already-persisted DevelopmentalExposure, ProtectiveFactor,
or Interpretation row is allowed to enter downstream psychology
(evidence accumulation, interpretation, pattern accumulation, timeline
replay, the narrative prompt).

Every event-derived row must map to a real experience/intervention ID that
actually belongs to this persona AND carry a real age; every backstory-
derived row must have neither (undated developmental background, not a
fabricated current-age event) - see developmental_pipeline.py's
"source=backstory, age=None" fix and timeline_replay.py's identical
convention. A row that claims a source_event_id which isn't in the
persona's actual set of experience/intervention IDs must never be trusted,
regardless of what age it claims - that's exactly what would let a
cross-persona or otherwise orphaned row silently contribute evidence.
"""
from app.services.canonical_provenance import (
    exposure_has_provenance,
    protective_factor_has_provenance,
    interpretation_has_provenance,
)


def _exposure(source, source_event_id=None, age_at_exposure=None):
    return {"source": source, "source_event_id": source_event_id, "age_at_exposure": age_at_exposure}


class TestExposureProvenance:
    def test_backstory_exposure_with_no_id_and_no_age_is_valid(self):
        assert exposure_has_provenance(_exposure("backstory")) is True

    def test_backstory_exposure_with_an_age_is_invalid(self):
        # Exactly the bug developmental_pipeline.py's age=None fix targets:
        # undated background must never carry a fabricated current-age.
        assert exposure_has_provenance(_exposure("backstory", age_at_exposure=40)) is False

    def test_backstory_exposure_with_a_source_event_id_is_invalid(self):
        assert exposure_has_provenance(_exposure("backstory", source_event_id="exp-1")) is False

    def test_experience_exposure_with_valid_id_and_age_is_valid(self):
        assert exposure_has_provenance(
            _exposure("experience", source_event_id="exp-1", age_at_exposure=40),
            valid_event_ids={"exp-1"},
        ) is True

    def test_experience_exposure_with_id_not_belonging_to_this_persona_is_invalid(self):
        # The exact protection against a stale/orphaned/cross-persona row
        # silently surviving a rebuild.
        assert exposure_has_provenance(
            _exposure("experience", source_event_id="exp-999", age_at_exposure=40),
            valid_event_ids={"exp-1"},
        ) is False

    def test_experience_exposure_with_no_age_is_invalid(self):
        assert exposure_has_provenance(
            _exposure("experience", source_event_id="exp-1", age_at_exposure=None),
            valid_event_ids={"exp-1"},
        ) is False

    def test_experience_exposure_with_no_source_event_id_is_invalid(self):
        assert exposure_has_provenance(
            _exposure("experience", source_event_id=None, age_at_exposure=40),
        ) is False

    def test_intervention_source_follows_the_same_rule_as_experience(self):
        assert exposure_has_provenance(
            _exposure("intervention", source_event_id="int-1", age_at_exposure=40),
            valid_event_ids={"int-1"},
        ) is True
        assert exposure_has_provenance(
            _exposure("intervention", source_event_id="int-999", age_at_exposure=40),
            valid_event_ids={"int-1"},
        ) is False

    def test_no_valid_id_set_provided_skips_membership_check(self):
        # Callers that haven't loaded a valid-ID set (or don't need to)
        # still get the shape checks - membership is opt-in via
        # valid_event_ids, not silently bypassed by omission elsewhere.
        assert exposure_has_provenance(_exposure("experience", source_event_id="exp-1", age_at_exposure=40)) is True

    def test_unknown_source_value_is_invalid(self):
        assert exposure_has_provenance(_exposure("something_else")) is False

    def test_works_with_orm_style_attribute_access(self):
        class FakeRow:
            source = "backstory"
            source_event_id = None
            age_at_exposure = None
        assert exposure_has_provenance(FakeRow()) is True


class TestProtectiveFactorProvenance:
    def test_backstory_convention_no_id_no_age_is_valid(self):
        assert protective_factor_has_provenance({"source_event_id": None, "active_from_age": None}) is True

    def test_backstory_convention_no_id_but_has_age_is_invalid(self):
        assert protective_factor_has_provenance({"source_event_id": None, "active_from_age": 40}) is False

    def test_experience_sourced_factor_needs_valid_id_and_age(self):
        assert protective_factor_has_provenance(
            {"source_event_id": "exp-1", "active_from_age": 12}, valid_event_ids={"exp-1"}
        ) is True
        assert protective_factor_has_provenance(
            {"source_event_id": "exp-999", "active_from_age": 12}, valid_event_ids={"exp-1"}
        ) is False

    def test_experience_sourced_factor_with_no_age_is_invalid(self):
        assert protective_factor_has_provenance(
            {"source_event_id": "exp-1", "active_from_age": None}, valid_event_ids={"exp-1"}
        ) is False


class TestInterpretationProvenance:
    def test_backstory_interpretation_no_id_no_age_is_valid(self):
        assert interpretation_has_provenance({"source_event_id": None, "age_at_event": None}) is True

    def test_backstory_interpretation_with_fabricated_age_is_invalid(self):
        assert interpretation_has_provenance({"source_event_id": None, "age_at_event": 40}) is False

    def test_experience_interpretation_needs_valid_id_and_age(self):
        assert interpretation_has_provenance(
            {"source_event_id": "exp-1", "age_at_event": 40}, valid_event_ids={"exp-1"}
        ) is True

    def test_experience_interpretation_citing_a_nonexistent_event_is_invalid(self):
        # "Pattern emergence cannot cite a nonexistent event" - the exact
        # requirement this guards, at the interpretation layer specifically
        # (accumulate_patterns groups interpretations into pattern history,
        # so an interpretation with fake provenance would otherwise still
        # produce a pattern reinforcement entry citing a fabricated event).
        assert interpretation_has_provenance(
            {"source_event_id": "exp-does-not-exist", "age_at_event": 40}, valid_event_ids={"exp-1"}
        ) is False
