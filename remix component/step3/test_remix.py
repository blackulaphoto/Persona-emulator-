"""
Tests for Remix Service and API

Tests timeline snapshots, comparisons, and "what if" analysis.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.core.database import Base, get_db
from app.main import app
from app.models.persona import Persona
from app.models.experience import Experience
from app.models.intervention import Intervention
from app.models.timeline_snapshot import TimelineSnapshot
from app.services.remix_service import (
    create_timeline_snapshot,
    get_persona_snapshots,
    compare_snapshots,
    calculate_intervention_impact,
    get_remix_suggestions_for_persona,
    delete_snapshot,
)


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_persona(db_session):
    """Create a sample persona for testing"""
    persona = Persona(
        name="Test Persona",
        baseline_age=5,
        current_age=10,
        baseline_personality={
            "openness": 0.5,
            "conscientiousness": 0.6,
            "extraversion": 0.4,
            "agreeableness": 0.7,
            "neuroticism": 0.5
        },
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.3,
            "agreeableness": 0.7,
            "neuroticism": 0.7
        },
        baseline_attachment_style="secure",
        current_attachment_style="anxious",
        current_trauma_markers=["social_anxiety", "fear_of_rejection"]
    )
    db_session.add(persona)
    db_session.commit()
    db_session.refresh(persona)
    return persona


# Service Tests

# Test 1: Create timeline snapshot
def test_create_timeline_snapshot(db_session, sample_persona):
    """Test creating a snapshot of persona timeline"""
    snapshot = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Original",
        description="Baseline before modifications"
    )
    
    assert snapshot.persona_id == sample_persona.id
    assert snapshot.label == "Original"
    assert snapshot.personality_snapshot == sample_persona.current_personality
    assert set(snapshot.trauma_markers_snapshot) == set(sample_persona.current_trauma_markers)
    assert snapshot.personality_difference["neuroticism"] == 0.2  # 0.7 - 0.5


# Test 2: Create snapshot with experiences
def test_create_snapshot_with_experiences(db_session, sample_persona):
    """Test snapshot captures experiences"""
    # Add experience
    experience = Experience(
        persona_id=sample_persona.id,
        sequence_number=1,
        age_at_event=7,
        user_description="Bullied at school",
        immediate_effects={"neuroticism": 0.65},
        symptoms_developed=["social_anxiety"],
        symptom_severity={"social_anxiety": 7}
    )
    db_session.add(experience)
    db_session.commit()
    
    snapshot = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="After Bullying"
    )
    
    assert len(snapshot.modified_experiences) == 1
    assert snapshot.modified_experiences[0]["age_at_event"] == 7
    assert snapshot.symptom_severity_snapshot["social_anxiety"] == 7


# Test 3: Get persona snapshots
def test_get_persona_snapshots(db_session, sample_persona):
    """Test retrieving all snapshots for a persona"""
    # Create multiple snapshots
    snapshot1 = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Original"
    )
    
    snapshot2 = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Modified"
    )
    
    snapshots = get_persona_snapshots(db_session, sample_persona.id)
    
    assert len(snapshots) == 2
    assert snapshots[0].id == snapshot1.id
    assert snapshots[1].id == snapshot2.id


# Test 4: Compare snapshots
def test_compare_snapshots(db_session, sample_persona):
    """Test comparing two timeline snapshots"""
    # Create baseline snapshot
    snapshot1 = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Baseline"
    )
    
    # Modify persona
    sample_persona.current_personality["neuroticism"] = 0.5  # Improved
    sample_persona.current_trauma_markers = ["social_anxiety"]  # fear_of_rejection resolved
    db_session.commit()
    
    # Create after-intervention snapshot
    snapshot2 = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="After CBT"
    )
    
    # Compare
    comparison = compare_snapshots(
        db=db_session,
        snapshot_id_1=snapshot1.id,
        snapshot_id_2=snapshot2.id
    )
    
    assert comparison["personality_differences"]["neuroticism"]["difference"] == -0.2
    assert comparison["personality_differences"]["neuroticism"]["change_direction"] == "decreased"
    assert "fear_of_rejection" in comparison["symptom_differences"]["only_in_snapshot_1"]
    assert "resolved" in comparison["summary"].lower()


# Test 5: Calculate intervention impact
def test_calculate_intervention_impact(db_session, sample_persona):
    """Test analyzing intervention effectiveness"""
    # Create baseline snapshot
    baseline = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Pre-intervention"
    )
    
    # Add intervention
    intervention = Intervention(
        persona_id=sample_persona.id,
        age_at_intervention=11,
        therapy_type="CBT",
        duration="6_months",
        intensity="weekly",
        target_symptoms=["social_anxiety", "fear_of_rejection"]
    )
    db_session.add(intervention)
    
    # Modify persona (simulate intervention effect)
    sample_persona.current_personality["neuroticism"] = 0.55
    sample_persona.current_trauma_markers = ["social_anxiety"]  # One resolved
    db_session.commit()
    
    # Calculate impact
    impact = calculate_intervention_impact(
        db=db_session,
        persona_id=sample_persona.id,
        baseline_snapshot_id=baseline.id
    )
    
    assert impact["interventions_applied"] == 1
    assert "fear_of_rejection" in impact["symptom_changes"]["resolved"]
    assert impact["personality_changes"]["neuroticism"]["change"] == 0.05  # 0.55 - 0.5


# Test 6: Get remix suggestions
def test_get_remix_suggestions(db_session, sample_persona):
    """Test generating remix suggestions"""
    # Add experience
    experience = Experience(
        persona_id=sample_persona.id,
        sequence_number=1,
        age_at_event=8,
        user_description="Traumatic event",
        symptoms_developed=["anxiety", "hypervigilance", "avoidance"]
    )
    db_session.add(experience)
    db_session.commit()
    
    suggestions = get_remix_suggestions_for_persona(
        db=db_session,
        persona_id=sample_persona.id
    )
    
    assert len(suggestions) > 0
    assert any("Early Intervention" in s["title"] for s in suggestions)


# Test 7: Delete snapshot
def test_delete_snapshot(db_session, sample_persona):
    """Test deleting a timeline snapshot"""
    snapshot = create_timeline_snapshot(
        db=db_session,
        persona_id=sample_persona.id,
        label="Test"
    )
    
    deleted = delete_snapshot(db_session, snapshot.id)
    assert deleted is True
    
    # Verify deleted
    result = db_session.query(TimelineSnapshot).filter(
        TimelineSnapshot.id == snapshot.id
    ).first()
    assert result is None


# API Tests (require feature flag mock)

from unittest.mock import patch


@pytest.fixture
def enable_remix_flag():
    """Enable remix feature flag for tests"""
    with patch('app.api.routes.remix.FeatureFlags.is_enabled', return_value=True):
        yield


# Test 8: Create snapshot via API
def test_api_create_snapshot(client, db_session, sample_persona, enable_remix_flag):
    """Test creating snapshot via API"""
    request_data = {
        "persona_id": str(sample_persona.id),
        "label": "Test Snapshot",
        "description": "Test description",
        "modifications": []
    }
    
    response = client.post("/api/v1/remix/snapshots", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Test Snapshot"
    assert data["persona_id"] == str(sample_persona.id)


# Test 9: List snapshots via API
def test_api_list_snapshots(client, db_session, sample_persona, enable_remix_flag):
    """Test listing persona snapshots via API"""
    # Create snapshots
    create_timeline_snapshot(db_session, sample_persona.id, "Snapshot 1")
    create_timeline_snapshot(db_session, sample_persona.id, "Snapshot 2")
    
    response = client.get(f"/api/v1/remix/personas/{sample_persona.id}/snapshots")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# Test 10: Get single snapshot via API
def test_api_get_snapshot(client, db_session, sample_persona, enable_remix_flag):
    """Test getting snapshot details via API"""
    snapshot = create_timeline_snapshot(db_session, sample_persona.id, "Test")
    
    response = client.get(f"/api/v1/remix/snapshots/{snapshot.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == snapshot.id
    assert data["label"] == "Test"


# Test 11: Compare snapshots via API
def test_api_compare_snapshots(client, db_session, sample_persona, enable_remix_flag):
    """Test comparing snapshots via API"""
    snapshot1 = create_timeline_snapshot(db_session, sample_persona.id, "Before")
    
    # Modify persona
    sample_persona.current_personality["neuroticism"] = 0.5
    db_session.commit()
    
    snapshot2 = create_timeline_snapshot(db_session, sample_persona.id, "After")
    
    request_data = {
        "snapshot_id_1": snapshot1.id,
        "snapshot_id_2": snapshot2.id
    }
    
    response = client.post("/api/v1/remix/snapshots/compare", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "personality_differences" in data
    assert "summary" in data


# Test 12: Get intervention impact via API
def test_api_intervention_impact(client, db_session, sample_persona, enable_remix_flag):
    """Test getting intervention impact via API"""
    baseline = create_timeline_snapshot(db_session, sample_persona.id, "Baseline")
    
    # Add intervention
    intervention = Intervention(
        persona_id=sample_persona.id,
        age_at_intervention=12,
        therapy_type="DBT",
        duration="1_year",
        intensity="weekly",
        target_symptoms=["emotional_dysregulation"]
    )
    db_session.add(intervention)
    db_session.commit()
    
    response = client.get(
        f"/api/v1/remix/personas/{sample_persona.id}/intervention-impact",
        params={"baseline_snapshot_id": baseline.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["interventions_applied"] == 1
    assert "personality_changes" in data


# Test 13: Get remix suggestions via API
def test_api_remix_suggestions(client, db_session, sample_persona, enable_remix_flag):
    """Test getting remix suggestions via API"""
    response = client.get(f"/api/v1/remix/personas/{sample_persona.id}/suggestions")
    
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


# Test 14: Delete snapshot via API
def test_api_delete_snapshot(client, db_session, sample_persona, enable_remix_flag):
    """Test deleting snapshot via API"""
    snapshot = create_timeline_snapshot(db_session, sample_persona.id, "To Delete")
    
    response = client.delete(f"/api/v1/remix/snapshots/{snapshot.id}")
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]


# Test 15: Invalid persona ID returns 400
def test_api_invalid_persona_id(client, db_session, enable_remix_flag):
    """Test that invalid persona ID returns 400"""
    request_data = {
        "persona_id": "invalid-id",
        "label": "Test"
    }
    
    response = client.post("/api/v1/remix/snapshots", json=request_data)
    assert response.status_code == 400


# Test 16: Feature flag disabled returns 404
def test_api_feature_disabled(client, db_session, sample_persona):
    """Test that endpoints return 404 when feature disabled"""
    response = client.get(f"/api/v1/remix/personas/{sample_persona.id}/snapshots")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
