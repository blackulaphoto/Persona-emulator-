"""
Test database models and persistence.

T1: Database Schema & Models
TEST: Create persona → add experience → query database → assert data persisted
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import User, Persona, Experience, Intervention, PersonalitySnapshot


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_user(db_session):
    """Test creating and querying a user."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.commit()
    
    queried_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert queried_user is not None
    assert queried_user.email == "test@example.com"
    assert queried_user.hashed_password == "hashed_pw"


def test_create_persona_with_baseline(db_session):
    """Test creating a persona with baseline personality."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.commit()
    
    persona = Persona(
        owner_id=user.id,
        name="Test Person",
        baseline_age=8,
        baseline_gender="female",
        baseline_background="Loving family, confident child",
        current_age=8,
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.6,
            "agreeableness": 0.7,
            "neuroticism": 0.3
        },
        current_attachment_style="secure",
        current_trauma_markers=[]
    )
    db_session.add(persona)
    db_session.commit()
    
    queried_persona = db_session.query(Persona).filter_by(name="Test Person").first()
    assert queried_persona is not None
    assert queried_persona.baseline_age == 8
    assert queried_persona.current_personality["openness"] == 0.5
    assert queried_persona.current_attachment_style == "secure"


def test_add_experience_to_persona(db_session):
    """Test adding life experience to persona."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    persona = Persona(
        owner_id=user.id,
        name="Test Person",
        baseline_age=8,
        current_age=10,
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
    )
    db_session.add(persona)
    db_session.commit()
    
    experience = Experience(
        persona_id=persona.id,
        sequence_number=1,
        age_at_event=10,
        user_description="Parents got divorced when I was 10",
        event_type="trauma",
        severity=7,
        symptoms_developed=["anxiety", "trust_issues"],
        symptom_severity={"anxiety": 6, "trust_issues": 7}
    )
    db_session.add(experience)
    db_session.commit()
    
    queried_experience = db_session.query(Experience).filter_by(persona_id=persona.id).first()
    assert queried_experience is not None
    assert queried_experience.age_at_event == 10
    assert queried_experience.event_type == "trauma"
    assert "anxiety" in queried_experience.symptoms_developed
    assert queried_experience.symptom_severity["anxiety"] == 6


def test_add_intervention_to_persona(db_session):
    """Test adding therapeutic intervention."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    persona = Persona(
        owner_id=user.id,
        name="Test Person",
        baseline_age=8,
        current_age=30,
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
    )
    db_session.add(persona)
    db_session.commit()
    
    intervention = Intervention(
        persona_id=persona.id,
        sequence_number=1,
        age_at_intervention=30,
        therapy_type="ACT",
        duration="4 months",
        intensity="weekly",
        efficacy_match=0.85,
        symptom_changes={"hoarding": {"before": 8, "after": 4}}
    )
    db_session.add(intervention)
    db_session.commit()
    
    queried_intervention = db_session.query(Intervention).filter_by(persona_id=persona.id).first()
    assert queried_intervention is not None
    assert queried_intervention.therapy_type == "ACT"
    assert queried_intervention.efficacy_match == 0.85
    assert queried_intervention.symptom_changes["hoarding"]["after"] == 4


def test_create_personality_snapshot(db_session):
    """Test creating personality snapshots for timeline."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    persona = Persona(
        owner_id=user.id,
        name="Test Person",
        baseline_age=8,
        current_age=10,
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
    )
    db_session.add(persona)
    db_session.commit()
    
    snapshot = PersonalitySnapshot(
        persona_id=persona.id,
        age=10,
        personality_profile={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.4, "agreeableness": 0.5, "neuroticism": 0.6},
        attachment_style="anxious",
        trauma_markers=["abandonment_fear"],
        symptom_severity={"anxiety": 6}
    )
    db_session.add(snapshot)
    db_session.commit()
    
    queried_snapshot = db_session.query(PersonalitySnapshot).filter_by(persona_id=persona.id).first()
    assert queried_snapshot is not None
    assert queried_snapshot.age == 10
    assert queried_snapshot.attachment_style == "anxious"
    assert "abandonment_fear" in queried_snapshot.trauma_markers


def test_relationships(db_session):
    """Test that relationships between models work."""
    user = User(email="test@example.com", hashed_password="hashed_pw")
    db_session.add(user)
    db_session.flush()  # Flush to get user.id
    
    persona = Persona(
        owner_id=user.id,
        name="Test Person",
        baseline_age=8,
        current_age=10,
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5}
    )
    experience = Experience(
        persona=persona,
        sequence_number=1,
        age_at_event=10,
        user_description="Test experience"
    )
    
    db_session.add(persona)
    db_session.add(experience)
    db_session.commit()
    
    # Test forward relationships
    assert len(persona.experiences) == 1
    assert persona.experiences[0].user_description == "Test experience"
    
    # Test backward relationship
    assert experience.persona.name == "Test Person"
