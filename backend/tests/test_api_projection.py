from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import (
    AdaptationPattern, ClinicalPatternHypothesis, Experience, Interpretation,
    Persona, PersonalitySnapshot, User,
)
from app.services.api_projection import experience_psychology_projection, persona_projection


def _db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _persona(db):
    db.add(User(id="owner", email="owner@example.com", hashed_password="x"))
    persona = Persona(
        id="persona", user_id="owner", name="Emma", baseline_age=8,
        current_age=14, baseline_gender="female", baseline_background="Stable home",
        baseline_personality={"openness": .4, "conscientiousness": .5, "extraversion": .6, "agreeableness": .7, "neuroticism": .2},
        current_personality={"openness": .5, "conscientiousness": .5, "extraversion": .4, "agreeableness": .7, "neuroticism": .5},
        current_attachment_style="secure", current_trauma_markers=[], current_state={"trust": .3},
        foundational_environment_signals={"caregiver_stability": 2}, narrative_mode="case_subject",
    )
    db.add(persona)
    db.commit()
    return persona


def test_persona_projection_keeps_baseline_stable_and_computes_delta():
    db = _db()
    persona = _persona(db)
    projected = persona_projection(db, persona)
    assert projected["baseline_personality"]["neuroticism"] == .2
    assert projected["current_personality"]["neuroticism"] == .5
    assert projected["personality_delta"]["neuroticism"] == .3
    assert projected["foundational_environment_signals"] == {"caregiver_stability": 2}
    assert projected["narrative_mode"] == "case_subject"


def test_experience_projection_exposes_persisted_interpretation_and_links():
    db = _db()
    persona = _persona(db)
    experience = Experience(
        id="event-1", persona_id=persona.id, user_id="owner", sequence_number=1,
        age_at_event=10, user_description="A difficult move",
    )
    db.add(experience)
    pattern = AdaptationPattern(
        id="pattern-1", persona_id=persona.id, pattern_name="Stay guarded",
        adaptation_strategy="avoidance", status="emerging", evidence_strength=.2,
        reinforcement_history=[{"experience_id": "event-1", "age": 10, "effect": "originated"}],
    )
    db.add(pattern)
    db.flush()
    db.add(Interpretation(
        id="interpretation-1", persona_id=persona.id, source_event_id="event-1",
        age_at_event=10, belief_statement="Belonging is fragile", adaptation_strategy="avoidance",
        reasoning="The move disrupted continuity", state_implications={"trust": {"direction": "decrease"}},
        trait_implications={"neuroticism": {"direction": "increase"}}, pattern_id=pattern.id,
    ))
    db.add(ClinicalPatternHypothesis(
        id="hypothesis-1", persona_id=persona.id, pattern_key="social_anxiety",
        supporting_evidence=[{"source_id": "event-1", "description": "social withdrawal"}],
        contradicting_evidence=[], evidence_strength=.35, previous_evidence_strength=.2,
    ))
    db.commit()

    projected = experience_psychology_projection(db, experience)
    assert projected["interpretation"]["belief_statement"] == "Belonging is fragile"
    assert projected["pattern_connections"][0]["effect"] == "originated"
    assert projected["hypothesis_connections"][0]["evidence_role"] == "supporting"
    assert projected["hypothesis_connections"][0]["direction"] == "strengthening"


def test_snapshot_schema_has_state_profile_column():
    db = _db()
    persona = _persona(db)
    snapshot = PersonalitySnapshot(
        persona_id=persona.id, age=14, personality_profile=persona.current_personality,
        attachment_style="secure", trauma_markers=[], symptom_severity={},
        state_profile={"trust": .3}, created_at=datetime.utcnow(),
    )
    db.add(snapshot)
    db.commit()
    assert snapshot.state_profile == {"trust": .3}
