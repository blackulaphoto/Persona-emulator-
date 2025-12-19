# 🔧 COMPREHENSIVE FIX GUIDE - GET EVERYTHING WORKING

**Based on**: REMIX_SYSTEM_EVALUATION_REPORT.md  
**Status**: Cursor stuck, multiple issues blocking progress  
**Goal**: Get templates and experiences working properly

---

## 📊 CURRENT STATUS SUMMARY

### ✅ What's Working
- Backend server runs
- Templates API endpoints exist
- Feature flags enabled
- Frontend loads (with CORS issues)

### ❌ What's Broken
1. **CORS errors** - Frontend can't talk to backend
2. **Experience addition failing** - Can't add experiences to personas
3. **TimelineSnapshot schema mismatch** - Remix snapshots will fail
4. **Template experience application** - Failing due to SQLAlchemy errors

---

## 🎯 FIX PRIORITY ORDER

### FIX #1: CORS (BLOCKS EVERYTHING) - 5 MIN ⚡

**Problem**: Frontend gets "CORS header 'Access-Control-Allow-Origin' missing"

**Solution**: Update `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ADD THIS

app = FastAPI()

# ADD THIS BLOCK - MUST BE BEFORE ROUTE REGISTRATIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... rest of your code (route registrations, etc.)
```

**Verify**:
```bash
# Restart backend
# Then in browser console:
fetch('http://localhost:8000/api/v1/templates').then(r => r.json()).then(console.log)
# Should return data, not CORS error
```

---

### FIX #2: TimelineSnapshot Schema Mismatch - 10 MIN 🔧

**Problem**: Model field names don't match service usage

**Files Provided**:
1. `fixes/timeline_snapshot_FIXED.py` - Corrected model
2. `fixes/migration_fix_timeline_snapshot.py` - Database migration

**Steps**:

```bash
cd backend

# 1. Replace the broken model
cp fixes/timeline_snapshot_FIXED.py app/models/timeline_snapshot.py

# 2. Copy migration to alembic versions directory
cp fixes/migration_fix_timeline_snapshot.py alembic/versions/002_fix_timeline_snapshot_schema.py

# 3. Run migration
alembic upgrade head

# Expected output: Migration applied successfully
```

**Verify**:
```bash
# Check database schema
sqlite3 app.db ".schema timeline_snapshots"

# Should show:
# - personality_snapshot (not snapshot_personality)
# - trauma_markers_snapshot (not snapshot_symptoms)
# - symptom_severity_snapshot (not snapshot_symptom_severity)
# - personality_difference (NEW)
# - symptom_difference (NEW)
```

---

### FIX #3: Experience Addition Debugging - 15 MIN 🔍

**Problem**: "Can't add experience" - need to investigate

**Step 1: Check if endpoint exists**

```bash
# Test add experience endpoint directly
curl -X POST http://localhost:8000/api/v1/personas/{PERSONA_ID}/experiences \
  -H "Content-Type: application/json" \
  -d '{
    "user_description": "Test experience",
    "age_at_event": 10,
    "category": "social",
    "valence": "negative",
    "intensity": "moderate"
  }'

# If you get CORS error: Fix #1 not applied
# If you get 404: Route not registered
# If you get 500: Check backend logs
```

**Step 2: Check backend logs**

```bash
# Look at terminal where uvicorn is running
# Check for errors when you try to add experience

# Common errors:
# - "object is not bound to a Session" → SQLAlchemy ORM issue
# - "Missing required field" → Request validation error
# - "analyze_experience() missing argument" → Function signature mismatch
```

**Step 3: Verify analyze_experience signature**

File: `backend/app/services/psychology_engine.py`

```python
# Correct signature should be:
async def analyze_experience(
    persona: Persona,  # Full Persona object, NOT dict
    description: str,
    age_at_event: int,
    category: str,
    valence: str,
    intensity: str,
    db: Session
) -> Dict[str, Any]:
```

**Step 4: Verify experiences.py calls it correctly**

File: `backend/app/api/routes/experiences.py`

