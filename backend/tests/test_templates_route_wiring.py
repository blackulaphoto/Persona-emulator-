"""
Integration tests for Step 11g (docs/MIGRATION_MAP.md): the canonical
developmental pipeline wired into
app/api/routes/templates.py::apply_experience_set, replacing its old call to
psychology_engine.analyze_experience() - the last live runtime caller of
that function anywhere in the app.

Every AI call across all engines the pipeline touches is mocked to fail
fast, forcing the fallback/heuristic paths - the honest current production
state (no OpenAI credits configured), same convention as
test_experiences_route_wiring.py.

get_template_experiences is patched directly for the apply_experience_set
tests below rather than going through create_persona_from_template, so
those tests stay focused on this step's actual scope
(psychology_engine.analyze_experience() retirement) - same convention every
other *_route_wiring.py test file in this project already uses (personas
built directly via the ORM).

TestCreatePersonaFromTemplateGetsARealUserId covers a separate, adjacent fix
made in the same pass: template_service.py::create_persona_from_template
used to construct Persona(owner_id=...) - owner_id is not a real column
(renamed to user_id at some point; confirmed empirically this raised
TypeError: 'owner_id' is an invalid keyword argument for Persona on every
call), and the route never supplied a real user_id anyway (no auth
dependency, and the frontend never sends the request body's optional
owner_id field). Both are fixed: the route now requires an authenticated
caller (matching personas.py/experiences.py/interventions.py) and
create_persona_from_template maps it onto Persona.user_id correctly.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Persona, Experience, PersonalitySnapshot, DevelopmentalExposure,
    Interpretation, AdaptationPattern, ClinicalTemplate,
)
import app.api.routes.templates as templates_module
from app.api.routes.templates import (
    apply_experience_set, list_templates, get_template_details,
    create_persona_from_template_endpoint,
)
from app.services.template_service import populate_templates_database
from app.schemas.template_schemas import ApplyExperienceSetRequest, CreatePersonaFromTemplateRequest

TEST_DB_URL = "sqlite:///./test_templates_route_wiring.db"
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


def _template_exp(age, description, **overrides):
    defaults = dict(category="attachment", valence="negative", intensity="moderate", clinical_note=None)
    defaults.update(overrides)
    return {"age": age, "description": description, **defaults}


BULLYING_EXPERIENCES = [
    _template_exp(8, "He was bullied by classmates at school."),
    _template_exp(9, "He was picked on by classmates again."),
    _template_exp(10, "He was made fun of by classmates once more."),
    _template_exp(11, "He was excluded by classmates yet again."),
]


async def _apply_experiences(db, persona, experiences, indices=None):
    with patch.object(templates_module, "get_template_experiences", return_value=experiences):
        return await apply_experience_set(
            persona_id=persona.id,
            request=ApplyExperienceSetRequest(template_id="fake-template", experience_indices=indices),
            db=db,
        )


class TestPsychologyEngineFullyRetiredFromThisRoute:
    def test_analyze_experience_no_longer_imported(self):
        assert not hasattr(templates_module, "analyze_experience")

    def test_route_module_does_not_import_psychology_engine(self):
        import inspect
        source = inspect.getsource(templates_module)
        assert "import psychology_engine" not in source
        assert "from app.services.psychology_engine" not in source


class TestApplyExperienceSetRunsCanonicalPipeline:
    @pytest.mark.asyncio
    async def test_creates_developmental_exposures(self, db):
        persona = _make_persona(db)
        response = await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])

        exposures = db.query(DevelopmentalExposure).filter(DevelopmentalExposure.persona_id == persona.id).all()
        assert len(exposures) >= 1
        assert all(e.source == "experience" for e in exposures)
        assert response.experiences_applied == 1
        assert len(response.experience_ids) == 1

    @pytest.mark.asyncio
    async def test_creates_interpretation_and_pattern(self, db):
        persona = _make_persona(db)
        await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])
        assert db.query(Interpretation).filter(Interpretation.persona_id == persona.id).count() == 1
        assert db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).count() == 1

    @pytest.mark.asyncio
    async def test_current_trauma_markers_only_from_canonical_projection(self, db):
        # A single experience never crosses the display threshold - same
        # invariant as every other experience-creation path in this rebuild.
        persona = _make_persona(db)
        await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])
        db.refresh(persona)
        assert persona.current_trauma_markers == []

    @pytest.mark.asyncio
    async def test_experience_row_gets_a_real_user_id(self, db):
        # Regression guard for the pre-existing NOT NULL bug this step fixed
        # incidentally (Experience.user_id is required; the old constructor
        # call never set it, so every call to this endpoint 500'd before).
        persona = _make_persona(db, user_id="user-42")
        response = await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])
        experience = db.query(Experience).filter(Experience.id == response.experience_ids[0]).first()
        assert experience.user_id == "user-42"

    @pytest.mark.asyncio
    async def test_state_populated_and_snapshot_carries_it(self, db):
        persona = _make_persona(db)
        response = await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])
        db.refresh(persona)
        assert persona.current_state != {}

        snapshot = db.query(PersonalitySnapshot).filter(
            PersonalitySnapshot.experience_id == response.experience_ids[0]
        ).first()
        assert snapshot is not None
        assert snapshot.state_profile == persona.current_state


class TestOldUngatedBigFiveWriteIsGone:
    @pytest.mark.asyncio
    async def test_single_experience_never_moves_trait(self, db):
        persona = _make_persona(db)
        response = await _apply_experiences(db, persona, [BULLYING_EXPERIENCES[0]])
        assert response.personality_before == response.personality_after
        assert response.personality_after == {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5,
        }


class TestSameStatePatternTraitRulesAsEveryOtherExperience:
    @pytest.mark.asyncio
    async def test_trait_gate_opens_only_on_the_fourth_reinforcement(self, db):
        # Reuses the same deterministic 4-text bullying sequence as
        # test_experiences_route_wiring.py / test_developmental_pipeline_
        # state_trait_engine.py - applied here as one template experience
        # set instead of four separate /experiences calls.
        persona = _make_persona(db)
        response = await _apply_experiences(db, persona, BULLYING_EXPERIENCES)

        db.refresh(persona)
        assert response.experiences_applied == 4
        assert persona.current_personality["extraversion"] < 0.5
        assert response.personality_before["extraversion"] == 0.5
        assert response.personality_after["extraversion"] == persona.current_personality["extraversion"]

        patterns = db.query(AdaptationPattern).filter(AdaptationPattern.persona_id == persona.id).all()
        assert any(p.status == "established" for p in patterns)


class TestPipelineFailureRollsBackTheWholeBatch:
    @pytest.mark.asyncio
    async def test_failure_on_second_experience_rolls_back_the_first_too(self, db):
        # Preserves this endpoint's pre-existing all-or-nothing contract -
        # different from experiences.py::add_experience's per-call graceful
        # degradation, which is a different endpoint with a different contract.
        persona = _make_persona(db)

        call_count = {"n": 0}
        real = templates_module.process_developmental_text

        async def _flaky(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated crash on second experience")
            return await real(*args, **kwargs)

        with patch.object(templates_module, "process_developmental_text", side_effect=_flaky):
            with pytest.raises(Exception):
                await _apply_experiences(db, persona, BULLYING_EXPERIENCES[:2])

        assert db.query(Experience).filter(Experience.persona_id == persona.id).count() == 0


class TestExperienceIndicesSubsetStillWorks:
    @pytest.mark.asyncio
    async def test_only_selected_indices_applied(self, db):
        persona = _make_persona(db)
        response = await _apply_experiences(db, persona, BULLYING_EXPERIENCES, indices=[0, 2])
        assert response.experiences_applied == 2


class TestTemplatesAndCitationsPreserved:
    """Step 11g touched only apply_experience_set - confirm the untouched endpoints/data still work."""

    @pytest.mark.asyncio
    async def test_seeded_templates_still_list_with_citations(self, db):
        from app.services.template_service import populate_templates_database
        populate_templates_database(db)

        templates = db.query(ClinicalTemplate).all()
        assert len(templates) > 0
        assert any(t.citations for t in templates)

    @pytest.mark.asyncio
    async def test_get_template_details_unaffected(self, db):
        from app.services.template_service import populate_templates_database
        populate_templates_database(db)

        template = db.query(ClinicalTemplate).first()
        result = await get_template_details(template_id=template.id, db=db)
        assert result.id == template.id
        assert result.predefined_experiences


class TestCreatePersonaFromTemplateGetsARealUserId:
    """The owner_id/user_id fix - see module docstring."""

    @pytest.mark.asyncio
    async def test_persona_created_with_authenticated_users_id(self, db):
        populate_templates_database(db)
        template = db.query(ClinicalTemplate).first()

        response = await create_persona_from_template_endpoint(
            request=CreatePersonaFromTemplateRequest(template_id=template.id),
            user_id="auth-user-77",
            db=db,
        )

        persona = db.query(Persona).filter(Persona.id == response.persona_id).first()
        assert persona is not None
        assert persona.user_id == "auth-user-77"

    @pytest.mark.asyncio
    async def test_persona_owned_by_the_caller_shows_up_in_their_persona_list(self, db):
        # Confirms the whole point of stamping a real user_id: the persona
        # is actually findable by its owner afterward, the same way
        # personas.py::list_personas filters (Persona.user_id == user_id).
        populate_templates_database(db)
        template = db.query(ClinicalTemplate).first()

        response = await create_persona_from_template_endpoint(
            request=CreatePersonaFromTemplateRequest(template_id=template.id),
            user_id="auth-user-77",
            db=db,
        )

        owned = db.query(Persona).filter(Persona.user_id == "auth-user-77").all()
        assert response.persona_id in [p.id for p in owned]

    @pytest.mark.asyncio
    async def test_client_supplied_owner_id_is_ignored_not_trusted(self, db):
        # A client-supplied owner_id must not be able to assign a persona to
        # someone else's Firebase UID - only the authenticated caller's own
        # user_id (from Depends(get_current_user)) is ever used.
        populate_templates_database(db)
        template = db.query(ClinicalTemplate).first()

        response = await create_persona_from_template_endpoint(
            request=CreatePersonaFromTemplateRequest(template_id=template.id, owner_id="someone-elses-uid"),
            user_id="auth-user-77",
            db=db,
        )

        persona = db.query(Persona).filter(Persona.id == response.persona_id).first()
        assert persona.user_id == "auth-user-77"
        assert persona.user_id != "someone-elses-uid"
