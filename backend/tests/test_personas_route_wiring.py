"""
Integration tests for the developmental pipeline wired into
app/api/routes/personas.py::create_persona (docs/MIGRATION_MAP.md, "wiring
steps 2-5 into routes"). Calls the route function directly with explicit
user_id/db args, dedicated SQLite file, no app.main - matching
tests/test_chat_route.py's pattern. Every AI call is mocked to fail fast,
forcing the fallback/heuristic paths - the honest current production state
(no OpenAI credits configured).
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Persona, PersonaSymptom, DevelopmentalExposure, Interpretation,
    AdaptationPattern, ClinicalPatternHypothesis,
)
from app.api.routes.personas import create_persona
from app.schemas import PersonaCreate

TEST_DB_URL = "sqlite:///./test_personas_route_wiring.db"
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
    patches = [
        patch("app.utils.foundational_baseline.openai_service.analyze", new_callable=AsyncMock),
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


def _payload(**overrides):
    defaults = dict(
        name="Timmy", baseline_age=6, baseline_gender="male",
        baseline_background="My father drank constantly and disappeared for days.",
    )
    defaults.update(overrides)
    return PersonaCreate(**defaults)


class TestPipelineActuallyRuns:
    @pytest.mark.asyncio
    async def test_creates_developmental_exposures(self, db):
        response = await create_persona(_payload(), user_id="user-1", db=db)

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == response.id).all()
        assert len(exposures) >= 1
        assert all(e.speaker_role == "case_author" for e in exposures)
        assert all(e.source == "backstory" for e in exposures)

    @pytest.mark.asyncio
    async def test_creates_interpretation_and_pattern(self, db):
        response = await create_persona(_payload(), user_id="user-1", db=db)

        assert db.query(Interpretation).filter(Interpretation.persona_id == response.id).count() == 1
        assert db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == response.id).count() == 1

    @pytest.mark.asyncio
    async def test_creates_clinical_pattern_hypotheses(self, db):
        response = await create_persona(_payload(), user_id="user-1", db=db)
        assert db.query(ClinicalPatternHypothesis).filter(ClinicalPatternHypothesis.persona_id == response.id).count() >= 1

    @pytest.mark.asyncio
    async def test_trauma_markers_come_from_projection_not_keyword_mapper(self, db):
        # A single exposure never seeds a starting belief - current_trauma_markers
        # should be empty right after creation, not populated with a keyword hit.
        response = await create_persona(_payload(), user_id="user-1", db=db)
        assert response.current_trauma_markers == []

    @pytest.mark.asyncio
    async def test_no_personasymptom_rows_created_anymore(self, db):
        # The old backstory_symptom_mapper.py path is fully retired from this route.
        response = await create_persona(_payload(), user_id="user-1", db=db)
        assert db.query(PersonaSymptom).filter(PersonaSymptom.persona_id == response.id).count() == 0

    @pytest.mark.asyncio
    async def test_neutral_backstory_produces_no_exposures(self, db):
        response = await create_persona(
            _payload(baseline_background="They lived in a house and went to school."),
            user_id="user-1", db=db,
        )
        assert db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == response.id).count() == 0
        assert response.current_trauma_markers == []

    @pytest.mark.asyncio
    async def test_current_state_populated_from_backstory(self, db):
        # Step 11: State tier applies unconditionally as soon as there's a
        # real interpretation - unlike Trait, it doesn't need reinforcement.
        response = await create_persona(_payload(), user_id="user-1", db=db)
        persona = db.query(Persona).filter(Persona.id == response.id).first()
        assert persona.current_state != {}

    @pytest.mark.asyncio
    async def test_current_personality_untouched_by_a_single_backstory(self, db):
        # Step 11: Trait gate requires an "established" pattern - a single
        # backstory only ever produces one interpretation ("emerging").
        response = await create_persona(_payload(), user_id="user-1", db=db)
        assert response.current_personality == {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5,
        }

    @pytest.mark.asyncio
    async def test_current_state_surfaced_in_api_response(self, db):
        # Step 11f: current_state has been written to the DB since Step 11c
        # but PersonaResponse never exposed it until now.
        response = await create_persona(_payload(), user_id="user-1", db=db)
        persona = db.query(Persona).filter(Persona.id == response.id).first()
        assert response.current_state == persona.current_state
        assert response.current_state != {}


class TestPipelineFailureDoesNotBlockPersonaCreation:
    @pytest.mark.asyncio
    async def test_persona_still_created_if_pipeline_raises(self, db):
        with patch(
            "app.api.routes.personas.process_developmental_text",
            new_callable=AsyncMock,
            side_effect=RuntimeError("simulated pipeline crash"),
        ):
            response = await create_persona(_payload(), user_id="user-1", db=db)

        assert response.name == "Timmy"
        assert response.current_trauma_markers == []  # default, pipeline never ran
        # Persona row itself must be durably committed despite the pipeline failure.
        persisted = db.query(Persona).filter(Persona.id == response.id).first()
        assert persisted is not None


class TestBaselinePersonalityUnaffected:
    @pytest.mark.asyncio
    async def test_baseline_personality_still_derived(self, db):
        # Step 6 behavior is untouched by this wiring - confirm it still runs.
        response = await create_persona(_payload(), user_id="user-1", db=db)
        assert set(response.current_personality.keys()) == {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
