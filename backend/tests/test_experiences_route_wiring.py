"""
Integration tests for the developmental pipeline wired into
app/api/routes/experiences.py::add_experience.

Covers both docs/MIGRATION_MAP.md "wiring steps 2-5 into routes" (the
pipeline runs for real) and Step 11d (the pipeline, via
legacy_experience_adapter.py, is now the ONLY analysis path -
psychology_engine.analyze_experience()'s old, ungated, independent GPT call
has been removed from this route entirely, not just left running alongside
the new one). Every AI call across all four engines the pipeline touches is
mocked to fail fast, forcing the fallback/heuristic paths - the honest
current production state (no OpenAI credits configured).
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import Persona, Experience, DevelopmentalExposure, AdaptationPattern, PersonalitySnapshot
import app.api.routes.experiences as experiences_module
from app.api.routes.experiences import add_experience
from app.schemas import ExperienceCreate

TEST_DB_URL = "sqlite:///./test_experiences_route_wiring.db"
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
def _fail_all_pipeline_ai_calls():
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
        baseline_background="...",
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_attachment_style="secure", current_trauma_markers=[], current_state={}, user_id="user-1",
    )
    defaults.update(overrides)
    persona = Persona(**defaults)
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona


BULLYING_TEXTS = [
    "He was bullied by classmates at school.",
    "He was picked on by classmates again.",
    "He was made fun of by classmates once more.",
    "He was excluded by classmates yet again.",
]


class TestPsychologyEngineFullyRetiredFromThisRoute:
    def test_analyze_experience_no_longer_imported(self):
        # Step 11d: not just unused - actually removed from the module, so a
        # stray reference anywhere in this file would fail loudly, not silently.
        assert not hasattr(experiences_module, "analyze_experience")

    def test_route_module_does_not_import_psychology_engine(self):
        # Precise check for an actual import statement, not a comment
        # mentioning psychology_engine.py by name for historical context.
        import inspect
        source = inspect.getsource(experiences_module)
        assert "import psychology_engine" not in source
        assert "from app.services.psychology_engine" not in source


class TestPipelineActuallyRunsOnExperienceAdd:
    @pytest.mark.asyncio
    async def test_explicit_same_age_sequence_is_persisted_and_returned(self, db):
        persona = _make_persona(db)
        response = await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(
                user_description="A later same-age event", age_at_event=16, sequence_index=2
            ),
            user_id="user-1", db=db,
        )
        assert response.sequence_index == 2
        assert db.get(Experience, response.id).sequence_index == 2

    @pytest.mark.asyncio
    async def test_creates_developmental_exposures_for_this_experience(self, db):
        persona = _make_persona(db)
        response = await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description="He was gone again for days, drinking the whole time.", age_at_event=10),
            user_id="user-1", db=db,
        )

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
        assert len(exposures) >= 1
        assert all(e.source == "experience" for e in exposures)
        assert all(e.source_event_id == response.id for e in exposures)

    @pytest.mark.asyncio
    async def test_current_state_populated_and_snapshot_carries_it(self, db):
        # Step 11: State tier is unconditional (unlike Trait) - a single
        # experience with a real exposure/interpretation should move it, and
        # the PersonalitySnapshot created for this experience should freeze
        # a copy of it alongside the existing personality_profile.
        persona = _make_persona(db)
        response = await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description=BULLYING_TEXTS[0], age_at_event=10),
            user_id="user-1", db=db,
        )

        db.refresh(persona)
        assert persona.current_state != {}

        snapshot = db.query(PersonalitySnapshot).filter(PersonalitySnapshot.experience_id == response.id).first()
        assert snapshot is not None
        assert snapshot.state_profile == persona.current_state

    @pytest.mark.asyncio
    async def test_immediate_effects_now_reflects_real_current_personality(self, db):
        # Step 11d: immediate_effects no longer means "the AI's independently
        # decided new Big Five values" - it means current_personality as of
        # right after this call (see legacy_experience_adapter.py).
        # Step 12: that value now includes this event's small provisional trait
        # nudge, so it is the persona's REAL post-event personality rather than
        # an untouched baseline - which is the whole point of the field.
        persona = _make_persona(db)
        response = await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description=BULLYING_TEXTS[0], age_at_event=10),
            user_id="user-1", db=db,
        )
        db.refresh(persona)
        assert response.immediate_effects == persona.current_personality
        # avoidance's heuristic default nudges extraversion down provisionally.
        assert response.immediate_effects["extraversion"] < 0.5
        # Untouched traits stay exactly at baseline - the nudge is targeted,
        # not a blanket shift of everything.
        assert response.immediate_effects["openness"] == 0.5

    @pytest.mark.asyncio
    async def test_legacy_fields_derived_honestly_not_fabricated(self, db):
        # coping_mechanisms/long_term_patterns are now real, derived from
        # this event's actual Interpretation - "avoidance" for bullying text
        # (see pattern_engine.EXPOSURE_INTERPRETATION_DEFAULTS), not an
        # arbitrary AI guess. cross_experience_triggers/recommended_therapies
        # are honestly empty (see legacy_experience_adapter.py's docstring).
        persona = _make_persona(db)
        response = await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description=BULLYING_TEXTS[0], age_at_event=10),
            user_id="user-1", db=db,
        )
        assert response.coping_mechanisms == ["avoidance"]
        assert response.long_term_patterns == ["I don't fit in."]
        assert response.cross_experience_triggers == []
        assert response.recommended_therapies == []

    @pytest.mark.asyncio
    async def test_current_trauma_markers_empty_for_a_single_new_exposure(self, db):
        # A single exposure never crosses the display threshold - real
        # invariant from step 4, still true now that this is the only path.
        persona = _make_persona(db)
        await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description="He was gone again for days, drinking the whole time.", age_at_event=10),
            user_id="user-1", db=db,
        )
        db.refresh(persona)
        assert persona.current_trauma_markers == []

    @pytest.mark.asyncio
    async def test_second_experience_reinforces_pattern_not_duplicates(self, db):
        persona = _make_persona(db)
        await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description="He was gone for days, drinking.", age_at_event=8),
            user_id="user-1", db=db,
        )
        await add_experience(
            persona_id=persona.id,
            experience_data=ExperienceCreate(user_description="Gone again for days, drinking the whole time.", age_at_event=12),
            user_id="user-1", db=db,
        )

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        strategies = [p.adaptation_strategy for p in patterns]
        assert len(strategies) == len(set(strategies))  # no duplicate rows per strategy


class TestRealReinforcementAcrossMultipleExperiences:
    @pytest.mark.asyncio
    async def test_symptom_severity_and_trait_both_earn_movement_from_real_recurrence(self, db):
        # Same deterministic 4-call bullying sequence as
        # tests/test_developmental_pipeline_state_trait.py, but exercised
        # through the actual route + legacy adapter this time. By the 4th
        # call: the pattern is "established" (Trait gate opens - extraversion
        # moves), AND persistence evidence (4 distinct occurrences) crosses
        # DISPLAY_THRESHOLD, so symptom_severity should carry a real,
        # evidence-derived int for one of peer_rejection_or_bullying's
        # candidate patterns (evidence_accumulator.EXPOSURE_HYPOTHESIS_PRIORS).
        persona = _make_persona(db)
        response = None
        for i, text in enumerate(BULLYING_TEXTS):
            response = await add_experience(
                persona_id=persona.id,
                experience_data=ExperienceCreate(user_description=text, age_at_event=8 + i),
                user_id="user-1", db=db,
            )

        db.refresh(persona)
        assert persona.current_personality["extraversion"] < 0.5
        assert response.symptoms_developed  # non-empty - crossed the display threshold
        assert response.symptom_severity  # non-empty dict
        assert all(isinstance(v, int) and 0 <= v <= 10 for v in response.symptom_severity.values())
        assert set(response.symptom_severity.keys()) == set(response.symptoms_developed)


class TestPipelineFailureDoesNotBlockExperienceCreation:
    @pytest.mark.asyncio
    async def test_experience_still_created_if_pipeline_raises(self, db):
        # Step 11d: the pipeline is now the ONLY analysis path, so a failure
        # here is more consequential than before - this confirms the route
        # still degrades gracefully (creates the Experience row with empty
        # legacy fields) rather than losing the user's input or 500ing, same
        # philosophy as every other AI-dependent path in this rebuild.
        persona = _make_persona(db)
        with patch("app.api.routes.experiences.process_developmental_text", new_callable=AsyncMock, side_effect=RuntimeError("simulated crash")):
            response = await add_experience(
                persona_id=persona.id,
                experience_data=ExperienceCreate(user_description="Something happened.", age_at_event=10),
                user_id="user-1", db=db,
            )

        assert response.user_description == "Something happened."
        assert response.symptoms_developed is None
        persisted = db.query(Experience).filter(Experience.id == response.id).first()
        assert persisted is not None
