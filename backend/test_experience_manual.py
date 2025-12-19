"""Manual test for experience API with mocked AI (no real OpenAI call)."""
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

# Mock AI response
MOCK_ANALYSIS = {
    "immediate_effects": {
        "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.4,
        "agreeableness": 0.5, "neuroticism": 0.65
    },
    "long_term_patterns": ["trust_issues", "fear_of_abandonment"],
    "symptoms_developed": ["anxiety", "hypervigilance"],
    "symptom_severity": {"anxiety": 7, "hypervigilance": 5},
    "coping_mechanisms": ["journaling (adaptive)"],
    "worldview_shifts": {"trust": -0.3, "safety": -0.2},
    "cross_experience_triggers": [],
    "recommended_therapies": ["CBT", "play_therapy"],
    "reasoning": "Divorce impacts attachment and trust..."
}

print("=== TEST 1: Create Persona ===")
response = client.post("/api/v1/personas", json={
    "name": "Emma",
    "baseline_age": 8,
    "baseline_gender": "female",
    "baseline_background": "Happy childhood with both parents"
})
print(f"Status: {response.status_code}")
persona = response.json()
persona_id = persona['id']
print(f"Created: {persona['name']} (baseline neuroticism: {persona['current_personality']['neuroticism']})")

print("\n=== TEST 2: Add Experience (with mock AI) ===")
with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_ANALYSIS
    
    response = client.post(f"/api/v1/personas/{persona_id}/experiences", json={
        "user_description": "Parents divorced when I was 10",
        "age_at_event": 10
    })
    
    print(f"Status: {response.status_code}")
    experience = response.json()
    print(f"Experience #{experience['sequence_number']}: {experience['user_description']}")
    print(f"Symptoms developed: {experience['symptoms_developed']}")
    print(f"Severity: {experience['symptom_severity']}")

print("\n=== TEST 3: Check Persona Updated ===")
response = client.get(f"/api/v1/personas/{persona_id}")
updated_persona = response.json()
print(f"Current age: {updated_persona['current_age']} (was {persona['baseline_age']})")
print(f"Neuroticism: {updated_persona['current_personality']['neuroticism']} (was 0.5)")
print(f"Extraversion: {updated_persona['current_personality']['extraversion']} (was 0.5)")
print(f"Trauma markers: {updated_persona['current_trauma_markers']}")
print(f"Experience count: {updated_persona['experiences_count']}")

print("\n=== TEST 4: Get All Experiences ===")
response = client.get(f"/api/v1/personas/{persona_id}/experiences")
experiences = response.json()
print(f"Total experiences: {len(experiences)}")
for exp in experiences:
    print(f"  #{exp['sequence_number']}: {exp['user_description']} (age {exp['age_at_event']})")

print("\n✅ Experience API working with AI integration!")
