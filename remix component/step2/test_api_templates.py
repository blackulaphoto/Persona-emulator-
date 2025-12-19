"""
Tests for Template API Routes

Following test patterns from T7 (personas), T8 (experiences), T9 (interventions).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from app.core.database import Base, get_db
from app.main import app
from app.models.persona import Persona
from app.models.clinical_template import ClinicalTemplate
from app.services.template_service import populate_templates_database


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


@pytest.fixture(scope="function")
def enable_feature_flag():
    """Enable clinical templates feature flag for tests"""
    with patch('app.api.routes.templates.FeatureFlags.is_enabled', return_value=True):
        yield


# Test 1: List templates (empty database)
def test_list_templates_populates_database(client, db_session, enable_feature_flag):
    """Test that listing templates populates database on first call"""
    response = client.get("/api/v1/templates")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Should have BPD, C-PTSD, Social Anxiety minimum
    assert any(t["disorder_type"] == "BPD" for t in data)


# Test 2: List templates with disorder filter
def test_list_templates_with_filter(client, db_session, enable_feature_flag):
    """Test filtering templates by disorder type"""
    # First populate
    populate_templates_database(db_session)
    
    # Filter for BPD only
    response = client.get("/api/v1/templates?disorder_type=BPD")
    
    assert response.status_code == 200
    data = response.json()
    assert all(t["disorder_type"] == "BPD" for t in data)


# Test 3: Get template details
def test_get_template_details(client, db_session, enable_feature_flag):
    """Test getting detailed template information"""
    # Populate templates
    populate_templates_database(db_session)
    
    response = client.get("/api/v1/templates/bpd_classic_pathway")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "bpd_classic_pathway"
    assert data["disorder_type"] == "BPD"
    assert "predefined_experiences" in data
    assert len(data["predefined_experiences"]) == 7
    assert "expected_outcomes" in data


# Test 4: Get nonexistent template returns 404
def test_get_nonexistent_template(client, db_session, enable_feature_flag):
    """Test that requesting nonexistent template returns 404"""
    response = client.get("/api/v1/templates/nonexistent_template")
    
    assert response.status_code == 404


# Test 5: Get disorder types
def test_get_disorder_types(client, db_session, enable_feature_flag):
    """Test getting list of disorder types"""
    response = client.get("/api/v1/templates/meta/disorder-types")
    
    assert response.status_code == 200
    data = response.json()
    assert "BPD" in data
    assert "C-PTSD" in data
    assert "Social_Anxiety" in data


# Test 6: Create persona from template
def test_create_persona_from_template(client, db_session, enable_feature_flag):
    """Test creating persona from BPD template"""
    # Populate templates
    populate_templates_database(db_session)
    
    request_data = {
        "template_id": "bpd_classic_pathway",
        "custom_name": "Test BPD Case"
    }
    
    response = client.post("/api/v1/templates/create-persona", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["template_id"] == "bpd_classic_pathway"
    assert data["persona_name"] == "Test BPD Case"
    assert data["baseline_age"] == 2
    assert data["baseline_personality"]["neuroticism"] == 0.75
    assert data["predefined_experiences_available"] == 7
    
    # Verify persona created in database
    persona = db_session.query(Persona).filter(
        Persona.name == "Test BPD Case"
    ).first()
    assert persona is not None


# Test 7: Create persona without custom name uses default
def test_create_persona_default_name(client, db_session, enable_feature_flag):
    """Test persona creation uses disorder type if no custom name"""
    populate_templates_database(db_session)
    
    request_data = {
        "template_id": "bpd_classic_pathway"
    }
    
    response = client.post("/api/v1/templates/create-persona", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "BPD" in data["persona_name"]


# Test 8: Create persona from nonexistent template returns 404
def test_create_persona_nonexistent_template(client, db_session, enable_feature_flag):
    """Test creating persona from nonexistent template fails"""
    request_data = {
        "template_id": "nonexistent_template"
    }
    
    response = client.post("/api/v1/templates/create-persona", json=request_data)
    
    assert response.status_code == 404


# Test 9: Apply experience set with mocked AI
@pytest.mark.asyncio
async def test_apply_experience_set(client, db_session, enable_feature_flag):
    """Test applying multiple experiences from template"""
    # Create persona first
    populate_templates_database(db_session)
    persona = Persona(
        name="Test Persona",
        baseline_age=2,
        current_age=2,
        baseline_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        },
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5
        },
        baseline_attachment_style="secure",
        current_attachment_style="secure",
        current_trauma_markers=[]
    )
    db_session.add(persona)
    db_session.commit()
    db_session.refresh(persona)
    
    # Mock AI analysis
    mock_analysis = {
        "immediate_effects": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.4,
            "agreeableness": 0.5,
            "neuroticism": 0.65
        },
        "long_term_patterns": ["trust_issues"],
        "symptoms_developed": ["anxiety"],
        "symptom_severity": {"anxiety": 6},
        "coping_mechanisms": ["avoidance"],
        "worldview_shifts": {"trust": -0.3},
        "cross_experience_triggers": [],
        "recommended_therapies": ["CBT"]
    }
    
    with patch('app.api.routes.templates.analyze_experience', new=AsyncMock(return_value=mock_analysis)):
        request_data = {
            "template_id": "bpd_classic_pathway",
            "experience_indices": [0, 1]  # Apply first 2 experiences only
        }
        
        response = client.post(
            f"/api/v1/templates/personas/{persona.id}/apply-experiences",
            json=request_data
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["experiences_applied"] == 2
    assert len(data["experience_ids"]) == 2
    assert data["personality_before"]["neuroticism"] == 0.5
    # After 2 experiences, neuroticism should have increased
    assert "neuroticism" in data["personality_after"]


# Test 10: Apply all experiences (no indices specified)
@pytest.mark.asyncio
async def test_apply_all_experiences(client, db_session, enable_feature_flag):
    """Test applying all experiences when indices not specified"""
    # Create persona
    populate_templates_database(db_session)
    persona = Persona(
        name="Test All Experiences",
        baseline_age=5,
        current_age=5,
        baseline_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.3,
            "agreeableness": 0.7,
            "neuroticism": 0.6
        },
        current_personality={
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.3,
            "agreeableness": 0.7,
            "neuroticism": 0.6
        },
        baseline_attachment_style="secure",
        current_attachment_style="secure",
        current_trauma_markers=[]
    )
    db_session.add(persona)
    db_session.commit()
    db_session.refresh(persona)
    
    # Mock AI
    mock_analysis = {
        "immediate_effects": {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.25,
            "agreeableness": 0.7,
            "neuroticism": 0.7
        },
        "long_term_patterns": ["social_anxiety"],
        "symptoms_developed": ["fear_of_evaluation"],
        "symptom_severity": {"fear_of_evaluation": 7},
        "coping_mechanisms": ["avoidance"],
        "worldview_shifts": {},
        "cross_experience_triggers": [],
        "recommended_therapies": ["CBT"]
    }
    
    with patch('app.api.routes.templates.analyze_experience', new=AsyncMock(return_value=mock_analysis)):
        request_data = {
            "template_id": "social_anxiety_developmental"
            # No experience_indices - should apply all
        }
        
        response = client.post(
            f"/api/v1/templates/personas/{persona.id}/apply-experiences",
            json=request_data
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["experiences_applied"] == 8  # Social anxiety template has 8 experiences


# Test 11: Apply experiences with invalid persona ID
def test_apply_experiences_invalid_persona_id(client, db_session, enable_feature_flag):
    """Test that invalid persona ID returns 400"""
    request_data = {
        "template_id": "bpd_classic_pathway"
    }
    
    response = client.post(
        "/api/v1/templates/personas/invalid-id/apply-experiences",
        json=request_data
    )
    
    assert response.status_code == 400


# Test 12: Apply experiences with nonexistent persona
def test_apply_experiences_nonexistent_persona(client, db_session, enable_feature_flag):
    """Test that nonexistent persona returns 404"""
    from uuid import uuid4
    
    request_data = {
        "template_id": "bpd_classic_pathway"
    }
    
    response = client.post(
        f"/api/v1/templates/personas/{uuid4()}/apply-experiences",
        json=request_data
    )
    
    assert response.status_code == 404


# Test 13: Apply experiences with invalid index
def test_apply_experiences_invalid_index(client, db_session, enable_feature_flag):
    """Test that out-of-range index returns 400"""
    populate_templates_database(db_session)
    persona = Persona(
        name="Test",
        baseline_age=2,
        current_age=2,
        baseline_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        current_personality={"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.5},
        baseline_attachment_style="secure",
        current_attachment_style="secure",
        current_trauma_markers=[]
    )
    db_session.add(persona)
    db_session.commit()
    
    request_data = {
        "template_id": "bpd_classic_pathway",
        "experience_indices": [0, 99]  # Index 99 doesn't exist
    }
    
    response = client.post(
        f"/api/v1/templates/personas/{persona.id}/apply-experiences",
        json=request_data
    )
    
    assert response.status_code == 400
    assert "out of range" in response.json()["detail"].lower()


# Test 14: Feature flag disabled returns 404
def test_feature_flag_disabled(client, db_session):
    """Test that endpoints return 404 when feature flag disabled"""
    # Don't enable feature flag
    response = client.get("/api/v1/templates")
    
    assert response.status_code == 404
    assert "not enabled" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
