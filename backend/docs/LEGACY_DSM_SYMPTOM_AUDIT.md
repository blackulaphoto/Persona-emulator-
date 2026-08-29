# Legacy DSM and symptom subsystem audit

## Scope and conclusion

This subsystem is live but parallel to the developmental engine. Do not surface it beside `ClinicalPatternHypothesis` as one coherent model. Preserve taxonomy and selected therapy metadata; quarantine the disorder writer and intervention calculator pending an architecture decision.

## What still works

- `app/main.py` registers `app/api/routes/symptoms.py`.
- Read routes expose disorder lists, categories, details, and symptoms.
- Authenticated routes read `PersonaSymptom` and `SymptomHistory`.
- The assessment route updates those rows and history.
- The intervention-effectiveness route returns a duration/adherence-adjusted reduction.
- Migration `008_add_persona_symptoms_tables.py` creates both tables.

## Data and conflicts

- `PersonaSymptom` stores a disorder-like name, severity, category, onset, status, generated details, and experience IDs. `SymptomHistory` stores before/after changes.
- `SYMPTOM_TAXONOMY` is static DSM/ICD-oriented reference data.
- `ClinicalPatternHypothesis` is the canonical evidence model with supporting/contradicting evidence, precursors, direction, and earned strength. `PersonaSymptom` writes a second disorder-like truth.
- Legacy assessment reads `Experience.event_type` and `Experience.severity`; the current route does not write them. Missing values default every event to `trauma` and severity `5`.
- Random symptom variance means unchanged history can produce changed persisted details.
- The effectiveness calculator duplicates therapy matching with a small hardcoded table and arbitrary default. The maintained route uses the therapy database and pattern/state/trait logic.
- The UI reads adapter/snapshot fields, not `PersonaSymptom`; no frontend client consumes these routes.

## Preserve

- Preserve `SYMPTOM_TAXONOMY` as reference knowledge; the evidence accumulator validates pattern keys against it.
- Preserve `therapy_database.py` metadata used by the maintained intervention engine.
- Preserve existing symptom/history rows until a migration decision. Delete nothing in this pass.
- Keep taxonomy reads for internal/reference use without presenting them as diagnosis.

## Integrate later

- Derive future symptom presentation from canonical hypothesis, exposure, and functional-observation evidence.
- Attach taxonomy labels/codes to hypothesis keys as metadata only; taxonomy must not set strength.
- Compare historical symptom rows before migration; leave ambiguous rows unmapped.
- Explicitly decide whether intervention effectiveness uses the maintained engine, literature metadata, or retirement.

## Deprecate or quarantine

- Quarantine the symptom assessment writer: dead inputs, trauma defaults, parallel truth, and nondeterminism.
- Deprecate fixed experience-to-disorder arithmetic and random symptom breakdown as inference.
- Deprecate the current intervention-effectiveness calculator; it implies unsupported precision.
- Do not add frontend symptom/history navigation before resolving the parallel model.

No broken read-only issue prevented inspection, so no legacy code was changed.