```python
# In add_experience endpoint:

# CORRECT (passes Persona object):
analysis = await analyze_experience(
    persona=persona,  # Full object from db.query(Persona).filter()...
    description=experience_data.user_description,
    age_at_event=experience_data.age_at_event,
    category=experience_data.category,
    valence=experience_data.valence,
    intensity=experience_data.intensity,
    db=db
)

# WRONG (passes dict):
analysis = await analyze_experience(
    persona=persona.dict(),  # ❌ Don't do this
    ...
)
```

---

### FIX #4: Template Experience Application - 20 MIN 🎯

**Problem**: Applying template experiences fails with SQLAlchemy error

**File**: `backend/app/api/routes/templates.py` 

**Check the endpoint** (around line 180-250):

```python
@router.post("/personas/{persona_id}/apply-experiences")
async def apply_experience_set(...):
    # ... code ...
    
    # CRITICAL: Check this section
    for exp_data in experiences_to_apply:
        # Get experience dict
        exp_dict = exp_data.dict() if hasattr(exp_data, 'dict') else exp_data
        
        # Call analyze_experience - MUST pass Persona object, not dict
        analysis = await analyze_experience(
            persona=persona,  # ✅ CORRECT - full object
            # NOT: persona=persona.dict(),  # ❌ WRONG
            description=exp_dict["description"],
            age_at_event=exp_dict["age"],
            category=exp_dict["category"],
            valence=exp_dict["valence"],
            intensity=exp_dict["intensity"],
            db=db
        )
        
        # Create Experience record
        experience = Experience(
            id=str(uuid.uuid4()),
            persona_id=persona.id,  # ✅ Use persona.id, not str(persona.id)
            sequence_number=next_sequence,
            age_at_event=exp_dict["age"],
            user_description=exp_dict["description"],
            # ... rest of fields
        )
        
        db.add(experience)
        
        # UPDATE PERSONA - CRITICAL
        # Refresh persona from DB before each update
        db.refresh(persona)
        
        # Update personality
        for trait, value in analysis["personality_changes"].items():
            persona.current_personality[trait] = value
        
        # Update trauma markers
        if analysis.get("new_trauma_markers"):
            current_markers = set(persona.current_trauma_markers or [])
            current_markers.update(analysis["new_trauma_markers"])
            persona.current_personality = list(current_markers)  # Fixed typo - should be current_trauma_markers
        
        # Mark as modified
        db.add(persona)
        
        next_sequence += 1
    
    # Commit all changes
    db.commit()
```

**Common Mistakes**:
1. Passing `persona.dict()` instead of `persona` object
2. Not refreshing persona from DB between updates
3. Typo: `persona.current_personality` instead of `persona.current_trauma_markers`
4. Not committing changes

---

### FIX #5: Frontend Template Loading - 10 MIN 💻

**Problem**: Templates might not load properly in frontend

**File**: `frontend/app/page.tsx` or `frontend/app/persona/[id]/page.tsx`

**Check loadTemplates function**:

```typescript
async function loadTemplates() {
  try {
    setTemplatesLoading(true);
    
    // CORRECT API call
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/templates`);
    
    if (!response.ok) {
      if (response.status === 404) {
        console.log('Templates feature not enabled');
        setTemplatesAvailable(false);
        return;
      }
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    setTemplates(data);
    setTemplatesAvailable(true);
    
  } catch (error) {
    console.error('Templates not available (feature may be disabled):', error);
    setTemplatesAvailable(false);
  } finally {
    setTemplatesLoading(false);
  }
}
```

**Verify .env.local**:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔍 DIAGNOSTIC COMMANDS

### Check Feature Flags

```bash
# Backend .env
cat backend/.env | grep FEATURE

# Should show:
# FEATURE_CLINICAL_TEMPLATES=true
# FEATURE_REMIX_TIMELINE=true
```

### Check Backend Endpoints

```bash
# List all routes
curl http://localhost:8000/docs

# Test templates endpoint
curl http://localhost:8000/api/v1/templates

# Test debug endpoint
curl http://localhost:8000/api/v1/templates/debug/feature-flags
```

### Check Database State

```bash
# SQLite
sqlite3 backend/app.db

# Check tables exist
.tables

# Should show:
# clinical_templates
# timeline_snapshots
# personas
# experiences
# interventions

# Check template count
SELECT COUNT(*) FROM clinical_templates;

# Should return 3 (BPD, C-PTSD, Social Anxiety)
```

### Check Backend Logs

```bash
# In terminal where uvicorn is running, look for:

