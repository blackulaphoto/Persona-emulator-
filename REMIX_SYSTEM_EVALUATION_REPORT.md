# REMIX SYSTEM & TEMPLATES API - COMPREHENSIVE EVALUATION REPORT

**Date:** Current Session  
**Scope:** Full evaluation of Clinical Templates and Timeline Remix features  
**Status:** Development/Integration Phase

---

## EXECUTIVE SUMMARY

Two major features were integrated into the Persona Evolution Simulator:

1. **Clinical Templates System** - Pre-built disorder development pathways
2. **Timeline Remix System** - "What if" scenario comparison via snapshots

Both features are protected by feature flags and have separate API routes. The integration encountered several SQLAlchemy ORM boundary violations and schema mismatches that required fixes.

---

## PART 1: FEATURES ADDED - DETAILED BREAKDOWN

### FEATURE 1: CLINICAL TEMPLATES SYSTEM

#### Purpose
Allows users to create personas from evidence-based disorder development pathways (BPD, C-PTSD, Social Anxiety, etc.) rather than starting from scratch.

#### Components Added

##### Backend Models
**File:** `backend/app/models/clinical_template.py`
- `ClinicalTemplate` SQLAlchemy model
- Stores: template metadata, baseline personality, predefined experiences, suggested interventions, expected outcomes, citations, remix suggestions
- JSON columns for complex nested data (experiences, interventions, outcomes)

##### Backend Services
**File:** `backend/app/services/template_service.py`

**Functions:**
1. `load_template_from_json(json_path)` - Loads template data from JSON files
2. `create_template_from_dict(db, template_data)` - Creates database records from template dict
3. `populate_templates_database(db)` - Auto-populates DB from JSON files on first use
4. `create_persona_from_template(db, template_id, owner_id, custom_name)` - Creates new Persona from template baseline
5. `get_template_experiences(template_id, db)` - Retrieves predefined experiences (from DB or JSON fallback)
6. `get_template_interventions(template_id, db)` - Retrieves predefined interventions (from DB or JSON fallback)
7. `get_all_disorder_types(db)` - Returns unique disorder types for filtering
8. `get_templates_by_disorder(db, disorder_type)` - Filters templates by disorder

**Template JSON Location:**
- Primary: `backend/data/templates/*.json`
- Fallback: `remix component/step 1/*.json`
- Currently contains: `bpd_classic_pathway.json`, `cptsd_chronic_trauma.json`, `social_anxiety_developmental.json`

##### Backend API Routes
**File:** `backend/app/api/routes/templates.py`
**Prefix:** `/api/v1/templates`

**Endpoints:**

1. **GET `/api/v1/templates`** - List all templates
   - Query param: `disorder_type` (optional filter)
   - Returns: `List[ClinicalTemplateListResponse]` (simplified template info)
   - Auto-populates database if empty
   - Protected by `require_templates_feature()` dependency

2. **GET `/api/v1/templates/{template_id}`** - Get template details
   - Returns: `ClinicalTemplateResponse` (full template with experiences/interventions)
   - Protected by `require_templates_feature()` dependency

3. **GET `/api/v1/templates/meta/disorder-types`** - Get disorder type list
   - Returns: `List[str]` (e.g., ["BPD", "C-PTSD", "Social_Anxiety"])
   - Protected by `require_templates_feature()` dependency

4. **POST `/api/v1/templates/create-persona`** - Create persona from template
   - Request: `CreatePersonaFromTemplateRequest` (template_id, custom_name, owner_id)
   - Returns: `CreatePersonaFromTemplateResponse` (persona_id, template info, available experiences count)
   - Protected by `require_templates_feature()` dependency

5. **POST `/api/v1/templates/personas/{persona_id}/apply-experiences`** - Apply template experiences to persona
   - Request: `ApplyExperienceSetRequest` (template_id, experience_indices)
   - Returns: `ApplyExperienceSetResponse` (experiences_applied, personality_before/after, symptoms)
   - **CRITICAL ENDPOINT** - This is where the SQLAlchemy error occurred
   - Protected by `require_templates_feature()` dependency

