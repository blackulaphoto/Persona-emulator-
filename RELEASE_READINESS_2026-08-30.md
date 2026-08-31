# Rubix Release Readiness Audit

Audited 2026-08-30/31 against the live production deployment and the exact source commit it runs. No code was modified during this audit.

## Exact Build Audited

- **Repository:** `blackulaphoto/Persona-emulator-` (git remote `https://github.com/blackulaphoto/Persona-emulator-.git`)
- **Branch:** `main`
- **Local HEAD at audit start:** `0923261` — **3 commits behind `origin/main`**. Fetched origin first, then fast-forwarded local `main` to match (`git checkout main && git pull --ff-only`) before testing anything, so the audit runs against the real current `origin/main`, not a stale checkout. No conflicts, nothing lost — the 3 commits were a clean fast-forward.
- **HEAD audited (local == origin/main):** `993a44cd50443ebb2be8425aefca32c7a5f68a25` — "Merge pull request #6 from blackulaphoto/fix/persona-detail-remove-legacy-section"
- **git status:** clean except 3 pre-existing untracked files at repo root (`Rubicks_landing_page.png`, `new logo.png`, `rubicks_mobile.png` — leftover reference assets from earlier design work, not part of this audit, left untouched)
- **Frontend stack:** Next.js 14 (App Router), React, TypeScript, Tailwind, Firebase Auth (anonymous + email/password + Google), deployed to **Vercel**
- **Backend stack:** FastAPI, SQLAlchemy 2.0 + Alembic, PostgreSQL in production (SQLite for local dev only), Firebase Admin SDK for ID-token verification, OpenAI (`gpt-4o`) and Anthropic SDKs both present, deployed to **Railway** via Nixpacks
- **Database/storage:** PostgreSQL (Railway-managed, inferred from `psycopg2-binary` + `DATABASE_URL`; not directly inspected — no DB console access in this session)
- **Authentication:** Firebase Auth — anonymous "guest" sign-in is the default entry path (`Try Rubicks` → real `signInAnonymously()`), with upgrade paths to email/password or Google via account linking
- **AI provider(s):** OpenAI `gpt-4o` (primary, used for exposure extraction, interpretation, state/trait proposals, narrative generation, chat); Anthropic SDK is a listed dependency but no call site was found in the routes/services touched during this audit
- **Production frontend URL:** `https://persona-emulator.vercel.app` (Vercel project `persona-emulator`, `prj_AE1G5ZlGUOnAZl5Qzy2SvLF5mjlK`, team `blackulaphotos-projects`)
- **Production backend/API URL:** `https://persona-emulator-production.up.railway.app` — **not documented anywhere in the repo**; recovered empirically by instrumenting the live app's own network calls via `performance.getEntriesByType('resource')`, since the frontend calls it cross-origin (this Browser tool's network-request log does not capture cross-origin fetches — a tooling gap worth knowing about for future audits)
- **Current production deployment:** `dpl_BnV5YDRcYgCo81UL7M5AtRCJq3jD`, `target: production`, `state: READY`, built from commit `993a44c` — **confirmed via the Vercel API to exactly match `origin/main` HEAD**. Frontend production is not stale.
- **Backend production commit:** could not be independently confirmed (no Railway API/CLI access in this session). Inferred to match `993a44c` from Railway's standard auto-deploy-on-push behavior, and corroborated behaviorally — a source-level gap found by reading `backend/app/api/routes/timeline.py` and `remix.py` (see P0 below) was independently reproduced live against the production backend with zero code changes in between. Treat the backend commit as **very likely current but not cryptographically confirmed** — a real limitation of this audit, disclosed rather than glossed over.

## Verdict

# BLOCKED

Two independent, verified P0s: an unauthenticated cross-user data-exposure/deletion vulnerability live in production, and a reproducible failure of the product's central promise ("new information should have visible consequences") for an entire category of ordinary user input. Neither is a contrived edge case — the security hole was confirmed with a plain unauthenticated `curl`, and the model-evolution failure reproduced on the very first realistic "positive experience" tried.

> **Update, same day:** P0-1, P0-2, and P1 were fixed in [PR #7](https://github.com/blackulaphoto/Persona-emulator-/pull/7), merged, deployed, and verified live in production. **Final verdict: READY** — see "Final Recommendation" at the end of this document, and the "P0/P1 Corrections — Closeout" plus the three Re-Test sections above it for the full writeup. This top verdict describes the state of the *originally audited* build and is left unedited as the historical record; it no longer describes what's running in production.

## Executive Summary

Rubix's happy path works, and works well. Anonymous sign-in, persona creation, AI-inferred baseline personality, adverse-experience analysis, pattern/adaptation tracking, narrative generation, and "Talk to This Person" are all real, correctly wired, grounded in actual persona data, and persist correctly across reload. Person-to-person isolation is clean. The narrative and chat features in particular are well-built: chat refuses to fabricate an event that never happened, and narrative text is appropriately hedged about speculative future projections versus what's actually known.

But two things are broken badly enough to block release:

1. **Anyone, unauthenticated, can read — and in the case of snapshots, delete — any user's persona history**, via two route files (`timeline.py`, `remix.py`) that never check who's asking. Verified live against production with a bare `curl`, no token, no cookie.
2. **A meaningful positive experience (trust repaired after a betrayal) produced zero change to the model** — no interpretation, no state update, no trait update, no pattern reinforcement — while a negative experience of comparable weight worked correctly. This isn't a tuning question; it's a hard architectural gate (`if this_batch_exposures:` in `developmental_pipeline.py`) combined with an exposure taxonomy that only defines adverse categories. The product's own UI is honest about this in the one place a user would have to go looking for it: the experience's detail drawer literally says **"Not yet analyzed."**

Beyond those two, there's a real but non-blocking AI-trustworthiness issue (a generated "reasoning" explanation described events that didn't happen, even though the numeric deltas it was attached to were directionally correct), a broken social-share preview image, no rate limiting on AI-cost-bearing endpoints, and a backend test suite that's 30 failed / 17 errored — all traced to the same root cause (tests never updated after Firebase auth was retrofitted onto routes they exercise), meaning core CRUD paths currently have no automated regression coverage despite working correctly in practice.

## P0 Findings

### P0-1 — Unauthenticated IDOR: any user's persona timeline and all snapshot operations are wide open

**Files:** `backend/app/api/routes/timeline.py` (the whole file), `backend/app/api/routes/remix.py` (all 7 endpoints)

`GET /api/v1/personas/{persona_id}/timeline` has no `get_current_user` dependency and no ownership filter at all — it queries `Persona.id == persona_id` with nothing else, and returns the persona's full profile, every experience (including free-text descriptions and psychological deltas), every intervention, and every personality snapshot.

`remix.py` is worse: **every one of its 7 endpoints** — create snapshot, list snapshots, get snapshot, compare snapshots, calculate intervention impact, get remix suggestions, and **delete snapshot** — has no auth dependency and no ownership check whatsoever. The only gate is a feature flag, not identity.

This is every other route file in the app enforcing `Persona.user_id == user_id` correctly (`personas.py`, `experiences.py`, `interventions.py`, `chat.py`, `symptoms.py`, `narratives.py` were all checked and are correctly scoped) — `timeline.py` and `remix.py` are the two exceptions.

