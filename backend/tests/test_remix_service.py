"""
Tests for step 9 of docs/MIGRATION_MAP.md: remix_service.py diffing
patterns and adaptations, not just Big Five deltas.

Uses a dedicated SQLite file (test_remix_service.db), not app.main or the
shared test.db several pre-existing API test files point at - those files
collide with each other via a shared autouse create_all/drop_all fixture
against the same physical file, a pre-existing, unrelated issue (see
docs/MIGRATION_MAP.md's "Known pre-existing issue" note). This file only
needs the service layer directly, not the FastAPI app, so it sidesteps that
entirely.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, AdaptationPattern, ClinicalPatternHypothesis
from app.services.remix_service import (
    create_timeline_snapshot,
    compare_snapshots,
    get_remix_suggestions_for_persona,
    _diff_pattern_lists,
    _diff_state_profile,
)

TEST_DB_URL = "sqlite:///./test_remix_service.db"
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


def _make_persona(db, **overrides):
    defaults = dict(
        name="Michael", baseline_age=6, current_age=32, baseline_gender="male",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.4, "extraversion": 0.4, "agreeableness": 0.5, "neuroticism": 0.7},
        current_attachment_style="insecure-anxious", current_trauma_markers=[],
        user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


class TestDiffPatternListsPureFunction:
    def test_new_pattern_detected(self):
        result = _diff_pattern_lists(
            [],
            [{"adaptation_strategy": "avoidance", "pattern_name": "Leave Before You're Left", "status": "emerging", "evidence_strength": None}],
            "adaptation_strategy",
        )
        assert len(result["new"]) == 1
        assert result["new"][0]["pattern_name"] == "Leave Before You're Left"

    def test_resolved_pattern_detected(self):
        result = _diff_pattern_lists(
            [{"adaptation_strategy": "avoidance", "pattern_name": "X", "status": "established", "evidence_strength": 0.6}],
            [],
            "adaptation_strategy",
        )
        assert len(result["resolved"]) == 1

    def test_strengthened_pattern_detected(self):
        result = _diff_pattern_lists(
            [{"adaptation_strategy": "avoidance", "pattern_name": "X", "status": "emerging", "evidence_strength": 0.2}],
            [{"adaptation_strategy": "avoidance", "pattern_name": "X", "status": "established", "evidence_strength": 0.6}],
            "adaptation_strategy",
        )
        assert len(result["changed"]) == 1
        assert result["changed"][0]["evidence_strength_change"] == pytest.approx(0.4)

    def test_unchanged_pattern_detected(self):
        entry = {"adaptation_strategy": "avoidance", "pattern_name": "X", "status": "established", "evidence_strength": 0.6}
        result = _diff_pattern_lists([entry], [dict(entry)], "adaptation_strategy")
        assert result["unchanged"] == ["avoidance"]
        assert result["changed"] == []

    def test_none_inputs_handled(self):
        assert _diff_pattern_lists(None, None, "pattern_key") == {"new": [], "resolved": [], "changed": [], "unchanged": []}


class TestCreateTimelineSnapshotCapturesPatterns:
    def test_snapshot_freezes_current_adaptation_patterns(self, db):
        persona = _make_persona(db)
        db.add(AdaptationPattern(
            persona_id=persona.id, pattern_name="Leave Before You're Left",
            adaptation_strategy="avoidance", status="established", evidence_strength=0.7,
        ))
        db.commit()

        snapshot = create_timeline_snapshot(db, persona.id, label="With pattern")
        assert snapshot.adaptation_patterns_snapshot is not None
        assert snapshot.adaptation_patterns_snapshot[0]["pattern_name"] == "Leave Before You're Left"
        assert snapshot.adaptation_patterns_snapshot[0]["evidence_strength"] == 0.7

    def test_snapshot_freezes_current_clinical_pattern_hypotheses(self, db):
        persona = _make_persona(db)
        db.add(ClinicalPatternHypothesis(
            persona_id=persona.id, pattern_key="complex_ptsd", tier="developmental_pattern", evidence_strength=0.3,
        ))
        db.commit()

        snapshot = create_timeline_snapshot(db, persona.id, label="With hypothesis")
        assert snapshot.clinical_pattern_hypotheses_snapshot[0]["pattern_key"] == "complex_ptsd"

    def test_snapshot_with_no_patterns_is_still_valid(self, db):
        # The current live-system default: no patterns exist yet.
        persona = _make_persona(db)
        snapshot = create_timeline_snapshot(db, persona.id, label="No patterns")
        assert snapshot.adaptation_patterns_snapshot is None
        assert snapshot.clinical_pattern_hypotheses_snapshot is None

    def test_snapshot_is_frozen_not_a_live_reference(self, db):
        # Later changes to the live AdaptationPattern row must not retroactively
        # alter an already-taken snapshot.
        persona = _make_persona(db)
        pattern = AdaptationPattern(
            persona_id=persona.id, pattern_name="X", adaptation_strategy="avoidance",
            status="emerging", evidence_strength=0.2,
        )
        db.add(pattern)
        db.commit()

        snapshot = create_timeline_snapshot(db, persona.id, label="Before strengthening")

        pattern.status = "established"
        pattern.evidence_strength = 0.8
        db.commit()

        assert snapshot.adaptation_patterns_snapshot[0]["status"] == "emerging"
        assert snapshot.adaptation_patterns_snapshot[0]["evidence_strength"] == 0.2


class TestCompareSnapshotsDiffsPatterns:
    def test_comparison_includes_new_pattern_and_summary_line(self, db):
        persona = _make_persona(db)
        snap_1 = create_timeline_snapshot(db, persona.id, label="Original")

        db.add(AdaptationPattern(
            persona_id=persona.id, pattern_name="Leave Before You're Left",
            adaptation_strategy="avoidance", status="emerging", evidence_strength=None,
        ))
        db.commit()
        snap_2 = create_timeline_snapshot(db, persona.id, label="Remix")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert "adaptation_pattern_differences" in comparison
        assert len(comparison["adaptation_pattern_differences"]["new"]) == 1
        assert "Leave Before You're Left" in comparison["summary"]

    def test_comparison_with_no_patterns_on_either_side_omits_pattern_summary(self, db):
        persona = _make_persona(db)
        snap_1 = create_timeline_snapshot(db, persona.id, label="A")
        snap_2 = create_timeline_snapshot(db, persona.id, label="B")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert comparison["adaptation_pattern_differences"] == {"new": [], "resolved": [], "changed": [], "unchanged": []}
        assert "pattern" not in comparison["summary"].lower()

    def test_strengthened_pattern_reflected_in_summary(self, db):
        persona = _make_persona(db)
        pattern = AdaptationPattern(
            persona_id=persona.id, pattern_name="X", adaptation_strategy="avoidance",
            status="emerging", evidence_strength=0.2,
        )
        db.add(pattern)
        db.commit()
        snap_1 = create_timeline_snapshot(db, persona.id, label="Weak")

        pattern.status = "established"
        pattern.evidence_strength = 0.7
        db.commit()
        snap_2 = create_timeline_snapshot(db, persona.id, label="Strong")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert "strengthened" in comparison["summary"]


class TestDiffStateProfilePureFunction:
    """Step 11f: _diff_state_profile, the State-tier counterpart to personality_differences."""

    def test_shared_key_diffed_normally(self):
        result = _diff_state_profile({"trust": 0.3}, {"trust": 0.6})
        assert result["trust"]["difference"] == pytest.approx(0.3)
        assert result["trust"]["change_direction"] == "increased"

    def test_unchanged_value(self):
        result = _diff_state_profile({"trust": 0.5}, {"trust": 0.5})
        assert result["trust"]["change_direction"] == "unchanged"
        assert result["trust"]["difference"] == 0

    def test_key_only_in_second_snapshot_is_newly_tracked(self):
        result = _diff_state_profile({}, {"mood": 0.4})
        assert result["mood"]["difference"] is None
        assert result["mood"]["change_direction"] == "newly_tracked"
        assert result["mood"]["snapshot_1"] is None

    def test_key_only_in_first_snapshot_is_no_longer_tracked(self):
        result = _diff_state_profile({"mood": 0.4}, {})
        assert result["mood"]["change_direction"] == "no_longer_tracked"
        assert result["mood"]["snapshot_2"] is None

    def test_none_inputs_handled(self):
        assert _diff_state_profile(None, None) == {}


class TestCreateTimelineSnapshotCapturesStateProfile:
    def test_snapshot_with_no_state_movement_is_none(self, db):
        persona = _make_persona(db)
        snapshot = create_timeline_snapshot(db, persona.id, label="No state yet")
        assert snapshot.state_profile_snapshot is None

    def test_snapshot_freezes_current_state(self, db):
        persona = _make_persona(db, current_state={"trust": 0.3, "mood": 0.6})
        snapshot = create_timeline_snapshot(db, persona.id, label="With state")
        assert snapshot.state_profile_snapshot == {"trust": 0.3, "mood": 0.6}

    def test_snapshot_is_frozen_not_a_live_reference(self, db):
        persona = _make_persona(db, current_state={"trust": 0.3})
        snapshot = create_timeline_snapshot(db, persona.id, label="Before change")

        persona.current_state = {"trust": 0.9}
        db.commit()

        assert snapshot.state_profile_snapshot == {"trust": 0.3}


class TestCompareSnapshotsDiffsStateProfile:
    def test_comparison_includes_state_differences_and_summary_line(self, db):
        persona = _make_persona(db, current_state={"trust": 0.3})
        snap_1 = create_timeline_snapshot(db, persona.id, label="Original")

        persona.current_state = {"trust": 0.7}
        db.commit()
        snap_2 = create_timeline_snapshot(db, persona.id, label="Remix")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert comparison["state_differences"]["trust"]["difference"] == pytest.approx(0.4)
        assert "State changes:" in comparison["summary"]
        assert "trust increased" in comparison["summary"]

    def test_comparison_includes_state_blocks_per_snapshot(self, db):
        persona = _make_persona(db, current_state={"trust": 0.3})
        snap_1 = create_timeline_snapshot(db, persona.id, label="Original")
        snap_2 = create_timeline_snapshot(db, persona.id, label="Remix")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert comparison["snapshot_1"]["state"] == {"trust": 0.3}
        assert comparison["snapshot_2"]["state"] == {"trust": 0.3}

    def test_small_state_change_below_threshold_omitted_from_summary(self, db):
        persona = _make_persona(db, current_state={"trust": 0.5})
        snap_1 = create_timeline_snapshot(db, persona.id, label="Original")

        persona.current_state = {"trust": 0.55}
        db.commit()
        snap_2 = create_timeline_snapshot(db, persona.id, label="Remix")

        comparison = compare_snapshots(db, snap_1.id, snap_2.id)
        assert "State changes:" not in comparison["summary"]


class TestRemixSuggestionsReferenceDominantPattern:
    def test_no_established_pattern_no_pattern_suggestion(self, db):
        persona = _make_persona(db, current_age=15)
        suggestions = get_remix_suggestions_for_persona(db, persona.id)
        assert not any("Interrupt" in s["title"] for s in suggestions)

    def test_established_pattern_produces_targeted_suggestion(self, db):
        persona = _make_persona(db, current_age=15)
        db.add(AdaptationPattern(
            persona_id=persona.id, pattern_name="Leave Before You're Left",
            adaptation_strategy="avoidance", status="established", evidence_strength=0.8,
            first_emerged_age=6,
        ))
        db.commit()

        suggestions = get_remix_suggestions_for_persona(db, persona.id)
        pattern_suggestion = next(s for s in suggestions if "Interrupt" in s["title"])
        assert "Leave Before You're Left" in pattern_suggestion["title"]
        assert "age 6" in pattern_suggestion["changes"][0]

    def test_emerging_pattern_not_yet_suggested(self, db):
        # Only "established" patterns are targeted directly - an emerging
        # one hasn't earned that level of attention yet.
        persona = _make_persona(db, current_age=15)
        db.add(AdaptationPattern(
            persona_id=persona.id, pattern_name="X", adaptation_strategy="avoidance",
            status="emerging", evidence_strength=None,
        ))
        db.commit()

        suggestions = get_remix_suggestions_for_persona(db, persona.id)
        assert not any("Interrupt" in s["title"] for s in suggestions)