6. **GET `/api/v1/templates/debug/feature-flags`** - Debug endpoint (no protection)
   - Returns feature flag status from env, settings, and FeatureFlags class
   - Added for troubleshooting feature flag issues

##### Backend Schemas
**File:** `backend/app/schemas/template_schemas.py`

**Schemas Defined:**
- `TemplateExperienceSchema` - Experience structure (age, category, valence, intensity, description, clinical_note)
- `TemplateInterventionSchema` - Intervention structure (age, therapy_type, duration, intensity, rationale)
- `ClinicalTemplateResponse` - Full template response
- `ClinicalTemplateListResponse` - Simplified template list item
- `CreatePersonaFromTemplateRequest` - Persona creation request
- `CreatePersonaFromTemplateResponse` - Persona creation response
- `ApplyExperienceSetRequest` - Experience application request
- `ApplyExperienceSetResponse` - Experience application response
- `TimelineSnapshotResponse` - Snapshot response (used by remix)
- `CompareSnapshotsResponse` - Snapshot comparison response

##### Frontend Components
**File:** `frontend/components/templates/TemplateBrowser.tsx`
- Displays list of available templates
- Filter by disorder type
- Styled with custom design system (cream/clay/moss/sage colors)

**File:** `frontend/components/templates/TemplateDetailsModal.tsx`
- Shows full template details in modal
- Displays: clinical rationale, predefined experiences, suggested interventions, expected outcomes, citations

**File:** `frontend/components/templates/SnapshotComparison.tsx`
- Displays side-by-side snapshot comparison
- Shows personality differences, symptom differences, severity changes

##### Frontend API Client
**File:** `frontend/lib/api/templates.ts`

**Exports:**
- `templatesAPI.list(disorderType?)` - List templates
- `templatesAPI.get(templateId)` - Get template details
- `templatesAPI.getDisorderTypes()` - Get disorder types
- `templatesAPI.createPersona(templateId, customName?)` - Create persona
- `templatesAPI.applyExperiences(personaId, templateId, experienceIndices?)` - Apply experiences

##### Frontend Integration Points

**File:** `frontend/app/page.tsx` (Home page)
- "Browse Clinical Templates" button
- Conditionally renders `TemplateBrowser` when button clicked
- `TemplateDetailsModal` for viewing template details
- `handleCreateFromTemplate()` - Creates persona and navigates to persona page

**File:** `frontend/app/persona/[id]/page.tsx` (Persona detail page)
- "Remix with Template" button in header (only shows if templates available)
- `TemplateRemixModal` component (defined inline in page.tsx)
- State: `templates`, `selectedTemplate`, `selectedExperienceIndices`, `applyingExperiences`
- Functions: `loadTemplates()`, `handleSelectTemplate()`, `handleApplyTemplateExperiences()`

---

### FEATURE 2: TIMELINE REMIX SYSTEM

#### Purpose
Allows users to save timeline snapshots and compare "what if" scenarios (e.g., "What if early intervention?" vs "Original timeline").

#### Components Added

##### Backend Models
**File:** `backend/app/models/timeline_snapshot.py`
- `TimelineSnapshot` SQLAlchemy model
- **CRITICAL SCHEMA MISMATCH IDENTIFIED:** Model fields don't match service usage

**Model Fields (as defined):**
```python
snapshot_personality = Column(JSON, nullable=False)
snapshot_symptoms = Column(JSON, nullable=False)
snapshot_symptom_severity = Column(JSON, nullable=False)
snapshot_attachment_style = Column(String, nullable=False)
snapshot_trauma_markers = Column(JSON, nullable=False)
snapshot_age = Column(JSON, nullable=False)  # NOTE: JSON, not Integer!
```