# Good signs:
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000

# Bad signs:
ERROR:    Exception in ASGI application
sqlalchemy.exc.InvalidRequestError: Object '<Persona at 0x...>' is not bound to a Session

# If you see SQLAlchemy errors, the ORM boundary violation issue has returned
```

---

## 🚨 CRITICAL CHECKS BEFORE TESTING

### Backend Checklist

- [ ] CORS middleware added to main.py
- [ ] CORS middleware added BEFORE route registrations
- [ ] TimelineSnapshot model replaced with fixed version
- [ ] Migration run successfully
- [ ] Feature flags set to `true` in .env
- [ ] Backend server restarted
- [ ] No errors in backend terminal

### Frontend Checklist

- [ ] NEXT_PUBLIC_API_URL set in .env.local
- [ ] Frontend server restarted
- [ ] Browser cache cleared (hard refresh: Cmd/Ctrl + Shift + R)
- [ ] No CORS errors in browser console
- [ ] Templates array populates (check React DevTools)

---

## 🎯 TESTING WORKFLOW

### Test 1: Basic API Access

```bash
# Should return template list
curl http://localhost:8000/api/v1/templates
```

### Test 2: Add Experience (Original Functionality)

1. Go to persona detail page
2. Click "Add Experience"
3. Fill out form
4. Submit
5. Check for errors in console
6. Verify experience appears in timeline

### Test 3: Create Persona from Template

1. Go to home page
2. Click "Browse Clinical Templates"
3. Click template card
4. Click "Create Persona from Template"
5. Verify persona created
6. Check persona appears in list

### Test 4: Apply Template Experiences

1. Go to persona detail page
2. Click "Remix with Template"
3. Select template
4. Click "Apply All Experiences"
5. Check console for errors
6. Verify experiences added to timeline

### Test 5: Create Snapshot

1. On persona with experiences
2. Use Remix API to create snapshot:

```javascript
fetch('http://localhost:8000/api/v1/remix/snapshots', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    persona_id: 'YOUR_PERSONA_ID',
    label: 'Test Snapshot'
  })
}).then(r => r.json()).then(console.log)
```

---

## 🔄 IF STILL BROKEN

### Nuclear Option: Clean Restart

```bash
# 1. Stop all servers (Ctrl+C in both terminals)

# 2. Backend cleanup
cd backend
rm app.db  # Delete database
alembic upgrade head  # Recreate fresh

# 3. Restart backend
uvicorn app.main:app --reload --port 8000

# 4. In new terminal, restart frontend
cd frontend
npm run dev

# 5. Hard refresh browser (Cmd/Ctrl + Shift + R)

# 6. Test basic persona creation (without templates)
# 7. Then test templates
```

### Get Detailed Error Info

Add this to your frontend API client (`frontend/lib/api/templates.ts`):

```typescript
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    console.error('API Error:', {
      status: response.status,
      statusText: response.statusText,
      error: error,
      url: response.url
    });
    throw new APIError(
      error.detail || `HTTP ${response.status}`,
      response.status,
      error
    );
  }
  return response.json();
}
```

---

## 📝 QUICK REFERENCE

### Feature Flags

```bash
# Enable templates
FEATURE_CLINICAL_TEMPLATES=true

# Enable remix
FEATURE_REMIX_TIMELINE=true

# Restart backend after changing
```

### File Locations

```
backend/app/main.py                     → Add CORS here
backend/app/models/timeline_snapshot.py → Replace with fixed version
backend/app/api/routes/templates.py     → Check analyze_experience calls
backend/app/api/routes/experiences.py   → Check add_experience endpoint
backend/.env                            → Set feature flags
frontend/.env.local                     → Set NEXT_PUBLIC_API_URL
```

---

## 🎉 SUCCESS CRITERIA

You'll know it's working when:

1. ✅ No CORS errors in browser console
2. ✅ Templates load on home page
3. ✅ Can create persona normally (without template)
4. ✅ Can add experience to persona normally
5. ✅ Can create persona from template
6. ✅ Can apply template experiences
7. ✅ No SQLAlchemy errors in backend logs
8. ✅ Can create snapshots (after testing)

---

**Start with Fix #1 (CORS) - everything else depends on it!** 🚀
