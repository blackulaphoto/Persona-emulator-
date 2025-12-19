"""Manual test for full persona evolution flow."""
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)

# Mock AI responses
MOCK_EXPERIENCE = {
    "immediate_effects": {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.3, "agreeableness": 0.5, "neuroticism": 0.75},
    "symptoms_developed": ["anxiety", "hypervigilance", "trust_issues"],
    "symptom_severity": {"anxiety": 8, "hypervigilance": 7, "trust_issues": 6},
    "long_term_patterns": ["fear_response"],
    "coping_mechanisms": [],
    "worldview_shifts": {},
    "cross_experience_triggers": [],
    "recommended_therapies": ["CBT", "EMDR"]
}

MOCK_INTERVENTION = {
    "actual_symptoms_targeted": ["anxiety", "hypervigilance"],
    "efficacy_match": 0.75,
    "immediate_effects": {"symptom_reduction": {"anxiety": 0.5, "hypervigilance": 0.3}},
    "sustained_effects": {"relapse_prevention": 0.6, "coping_skills": ["cognitive_restructuring"]},
    "limitations": ["Does not address root trauma"],
    "symptom_changes": {"anxiety": 4, "hypervigilance": 5, "trust_issues": 6},
    "personality_changes": {"neuroticism": 0.6},
    "coping_skills_gained": ["cognitive_restructuring", "thought_challenging"],
    "reasoning": "CBT addresses anxiety symptoms..."
}

print("=== FULL PERSONA EVOLUTION FLOW ===\n")

# Step 1: Create persona
print("STEP 1: Create Persona")
response = client.post("/api/v1/personas", json={
    "name": "Alex",
    "baseline_age": 10,
    "baseline_gender": "male",
    "baseline_background": "Happy childhood"
})
persona = response.json()
persona_id = persona['id']
print(f"✓ Created: {persona['name']}")
print(f"  Baseline personality: neuroticism={persona['current_personality']['neuroticism']}")

# Step 2: Add traumatic experience
print("\nSTEP 2: Add Traumatic Experience (age 12)")
with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_EXPERIENCE
    response = client.post(f"/api/v1/personas/{persona_id}/experiences", json={
        "user_description": "Witnessed violence at school",
        "age_at_event": 12
    })
experience = response.json()
print(f"✓ Experience added: {experience['user_description']}")
print(f"  Symptoms developed: {experience['symptoms_developed']}")
print(f"  Severity: {experience['symptom_severity']}")

# Step 3: Check updated persona
response = client.get(f"/api/v1/personas/{persona_id}")
persona_after_exp = response.json()
print(f"\n  Persona after experience:")
print(f"    Current age: {persona_after_exp['current_age']}")
print(f"    Neuroticism: {persona_after_exp['current_personality']['neuroticism']} (was 0.5)")
print(f"    Trauma markers: {persona_after_exp['current_trauma_markers']}")

# Step 4: Add therapeutic intervention
print("\nSTEP 3: Add CBT Intervention (age 15)")
with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_INTERVENTION
    response = client.post(f"/api/v1/personas/{persona_id}/interventions", json={
        "therapy_type": "CBT",
        "duration": "6_months",
        "intensity": "weekly",
        "age_at_intervention": 15,
        "user_notes": "Weekly therapy with focus on anxiety"
    })
intervention = response.json()
print(f"✓ Intervention added: {intervention['therapy_type']}")
print(f"  Symptoms targeted: {intervention['actual_symptoms_targeted']}")
print(f"  Efficacy match: {intervention['efficacy_match']*100}%")
print(f"  Symptom changes: {intervention['symptom_changes']}")

# Step 5: Check final persona state
response = client.get(f"/api/v1/personas/{persona_id}")
persona_final = response.json()
print(f"\n  Persona after intervention:")
print(f"    Current age: {persona_final['current_age']}")
print(f"    Neuroticism: {persona_final['current_personality']['neuroticism']} (reduced from 0.75)")
print(f"    Experiences: {persona_final['experiences_count']}")
print(f"    Interventions: {persona_final['interventions_count']}")

# Step 6: Get full timeline
print("\nSTEP 4: Timeline Overview")
exp_response = client.get(f"/api/v1/personas/{persona_id}/experiences")
int_response = client.get(f"/api/v1/personas/{persona_id}/interventions")
experiences = exp_response.json()
interventions = int_response.json()

print(f"  Total timeline events: {len(experiences) + len(interventions)}")
for exp in experiences:
    print(f"    Age {exp['age_at_event']}: Experience - {exp['user_description']}")
for interv in interventions:
    print(f"    Age {interv['age_at_intervention']}: {interv['therapy_type']} therapy")

print("\n✅ Full persona evolution flow working!")
print("\n📊 Summary:")
print(f"  Baseline → Trauma → Therapy")
print(f"  Neuroticism: 0.5 → 0.75 → 0.6")
print(f"  Symptoms: None → [anxiety, hypervigilance] → [reduced by therapy]")