**Service Usage (remix_service.py):**
```python
personality_snapshot=dict(persona.current_personality),
trauma_markers_snapshot=list(persona.current_trauma_markers),
symptom_severity_snapshot=symptom_severity_snapshot,
personality_difference=personality_difference,
symptom_difference=None
```

**MISMATCH:** Service uses `personality_snapshot`, `trauma_markers_snapshot`, `symptom_severity_snapshot` but model defines `snapshot_personality`, `snapshot_symptoms`, `snapshot_symptom_severity`, `snapshot_age` (as JSON instead of Integer).

##### Backend Services
**File:** `backend/app/services/remix_service.py`

**Functions:**
1. `create_timeline_snapshot(db, persona_id, label, description, template_id, modifications)` - Creates snapshot
2. `get_persona_snapshots(db, persona_id)` - Lists snapshots for persona
3. `compare_snapshots(db, snapshot_id_1, snapshot_id_2)` - Compares two snapshots
4. `calculate_intervention_impact(db, persona_id, baseline_snapshot_id)` - Analyzes intervention effectiveness
5. `get_remix_suggestions_for_persona(db, persona_id, template_id)` - Generates "what if" suggestions
6. `delete_snapshot(db, snapshot_id)` - Deletes snapshot

**Schema Mismatch Issues:**
- Service tries to set fields that don't exist in model
- Model has `snapshot_age` as JSON, but should be Integer
- Field name mismatches between model and service

##### Backend API Routes
**File:** `backend/app/api/routes/remix.py`
**Prefix:** `/api/v1/remix`

**Endpoints:**

1. **POST `/api/v1/remix/snapshots`** - Create snapshot
   - Request: `CreateTimelineSnapshotRequest` (persona_id, label, description, template_id, modifications)
   - Returns: `TimelineSnapshotResponse`
   - Protected by `require_remix_feature()` dependency

2. **GET `/api/v1/remix/personas/{persona_id}/snapshots`** - List persona snapshots
   - Returns: `List[TimelineSnapshotResponse]`
   - Protected by `require_remix_feature()` dependency

3. **GET `/api/v1/remix/snapshots/{snapshot_id}`** - Get single snapshot
   - Returns: `TimelineSnapshotResponse`
   - Protected by `require_remix_feature()` dependency

4. **POST `/api/v1/remix/snapshots/compare`** - Compare two snapshots
   - Request: `CompareSnapshotsRequest` (snapshot_id_1, snapshot_id_2)
   - Returns: `CompareSnapshotsResponse` (detailed comparison with summary)
   - Protected by `require_remix_feature()` dependency

5. **GET `/api/v1/remix/personas/{persona_id}/intervention-impact`** - Calculate intervention impact
   - Query param: `baseline_snapshot_id`
   - Returns intervention effectiveness analysis
   - Protected by `require_remix_feature()` dependency

6. **GET `/api/v1/remix/personas/{persona_id}/suggestions`** - Get remix suggestions
   - Query param: `template_id` (optional)
   - Returns: `{suggestions: [...]}`
   - Protected by `require_remix_feature()` dependency

7. **DELETE `/api/v1/remix/snapshots/{snapshot_id}`** - Delete snapshot
   - Protected by `require_remix_feature()` dependency

##### Frontend API Client
**File:** `frontend/lib/api/templates.ts` (includes remix API)

**Exports:**
- `remixAPI.createSnapshot(personaId, label, description?, templateId?)` - Create snapshot
- `remixAPI.listSnapshots(personaId)` - List snapshots
- `remixAPI.getSnapshot(snapshotId)` - Get snapshot
- `remixAPI.compareSnapshots(snapshotId1, snapshotId2)` - Compare snapshots
- `remixAPI.getInterventionImpact(personaId, baselineSnapshotId)` - Get intervention impact
- `remixAPI.getSuggestions(personaId, templateId?)` - Get suggestions
- `remixAPI.deleteSnapshot(snapshotId)` - Delete snapshot

##### Frontend Integration Points

