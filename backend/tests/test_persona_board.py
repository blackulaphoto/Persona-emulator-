"""
Tests for app/services/persona_board.py (docs/MIGRATION_MAP.md, Step 12).

The board projection is what makes the engine's reasoning visible. The audit
this step came from found the engine was inferring correctly while the board
showed "All is well right now", because adaptations and clinical hypotheses
had no API surface at all. These tests pin the projection rules that fix
that - especially the two that are easy to regress back into silence:
  - hypotheses surface BELOW evidence_accumulator.DISPLAY_THRESHOLD,
  - but a hypothesis with no evidence at all still does not surface.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, AdaptationPattern, ClinicalPatternHypothesis
from app.services.evidence_accumulator import DISPLAY_THRESHOLD
from app.services.persona_board import (
    adaptation_pattern_summaries,
    clinical_pattern_hypothesis_summaries,
    board_sections_for_persona,
)

TEST_DB_URL = "sqlite:///./test_persona_board.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _persona(db):
    persona = Persona(
        name="Board Test", baseline_age=10, current_age=20, baseline_gender="female",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
                             "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], current_state={},
        user_id="user-1",
    )
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


def _pattern(db, persona_id, strategy, strength, status="emerging", name=None):
    row = AdaptationPattern(
        persona_id=persona_id, pattern_name=name or f"Pattern {strategy}",
        adaptation_strategy=strategy, status=status, evidence_strength=strength,
        supporting_experience_ids=[], current_manifestations=[], first_emerged_age=10,
    )
    db.add(row)
    db.commit()
    return row


def _hypothesis(db, persona_id, key, strength, previous=None, status="open"):
    row = ClinicalPatternHypothesis(
        persona_id=persona_id, pattern_key=key, tier="developmental_pattern",
        evidence_strength=strength, previous_evidence_strength=previous, status=status,
        supporting_evidence=[], contradicting_evidence=[],
        developmental_precursors=["avoidance"], current_manifestations=[], opened_at_age=12,
    )
    db.add(row)
    db.commit()
    return row


class TestAdaptationPatternSummaries:
    def test_empty_persona_has_no_patterns(self, db):
        persona = _persona(db)
        assert adaptation_pattern_summaries(db, persona.id) == []

    def test_pattern_with_no_strength_still_surfaces(self, db):
        # Watching an adaptation emerge is the product's point - status
        # already communicates how provisional it is.
        persona = _persona(db)
        _pattern(db, persona.id, "avoidance", None)
        result = adaptation_pattern_summaries(db, persona.id)
        assert len(result) == 1
        assert result[0]["status"] == "emerging"
        assert result[0]["confidence"] is None

    def test_confidence_is_whole_percent(self, db):
        persona = _persona(db)
        _pattern(db, persona.id, "avoidance", 0.6)
        assert adaptation_pattern_summaries(db, persona.id)[0]["confidence"] == 60

    def test_sorted_strongest_first(self, db):
        persona = _persona(db)
        _pattern(db, persona.id, "avoidance", 0.2)
        _pattern(db, persona.id, "hypervigilance", 0.8)
        _pattern(db, persona.id, "perfectionism", None)
        result = adaptation_pattern_summaries(db, persona.id)
        assert [p["adaptation_strategy"] for p in result] == ["hypervigilance", "avoidance", "perfectionism"]


class TestClinicalPatternHypothesisSummaries:
    def test_surfaces_below_display_threshold(self, db):
        # The headline Step 12 behavior: the user gets to see the engine
        # considering something at 28%, not only conclusions it already
        # considers settled. current_trauma_markers stays gated; this does not.
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.28)
        result = clinical_pattern_hypothesis_summaries(db, persona.id)
        assert len(result) == 1
        assert result[0]["confidence"] == 28
        assert result[0]["evidence_strength"] < DISPLAY_THRESHOLD

    def test_zero_and_null_evidence_do_not_surface(self, db):
        # "Opened for investigation" is not "we have something to say" -
        # showing every opened prior would bury the real signal.
        persona = _persona(db)
        _hypothesis(db, persona.id, "ptsd", 0.0)
        _hypothesis(db, persona.id, "depression", None)
        assert clinical_pattern_hypothesis_summaries(db, persona.id) == []

    def test_dismissed_hypotheses_excluded(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "ptsd", 0.5, status="dismissed")
        assert clinical_pattern_hypothesis_summaries(db, persona.id) == []

    def test_direction_strengthening(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.47, previous=0.28)
        assert clinical_pattern_hypothesis_summaries(db, persona.id)[0]["direction"] == "strengthening"

    def test_direction_weakening(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.35, previous=0.47)
        assert clinical_pattern_hypothesis_summaries(db, persona.id)[0]["direction"] == "weakening"

    def test_direction_none_without_a_prior_value(self, db):
        # A hypothesis computed only once is emerging, not "stable" -
        # claiming stability would overstate what we know.
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.3, previous=None)
        assert clinical_pattern_hypothesis_summaries(db, persona.id)[0]["direction"] is None

    def test_sorted_strongest_first(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.2)
        _hypothesis(db, persona.id, "complex_ptsd", 0.7)
        result = clinical_pattern_hypothesis_summaries(db, persona.id)
        assert [h["pattern_key"] for h in result] == ["complex_ptsd", "avoidant_personality"]

    def test_current_age_none_applies_no_age_gating(self, db):
        # The caller-guard default: an unscoped call (current_age not
        # supplied) must not silently suppress every age-scoped hypothesis -
        # this is the exact wiring gap that let a personality-disorder
        # hypothesis vanish from the board at the old current_age=0 default.
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.3)
        result = clinical_pattern_hypothesis_summaries(db, persona.id)
        assert len(result) == 1
        assert result[0]["applicability"] == {
            "currently_applicable": True, "historical_developmental_only": False,
            "historical_label": None, "reason": None,
        }

    def test_age_scoped_hypothesis_hidden_from_current_list_for_a_child(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.3)
        assert clinical_pattern_hypothesis_summaries(db, persona.id, current_age=10) == []

    def test_age_scoped_hypothesis_shown_for_an_adult_with_historical_framing(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "avoidant_personality", 0.3)
        result = clinical_pattern_hypothesis_summaries(db, persona.id, current_age=25)
        assert len(result) == 1
        assert result[0]["applicability"]["currently_applicable"] is True

    def test_reactive_attachment_disorder_hidden_for_an_adult_current_age(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "reactive_attachment_disorder", 0.3)
        result = clinical_pattern_hypothesis_summaries(db, persona.id, current_age=40)
        assert result == []

    def test_reactive_attachment_disorder_shown_for_a_child_current_age(self, db):
        persona = _persona(db)
        _hypothesis(db, persona.id, "reactive_attachment_disorder", 0.3)
        result = clinical_pattern_hypothesis_summaries(db, persona.id, current_age=8)
        assert len(result) == 1
        assert result[0]["applicability"]["currently_applicable"] is True


class TestBoardSections:
    def test_returns_both_sections_keyed_for_persona_response(self, db):
        persona = _persona(db)
        _pattern(db, persona.id, "avoidance", 0.4)
        _hypothesis(db, persona.id, "avoidant_personality", 0.3)
        sections = board_sections_for_persona(db, persona.id)
        assert set(sections) == {"adaptation_patterns", "clinical_pattern_hypotheses"}
        assert len(sections["adaptation_patterns"]) == 1
        assert len(sections["clinical_pattern_hypotheses"]) == 1

    def test_other_personas_state_never_leaks(self, db):
        persona_a = _persona(db)
        persona_b = _persona(db)
        _pattern(db, persona_a.id, "avoidance", 0.4)
        _hypothesis(db, persona_a.id, "avoidant_personality", 0.3)
        sections = board_sections_for_persona(db, persona_b.id)
        assert sections == {"adaptation_patterns": [], "clinical_pattern_hypotheses": []}
