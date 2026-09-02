"""
Security regression tests for the P0 correction: app/api/routes/experiences.py
::add_experience and app/api/routes/interventions.py::add_intervention
previously fell back to "persona not owned by user -> log a warning ->
proceed anyway" instead of denying the request, when every other persona-
scoped route in this codebase (personas.py, timeline.py, remix.py) already
required get_current_user and 404'd a persona that exists but isn't owned
by the caller. An authenticated user A could create an experience or
intervention on user B's persona.

A third instance of the exact same class of bug, found while auditing "every
route that accepts persona_id and determine whether ownership is enforced"
per this fix's own instructions: app/api/routes/templates.py::
apply_experience_set had no `user_id: Depends(get_current_user)` parameter
at all and no ownership check whatsoever - worse than the two originally
surfaced routes, which at least authenticated the caller. Fixed and covered
here alongside the other two.

Two layers, matching tests/test_timeline_remix_security.py's established
convention - the one thing direct calls can't prove is that a request with
NO credentials at all is rejected by FastAPI's own HTTPBearer dependency
before the route body ever runs, so a small number of real HTTP tests cover
exactly that; everything else (the actual ownership logic) is exercised via
direct function calls, matching every other *_route_wiring.py file's own
convention in this project.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models import Persona, Experience, Intervention
from app.services.attachment_engine import dimensions_for_style
from app.schemas import ExperienceCreate, ExperienceUpdate, InterventionCreate
from app.schemas.template_schemas import ApplyExperienceSetRequest
from app.api.routes.experiences import (
    add_experience, update_experience, delete_experience, get_persona_experiences,
)
from app.api.routes.interventions import add_intervention, get_persona_interventions
import app.api.routes.templates as templates_module
from app.api.routes.templates import apply_experience_set


# ============================================================
# Direct-function-call layer - ownership logic
# ============================================================

def _db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _make_persona(db, persona_id, owner_id):
    baseline = {"openness": .5, "conscientiousness": .5, "extraversion": .5, "agreeableness": .5, "neuroticism": .5}
    persona = Persona(
        id=persona_id, user_id=owner_id, name=f"Persona {persona_id}", baseline_age=10, current_age=10,
        baseline_gender="female", baseline_background="stable", baseline_personality=baseline,
        current_personality=dict(baseline), baseline_attachment_style="secure",
        current_attachment_style="secure", baseline_attachment_dimensions=dimensions_for_style("secure"),
        current_attachment_dimensions=dimensions_for_style("secure"), current_trauma_markers=[], current_state={},
    )
    db.add(persona)
    db.commit()
    return persona


@pytest.fixture
def db():
    session = _db()
    yield session
    session.close()


@pytest.fixture
def owner_persona(db):
    return _make_persona(db, "persona-owner", "user-owner")


def _mock_intervention_analysis():
    # Flat shapes matching InterventionResponse (symptom_changes:
    # Dict[str, int], sustained_effects: Dict) rather than the nested/list
    # shapes analyze_intervention's own AI-success path can return - the
    # POST route's own response converts those, but the stored row and the
    # GET route's serialization do not (a real, separate, already-
    # documented pre-existing bug - see test_api_interventions.py::
    # test_get_persona_interventions in the deferred baseline - deliberately
    # not touched here, out of this fix's scope).
    return {
        "efficacy_match": 0.5,
        "symptom_changes": {"avoidance": 5},
        "personality_changes": {},
        "coping_skills_gained": [],
        "sustained_effects": {"notes": "stable"},
        "limitations": [],
        "reasoning": "test reasoning",
    }


class TestAddExperienceOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_add_experience(self, db, owner_persona):
        response = await add_experience(
            "persona-owner", ExperienceCreate(user_description="A quiet day.", age_at_event=10),
            user_id="user-owner", db=db,
        )
        assert response.persona_id == "persona-owner"

    @pytest.mark.asyncio
    async def test_other_authenticated_user_denied(self, db, owner_persona):
        with pytest.raises(HTTPException) as exc:
            await add_experience(
                "persona-owner", ExperienceCreate(user_description="A quiet day.", age_at_event=10),
                user_id="user-intruder", db=db,
            )
        assert exc.value.status_code == 404
        # The critical assertion: a denied write must not have happened.
        assert db.query(Experience).filter_by(persona_id="persona-owner").count() == 0

    @pytest.mark.asyncio
    async def test_nonexistent_persona_denied(self, db):
        with pytest.raises(HTTPException) as exc:
            await add_experience(
                "no-such-persona", ExperienceCreate(user_description="A quiet day.", age_at_event=10),
                user_id="user-owner", db=db,
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_user_and_missing_persona_get_identical_rejection(self, db, owner_persona):
        with pytest.raises(HTTPException) as cross_user_exc:
            await add_experience(
                "persona-owner", ExperienceCreate(user_description="x", age_at_event=10),
                user_id="user-intruder", db=db,
            )
        with pytest.raises(HTTPException) as missing_exc:
            await add_experience(
                "no-such-persona", ExperienceCreate(user_description="x", age_at_event=10),
                user_id="user-intruder", db=db,
            )
        assert cross_user_exc.value.status_code == missing_exc.value.status_code == 404
        assert cross_user_exc.value.detail == missing_exc.value.detail


class TestUpdateExperienceOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_update_own_experience(self, db, owner_persona):
        created = await add_experience(
            "persona-owner", ExperienceCreate(user_description="Original.", age_at_event=10),
            user_id="user-owner", db=db,
        )
        result = await update_experience(
            "persona-owner", created.id, ExperienceUpdate(user_description="Updated."),
            user_id="user-owner", db=db,
        )
        assert result.id == "persona-owner"
        assert db.query(Experience).filter_by(id=created.id).first().user_description == "Updated."

    @pytest.mark.asyncio
    async def test_other_user_denied_and_experience_unchanged(self, db, owner_persona):
        created = await add_experience(
            "persona-owner", ExperienceCreate(user_description="Original.", age_at_event=10),
            user_id="user-owner", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await update_experience(
                "persona-owner", created.id, ExperienceUpdate(user_description="Hijacked."),
                user_id="user-intruder", db=db,
            )
        assert exc.value.status_code == 404
        assert db.query(Experience).filter_by(id=created.id).first().user_description == "Original."

    @pytest.mark.asyncio
    async def test_experience_belonging_to_a_different_persona_denied(self, db):
        # Child-id-mismatch: a real, persisted experience_id, but under a
        # DIFFERENT persona than the one named in the URL - must 404, not
        # resolve the experience by id alone and let it through.
        _make_persona(db, "persona-a", "user-a")
        _make_persona(db, "persona-b", "user-a")  # same owner, different persona
        created = await add_experience(
            "persona-a", ExperienceCreate(user_description="Belongs to A.", age_at_event=10),
            user_id="user-a", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await update_experience(
                "persona-b", created.id, ExperienceUpdate(user_description="Hijacked via wrong persona_id."),
                user_id="user-a", db=db,
            )
        assert exc.value.status_code == 404
        assert db.query(Experience).filter_by(id=created.id).first().user_description == "Belongs to A."

    @pytest.mark.asyncio
    async def test_nonexistent_experience_denied(self, db, owner_persona):
        with pytest.raises(HTTPException) as exc:
            await update_experience(
                "persona-owner", "no-such-experience", ExperienceUpdate(user_description="x"),
                user_id="user-owner", db=db,
            )
        assert exc.value.status_code == 404


class TestDeleteExperienceOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_delete_own_experience(self, db, owner_persona):
        created = await add_experience(
            "persona-owner", ExperienceCreate(user_description="Doomed.", age_at_event=10),
            user_id="user-owner", db=db,
        )
        await delete_experience("persona-owner", created.id, user_id="user-owner", db=db)
        assert db.query(Experience).filter_by(id=created.id).first() is None

    @pytest.mark.asyncio
    async def test_other_user_denied_and_experience_survives(self, db, owner_persona):
        created = await add_experience(
            "persona-owner", ExperienceCreate(user_description="Survivor.", age_at_event=10),
            user_id="user-owner", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await delete_experience("persona-owner", created.id, user_id="user-intruder", db=db)
        assert exc.value.status_code == 404
        assert db.query(Experience).filter_by(id=created.id).first() is not None

    @pytest.mark.asyncio
    async def test_experience_belonging_to_a_different_persona_denied(self, db):
        _make_persona(db, "persona-a", "user-a")
        _make_persona(db, "persona-b", "user-a")
        created = await add_experience(
            "persona-a", ExperienceCreate(user_description="Belongs to A.", age_at_event=10),
            user_id="user-a", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await delete_experience("persona-b", created.id, user_id="user-a", db=db)
        assert exc.value.status_code == 404
        assert db.query(Experience).filter_by(id=created.id).first() is not None


class TestGetPersonaExperiencesOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_read(self, db, owner_persona):
        await add_experience(
            "persona-owner", ExperienceCreate(user_description="x", age_at_event=10),
            user_id="user-owner", db=db,
        )
        result = await get_persona_experiences("persona-owner", user_id="user-owner", db=db)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_other_user_denied_read(self, db, owner_persona):
        await add_experience(
            "persona-owner", ExperienceCreate(user_description="private", age_at_event=10),
            user_id="user-owner", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await get_persona_experiences("persona-owner", user_id="user-intruder", db=db)
        assert exc.value.status_code == 404


class TestAddInterventionOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_add_intervention(self, db, owner_persona):
        with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = _mock_intervention_analysis()
            response = await add_intervention(
                "persona-owner",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-owner", db=db,
            )
        assert response.persona_id == "persona-owner"

    @pytest.mark.asyncio
    async def test_other_authenticated_user_denied(self, db, owner_persona):
        with pytest.raises(HTTPException) as exc:
            await add_intervention(
                "persona-owner",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-intruder", db=db,
            )
        assert exc.value.status_code == 404
        # Ownership is checked before the AI call, so the denied write must
        # never have happened at all.
        assert db.query(Intervention).filter_by(persona_id="persona-owner").count() == 0

    @pytest.mark.asyncio
    async def test_nonexistent_persona_denied(self, db):
        with pytest.raises(HTTPException) as exc:
            await add_intervention(
                "no-such-persona",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-owner", db=db,
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_user_and_missing_persona_get_identical_rejection(self, db, owner_persona):
        with pytest.raises(HTTPException) as cross_user_exc:
            await add_intervention(
                "persona-owner",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-intruder", db=db,
            )
        with pytest.raises(HTTPException) as missing_exc:
            await add_intervention(
                "no-such-persona",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-intruder", db=db,
            )
        assert cross_user_exc.value.status_code == missing_exc.value.status_code == 404
        assert cross_user_exc.value.detail == missing_exc.value.detail


class TestGetPersonaInterventionsOwnership:
    @pytest.mark.asyncio
    async def test_owner_can_read(self, db, owner_persona):
        with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = _mock_intervention_analysis()
            await add_intervention(
                "persona-owner",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-owner", db=db,
            )
        result = await get_persona_interventions("persona-owner", user_id="user-owner", db=db)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_other_user_denied_read(self, db, owner_persona):
        with patch("app.services.intervention_engine.openai_service.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = _mock_intervention_analysis()
            await add_intervention(
                "persona-owner",
                InterventionCreate(therapy_type="CBT", duration="6_months", intensity="weekly", age_at_intervention=10),
                user_id="user-owner", db=db,
            )
        with pytest.raises(HTTPException) as exc:
            await get_persona_interventions("persona-owner", user_id="user-intruder", db=db)
        assert exc.value.status_code == 404


class TestApplyExperienceSetOwnership:
    """
    templates.py::apply_experience_set - found during this same audit, same
    class of bug (worse: no auth dependency at all, not merely a fallback).
    Fixed alongside experiences.py/interventions.py.
    """

    @pytest.mark.asyncio
    async def test_owner_can_apply(self, db, owner_persona):
        experiences = [{"age": 10, "description": "A quiet day.", "category": "neutral",
                         "valence": "neutral", "intensity": "mild", "clinical_note": None}]
        with patch.object(templates_module, "get_template_experiences", return_value=experiences):
            response = await apply_experience_set(
                persona_id="persona-owner",
                request=ApplyExperienceSetRequest(template_id="fake-template", experience_indices=None),
                user_id="user-owner", db=db,
            )
        assert response.persona_id == "persona-owner"
        assert response.experiences_applied == 1

    @pytest.mark.asyncio
    async def test_other_authenticated_user_denied(self, db, owner_persona):
        experiences = [{"age": 10, "description": "A quiet day.", "category": "neutral",
                         "valence": "neutral", "intensity": "mild", "clinical_note": None}]
        with patch.object(templates_module, "get_template_experiences", return_value=experiences):
            with pytest.raises(HTTPException) as exc:
                await apply_experience_set(
                    persona_id="persona-owner",
                    request=ApplyExperienceSetRequest(template_id="fake-template", experience_indices=None),
                    user_id="user-intruder", db=db,
                )
        assert exc.value.status_code == 404
        assert db.query(Experience).filter_by(persona_id="persona-owner").count() == 0

    @pytest.mark.asyncio
    async def test_nonexistent_persona_denied(self, db):
        with pytest.raises(HTTPException) as exc:
            await apply_experience_set(
                persona_id="no-such-persona",
                request=ApplyExperienceSetRequest(template_id="fake-template", experience_indices=None),
                user_id="user-owner", db=db,
            )
        assert exc.value.status_code == 404

    def test_user_id_is_a_required_parameter_not_optional(self):
        # Regression lock for the root cause itself: this route previously
        # had NO user_id/get_current_user dependency in its signature at
        # all. Confirm it is now a required parameter with no default,
        # matching every other persona-scoped route.
        import inspect
        sig = inspect.signature(apply_experience_set)
        assert "user_id" in sig.parameters
        assert sig.parameters["user_id"].default is not inspect.Parameter.empty  # Depends(...) is the "default"
        from fastapi.params import Depends as DependsMarker
        assert isinstance(sig.parameters["user_id"].default, DependsMarker)


# ============================================================
# HTTP layer - proves the wire-level rejection, not just the ownership logic
# ============================================================

@pytest.fixture
def http_client_no_auth_override():
    """
    TestClient against the real app with NO get_current_user override - a
    request sent with no Authorization header at all must be rejected by
    FastAPI's HTTPBearer dependency before any route body runs. See
    test_timeline_remix_security.py's identical fixture docstring for why
    the save/clear/restore dance around app.dependency_overrides is
    necessary (mutable state shared across the whole test process).
    """
    from app.main import app

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    had_auth_override = get_current_user in app.dependency_overrides
    saved_auth_override = app.dependency_overrides.pop(get_current_user, None)
    saved_db_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    if saved_db_override is not None:
        app.dependency_overrides[get_db] = saved_db_override
    else:
        app.dependency_overrides.pop(get_db, None)
    if had_auth_override:
        app.dependency_overrides[get_current_user] = saved_auth_override


class TestUnauthenticatedRequestsOverHTTP:
    def test_add_experience_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.post(
            "/api/v1/personas/does-not-matter/experiences",
            json={"user_description": "x", "age_at_event": 10},
        )
        assert response.status_code in (401, 403)

    def test_update_experience_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.patch(
            "/api/v1/personas/does-not-matter/experiences/does-not-matter",
            json={"user_description": "x"},
        )
        assert response.status_code in (401, 403)

    def test_delete_experience_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.delete(
            "/api/v1/personas/does-not-matter/experiences/does-not-matter"
        )
        assert response.status_code in (401, 403)

    def test_get_experiences_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/personas/does-not-matter/experiences")
        assert response.status_code in (401, 403)

    def test_add_intervention_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.post(
            "/api/v1/personas/does-not-matter/interventions",
            json={"therapy_type": "CBT", "duration": "6_months", "intensity": "weekly", "age_at_intervention": 10},
        )
        assert response.status_code in (401, 403)

    def test_get_interventions_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/personas/does-not-matter/interventions")
        assert response.status_code in (401, 403)
