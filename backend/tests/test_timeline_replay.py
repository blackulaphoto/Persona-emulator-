from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import DevelopmentalExposure, Experience, Interpretation, Persona, User
from app.services.attachment_engine import dimensions_for_style
from app.services.timeline_replay import rebuild_persona_from_timeline
from app.api.routes.experiences import delete_experience, update_experience
from app.api.routes.timeline import get_persona_timeline
from app.schemas import ExperienceUpdate
from unittest.mock import AsyncMock, patch
import pytest


def _db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _setup(db):
    db.add(User(id="owner", email="owner@example.com", hashed_password="x"))
    baseline = {"openness": .5, "conscientiousness": .5, "extraversion": .6, "agreeableness": .6, "neuroticism": .2}
    persona = Persona(id="p", user_id="owner", name="Emma", baseline_age=8, current_age=18,
        baseline_gender="female", baseline_background="stable", baseline_personality=baseline,
        current_personality=dict(baseline), baseline_attachment_style="secure",
        current_attachment_style="secure", baseline_attachment_dimensions=dimensions_for_style("secure"),
        current_attachment_dimensions=dimensions_for_style("secure"), current_trauma_markers=[], current_state={})
    db.add(persona)
    db.commit()
    return persona


def _event(db, event_id, age, magnitude="moderate", description=None, sequence_index=1):
    event = Experience(id=event_id, user_id="owner", persona_id="p", sequence_number=age,
        sequence_index=sequence_index, age_at_event=age, user_description=description or event_id)
    db.add(event)
    db.add(DevelopmentalExposure(id=f"x-{event_id}", persona_id="p", source_event_id=event_id,
        source="experience", age_at_exposure=age, exposure_type="caregiver_absence",
        developmental_domains=["attachment_security"], raw_text=event.user_description))
    db.add(Interpretation(id=f"i-{event_id}", persona_id="p", source_event_id=event_id, age_at_event=age,
        adaptation_strategy="avoidance", belief_statement="People leave", developmental_domains=["attachment_security"],
        state_implications={"trust": {"direction": "decrease", "magnitude": magnitude},
                            "avoidance": {"direction": "increase", "magnitude": magnitude}},
        trait_implications={"neuroticism": {"direction": "increase", "magnitude": magnitude, "evidence_strength": "moderate"}}))
    db.commit()


def _state(db):
    persona = db.get(Persona, "p")
    hypothesis = next(iter(persona.clinical_pattern_hypotheses), None)
    return {"personality": dict(persona.current_personality), "state": dict(persona.current_state),
            "attachment": dict(persona.current_attachment_dimensions),
            "patterns": [(p.adaptation_strategy, len(p.reinforcement_history or [])) for p in persona.adaptation_patterns],
            "hypothesis_strength": hypothesis.evidence_strength if hypothesis else None}


def test_remove_readd_and_edit_replay_without_stale_contribution():
    db = _db()
    _setup(db)
    _event(db, "a", 10)
    _event(db, "b", 14, "high")
    _event(db, "c", 18)
    rebuild_persona_from_timeline(db, "p")
    db.commit()
    original = _state(db)

    db.query(Interpretation).filter_by(source_event_id="b").delete()
    db.query(DevelopmentalExposure).filter_by(source_event_id="b").delete()
    db.query(Experience).filter_by(id="b").delete()
    rebuild_persona_from_timeline(db, "p")
    db.commit()
    removed = _state(db)
    assert removed["state"]["trust"] > original["state"]["trust"]
    assert removed["attachment"]["attachment_avoidance"] < original["attachment"]["attachment_avoidance"]
    assert removed["patterns"][0][1] == 2
    assert removed["hypothesis_strength"] < original["hypothesis_strength"]

    _event(db, "b2", 14, "high")
    rebuild_persona_from_timeline(db, "p")
    db.commit()
    assert _state(db) == original

    edited = db.query(Interpretation).filter_by(source_event_id="b2").one()
    edited.state_implications = {"trust": {"direction": "increase", "magnitude": "high"},
                                 "avoidance": {"direction": "decrease", "magnitude": "high"}}
    edited.trait_implications = {"neuroticism": {"direction": "decrease", "magnitude": "high", "evidence_strength": "moderate"}}
    rebuild_persona_from_timeline(db, "p")
    db.commit()
    changed = _state(db)
    assert changed["state"]["trust"] > original["state"]["trust"]
    assert changed["personality"]["neuroticism"] < original["personality"]["neuroticism"]


@pytest.mark.asyncio
async def test_delete_route_rebuilds_instead_of_leaving_residue():
    db = _db(); _setup(db); _event(db, "a", 10); _event(db, "b", 14); _event(db, "c", 18)
    rebuild_persona_from_timeline(db, "p"); db.commit()
    before = _state(db)
    response = await delete_experience("p", "b", "owner", db)
    after = _state(db)
    assert response.current_age == 18
    assert after["state"]["trust"] > before["state"]["trust"]
    assert db.query(Interpretation).filter_by(source_event_id="b").count() == 0


