# Run Tests Now - Step by Step Guide

## Quick Start

### Step 1: Start Backend Server

Open a **new PowerShell terminal** and run:

```powershell
cd "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\backend"
.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

Wait until you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Test Backend API (In Another Terminal)

Open a **second PowerShell terminal** and run these commands one by one:

#### Test 1: Create Persona
```powershell
$body = @{
    name = "Test Persona"
    baseline_age = 10
    baseline_gender = "female"
    baseline_background = "Test background"
} | ConvertTo-Json

$r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas" -Method POST -Body $body -ContentType "application/json"
Write-Host "✅ Persona created: $($r.name) (ID: $($r.id))" -ForegroundColor Green
$personaId = $r.id
```

#### Test 2: Add Experience
```powershell
$exp = @{
    description = "Parents divorced when persona was 12. Family conflict."
    age_at_event = 12
} | ConvertTo-Json

$r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas/$personaId/experiences" -Method POST -Body $exp -ContentType "application/json"
Write-Host "✅ Experience added at age $($r.age_at_event)" -ForegroundColor Green
Write-Host "   Symptoms: $($r.symptoms_developed -join ', ')" -ForegroundColor Gray
```

#### Test 3: Add Intervention
```powershell
$intv = @{
    therapy_type = "CBT"
    duration = "6_months"
    intensity = "weekly"
    age_at_intervention = 16
} | ConvertTo-Json

$r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/personas/$personaId/interventions" -Method POST -Body $intv -ContentType "application/json"
Write-Host "✅ Intervention added: $($r.therapy_type) at age $($r.age_at_intervention)" -ForegroundColor Green
Write-Host "   Efficacy: $($r.efficacy_match)" -ForegroundColor Gray
```

#### Test 4: Templates API
```powershell
try {
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/templates" -Method GET
    Write-Host "✅ Templates API: Found $($r.Count) templates" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "⚠️  Templates feature disabled (expected if FEATURE_CLINICAL_TEMPLATES=false)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

#### Test 5: Remix/Snapshot API
```powershell
$snap = @{
    persona_id = $personaId
    label = "Test Snapshot"
    description = "Baseline state"
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/remix/snapshots" -Method POST -Body $snap -ContentType "application/json"
    Write-Host "✅ Snapshot created: $($r.label)" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) {
        Write-Host "⚠️  Remix feature disabled (expected if FEATURE_REMIX_TIMELINE=false)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

### Step 3: Run Automated Test Script

Alternatively, use the automated PowerShell test script:

```powershell
cd "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\backend"
.\test_integration.ps1
```

Or use the Python test script:

```powershell
cd "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\backend"
.\venv\Scripts\python.exe test_full_integration.py
```

### Step 4: Run Unit Tests

```powershell
cd "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\backend"
.\venv\Scripts\pytest.exe tests/ -v
```

### Step 5: Test Frontend

Open a **third PowerShell terminal** and run:

```powershell
cd "E:\google photos\personality2\persona-evolution-simulator-complete\persona-evolution-simulator\frontend"
npm run dev
```

Then open your browser to:
- http://localhost:3000 - Main page
- http://localhost:3000/templates - Templates page
- http://localhost:3000/create - Create persona page
- http://localhost:3000/persona/{id} - Persona detail page (use ID from Test 1)

## Expected Results

### ✅ Success Indicators:
- Persona creation returns 201 with ID
- Experience addition returns 201 with symptoms
- Intervention addition returns 201 with efficacy match
- Templates API returns 200 (if enabled) or 404 (if disabled)
- Remix API returns 200 (if enabled) or 404 (if disabled)
- Frontend pages load without errors

### ❌ Common Issues:

1. **"Unable to connect"** → Backend server not running
   - Solution: Check Step 1, ensure server started successfully

2. **"404 Not Found"** → Feature flag disabled
   - Solution: This is expected if `FEATURE_CLINICAL_TEMPLATES=false` or `FEATURE_REMIX_TIMELINE=false`

3. **"500 Internal Server Error"** → Check backend terminal for error messages
   - Common causes: Missing .env file, database issues, OpenAI API key issues

4. **"CORS error"** → Frontend can't connect to backend
   - Solution: Verify CORS settings in `backend/app/main.py` include `http://localhost:3000`

## Full Test Checklist

- [ ] Backend server running on port 8000
- [ ] Persona creation test passes
- [ ] Experience addition test passes
- [ ] Intervention addition test passes
- [ ] Templates API responds (200 or 404)
- [ ] Remix/Snapshot API responds (200 or 404)
- [ ] Frontend server running on port 3000
- [ ] Frontend pages load
- [ ] Can create persona from UI
- [ ] Can add experiences from UI
- [ ] Can add interventions from UI
- [ ] Templates page loads (if enabled)
- [ ] Can create persona from template (if enabled)
- [ ] Can create snapshots (if enabled)

## Need Help?

See `TESTING_GUIDE.md` for detailed documentation.


