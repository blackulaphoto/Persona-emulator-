"""
Full Integration Test Suite

Tests all functionality:
1. Persona creation
2. Experience/event addition
3. Intervention addition
4. Templates API (with feature flags)
5. Remix/snapshot functionality
"""
import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional

# Set feature flags for testing
os.environ['FEATURE_CLINICAL_TEMPLATES'] = 'true'
os.environ['FEATURE_REMIX_TIMELINE'] = 'true'

API_BASE = os.getenv('API_BASE', 'http://localhost:8000/api/v1')

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str):
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"{Colors.BOLD}TEST: {name}{Colors.END}")
    print(f"{'='*80}{Colors.END}")

def print_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS: {msg}{Colors.END}")

def print_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL: {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")

def check_server():
    """Check if backend server is running."""
    try:
        response = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=2)
        if response.status_code == 200:
            print_pass("Backend server is running")
            return True
        else:
            print_fail(f"Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_fail(f"Cannot connect to backend server: {e}")
        print_info("Make sure backend is running: cd backend && uvicorn app.main:app --reload")
        return False

# Test results tracker
test_results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def run_test(name: str, test_func):
    """Run a test and track results."""
    try:
        result = test_func()
        if result:
            test_results['passed'] += 1
            test_results['tests'].append({'name': name, 'status': 'PASS'})
            print_pass(name)
            return True
        else:
            test_results['failed'] += 1
            test_results['tests'].append({'name': name, 'status': 'FAIL'})
            print_fail(name)
            return False
    except Exception as e:
        test_results['failed'] += 1
        test_results['tests'].append({'name': name, 'status': 'ERROR', 'error': str(e)})
        print_fail(f"{name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# TEST 1: Persona Creation
# ============================================================================

def test_create_persona():
    """Test creating a persona."""
    print_test("Creating Persona")
    
    data = {
        "name": "Test Persona",
        "baseline_age": 10,
        "baseline_gender": "female",
        "baseline_background": "Test background"
    }
    
    response = requests.post(f"{API_BASE}/personas", json=data)
    
    if response.status_code == 201:
        persona = response.json()
        print_pass(f"Persona created: {persona.get('name')} (ID: {persona.get('id')})")
        print_info(f"Current age: {persona.get('current_age')}, Personality: {persona.get('current_personality')}")
        return persona
    else:
        print_fail(f"Failed to create persona: {response.status_code} - {response.text}")
        return None

# ============================================================================
# TEST 2: Add Experience/Event
# ============================================================================

def test_add_experience(persona_id: str):
    """Test adding an experience to a persona."""
    print_test("Adding Experience/Event")
    
    data = {
        "description": "Parents divorced when persona was 12 years old. Family conflict and instability.",
        "age_at_event": 12
    }
    
    response = requests.post(f"{API_BASE}/personas/{persona_id}/experiences", json=data)
    
    if response.status_code == 201:
        experience = response.json()
        print_pass(f"Experience added at age {experience.get('age_at_event')}")
        print_info(f"Symptoms developed: {experience.get('symptoms_developed', [])}")
        return experience
    else:
        print_fail(f"Failed to add experience: {response.status_code} - {response.text}")
        return None

# ============================================================================
# TEST 3: Add Intervention
# ============================================================================

def test_add_intervention(persona_id: str):
    """Test adding an intervention."""
    print_test("Adding Intervention")
    
    data = {
        "therapy_type": "CBT",
        "duration": "6_months",
        "intensity": "weekly",
        "age_at_intervention": 16
    }
    
    response = requests.post(f"{API_BASE}/personas/{persona_id}/interventions", json=data)
    
    if response.status_code == 201:
        intervention = response.json()
        print_pass(f"Intervention added: {intervention.get('therapy_type')} at age {intervention.get('age_at_intervention')}")
        print_info(f"Efficacy match: {intervention.get('efficacy_match')}")
        return intervention
    else:
        print_fail(f"Failed to add intervention: {response.status_code} - {response.text}")
        if response.status_code == 500:
            try:
                error_detail = response.json()
                print_info(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print_info(f"Error response: {response.text}")
        return None

# ============================================================================
# TEST 4: Templates API (with feature flags)
# ============================================================================

def test_templates_api():
    """Test templates API endpoints."""
    print_test("Templates API")
    
    # Test list templates
    response = requests.get(f"{API_BASE}/templates")
    
    if response.status_code == 200:
        templates = response.json()
        print_pass(f"List templates: Found {len(templates)} templates")
        if templates:
            print_info(f"First template: {templates[0].get('name')} ({templates[0].get('disorder_type')})")
            return templates[0].get('id')
        return None
    elif response.status_code == 404:
        print_info("Templates feature is disabled (404) - this is expected if FEATURE_CLINICAL_TEMPLATES=false")
        return None
    else:
        print_fail(f"Failed to list templates: {response.status_code} - {response.text}")
        return None

def test_template_details(template_id: str):
    """Test getting template details."""
    if not template_id:
        return False
        
    response = requests.get(f"{API_BASE}/templates/{template_id}")
    
    if response.status_code == 200:
        template = response.json()
        print_pass(f"Template details retrieved: {template.get('name')}")
        print_info(f"Experiences: {len(template.get('predefined_experiences', []))}, Interventions: {len(template.get('predefined_interventions', []))}")
        return True
    else:
        print_fail(f"Failed to get template details: {response.status_code}")
        return False

def test_create_persona_from_template(template_id: str):
    """Test creating persona from template."""
    if not template_id:
        return None
        
    data = {
        "template_id": template_id,
        "custom_name": "Test Persona from Template"
    }
    
    response = requests.post(f"{API_BASE}/templates/create-persona", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print_pass(f"Persona created from template: {result.get('persona_name')}")
        return result.get('persona_id')
    else:
        print_fail(f"Failed to create persona from template: {response.status_code} - {response.text}")
        return None

# ============================================================================
# TEST 5: Remix/Snapshot API
# ============================================================================

def test_create_snapshot(persona_id: str):
    """Test creating a timeline snapshot."""
    print_test("Creating Timeline Snapshot")
    
    data = {
        "persona_id": persona_id,
        "label": "Baseline Snapshot",
        "description": "Initial state before interventions"
    }
    
    response = requests.post(f"{API_BASE}/remix/snapshots", json=data)
    
    if response.status_code == 200:
        snapshot = response.json()
        print_pass(f"Snapshot created: {snapshot.get('label')} (ID: {snapshot.get('id')})")
        return snapshot.get('id')
    elif response.status_code == 404:
        print_info("Remix feature is disabled (404) - this is expected if FEATURE_REMIX_TIMELINE=false")
        return None
    else:
        print_fail(f"Failed to create snapshot: {response.status_code} - {response.text}")
        return None

def test_list_snapshots(persona_id: str):
    """Test listing snapshots for a persona."""
    response = requests.get(f"{API_BASE}/remix/personas/{persona_id}/snapshots")
    
    if response.status_code == 200:
        snapshots = response.json()
        print_pass(f"Listed {len(snapshots)} snapshots")
        return snapshots
    elif response.status_code == 404:
        print_info("Remix feature disabled (404)")
        return []
    else:
        print_fail(f"Failed to list snapshots: {response.status_code}")
        return []

def test_compare_snapshots(snapshot_id_1: str, snapshot_id_2: str):
    """Test comparing two snapshots."""
    if not snapshot_id_1 or not snapshot_id_2:
        return False
        
    data = {
        "snapshot_id_1": snapshot_id_1,
        "snapshot_id_2": snapshot_id_2
    }
    
    response = requests.post(f"{API_BASE}/remix/snapshots/compare", json=data)
    
    if response.status_code == 200:
        comparison = response.json()
        print_pass("Snapshot comparison successful")
        print_info(f"Summary: {comparison.get('summary', '')[:100]}...")
        return True
    else:
        print_fail(f"Failed to compare snapshots: {response.status_code}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"{Colors.BOLD}FULL INTEGRATION TEST SUITE{Colors.END}")
    print(f"{'='*80}{Colors.END}\n")
    
    # Check server
    if not check_server():
        print("\n❌ Cannot proceed - backend server not running")
        print("\nTo start server:")
        print("  cd backend")
        print("  .\\venv\\Scripts\\uvicorn.exe app.main:app --reload --port 8000")
        return
    
    # Test 1: Create Persona
    persona = test_create_persona()
    if not persona:
        print("\n❌ Cannot proceed - persona creation failed")
        return
    
    persona_id = persona.get('id')
    
    # Test 2: Add Experience
    experience = test_add_experience(persona_id)
    
    # Test 3: Add Intervention
    intervention = test_add_intervention(persona_id)
    
    # Test 4: Templates API
    template_id = test_templates_api()
    if template_id:
        test_template_details(template_id)
        template_persona_id = test_create_persona_from_template(template_id)
    
    # Test 5: Remix/Snapshot
    snapshot_id_1 = test_create_snapshot(persona_id)
    snapshots = test_list_snapshots(persona_id)
    
    # If we have multiple snapshots, test comparison
    if len(snapshots) >= 2:
        snapshot_id_2 = snapshots[1].get('id')
        test_compare_snapshots(snapshots[0].get('id'), snapshot_id_2)
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"TEST SUMMARY{Colors.END}")
    print(f"{'='*80}")
    print(f"{Colors.GREEN}✓ Passed: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}✗ Failed: {test_results['failed']}{Colors.END}")
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    main()


