# TypeScript to Python Database Conversion Mapping

This document explains how the TypeScript template fields were mapped to the Python database schema.

## Field Mappings

### Direct Mappings (1:1)

| TypeScript Field | Database Field | Notes |
|-----------------|----------------|-------|
| `name` | `name` | Character name |
| `age` | `baseline_age` | Starting age for template |
| `gender` | `baseline_gender` | Gender identity |
| `backgroundStory` | `baseline_background` | Background context |
| `narrative` | `clinical_rationale` | Long-form clinical explanation |

### Derived/Computed Mappings

| TypeScript Field | Database Field | Transformation |
|-----------------|----------------|----------------|
| `personalityTraits[]` | `baseline_personality` | Converted to Big Five dict (0-1 scale) |
| `lifeEvents[]` (non-therapy) | `predefined_experiences[]` | Filtered and restructured |
| `lifeEvents[]` (type: therapy) | `predefined_interventions[]` | Extracted therapy events only |
| `currentSymptoms[]` | `expected_outcomes.symptoms_developed[]` | Final symptom state |

### Personality Trait Conversion

TypeScript personality traits (0-100 scale) are converted to Big Five format (0-1 scale):

```typescript
// TypeScript format
personalityTraits: [
  { name: 'Openness', value: 55, description: '...' },
  { name: 'Conscientiousness', value: 75, description: '...' },
  { name: 'Extraversion', value: 80, description: '...' },
  { name: 'Agreeableness', value: 25, description: '...' },
  { name: 'Emotional Sensitivity', value: 85, description: '...' }
]
```

```python
# Python database format
baseline_personality = {
    'openness': 0.55,
    'conscientiousness': 0.75,
    'extraversion': 0.80,
    'agreeableness': 0.25,
    'neuroticism': 0.85  # Emotional Sensitivity → Neuroticism
}
```

**Note:** "Emotional Sensitivity" is mapped to "Neuroticism" as they represent the same Big Five dimension.

### Experience Object Mapping

TypeScript `lifeEvents` (non-therapy) are converted to `predefined_experiences`:

```typescript
// TypeScript format
{
  id: 'npd1',
  age: 5,
  title: 'The Golden Child',
  description: 'Marcus\'s parents constantly praised him...',
  type: 'challenge',
  impact: 'Developed inflated sense of self-importance...',
  personalityChanges: [...],
  symptoms: [...]
}
```

```python
# Python database format
{
    'age': 5,
    'category': 'family_dynamics',  # Derived from context
    'valence': 'negative',  # Mapped from type
    'intensity': 'moderate',  # Calculated from symptom severity
    'title': 'The Golden Child',
    'description': 'Marcus\'s parents constantly praised him...',
    'impact': 'Developed inflated sense of self-importance...',
    'clinical_note': 'Excessive praise without emotional attunement...',
    'symptoms_developed': [...],  # Original symptoms array
    'personality_changes': [...]  # Original personality changes
}
```

**Type to Valence Mapping:**
- `challenge` → `negative`
- `growth` → `positive`
- `neutral` → `neutral`
- `trauma` → `negative`

**Intensity Calculation:**
Based on average symptom severity:
- Average >= 8 → `severe`
- Average >= 6 → `moderate`
- Average < 6 → `mild`

### Intervention Object Mapping

TypeScript `lifeEvents` with `type: 'therapy'` are converted to `predefined_interventions`:

```typescript
// TypeScript format
{
  id: 'sud7',
  age: 24,
  type: 'therapy',
  therapyApproach: 'Inpatient rehab + 12-step',
  sessionCount: 30,
  description: 'Aisha entered inpatient treatment...',
  impact: 'First treatment episode...',
  therapyOutcomes: [
    { metric: 'Days of sobriety', improvement: 100 },
    { metric: 'Coping skills', improvement: 40 }
  ]
}
```

```python
# Python database format
{
    'age': 24,
    'therapy_type': 'Inpatient rehab + 12-step',
    'duration': '30_sessions',
    'intensity': 'weekly',  # Default assumption
    'rationale': 'First treatment episode...',
    'description': 'Aisha entered inpatient treatment...',
    'outcomes': [
        {'metric': 'Days of sobriety', 'improvement': 100},
        {'metric': 'Coping skills', 'improvement': 40}
    ]
}
```

