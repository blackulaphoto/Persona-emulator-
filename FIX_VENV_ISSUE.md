# Fix Virtual Environment Path Issue

## Problem

The virtual environment was created when the project was on the `D:\` drive, but the project is now on the `E:\` drive. This causes errors like:

```
Fatal error in launcher: Unable to create process using '"D:\google photos\...\python.exe"'
```

## Solution Options

### Option 1: Use Direct Python (Quick Fix - Recommended)

Use the `start_server.ps1` script:

```powershell
cd backend
.\start_server.ps1
```

Or manually:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Option 2: Recreate Virtual Environment (Best Long-term Fix)

If Option 1 doesn't work, recreate the virtual environment:

```powershell
cd backend

# Remove old venv
Remove-Item -Recurse -Force venv

# Create new venv
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Now uvicorn should work
.\venv\Scripts\uvicorn.exe app.main:app --reload
```

### Option 3: Use Python Module Directly

Always use Python's `-m` flag to avoid launcher issues:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
.\venv\Scripts\python.exe -m pytest tests/ -v
.\venv\Scripts\python.exe test_full_integration.py
```

## Updated Start Commands

All commands should use `python.exe -m` instead of direct executables:

### Start Backend:
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Run Tests:
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
.\venv\Scripts\python.exe test_full_integration.py
```

### Run Integration Test Script:
```powershell
cd backend
.\start_server.ps1  # Uses the fixed method
```

## Why This Happens

Virtual environments on Windows store absolute paths in their launcher scripts. When you move a project to a different drive or path, those launchers break. Using `python.exe -m <module>` bypasses the launcher and works regardless of the original venv location.