**File:** `frontend/app/persona/[id]/page.tsx`
- "Save Snapshot" button in header
- Snapshots section displays saved snapshots
- "Compare Snapshots" button (shows when 2+ snapshots)
- `CreateSnapshotModal` component (defined inline)
- `SnapshotComparisonView` component (imported from components)
- State: `snapshots`, `showCreateSnapshot`, `showSnapshotComparison`, `comparisonSnapshot1`, `comparisonSnapshot2`
- Functions: `loadSnapshots()`

---

## PART 2: ROUTE INTERACTION MAP

### Templates API Flow

```
Frontend (page.tsx)
  ↓
templatesAPI.list()
  ↓
GET /api/v1/templates
  ↓
templates.py::list_templates()
  ↓
template_service.py::populate_templates_database() [if DB empty]
  ↓
template_service.py::load_template_from_json() [for each JSON file]
  ↓
template_service.py::create_template_from_dict() [creates DB records]
  ↓
Returns: List[ClinicalTemplateListResponse]
```

```
Frontend (TemplateBrowser)
  ↓
templatesAPI.get(templateId)
  ↓
GET /api/v1/templates/{template_id}
  ↓
templates.py::get_template_details()
  ↓
db.query(ClinicalTemplate).filter(ClinicalTemplate.id == template_id)
  ↓
Returns: ClinicalTemplateResponse (includes predefined_experiences, predefined_interventions)
```

```
Frontend (TemplateRemixModal in persona/[id]/page.tsx)
  ↓
templatesAPI.applyExperiences(personaId, templateId, indices)
  ↓
POST /api/v1/templates/personas/{persona_id}/apply-experiences
  ↓
templates.py::apply_experience_set()
  ↓
1. Validates persona exists
2. template_service.py::get_template_experiences(template_id, db)
3. Loops through selected experience indices:
   a. Gets previous_experiences for context
   b. psychology_engine.py::analyze_experience(persona_id, description, age, db, previous_experiences)
   c. Creates Experience() record
   d. Updates persona.current_personality
   e. Updates persona.current_trauma_markers
   f. Creates PersonalitySnapshot() record
4. db.commit()
  ↓
Returns: ApplyExperienceSetResponse
```

### Remix API Flow

```
Frontend (persona/[id]/page.tsx)
  ↓
remixAPI.createSnapshot(personaId, label, ...)
  ↓
POST /api/v1/remix/snapshots
  ↓
remix.py::create_snapshot()
  ↓
remix_service.py::create_timeline_snapshot()
  ↓
1. Gets persona + all experiences + interventions
2. Builds modified_experiences JSON array
3. Builds modified_interventions JSON array
4. Calculates symptom_severity_snapshot (aggregates from experiences)
5. Creates TimelineSnapshot() record [SCHEMA MISMATCH HERE]
  ↓
Returns: TimelineSnapshotResponse
```

```
Frontend (persona/[id]/page.tsx)
  ↓
remixAPI.listSnapshots(personaId)
  ↓
GET /api/v1/remix/personas/{persona_id}/snapshots
  ↓
remix.py::list_persona_snapshots()
  ↓
remix_service.py::get_persona_snapshots()
  ↓
db.query(TimelineSnapshot).filter(TimelineSnapshot.persona_id == persona_id)
  ↓
Returns: List[TimelineSnapshotResponse]
```

```
Frontend (SnapshotComparison component)
  ↓
remixAPI.compareSnapshots(snapshotId1, snapshotId2)
  ↓
POST /api/v1/remix/snapshots/compare
  ↓
remix.py::compare_timeline_snapshots()
  ↓
remix_service.py::compare_snapshots()
  ↓
1. Loads both snapshots
2. Calculates personality_differences (trait by trait)
3. Calculates symptom_differences (sets: only_in_1, only_in_2, in_both)
4. Calculates symptom_severity_differences
5. Generates natural language summary
  ↓
Returns: CompareSnapshotsResponse
```

---

