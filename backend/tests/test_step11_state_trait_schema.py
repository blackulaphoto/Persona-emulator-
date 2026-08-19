"""
Tests for Step 11a of docs/MIGRATION_MAP.md: additive schema only for the
State/Trait split - no engine, no route wiring yet. Covers the four new
columns (Persona.current_state, PersonalitySnapshot.state_profile,
Interpretation.state_implications/trait_implications) and the new
DevelopmentalAnalysisResult Pydantic schema + its controlled vocabularies.

Dedicated SQLite file, service-layer only (no app.main) - same pattern as
tests/test_remix_service.py, sidesteps the pre-existing shared-test.db
collision issue documented in docs/MIGRATION_MAP.md.
"""
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, PersonalitySnapshot, Interpretation
from app.schemas.developmental_analysis_schemas import (
    DevelopmentalAnalysisResult,
    StateImplication,
    TraitImplication,
    STATE_VARIABLES,
    TRAIT_NAMES,
)

TEST_DB_URL = "sqlite:///./test_step11_state_trait_schema.db"
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
        name="Michael", baseline_age=6, current_age=6, baseline_gender="male",
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


class TestPersonaCurrentState:
    def test_defaults_to_empty_dict(self, db):
        persona = _make_persona(db)
        assert persona.current_state == {}

    def test_current_personality_unaffected_by_new_column(self, db):
        # State and Trait are genuinely separate columns - writing one must
        # never touch the other.
        persona = _make_persona(db)
        persona.current_state = {"trust": "low"}
        db.commit()
        db.refresh(persona)
        assert persona.current_personality["neuroticism"] == 0.5

    def test_can_be_written_and_persists(self, db):
        persona = _make_persona(db)
        persona.current_state = {"trust": "low", "threat_sensitivity": "elevated"}
        db.commit()
        db.refresh(persona)
        assert persona.current_state == {"trust": "low", "threat_sensitivity": "elevated"}


class TestPersonalitySnapshotStateProfile:
    def test_defaults_to_none(self, db):
        persona = _make_persona(db)
        snapshot = PersonalitySnapshot(
            persona_id=persona.id, age=10,
            personality_profile=persona.current_personality,
            attachment_style="secure", trauma_markers=[],
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        assert snapshot.state_profile is None
        # personality_profile (Trait tier) is untouched by the new column.
        assert snapshot.personality_profile["extraversion"] == 0.5

    def test_can_store_frozen_state_copy(self, db):
        persona = _make_persona(db)
        snapshot = PersonalitySnapshot(
            persona_id=persona.id, age=10,
            personality_profile=persona.current_personality,
            attachment_style="secure", trauma_markers=[],
            state_profile={"trust": "low"},
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        assert snapshot.state_profile == {"trust": "low"}


class TestInterpretationImplicationsColumns:
    def test_default_to_none(self, db):
        persona = _make_persona(db)
        interp = Interpretation(persona_id=persona.id, age_at_event=9)
        db.add(interp)
        db.commit()
        db.refresh(interp)
        assert interp.state_implications is None
        assert interp.trait_implications is None

    def test_can_store_proposals(self, db):
        persona = _make_persona(db)
        interp = Interpretation(
            persona_id=persona.id, age_at_event=9,
            state_implications={"trust": {"direction": "decrease", "magnitude": "high"}},
            trait_implications={"neuroticism": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
        )
        db.add(interp)
        db.commit()
        db.refresh(interp)
        assert interp.state_implications["trust"]["direction"] == "decrease"
        assert interp.trait_implications["neuroticism"]["evidence_strength"] == "low"


class TestDevelopmentalAnalysisResultSchema:
    def test_all_defaults(self):
        result = DevelopmentalAnalysisResult()
        assert result.exposures == []
        assert result.state_changes == {}
        assert result.trait_changes == {}
        assert result.verdict is None

    def test_full_example_validates(self):
        result = DevelopmentalAnalysisResult(
            verdict="This experience reinforced an existing abandonment pattern.",
            developmental_impact={"domains": ["attachment_security", "trust"], "magnitude": "high"},
            state_changes={"trust": {"direction": "decrease", "magnitude": "high"}},
            trait_changes={"neuroticism": {"direction": "increase", "magnitude": "mild", "evidence_strength": "low"}},
            evidence_strength="moderate",
            reasoning="...",
        )
        assert isinstance(result.state_changes["trust"], StateImplication)
        assert isinstance(result.trait_changes["neuroticism"], TraitImplication)
        assert result.developmental_impact.domains == ["attachment_security", "trust"]

    def test_rejects_unknown_state_variable(self):
        with pytest.raises(ValidationError):
            DevelopmentalAnalysisResult(
                state_changes={"extraversion": {"direction": "increase", "magnitude": "mild"}}
            )

    def test_rejects_unknown_trait(self):
        with pytest.raises(ValidationError):
            DevelopmentalAnalysisResult(
                trait_changes={"trust": {"direction": "increase", "magnitude": "mild"}}
            )

    def test_rejects_invalid_magnitude(self):
        with pytest.raises(ValidationError):
            DevelopmentalAnalysisResult(
                state_changes={"trust": {"direction": "increase", "magnitude": "severe"}}
            )

    def test_rejects_invalid_direction(self):
        with pytest.raises(ValidationError):
            DevelopmentalAnalysisResult(
                state_changes={"trust": {"direction": "sideways", "magnitude": "mild"}}
            )

    def test_state_variables_and_trait_names_are_disjoint(self):
        # A guard against accidentally aliasing the two tiers - they must
        # never share a key, or "which tier moved" becomes ambiguous.
        assert set(STATE_VARIABLES).isdisjoint(set(TRAIT_NAMES))
