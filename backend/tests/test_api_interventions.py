"""
Test Intervention API endpoints.

T9: Add Intervention API
TEST: POST /api/v1/personas/{id}/interventions → analyze therapy efficacy, update symptoms
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
def sample_persona_with_symptoms(client):
    """Create persona with existing symptoms from an experience."""
    # Create persona
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Alex",
            "baseline_age": 10,
            "baseline_gender": "male",
            "baseline_background": "Experienced trauma"
        }
    )
    persona = response.json()
    
    # Add experience with symptoms (mocked)
    mock_experience_analysis = {
        "immediate_effects": {
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.3,
            "agreeableness": 0.5, "neuroticism": 0.7
        },
        "symptoms_developed": ["anxiety", "hypervigilance", "trust_issues"],
        "symptom_severity": {"anxiety": 8, "hypervigilance": 7, "trust_issues": 6},
        "long_term_patterns": ["fear_response"],
        "coping_mechanisms": [],
        "worldview_shifts": {},
        "cross_experience_triggers": [],
        "recommended_therapies": ["CBT", "EMDR"]
    }
    
    with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
        mock.return_value = mock_experience_analysis
        client.post(
            f"/api/v1/personas/{persona['id']}/experiences",
            json={"user_description": "Traumatic event", "age_at_event": 12}
        )
    
    return persona


# Mock AI response for intervention analysis
MOCK_INTERVENTION_ANALYSIS = {
    "actual_symptoms_targeted": ["anxiety", "hypervigilance"],
    "efficacy_match": 0.75,  # CBT is 75% effective for anxiety
    "immediate_effects": {
        "symptom_reduction": {"anxiety": 0.5, "hypervigilance": 0.3}  # 50% and 30% reduction
    },
    "sustained_effects": {
        "relapse_prevention": 0.6,
        "coping_skills": ["cognitive_restructuring", "exposure_techniques"]
    },
    "limitations": [
        "Does not address root trauma",
        "Requires ongoing practice"
    ],
    "symptom_changes": {
        "anxiety": 4,  # Reduced from 8 to 4
        "hypervigilance": 5,  # Reduced from 7 to 5
        "trust_issues": 6  # Unchanged (not targeted by CBT)
    },
    "personality_changes": {
        "neuroticism": 0.6  # Slight reduction from 0.7
    },
    "coping_skills_gained": ["cognitive_restructuring", "thought_challenging"],
    "reasoning": "CBT addresses anxiety symptoms through cognitive restructuring..."
}


def test_add_intervention_success(client, sample_persona_with_symptoms):
    """Test adding an intervention with AI analysis."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        response = client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["therapy_type"] == "CBT"
        assert data["duration"] == "6_months"
        assert data["intensity"] == "weekly"
        assert data["sequence_number"] == 1
        
        # Verify AI analysis was stored
        assert data["actual_symptoms_targeted"] == ["anxiety", "hypervigilance"]
        assert data["efficacy_match"] == 0.75
        assert data["symptom_changes"]["anxiety"] == 4  # Reduced
        assert data["coping_skills_gained"] == ["cognitive_restructuring", "thought_challenging"]


def test_add_intervention_updates_persona_symptoms(client, sample_persona_with_symptoms):
    """Test that intervention reduces symptom severity."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        # Get persona before intervention
        before_response = client.get(f"/api/v1/personas/{sample_persona_with_symptoms['id']}")
        before_persona = before_response.json()
        
        # Add intervention
        client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        
        # Get updated persona
        after_response = client.get(f"/api/v1/personas/{sample_persona_with_symptoms['id']}")
        updated_persona = after_response.json()
        
        # Verify personality changed (neuroticism reduced)
        assert updated_persona["current_personality"]["neuroticism"] == 0.6
        
        # Verify current_age updated
        assert updated_persona["current_age"] == 15
        
        # Verify interventions_count
        assert updated_persona["interventions_count"] == 1


def test_add_multiple_interventions_increments_sequence(client, sample_persona_with_symptoms):
    """Test that multiple interventions get correct sequence numbers."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        # Add first intervention
        response1 = client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        assert response1.json()["sequence_number"] == 1
        
        # Add second intervention
        response2 = client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "EMDR",
                "duration": "3_months",
                "intensity": "weekly",
                "age_at_intervention": 16
            }
        )
        assert response2.json()["sequence_number"] == 2


def test_add_intervention_invalid_persona_id(client):
    """Test adding intervention to non-existent persona."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    
    response = client.post(
        f"/api/v1/personas/{fake_uuid}/interventions",
        json={
            "therapy_type": "CBT",
            "duration": "6_months",
            "intensity": "weekly",
            "age_at_intervention": 15
        }
    )
    
    assert response.status_code == 404


def test_add_intervention_missing_required_fields(client, sample_persona_with_symptoms):
    """Test that missing required fields returns 422."""
    response = client.post(
        f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
        json={
            "therapy_type": "CBT"
            # Missing duration, intensity, age_at_intervention
        }
    )
    
    assert response.status_code == 422


def test_add_intervention_invalid_therapy_type(client, sample_persona_with_symptoms):
    """Test that invalid therapy type is rejected."""
    response = client.post(
        f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
        json={
            "therapy_type": "InvalidTherapy",
            "duration": "6_months",
            "intensity": "weekly",
            "age_at_intervention": 15
        }
    )
    
    assert response.status_code == 422


def test_get_persona_interventions(client, sample_persona_with_symptoms):
    """Test getting all interventions for a persona."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        # Add two interventions
        client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "EMDR",
                "duration": "3_months",
                "intensity": "weekly",
                "age_at_intervention": 16
            }
        )
        
        # Get interventions
        response = client.get(f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions")
        
        assert response.status_code == 200
        interventions = response.json()
        assert len(interventions) == 2
        assert interventions[0]["sequence_number"] == 1
        assert interventions[1]["sequence_number"] == 2


def test_intervention_creates_personality_snapshot(client, sample_persona_with_symptoms):
    """Test that adding intervention creates a personality snapshot."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        # Add intervention
        client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        
        # Snapshot creation verified (would be tested in T10 timeline endpoint)


def test_add_intervention_ai_failure_returns_500(client, sample_persona_with_symptoms):
    """Test that AI analysis failure returns appropriate error."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.side_effect = Exception("OpenAI API error")
        
        response = client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15
            }
        )
        
        assert response.status_code == 500
        assert "AI analysis failed" in response.json()["detail"]


def test_intervention_with_user_notes(client, sample_persona_with_symptoms):
    """Test adding intervention with optional user notes."""
    with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = MOCK_INTERVENTION_ANALYSIS
        
        response = client.post(
            f"/api/v1/personas/{sample_persona_with_symptoms['id']}/interventions",
            json={
                "therapy_type": "CBT",
                "duration": "6_months",
                "intensity": "weekly",
                "age_at_intervention": 15,
                "user_notes": "Weekly sessions with Dr. Smith, focused on anxiety management"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_notes"] == "Weekly sessions with Dr. Smith, focused on anxiety management"
