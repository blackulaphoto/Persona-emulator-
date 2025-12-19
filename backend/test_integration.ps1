# Full Integration Test Script (PowerShell)
# Tests all API endpoints and functionality

$ErrorActionPreference = "Continue"
$API_BASE = "http://localhost:8000/api/v1"

function Write-TestHeader {
    param([string]$Name)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST: $Name" -ForegroundColor Cyan -BackgroundColor Black
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Pass {
    param([string]$Message)
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

# Test results
$script:passed = 0
$script:failed = 0
$script:personaId = $null
$script:templateId = $null
$script:snapshotId = $null

# Check server
Write-TestHeader "Server Check"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        Write-Pass "Backend server is running"
    }
} catch {
    Write-Fail "Backend server not running. Please start it first:"
    Write-Host "  cd backend"
    Write-Host "  .\start_server.ps1"
    Write-Host "  (or: .\venv\Scripts\python.exe -m uvicorn app.main:app --reload)"
    exit 1
}

# Test 1: Create Persona
Write-TestHeader "1. Creating Persona"
try {
    $body = @{
        name = "Test Persona Integration"
        baseline_age = 10
        baseline_gender = "female"
        baseline_background = "Test background for integration testing"
    } | ConvertTo-Json

    $response = Invoke-WebRequest -Uri "$API_BASE/personas" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    if ($response.StatusCode -eq 201) {
        $persona = $response.Content | ConvertFrom-Json
        $script:personaId = $persona.id
        Write-Pass "Persona created: $($persona.name) (ID: $script:personaId)"
        Write-Info "Age: $($persona.current_age), Personality traits initialized"
        $script:passed++
    } else {
        Write-Fail "Status code: $($response.StatusCode)"
        $script:failed++
    }
} catch {
    Write-Fail "Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Info "Response: $responseBody"
    }
    $script:failed++
}

# Test 2: Add Experience
if ($script:personaId) {
    Write-TestHeader "2. Adding Experience/Event"
    try {
        $body = @{
            description = "Parents divorced when persona was 12. Family conflict and emotional instability. Child felt responsible and anxious about the future."
            age_at_event = 12
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$API_BASE/personas/$script:personaId/experiences" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
        if ($response.StatusCode -eq 201) {
            $experience = $response.Content | ConvertFrom-Json
            Write-Pass "Experience added at age $($experience.age_at_event)"
            Write-Info "Symptoms: $($experience.symptoms_developed -join ', ')"
            $script:passed++
        } else {
            Write-Fail "Status code: $($response.StatusCode)"
            $script:failed++
        }
    } catch {
        Write-Fail "Error: $($_.Exception.Message)"
        $script:failed++
    }
}

# Test 3: Add Intervention
if ($script:personaId) {
    Write-TestHeader "3. Adding Intervention"
    try {
        $body = @{
            therapy_type = "CBT"
            duration = "6_months"
            intensity = "weekly"
            age_at_intervention = 16
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$API_BASE/personas/$script:personaId/interventions" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
        if ($response.StatusCode -eq 201) {
            $intervention = $response.Content | ConvertFrom-Json
            Write-Pass "Intervention added: $($intervention.therapy_type) at age $($intervention.age_at_intervention)"
            Write-Info "Efficacy match: $($intervention.efficacy_match)"
            $script:passed++
        } else {
            Write-Fail "Status code: $($response.StatusCode)"
            if ($response.StatusCode -eq 500) {
                Write-Info "Response: $($response.Content)"
            }
            $script:failed++
        }
    } catch {
        Write-Fail "Error: $($_.Exception.Message)"
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Info "Response: $responseBody"
        }
        $script:failed++
    }
}

# Test 4: Templates API
Write-TestHeader "4. Templates API"
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/templates" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        $templates = $response.Content | ConvertFrom-Json
        Write-Pass "Templates API working: Found $($templates.Count) templates"
        if ($templates.Count -gt 0) {
            $script:templateId = $templates[0].id
            Write-Info "First template: $($templates[0].name) ($($templates[0].disorder_type))"
            $script:passed++
        } else {
            Write-Info "No templates found (this is OK if database is empty)"
        }
    } elseif ($response.StatusCode -eq 404) {
        Write-Info "Templates feature disabled (404) - Set FEATURE_CLINICAL_TEMPLATES=true to enable"
    } else {
        Write-Fail "Status code: $($response.StatusCode)"
        $script:failed++
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Info "Templates feature disabled (404) - Expected if FEATURE_CLINICAL_TEMPLATES=false"
    } else {
        Write-Fail "Error: $($_.Exception.Message)"
        $script:failed++
    }
}

# Test 5: Remix/Snapshot API
if ($script:personaId) {
    Write-TestHeader "5. Remix/Snapshot API"
    try {
        $body = @{
            persona_id = $script:personaId
            label = "Baseline Snapshot"
            description = "Initial state for testing"
        } | ConvertTo-Json

        $response = Invoke-WebRequest -Uri "$API_BASE/remix/snapshots" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $snapshot = $response.Content | ConvertFrom-Json
            $script:snapshotId = $snapshot.id
            Write-Pass "Snapshot created: $($snapshot.label) (ID: $script:snapshotId)"
            $script:passed++
        } elseif ($response.StatusCode -eq 404) {
            Write-Info "Remix feature disabled (404) - Set FEATURE_REMIX_TIMELINE=true to enable"
        } else {
            Write-Fail "Status code: $($response.StatusCode)"
            $script:failed++
        }
    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Info "Remix feature disabled (404) - Expected if FEATURE_REMIX_TIMELINE=false"
        } else {
            Write-Fail "Error: $($_.Exception.Message)"
            $script:failed++
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[PASS] Passed: $script:passed" -ForegroundColor Green
Write-Host "[FAIL] Failed: $script:failed" -ForegroundColor Red
Write-Host ""

