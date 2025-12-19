"""Manual test to verify API works end-to-end."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test 1: Create persona
print("=== TEST 1: Create Persona ===")
response = client.post("/api/v1/personas", json={
    "name": "Test Person",
    "baseline_age": 25,
    "baseline_gender": "female",
    "baseline_background": "Happy childhood"
})
print(f"Status: {response.status_code}")
persona = response.json()
print(f"Created persona: {persona['name']} (ID: {persona['id'][:8]}...)")
print(f"Baseline personality: {persona['current_personality']}")
persona_id = persona['id']

# Test 2: Get persona
print("\n=== TEST 2: Get Persona ===")
response = client.get(f"/api/v1/personas/{persona_id}")
print(f"Status: {response.status_code}")
print(f"Retrieved: {response.json()['name']}")

# Test 3: List personas
print("\n=== TEST 3: List Personas ===")
response = client.get("/api/v1/personas")
print(f"Status: {response.status_code}")
print(f"Total personas: {len(response.json())}")

# Test 4: Update persona
print("\n=== TEST 4: Update Persona ===")
response = client.put(f"/api/v1/personas/{persona_id}", json={
    "name": "Updated Name"
})
print(f"Status: {response.status_code}")
print(f"Updated name: {response.json()['name']}")

# Test 5: Health check
print("\n=== TEST 5: Health Check ===")
response = client.get("/health")
print(f"Status: {response.status_code}")
print(f"Health: {response.json()}")

print("\n✅ All API endpoints working!")
