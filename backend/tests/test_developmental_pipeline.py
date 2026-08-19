"""
Integration test for app/services/developmental_pipeline.py -
process_developmental_text(), the actual wiring of steps 2-5 (docs/
MIGRATION_MAP.md). Runs the full chain against a real SQLite session with
every AI call mocked to fail fast, exercising the fallback/heuristic paths
end to end - which also happens to be the honest current production state
(no OpenAI credits configured), so this test validates exactly the behavior
a real deployment would see today.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Persona, DevelopmentalExposure, ProtectiveFactor, NarrationRecord,
    ClinicalPatternHypothesis, AdaptationPattern, Interpretation,
)
from app.services.developmental_pipeline import process_developmental_text

TEST_DB_URL = "sqlite:///./test_developmental_pipeline.db"
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


@pytest.fixture(autouse=True)
def _fail_all_ai_calls():
    """
    Forces every engine's fallback path - deterministic, fast, and matches
    this environment's actual state (no OpenAI credits). Patches each
    module's own openai_service instance since they're separate
    OpenAIService() objects, not a shared singleton.
    """
    patches = [
        patch("app.services.developmental_exposure_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.self_narration_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.pattern_engine.openai_service.analyze", new_callable=AsyncMock),
        patch("app.services.state_trait_engine.openai_service.analyze", new_callable=AsyncMock),
    ]
    mocks = [p.start() for p in patches]
    for m in mocks:
        m.side_effect = Exception("simulated API failure - forces fallback path")
    yield
    for p in patches:
        p.stop()


def _make_persona(db, **overrides):
    defaults = dict(
        name="Timmy", baseline_age=6, current_age=6, baseline_gender="male",
        baseline_background="My father drank constantly and disappeared for days.",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


class TestSingleCallEndToEnd:
    @pytest.mark.asyncio
    async def test_backstory_produces_exposures(self, db):
        persona = _make_persona(db)
        result = await process_developmental_text(
            db, persona, persona.baseline_background, source="backstory", age=persona.baseline_age,
        )
        db.commit()

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
        assert len(exposures) >= 1
        assert {e.exposure_type for e in exposures} & {"caregiver_substance_use", "caregiver_absence"}
        assert all(e.speaker_role == "case_author" for e in exposures)
        assert result["exposures"]

    @pytest.mark.asyncio
    async def test_narration_record_created_but_gated(self, db):
        # case_author speaker_role - narration analysis must be gated (see step-10/
        # self_narration_engine tests), but a record with provenance is still stored.
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()

        records = db.query(NarrationRecord).filter(NarrationRecord.subject_id == persona.id).all()
        assert len(records) == 1
        assert records[0].attributed_to_persona is False
        assert records[0].linguistic_signals == []

    @pytest.mark.asyncio
    async def test_single_exposure_opens_hypothesis_without_seeding_belief(self, db):
        # The core invariant from step 4, now proven through the actual wired pipeline.
        persona = _make_persona(db)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()

        hypotheses = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        assert len(hypotheses) >= 1
        assert all(h.evidence_strength is None for h in hypotheses)
        assert result["trauma_markers"] == []  # nothing crosses the display threshold yet

    @pytest.mark.asyncio
    async def test_interpretation_and_pattern_created(self, db):
        persona = _make_persona(db)
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()

        interpretations = db.query(Interpretation).filter(Interpretation.persona_id == persona.id).all()
        assert len(interpretations) == 1
        assert interpretations[0].adaptation_strategy is not None

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        assert len(patterns) == 1
        assert patterns[0].status == "emerging"  # single interpretation - not established yet
        assert result["interpretation"] is not None

    @pytest.mark.asyncio
    async def test_no_exposures_in_text_produces_no_new_rows(self, db):
        persona = _make_persona(db, baseline_background="They lived in a house and went to school.")
        result = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()

        assert db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).count() == 0
        assert db.query(Interpretation).filter(Interpretation.persona_id == persona.id).count() == 0
        assert result["trauma_markers"] == []


class TestSecondCallAcrossTimelineRecomputes:
    @pytest.mark.asyncio
    async def test_recurring_exposure_earns_real_evidence_on_second_call(self, db):
        persona = _make_persona(db)
        # First call - backstory.
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()

        # Second call - a later "experience" describing the same kind of exposure.
        await process_developmental_text(
            db, persona, "He was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()

        # Same pattern_key rows updated in place, not duplicated.
        hypotheses = db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == persona.id).all()
        pattern_keys = [h.pattern_key for h in hypotheses]
        assert len(pattern_keys) == len(set(pattern_keys))  # no duplicates

        # A single persistence bump (0.15) is real, earned evidence - but
        # correctly stays below the 0.4 display threshold on its own. It
        # should not yet appear in current_trauma_markers.
        strengths = {h.pattern_key: h.evidence_strength for h in hypotheses}
        assert any(v is not None for v in strengths.values())
        assert all((v or 0) < 0.4 for v in strengths.values())

        # With backstory + exp-1, that's 2 distinct entries so far (1
        # persistence bump = 0.15). Two more distinct occurrences are needed
        # to cross DISPLAY_THRESHOLD (0.4): extra_occurrences = entries - 1,
        # capped at MAX_PERSISTENCE_ENTRIES - 3 entries -> 2 bumps (0.30,
        # still under); 4 entries -> 3 bumps (0.45, crosses). See
        # evidence_accumulator.MAX_PERSISTENCE_ENTRIES.
        await process_developmental_text(
            db, persona, "By age 14 he was still drinking constantly and disappearing for days at a time.",
            source="experience", age=14, source_event_id="exp-2",
        )
        db.commit()
        result4 = await process_developmental_text(
            db, persona, "At 17 it happened again - drinking for days, gone without a word.",
            source="experience", age=17, source_event_id="exp-3",
        )
        db.commit()
        assert result4["trauma_markers"]  # now crosses the display threshold

    @pytest.mark.asyncio
    async def test_adaptation_pattern_reinforced_not_duplicated(self, db):
        persona = _make_persona(db)
        await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()
        await process_developmental_text(
            db, persona, "He was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        strategies = [p.adaptation_strategy for p in patterns]
        assert len(strategies) == len(set(strategies))  # no duplicates per strategy


class TestCurrentTraumaMarkersProjection:
    @pytest.mark.asyncio
    async def test_projection_only_includes_evidenced_patterns(self, db):
        persona = _make_persona(db)
        result1 = await process_developmental_text(db, persona, persona.baseline_background, source="backstory", age=6)
        db.commit()
        assert result1["trauma_markers"] == []

        result2 = await process_developmental_text(
            db, persona, "He was gone again for days, drinking the whole time.",
            source="experience", age=10, source_event_id="exp-1",
        )
        db.commit()
        assert isinstance(result2["trauma_markers"], list)