@pytest.mark.asyncio
async def test_patch_route_regenerates_edited_event_then_replays():
    db = _db(); _setup(db); _event(db, "a", 10); _event(db, "b", 14); _event(db, "c", 18)
    rebuild_persona_from_timeline(db, "p"); db.commit()
    before = _state(db)

    async def regenerated(db_arg, persona, text, source, age, source_event_id):
        db_arg.add(DevelopmentalExposure(persona_id="p", source_event_id=source_event_id, source="experience",
            age_at_exposure=age, exposure_type="stable_relationship", developmental_domains=["attachment_security"], raw_text=text))
        db_arg.add(Interpretation(persona_id="p", source_event_id=source_event_id, age_at_event=age,
            adaptation_strategy="connection_seeking", belief_statement="People can stay", developmental_domains=["attachment_security"],
            state_implications={"trust": {"direction": "increase", "magnitude": "high"},
                                "avoidance": {"direction": "decrease", "magnitude": "high"}},
            trait_implications={"neuroticism": {"direction": "decrease", "magnitude": "high", "evidence_strength": "moderate"}}))
        db_arg.flush()
        return {"trauma_markers": []}

    with patch("app.api.routes.experiences.process_developmental_text", new=AsyncMock(side_effect=regenerated)):
        response = await update_experience("p", "b", ExperienceUpdate(user_description="A reliable partner stayed"), "owner", db)
    after = _state(db)
    assert response.current_age == 18
    assert after["state"]["trust"] > before["state"]["trust"]
    assert db.get(Experience, "b").user_description == "A reliable partner stayed"
    assert db.query(Interpretation).filter_by(source_event_id="b").count() == 1


def test_same_age_replay_uses_sequence_index_not_creation_time():
    db = _db(); persona = _setup(db)
    persona.baseline_attachment_dimensions = {
        "attachment_anxiety": .2, "attachment_avoidance": .2, "relational_security": .8,
    }
    db.add_all([
        Experience(id="positive", user_id="owner", persona_id="p", sequence_number=1,
                   sequence_index=1, age_at_event=16, user_description="support"),
        Experience(id="negative", user_id="owner", persona_id="p", sequence_number=2,
                   sequence_index=2, age_at_event=16, user_description="betrayal"),
        Interpretation(id="positive-i", persona_id="p", source_event_id="positive", age_at_event=16,
            belief_statement="People can be safe", developmental_domains=["attachment_security"],
            state_implications={"trust": {"direction": "increase", "magnitude": "high"}}),
        Interpretation(id="negative-i", persona_id="p", source_event_id="negative", age_at_event=16,
            belief_statement="People can betray me", developmental_domains=["attachment_security"],
            state_implications={"trust": {"direction": "decrease", "magnitude": "high"}}),
    ])
    db.commit()
    rebuild_persona_from_timeline(db, "p")
    support_then_betrayal = db.get(Persona, "p").current_attachment_dimensions["relational_security"]

    db.get(Experience, "positive").sequence_index = 2
    db.get(Experience, "negative").sequence_index = 1
    rebuild_persona_from_timeline(db, "p")
    betrayal_then_support = db.get(Persona, "p").current_attachment_dimensions["relational_security"]

    assert support_then_betrayal < betrayal_then_support
    assert support_then_betrayal == .78
    assert betrayal_then_support == .8


@pytest.mark.asyncio
async def test_patch_preserves_or_updates_same_age_sequence():
    db = _db(); _setup(db)
    _event(db, "first", 16, sequence_index=1)
    _event(db, "second", 16, sequence_index=2)

    with patch("app.api.routes.experiences.process_developmental_text", new=AsyncMock(return_value={})):
        await update_experience("p", "first", ExperienceUpdate(user_description="edited"), "owner", db)
        assert db.get(Experience, "first").sequence_index == 1
        await update_experience("p", "first", ExperienceUpdate(sequence_index=3), "owner", db)
        assert db.get(Experience, "first").sequence_index == 3


def test_timeline_orders_same_age_experiences_and_reuses_persona_projection():
    db = _db(); _setup(db)
    _event(db, "later", 16, sequence_index=2)
    _event(db, "earlier", 16, sequence_index=1)
    response = get_persona_timeline("p", user_id="owner", db=db)
    assert [item["id"] for item in response["experiences"]] == ["earlier", "later"]
    assert [item["sequence_index"] for item in response["timeline_events"]] == [1, 2]
    assert response["persona"]["baseline_attachment_dimensions"] == dimensions_for_style("secure")
    assert "attachment_delta" in response["persona"]