### Expected Outcomes Structure

```python
expected_outcomes = {
    'personality_changes': {
        # Final Big Five values
        'openness': 0.55,
        'conscientiousness': 0.75,
        'extraversion': 0.80,
        'agreeableness': 0.25,
        'neuroticism': 0.85
    },
    'symptoms_developed': [
        # List of final symptoms (strings)
        'Grandiosity',
        'Need for admiration',
        'Lack of empathy'
    ],
    'attachment_changes': 'anxious',  # Final attachment style
    'trauma_markers': [
        # List of trauma-related patterns (strings)
        'Narcissistic vulnerability to criticism',
        'Inability to form intimate relationships'
    ]
}
```

## New Fields Added

These fields were added in the database schema but not present in TypeScript templates:

| Field | Purpose | Default/Derivation |
|-------|---------|-------------------|
| `disorder_type` | Category identifier | Derived from template (e.g., "NPD", "MDD") |
| `description` | User-facing summary | Created from narrative/background |
| `clinical_rationale` | Evidence-based explanation | From `narrative` field |
| `baseline_attachment_style` | Starting attachment | Inferred from background (default: "secure") |
| `citations` | Research references | Added manually based on template content |
| `remix_suggestions` | Alternative scenarios | Added to suggest "what if" modifications |

## Data Type Conversions

| TypeScript Type | Database Type | Notes |
|----------------|---------------|-------|
| `string` | `String/Text` | Direct conversion |
| `number` (0-100) | `FLOAT` (0-1) | Personality traits scaled down |
| `number` (age) | `Integer` | Direct conversion |
| `array of objects` | `JSON` | Serialized as JSON |
| `object` | `JSON` | Serialized as JSON |

## Validation Rules Applied

1. **Age Validation**: All ages are positive integers
2. **Personality Traits**: All Big Five values are between 0 and 1
3. **Symptom Severity**: Original severity values (0-10) preserved in JSON
4. **Required Fields**: name, disorder_type, description, clinical_rationale, baseline_age all required
5. **JSON Structure**: All JSON fields validated for proper structure

## Example: Complete Conversion

### TypeScript (npd_template.ts)
```typescript
export const npdTemplate = {
  id: 'npd_001',
  name: 'Marcus',
  age: 28,
  gender: 'male',
  tagline: 'The world revolves around achievement',
  backgroundStory: 'Marcus grew up as an only child...',
  emotionalStability: 45,
  personalityTraits: [
    { name: 'Openness', value: 55 },
    { name: 'Conscientiousness', value: 75 },
    // ...
  ],
  currentSymptoms: [
    { name: 'Grandiosity', severity: 9 },
    // ...
  ],
  lifeEvents: [
    { age: 5, title: 'The Golden Child', type: 'challenge', ... },
    // ...
  ],
  narrative: `Marcus presents as a highly successful...`
}
```

### Python Database (ClinicalTemplate model)
```python
ClinicalTemplate(
    name="Marcus - Narcissistic Personality Disorder",
    disorder_type="NPD",
    description="Marcus presents as a highly successful...",
    clinical_rationale="This template demonstrates the classic...",
    baseline_age=5,  # Starting age of first experience
    baseline_gender="male",
    baseline_background="Marcus grew up as an only child...",
    baseline_personality={
        'openness': 0.55,
        'conscientiousness': 0.75,
        'extraversion': 0.80,
        'agreeableness': 0.25,
        'neuroticism': 0.85
    },
    baseline_attachment_style="anxious",
    predefined_experiences=[...],  # Converted life events
    predefined_interventions=[],   # No therapy in NPD template
    expected_outcomes={
        'personality_changes': {...},
        'symptoms_developed': ['Grandiosity', ...],
        'attachment_changes': 'anxious',
        'trauma_markers': [...]
    },
    citations=[...],
    remix_suggestions=[...]
)
```

## Future Considerations

1. **Attachment Style Inference**: Could be improved with more sophisticated logic based on early experiences
2. **Category Assignment**: Could use NLP to better categorize experiences
3. **Intensity Calculation**: Could factor in more than just symptom severity
4. **Validation**: Could add more robust validation for clinical accuracy
5. **Versioning**: Consider adding template version tracking for updates