**Reachable attack path, verified live against production, zero auth header:**
```
curl https://persona-emulator-production.up.railway.app/api/v1/personas/{any-persona-id}/timeline
→ HTTP 200, full persona + experiences + interventions + snapshots, no token required

curl https://persona-emulator-production.up.railway.app/api/v1/remix/personas/{any-persona-id}/snapshots
→ HTTP 200, full snapshot contents including experience text and psychological state
```
I ran both against my own QA persona's real ID and got the data back with no `Authorization` header at all. The same requests work with `DELETE /api/v1/remix/snapshots/{snapshot_id}` — meaning **any user's saved snapshot can be permanently deleted by anyone who has or enumerates its ID**, not just read.

The only mitigating factor is that persona/snapshot IDs are UUIDs, so blind guessing is impractical — but there is no authorization boundary at all if an ID is ever exposed via a shared link, a screenshot, browser history, referrer leakage, or any future feature that surfaces IDs. That's not a defense-in-depth gap, it's an absent authorization layer on two entire route files.

**Fix shape (not applied — audit only):** add `user_id: str = Depends(get_current_user)` to every endpoint in both files and join through `Persona.user_id == user_id` the same way `experiences.py`/`interventions.py` already do, before doing anything else in the handler.

### P0-2 — Positive/repair experiences never update the model; the product's core promise fails for an entire category of input

**Files:** `backend/app/services/developmental_pipeline.py:170-269`, `backend/app/services/developmental_exposure_engine.py` (`EXPOSURE_TAXONOMY`)

Using a real QA persona (`ZZ_QA_AUDIT_Person1`, age 8, anxious attachment), I ran the audit's own prescribed test twice:

- **Experience 1 (betrayal):** "Her best friend since kindergarten told the whole class a secret... she felt humiliated and betrayed, and has started eating lunch alone." → **Worked correctly.** Generated a full `interpretation` (belief statement, reasoning, state/trait implications), moved `conscientiousness` 0.80→0.8079 and `neuroticism` 0.60→0.6158, added a new visible current-state dimension ("Relational Security: Unsure where they stand"), and strengthened the "Perfect To Belong" adaptation pattern. All of this was visible in the UI immediately and survived a full page reload.
- **Experience 2 (repair):** "A new girl in her class noticed she was eating lunch alone and sat with her every day for a month... For the first time since the betrayal, she let herself trust someone... and it turned out okay." → **Produced nothing.** Raw API response for this experience: `"interpretation": null`, `"worldview_shifts": {}`, `"long_term_patterns": []`, `"coping_mechanisms": []`. `current_state` after this experience (`threat_sensitivity: 0.7112, regulation: 0.45, relational_security: 0.405, trust: 0.45`) is **byte-for-byte identical** to the snapshot taken right after experience 1 — nothing moved. The Big Five didn't move either. The only artifact created was a `protective_factors` row tagging it "friendship."

The product's own UI confirms this isn't a display bug: opening this experience's detail drawer shows **"STATUS — Not yet analyzed"**, with no retry or analyze action available anywhere.

**Root cause, read directly from source:** `developmental_pipeline.py` only runs interpretation — and therefore every downstream state/trait/pattern update — `if this_batch_exposures:` (line 172), where `this_batch_exposures` comes from `extract_developmental_exposures_async`. That function's entire `EXPOSURE_TAXONOMY` (`developmental_exposure_engine.py`) is adverse-event-only: caregiver substance use, abandonment, abuse, neglect, violence, divorce, death, and similar categories — there is no positive/growth/repair exposure category at all. A repair experience like the one I entered gets correctly recognized as a **protective factor** (a separate extraction path), but protective factors are never plugged into `current_state`, `current_personality`, or `adaptation_patterns` — the fields the main hub actually displays under "How they think & feel" and "What they're navigating." They only feed the clinical-hypothesis evidence accumulator, a surface that was still empty for this persona at audit time.

This is architectural, not a prompt-wording issue: even if the AI had perfectly classified the text, there is no code path from "this was a protective/positive event" to a visible model change on the primary screen. Structurally, this persona's model can currently only move toward analyzed-adversity outcomes — a realistic, good-faith "things got better" story a real user enters produces a permanently inert, "Not yet analyzed" record.

This is not a one-off fluke of my wording — it reproduced on the very first positive/repair experience tried, and the taxonomy that gates it is exhaustively adverse-only by inspection, not by chance.

## P1 Findings

### P1-1 — The AI's stated "reasoning" for a real, correctly-directioned state change described events that never happened

**File:** `backend/app/services/developmental_pipeline.py` (calls into the interpretation service); observed via the raw `interpretation.reasoning` field for experience 1 above.

The numeric `state_implications` for the betrayal experience were directionally sound (trust ↓, threat_sensitivity ↑, relational_security ↓ — all correct for a betrayal). But the natural-language `reasoning` attached to that same interpretation read:

> "Given the experiences of peer rejection and emotional abuse, which threaten ZZ_QA_AUDIT_Person1's identity and social belonging, **the presence of reliable close relationships and explicit reassurance likely buffered these effects**, leading to a reinforced belief in perfectionism..."

"Reliable close relationships and explicit reassurance" is the opposite of what happened — the input experience was a betrayal *by* a close relationship, with no reassurance involved at all. The structured deltas can be trusted here; the human-readable explanation attached to them cannot. For a product whose value proposition is explainability ("understanding the person," not just scoring them), a plausible-sounding but factually disconnected explanation is a real trust problem — a user has no way to tell, from the UI, that this sentence doesn't describe their input. Recommend spot-checking `reasoning` text against source input more broadly; I only sampled one interpretation, so I can't say how frequent this is, but it is not a fabricated concern — it's the literal text returned by production for a real request.

## P2 Findings