## PART 3: FAILURES & ISSUES - COMPLETE LOG

### FAILURE 1: SQLAlchemy ORM Object in SQL Expression

**Error Message:**
```
SQL expression element expected, got <app.models.persona.Persona object>
```

**Location:**
- **File:** `backend/app/api/routes/templates.py`
- **Function:** `apply_experience_set()` (line 305)
- **Trigger:** During template experience application, when calling `analyze_experience()`

**Root Cause:**
The `analyze_experience()` function was originally designed to accept a `Persona` ORM object directly. When SQLAlchemy tried to use this object in a query context or comparison, it failed because ORM objects cannot be used as SQL expressions.

**Original Problematic Code:**
```python
# backend/app/services/psychology_engine.py (original)
async def analyze_experience(
    persona,  # ❌ Persona ORM object
    experience_description: str,
    age_at_event: int,
    previous_experiences: List = None
) -> Dict:
    # Function accessed persona.name, persona.current_personality, etc.
```

**Where It Was Called:**
```python
# backend/app/api/routes/templates.py (original)
analysis = await analyze_experience(
    persona=persona,  # ❌ Passing ORM object
    experience_description=exp_data["description"],
    age_at_event=exp_data["age"],
    previous_experiences=previous_experiences
)
```

**Fix Applied:**
1. Refactored `analyze_experience()` to accept `persona_id: str` and `db: Session`
2. Function now fetches persona internally if needed
3. Added defensive assertion to prevent ORM objects
4. Updated all call sites to pass `persona_id` instead of `persona`

**Fixed Code:**
```python
# backend/app/services/psychology_engine.py (fixed)
async def analyze_experience(
    persona_id: str,  # ✅ ID, not ORM object
    experience_description: str,
    age_at_event: int,
    db: Session,  # ✅ Added db parameter
    previous_experiences: List = None
) -> Dict:
    # Defensive assertion
    assert not isinstance(persona_id, Persona), "analyze_experience received Persona ORM object instead of persona_id"
    
    # Fetch persona if needed
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise ValueError(f"Persona {persona_id} not found")
    
    # Extract data as dict
    persona_data = {
        "name": persona.name,
        "baseline_age": persona.baseline_age,
        # ... etc
    }
    # Use persona_data for prompt generation
```

**Files Modified:**
- `backend/app/services/psychology_engine.py` - Function signature changed
- `backend/app/api/routes/templates.py` - Call site updated
- `backend/app/api/routes/experiences.py` - Call site updated
- `backend/app/services/psychology_engine.py` - `batch_analyze_experiences()` also fixed

**Status:** ✅ FIXED

---

### FAILURE 2: TimelineSnapshot Model Schema Mismatch

**Error Type:** Schema definition doesn't match service usage

**Location:**
- **Model File:** `backend/app/models/timeline_snapshot.py`
- **Service File:** `backend/app/services/remix_service.py`
- **Function:** `create_timeline_snapshot()` (line 111-124)

**Problem:**
The `TimelineSnapshot` model defines fields with different names than what the service uses when creating snapshots.

**Model Definition (timeline_snapshot.py):**
```python
class TimelineSnapshot(Base):
    snapshot_personality = Column(JSON, nullable=False)  # ❌ Different name
    snapshot_symptoms = Column(JSON, nullable=False)     # ❌ Different name
    snapshot_symptom_severity = Column(JSON, nullable=False)  # ❌ Different name
    snapshot_attachment_style = Column(String, nullable=False)
    snapshot_trauma_markers = Column(JSON, nullable=False)
    snapshot_age = Column(JSON, nullable=False)  # ❌ Should be Integer, not JSON
```

**Service Usage (remix_service.py line 111-124):**
```python
snapshot = TimelineSnapshot(
    # ...
    personality_snapshot=dict(persona.current_personality),  # ❌ Wrong field name
    trauma_markers_snapshot=list(persona.current_trauma_markers),  # ❌ Wrong field name
    symptom_severity_snapshot=symptom_severity_snapshot,  # ❌ Wrong field name
    personality_difference=personality_difference,  # ❌ Field doesn't exist in model
    symptom_difference=None  # ❌ Field doesn't exist in model
)
```

