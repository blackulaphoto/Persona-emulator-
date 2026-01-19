# Database Seeding Scripts

This directory contains scripts for seeding the database with clinical templates and other data.

## Available Scripts

### seed_psych_templates.py

Seeds the `clinical_templates` table with 6 evidence-based psychological disorder templates converted from TypeScript template files.

**Templates Included:**
1. **NPD (Narcissistic Personality Disorder)** - Marcus: Classic developmental pathway through excessive praise and emotional neglect
2. **Schizophrenia** - Daniel: Neurodevelopmental trajectory from prodrome to first episode psychosis
3. **SUD (Substance Use Disorder)** - Aisha: Self-medication pathway from trauma to addiction
4. **MDD (Major Depressive Disorder)** - Sofia: Kindling/stress-sensitization model of recurrent depression
5. **Anorexia Nervosa** - Lily: Perfectionism-control pathway to eating disorder
6. **OCD (Obsessive-Compulsive Disorder)** - Ryan: Childhood-onset OCD with contamination and symmetry themes

**Usage:**

```bash
# From backend directory
cd backend

# Seed database (will warn if templates already exist)
python scripts/seed_psych_templates.py

# Force reseed (deletes existing templates first)
python scripts/seed_psych_templates.py --force
```

**What it does:**
- Creates database tables if they don't exist
- Checks for existing templates
- Converts TypeScript template data to SQLAlchemy models
- Maps personality traits to Big Five format
- Separates life events into experiences and interventions
- Inserts all 6 templates with complete clinical data

**Template Structure:**
Each template includes:
- **Basic Info**: name, disorder_type, description, clinical_rationale
- **Baseline Configuration**: age, gender, background, personality (Big Five), attachment style
- **Predefined Experiences**: Array of life events with ages, impacts, symptoms, personality changes
- **Predefined Interventions**: Array of therapy/treatment events with outcomes
- **Expected Outcomes**: Final personality state, symptoms, trauma markers
- **Research Citations**: Evidence-based references
- **Remix Suggestions**: Alternative pathway scenarios

**Database Schema:**
Templates are stored in the `clinical_templates` table with JSON fields for complex data structures. See `backend/app/models/clinical_template.py` for full schema.

**Verification:**
After seeding, you can verify the data was inserted correctly:

```python
from app.core.database import SessionLocal
from app.models.clinical_template import ClinicalTemplate

db = SessionLocal()
templates = db.query(ClinicalTemplate).all()
print(f"Total templates: {len(templates)}")
for t in templates:
    print(f"- {t.disorder_type}: {t.name}")
db.close()
```

## Source Templates

The original TypeScript templates are located in:
```
new templates/psych-templates/
├── npd_template.ts
├── schizophrenia_template.ts
├── sud_template.ts
├── mdd_template.ts
├── anorexia_template.ts
└── ocd_template.ts
```

## Notes

- Templates are designed for educational and research purposes
- Based on evidence-based psychological research and clinical models
- Include detailed clinical rationales and research citations
- Can be used to create personas demonstrating specific disorder development pathways
- Remix suggestions allow exploration of "what if" scenarios with different interventions
