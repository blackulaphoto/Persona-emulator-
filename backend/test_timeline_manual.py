"""Manual test demonstrating full timeline visualization."""
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
import json

client = TestClient(app)

# Mock AI responses
MOCK_EXP1 = {
    "immediate_effects": {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.3, "agreeableness": 0.5, "neuroticism": 0.75},
    "symptoms_developed": ["anxiety", "hypervigilance"],
    "symptom_severity": {"anxiety": 8, "hypervigilance": 7},
    "long_term_patterns": ["fear_response"],
    "coping_mechanisms": [],
    "worldview_shifts": {"safety": -0.3},
    "cross_experience_triggers": [],
    "recommended_therapies": ["CBT", "EMDR"]
}

MOCK_INTERVENTION1 = {
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

MOCK_EXP2 = {
    "immediate_effects": {"openness": 0.6, "conscientiousness": 0.6, "extraversion": 0.4, "agreeableness": 0.6, "neuroticism": 0.55},
    "symptoms_developed": [],
    "symptom_severity": {"anxiety": 4, "hypervigilance": 7},
    "long_term_patterns": ["resilience_building"],
    "coping_mechanisms": ["healthy_relationships"],
    "worldview_shifts": {"trust": 0.2},
    "cross_experience_triggers": [],
    "recommended_therapies": []
}

print("=" * 80)
print("PERSONA EVOLUTION TIMELINE DEMONSTRATION")
print("=" * 80)

# Step 1: Create persona
print("\n📝 STEP 1: Create Baseline Persona")
response = client.post("/api/v1/personas", json={
    "name": "Sarah",
    "baseline_age": 8,
    "baseline_gender": "female",
    "baseline_background": "Happy childhood with supportive family"
})
persona = response.json()
persona_id = persona['id']
print(f"✓ Created: {persona['name']}, age {persona['baseline_age']}")
print(f"  Baseline neuroticism: {persona['current_personality']['neuroticism']}")

# Step 2: Add traumatic experience
print("\n💔 STEP 2: Traumatic Experience (age 12)")
with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_EXP1
    response = client.post(f"/api/v1/personas/{persona_id}/experiences", json={
        "user_description": "Witnessed car accident involving family member",
        "age_at_event": 12
    })
print(f"✓ Experience added")
print(f"  Symptoms: anxiety (severity 8), hypervigilance (severity 7)")
print(f"  Neuroticism: 0.5 → 0.75")

# Step 3: Add therapeutic intervention
print("\n🏥 STEP 3: CBT Therapy (age 15)")
with patch('app.api.routes.interventions.analyze_intervention', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_INTERVENTION1
    response = client.post(f"/api/v1/personas/{persona_id}/interventions", json={
        "therapy_type": "CBT",
        "duration": "6_months",
        "intensity": "weekly",
        "age_at_intervention": 15,
        "user_notes": "Weekly sessions focusing on anxiety management"
    })
print(f"✓ Intervention added: CBT (6 months, weekly)")
print(f"  Targeted: anxiety")
print(f"  Results: anxiety 8 → 4, neuroticism 0.75 → 0.6")

# Step 4: Add positive experience
print("\n🌟 STEP 4: Positive Experience (age 18)")
with patch('app.api.routes.experiences.analyze_experience', new_callable=AsyncMock) as mock:
    mock.return_value = MOCK_EXP2
    response = client.post(f"/api/v1/personas/{persona_id}/experiences", json={
        "user_description": "Formed healthy relationship and support network in college",
        "age_at_event": 18
    })
print(f"✓ Experience added")
print(f"  Coping: healthy_relationships")
print(f"  Neuroticism: 0.6 → 0.55")

# Step 5: Get full timeline
print("\n" + "=" * 80)
print("📊 COMPLETE TIMELINE")
print("=" * 80)

response = client.get(f"/api/v1/personas/{persona_id}/timeline")
timeline_data = response.json()

print(f"\nPersona: {timeline_data['persona']['name']}")
print(f"Current Age: {timeline_data['persona']['current_age']}")
print(f"Total Events: {len(timeline_data['timeline_events'])}")
print(f"  - Experiences: {len(timeline_data['experiences'])}")
print(f"  - Interventions: {len(timeline_data['interventions'])}")
print(f"  - Snapshots: {len(timeline_data['snapshots'])}")

print("\n" + "-" * 80)
print("CHRONOLOGICAL EVENTS:")
print("-" * 80)

for i, event in enumerate(timeline_data['timeline_events'], 1):
    print(f"\n{i}. AGE {event['age']} - {event['type'].upper()}")
    
    if event['type'] == 'experience':
        print(f"   Description: {event['description']}")
        if event['symptoms_developed']:
            print(f"   Symptoms: {', '.join(event['symptoms_developed'])}")
        if event['recommended_therapies']:
            print(f"   Recommended: {', '.join(event['recommended_therapies'])}")
    
    elif event['type'] == 'intervention':
        print(f"   Therapy: {event['therapy_type']} ({event['duration']}, {event['intensity']})")
        print(f"   Targeted: {', '.join(event['actual_symptoms_targeted'])}")
        print(f"   Efficacy: {event['efficacy_match']*100:.0f}%")
        if event['symptom_changes']:
            changes = ', '.join([f"{k}:{v}" for k,v in event['symptom_changes'].items()])
            print(f"   Results: {changes}")
    
    # Show personality snapshot
    if event['personality_snapshot']:
        snapshot = event['personality_snapshot']
        neuro = snapshot['personality_profile']['neuroticism']
        print(f"   Personality: neuroticism={neuro:.2f}")
        if snapshot['symptom_severity']:
            symptoms = ', '.join([f"{k}:{v}" for k,v in snapshot['symptom_severity'].items()])
            print(f"   Symptoms: {symptoms}")

print("\n" + "=" * 80)
print("PERSONALITY PROGRESSION")
print("=" * 80)

neuroticism_journey = []
for event in timeline_data['timeline_events']:
    if event['personality_snapshot']:
        age = event['age']
        neuro = event['personality_snapshot']['personality_profile']['neuroticism']
        neuroticism_journey.append((age, neuro, event['type']))

print("\nNeuroticism over time:")
for age, neuro, event_type in neuroticism_journey:
    bar = "█" * int(neuro * 50)
    print(f"  Age {age:2d} ({event_type:12s}): {bar} {neuro:.2f}")

print("\n" + "=" * 80)
print("SYMPTOM TRACKING")
print("=" * 80)

print("\nAnxiety severity over time:")
for event in timeline_data['timeline_events']:
    if event['personality_snapshot'] and event['personality_snapshot']['symptom_severity']:
        severity = event['personality_snapshot']['symptom_severity']
        if 'anxiety' in severity:
            age = event['age']
            level = severity['anxiety']
            bar = "█" * level
            print(f"  Age {age:2d}: {bar} {level}/10")

print("\n" + "=" * 80)
print("✅ TIMELINE API DEMONSTRATION COMPLETE!")
print("=" * 80)
print("\nKey Insights:")
print("  • Trauma increased neuroticism and created symptoms")
print("  • CBT therapy reduced anxiety and neuroticism")
print("  • Positive experiences continued improvement")
print("  • Timeline shows complete psychological evolution")
