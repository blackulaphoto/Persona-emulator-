# Start Backend Server Script
# Fixes the venv path issue by using Python directly

$backendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $backendPath "venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python executable not found at: $pythonExe" -ForegroundColor Red
    Write-Host "   You may need to recreate the virtual environment:" -ForegroundColor Yellow
    Write-Host "   cd backend"
    Write-Host "   python -m venv venv"
    Write-Host "   .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

Write-Host "Starting backend server..." -ForegroundColor Cyan
Write-Host "Python: $pythonExe" -ForegroundColor Gray
Write-Host ""

Push-Location $backendPath
Write-Host "Server will start in this window. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""
& $pythonExe -m uvicorn app.main:app --reload --port 8000
Pop-Location