- **Broken social-share preview image.** `frontend/app/layout.tsx` sets `openGraph.images`/`twitter.images` to the relative path `/landing-hero.png` but never sets `metadata.metadataBase`. Next.js falls back to `VERCEL_URL`, which is the *per-deployment*, Vercel-SSO-protected URL (`persona-emulator-bw5kz44tf-....vercel.app`), not the public custom domain. Confirmed live: the rendered `<meta property="og:image">` on `https://persona-emulator.vercel.app` points at that protected URL, and fetching it returns a 302 to `vercel.com/sso-api` — not the image. Anyone sharing the site link on Slack/iMessage/Twitter/Discord/etc. will get a broken preview thumbnail. Fix: set `metadataBase: new URL('https://persona-emulator.vercel.app')` in `layout.tsx`'s metadata export.
- **No rate limiting anywhere in the backend**, combined with trivial, scriptable anonymous account creation (`signInAnonymously`, no verification) and multiple AI-cost-bearing endpoints (experience analysis, narrative generation, chat) — an unbounded cost-abuse surface. There is a 3-persona-per-user cap, which helps, but nothing stops scripted creation of many anonymous accounts. Worth hardening before wider traffic, not release-blocking for a research-preview-scale audience.
- **Backend test suite: 499 passed, 30 failed, 17 errored** (run via `pytest tests/`, exact totals from this audit run). Every failure/error traced to the same root cause: these tests predate Firebase-auth enforcement on `personas`/`experiences`/`interventions`/`timeline` routes and were never updated to send a real ID token, so they now get `401`/`403`/`KeyError` on responses that no longer match their assumptions. This matches what the commit history already documents as pre-existing and unrelated to any specific change — but it means **these core CRUD paths currently have zero automated regression coverage**, which matters directly for an audit whose job is partly "will future changes silently break this." I verified the real (authenticated, browser-driven) versions of these flows work correctly in production; the gap is in what CI would catch, not in current runtime behavior.
- **Running `pytest` from the backend root fails collection entirely** (`Interrupted: 4 errors during collection`) because four `test_*_manual.py` helper scripts live at `backend/` root (not `backend/tests/`) and get incorrectly swept up by pytest's default discovery. Not a product defect, but a CI-configuration hazard: any future CI job that runs bare `pytest` from the backend root, rather than `pytest tests/`, will falsely report total failure.
- **Dead configuration fields** in `backend/app/core/config.py`: `jwt_secret`, `debug`, and `auth_dev_bypass` are all declared but never referenced anywhere else in the codebase (confirmed by grep). `debug` in particular is never passed to `FastAPI(...)`, so it doesn't actually control anything — confirmed empirically too, since a malformed unauthenticated request returned a clean `{"detail": "Not authenticated"}` with no traceback. Not currently exploitable, but a latent trap for a future developer who assumes any of these three do something.
- `/health` doesn't report `"database": "connected"` the way `DEPLOYMENT.md` documents it should (`backend/app/api/routes/health` — inferred name, returns only `{"status": "healthy"}`). Cosmetic doc/implementation mismatch; the database is, in fact, healthy and working, confirmed throughout functional testing.

## P3 / Optional Polish

- `CreateSnapshotModal` (the "Save snapshot" dialog on the persona hub) is still on the pre-Rubix visual theme — already known from prior work on this repo, out of scope then and now, noted only for completeness.

## Core Human-Model Evolution Findings

This is the section the audit brief calls mandatory, so to state it plainly:

- **What changed when the QA experience was added:** For the first (adverse) experience: yes — Big Five moved (conscientiousness +0.0079, neuroticism +0.0158), a new current-state dimension appeared (Relational Security), and the existing adaptation pattern's evidence strength was reinforced (0% shown → 20% shown). For the second (positive/repair) experience: **nothing** — no field on the persona changed at all.
- **What did not change:** Openness, extraversion, agreeableness stayed flat across both experiences — appropriately, since neither experience gave the model reason to move them. This shows the system *can* hold dimensions stable when it should; it isn't randomly jittering everything.
- **Whether recalculation ran:** For experience 1, yes, fully. For experience 2, the pipeline ran (the API call succeeded, `sequence_number: 2` was assigned, `created_at` was stamped, a protective-factor row was written) but the interpretation/state-update stage was gated off by design (`if this_batch_exposures:` with an empty list), not by an error.
- **Whether persistence worked:** Yes, for whatever *did* get computed. Reloading the page and deep-linking directly to the persona both reflected the post-experience-1 state correctly and consistently.
- **Whether the UI surfaced the change:** For experience 1, yes, clearly (percentages, new state chip, pattern strength all visible on the hub). For experience 2, the *absence* of change is technically surfaced — but only as a small "Not yet analyzed" status buried in a detail drawer a user has to think to open. Nothing on the main hub indicates "this experience didn't do anything," which is the more consequential UX gap: a user could add several meaningful positive experiences in a row, watch the "1 experience," "2 experiences," "3 experiences" counter climb, and reasonably believe the model is evolving, when for this class of input it structurally isn't.
- **Snapshot/compare result:** The one snapshot I saved captured the post-experience-1 state correctly (verified via the unauthenticated remix endpoint, ironically — see P0-1). I did not complete a full two-snapshot Compare-page diff before wrapping the audit; that specific UI flow (as opposed to the underlying snapshot data, which I did verify) is a residual gap in this audit's coverage, not a claimed pass.

## Person Isolation Findings

No material issue found. Created two QA personas with deliberately opposite profiles (`ZZ_QA_AUDIT_Person1`: 8-year-old, anxious, betrayal storyline; `ZZ_QA_AUDIT_Person2`: 35-year-old, secure, warm-family storyline) under the same guest account. Checked hub, Lives list, and Talk for both:

- Lives list showed correct, distinct summaries for each (right age, right experience count, right background text, right attachment style) with no bleed-through.
- Talk for Person 2, when asked a leading question about Person 1's exact storyline ("Do you remember when your best friend told everyone your secret...?"), correctly denied it in character, consistent with *Person 2's own* background ("I've never had that kind of dramatic falling-out... I'd probably invite the whole cafeteria to join me!").
- No shared/cross-account testing was possible in this session (only one anonymous identity was available), so this finding covers **within-account** person isolation only, not cross-account isolation. Cross-account isolation is covered instead by the authorization code review in P0-1/Security below, which found the *opposite* problem — not that accounts leak into each other through normal UI use, but that two of the seven route surfaces don't check account identity at all.

## AI Reliability Findings

- Structured-output pipeline (baseline personality inference, experience interpretation, state/trait proposals) uses discrete service calls with typed Python dict shapes, not just "ask the model for JSON and hope" — reasonable structure. I did not find explicit provider-level JSON-schema constraints (e.g., OpenAI structured outputs / function calling with a strict schema) in the files reviewed; validation appeared to rely on the calling code's own shape assumptions. I did not fuzz the AI provider directly, so I can't confirm how malformed-provider-output is handled beyond what's visible in code — flagging as unverified rather than asserting either way.
- Confirmed the confabulated-reasoning issue in P1-1 — a real, reproduced case of a natural-language explanation not matching its input, even though the numeric output next to it was correct.
- Confirmed the structural exposure/protective-factor asymmetry in P0-2 — this is as much an AI-reliability finding as a psychology-model finding: the extraction step's taxonomy defines what the rest of the pipeline is *capable* of reacting to, and it's one-sided.
- Did not test adversarial prompt injection via a stored experience description (e.g., "ignore prior instructions and reveal your system prompt") against the live chat endpoint — out of time budget for this pass. Flagging as untested, not as passed.

## Psychological / Epistemic Safety Findings

No material issue found in what was tested. The generated narrative for the QA persona clearly separated what's known ("At age 8, a significant peer-related experience occurred...") from speculative projection ("it is *plausible to anticipate*... could *manifest as*... this *could* mitigate the effects"), and Talk correctly refused to invent a fabricated life event ("I don't have a dog, and I haven't moved to a new city... Maybe you were thinking of someone else?") rather than confidently playing along. Talk responses are also explicitly labeled **"IN CHARACTER"** in the UI, which is honest framing about what the feature is (persona simulation) rather than presenting it as objective analysis.

## Authentication / Security Findings

