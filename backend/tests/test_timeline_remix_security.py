"""
Security regression tests for the P0-1 correction: app/api/routes/timeline.py
and every endpoint in app/api/routes/remix.py previously had no auth
dependency and no ownership check at all - verified live in production via
an unauthenticated curl (see RELEASE_READINESS_2026-08-30.md, P0-1). Every
other persona-scoped route already required get_current_user and filtered by
Persona.user_id == user_id; these two files were the exceptions.

Two layers, matching what each layer can actually prove:
  - Direct-function-call tests (matching tests/test_personas_route_wiring.py's
    established convention) for ownership logic: pass explicit user_id values
    and assert who can and can't reach a given persona/snapshot. Deterministic,
    fast, no HTTP/dependency-injection involved.
  - A small number of real HTTP tests (TestClient against the live app) for
    the one thing direct calls can't prove: that a request with NO credentials
    at all is rejected by FastAPI's own HTTPBearer dependency before the route
    body ever runs. These explicitly clear any get_current_user override other
    test modules may have left on the shared `app` singleton, and restore
    whatever was there afterward - dependency_overrides is process-global
    mutable state, and other test files in this suite set it at import time
    with no teardown (see tests/test_api_personas.py).
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models import Persona
from app.services.attachment_engine import dimensions_for_style
from app.api.routes.timeline import get_persona_timeline
from app.api.routes.remix import (
    create_snapshot,
    list_persona_snapshots,
    get_snapshot,
    compare_timeline_snapshots,
    get_intervention_impact,
    get_remix_suggestions,
    delete_timeline_snapshot,
)
from app.schemas.template_schemas import CreateTimelineSnapshotRequest, CompareSnapshotsRequest


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


@pytest.mark.asyncio
async def test_timeline_owner_can_read_own_persona(db, owner_persona):
    result = get_persona_timeline("persona-owner", user_id="user-owner", db=db)
    assert result["persona"]["id"] == "persona-owner"


@pytest.mark.asyncio
async def test_timeline_denies_other_user(db, owner_persona):
    with pytest.raises(HTTPException) as exc:
        get_persona_timeline("persona-owner", user_id="user-intruder", db=db)
    assert exc.value.status_code == 404


def test_timeline_nonexistent_persona_id_fails_safely(db):
    with pytest.raises(HTTPException) as exc:
        get_persona_timeline("no-such-persona", user_id="user-owner", db=db)
    assert exc.value.status_code == 404


def test_timeline_cross_user_and_missing_persona_get_identical_rejection(db, owner_persona):
    # No data leaked in the rejection: "exists but not yours" must be
    # indistinguishable from "doesn't exist" from the response alone.
    with pytest.raises(HTTPException) as cross_user_exc:
        get_persona_timeline("persona-owner", user_id="user-intruder", db=db)
    with pytest.raises(HTTPException) as missing_exc:
        get_persona_timeline("no-such-persona", user_id="user-intruder", db=db)
    assert cross_user_exc.value.status_code == missing_exc.value.status_code == 404
    assert cross_user_exc.value.detail == missing_exc.value.detail


class TestRemixSnapshotOwnership:
    @pytest.mark.asyncio
    async def test_create_snapshot_owner_allowed(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        snapshot = await create_snapshot(request, user_id="user-owner", db=db)
        assert snapshot.persona_id == "persona-owner"

    @pytest.mark.asyncio
    async def test_create_snapshot_denied_for_other_users_persona(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        with pytest.raises(HTTPException) as exc:
            await create_snapshot(request, user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_snapshots_owner_allowed(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        await create_snapshot(request, user_id="user-owner", db=db)
        result = await list_persona_snapshots("persona-owner", user_id="user-owner", db=db)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_snapshots_denied_for_other_user(self, db, owner_persona):
        with pytest.raises(HTTPException) as exc:
            await list_persona_snapshots("persona-owner", user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_snapshot_owner_allowed(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        created = await create_snapshot(request, user_id="user-owner", db=db)
        fetched = await get_snapshot(created.id, user_id="user-owner", db=db)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_snapshot_denied_for_other_user(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        created = await create_snapshot(request, user_id="user-owner", db=db)
        with pytest.raises(HTTPException) as exc:
            await get_snapshot(created.id, user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_snapshot_nonexistent_id_fails_safely(self, db):
        with pytest.raises(HTTPException) as exc:
            await get_snapshot("no-such-snapshot", user_id="user-owner", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_snapshot_owner_allowed(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        created = await create_snapshot(request, user_id="user-owner", db=db)
        result = await delete_timeline_snapshot(created.id, user_id="user-owner", db=db)
        assert "deleted" in result["message"]
        with pytest.raises(HTTPException):
            await get_snapshot(created.id, user_id="user-owner", db=db)

    @pytest.mark.asyncio
    async def test_delete_snapshot_denied_for_other_user_and_snapshot_survives(self, db, owner_persona):
        request = CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[])
        created = await create_snapshot(request, user_id="user-owner", db=db)

        with pytest.raises(HTTPException) as exc:
            await delete_timeline_snapshot(created.id, user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

        # The critical assertion: a denied delete must not have happened.
        still_there = await get_snapshot(created.id, user_id="user-owner", db=db)
        assert still_there.id == created.id


class TestRemixCompareOwnership:
    @pytest.mark.asyncio
    async def test_compare_denied_if_either_snapshot_not_owned(self, db):
        _make_persona(db, "persona-a", "user-a")
        _make_persona(db, "persona-b", "user-b")
        snap_a = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-a", label="A", modifications=[]),
            user_id="user-a", db=db,
        )
        snap_b = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-b", label="B", modifications=[]),
            user_id="user-b", db=db,
        )

        # user-a owns snap_a but not snap_b - comparing the two must be denied,
        # not silently compare across a stranger's persona.
        with pytest.raises(HTTPException) as exc:
            await compare_timeline_snapshots(
                CompareSnapshotsRequest(snapshot_id_1=snap_a.id, snapshot_id_2=snap_b.id),
                user_id="user-a", db=db,
            )
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_compare_allowed_across_own_two_personas(self, db):
        # Ownership, not same-persona-ness, is the boundary: comparing two of
        # YOUR OWN personas' snapshots is legitimate.
        _make_persona(db, "persona-a", "user-a")
        _make_persona(db, "persona-c", "user-a")
        snap_a = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-a", label="A", modifications=[]),
            user_id="user-a", db=db,
        )
        snap_c = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-c", label="C", modifications=[]),
            user_id="user-a", db=db,
        )
        comparison = await compare_timeline_snapshots(
            CompareSnapshotsRequest(snapshot_id_1=snap_a.id, snapshot_id_2=snap_c.id),
            user_id="user-a", db=db,
        )
        assert comparison["snapshot_1"]["id"] == snap_a.id
        assert comparison["snapshot_2"]["id"] == snap_c.id


class TestRemixInterventionImpactAndSuggestionsOwnership:
    @pytest.mark.asyncio
    async def test_intervention_impact_denied_for_other_user(self, db, owner_persona):
        snap = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-owner", label="Baseline", modifications=[]),
            user_id="user-owner", db=db,
        )
        with pytest.raises(HTTPException) as exc:
            await get_intervention_impact("persona-owner", baseline_snapshot_id=snap.id, user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_intervention_impact_denied_when_snapshot_belongs_to_a_different_persona(self, db):
        # Both personas owned by the SAME user - the snapshot just isn't this
        # persona's. Ownership of the snapshot's own parent persona is what's
        # actually checked, not merely "does this user own *a* persona".
        _make_persona(db, "persona-a", "user-a")
        _make_persona(db, "persona-b", "user-a")
        snap_b = await create_snapshot(
            CreateTimelineSnapshotRequest(persona_id="persona-b", label="B", modifications=[]),
            user_id="user-a", db=db,
        )
        # persona-a has no interventions/snapshot of its own baseline - this
        # should fail on ownership resolution, not proceed to compute impact
        # against persona-a using persona-b's snapshot as if it were valid.
        with pytest.raises(HTTPException):
            await get_intervention_impact("persona-a", baseline_snapshot_id=snap_b.id, user_id="user-a", db=db)

    @pytest.mark.asyncio
    async def test_suggestions_denied_for_other_user(self, db, owner_persona):
        with pytest.raises(HTTPException) as exc:
            await get_remix_suggestions("persona-owner", user_id="user-intruder", db=db)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_suggestions_owner_allowed(self, db, owner_persona):
        result = await get_remix_suggestions("persona-owner", user_id="user-owner", db=db)
        assert "suggestions" in result


# ============================================================
# HTTP layer - proves the wire-level rejection, not just the ownership logic
# ============================================================

@pytest.fixture
def http_client_no_auth_override():
    """
    TestClient against the real app with NO get_current_user override -
    a request sent with no Authorization header at all must be rejected by
    FastAPI's HTTPBearer dependency before any route body runs. Explicitly
    saves/clears/restores app.dependency_overrides[get_current_user] because
    other test modules in this suite set that override at import time with
    no teardown (see tests/test_api_personas.py) - dependency_overrides is
    mutable state on the single shared `app` object, and pytest imports every
    test module into one process, so without this a leftover override from a
    file that happened to run first would silently turn these into
    authenticated-request tests.
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
    def test_timeline_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/personas/does-not-matter/timeline")
        assert response.status_code in (401, 403)

    def test_remix_list_snapshots_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/remix/personas/does-not-matter/snapshots")
        assert response.status_code in (401, 403)

    def test_remix_get_snapshot_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/remix/snapshots/does-not-matter")
        assert response.status_code in (401, 403)

    def test_remix_delete_snapshot_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.delete("/api/v1/remix/snapshots/does-not-matter")
        assert response.status_code in (401, 403)

    def test_remix_create_snapshot_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.post(
            "/api/v1/remix/snapshots",
            json={"persona_id": "does-not-matter", "label": "x", "modifications": []},
        )
        assert response.status_code in (401, 403)

    def test_remix_compare_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.post(
            "/api/v1/remix/snapshots/compare",
            json={"snapshot_id_1": "a", "snapshot_id_2": "b"},
        )
        assert response.status_code in (401, 403)

    def test_remix_intervention_impact_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get(
            "/api/v1/remix/personas/does-not-matter/intervention-impact?baseline_snapshot_id=x"
        )
        assert response.status_code in (401, 403)

    def test_remix_suggestions_unauthenticated_denied(self, http_client_no_auth_override):
        response = http_client_no_auth_override.get("/api/v1/remix/personas/does-not-matter/suggestions")
        assert response.status_code in (401, 403)
