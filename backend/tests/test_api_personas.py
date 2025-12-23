"""
Test Persona API endpoints.

T7: Create Persona API
TEST: POST /personas → assert 201, persona created in DB with baseline personality
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


def test_create_persona_success(client):
    """Test creating a persona with valid data."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Emma",
            "baseline_age": 8,
            "baseline_gender": "female",
            "baseline_background": "Neutral upbringing."
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify response structure
    assert "id" in data
    assert data["name"] == "Emma"
    assert data["baseline_age"] == 8
    assert data["current_age"] == 8
    
    # Verify neutral baseline when no signals are detected
    assert data["current_personality"]["openness"] == 0.5
    assert data["current_personality"]["conscientiousness"] == 0.5
    assert data["current_personality"]["extraversion"] == 0.5
    assert data["current_personality"]["agreeableness"] == 0.5
    assert data["current_personality"]["neuroticism"] == 0.5
    
    # Verify baseline attachment
    assert data["current_attachment_style"] == "secure"
    assert data["current_trauma_markers"] == []


def test_create_persona_with_custom_baseline(client):
    """Test creating persona with custom baseline personality."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Alex",
            "baseline_age": 25,
            "baseline_gender": "non-binary",
            "baseline_background": "Complex childhood",
            "baseline_personality": {
                "openness": 0.7,
                "conscientiousness": 0.4,
                "extraversion": 0.3,
                "agreeableness": 0.6,
                "neuroticism": 0.6
            },
            "baseline_attachment_style": "insecure-anxious"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["current_personality"]["openness"] == 0.6
    assert data["current_personality"]["conscientiousness"] == 0.4
    assert data["current_personality"]["extraversion"] == 0.4
    assert data["current_personality"]["agreeableness"] == 0.6
    assert data["current_personality"]["neuroticism"] == 0.6
    assert data["current_attachment_style"] == "insecure-anxious"


def test_create_persona_baseline_bias_from_environment(client):
    """Test that early environment slightly biases baseline traits."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Nora",
            "baseline_age": 9,
            "baseline_gender": "female",
            "baseline_background": (
                "A stable, supportive home with reliable caregivers in a peaceful community. "
                "She had friendly peers and was encouraged to try new things."
            )
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["current_personality"]["openness"] == 0.52
    assert data["current_personality"]["conscientiousness"] == 0.52
    assert data["current_personality"]["extraversion"] == 0.54
    assert data["current_personality"]["agreeableness"] == 0.53
    assert data["current_personality"]["neuroticism"] == 0.4


def test_create_persona_baseline_clamped(client):
    """Test that extreme environment stays within 0.4-0.6 bounds."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Leo",
            "baseline_age": 7,
            "baseline_gender": "male",
            "baseline_background": (
                "An abusive, chaotic, unstable, violent home with unreliable caregivers. "
                "Inconsistent support, bullying, and discouraged, restricted curiosity."
            )
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["current_personality"]["openness"] == 0.46
    assert data["current_personality"]["conscientiousness"] == 0.46
    assert data["current_personality"]["extraversion"] == 0.44
    assert data["current_personality"]["agreeableness"] == 0.44
    assert data["current_personality"]["neuroticism"] == 0.6


def test_create_persona_missing_required_fields(client):
    """Test that missing required fields returns 422."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Incomplete"
            # Missing baseline_age, baseline_gender, baseline_background
        }
    )
    
    assert response.status_code == 422


def test_create_persona_invalid_personality_values(client):
    """Test that personality values outside 0.0-1.0 are rejected."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Invalid",
            "baseline_age": 20,
            "baseline_gender": "male",
            "baseline_background": "Test",
            "baseline_personality": {
                "openness": 1.5,  # Invalid: > 1.0
                "conscientiousness": -0.1,  # Invalid: < 0.0
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            }
        }
    )
    
    assert response.status_code == 422


def test_get_persona_by_id(client):
    """Test retrieving a persona by ID."""
    # Create persona
    create_response = client.post(
        "/api/v1/personas",
        json={
            "name": "Test Person",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Test background"
        }
    )
    persona_id = create_response.json()["id"]
    
    # Get persona
    response = client.get(f"/api/v1/personas/{persona_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == persona_id
    assert data["name"] == "Test Person"


def test_get_persona_not_found(client):
    """Test getting non-existent persona returns 404."""
    # Use a valid UUID that doesn't exist in the database
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/personas/{fake_uuid}")
    assert response.status_code == 404


def test_list_personas(client):
    """Test listing all personas."""
    # Create multiple personas
    client.post("/api/v1/personas", json={
        "name": "Person 1", "baseline_age": 10, "baseline_gender": "female", "baseline_background": "Test"
    })
    client.post("/api/v1/personas", json={
        "name": "Person 2", "baseline_age": 20, "baseline_gender": "male", "baseline_background": "Test"
    })
    
    # List personas
    response = client.get("/api/v1/personas")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Person 1"
    assert data[1]["name"] == "Person 2"


def test_update_persona(client):
    """Test updating persona details."""
    # Create persona
    create_response = client.post(
        "/api/v1/personas",
        json={
            "name": "Original Name",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Original background"
        }
    )
    persona_id = create_response.json()["id"]
    
    # Update persona
    response = client.put(
        f"/api/v1/personas/{persona_id}",
        json={
            "name": "Updated Name",
            "baseline_background": "Updated background"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["baseline_background"] == "Updated background"
    assert data["baseline_age"] == 10  # Unchanged


def test_delete_persona(client):
    """Test deleting a persona."""
    # Create persona
    create_response = client.post(
        "/api/v1/personas",
        json={
            "name": "To Delete",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Test"
        }
    )
    persona_id = create_response.json()["id"]
    
    # Delete persona
    response = client.delete(f"/api/v1/personas/{persona_id}")
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(f"/api/v1/personas/{persona_id}")
    assert get_response.status_code == 404


def test_persona_includes_experiences_count(client):
    """Test that persona response includes experience count."""
    # Create persona
    create_response = client.post(
        "/api/v1/personas",
        json={
            "name": "Test",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Test"
        }
    )
    
    data = create_response.json()
    assert "experiences_count" in data
    assert data["experiences_count"] == 0


def test_persona_created_at_timestamp(client):
    """Test that persona has created_at timestamp."""
    response = client.post(
        "/api/v1/personas",
        json={
            "name": "Test",
            "baseline_age": 10,
            "baseline_gender": "female",
            "baseline_background": "Test"
        }
    )
    
    data = response.json()
    assert "created_at" in data
    assert data["created_at"] is not None
