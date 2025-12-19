# Full Integration Testing Guide

This guide provides step-by-step instructions for testing all functionality of the Persona Evolution Simulator, including the new Templates and Remix features.

## Prerequisites

1. **Backend server running:**
   ```powershell
   cd backend
   .\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```

2. **Frontend server running:**
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Feature flags enabled (for Templates and Remix testing):**
   In `backend/.env`, ensure:
   ```
   FEATURE_CLINICAL_TEMPLATES=true
   FEATURE_REMIX_TIMELINE=true
   ```

---

## Test Suite 1: Backend Unit Tests

### Run All Tests
```powershell
cd backend
.\venv\Scripts\pytest.exe tests/ -v
```

### Individual Test Files
- `tests/test_api_personas.py` - Persona CRUD operations
- `tests/test_api_experiences.py` - Experience/event addition
- `tests/test_api_interventions.py` - Intervention addition
- `tests/test_api_timeline.py` - Timeline retrieval
- `tests/test_psychology_engine.py` - AI analysis logic
- `tests/test_intervention_engine.py` - Therapy matching logic

---

## Test Suite 2: API Endpoint Tests

### Test 1: Persona Creation

**Endpoint:** `POST /api/v1/personas`

**Request:**
```json
{
  "name": "Test Persona",
  "baseline_age": 10,
  "baseline_gender": "female",
  "baseline_background": "Happy childhood, loving parents"
}
```

**Expected Response:**
- Status: `201 Created`
- Contains: `id`, `name`, `current_personality` (all traits at 0.5), `current_age: 10`

**Test Command:**
```powershell
$body = @{
    name = "Test Persona"
    baseline_age = 10
    baseline_gender = "female"
    baseline_background = "Test background"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas" -Method POST -Body $body -ContentType "application/json"
```

**Verify:**
- ✅ Persona ID is generated
- ✅ All personality traits initialized to 0.5
- ✅ Current age matches baseline age
- ✅ Attachment style defaults to "secure"

---

### Test 2: Add Experience/Event

**Endpoint:** `POST /api/v1/personas/{persona_id}/experiences`

**Request:**
```json
{
  "description": "Parents divorced when persona was 12 years old. Family conflict and emotional instability.",
  "age_at_event": 12
}
```

**Expected Response:**
- Status: `201 Created`
- Contains: `symptoms_developed`, `immediate_effects`, `personality_changes`

**Test Command:**
```powershell
$personaId = "<from previous test>"
$body = @{
    description = "Parents divorced at age 12. Family conflict."
    age_at_event = 12
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas/$personaId/experiences" -Method POST -Body $body -ContentType "application/json"
```

**Verify:**
- ✅ Experience created with sequence number
- ✅ Symptoms developed (e.g., anxiety, trust_issues)
- ✅ Personality traits changed (neuroticism increased)
- ✅ Persona's current_age updated if needed
- ✅ Trauma markers added to persona

---

### Test 3: Add Intervention

**Endpoint:** `POST /api/v1/personas/{persona_id}/interventions`

**Request:**
```json
{
  "therapy_type": "CBT",
  "duration": "6_months",
  "intensity": "weekly",
  "age_at_intervention": 16
}
```

**Expected Response:**
- Status: `201 Created`
- Contains: `efficacy_match`, `immediate_effects`, `symptom_changes`

**Test Command:**
```powershell
$body = @{
    therapy_type = "CBT"
    duration = "6_months"
    intensity = "weekly"
    age_at_intervention = 16
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas/$personaId/interventions" -Method POST -Body $body -ContentType "application/json"
```

**Verify:**
- ✅ Intervention created with sequence number
- ✅ Efficacy match calculated (0.0-1.0)
- ✅ Symptom changes recorded (before/after)
- ✅ Personality changes applied
- ✅ Persona's current_age updated

---

### Test 4: Templates API (Feature Flag Required)

**4a. List Templates**
- **Endpoint:** `GET /api/v1/templates`
- **Expected:** Array of template summaries
- **Test:** `Invoke-RestMethod -Uri "http://localhost:8000/api/v1/templates"`

**4b. Get Template Details**
- **Endpoint:** `GET /api/v1/templates/{template_id}`
- **Expected:** Full template with experiences, interventions, outcomes
- **Test:** `Invoke-RestMethod -Uri "http://localhost:8000/api/v1/templates/bpd-classic-pathway"`

**4c. Get Disorder Types**
- **Endpoint:** `GET /api/v1/templates/meta/disorder-types`
- **Expected:** `["BPD", "C-PTSD", "Social_Anxiety"]`

**4d. Create Persona from Template**
- **Endpoint:** `POST /api/v1/templates/create-persona`
- **Request:**
  ```json
  {
    "template_id": "bpd-classic-pathway",
    "custom_name": "Test Case Study"
  }
  ```
- **Expected:** Persona created with template's baseline configuration

**4e. Apply Template Experiences**
- **Endpoint:** `POST /api/v1/templates/personas/{persona_id}/apply-experiences`
- **Request:**
  ```json
  {
    "template_id": "bpd-classic-pathway",
    "experience_indices": [0, 1, 2]  // or null for all
  }
  ```

**Verify:**
- ✅ Templates load from JSON files or database
- ✅ Template details include all predefined experiences
- ✅ Persona created with correct baseline personality
- ✅ Experiences can be applied sequentially

---

### Test 5: Remix/Snapshot API (Feature Flag Required)

