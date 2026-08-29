from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import DevelopmentalExposure, Experience, Interpretation, Persona, User
from app.services.attachment_engine import dimensions_for_style
from app.services.timeline_replay import rebuild_persona_from_timeline


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


def _event(db, event_id, age, magnitude="moderate", description=None):
    event = Experience(id=event_id, user_id="owner", persona_id="p", sequence_number=age,
        age_at_event=age, user_description=description or event_id)
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
