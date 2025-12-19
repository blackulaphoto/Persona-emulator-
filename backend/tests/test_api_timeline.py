"""
Test Timeline API endpoints.

T10: Add Timeline API
TEST: GET /api/v1/personas/{id}/timeline → return complete chronological history
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock
from app.core.database import Base, get_db
from app.main import app


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# Mock AI responses
MOCK_EXPERIENCE = {
    "immediate_effects": {
        "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.3,
        "agreeableness": 0.5, "neuroticism": 0.75
    },
    "symptoms_developed": ["anxiety", "hypervigilance"],
    "symptom_severity": {"anxiety": 8, "hypervigilance": 7},
    "long_term_patterns": ["fear_response"],
    "coping_mechanisms": [],
    "worldview_shifts": {},
    "cross_experience_triggers": [],
    "recommended_therapies": ["CBT"]
}

MOCK_INTERVENTION = {
    "actual_symptoms_targeted": ["anxiety"],
    "efficacy_match": 0.75,
    "immediate_effects": {"symptom_reduction": {"anxiety": 0.5}},
    "sustained_effects": {"relapse_prevention": 0.6},
    "limitations": ["Does not address root trauma"],
    "symptom_changes": {"anxiety": 4, "hypervigilance": 7},
    "personality_changes": {"neuroticism": 0.6},
    "coping_skills_gained": ["cognitive_restructuring"],
    "reasoning": "CBT addresses anxiety..."
}


@pytest.fixture
def persona_with_timeline(client):
    """Create persona with full timeline (experience + intervention)."""
    # Create persona
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Timeline Test",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Normal childhood"
        }
    )
    persona = response.json()
    
    # Add experience at age 12
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_EXPERIENCE
        client.post(
            f"/api/v1/personas/{persona['id']}/experiences",
            json={
                "user_description": "Traumatic event at age 12",
                "age_at_event": 12
            }
        )
    
    # Add intervention at age 15
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_INTERVENTION
        client.post(
            f"/api/v1/personas/{persona['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
    
    # Add second experience at age 18
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_EXPERIENCE
        client.post(
            f"/api/v1/personas/{persona['id']}/experiences",
            json={
                "user_description": "Another event at age 18",
                "age_at_event": 18
            }
        )
    
    return persona


def test_get_timeline_success(client, persona_with_timeline):
    """Test getting complete timeline for a persona."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "persona" in data
    assert "experiences" in data
    assert "interventions" in data
    assert "snapshots" in data
    assert "timeline_events" in data
    
    # Verify persona
    assert data["persona"]["name"] == "Timeline Test"
    
    # Verify counts
    assert len(data["experiences"]) == 2
    assert len(data["interventions"]) == 1
    assert len(data["snapshots"]) >= 2  # At least one per event
    
    # Verify timeline events
    timeline = data["timeline_events"]
    assert len(timeline) == 3  # 2 experiences + 1 intervention


def test_timeline_chronological_order(client, persona_with_timeline):
    """Test that timeline events are in chronological order."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    timeline = data["timeline_events"]
    
    # Check ages are in ascending order
    ages = [event["age"] for event in timeline]
    assert ages == sorted(ages)
    
    # Verify specific order
    assert timeline[0]["age"] == 12
    assert timeline[0]["type"] == "experience"
    
    assert timeline[1]["age"] == 15
    assert timeline[1]["type"] == "intervention"
    
    assert timeline[2]["age"] == 18
    assert timeline[2]["type"] == "experience"


def test_timeline_event_structure(client, persona_with_timeline):
    """Test that timeline events have correct structure."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    timeline = data["timeline_events"]
    
    # Check experience event
    exp_event = timeline[0]
    assert exp_event["type"] == "experience"
    assert "age" in exp_event
    assert "description" in exp_event
    assert "personality_snapshot" in exp_event
    
    # Check intervention event
    int_event = timeline[1]
    assert int_event["type"] == "intervention"
    assert "age" in int_event
    assert "therapy_type" in int_event
    assert "personality_snapshot" in int_event


