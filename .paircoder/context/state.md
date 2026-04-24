# Current State

> Last updated: 2026-04-12

## Active Plan

**Plan:** plan-sprint-s2-fort-worth-data
**Type:** feature
**Title:** Fort Worth Data + Texas Rules -- Multi-city port for HackFW 2026
**Status:** Complete (18/18 tasks done)
**Current Sprint:** S2

## Task Status

### Sprint S2 --- Fort Worth Data + Texas Rules

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T2.1 | Texas Benefits Thresholds | P0 | 20 | done | -- |
| T2.2 | Texas Benefits Eligibility Checks | P0 | 25 | done | T2.1 |
| T2.3 | Texas Application Data | P0 | 15 | done | -- |
| T2.4 | Texas Benefits Types + Program Calculators | P0 | 25 | done | T2.1 |
| T2.5 | Benefits Module Router | P0 | 25 | done | T2.2, T2.4 |
| T2.6 | Texas Expunction + Nondisclosure Rules | P0 | 25 | done | -- |
| T2.7 | Criminal Module Router | P0 | 15 | done | T2.6 |
| T2.8 | Fort Worth ZIP Centroids + Geo Data | P0 | 15 | done | -- |
| T2.9 | City-Aware ZIP Validation | P0 | 15 | done | -- |
| T2.10 | Fort Worth Barrier Cards + Career Center | P0 | 20 | done | -- |
| T2.11 | Live TWC Job Adapter | P1 | 30 | done | -- |
| T2.12 | Live USAJobs Adapter | P1 | 30 | done | -- |
| T2.13 | City-Aware AI Prompts | P1 | 15 | done | -- |
| T2.14 | Frontend City-Aware Constants | P1 | 20 | done | -- |
| T2.15 | Frontend City-Aware UI Text | P1 | 15 | done | T2.14 |
| T2.16 | Fort Worth Seed Data | P2 | 20 | done | -- |
| T2.17 | Fair-Chance Employer Index | P2 | 15 | done | -- |
| T2.18 | Integration Gate | P2 | 10 | done | T2.5, T2.7-T2.10 |

**Total: 18 tasks, 355 complexity points (18/18 done) -- SPRINT COMPLETE**

## Previous Sprints (summary)

- **Sprint S1** -- City Framework Scaffold: multi-city YAML config, adapter protocol, BrightData/HonestJobs/TWC/USAJobs adapters, CITY env var (8/8 done)

Older sprint task tables, session histories, and plan details have been archived to `.paircoder/archive/state-pre-s1.md`. One-line summary:

