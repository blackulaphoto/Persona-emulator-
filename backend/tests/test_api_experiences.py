"""
Test Experience API endpoints.

T8: Add Experience API
TEST: POST /api/v1/personas/{id}/experiences → analyze with AI, update persona
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


@pytest.fixture
def sample_persona(client):
    """Create a sample persona for testing."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Test Person",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Happy childhood"
        }
    )
    return response.json()


# Mock AI response for testing
MOCK_AI_ANALYSIS = {
    "immediate_effects": {
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.4,
        "agreeableness": 0.5,
        "neuroticism": 0.6,
        "trait_changes": {"anxiety": 7, "trust_in_relationships": 3}
    },
    "long_term_patterns": ["fear_of_abandonment", "trust_issues"],
    "symptoms_developed": ["anxiety", "hypervigilance"],
    "symptom_severity": {"anxiety": 6, "hypervigilance": 5},
    "coping_mechanisms": ["people_pleasing (maladaptive)", "journaling (adaptive)"],
    "worldview_shifts": {"trust": -0.4, "safety": -0.3, "self_worth": -0.2},
    "cross_experience_triggers": [],
    "recommended_therapies": ["CBT", "play_therapy"],
    "reasoning": "Divorce at age 10 impacts trust and attachment..."
}


def test_add_experience_success(client, sample_persona):
    """Test adding an experience with AI analysis."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_AI_ANALYSIS
        
        response = client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Parents divorced when I was 10",
                "age_at_event": 10
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["user_description"] == "Parents divorced when I was 10"
        assert data["age_at_event"] == 10
        assert data["sequence_number"] == 1
        
        # Verify AI analysis was stored
        assert data["symptoms_developed"] == ["anxiety", "hypervigilance"]
        assert data["symptom_severity"]["anxiety"] == 6
        assert data["long_term_patterns"] == ["fear_of_abandonment", "trust_issues"]
        assert data["recommended_therapies"] == ["CBT", "play_therapy"]
        
        # Verify AI was called with correct parameters
        mock_analyze.assert_called_once()


def test_add_experience_updates_persona_personality(client, sample_persona):
    """Test that experience updates persona's personality."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_AI_ANALYSIS
        
        # Add experience
        client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Parents divorced",
                "age_at_event": 10
            }
        )
        
        # Get updated persona
        persona_response = client.get(f"/api/v1/personas/{sample_persona['id']}")
        updated_persona = persona_response.json()
        
        # Verify personality changed (neuroticism should increase to 0.6)
        assert updated_persona["current_personality"]["neuroticism"] == 0.6
        assert updated_persona["current_personality"]["extraversion"] == 0.4
        
        # Verify current_age updated
        assert updated_persona["current_age"] == 10
        
        # Verify experiences_count
        assert updated_persona["experiences_count"] == 1


def test_add_multiple_experiences_increments_sequence(client, sample_persona):
    """Test that multiple experiences get correct sequence numbers."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_AI_ANALYSIS
        
        # Add first experience
        response1 = client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Event 1",
                "age_at_event": 10
            }
        )
        assert response1.json()["sequence_number"] == 1
        
        # Add second experience
        response2 = client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Event 2",
                "age_at_event": 12
            }
        )
        assert response2.json()["sequence_number"] == 2


def test_add_experience_invalid_persona_id(client):
    """Test adding experience to non-existent persona."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = client.post(
        f"/api/v1/personas/{fake_uuid}/experiences",
        json={
            "user_description": "Test event",
            "age_at_event": 10
        }
    )
    
    assert response.status_code == 404


def test_add_experience_missing_required_fields(client, sample_persona):
    """Test that missing required fields returns 422."""
    response = client.post(
        f"/api/v1/personas/{sample_persona['id']}/experiences",
        json={
            "user_description": "Missing age"
            # Missing age_at_event
        }
    )
    
    assert response.status_code == 422


def test_add_experience_invalid_age(client, sample_persona):
    """Test that age < baseline_age or age > 120 is rejected."""
    # Age younger than baseline
    response1 = client.post(
        f"/api/v1/personas/{sample_persona['id']}/experiences",
        json={
            "user_description": "Too young",
            "age_at_event": 5  # Baseline is 10
        }
    )
    assert response1.status_code == 400
    
    # Age too old
    response2 = client.post(
        f"/api/v1/personas/{sample_persona['id']}/experiences",
        json={
            "user_description": "Too old",
            "age_at_event": 150
        }
    )
    assert response2.status_code == 422  # Pydantic validation


def test_get_persona_experiences(client, sample_persona):
    """Test getting all experiences for a persona."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_AI_ANALYSIS
        
        # Add two experiences
        client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={"user_description": "Event 1", "age_at_event": 10}
        )
        client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={"user_description": "Event 2", "age_at_event": 12}
        )
        
        # Get experiences
        response = client.get(f"/api/v1/personas/{sample_persona['id']}/experiences")
        
        assert response.status_code == 200
        experiences = response.json()
        assert len(experiences) == 2
        assert experiences[0]["sequence_number"] == 1
        assert experiences[1]["sequence_number"] == 2


def test_experience_creates_personality_snapshot(client, sample_persona):
    """Test that adding experience creates a personality snapshot."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_AI_ANALYSIS
        
        # Add experience
        client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Parents divorced",
                "age_at_event": 10
            }
        )
        
        # Get persona to check snapshot was created
        # (In future, we'll have a snapshots endpoint, but for now just verify count)
        persona_response = client.get(f"/api/v1/personas/{sample_persona['id']}")
        # Snapshots will be tested in T10 timeline endpoint


def test_add_experience_ai_failure_returns_500(client, sample_persona):
    """Test that AI analysis failure returns appropriate error."""
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = Exception("OpenAI API error")
        
        response = client.post(
            f"/api/v1/personas/{sample_persona['id']}/experiences",
            json={
                "user_description": "Test event",
                "age_at_event": 10
            }
        )
        
        assert response.status_code == 500
        assert "AI analysis failed" in response.json()["detail"]