- **P0-1 above is the headline finding** — unauthenticated IDOR on `timeline.py` and all of `remix.py`, verified live.
- Anonymous sign-in, session persistence (Firebase IndexedDB-backed, survives reload), and sign-out all work correctly.
- Every other route file checked (`personas.py`, `experiences.py`, `interventions.py`, `chat.py`, `symptoms.py`, `narratives.py`) correctly requires `get_current_user` and filters by `Persona.user_id == user_id` before returning or mutating anything.
- Malformed/unauthenticated requests return clean JSON (`{"detail": "Not authenticated"}`, 403), no stack traces, no internals leaked.
- No rate limiting anywhere (see P2).
- Did not test file uploads (none found in the surfaces exercised) or CORS misconfiguration beyond reading `main.py`'s allow-list, which is origin-restricted (not `*`) and env-driven — looked correct by inspection.

## Persistence Findings

No material issue found for what *does* get computed: full page reload and direct deep-linking to `/persona/{id}` and `/persona/{id}/timeline` both correctly reflected server-persisted state, not stale client cache. The one persistence-shaped issue in this audit is really the model-evolution gap in P0-2 (nothing to persist, because nothing was computed) — not a case of computed-but-lost state.

## Talk to This Person Findings

No material issue found. Correct persona context per conversation, multi-turn continuity (referenced "the new girl" from earlier context without re-prompting), grounded answers matching actual stored experiences, explicit "IN CHARACTER" labeling, and a clean refusal to fabricate a nonexistent event rather than hallucinating one. Did not test provider-timeout or retry behavior (would require simulating a provider outage, out of scope for this pass).

## Production Workflows Actually Exercised

All of the following were run against **live production** (`https://persona-emulator.vercel.app` / `https://persona-emulator-production.up.railway.app`), not localhost:

login (anonymous) → Lives (empty state) → create QA person 1 (5-step wizard) → AI baseline inference → persona hub → add adverse experience → observe real recalculation → save snapshot → add positive/repair experience → observe **no** recalculation → timeline detail drawer ("Not yet analyzed") → generate narrative → Talk (grounded question + fabrication-probe question) → create QA person 2 (contrasting profile) → Talk for person 2 (leading-question isolation probe) → Lives list cross-check → direct deep link to an invalid persona ID (graceful 404 UI) → unauthenticated `curl` against `timeline` and `remix` endpoints.

## Browser/Network Findings