**Impact:**
- Creating snapshots will fail with `TypeError: unexpected keyword argument`
- Schema mismatch means the service code can't actually create snapshots

**Status:** ❌ NOT FIXED (user requested evaluation only, no code changes)

---

### FAILURE 3: Feature Flags Not Working Initially

**Error Message:**
```
Clinical templates feature is not enabled. Contact administrator.
```

**Location:**
- **File:** `backend/app/api/routes/templates.py`
- **Function:** `require_templates_feature()` (line 43-49)
- **Trigger:** All template endpoints return 404 when feature flag is False

**Root Cause:**
1. Feature flags were defined in `.env` but not in `Settings` class
2. Pydantic validation failed because `extra="forbid"` prevented unknown fields
3. `@lru_cache()` on settings meant server restart was required

**Original Problem:**
```python
# backend/app/core/config.py (original)
class Settings(BaseSettings):
    # ... other fields ...
    # ❌ feature_clinical_templates not defined
    class Config:
        extra = "forbid"  # ❌ Prevents .env fields not in Settings
```

**Fix Applied:**
```python
# backend/app/core/config.py (fixed)
class Settings(BaseSettings):
    # ...
    feature_clinical_templates: bool = Field(
        default=True,  # ✅ Enabled by default in dev
        env="FEATURE_CLINICAL_TEMPLATES"
    )
    feature_remix_timeline: bool = Field(
        default=True,  # ✅ Enabled by default in dev
        env="FEATURE_REMIX_TIMELINE"
    )
```

**Files Modified:**
- `backend/app/core/config.py` - Added feature flag fields with Field(env="...")
- `backend/app/core/feature_flags.py` - Updated to read from settings instead of os.getenv()

**Status:** ✅ FIXED (but requires server restart due to @lru_cache())

---

### FAILURE 4: Missing onResetTemplate Prop

**Error Message:**
```
ReferenceError: onResetTemplate is not defined
```

**Location:**
- **File:** `frontend/app/persona/[id]/page.tsx`
- **Line:** 530 (inside TemplateRemixModal component)
- **Component:** `TemplateRemixModal`

**Problem:**
The `TemplateRemixModal` component's TypeScript type definition included `onResetTemplate`, and it was passed as a prop from the parent, but it was missing from the destructured function parameters.

**Problematic Code:**
```typescript
// frontend/app/persona/[id]/page.tsx
function TemplateRemixModal({
  personaId,
  templates,
  selectedTemplate,
  loadingTemplateDetails,
  selectedExperienceIndices,
  applyingExperiences,
  onSelectTemplate,
  onToggleExperience,
  onApply,  // ❌ Missing onResetTemplate here
  onClose,
  onSuccess,
}: {
  // Type definition included onResetTemplate: () => void
  // But it wasn't destructured
})
```

**Fix Applied:**
Added `onResetTemplate` to destructured parameters.

**Status:** ✅ FIXED

---

### FAILURE 5: CORS Errors

**Error Message:**
```
CORS Missing Allow Origin
Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource
```

**Location:**
- Frontend on `http://localhost:3001` trying to access backend on `http://localhost:8000`

**Root Cause:**
CORS middleware was configured but didn't include port 3001 (frontend was running on alternative port).

**Fix Applied:**
Added `http://localhost:3001` and `http://127.0.0.1:3001` to `allow_origins` in `backend/app/main.py`.

**Status:** ✅ FIXED (but requires server restart)

---

## PART 4: ARCHITECTURAL ANALYSIS

### Data Flow: Template Experience Application