**5a. Create Snapshot**
- **Endpoint:** `POST /api/v1/remix/snapshots`
- **Request:**
  ```json
  {
    "persona_id": "<persona_id>",
    "label": "Baseline State",
    "description": "Before any interventions"
  }
  ```
- **Expected:** Snapshot saved with current persona state

**5b. List Snapshots**
- **Endpoint:** `GET /api/v1/remix/personas/{persona_id}/snapshots`
- **Expected:** Array of all snapshots for persona

**5c. Compare Snapshots**
- **Endpoint:** `POST /api/v1/remix/snapshots/compare`
- **Request:**
  ```json
  {
    "snapshot_id_1": "<id>",
    "snapshot_id_2": "<id>"
  }
  ```
- **Expected:** Comparison showing personality differences, symptom changes

**5d. Get Remix Suggestions**
- **Endpoint:** `GET /api/v1/remix/personas/{persona_id}/suggestions?template_id=<optional>`
- **Expected:** Array of "what if" scenario suggestions

**Verify:**
- ✅ Snapshots capture current personality and symptoms
- ✅ Comparisons show meaningful differences
- ✅ Suggestions are relevant to persona state

---

## Test Suite 3: Frontend Integration Tests

### Test 1: Templates Page

1. Navigate to `http://localhost:3000/templates`
2. **Verify:**
   - ✅ Page loads without errors
   - ✅ Template browser displays templates
   - ✅ Filter by disorder type works
   - ✅ Template cards show correct information
   - ✅ Clicking "View Details" opens modal

3. **Test Template Details Modal:**
   - ✅ Overview tab shows clinical rationale
   - ✅ Experiences tab lists all predefined experiences
   - ✅ Interventions tab shows suggested therapies
   - ✅ Outcomes tab displays expected scenarios
   - ✅ Research tab shows citations

4. **Test Create Persona from Template:**
   - ✅ Click "Create Persona from Template"
   - ✅ Success modal appears
   - ✅ Can navigate to created persona
   - ✅ Persona has correct baseline configuration

---

### Test 2: Persona Page Integration

1. Navigate to `http://localhost:3000/persona/{id}` (from template or manually created)

2. **Verify:**
   - ✅ Timeline displays correctly
   - ✅ Personality overview shows current traits
   - ✅ Can add experiences
   - ✅ Can add interventions
   - ✅ Chat feature works (if implemented)

3. **Test Experience Addition:**
   - ✅ Modal opens
   - ✅ Can enter description and age
   - ✅ Experience appears on timeline after save
   - ✅ Personality traits update
   - ✅ Symptoms appear in timeline

4. **Test Intervention Addition:**
   - ✅ Modal opens with therapy options
   - ✅ Can select duration and intensity
   - ✅ Success message appears
   - ✅ Intervention appears on timeline
   - ✅ Symptom severity updates

---

### Test 3: Remix/Snapshot UI (if implemented)

1. **Test Snapshot Creation:**
   - ✅ Button to create snapshot exists
   - ✅ Can label and describe snapshot
   - ✅ Snapshot appears in list

2. **Test Snapshot Comparison:**
   - ✅ Can select two snapshots
   - ✅ Comparison view shows differences
   - ✅ Personality changes displayed clearly
   - ✅ Symptom changes highlighted

---

## Test Suite 4: Full Workflow Test

### Complete User Journey

1. **Create Persona from Template:**
   - Go to `/templates`
   - Select "BPD Classic Pathway"
   - Click "Create Persona"
   - Verify persona created

2. **Apply Template Experiences:**
   - On persona page, apply all experiences
   - Verify personality changes
   - Verify symptoms develop

3. **Create Baseline Snapshot:**
   - Create snapshot labeled "Original"

4. **Add Intervention:**
   - Add DBT intervention at age 16
   - Verify symptom improvements
   - Verify personality changes

5. **Create Comparison Snapshot:**
   - Create snapshot labeled "With DBT"

6. **Compare Snapshots:**
   - Compare "Original" vs "With DBT"
   - Verify improvements shown
   - Verify summary explains changes

---

## Automated Test Script

Run the automated test script:

```powershell
cd backend
.\test_integration.ps1
```

Or use Python:

```powershell
cd backend
.\venv\Scripts\python.exe test_full_integration.py
```

---

## Expected Test Results

### With Feature Flags ON:
- ✅ Templates API: 200 OK
- ✅ Remix API: 200 OK
- ✅ Can create personas from templates
- ✅ Can create and compare snapshots

### With Feature Flags OFF:
- ⚠️ Templates API: 404 Not Found
- ⚠️ Remix API: 404 Not Found
- ✅ Core persona/experience/intervention APIs: 200 OK

---

## Common Issues & Solutions

### Issue: "Feature not enabled" (404)
**Solution:** Set feature flags to `true` in `backend/.env`

### Issue: "Template not found"
**Solution:** Ensure JSON files are in `backend/data/templates/` or fallback path

### Issue: "Database error"
**Solution:** Ensure database tables created: `Base.metadata.create_all()` runs on server start

### Issue: "CORS error" (frontend)
**Solution:** Verify CORS settings in `backend/app/main.py` include `http://localhost:3000`

---

## Test Checklist

- [ ] Backend server starts without errors
- [ ] Frontend server starts without errors
- [ ] Persona creation works
- [ ] Experience addition works
- [ ] Intervention addition works
- [ ] Templates API responds (if enabled)
- [ ] Remix API responds (if enabled)
- [ ] Frontend templates page loads
- [ ] Template details modal works
- [ ] Can create persona from template
- [ ] Can create snapshots
- [ ] Can compare snapshots
- [ ] Full workflow completes successfully