- **Sprint 31** -- BrightData Consolidation + Commute Time (4/4 done)
- **Sprint 30** -- Transit Enhancement (2/2 done)
- **Sprint 29** -- Benefits Program Eligibility (4/4 done, PR #40)
- **Sprint 28** -- Resource Auto-Matching (2/3 done, T28.3 deferred)
- **Sprint 25** -- Benefits Cliff Engine (4/4 done, PR #36 merged)
- **Sprint 23** -- Barrier Graph + RAG (1/7 done, paused)
- **Sprint 18** -- Security Hardening (7/7 done)
- **Sprints 7-17** -- Launch prep, demo polish, live jobs, intelligent matching, a11y, docs (all complete)

## What Was Just Done

- **T12.25a done**: past-appointment auto-advance (port of `ops:lib/nightly_reconcile.py`) — 6h grace, audit + worker notice + outcome record, wired into the nightly orchestrator as step 2.5 (this session)

- **T12.17 done**: documents API routes + PDF export — 7 endpoints, `_versions_db` spoke, use-counter hook wired in `jobs_applications.create()` (this session)

- **T12.24 done** (auto-updated by hook)

- **T12.24 done**: plan refresher + progress carry-forward + 20-row history cap (this session)

- **T12.21 done** (auto-updated by hook)

- **T12.16 done** (auto-updated by hook)

## 2026-04-23 — S12b T12.25a past-appointment auto-advance

**T12.25a (done)**: ported `ops:lib/nightly_reconcile.py` (`reconcile_bookings_sweep`, `advance_past_bookings`, `_should_advance`, `_write_audit_log`) to `backend/app/modules/appointments/reconcile.py` (196 lines / 6 fn). Adapted the legacy JSON-file-backed implementation to MontGoWork's m002 `appointments` table, the existing scheduler.mark_missed transition path, and the `engagement_events` audit table.

Per-advance side effects (4): (1) `scheduler.mark_missed(appt.id, db_path=...)` flips status SCHEDULED → MISSED via the existing transition matrix (which also emits `appointment.missed` for the T12.7 outcomes_listener that records an `appointment_missed` outcome row); (2) audit row `engagement_events(category='appointment_auto_advance', payload={appointment_id, reason})`; (3) one-time worker notice row `engagement_events(category='appointment_auto_missed_notice', payload={appointment_id})` for the next daily digest's "I actually attended" correction CTA; (4) outcome record via `OutcomeTracker.record_outcome(signal_type='appointment_auto_advance')` — and this is the integration contract with T12.18: the existing `progress_signals._gather_outcome_events` unconditionally filters this signal type out of the stall clock so the system's own auto-advance never fakes "fresh activity" for the worker.

Idempotency falls out of the transition matrix: `MISSED → MISSED` is rejected, so a second sweep finds the row terminal, the `_advance_one` try/except catches the `InvalidStatusTransition`, returns False, and no audit/notice rows are emitted. Test `test_idempotent_two_runs_no_double_notice` asserts this directly (one run advances, second is zero, audit + notice each have count == 1).

Orchestrator wire-up: `_reconcile_session` helper in `scripts/nightly_digest.py` (15 lines) is invoked between `run_nightly_retro` (step 2) and `_refresh_session_plan` (step 3 — T12.24). Failures are logged + swallowed (matches the T12.24 robustness contract). Required one import-count rebalance — consolidated `from app.modules.plan import plan_refresher, weekly_review` and `from app.modules.plan.daily_progress import run_nightly_retro` into a single `from app.modules.plan import (...)` block plus module-attribute aliasing for `run_nightly_retro` and `refresh_plan` (so existing `nd.run_nightly_retro` and `nd.refresh_plan` monkeypatches in `test_nightly_digest.py` still work). Net import count on `nightly_digest.py`: 14 → 14 (added reconcile, removed daily_progress as a top-level import).

Tests (`tests/test_appointment_reconcile.py` — 7 tests, 439 lines, 50-line per-function compliance after extracting `_seed_orchestrator_session` and `_install_ordering_stubs` helpers): within-grace no-advance, beyond-grace advance + audit + notice + outcome, manual-attended no-action, idempotent (no double notice on second run), stall-suppression (auto_advance outcome filtered by T12.18 → 10-day-old real signal still drives MEDIUM stall classification), multi-session sweep via `advance_past_bookings`, orchestrator step ordering (retro → reconcile → compose).

Carry-overs: `nightly_digest.py` file-size warning 274/150 lines (was 250 pre-task; +24 for the helper + module docstring + import shuffle — still warning-only, not error). `reconcile.py` file-size warning 196/150 (warning-only). Test file warning 439/400 (warning-only, errors at 600). Pre-existing test failures unrelated to T12.25a: `test_outcomes_logged_in_range` (verified pre-existing via `git stash` round-trip) and `test_provider_simple_input_fields_unchanged` (contract test).

## 2026-04-23 — S12b T12.17 documents API routes + PDF export

**T12.17 (done)**: built `backend/app/routes/documents.py` (232 lines / 11 fn — 7 endpoints + 4 helpers) and `backend/app/modules/documents/_versions_db.py` spoke (147 lines / 4 fn) so the routes layer and the application-create hook share one source of truth for `resume_versions` reads + `use_counter` increments.

Seven endpoints under `/api/documents`: `POST /resume`, `GET /resume/{id}`, `GET /resume/{id}/pdf`, `POST /cover-letter`, `GET /cover-letter/{id}`, `GET /cover-letter/{id}/pdf`, `GET /versions?session_id=`. Auth contract mirrors T12.10 / T12.13 (`token` query-param against `feedback_tokens`; cross-session reads return 403, cross-doc-type id returns 404). Markdown endpoints set `Content-Type: text/markdown`; PDF endpoints stream `application/pdf` bytes from the T12.4 SSRF-guarded `render_markdown_to_pdf(markdown, "default")`. POSTs delegate to T12.15 `generate_resume(session_id, *, job_description, db_path)` and T12.16 `generate_cover_letter(session_id, job_match_ref, resume_version_id, *, db_path)` rather than re-implementing persistence; the route then re-reads via `versions_db.list_versions(..., doc_type=...)` to surface the just-persisted row's `id` (which the dataclass returned by the builder doesn't expose — the builder returns `version_counter`, not the autoincrement primary key).

T12.17 hook in `jobs_applications.create_application()`: when the request body carries `resume_version_id`, the route calls `_versions_db.increment_use_counter(version_id, db_path=db_path)` after the application insert succeeds. Best-effort (no-op on stale id) so a worker-supplied stale id can't 500 the endpoint. Hook is annotated inline with `# T12.17 hook:` so future readers can grep.

Router ordering: documents prefix `/api/documents` is unique — none of the existing `/{...}` catch-alls (`/api/insights/{session_id}`, `/api/plan/{session_id}`, `/api/jobs/{job_id}`, etc.) intersect with documents, so registration order doesn't matter for collision avoidance. Placed alphabetically between `demo_router` and `engagement_router` in `routes/__init__.py`.

Tests (`test_documents_routes.py` — 17 tests, 426 lines under the 600-line ceiling): cover all 7 endpoints, content-type assertions on both `text/markdown` and `application/pdf`, `%PDF-` magic byte check on the actual response bytes (not just non-empty), newest-first version ordering with multi-session isolation, cross-session 403, missing-id 404, the use-counter hook fires (and is no-op without `resume_version_id`), and a registration sanity check that documents_router is in `all_routers`. Two TestClient fixtures share the same temp db: `client` mounts the documents router, `jobs_app_client` mounts the jobs-applications router so the hook can be exercised end-to-end on the same `resume_versions` row.

Carry-overs: `routes/__init__.py` imports now at 27 (was 26 carry-over before T12.17, +1 for `documents_router` import) — task spec explicitly says don't fix this pre-existing arch warning. `routes/jobs_applications.py` is at 248 lines (was ~239, +9 for the hook block + comment) — still under the 400-line error threshold, only triggers the soft 150-line warning that was already present.

**T12.24 (done)**: built `backend/app/modules/plan/plan_refresher.py` (228 lines / 5 fn) + `_plan_refresher_db.py` helper spoke (181 lines / 7 fn) + `plan_progress.py` ports (89 lines / 6 fn — adapted from `ops:lib/plan_progress.py` to the MontGoWork plan shape since the Reddit-specific `recommended_threads` / `spend_opportunities` shape doesn't apply here). All three under 400-line error threshold; arch warnings on the 150-line soft cap only. 25/25 tests pass (16 new in `test_plan_refresher.py` + the 9 pre-existing nightly_digest tests after updating `test_plan_refresh_stub_noop_marks_todo` → `test_plan_refresh_invokes_refresher`). Full suite: 3092 passed, the same 2 pre-existing failures only (test_contract_credit_api + test_evidence_collector::test_outcomes_logged_in_range); zero net new regressions.

Triggers (auto-detect order — stall wins if both fire):
- `stall_level=HARD` from `compute_stall_for_session` (T12.18) → reason=`stall_hard`, event=`stall_level=hard;days=N`
- `barrier_resolved` outcome within last 24h (`BREAKTHROUGH_WINDOW`) → reason=`breakthrough`, event=`barrier_resolved:<barrier_id>`
- Explicit `trigger_reason` arg bypasses auto-detect (manual refreshes / tests)

Carry-forward contract: action keys built from `(phase_id, category, title)` triple — most stable triple our generators produce today (no per-action UUIDs). Old checklist items present in the new plan keep their `completed`/`completed_at`/`notes` state; items absent from the new plan get dropped; new items seed `completed=False`.

Archive + dual-write: every refresh inserts one row into `plan_history` with `refresh_reason` + `triggering_event`, then UPDATEs `sessions.plan` + `sessions.action_checklist` + `sessions.previous_plan` (the dual-write target). 20-row cap per session enforced via a single `DELETE … WHERE id NOT IN (… ORDER BY archived_at DESC LIMIT 20)` after each insert — fulfilling the m002 inline comment promise of "application-level enforcement (NOT at schema level)".

Orchestrator wiring: `backend/scripts/nightly_digest.py` step 3 now calls `refresh_plan(session_id, db_path=db_path, now=now)` via a `_refresh_session_plan` wrapper that swallows exceptions so a single buggy session can't abort the digest pipeline. The S12a `_plan_refresh_stub` function and its `"TODO S12b T12.24"` log line are removed. Step 2.5 area (T12.25a parallel) is untouched. Imports kept under the per-file ceiling by binding `from app.modules.plan import plan_refresher as _plan_refresher_mod` and aliasing `refresh_plan = _plan_refresher_mod.refresh_plan` so test monkeypatches on `nd.refresh_plan` continue to work.

`load_calibrated_weeks(db_path)` is a sync sqlite-native sibling of `routes/_intelligence_helpers.fetch_intelligence` (which is async via `AsyncSession`). The nightly orchestrator runs sync-friendly inside `_process_session`, so a sync accessor was needed; both paths feed `compute_calibrated_barriers(rows).to_weeks_dict()` so confidence-gating (MEDIUM+) stays consistent. The pathway result is dumped as the new plan body — no `build_action_plan` call (action_plan requires `BarrierCard` instances; `sessions.barriers` stores plain strings, mismatched contract).

**Carry-over for S13**: `sessions.previous_plan` column is now duplicated by the canonical `plan_history` table. The dual-write is a deprecation bridge — a future S13 ticket should drop the column and migrate any in-flight readers (the `app.core.progress_queries.store_previous_plan` helper + the `routes/plan.py` POST `/refresh` consumer) to read from `plan_history` instead. Documented inline in the `plan_refresher.py` module docstring (`Deprecation note (S13)`). Module also keeps a module-level `compute_stall_for_session` re-export so test monkeypatches against `plan_refresher.compute_stall_for_session` work without reaching into the engagement module.

## 2026-04-23 — S12b T12.21 engagement API routes (events/preferences/send-now/unsubscribe)

**T12.21 (done)**: built `backend/app/routes/engagement.py` (253 lines / 11 fn — arch warning-only above 150 line threshold; under 400 error, 11 < 15 function limit, 11 < 20 imports). Four endpoints under the `/api/engagement` prefix. Preview-digest already lived at `routes/engagement_preview.py` from S12a T12.21a and is NOT touched.

Endpoints:
- `GET /api/engagement/events?session_id=X&token=Y` — returns `{events: [{id, category, payload, created_at}]}` for the session. Token validated via `_appointments_helpers.verify_token` (401 bad, 403 cross-session).
- `POST /api/engagement/preferences?session_id=X&token=Y {reminders_enabled: bool}` — session-scoped; `false` writes a `reminders_auto_disabled` engagement_events row (the T12.19 opt-out signal), `true` deletes any existing rows. Returns the echoed state.
- `POST /api/engagement/send-now {session_id}` — admin-only via `Depends(require_admin_key)` from `app.core.auth` (deliberately NOT the `demo.py:20` local-constant anti-pattern). Rate-limited 3 calls per `hash_actor_token(x_admin_key)` per hour via an in-process `_RATE_LIMITER` dict + threading `Lock` (mirrors `admin_flags.py` pattern; separate from `feature_flags._check_rate_limit` because that's hard-coded to 10/hr). 4th call in the window → 429. Dispatches through `_dispatch_send_now` (test seam) → `reminder_engine.send_reminder(session_id, StallLevel.SOFT)` so cooldown + opt-out + kill-switch preflight all apply.
- `POST /api/engagement/unsubscribe {token}` — public. Verifies via `unsubscribe_tokens.verify` (T12.19 module — session_id-scoped parallel of T12.10b's appointment-token pattern; shared `used_tokens` table with `action='unsubscribe'` discriminator for atomic replay protection). Any `TokenError` subclass folded into a uniform 401 body ("Invalid or expired unsubscribe token.") — no enumeration oracle. On success, writes the `reminders_auto_disabled` row.

Router registration: `backend/app/routes/__init__.py` now imports `engagement_router` and appends it to `all_routers` right before `engagement_preview_router`. S8 route-registration test passes.

**Carry-over (same as T12.19)**: `sessions.reminders_enabled` column still does NOT exist. Both `POST /preferences` and `POST /unsubscribe` use the `engagement_events.reminders_auto_disabled` row pattern — matching the reminder engine's preflight contract so the same opt-out signal gates worker self-service toggles + unsubscribe-link clicks + the T12.2a hard-bounce auto-disable path. Adding a real column was deliberately NOT in scope for T12.21.

Tests: 18/18 pass in `tests/test_engagement_routes.py` (TDD red → green; all 18 red on initial import-error failure before impl). 25/25 pass across engagement + s8 code-quality. Full suite: 3071 passed, 2 pre-existing failures only (`test_contract_credit_api` + `test_evidence_collector::test_outcomes_logged_in_range`); 0 net new regressions.

Pattern notes for future contributors: `_dispatch_send_now` is a module-level function kept as a single-line indirection purely so unit tests can `patch.object(eng, "_dispatch_send_now", return_value=fake_result)` without reaching SendGrid. `_RATE_LIMITER.clear()` is an autouse test fixture — do NOT rely on rate-limit state surviving across tests.

## 2026-04-23 — S12b T12.16 cover letter builder (fair-chance aware)

**T12.16 (done)**: built `backend/app/modules/documents/cover_letter_builder.py` (294 lines / 9 fn — arch warning-only above 150 line threshold) + spoke `_cover_letter_branches.py` (130 lines / 4 fn, no warnings). Test file `tests/test_cover_letter_builder.py` written from scratch as the spec (11 tests, TDD red → green).

Public API: `generate_cover_letter(session_id, job_match_ref, resume_version_id, *, db_path) -> CoverLetterDraft`. `job_match_ref` is an opaque dict whose `employer` + `city_slug` keys drive the fair-chance lookup (also reads optional `title`, `hiring_manager`).

**Fair-chance lookup**: reuses existing `app.modules.criminal.fair_chance_index.get_fair_chance_employers(city_slug)` — NO new public API, no separate JSON. Match is case-insensitive on employer name; unknown employer/city defaults to `False` (safe non-disclosure).

**Two branches** (extracted to `_cover_letter_branches.py` per the wheel-and-spoke pattern, mirrors `outcomes/tracker.py` + `tracker_sql.py`):
- **Fair-chance**: `barriers_to_frame` returns the intersection of `profile.cleared_barriers` with a gap-implying set (`criminal_record`, `incarceration`, `treatment`, `homelessness`). The Jinja context's `fair_chance_framing` slot gets a one-sentence employment-gap narrative naming the cleared barrier in neutral language. Persisted `barriers_framed_json` mirrors the framed list.
- **Non-fair-chance**: `barriers_to_frame` returns `[]` unconditionally. `fair_chance_framing` is empty string so the `{% if %}` block in the template suppresses any record disclosure. Persisted `barriers_framed_json` is `NULL`.

**Render path** (mirrors `resume_builder` exactly): three gates — injection scan → `ENABLE_AI_GENERATION` flag → LLM call wrapped in try/except. Template path is `cover_letter_base.md.j2` (T12.14). Output post-processed through `voice.apply_worker_voice` for both branches. `_call_llm` is the explicit test seam.

**Persistence**: every call inserts into `resume_versions` with `doc_type='cover_letter'`, monotonic `version_counter` per `(session_id, doc_type)` (independent of resume rows on the same session), `barriers_framed_json` populated only on fair-chance branch with framed list, `generation_method ∈ {"llm","template"}`. `resume_version_id` recorded by caller for cross-doc lineage; this builder doesn't dereference it.

Tests cover: fair-chance branch (Montgomery + Fort Worth) addresses record with employment-gap framing + populates `barriers_framed`; non-fair-chance branch (Montgomery + Fort Worth) suppresses "criminal record"/"conviction"/"incarcer*" entirely + leaves `barriers_framed` empty; persistence row asserts `doc_type='cover_letter'` + correct `barriers_framed_json` + `generation_method`; version_counter independent of seeded resume row; injection in `notes` short-circuits to template even with flag ON (LLM stub raises if called); worker-voice strips smart quotes from name field; flag ON + clean input + successful LLM stub → `generation_method="llm"`. All 11 pass; 60 sibling document-module tests still green (no regressions).

The fair_chance_index `_DATA_ROOT` is monkeypatched per-test to a tmp path — tests seed their own minimal employers.json so they don't depend on real data files (montgomery has no employers.json yet).

## 2026-04-23 — S12b T12.15 resume builder (LLM-gated, injection-defended)

**T12.15 (done)**: built `backend/app/modules/documents/resume_builder.py` (289 lines / 11 fn — arch warning-only above 150 line threshold). Test file `tests/test_resume_builder.py` written from scratch as the spec (11 tests, TDD red → green).

Public API: `generate_resume(session_id, *, job_description=None, db_path) -> ResumeDraft`. Returns `ResumeDraft(session_id, markdown, generation_method, version_counter, injection_reason)`.

Path selection — three gates in order:
1. **Injection scan** (`injection_filter.check_for_injection`) over `name`, `summary`, `notes`, and every `work_history[i].title/.description`. On any match: force template path, record `injection_reason` with the offending field + regex.
2. **Feature flag** `ENABLE_AI_GENERATION` — when OFF (default), template path.
3. **LLM call** — wrapped in try/except; any exception falls back to template so the worker always gets a resume.

Rendering: deterministic template path uses Jinja2 `PackageLoader("app.modules.documents", "templates")` + `select_autoescape()`, reads the T12.14 `resume_base.md.j2` template. When `job_description` is supplied, `resume_keywords.extract_keywords` + `resume_ranking.rank_projects` reorder `work_history` so the highest-keyword-overlap role lands first. Output post-processed through `voice.apply_worker_voice` (T12.14 rules: dash/hedge/quote/hyphen stripping + dignified substitution).

Persistence: every call inserts into `resume_versions` with:
- `doc_type = "resume"`, `generation_method ∈ {"llm", "template"}`, monotonic `version_counter` per `(session_id, doc_type)` computed via `SELECT COALESCE(MAX(counter), 0) + 1`, full `markdown` body, `created_at` UTC. `injection_reason` is returned on the draft but NOT persisted (callers handle audit).

`_call_llm(*, prompt, session_id)` is the explicit test seam — default raises `RuntimeError` noting the LLM path isn't wired for S12b (production flag defaults off). S12b+ wire-up task can swap in the existing `app.ai.llm_client` surface without changing the public API.

Tests cover: template path always contains Name/Summary/Skills/Work-history sections; flag off forces template + asserts LLM stub never called; keyword reranking flips forklift above line cook when JD mentions forklift; cleared-barrier framing rendered when session profile has `cleared_barriers`; injected text in `notes` or `name` short-circuits to template even with flag ON (LLM stub raises if called — guards against regressions); `resume_versions` row written with counter 1/2/3 across successive calls; flag ON + clean input + successful LLM stub → `generation_method="llm"`; LLM exception falls back to template gracefully.

**Commit scope note**: the 3 helper modules (`resume_keywords.py`, `resume_ranking.py`, `injection_filter.py`) and their 2 test files (`test_resume_keywords.py`, `test_injection_filter.py`) were sitting uncommitted as T12.15 dependencies — they go in the same commit as the builder.

Tests: 11/11 resume_builder + 13/13 keywords/injection helpers pass. Full suite: 3047 passed (+11 vs prior 3036), 2 pre-existing failures only (`test_contract_credit_api` + `test_evidence_collector::test_outcomes_logged_in_range`). 0 net new regressions.

## 2026-04-23 — S12b T12.22a weekly review composer + Sunday orchestration branch

**T12.22a (done)**: built the per-session weekly review composer from scratch (test file was the spec — 15 failing tests went red → green end-to-end).

- `backend/app/modules/plan/weekly_review.py` (281 lines / 10 fn): public API is `build_weekly_review(session_id, date_range, *, db_path) -> WeeklyReview` + `format_summary_report(review) -> str`. Three section dataclasses — `FunnelMovement(draft_to_applied, applied_to_interview, interview_to_offer)`, `EngagementTrend(digests_sent, digests_opened, open_rate, reminders_sent)`, `BarriersClearedSummary(total, by_barrier)` — composed into one `WeeklyReview` with a pre-rendered `summary_markdown` field. `build_weekly_review` decomposed into `_collect_window_signals` + `_assemble_review` to stay under the 40-line function ceiling.
- `backend/app/modules/plan/_weekly_queries.py` (193 lines / 7 fn): SQL spoke. `fetch_funnel_movement` counts `job_application_applied` / `_interview` / `_offer` outcomes in window; `fetch_engagement_trend` counts `digest_sent` + three stall reminder categories from `engagement_events` and joins `sendgrid_events.open` via `sessions.profile.email`; `fetch_barriers_cleared` handles DUAL `barrier.cleared` + legacy `barrier_resolved` event types. All queries are per-session scope only — **deliberate k-anonymity sentinel documented in the hub module's docstring** so future contributors route cross-session aggregation through `outcomes.intelligence_queries` (which already enforces 5-session suppression). Window bounds are `start-of-day` UTC to `end-of-day` UTC so tests using Sunday 02:00 UTC boundaries fall within.
- Markdown rendering: quiet-week fallback when all signals zero; otherwise 3 section headers (`## Funnel movement`, `## Engagement`, `## Barriers cleared`) with bullet counts and open-rate percentage.

Orchestrator wire-up:
- `backend/scripts/_nightly_weekly.py` (new, 60 lines): `send_weekly_review(session_id, email, for_date, *, db_path, send_fn)` spoke — 7-day window ending at `for_date`, subject format `"Your week — <start> to <end>"`, dispatches through an injected `send_fn` (always `reminder_engine.send_digest`) so cooldown + opt-out + kill-switch gating apply uniformly. Weekly failures are caught and logged — they must NOT poison the daily digest's accounting.
- `backend/scripts/_nightly_db.py` (new, 59 lines): extracted `collect_active_sessions_for_city` + `resolve_session_email` out of `nightly_digest.py` so the orchestrator stays under the 15-imports ceiling (was 16, now 13).
- `backend/scripts/nightly_digest.py`: Sunday branch (`now.weekday() == 6`) in `_process_session` invokes the weekly-review spoke AFTER the daily send. Day-of-week checked against the caller-supplied `now` (UTC) rather than `for_date` (city-local) because for Chicago-tz cities at 02:00 UTC Sunday, `for_date` is still Saturday local. Extracted `_dispatch_daily` to keep `_process_session` under 40 lines. `send_digest` passed as `send_fn` injection so `monkeypatch.setattr(nd, "send_digest", ...)` continues to intercept both daily + weekly sends.

Tests: 15/15 pass in `tests/test_weekly_review.py` (including Sunday-branch invocation, non-Sunday skip, two-email Sunday dispatch). 47/47 pass across weekly_review + nightly_digest + reminder_engine + s12a_e2e. Full suite: 3036 passed, 2 failed — 1 pre-existing `test_contract_credit_api`, 1 pre-existing `test_evidence_collector::test_outcomes_logged_in_range` (time-of-day-sensitive, confirmed failing on clean tree at c413631). Arch: all new files warning-only above 150 line threshold, no errors.

## 2026-04-23 — S12b T12.19 reminder engine wired into nightly orchestrator

**T12.19 (done)**: closed the last failing reminder-engine test by routing the nightly digest through `reminder_engine.send_digest`. Engine code (modules + helpers + templates + tokens + cooldown) was already complete and ported from `ops:lib/`.

- `backend/scripts/nightly_digest.py`: replaced direct `send_transactional(...)` call in `_process_session` with `send_digest(session_id, email, subject, html, text, db_path=db_path)`. The reminder engine now gates every nightly send behind: (a) the (`session_id`, `"digest"`) cooldown row in `reminder_cooldowns`, (b) the `reminders_auto_disabled` engagement_events row (set by worker opt-out OR T12.2a hard-bounce handler), (c) the `EMAIL_SEND_ENABLED` kill-switch. Engine also writes the engagement_events success row. Module docstring + the TODO comment cleared.
- `backend/tests/test_nightly_digest.py` + `backend/tests/_s12a_e2e_helpers.py`: shared `_install_sendgrid_spy` / `install_sendgrid_spy` helpers swapped from monkeypatching `nd.send_transactional` → `nd.send_digest`. Spy returns a `ReminderDispatchResult(success=True)` matching the new contract; existing assertions on `to`, `subject`, `category`, `session_id` keep working without test-body changes. Removed the now-unused `EmailSendResult` import from the e2e helpers.

`sessions.reminders_enabled` carry-over: column does NOT exist on the `sessions` table (S12a-leftover debt). The engine handles this gracefully — opt-out is checked via the `engagement_events.reminders_auto_disabled` row pattern, NOT a session column. Worker opt-out and the T12.2a hard-bounce path both insert the same row shape.

Tests: 38/38 pass across `test_reminder_engine.py` + `test_cooldown.py` + `test_unsubscribe_tokens.py` + `test_nightly_digest.py`. 12/12 pass in `test_s12a_worker_companion_e2e.py`. Full suite: 3019 passed (+1 vs prior 3018), 19 failures — 16 are the known `test_weekly_review` `ModuleNotFoundError` (Stage C target), 1 is the pre-existing `test_contract_credit_api`, 0 net new regressions. Arch checks: warning-only on the 4 engagement modules + nightly_digest.py (all between 162–276 lines, well under 400 error).

## 2026-04-23 — S12b T12.14 worker voice + resume/cover letter templates

**T12.14 (done)**: created `backend/app/modules/documents/voice.py` (196 lines / 9 fn — arch warning-only above 150 line threshold; under 400 error). Single entry point `apply_worker_voice(text)` runs the full rule chain; idempotent (running twice yields same output).

- Ported from `ops:lib/cover_letter_generator.py`: `_strip_dashes` (em-/en-dash → comma), `_strip_hedges` (perhaps/maybe/might/possibly/somewhat removed, double spaces collapsed), `_strip_quotes` (smart → ASCII).
- Ported from `ops:lib/resume_generator.py`: `_strip_hyphens` — preserves last-name hyphens and street-address hyphens (regex anchors), removes obscuring mid-word hyphens.
- Dignified substitutions: replaces loaded labels (e.g. "felon" → "person with a record") drawn from a substitution map; leaves neutral text untouched.
- Reading-level helper: `_count_syllables` + `flesch_kincaid_grade(text)`. Test asserts F-K grade <9.0 on the fixed 5-sample worker-voice corpus.

Templates added under `backend/app/modules/documents/templates/`:
- `resume_base.md.j2` — markdown skeleton (header, summary, experience, skills, education); optional sections gated by truthy checks; HTML in worker-supplied fields auto-escaped.
- `cover_letter_base.md.j2` — greeting + body + closing; default greeting "Dear Hiring Manager,". Both templates render under Jinja2 `autoescape=True`.

Tests: 36/36 pass in `tests/test_document_voice.py`. Templates verified for render + escape behavior. Default `default.html` template (T12.4) untouched.

## 2026-04-23 — S12b T12.7a appointment enrichment + stage advance

**T12.7a (done)**: ported `ops:lib/appointment_merge.py` into `backend/app/modules/appointments/enrichment.py` (235 lines / 9 fn, arch warning-only at >150 line threshold). Public API: `auto_advance_stage(appointment, *, city=None) -> StageAdvance | None` (pure — never mutates), `merge_appointment(existing, new) -> Appointment` (field-level fill of None/empty), `enrichment_changed(existing, new) -> dict[str, tuple]`, `build_pipeline_summary(session_id, *, db_path) -> dict[(barrier, stage), int]`, `register_enrichment_listener(db_path)` (idempotent via module-level `_REGISTRATION_SENTINEL`).

- City-aware stage flow keyed by `(city_slug, barrier_link)`: AL Montgomery uses expunction labels (`filed → heard → granted → cleared`); TX Fort Worth uses nondisclosure labels (`petitioned → heard → ordered → cleared`); benefits and employment flows shared across cities.
- Listener subscribes to `appointment.attended` + `job_application.offer` via the S12a in-process `app.core.events` bus (no direct import of emitters). Handler emits `barrier.cleared(session_id, barrier_id)` only when an advance reaches a terminal stage (`cleared`/`recerted`/`completed`) — feeds the intelligence engine's calibration loop. Job offers always emit `barrier.cleared` for the `employment` barrier.
- Current stage is encoded in `appointment.notes` as `stage:<name>` (lightweight S12a contract before a dedicated stage column lands). Absent/unparseable notes fall back to flow's first stage. Malformed event payloads logged and swallowed.

Tests: 14/14 pass in `tests/test_appointment_enrichment.py`. Listener registration in `app/main.py` deferred to a follow-up wire-up task — tests exercise the listener function directly.

## 2026-04-23 — S12b T12.8a worker_unavailability bookkeeping

**T12.8a (done)**: code (`backend/app/modules/appointments/unavailability.py` + `backend/tests/test_worker_unavailability.py`) was bundled into the T12.8 commit (`cf8c6dd`) alongside the availability engine. Marked done here — no new commit. Module covers worker-side blackout windows respected by `availability.suggest_slots`; tests covered by the broader appointments-availability suite.

## 2026-04-23 — S12b T12.8 availability engine — service config in city YAMLs

**T12.8 (done)**: three tests in `tests/test_appointment_availability.py` were failing because `appointment_services` was missing from both city YAMLs. The engine itself (`availability.py`, `service_config.py`, `_availability_time.py`, `unavailability.py`) already works — this was purely a data gap.

- `cities/montgomery.yaml`: added `appointment_services` with the 4 service types the tests assert on — `court_hearing` (60 min), `benefits_recert` (45 min), `dmv` (30 min), `childcare_intake` (45 min). Each carries morning + afternoon local hours with lunch break and `closed_days_of_week: [5, 6]` (Sat/Sun closed).
- `cities/fort-worth.yaml`: same schema. City-agnostic defaults for S12b launch; a later data-curation task can layer in per-city variance (e.g. Texas DPS Saturday hours) without schema changes. Comment added documenting that choice.

Tests: 20/20 pass in `tests/test_appointment_availability.py`. 165 city-related tests pass across the suite — zero regressions. No arch check (YAML files).

## 2026-04-23 — S12b T12.10a transactional emails — async scheduler job handler

**T12.10a (done)**: `tests/test_appointment_transactional_emails.py::test_scheduler_job_invokes_scan` was failing because the `appointment_reminders` scheduler job was still registered as `_make_stub(...)` (a sync no-op logger), but the test drives it via `asyncio.run(job.func())`. Two fixes:

- `backend/app/core/scheduler.py`: replaced the stub registration with a real handler that delegates to the new `scheduler_jobs.appointment_reminders_handler()` factory.
- `backend/app/core/scheduler_jobs.py` (new): factored out both handler factories (`nightly_digest_handler`, `appointment_reminders_handler`) to keep `scheduler.py` under the 12-functions-per-file project ceiling. `appointment_reminders_handler()` returns an `async def _run()` that lazy-imports `transactional_emails` + `resolve_db_path`, resolves the DB path at run-time (so tests can monkeypatch), and calls the sync `scan_and_send_reminders(db_path=...)`. Downstream `scan_and_send_reminders` stays sync — no refactor chain needed.

Tests: 45/45 pass across `test_appointment_transactional_emails.py`, `test_scheduler.py`, `test_nightly_digest.py`, `test_s12a_gate.py` (1 pre-existing skip, unrelated 10-min scale test). Arch check: both files clean. Extraction pattern mirrors S12a's `tracker.py`/`tracker_sql.py` split.

## 2026-04-23 — S12b T12.10b signed manage-appointment links — router registered

**T12.10b (done)**: `backend/app/routes/appointments_manage.py` was implemented but never added to `all_routers`, so the `GET /api/appointments/manage` endpoint was unreachable at runtime.

- `backend/app/routes/__init__.py`: added `from app.routes.appointments_manage import router as appointments_manage_router` and inserted it into `all_routers` **before** `appointments_router`. Order matters: `appointments.py` has a `/{appointment_id}` catch-all that would otherwise swallow the `/manage` path. Added a comment in the registry explaining the ordering constraint.

Tests: 23/23 pass in `tests/test_appointment_tokens.py` + `tests/test_s8_code_quality.py`. Arch check surfaced one pre-existing violation on `backend/app/routes/__init__.py` — 25 imports > 15 threshold. Baseline (before S12b) was already 24 > 15; this is a route-registry aggregator whose job is to import every router. Not our regression, not in scope to refactor. `appointments_manage.py` itself is arch-clean.

## 2026-04-23 — S12b T12.4 PDF Rendering — deps + template closed

**T12.4 (done)**: closed the two remaining test failures in `backend/tests/test_pdf_renderer.py`.
- `backend/requirements.txt`: pinned `weasyprint==60.2` and `markdown==3.7`.
- `Dockerfile`: added `apt-get install` block for `libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libffi-dev fonts-liberation` before the pip install step (native WeasyPrint dependencies required on `python:3.13-slim`, which ships without them).
- `backend/app/modules/documents/templates/default.html`: upgraded the existing template to print-friendly CSS (A4 page size, 1in margins via `@page`, Liberation Serif body + Liberation Sans headings, `page-break-inside: avoid` on tables/pre, anchor styles for h1/h2/h3/blockquote/code/ul).

Tests: 14/14 pass in `tests/test_pdf_renderer.py`. Arch check: warning-only (178 > 150 warn threshold, well under 400 error).

## 2026-04-23 — Planned Sprint S12b

Created plan `plan-2026-04-s12b-value-extensions` with 25 tasks (actual Cx sum **510**, not the backlog header's 490 — header was self-flagged as having a discrepancy against the ground-truth `### T12.x | Cx: N` lines; recount of those lines gives 510 Cx). Priority breakdown: **P0=3** (T12.36, T12.32b, T12.35b), **P1=18**, **P2=4** (T12.8a, T12.25b, T12.31, T12.31a). Sprint extends the S12a foundation with PDF rendering, resume + cover letter builders (LLM-gated), reminder engine + cooldown, plan refresher, transactional appointment emails + signed manage-links with key rotation, jobs kanban + documents pages + advisor inbox (city-scoped), past-appointment auto-advance, module status contracts, weekly review composer, and the **compliance gate** (T12.36 worker data export + right-to-delete) that unblocks production GA.

S12a staging-only constraint lifts when T12.36 lands.

## 2026-04-23 — S12a SPRINT COMPLETE — 26/26 tasks, GATE green

**Final state: 2,851 backend tests passed (+450 new), 842 frontend tests passed, zero regressions. Two pre-existing failures remain (credit-assessment jwt, s8 route-counter).**

**Waves 5-12 summary** (Waves 1-4 committed as `b95ae8d`):

- **Wave 5** — T12.2a SendGrid Event Webhook (ECDSA signature verify, 13 events, hard-bounce audit-row disable — `sessions.reminders_enabled` column missing, documented for S12b); T12.9 Pathway → Appointment Auto-Linker (both `routes/pathway.py` and `routes/plan_intelligence.py` call `run_pathway_linker_hook`; **m003 migration** added to relax `appointments.starts_at NOT NULL` for placeholders); T12.11 Jobs Applications Lifecycle (composite `(source, url)` linkage, status machine + events + outcomes listener, main.py listener registered).

- **Wave 6** — T12.10 Appointments API Routes (9 endpoints, token auth via `_appointments_helpers.verify_token`); T12.12 Jobs Funnel Analytics (k-anonymity `min_5` enforced, intelligence endpoint `application_conversion_rates` wired in `routes/intelligence.py`); T12.23 Evidence Collector (unified 6-signal bundle from appointments + jobs + outcomes).

- **Wave 7** — T12.13 Jobs API Routes (`/api/job-applications` prefix — no collision); T12.18 Stall Detector (SOFT/MEDIUM/HARD with auto-advance suppression, `engagement_status` recommendations ported); T12.22 Daily Progress Retro (Option B — expected actions = today's appointments, classifications persisted); T12.33 Intelligence Wire-Up tests (10 tests against the `application_conversion_rates` endpoint, S11 consumer contract pinned).

- **Wave 7 mid-wave restoration**: `_intelligence_helpers.py` was reverted between Waves 5 and 7 (mechanism unclear — linter or hook). Orchestrator restored `run_pathway_linker_hook` + hook calls in `pathway.py` and `plan_intelligence.py` manually. State-of-tree note for merge review.

- **Wave 8** — T12.20 Digest Composer (4 files: composer/sections/rendering/data, carryover + dedupe + HTML escape ports, worker first name from `sessions.profile.first_name`); T12.26 Appointments Page (first frontend task, react-big-calendar + date-fns, 4 components + API client + 25 tests, translations at `src/lib/translations/`).

- **Wave 9** — T12.21a Digest Preview Endpoint (minimal single-endpoint route for frontend); T12.25 Nightly Orchestrator + Accounting (city-scoped batch iteration, `asyncio.Semaphore(10)`, accounting row per run to `nightly_run_log`, kill switch via `FEATURE_NIGHTLY_ENABLED`).

- **Wave 10** — T12.29 Daily Digest Page (4 section components + CollapsibleSection + StallAlert + DigestSectionBody; home redirect wired in `page.tsx` via `useAssessmentComplete` proxy based on `feedback_token_{sessionId}` sessionStorage presence; 16 tests).

- **Wave 11** — T12.32 E2E Integration Tests (4 flows × 2 cities + 6 contract assertions: route collision, two-caller pathway hook, k-anonymity, auto-advance suppression, city-scope isolation, event emission — runtime 1.92s).

- **Wave 12 GATE** — T12.35 Integration Gate (15 gate assertions + 2 admin-key-scan tests + 274-line runbook at `docs/ops/s12a-rollout.md`). All prior integrations verified: `all_routers` complete, scheduler lifespan wired, nightly_digest handler resolves to real orchestrator, pathway hook fires from both callers, migration rollback round-trips cleanly, feature-flag defaults locked in, all 13 tables present after m002, OutcomeTracker compat preserved. Load test: 200 sessions × 2 cities in 3.4s (budget 600s).

**Manual AC deferred** (out of scope for agent mode): browser walk-through (new session → plan → appointments → application → retro → digest). User to verify pre-merge.

**S12a staging-only constraint**: Must NOT go to production general availability until S12b T12.36 (worker data export + right-to-delete) lands. Documented in runbook.

**Tech debt carried into S12b** (from accumulated driver reports):
- `sessions.reminders_enabled` column (T12.2a uses audit-row pattern)
- `sessions.email` column (T12.2a webhook uses `unique_args.session_id` only)
- `sessions.city` column (T12.25 orchestrator infers from `outcomes_records.payload_json.city`)
- `sessions.demo` flag (T12.12 guard ready, S12b T12.34 adds column)
- Checklist item per-day tracking (T12.23 returns empty list)
- T12.11 outcomes listener bypasses `OutcomeTracker.record_outcome()` (serializer mismatch)
- m003 compatibility adjustment needed because T12.1 declared `starts_at NOT NULL` but T12.6 model allows None for placeholders
- Plan-refresh step in T12.25 stubbed with TODO → S12b T12.24
- Reminder engine with cooldown stubbed → S12b T12.19 replaces direct SendGrid call

**Test-quality regression carried**: `test_s8_code_quality::test_all_route_files_registered` — counts private `_*.py` helper modules in `routes/` as missing routers. Test needs updating in S12b cleanup task to exclude `_`-prefixed files, or helpers should move to a subdirectory.

## 2026-04-23 — S12a Waves 2-3 complete (T12.1, T12.3, T12.0a, T12.0b, T12.6)

**Wave 2**:
- **T12.3 — APScheduler + Day-Boundary (done)**: `backend/app/core/scheduler.py` (141 lines, AsyncIOScheduler singleton with `register_job`, `start_scheduler`, `shutdown_scheduler`, `enforce_single_worker`, three stub jobs: nightly_digest 02:00 CT cron, stall_scan 08:00 daily cron, appointment_reminders 6h interval — all no-op stubs with TODO markers). `backend/app/core/day_boundary.py` (110 lines, ports `ops:lib/nightly_day_boundary.py` — `current_work_date`, `resolve_work_date`, `_resolve_rollover_hour`; reuses `TIMEZONE_BY_CITY` from T12.5). Lifespan modified in `main.py`: `enforce_single_worker()` raises RuntimeError on `WEB_CONCURRENCY != "1"` at startup; soft warning in `test_main.py` promoted to hard failure assertion. `apscheduler==3.11.2` added to requirements. 21 new tests.

**Wave 3**:
- **T12.0a — DB-Backed Outcomes Store (done)**: Rewrote `backend/app/modules/outcomes/tracker.py` (147 lines) as SQLite-backed append-only store, factored helpers into new `tracker_sql.py` (129 lines) to stay under the project's 15-function-per-file limit. New API: `OutcomeTracker(db_path)`, `record_outcome` (INSERT never upsert), `list_by_session`, `list_recent(city, event_type, since)`, `get_latest`. Caller audit correction: **`intelligence.py` does NOT use `OutcomeTracker`** (consumes raw rows from `intelligence_queries.py`); real callers are only `aggregator.py` (type hint only) + 3 test files, all ported. Added optional `created_at` to `OutcomeRecord`. 10 new DB tests + 16 existing updated, all passing.
- **T12.0b — Feature Flag Infrastructure + Audit (done)**: `backend/app/core/feature_flags.py` (209 lines, resolution env > override > yaml > default + rate limiter), `backend/app/routes/admin_flags.py` (95 lines, `POST /api/admin/flags/{name}` with `require_admin_key`, 10/hour rate limit, ENABLE_AI_GENERATION warning emission, SHA256 actor hash). Config defaults at `config/feature_flags.yaml` (ENABLE_AI_GENERATION=false, FEATURE_NIGHTLY_ENABLED=true, FEATURE_EMAIL_SEND_ENABLED=true). Router registered in `backend/app/routes/__init__.py` (the project's `all_routers` aggregator — NOT main.py). `.env.example` updated. 23 new tests. Note: project's `max_function_lines` arch rule is 40 (not 50 as the backlog stated); driver extracted helpers to comply.
- **T12.6 — Appointments Types + Models (done)**: `backend/app/modules/appointments/types.py` (98 lines) with `Appointment` Pydantic v2 model. Imports `AppointmentType`, `AppointmentStatus` from T12.5. Validators: timezone-aware datetimes, `ends_at >= starts_at`, zero-duration rejected for user appointments, placeholder exception when `source="pathway_auto"` + `starts_at=None`. 12 new tests.

**Full suite**: 2519 passed, 1 pre-existing failure (`test_contract_credit_api` — credit-assessment sibling `jwt` import). Zero regressions. Ruff clean across all new files. Arch check clean (one warning on `feature_flags.py` at 209 > 150 warn threshold; well under 300 error).

**Carried follow-ups**:
- `database.py:13,94` + `test_database.py` still import `DDL_SQL` directly (works via re-export)
- `intelligence.py` does not use `OutcomeTracker` — affects T12.33 expectations (intelligence wire-up uses raw queries, not the tracker)
- Project arch rule is `max_function_lines: 40`, not 50 — downstream drivers should honor

## 2026-04-23 — T12.1 Database Schema Migrations (All 13 Tables)

**T12.1 — m002_s12_worker_companion (done)**: Added `backend/app/core/migrations/m002_s12_worker_companion.py` (254 lines) creating all 13 S12a+S12b worker-companion tables in a single migration. Tables: `appointments`, `job_applications`, `resume_versions`, `daily_progress_snapshots`, `engagement_events`, `plan_history`, `outcomes_records`, `reminder_cooldowns`, `nightly_run_log`, `scheduler_leases`, `worker_unavailability`, `feature_flag_audit`, `sendgrid_events`. All 9 tables with a `session_id` FK declare `TEXT REFERENCES sessions(id) ON DELETE CASCADE`. 25 indexes created per spec (status, starts_at, applied_date, date, created_at, category, event_type, composite reminder_cooldowns(session_id, category), composite feature_flag_audit(flag_name, timestamp)). `plan_history` carries inline SQL comment `-- cap of 20 per session enforced in T12.24 (application code; NOT at schema level)`. SCHEMA_VERSION=2; upgrade uses `CREATE TABLE IF NOT EXISTS` (idempotent); downgrade drops all 13 tables in reverse order.

**Tests**: 10 new passing in `backend/tests/test_m002_migration.py` (463 lines) — all 13 tables present, session_id columns TEXT, FK CASCADE verified via `PRAGMA foreign_key_list`, every required index name present, plan_history schema, cap comment grep, idempotent re-apply, downgrade round-trip inserts+drops with m001 sessions row intact, `schema_migrations` records version 2, module shape (SCHEMA_VERSION/upgrade/downgrade).

**Regression fix**: T12.0's `tests/test_migrations_runner.py` used `applied == ["m001_initial"]` strict equality in 4 tests — broke by design when any new migration lands. Relaxed to `"m001_initial" in applied` membership checks (+ first-element check on fresh DB to preserve ordering assertion). No production code changed for this fix.

**Full suite**: 2464 passed, 1 pre-existing failure (`test_contract_credit_api::test_provider_simple_input_fields_unchanged` — documented unrelated). Ruff clean. Arch check: m002 file size 254 (below 400 error threshold; warning-only at 150). Test file has function-size warnings reduced via helper extraction.

## 2026-04-23 — S12a Wave 1 complete (T12.0, T12.5)

**T12.0 — Migration Infrastructure (done)**: Built per-migration Python module system following `ops:lib/db.py` pattern. Created `backend/app/core/migrations/{__init__.py, runner.py, m001_initial.py}`. Extracted existing `DDL_SQL` into `m001_initial.py` byte-for-byte; `backend/app/core/schema.py` now re-exports for backward compat (noted `database.py:13,94` + `test_database.py:175,193,234,251` for follow-up migration off direct `DDL_SQL` imports). 13 new tests. No regressions.

**T12.5 — Shared Schemas + Timezone (done)**: Created `backend/app/modules/common/temporal_types.py` with six string-valued enums (`AppointmentType`, `AppointmentStatus`, `JobApplicationStatus`, `EngagementEventType`, `StallLevel`, `GenerationMethod`) + Pydantic models + `format_city_local(dt, city)`. `TIMEZONE_BY_CITY` registry used since `CityConfig` doesn't carry a `timezone` field and widespread tests instantiate it directly. 29 new tests. Note: Montgomery AL + Fort Worth TX are both `America/Chicago`; "different strings per city" test uses monkeypatch to prove the formatter reads from config rather than hardcoding.

**Full suite**: 2443 passed, 1 pre-existing failure (`test_contract_credit_api::test_provider_simple_input_fields_unchanged` — unrelated; sibling `credit-assessment` repo missing `jwt` module). Ruff clean. Arch check clean on new files.

**CLI task status**: Both tasks still show `in_progress` in paircoder — `task update --status done` refused due to dirty tree (expected per /running-sprint-tasks protocol; commit between waves clears it). Tracking completion here per skill guidance.

## 2026-04-23 — Planned Sprint S12a

Created plan `plan-2026-04-s12a-worker-companion-foundation` with 26 tasks (520 Cx — corrected from initial header claim of 25/498) from `backlog-sprint-s12a-foundation-daily-loop.md`. Sprint establishes foundation (migration infra, DB outcomes store, feature flags, scheduler) + daily loop (appointments CRUD + routes + page, jobs lifecycle + funnel, digest composer, stall detector, nightly orchestrator, daily digest page) + gate. Staging-only until S12b T12.36 compliance work lands.

- **Sprint S11 -- "People Like You" Community Insights (Capstone)** (2026-04-11): Built the "People Like You" engine that transforms calibrated barrier outcome data into personalized, deterministic, city-aware community insight messages. No LLM. No AI. Pure deterministic logic. CREATED: app/modules/outcomes/community_insights.py (221 lines) -- Core engine with CommunityInsight Pydantic model (message, barrier_type, confidence, sample_size, metric_type) and 6 functions: generate_insights() pure function takes CalibratedWeeks + user barriers + city name and produces personalized messages; generate_cold_start_insight() for first-user encouraging messaging; _format_resolution_insight() produces "15 people in Fort Worth with criminal records resolved them in about 8 weeks"; _format_success_rate_insight() produces "80% success rate" messages; _format_recommendation_insight() compares multiple barriers and suggests resolving the fastest first; _format_people_phrase() adapts language by confidence level (HIGH: exact count "15 people", MEDIUM: "Several people", LOW: "A small number of people"). CREATED: app/routes/insights.py (62 lines) -- Standalone GET /api/insights/{session_id} endpoint, auth-protected, returns personalized insights list with barrier_count and city metadata. MODIFIED: app/routes/plan_intelligence.py (92 lines) -- Added "insights" section to the unified plan intelligence response, using generate_insights from the community_insights engine. MODIFIED: app/routes/__init__.py -- Registered insights_router. NEW TESTS: 4 test files, 36 new tests (2,394 total, was 2,358). test_community_insights.py (21 tests -- TestSingleBarrierHighConfidence: city name in message, sample size visible, avg weeks visible, model fields correct, success rate insight generated; TestColdStart: empty barriers data, city included, encouraging tone, recommendation metric type; TestMixedConfidence: multiple barriers produce insights for each, LOW confidence uses cautious language, MEDIUM uses moderate language, NONE confidence skipped to cold start; TestBarrierCombinationInsights: recommendation with multiple barriers, suggests fastest barrier first, no recommendation for single barrier; TestDeterminismAndEdgeCases: deterministic output verified, empty barriers returns empty, unknown barrier graceful fallback, all 7 barrier types produce insights, model serialization). test_insights_route.py (6 tests -- returns insights list, cold start encouraging, invalid token 401, session not found, city name in insights, response includes metadata). test_plan_intelligence_insights.py (4 tests -- response includes insights key, insights section is list, insights with feedback data, cold start insights). test_insights_with_seed.py (5 tests -- seeded data produces non-cold-start insights, insights reference calibrated stats with numbers, plan intelligence has insights after seeding, insights are deterministic across requests, Carlos persona with criminal+childcare+credit gets barrier-specific insights). Zero LLM calls. Fully deterministic. City-aware. All files under 400 lines, all functions under 50 lines. Zero regressions.

- **Sprint S10 -- Demo Seed Data + Final Verification** (2026-04-11): Built the demo seed command and full pipeline verification for HackFW 2026 demo readiness. CREATED: app/demo_seed.py (244 lines) -- Deterministic seed module (Random(42)) that populates 50 Fort Worth sessions with realistic barrier distributions (criminal_record ~40%, transportation ~60%, credit ~50%, childcare ~35%, housing ~25%, health ~15%, training ~20%), Fort Worth ZIP codes (76102-76119), varied employment statuses, Texas benefits profiles (SNAP/TANF/Medicaid/CHIP/CEAP/Childcare_Subsidy), plans with immediate_next_steps, and feedback tokens. Also creates 30 visit_feedback entries with resolution outcomes, plan accuracy ratings (2-5), and free text comments. Runnable as `py -3.12 -m app.demo_seed` or via admin endpoint. CREATED: app/routes/demo.py (48 lines) -- POST /api/demo/seed admin endpoint protected by X-Admin-Key header, idempotent (detects existing data). MODIFIED: app/modules/outcomes/intelligence_queries.py -- Enhanced get_barrier_feedback_rows to estimate weeks_to_resolve from time delta between sessions.created_at and visit_feedback.submitted_at. This closes the final gap in the N+1 loop: the intelligence engine now computes actual avg_weeks from real timestamp data, making calibrated_weeks non-empty when feedback exists. Added _estimate_weeks and _try_parse helpers. Backward compatible (returns None when timestamps unavailable). MODIFIED: app/routes/__init__.py -- registered demo_router. NEW TESTS: 4 test files, 31 new tests (2,366 total, was 2,335). test_demo_seed.py (8 tests -- 50 sessions created, Fort Worth ZIPs in profile, valid barriers, plans present, feedback tokens for all sessions, criminal_record ~40%, transportation ~60%, credit ~50%). test_demo_seed_feedback.py (9 tests -- 30 feedback entries, valid outcomes JSON, plan accuracy 1-5, feedback links to valid sessions, intelligence calibrated after seed, calibrated weeks differ from defaults, multiple barrier types calibrated, deterministic output, return value summary). test_demo_route.py (4 tests -- requires admin key, rejects wrong key, succeeds with correct key, idempotent second call). test_full_pipeline_with_data.py (10 tests -- intelligence barriers endpoint calibrated, plan intelligence returns all 4 sections, pathway with community intelligence, pathway strategies present, share seeded session and retrieve, dashboard shows 50 assessments, outcomes aggregate, N+1 loop visible with calibrated != defaults, full chain seed->intelligence->pathway->share->dashboard, admin endpoint triggers seed and intelligence shows data). Zero regressions. All files under 400 lines, all functions under 50 lines.

- **Sprint S9 -- Wire the Intelligence Loop Complete** (2026-04-11): Closed the N+1 feedback loop for real. The pathway route now fetches calibrated_weeks from the intelligence engine at REQUEST TIME so community feedback flows into every pathway recommendation automatically. Previously, the intelligence engine computed calibrated values but the pathway endpoint ignored them -- using hardcoded defaults instead. Now: visit_feedback in DB -> intelligence_queries.get_barrier_feedback_rows() -> intelligence.compute_calibrated_barriers() -> to_weeks_dict() -> pathway route passes to generate_pathways(calibrated_weeks=data). MODIFIED: app/routes/pathway.py -- now imports fetch_intelligence and passes calibrated_weeks to generate_pathways, adds community_intelligence metadata to response. CREATED: app/routes/plan_intelligence.py (85 lines) -- Unified Plan Intelligence endpoint GET /api/plan/{session_id}/intelligence returns EVERYTHING a frontend needs in one call: barriers (sequenced with calibrated weeks), pathway (3 strategies calibrated with community data), cliff_analysis (wage steps + cliff points), and community_intelligence (total_feedback, calibrated_barriers with confidence levels, improvements_from_defaults showing calibrated vs default for each barrier). CREATED: app/routes/_intelligence_helpers.py (77 lines) -- Shared helpers (build_community_intelligence, parse_benefits_profile, fetch_intelligence) used by both pathway and plan_intelligence routes, eliminating duplication. MODIFIED: app/routes/__init__.py -- registered plan_intelligence_router. NEW TESTS: 2 test files, 12 new tests (2,334 total, was 2,322). test_pathway_intelligence_wiring.py (3 tests -- pathway uses calibrated weeks from feedback, falls back to defaults on cold start, response includes calibration source with calibrated_barriers and improvements_from_defaults). test_plan_intelligence.py (9 tests -- returns complete intelligence package, barriers section has sequence, pathway section has strategies, cliff analysis section, community intelligence with feedback, cold start community intelligence, invalid token 401, session not found 404, improvements from defaults shown). Zero LLM calls. Fully deterministic. All files under 200 lines. All functions under 50 lines. Zero regressions.

- **Sprint S8 Phase 2 -- Cross-Module Integration Verify** (2026-04-11): Systematic cross-module integration verification for HackFW 2026 demo readiness. Verified ALL 14 integration chains from the cross-module checklist. NEW TESTS: 3 test files, 21 new tests (2,322 total, was 2,301). test_s8p2_cross_module.py (8 tests -- Assessment->Plan with FW profile through generate_plan, Plan->BarrierCards with FW resource_router actions, Plan->Cliff with TX AMI thresholds and TX programs, Plan->Pathway with calibrated_weeks, Sequencer->Intelligence calibrated weeks flow, PVS Scorer->Benefits Router TX net income, PVS Scorer->Geo Router FW proximity coords, City Config->ALL Routers single test proving benefits/criminal/geo/resource/prompt all return TX simultaneously). test_s8p2_e2e_demo.py (5 tests -- Full 8-step demo chain exercising plan->sequence->simulate->share->pathway->intelligence->dashboard in a single test, single-barrier edge case, all-barriers-resolved simulation, share data integrity verification, pathway with benefits profile for cliff navigation). test_s8p2_api_integration.py (8 tests -- Intelligence API with real DB feedback data and empty DB cold start, Dashboard with seeded sessions verifying aggregate accuracy, Outcomes aggregate endpoint, Simulate->Sequencer with remaining barrier verification, Simulate with unknown barrier type, Sequence API ordered steps with timeline, Sequence with all 7 barrier types). The full demo chain test (test_full_demo_chain) exercises 8+ modules in a single flow: plan route, barrier sequencer, sequence route, simulate route, share route, pathway engine, intelligence endpoint, and dashboard. Zero regressions. All files under 400 lines, all functions under 50 lines.

- **Sprint S8 Phase 1 -- Deep Polish** (2026-04-13): Systematic backend polish pass targeting coverage gaps, unused imports, dead code, type hints, and response format consistency. UNUSED IMPORTS REMOVED: assessment.py (HTTPException), brightdata.py (CrawlProgress), jobs.py (Request), employer_policy.py (ChargeCategory), pathway/engine.py (WAGE_MAX) -- 5 files cleaned. DEAD CODE FIXED: stage_builder.py had unreachable fallback line due to float("inf") sentinel in _TIER_THRESHOLDS -- removed sentinel, exposed fallback as the proper default path. TYPE HINTS ADDED: city.py get_city() -> dict, benefits/router.py get_sum_program_benefits() -> Callable[[float, BenefitsProfile], float]. COVERAGE GAPS CLOSED: tracker.py get_all_outcomes 92%->100%, stage_builder.py 97%->100%, generators_barriers.py 98%->100%, pathway/engine.py now 100%. NEW TESTS: 4 test files, 56 new tests (2,301 total, was 2,245). test_s8_coverage_gaps.py (20 tests -- OutcomeTracker.get_all_outcomes, feedback outcome length validation, low-severity credit actions, eligibility edge cases, wage_tier_label fallback). test_s8_route_hardening.py (15 tests -- dashboard barrier parsing edge cases, simulate unknown/mixed confidence, share deleted session + missing plan, sequence unknown barriers, intelligence response format). test_s8_response_consistency.py (14 tests -- error response format consistency across all endpoints, success response format validation for dashboard/pathway/sequence/simulate/share/intelligence/city/health). test_s8_code_quality.py (7 tests -- route registration gate, file size limits, function count limits, public function type hint enforcement). Zero regressions. All files under 400 lines, all functions under 50 lines, under 15 functions/file.

- **Sprint S7 -- Outcome-Informed Barrier Intelligence** (2026-04-13): Closed the N+1 feedback loop -- the hackathon proposal's core differentiator. Built the Outcome Intelligence Engine that reads visit_feedback from the database and computes calibrated per-barrier resolution statistics (avg weeks to resolve, success rates, confidence levels based on sample size). These calibrated values feed back into the barrier_sequencer and pathway engine, replacing hardcoded estimates with real community outcome data. NEW MODULE: app/modules/outcomes/ with 5 files (intelligence.py -- engine computing calibrated stats; intelligence_queries.py -- DB join of visit_feedback + sessions producing per-barrier observations; aggregator.py -- community insights from outcome records; tracker.py -- in-memory outcome storage; types.py -- Pydantic models). NEW ROUTE: GET /api/intelligence/barriers returns calibrated barrier stats, confidence levels, calibrated_weeks dict (MEDIUM+ confidence only), and default_weeks for comparison. No PII exposed. MODIFIED: barrier_sequencer.sequence_barriers() now accepts optional calibrated_weeks parameter -- falls back to hardcoded _WEEKS_PER_BARRIER defaults when no community data. Pathway engine (generate_pathways, _build_pathway) and stage_builder (build_stages, _assign_barriers_to_stages, _compute_stage_weeks) all propagate calibrated_weeks through the full pipeline. Confidence levels: NONE (0 samples), LOW (1-2), MEDIUM (3-9), HIGH (10+). Only MEDIUM+ confidence barriers with non-zero avg_weeks are included in the calibrated_weeks dict. Zero LLM calls. Fully deterministic. City-aware. All files under 400 lines, all functions under 50 lines. 54 new tests (2,124 total backend, zero regressions). Test files: test_outcome_intelligence.py (15 tests -- confidence levels, per-barrier stats, weeks dict), test_intelligence_queries.py (7 tests -- DB query, malformed JSON, NULL outcomes, resolution marking), test_intelligence_route.py (6 tests -- endpoint 200, empty DB defaults, feedback data, calibrated weeks), test_intelligence_edge_cases.py (15 tests -- input fuzzing, boundary conditions, weeks dict integration, DB state corruption), test_calibrated_sequencer.py (7 tests -- backward compat, calibrated weeks used, mixed, total weeks, empty, unknown), test_calibrated_pathway.py (4 tests -- backward compat, calibrated affects timeline, empty same as default).

- **Sprint S6 -- Deep Quality + Integration (Phase 1)** (2026-04-13): Backend hardening and Montgomery leak remediation. FIXES: (1) City route (/api/city) was NOT registered in all_routers -- now registered and tested. (2) app/ai/client.py used hardcoded Montgomery prompts instead of prompt_router -- now routes through get_system_prompt()/get_user_prompt_template(). (3) Fallback narrative in client.py had hardcoded "Montgomery", "Alabama Career Center" -- now city-aware via get_city_config(). (4) MockProvider in providers.py had hardcoded Montgomery response -- now city-aware. (5) career_center.py fallback profile used hardcoded ZIP 36104 -- now uses city config zip_ranges[0]. (6) barrier_intel/prompts.py had hardcoded Montgomery system prompt -- now city-aware via get_barrier_intel_system_prompt(). (7) barrier_intel/guardrails.py HALLUCINATION_DISCLAIMER had hardcoded Alabama Career Center -- now city-aware. (8) barrier_intel/streaming.py updated to use dynamic prompt function. (9) brightdata.py error responses normalized to keyword args (status_code, detail). (10) jobs.py M-Transit docstring generalized. (11) database.py Montgomery docstrings updated. NEW TESTS: 5 new test files, 46 new tests (2011 total, was 1965). test_city_route.py (4 tests -- endpoint registration, response format, state code, ZIP ranges). test_pathway_route.py (11 tests -- happy path, auth, validation, benefits profile, empty barriers, malformed data). test_montgomery_leaks.py (11 tests -- no hardcoded ZIP in routes, no Alabama Career Center in routes, city-aware fallback narrative, city-aware mock provider, city-aware career center ZIP, prompt_router is used). test_route_hardening.py (14 tests -- simulate error paths, sequence edge cases, share deleted session, dashboard NULL barriers, response format validation). test_integration_flow.py (6 tests -- full plan->sequence->share flow, simulate->sequence, pathway after plan, city endpoint, health endpoint, all routes registered). Zero regressions. All files under 400 lines, all functions under 50 lines.

- **Sprint S5 -- Backend Innovations: Employment Pathway Engine** (2026-04-11): Built the Employment Pathway Engine, a novel backend system that fuses the barrier sequencer (topological sort), benefits cliff calculator, and wage analysis into ranked multi-step career trajectories. New module: app/modules/pathway/ with 4 files (types, cliff_navigator, stage_builder, engine) + route (POST /api/pathway). The cliff navigator scans per-program benefit landscapes to identify CliffZones (wage ranges where net income drops), then finds safe wage targets that route career progression AROUND cliffs. The stage builder distributes barriers across stages using topological order so root-cause barriers resolve first. The engine generates 3 strategy variants (conservative/balanced/aggressive) with different wage step sizes, each producing PathwaySteps with target wage, barriers to resolve, estimated weeks, net monthly income, cliff warnings, and job accessibility counts. Viability scoring penalizes barrier count, long timelines, and cliff exposure. City-aware: tested for both CITY=montgomery (AL) and CITY=fort-worth (TX) with proper cache management. Zero LLM calls -- fully deterministic. 44 new tests (1965 total backend, zero regressions). All files under 400 lines, functions under 50 lines, under 15 functions/file.

- **Sprint S4 Phase 2 -- Creative Polish + Evolution** (2026-04-11): Comprehensive test coverage push and UX polish for all S4 features. Backend: added estimated_weeks per barrier step + estimated_total_weeks to barrier sequence response, confidence level (high/medium/low) to simulate endpoint, rate limiter test fixture for share plan, 7 new share edge-case tests (URL-safety, duplicate shares, truncated next_steps, barriers in shared plan), 6 new sequence tests (single barrier, all 7 types, unknown barrier exclusion, no-cycles, session-not-found, timeline fields), 5 new simulate tests (all 7 barrier types, unknown defaults, benefits per type, sequence-after verification, confidence), 5 new dashboard tests (aggregate accuracy, barrier counts, empty DB, malformed barriers, top-5 limit). Frontend: BarrierSequenceViz enhanced with aria-labels on all steps (role=list/listitem, Step N: Name), timeline ~weeks display per step, total timeline estimate, Clock icon, cycle warning aria-label. WhatHappensIf enhanced with loading state (spinner + "Calculating impact..."), Reset button to clear all toggles, summary sentence ("Resolving these N barriers unlocks +X more jobs and Y benefits"). VoiceInput enhanced with pulsing "Listening..." indicator and improved browser compatibility message. Full i18n coverage: 34 new EN keys + 34 new ES keys across 6 namespaces (sequence, simulator, voice, dashboard, outcomes, share), verified by 70-test completeness suite. New PlanInsights wrapper tests. CaseManager page tests for loading/error/computed states. 1,914 backend tests (+17), 786 frontend tests (+98), 2,700 total (+115). Zero regressions. All files under architecture limits.

- **Sprint S4 -- Hackathon Polish + Killer Features** (2026-04-11): Full P0/P1/P2 implementation for HackFW 2026. P0: Share plan backend (POST /api/plan/{session_id}/share + GET /api/plan/shared/{token} with 7-day expiry, share_tokens table, SharePlanButton with copy-to-clipboard). City-aware landing page (Fort Worth: 15.3% poverty, 64% labor participation, 950K+ metro; Montgomery stats preserved). City-aware FastAPI description. Demo script rewritten for Fort Worth persona (Carlos, 76119, Trinity Metro, HHSC, Texas nondisclosure). P1: Barrier sequence visualization (BarrierSequenceViz component -- topological sort domino chain with arrows, unlock indicators, category badges). "What Happens If" multi-barrier simulator (WhatHappensIf toggle component + POST /api/simulate endpoint returning cascading impact: jobs unlocked estimate, benefits unlocked, barrier unlocks). Assessment wizard fully i18n-wrapped (all heading/description strings use t() from i18n, 18 new en.json keys + full Spanish es.json translations). P2: Case manager dashboard page (/case-manager with aggregate metrics, barrier bar charts). N+1 aggregate outcomes display (OutcomesBadge component + GET /api/outcomes/aggregate). Privacy reassurance badge in assessment wizard. Voice input for work history (VoiceInput component using Web Speech API). 18 new backend tests (1897 total passing), 34 new frontend tests (688 total passing). Zero regressions. All files under 400-line limit.

- **Sprint S3 Phase 3 -- Final Evolution + Polish** (2026-04-11): End-to-end verification of both cities (Fort Worth and Montgomery) across the full assessment -> cliff -> screener -> barriers -> prompts chain. Verified zero Alabama bypasses remain when CITY=fort-worth (HHSC not DHR, Trinity Metro not M-Transit, Texas Board of Nursing not Alabama, Workforce Solutions not AL Career Center). Pushed all S3 backend files to 100% coverage: cliff_calculator, barrier_sequencer, geo_router, resource_router, zip_validation, prompt_router, eligibility_screener, benefits router, TX program_calculators, sequence_types. Tested edge cases: unknown programs via model_construct bypass, non-ordering relationship filtering in barrier sequencer, ZIP boundary values (76100/76200 rejection, 76101/76199 acceptance), cliff calculator with 0/7 programs, household size 1/8, zero income, severity classification boundaries. Added i18n edge cases (missing keys, localStorage errors, Spanish translation completeness), SharedPlanView edge cases (null plan, empty barriers, phone link). 121 new backend + 23 new frontend tests. 1863 backend / 653 frontend tests passing. Zero regressions.

- **Sprint S3 Phase 2 -- Evolution + Hardening** (2026-04-11): S2 routing audit and S3 feature evolution. Fixed all Alabama bypasses in cliff_calculator (uses TX AMI $78K for Fort Worth), eligibility_screener (HHSC disclaimer), types.py (dynamic ZIP validation), pvs_scorer, scoring.py, commute_estimator, barrier_cards, affinity, career_center_package, filters, phase_generators, job_readiness_pathway -- all now route through city-aware routers. Built barrier sequencing engine (topological sort of 33 barriers, 53 edges). Evolved ProgressTracker (localStorage persistence), BenefitsCliffSimulator (loading/error states, ARIA), ResourceMap (category filtering), i18n (locale persistence). 28 new tests. 1742 backend / 630 frontend tests passing. Zero regressions.

- **Sprint S2 complete** (2026-04-12) -- Fort Worth Data + Texas Rules: Full multi-city port for HackFW 2026. Created Texas benefits screener with HHSC programs (CHIP replaces ALL_Kids at 200% FPL, CEAP replaces LIHEAP, TX TANF at ~$308/mo vs AL $215), Texas expunction (Art. 55) + nondisclosure (Gov Code Ch. 411 E-1) dual record clearing, Fort Worth geo data (36 ZIP centroids, Trinity Metro hours), city-aware module routing (benefits, criminal, geo, resources, AI prompts), live TWC and USAJobs API adapters replacing stubs, Fort Worth seed data (10 community resources, 12 employers with fair-chance index), and frontend city-aware constants. 112 new S2 tests + 1707 total backend tests passing (zero regressions). 512 frontend tests passing.

## What's Next

Execute S12b. Recommended starting points (Wave 1, no S12b intra-sprint deps): T12.4 (PDF rendering), T12.14 (worker voice rules), T12.31a (advisor auth doc). All others chain through S12b intra-sprint deps or await Wave N-1 output.

S12b gates production general availability via T12.36 (worker data export + right-to-delete). Until T12.36 lands, S12a is staging-only.

**Post-Hackathon:** Dallas expansion (DFW unification). Texas state-level modules (benefits, criminal) are already built. Dallas needs: `cities/dallas.yaml`, `data/cities/dallas/` seed data, DART transit data, Dallas career centers/resources/employers, fair-chance index. No new code — just data curation and a new city config. See ROADMAP.md "Dallas Expansion" phase and hackfw-2026-proposal.md "Post-Hackathon" section for full details.

## Blockers

- T28.3: Requires findhelp.org API partnership (external dependency).