```
1. User clicks "Remix with Template" button
   ↓
2. Frontend: templatesAPI.list() → GET /api/v1/templates
   ↓
3. Backend: list_templates() → Returns template list
   ↓
4. User selects template
   ↓
5. Frontend: templatesAPI.get(templateId) → GET /api/v1/templates/{id}
   ↓
6. Backend: get_template_details() → Returns full template with predefined_experiences
   ↓
7. User selects experiences to apply (checkboxes)
   ↓
8. Frontend: templatesAPI.applyExperiences(personaId, templateId, indices)
   ↓
9. Backend: POST /api/v1/templates/personas/{persona_id}/apply-experiences
   ↓
10. Backend: apply_experience_set()
    a. Validates persona exists
    b. Gets template experiences (from DB or JSON fallback)
    c. For each selected experience index:
       - Gets previous_experiences for context
       - Calls analyze_experience(persona_id, description, age, db, previous_experiences)
       - analyze_experience() fetches persona internally
       - Creates Experience() record
       - Updates persona.current_personality (in-place JSON modification)
       - Updates persona.current_trauma_markers
       - Creates PersonalitySnapshot() record
    d. db.commit()
    ↓
11. Returns: ApplyExperienceSetResponse with personality_before/after
    ↓
12. Frontend reloads timeline to show new experiences
```

### Critical Dependencies

**Templates depend on:**
- `psychology_engine.analyze_experience()` - For AI analysis of template experiences
- `Experience` model - For storing applied experiences
- `PersonalitySnapshot` model - For tracking personality state changes
- `Persona` model - For updating persona state
- JSON template files in `backend/data/templates/`

**Remix depends on:**
- `TimelineSnapshot` model - **SCHEMA MISMATCH IDENTIFIED**
- `Persona`, `Experience`, `Intervention` models - For snapshot data
- Templates (optional) - For template-specific remix suggestions

### Feature Flag Protection

**Templates endpoints protected by:**
- `require_templates_feature()` dependency
- Checks `FeatureFlags.is_enabled(FeatureFlags.CLINICAL_TEMPLATES)`
- Returns 404 if disabled

**Remix endpoints protected by:**
- `require_remix_feature()` dependency
- Checks `FeatureFlags.is_enabled(FeatureFlags.REMIX_TIMELINE)`
- Returns 404 if disabled

**Feature flag evaluation:**
- `FeatureFlags.is_enabled()` reads from `settings` object (from config.py)
- Settings reads from `.env` via `Field(env="FEATURE_CLINICAL_TEMPLATES")`
- `@lru_cache()` on `get_settings()` means restart required for changes

---

## PART 5: KNOWN ISSUES & LIMITATIONS

### ISSUE 1: TimelineSnapshot Schema Mismatch (CRITICAL)

**Status:** ❌ NOT RESOLVED

**Problem:**
- Model defines fields: `snapshot_personality`, `snapshot_symptoms`, `snapshot_symptom_severity`, `snapshot_age` (as JSON)
- Service uses fields: `personality_snapshot`, `trauma_markers_snapshot`, `symptom_severity_snapshot`, `personality_difference`, `symptom_difference`
- Field names don't match
- `snapshot_age` is JSON in model but should be Integer
- Service tries to set fields that don't exist in model

**Impact:**
- Creating snapshots will fail
- Remix feature cannot save snapshots

**Files Affected:**
- `backend/app/models/timeline_snapshot.py` - Model definition
- `backend/app/services/remix_service.py` - Service usage (line 111-124)
- `backend/app/schemas/template_schemas.py` - Schema definition (may also need update)

---

### ISSUE 2: Template Remix UI Moved from Persona Page to Home Page

**Status:** ⚠️ PARTIALLY IMPLEMENTED

**What Happened:**
- User requested templates to be on main page, not individual persona pages
- Template browsing moved to `frontend/app/page.tsx`
- But `TemplateRemixModal` still exists in `frontend/app/persona/[id]/page.tsx` for applying experiences to existing personas

**Current State:**
- Home page: Browse templates, create new personas from templates
- Persona page: "Remix with Template" button to apply template experiences to existing persona