def test_timeline_includes_personality_snapshots(client, persona_with_timeline):
    """Test that timeline includes personality snapshots at each event."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    timeline = data["timeline_events"]
    
    # Each event should have personality snapshot
    for event in timeline:
        assert "personality_snapshot" in event
        snapshot = event["personality_snapshot"]
        assert snapshot is not None, f"Missing snapshot for {event['type']} at age {event['age']}"
        assert "personality_profile" in snapshot
        assert "trauma_markers" in snapshot
        assert "symptom_severity" in snapshot


def test_timeline_shows_personality_progression(client, persona_with_timeline):
    """Test that timeline shows personality changes over time."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    timeline = data["timeline_events"]
    
    # Get neuroticism at each point
    neuroticism_values = []
    for event in timeline:
        snapshot = event["personality_snapshot"]
        neuroticism = snapshot["personality_profile"]["neuroticism"]
        neuroticism_values.append(neuroticism)
    
    # After experience (age 12): neuroticism increases
    assert neuroticism_values[0] > 0.5  # Baseline was 0.5
    
    # After intervention (age 15): neuroticism should decrease
    assert neuroticism_values[1] < neuroticism_values[0]


def test_timeline_invalid_persona_id(client):
    """Test timeline for non-existent persona returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = client.get(f"/api/v1/personas/{fake_uuid}/timeline")
    
    assert response.status_code == 404


def test_timeline_empty_for_new_persona(client):
    """Test timeline for persona with no events is empty."""
    # Create persona
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Empty Timeline",
            "baseline_age": 20,
            "baseline_gender": "male",
            "baseline_background": "Test"
        }
    )
    persona = response.json()
    
    # Get timeline
    response = client.get(f"/api/v1/personas/{persona['id']}/timeline")
    data = response.json()
    
    assert response.status_code == 200
    assert len(data["experiences"]) == 0
    assert len(data["interventions"]) == 0
    assert len(data["timeline_events"]) == 0


def test_timeline_snapshot_symptom_tracking(client, persona_with_timeline):
    """Test that snapshots track symptom severity changes over time."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    timeline = data["timeline_events"]
    
    # First event (experience): symptoms appear
    first_snapshot = timeline[0]["personality_snapshot"]
    assert "anxiety" in first_snapshot["symptom_severity"]
    anxiety_before = first_snapshot["symptom_severity"]["anxiety"]
    
    # Second event (intervention): symptoms reduce
    second_snapshot = timeline[1]["personality_snapshot"]
    assert "anxiety" in second_snapshot["symptom_severity"]
    anxiety_after = second_snapshot["symptom_severity"]["anxiety"]
    
    # Verify reduction
    assert anxiety_after < anxiety_before


def test_timeline_includes_baseline_state(client):
    """Test that timeline can show baseline state."""
    # Create persona
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Baseline Test",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Happy childhood",
            "baseline_personality": {
                "openness": 0.7,
                "conscientiousness": 0.6,
                "extraversion": 0.8,
                "agreeableness": 0.7,
                "neuroticism": 0.3
            }
        }
    )
    persona = response.json()
    
    # Get timeline
    response = client.get(f"/api/v1/personas/{persona['id']}/timeline")
    data = response.json()
    
    # Verify baseline in persona
    assert data["persona"]["baseline_age"] == 10
    assert data["persona"]["baseline_personality"]["neuroticism"] == 0.3
    assert data["persona"]["current_personality"]["neuroticism"] == 0.3  # No changes yet


def test_timeline_experience_details(client, persona_with_timeline):
    """Test that timeline includes detailed experience information."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    # Find experience in timeline
    exp_events = [e for e in data["timeline_events"] if e["type"] == "experience"]
    
    assert len(exp_events) == 2
    
    # Check first experience details
    exp = exp_events[0]
    assert exp["description"] == "Traumatic event at age 12"
    assert "symptoms_developed" in exp
    assert "recommended_therapies" in exp


def test_timeline_intervention_details(client, persona_with_timeline):
    """Test that timeline includes detailed intervention information."""
    response = client.get(f"/api/v1/personas/{persona_with_timeline['id']}/timeline")
    data = response.json()
    
    # Find intervention in timeline
    int_events = [e for e in data["timeline_events"] if e["type"] == "intervention"]
    
    assert len(int_events) == 1
    
    # Check intervention details
    interv = int_events[0]
    assert interv["therapy_type"] == "CBT"
    assert "duration" in interv
    assert "efficacy_match" in interv
    assert "symptom_changes" in interv