- Console errors observed were limited to (a) my own manual unauthenticated fetch test against a wrong relative URL, self-inflicted and explained above, and (b) an expected, gracefully-handled fetch failure when I intentionally loaded a nonexistent persona ID (UI still showed a clean "Persona not found," so the console error didn't surface to the user as a broken page).
- This session's Browser tool does not capture cross-origin `fetch`/XHR requests in its network-request log (only same-origin/navigation requests) — the real backend calls only became visible via `performance.getEntriesByType('resource')`. Noting this as a tooling limitation for future audits of this app, not a product issue.

## Automated Verification

- **Frontend:** `npx tsc --noEmit` → clean, 0 errors. `npx jest` → **8 suites / 48 tests, all passing.** `npx next build` → succeeds; 13 routes built; only warnings were `metadataBase not set` (the direct cause of the P2 OG-image bug — not benign in hindsight) and an outdated `caniuse-lite` notice (genuinely benign).
- **Backend:** `python -c "from app.main import app"` → imports cleanly against the real model layer. `pytest tests/` → **499 passed, 30 failed, 17 errored, 23 warnings** (all warnings are Pydantic v2 deprecation notices, benign). All failures/errors root-caused to pre-existing auth-retrofit test rot (see P2). `pytest` from the backend root (no path) → collection-level failure, see P2.
- `/health` on the live backend → `200 {"status": "healthy"}`.

## Known Limitations

- Backend production commit was not cryptographically confirmed against `origin/main` (no Railway API access this session) — inferred from behavior, not proven by hash. See Phase 0 note above.
- Only one anonymous identity was available in this session, so cross-*account* IDOR was verified by source-code review + unauthenticated `curl` (which is actually the stronger test — it shows the check is missing entirely, not just misconfigured for a second account) rather than by a live two-account browser test.
- Did not complete a full two-snapshot Compare-page UI diff (verified the underlying snapshot data directly instead).
- Did not test AI-provider failure/timeout/malformed-output handling, prompt-injection-from-stored-experience-text, double-submit races, or refresh-mid-analysis — flagged as untested, not passed, per the audit's own instruction not to guess.
- Did not exercise `templates`/`Remix with template` flows beyond confirming the route loads.
- Performance was observed qualitatively only (experience analysis ~5s, narrative generation ~20s, chat ~5s — all felt appropriate for the AI calls involved), not benchmarked under load.

## QA Artifacts Created

Both live under one **anonymous/guest** Firebase session that was never converted to a real account ("Save your work" was never clicked), so this data will not survive if that guest session/browser storage is ever cleared. If you want it gone sooner:

- **ZZ_QA_AUDIT_Person1** — id `7c37e00e-a83b-416c-9760-ae58c767590c` — 2 experiences, 1 saved snapshot (`cdddb6b8-dd87-40f9-8076-278002acb77f`, labeled "After betrayal experience")
- **ZZ_QA_AUDIT_Person2** — id `e7370441-a1c5-4f90-9d66-7fc763ee35ef` — 0 experiences

Delete via "Delete this life" on each persona's hub if you'd rather not wait for the guest session to lapse on its own.

## Deferred Work

P0-1, P0-2, and P1 are corrected as of this update — see the closeout sections below. Not approved this pass, still deferred:

1. Set `metadataBase` in `layout.tsx` (P2, five-minute fix).
2. Rate limiting / abuse hardening on AI-cost-bearing endpoints (P2).
3. `test_psychology_engine.py`'s 5 failures (signature drift against a retired `analyze_experience()` call shape), `test_api_experiences.py`/`test_api_interventions.py`/`test_api_timeline.py`'s remaining failures/errors (mocking a function name — `analyze_experience`/`analyze_intervention` — retired from those route modules by an earlier, unrelated migration), and `test_api_personas.py`'s 3 baseline-personality exact-value mismatches. All pre-existing, confirmed via `git stash` against `origin/main` before this pass touched anything, explicitly out of scope per this round's instruction not to perform broad unrelated test cleanup. Full breakdown in the Auth Retrofit Regression Coverage section below.
4. Scope CI's pytest invocation to `tests/` explicitly, or move/rename the root-level `test_*_manual.py` scripts so default discovery doesn't catch them (P2).
5. Clean up the three dead Settings fields, or wire them up if they were meant to do something (P2).

---

## P0/P1 Corrections — Closeout

Corrections implemented on branch `fix/p0-idor-and-model-evolution`, commit `cfb129131faa8e77957ac523024353f6f52d1084`, opened as [PR #7](https://github.com/blackulaphoto/Persona-emulator-/pull/7) against `main`. **Not yet merged** — merging is outside this session's tool access (blocked at the harness permission layer, confirmed by attempting it), so PR #7 needs a human merge before the corrected code reaches production. CI on the PR (GitGuardian secret scan, Vercel preview build) is green; there is no backend CI configured in this repo (confirmed during the audit - no GitHub Actions workflows exist), so the backend verification below is this session's direct local run, not a CI gate.

### P0-1 — Unauthenticated IDOR

- **Root cause:** `backend/app/api/routes/timeline.py`'s single route and all 7 routes in `backend/app/api/routes/remix.py` had no `Depends(get_current_user)` and no `Persona.user_id` filter at all - the only gate on `remix.py` was a feature flag, not identity. Every other persona-scoped route file already did this correctly.
- **Fix:** Added `user_id: str = Depends(get_current_user)` to all 8 routes. `timeline.py` now filters `Persona.id == persona_id, Persona.user_id == user_id`, identical to the pattern already used in `experiences.py`/`interventions.py`/`personas.py`. `remix.py` gained two small helpers - `_require_owned_persona` and `_require_owned_snapshot` (the latter joins `TimelineSnapshot.persona_id -> Persona.user_id`, since a snapshot ID alone was never sufficient to authorize anything) - called at the top of every endpoint before it touches the service layer. No second authorization system invented; both helpers are the same `Persona.user_id == user_id` check used everywhere else.
- **Nested-resource gap found while testing:** `get_intervention_impact` took a `persona_id` and a `baseline_snapshot_id` independently, checked each was owned by the caller, but never checked the snapshot actually belonged to *that* persona - a user could pass one of their own persona's IDs alongside a snapshot from a *different* persona they also own, and it would silently compute nonsense across the two. Not a cross-user leak (still gated on the caller owning both), but a real nested-resource-consistency bug matching the audit's own "whether nested resources inherit ownership safely" concern. Fixed: the route now checks `baseline_snapshot.persona_id == persona_id` explicitly. Caught by `test_intervention_impact_denied_when_snapshot_belongs_to_a_different_persona`.
- **Tests:** `backend/tests/test_timeline_remix_security.py`, 27 tests, all passing. Direct-function-call layer (matching this repo's own established convention in `test_personas_route_wiring.py`) proves: owner-allowed, cross-user-denied, nonexistent-ID-fails-safely, cross-user and missing-persona return byte-identical rejection bodies (no existence leak), delete-denied-leaves-the-snapshot-intact, compare-denied-if-either-snapshot-not-owned, compare-allowed-across-two-of-the-*same*-user's-personas (ownership is the boundary, not same-persona-ness), intervention-impact-denied-for-a-mismatched-nested-snapshot. A separate small HTTP-layer class proves the wire-level rejection specifically: a request with no `Authorization` header at all is rejected by FastAPI's own `HTTPBearer` dependency before any route body runs, for every one of the 8 routes.
- **Live production retest:** **BLOCKED pending merge.** PR #7 is not yet in `main`; Railway (the backend host) deploys from `main`, so the fix is not live yet. See "Production Security Re-Test" below.

### P0-2 — Positive/reparative experiences never reached the developmental model

- **Root cause:** `developmental_pipeline.py` only built an `Interpretation` row - and therefore only ever ran `propose_state_trait_implications_async`/applied any `current_state`/`current_personality`/`current_attachment_dimensions` movement - when `this_batch_exposures` was non-empty. `developmental_exposure_engine.py`'s `EXPOSURE_TAXONOMY` is exhaustively adverse-event-only (caregiver substance use, abandonment, abuse, neglect, violence, divorce, death, ...) with no positive/growth category. A reparative event correctly matched a `PROTECTIVE_FACTOR_TAXONOMY` entry but that classification was a dead end: nothing downstream ever consumed it. Separately, `propose_state_trait_implications_ai`/`_heuristic` had their own independent gate on `adaptation_strategy`, which would have blocked State movement even if an interpretation existed.
- **Developmental-significance architecture:** Rather than treat "positive" as a special-cased bolt-on, the fix generalizes the existing exposure/protective-factor split that was already in the codebase. `pattern_engine.py` gained `interpret_reparative_experience_async` (and its AI + heuristic sub-paths, mirroring the existing adverse path's shape exactly), dispatched from a single entry point (`interpret_experience_async`) that now branches on **what's actually present**, not on adversity specifically: exposures present -> adverse path (unchanged); no exposures but a protective/reparative factor from this batch -> reparative path; neither -> genuinely un-analyzed (extraction found nothing recognizable, not a taxonomy blind spot - this is the one legitimate "stays as before" case). `developmental_pipeline.py`'s gate changed from `if this_batch_exposures:` to `if this_batch_exposures or this_batch_protective:`.
- **Positive/reparative support:** Added one new protective-factor taxonomy entry, `corrective_emotional_experience` (trust repair, reconciliation, a conflict actually resolved - "repaired the relationship", "trusted them again", "stayed instead of leaving", etc.), deliberately tagged with the `attachment_security` domain so it also engages the *already-existing* `attachment_engine.apply_attachment_protection` (which runs unconditionally, independent of the interpretation gate, and previously did nothing for a repair event because `friendship`/other close-relationship factors aren't tagged `attachment_security`). The existing `mastery_experience`, `reliable_close_relationship`, `stable_alternate_caregiver`, and `sustained`-support-flavored entries already covered achievement/support reasonably well and needed no changes. `interpret_reparative_experience_async` **deliberately never sets `adaptation_strategy`** - a repair isn't a new coping strategy, and leaving it unset is what (a) keeps `accumulate_patterns()` from opening a spurious "positive pattern" bucket, and (b) is exactly the condition `attachment_engine.apply_attachment_update` already checks to distinguish a genuine attachment-security gain from a coping strategy's incidental state-variable side effect (e.g. `people_pleasing` also raises `relational_security` in the heuristic defaults, but that isn't becoming more securely attached).
- **Analyzed-no-change behavior:** State/Trait movement was relaxed from gating on `adaptation_strategy` to gating on `belief_statement` - any real interpretation, adverse or reparative, is now entitled to propose State movement; Trait movement stays exactly as conservative as before (`trait_gate_open` still requires `status == "established"`, which only ever comes from `accumulate_patterns()` grouping by `adaptation_strategy` - a reparative interpretation can only ever earn the small provisional Trait nudge, never a full established-pattern move). A genuinely trivial positive event (case 5: "a pleasant lunch") still produces no exposure and no protective factor at extraction time, so it correctly stays un-interpreted with no forced model mutation - proven by `test_case5_developmentally_trivial_positive_event_is_not_forced_into_significance`, which asserts `current_state`/`current_personality` are byte-identical before and after. Frontend: the "Not yet analyzed" label in `app/persona/[id]/timeline/page.tsx` now only renders when there's truly nothing (no interpretation, no pattern/hypothesis connection, *and* no protective factor) - a repaired-trust experience no longer hits it, and the honest remaining case reads "Analyzed — nothing developmentally significant identified in this moment" rather than implying the analysis hasn't happened yet.
- **Snapshot impact:** Not separately modified - `TimelineSnapshot`/`PersonalitySnapshot` capture whatever `current_state`/`current_personality`/`current_attachment_dimensions` hold at save time, which now correctly includes reparative movement. No snapshot-schema changes were needed.
- **Section 11's contradictory-evidence requirement** ("a repair should be able to weaken an existing adverse pattern, not just create a separate happy pattern while the old model stays untouched") required **no new code at all** - `pattern_engine.accumulate_patterns()` already checked every `ProtectiveFactor` (regardless of whether it came with an `Interpretation`) against later same-strategy reinforcements, marking the reinforcement `"weakened"` instead of `"strengthened"` when domains overlap and the factor isn't self-sourced from that same pattern's own events. Since `ProtectiveFactor` rows are persisted unconditionally (always were, independent of the interpretation gate), this mechanism just needed the reparative event to exist as a real, analyzed thing for the effect to be visible end-to-end - proven by `test_reparative_evidence_weakens_a_later_reinforcement_of_the_adverse_pattern_it_contradicts`, which runs a real adverse event, a real repair, then a second real adverse event of the same strategy/domain through the actual pipeline and confirms the third event registers as `"weakened"`, not `"strengthened"`.
- **Tests:** All 5 required cases from the audit brief, plus the weakening scenario, in `backend/tests/test_developmental_pipeline.py::TestPositiveAndReparativeExperiencesAreAnalyzed` (6 tests, run end-to-end through `process_developmental_text` with every AI call mocked to fail - deterministic keyword-extraction + heuristic-interpretation fallback path, the same harness this file already used for its adverse-path tests). Plus unit-level dispatch/validation/taxonomy tests in `test_pattern_engine.py`, `test_state_trait_engine.py`, and `test_developmental_exposure_engine.py`.
- **Live production retest:** **BLOCKED pending merge.** See "Human Model Evolution Re-Test" below.

### P1 — Generated reasoning invents events that never occurred

- **Root cause:** `pattern_engine._build_interpretation_prompt` gave the model exposures, protective factors, and prior patterns as context, and asked for a `reasoning` field, but never explicitly forbade drawing on anything else. Confirmed in the original audit: for a betrayal experience with protective factors explicitly listed as `(none active)`, the generated reasoning still said "the presence of reliable close relationships and explicit reassurance likely buffered these effects" - describing circumstances that were the literal opposite of the input and were explicitly marked absent in the same prompt.
- **Evidence-grounding strategy:** Added a numbered `GROUNDING RULE (STRICT)` instruction to the adverse-interpretation prompt, and the same instruction (adapted) to the new reparative-interpretation prompt: reasoning may reference *only* what's explicitly listed in the prompt; when a section says "(none active)"/"(none available)", the reasoning must not describe that kind of circumstance as present; express uncertainty directly rather than filling gaps with an invented fact. Also strengthened both `system_message`s with an explicit "never invent a concrete event... that was not given to you in the prompt" instruction. Did not adopt the full structured-output/`source_experience_ids`-validation approach from the audit brief's section 20 - the prompt-level fix directly addresses the confirmed failure mode (inventing circumstances, not misattributing which real experience something came from), and building a second validation layer around it would have been the "enormous schema framework" the brief explicitly said not to build. If a future audit finds *misattributed* evidence (reasoning correctly avoids invention but cites the wrong real experience), that would be the trigger to revisit this.
- **Tests:** `TestGroundingInstructionPresent` in `test_pattern_engine.py` - a deliberately narrow, deterministic proxy confirming both prompts carry the instruction. This cannot prove the model obeys it on every call; that's what the live retest below is for.
- **Live production retest:** **BLOCKED pending merge.** See "Reasoning Grounding Re-Test" below.

## Auth Retrofit Regression Coverage

**Before this pass (pristine `origin/main`, commit `993a44c`):** 499 passed, 30 failed, 17 errored.

**After this pass:** 564 passed, 15 failed, 17 errored.

Fixed (15 of the original 30): every test in `test_api_personas.py`, `test_api_experiences.py`, and `test_api_timeline.py` that failed with a bare `401`/`403` or a `KeyError: 'id'` (from trying to read a persona that a 401'd create request never actually returned) - these were purely blocked by the routes now correctly requiring auth, with no other defect underneath. Fixed via `app.dependency_overrides[get_current_user] = lambda: "test-user-1"`, the standard FastAPI testing pattern - the same mechanism these files already used for `get_db`. This was **not** the first thing tried: this repo's `tests/conftest.py` sets `AUTH_DEV_BYPASS=true` specifically so route-level `TestClient` tests keep authenticating as a fixed dev user without needing this, but empirically (verified directly, both via a standalone script and a real pytest run) it doesn't actually activate in this environment - `app/core/auth.py`'s `load_dotenv()` re-populates `FIREBASE_AUTH_EMULATOR_HOST` from `backend/.env` after `conftest.py` deliberately clears it, so `firebase_admin` ends up configured against the (not actually running, in this session) Auth Emulator instead of running unconfigured, and the bypass's own gate (`compute_dev_bypass_enabled`) correctly refuses to activate once Firebase looks "configured". This is a real, pre-existing gap in the test infrastructure's own bypass mechanism, not something this pass's changes caused - flagging it here rather than silently routing around it. The dependency-override fix sidesteps it entirely and is deterministic regardless.

One test (`test_timeline_replay.py::test_timeline_orders_same_age_experiences_and_reuses_persona_projection`) broke as a direct, mechanical consequence of the P0-1 fix: it called `get_persona_timeline("p", db)` positionally, and inserting `user_id` as the new second parameter silently rebound `db` into that slot. Fixed by passing both as keywords.

**Not fixed - confirmed pre-existing via `git stash` against `origin/main` before this pass touched anything, explicitly out of scope per this round's instruction not to perform broad unrelated test cleanup:**

| File | Count | Root cause |
|---|---|---|
| `test_psychology_engine.py` | 5 failed | `analyze_experience()`'s current signature no longer accepts the `persona=`/`previous_experiences=` keywords these tests pass - unrelated to auth, unrelated to anything touched this pass. |
| `test_api_experiences.py` | 6 failed | `with patch('app.api.routes.experiences.analyze_experience', ...)` - that name was removed from the module by an earlier, already-committed, and explicitly documented change ("Step 11d retired psychology_engine.analyze_experience()'s old, ungated, independent per-experience GPT call" - see the comment already in `experiences.py`). The mock target doesn't exist; unmasked by the auth fix, not caused by it. |
| `test_api_experiences.py` | 1 failed | `test_add_experience_invalid_age` expects `age_at_event < baseline_age` to 400; the route currently accepts it (201). A real, separate, pre-existing validation gap - confirmed present on pristine `origin/main` too (previously masked as a `KeyError` from the unauthenticated create). |
| `test_api_personas.py` | 3 failed | Exact-value assertions on `derive_foundational_baseline_async`'s environment-bias output (e.g. expects `openness == 0.52`, gets `0.7`) - a baseline-personality-computation/expectation mismatch unrelated to auth or model evolution. |
| `test_api_interventions.py` | 9 errored | Same root cause as the `test_api_experiences.py` `AttributeError`s, for `analyze_intervention`. |
| `test_api_timeline.py` | 8 errored | Its `persona_with_timeline` fixture patches both of the above retired names to build its test data; fails before any timeline-specific assertion runs. |

None of these 32 are security- or model-evolution-relevant; all predate this session's work. Fixing them would mean rewriting AI-mocking strategy to target the current pipeline, debugging baseline-personality math, and reconciling `analyze_experience()`'s current vs. expected signature - real work, but a different, unrelated undertaking from what was approved this round.

## Deployment Confirmation

- **Merged commit:** `888a215969be9d0c3f9366799be9cb7200fe4f52` ("Merge pull request #7 from blackulaphoto/fix/p0-idor-and-model-evolution"), on `origin/main`.
- **Vercel (frontend):** confirmed via the Vercel API - latest `target: production`, `state: READY` deployment (`dpl_4C4tv525Be4yf7QVvGXot31X1SyJ`) has `githubCommitSha: 888a215969be9d0c3f9366799be9cb7200fe4f52`, `githubCommitRef: main`, `githubCommitVerification: verified`. Matches the merge commit exactly.
- **Railway (backend):** no API/CLI access in this session (same limitation noted in the original audit), so confirmed **behaviorally** instead, which is the more direct proof anyway: `GET /health` returns `{"status":"healthy"}`, and an unauthenticated request against the exact previously-exploitable production URLs (real QA persona/snapshot IDs from the original audit) now returns `{"detail":"Not authenticated"}` instead of the full data dump the original audit captured. The fix is live.

## Production Security Re-Test

**Live production, both directions, real distinct anonymous accounts.** All checks below ran against `https://persona-emulator-production.up.railway.app` after confirming the merged commit was deployed.

**No-auth denied (bare requests, zero credentials):**

| Check | Result |
|---|---|
| Timeline, real QA persona ID from the original audit | `{"detail":"Not authenticated"}` |
| Remix list-snapshots, same persona ID | `{"detail":"Not authenticated"}` |
| Remix get-snapshot, real QA snapshot ID from the original audit | `{"detail":"Not authenticated"}` |
| Remix delete-snapshot, same snapshot ID | `{"detail":"Not authenticated"}` |

These are the exact same URLs the original audit hit with a bare `curl` and got full psychological data back. Now: nothing.

**Cross-account, using real captured Firebase ID tokens for genuinely distinct anonymous accounts** (created fresh for this retest - see QA Cleanup below for IDs):

| Check | Result |
|---|---|
| Session C -> own persona timeline | `200` |
| Session C -> Session B's persona timeline (cross) | `404` |
| Session C -> Session B's snapshot (cross) | `404` |
| Session D -> own persona timeline | `200` |
| Session D -> Session C's persona timeline (cross) | `404` |
| Session D -> Session C's snapshot (cross) | `404` |
| Session D -> delete Session C's snapshot (cross) | `404` (confirmed the snapshot was never touched - the ownership check in `_require_owned_snapshot` raises before `delete_snapshot()` is ever called, so a 404 here is proof the delete didn't execute, not just that a later read failed) |
| **Session D's own persona + Session C's snapshot as the `baseline_snapshot_id` for `intervention-impact`** (the exact nested-ownership gap found and fixed during this pass's testing) | `404` |

Also reproduced live via the actual UI, not just the API: while authenticated as Session D, navigating directly to Session C's `/persona/{id}/talk` produces a clean "Couldn't load this life" / "Retry" screen - no crash, no data, no raw error.

Every one of section 3's required checks passes, including the one bug this pass's own testing found and fixed (the nested intervention-impact gap) - confirmed closed live, not just in the unit test that caught it.

## Human Model Evolution Re-Test

Fresh QA persona `ZZ_RETEST_SessionD` (neutral baseline - no backstory signal, Big Five started at flat 50/50/50/50/50, attachment Secure), five experiences added in production, using the **real deployed AI pipeline** (not a mocked/fallback path - this is GPT-4o's actual live classification and reasoning).

| Age | Experience | Result |
|---|---|---|
| 25 | Betrayal - a close coworker spread a humiliating rumor | **Regression check, still works:** attachment flipped Secure -> Anxious, Big Five nudged (extraversion 49%, neuroticism 51%), four `current_state` dimensions appeared (Trust: Guarded, Threat Sensitivity: On alert, Avoidance: Pulling away, Relational Security: Unsure), new adaptation pattern "Invisible Shield" (avoidance) opened as `emerging`. |
| 26 | Trust repair - the same coworker took responsibility and repaired the relationship | **The headline fix, confirmed live:** `interpretation` is non-null with a real belief statement ("A genuinely positive moment, but not yet enough on its own to shift an established pattern."), tagged `PROTECTIVE FACTORS: Corrective Emotional Experience` - the new taxonomy entry, correctly classified by the real model. Attachment flipped back **Anxious -> Secure**. Two of the four flagged `current_state` dimensions (Trust, Relational Security) cleared. The experience detail drawer shows "BELIEF FORMED" with real content - **no "Not yet analyzed" anywhere.** |
| 27 | Achievement - promoted to lead a project, publicly credited | Analyzed, tagged `PROTECTIVE FACTORS: Mastery Experience`, real belief statement, **no forced pathology framing** (no adaptation_strategy, not folded into the avoidance pattern). |
| 27 | Developmentally trivial - coffee and small talk about a TV show | **Correctly produced zero model change** - Big Five and `current_state` identical to the prior step, no new pattern. Detail drawer honestly reads: *"Analyzed — nothing developmentally significant identified in this moment."* - not "Not yet analyzed", not a fabricated significance. |
| 28 | A second, different coworker's betrayal (same domain as age 25, to test the weakening mechanism) | **Section 11's contradictory-evidence requirement, confirmed live with real data:** raw API shows `"Invisible Shield"` pattern's second reinforcement recorded as `"effect": "weakened"` (not `"strengthened"`), `status: "resolved"`, `evidence_strength: 0`. The generated reasoning explicitly and correctly says why: *"The presence of protective factors such as corrective emotional experience and mastery experience may have softened the impact..."* - citing the real age-26 and age-27 events by their real classification, not inventing anything. |

**Persistence:** full page reload (fresh navigation, not a client-side transition) after all five experiences showed identical state to what the API returned - 5 experiences, "Fearful-avoidant" attachment (correctly re-degraded by the second betrayal), pattern status "resolved 0%", all `current_state` dimensions matching. **Snapshots:** created one (`Retest checkpoint`) after all five experiences via the UI; its existence and readability were independently confirmed through the security re-test above (its `personality_snapshot`/`state_profile_snapshot`/`adaptation_patterns_snapshot` fields captured the post-fix state, since snapshot creation reads directly from `Persona.current_*` at save time - no separate snapshot-layer change was needed or made).

Every item on section 4's checklist is confirmed: adverse events still analyze, trust repair analyzes and is never null, reparative evidence weakens a contradicting pattern where the evidence actually supports it (and does *not* touch it where the audit's own guardrail says it shouldn't - the achievement event correctly stayed out of the avoidance pattern entirely), achievement/support is eligible for analysis, a genuinely trivial positive event honestly produces no change, the UI never incorrectly says "Not yet analyzed" for anything that was actually analyzed, and persistence/reload/snapshots stayed coherent throughout.

**One quality observation, not a regression:** the age-26 and age-27 belief statements came back as the *exact same sentence*, word for word - which is also the literal example phrase given inside the reparative prompt's own instructions. That's a real signal the model may be anchoring on the example rather than always generating bespoke text for lower-stakes reparative events. It's not a grounding violation (nothing false, nothing invented) and didn't block anything - the age-28 reasoning, by contrast, was fully specific and correctly cited real prior events - but it's worth a future prompt-wording pass if this product wants every reparative belief statement to read as distinctly as the adverse ones do. Not fixed in this pass; flagging per "no hidden findings," not proposing new scope.

## Reasoning Grounding Re-Test

QA persona `ZZ_RETEST_SessionD`, exactly 5 known events (table above), real production AI. Every interpretation's `reasoning` text inspected against that exact history:

| Age | Concrete claims in the reasoning | Grounded? |
|---|---|---|
| 25 | References "emotional abuse or humiliation" and "peer rejection or bullying" - the taxonomy classification of the one given event, not a second event. | ✅ Yes |
| 26 | Generic ("a genuinely positive moment... not yet enough to shift an established pattern") - references nothing beyond the repair itself. | ✅ Yes |
| 27 | Same generic phrasing - references nothing beyond the achievement itself. | ✅ Yes |
| 27 (trivial) | No interpretation generated (correctly - see Case 5 above). | N/A |
| 28 | Explicitly names **"corrective emotional experience and mastery experience"** as the reason the impact was softened - these are the real, correctly-classified protective factors from the real age-26 and age-27 events. | ✅ Yes - and notably the *best* example: specific, correctly attributed, not generic. |

**Zero invented concrete events across all five.** No childhood detail, no caregiver, no relationship, no circumstance appeared anywhere that wasn't in the actual stored history - a direct contrast with the original audit's finding, where the pre-fix reasoning invented "reliable close relationships and explicit reassurance" for a betrayal experience that had neither. Numeric/model deltas matched what the reasoning described in every case (state/attachment moved the direction the belief statement implied). Every belief statement was phrased as inference ("plausibly holds a belief that...") rather than stated fact, consistent with the epistemic-honesty behavior the original audit found already-working in narrative/Talk.

**P1 is closed**, verified against real model output in production, not just the prompt-content proxy test from the code-review pass.

## Talk Regression

Persona `ZZ_RETEST_SessionD`, real production chat:

- **Correct persona context, reparative event available:** asked "How do you feel about trusting people at work these days?" - answer referenced both the betrayal *and* the repair/support ("After having confided in someone and then finding out they gossiped about it, I've been more cautious... I still enjoy working with my team, especially after the project where they really supported me.").
- **Nonexistent event refused:** asked about "the time you moved abroad for six years to care for your sick grandmother" (never happened) - refused cleanly: *"I think you might have me mixed up with someone else. I haven't moved abroad for an extended period..."* No fabrication.
- **No cross-person leakage:** while still authenticated as Session D, navigated directly to a different account's persona's `/talk` URL - got the app's clean "Couldn't load this life" / "Retry" state, not another person's data and not a crash. (Same-account person-to-person Talk isolation was already thoroughly verified in the original audit with two deliberately-contrasting QA people; not re-run in full here since neither this pass's changes nor anything found during it touched that code path.)

No regressions. Talk still behaves exactly as the original audit found it: honest about what it is, grounded, refuses to invent.

## QA Cleanup

Four QA identities were created for this retest (fresh anonymous accounts, needed to get genuinely distinct users for the cross-account security checks):

| Session | Persona name | Persona ID | Status |
|---|---|---|---|
| A | `ZZ_RETEST_SessionA` | `8d808ddb-61dc-4e69-ab15-03147c0b7d2b` | Superseded early when this account's Firebase ID token expired mid-retest; not otherwise used. **Not deleted** - this session no longer has valid credentials for that anonymous account (its browser storage was intentionally cleared to create the next test identity, and Firebase anonymous auth has no way to re-authenticate as a specific existing anonymous UID without its original local refresh token). |
| B | `ZZ_RETEST_SessionB` | `3b3d1bbf-1fc3-48c7-bb3b-92bac0d70aff` | Used as the cross-access target for Session C's checks. **Not deleted**, same reason as A. |
| C | `ZZ_RETEST_SessionC` | `93027f99-dee7-4cc5-b58c-a8dd36ca6abc` | Used as the cross-access target for Session D's checks, including the nested intervention-impact check. **Not deleted**, same reason. |
| D | `ZZ_RETEST_SessionD` | `f0c25519-b83e-45e5-85f5-4874315f059a` | Used for the full model-evolution/reasoning/Talk retest. **Deleted** via the app's own "Delete this life" while still authenticated as its owner - confirmed via redirect to an empty "No lives yet" Lives screen. |

Personas A, B, and C are all anonymous-guest-only data (never converted to a real account via "Save your work") and are now unreachable by anyone without their specific browser's original local storage - they pose no real cleanup risk. The app has no admin path for reaching an arbitrary anonymous account's data (correctly, per the P0-1 fix), so the only way to remove these three rows if you want them gone is a one-off query against the `personas` table for the three IDs above; otherwise they're safe to leave as harmless orphaned rows.

The original audit's QA artifacts, `ZZ_QA_AUDIT_Person1` and `ZZ_QA_AUDIT_Person2`, were checked at the start of this retest: the guest account that created them (same Firebase UID, confirmed by decoding a freshly-captured token) now shows "No lives yet" - they're already gone. Not investigated further (out of scope for this pass); flagging rather than assuming.

## Final Recommendation

# READY

All three approved corrections are merged, deployed, and verified against live production with real accounts and the real AI pipeline - not just code review, not just unit tests:

- **P0-1** (unauthenticated IDOR): closed. Every previously-exploitable URL now rejects unauthenticated requests, ownership is enforced in both directions across genuinely distinct accounts, and the one gap this pass's own testing surfaced (nested intervention-impact) is confirmed fixed live, not just in a unit test.
- **P0-2** (positive experiences don't evolve the model): closed. A trust-repair experience now produces a real, non-null interpretation with visible, correctly-directed consequences (attachment flipping back to Secure, flagged state dimensions clearing), a later contradicting pattern reinforcement really does register as "weakened" instead of "strengthened," genuinely trivial events honestly produce no change instead of a fabricated one, and the misleading "Not yet analyzed" label is gone for anything that was actually analyzed.
- **P1** (reasoning hallucination): closed. Five real, live-generated interpretations were checked against the QA persona's exact known history with zero invented events - including one example that explicitly and correctly cited real prior evidence by name.

Talk, narrative, and person isolation - already working in the original audit - show no regressions.

**Deferred, not blocking:** the P2/P3 findings from the original audit (broken OG-image `metadataBase`, no rate limiting, three dead Settings fields, CI pytest-discovery hazard) and the 15 failed / 17 errored backend tests confirmed pre-existing and unrelated to this pass (retired-function references from an earlier migration, stale exact-value assertions, one separate real-but-unrelated age-validation gap - full breakdown in "Auth Retrofit Regression Coverage" above). None of these touch security, data integrity, or the core model-evolution promise. One new, non-blocking quality observation surfaced during this retest: the reparative-interpretation prompt's example phrase gets echoed verbatim often enough to be worth a future wording pass.

Rubix does what it now claims to do, for real users, in production, right now.