**Confusion:**
- Two different workflows: "Create from template" vs "Apply template experiences to existing persona"
- Both use same templates but different endpoints

---

### ISSUE 3: Experience Addition Failing (Current Issue)

**Status:** ❌ CURRENT PROBLEM

**User Report:**
"now were back to cant add experience"

**Possible Causes:**
1. SQLAlchemy error may have re-emerged if analyze_experience() is called incorrectly
2. CORS error blocking requests
3. Backend server not running
4. Database connection issue
5. Another ORM object boundary violation

**Investigation Needed:**
- Check if `add_experience` endpoint (`POST /api/v1/personas/{persona_id}/experiences`) works
- Verify `analyze_experience()` call in `experiences.py` uses correct signature
- Check backend logs for actual error

---

### ISSUE 4: Template JSON Path Fallback Logic

**File:** `backend/app/services/template_service.py` (line 21-34)

**Problem:**
The service has a fallback path to `remix component/step 1` directory. This suggests uncertainty about where template files should live.

**Code:**
```python
TEMPLATE_JSON_DIR = Path(__file__).parent.parent.parent / "data" / "templates"
FALLBACK_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "remix component" / "step 1"
```

**Impact:**
- Templates might load from wrong location
- Path resolution could fail if project structure changes

---

## PART 6: TESTING STATUS

### Templates API
- ✅ List templates endpoint works (confirmed by curl test)
- ✅ Feature flags enabled (confirmed by debug endpoint)
- ❌ Apply experiences endpoint - FAILING (SQLAlchemy error occurred, fixed, but user reports still failing)
- ❓ Create persona from template - Not tested
- ❓ Get template details - Not tested

### Remix API
- ❌ Create snapshot - WILL FAIL (schema mismatch)
- ❌ List snapshots - Not tested
- ❌ Compare snapshots - Not tested
- ❌ All remix endpoints - Likely failing due to schema mismatch

### Frontend Integration
- ✅ Templates load on home page
- ✅ "Remix with Template" button appears on persona page
- ❌ Template experience application - FAILING (backend error)
- ❌ Snapshot creation - Not tested (will fail due to schema mismatch)

---

## PART 7: RECOMMENDATIONS

### CRITICAL FIXES NEEDED

1. **Fix TimelineSnapshot Schema Mismatch**
   - Align model fields with service usage
   - Change `snapshot_age` from JSON to Integer
   - Add missing fields: `personality_difference`, `symptom_difference`
   - Update service to use correct field names OR update model to match service

2. **Investigate Current Experience Addition Failure**
   - Check backend logs
   - Verify `add_experience` endpoint
   - Confirm `analyze_experience()` is called correctly
   - Test with curl/Postman to isolate frontend vs backend issue

3. **Resolve Template JSON Path**
   - Decide on single canonical location
   - Remove fallback logic or make it more explicit
   - Document template file location in README

### ARCHITECTURAL IMPROVEMENTS

1. **Database Migration for TimelineSnapshot**
   - Create Alembic migration to fix schema
   - Handle existing data if any

2. **Error Handling**
   - Add better error messages when templates not found
   - Add validation for experience indices
   - Add rollback handling in apply_experience_set()

3. **Testing**
   - Add integration tests for template application
   - Add tests for remix snapshots
   - Test schema compatibility

---

## SUMMARY

**Features Added:** 2 major features (Clinical Templates, Timeline Remix)

**Backend Files Added/Modified:** ~15 files
**Frontend Files Added/Modified:** ~8 files

**Critical Issues:** 1 (TimelineSnapshot schema mismatch)
**Resolved Issues:** 4 (SQLAlchemy ORM, feature flags, onResetTemplate, CORS)
**Current Issues:** 1 (experience addition failing - needs investigation)

**Status:** Templates feature partially working, Remix feature blocked by schema mismatch, experience addition currently failing for unknown reason.

---

**END OF REPORT**


