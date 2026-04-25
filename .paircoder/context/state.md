# Current State

> Last updated: 2026-04-24

## Active Plan

**Plan:** plan-2026-04-s13-platform-qc
**Type:** chore
**Title:** S13 — Platform-Wide QC + Submission Readiness
**Status:** Planned + decisions locked (0/128 tasks, 1,545 Cx, ~692K token estimate)
**Branch:** not yet cut
**Current Sprint:** S13

## Previous Sprints (summary)

- **Sprint S12b** — Worker Companion Value Extensions: PDF rendering, resume + cover-letter builders (LLM-gated, injection-defended), reminder engine + cooldown, plan refresher + 20-row history cap, transactional appointment emails + signed manage-link key rotation, jobs kanban, documents pages, advisor inbox (city-scoped), past-appointment auto-advance, module status contracts, weekly review, compliance gate (export + right-to-delete + retention sweep). 25/25 done, 510 Cx, GATE green, GA unblocked.
- **Sprint S12a** — Worker Companion Foundation: 26/26 done, GATE green, staging-only until S12b T12.36 (now landed). Migration infra, DB-backed outcomes, feature flags + audit, APScheduler, day boundary, appointments + jobs + documents + plan modules, digest composer, stall detector, nightly orchestrator, daily-digest page, appointments page. Detail in `.paircoder/archive/state-s12a.md`.
- **Sprint S11** — "People Like You" Community Insights (deterministic, city-aware, no-LLM). Detail archived.
- **Sprint S10** — Demo seed + full pipeline verification. Detail archived.
- **Sprint S9** — Wired the intelligence loop end-to-end (calibrated_weeks → pathway). Detail archived.
- **Sprint S8** — Cross-module integration verify + deep polish. Detail archived.
- **Sprint S7** — Outcome-Informed Barrier Intelligence (N+1 loop). Detail archived.
- **Sprint S6** — Backend hardening + Montgomery leak remediation. Detail archived.
- **Sprint S5** — Employment Pathway Engine (cliff-aware multi-step). Detail archived.
- **Sprint S4** — Hackathon polish + killer features (share, sequence viz, what-if simulator, case-manager dashboard, voice input, i18n). Detail archived.
- **Sprint S3** — Texas/Fort Worth audit + S3 evolution. Detail archived.
- **Sprint S2** — Fort Worth Data + Texas Rules: 18/18 done. Detail archived.
- **Sprint S1** — City Framework Scaffold: 8/8 done. Detail archived.

Older sprint task tables and session histories (Sprints 7 — 31) are in `.paircoder/archive/state-pre-s1.md`. S12a per-session entries plus S2 — S11 detail are in `.paircoder/archive/state-s12a.md`.

## What Was Just Done

- **Wave 0 complete (T13.1-T13.5 + T13.128 partial).** QC foundation in place: config + suite template + README, demo seed extension, reset CLI, axe-core install, fake-clock harness, staging deploy artifacts. End-to-end smoke verified: fresh DB → migrate → qc_reset wipes & reseeds 10 demo sessions in 2.76 ms. T13.128 needs `fly deploy` from a user-authed shell to complete (runbook ready). 5/128 tasks done; Tier-1 browser suite authoring (T13.10-T13.52) is unblocked.
- **T13.3 done** — QC Reset CLI (`scripts/qc_reset.py`) wipes every demo-flagged row across the worker-companion schema and reseeds via the T13.2 factory in <5s. 16 tests across cycles 1-7. Wave 0B complete.
- **T13.5 done** (auto-updated by hook)

- **T13.4 done** (auto-updated by hook)

- **T13.2 done** (auto-updated by hook)

- **Wave 0A complete**: T13.2 + T13.4 + T13.5 done; T13.128 partial (runbook + scaffold landed; user runs `fly deploy`)
- **T13.1 done** (auto-updated by hook)

### 2026-04-24 — T13.3 driver session — QC Reset CLI

Built `scripts/qc_reset.py` so QC suites can land on a deterministic demo baseline between runs.

**Files created:**
- `scripts/qc_reset.py` (183L) — CLI hub. `main(db_path, *, reseed, now)` returns `{"deleted": {table: count, ...}, "reseeded": bool, "sessions_after_reseed": int}`. Argparse layer accepts `--db-path` (defaults to `app.core.config.Settings.database_url`) and `--no-reseed`. Pretty-prints a per-table delete summary. Bootstraps `sys.path` so the script runs from the repo root or any cwd.
- `scripts/_qc_reset_wipe.py` (134L) — pure-SQL wipe spoke. Single transaction; per-table delete helpers; demo-id discovery + `_advisor_audit` placeholder preservation.
- `backend/tests/test_qc_reset.py` (454L) — 16 tests across 7 cycles (smoke, cascade, idempotency, non-demo sentinel, determinism, speed, CLI argparse).

**Demo-scoped tables wiped (18):**
- Session-keyed (cascade): `appointments`, `job_applications`, `resume_versions`, `daily_progress_snapshots`, `engagement_events`, `plan_history`, `outcomes_records`, `reminder_cooldowns`, `worker_unavailability`, `feedback_tokens`, `visit_feedback`, `resource_feedback`, `record_profiles`, `share_tokens`.
- Hash-keyed: `compliance_audit` (filtered by `sha256(session_id)` for demo sessions).
- Demo-prefix in shared tables: `advisor_tokens` (`advisor_id LIKE 'adv-demo-%'`), `sendgrid_events` (`message_id LIKE 'demo-%'`).
- Direct `demo=1` filter: `sessions` (preserving `_advisor_audit` placeholder; its child engagement events are still wiped).

**Non-demo guard:** every DELETE is scoped by `demo = 1` (excluding the placeholder), the demo-session-id list, or a deterministic `demo-` prefix. `used_tokens` (m004) intentionally not wiped — no session linkage and not seeded by the demo factory.

**Test results:** 16/16 pass in 0.59s. Full demo-seed suite (43 tests across 4 files) also green — no regression.

**Speed measured:** 2.76 ms for full reset+reseed on a populated demo DB (well under the 5s budget).

**Acceptance criteria (T13.3 spec):**
- `python scripts/qc_reset.py` truncates every `demo=1` scoped row (verified via `test_wipe_clears_every_demo_scoped_table`, `_compliance_audit_for_demo_sessions`, `_demo_advisor_tokens`, `_demo_sendgrid_events`).
- Reseeds via T13.2 factory (`test_main_wipes_demo_sessions_and_reseeds`).
- Idempotent: `test_reset_is_idempotent_on_clean_db` + `test_reset_twice_produces_stable_state`.
- Does NOT touch non-demo data: `test_non_demo_session_and_children_survive_reset` + `test_non_demo_advisor_token_survives_reset` + `test_advisor_audit_placeholder_session_is_preserved`.
- Runs in <5s: `test_reset_runs_under_five_seconds` (2.76 ms measured).
- `bpsai-pair arch check` passes (zero errors; warnings only on file size — `qc_reset.py` 183L vs 150L tool default warning, well under the 400L project error limit per `.claude/rules/architecture.md`).

**Wave 0B complete.** All 6 Wave 0/0A/0B foundation tasks now landed (T13.1, T13.2, T13.3, T13.4, T13.5; T13.128 still pending user `fly deploy`). Tier-1 browser suite authoring (T13.10–T13.52) unblocked.

### 2026-04-24 — Wave 0A complete (T13.2 + T13.4 + T13.5 + T13.128 partial)

Four driver agents ran in parallel against the foundation tasks:
- T13.2: demo seed extension (compliance + weekly + advisor + reminders); +14 tests; module-status coverage assertion live.
- T13.4: axe-core declared in frontend/package.json (was transitive only); 946 frontend tests pass.
- T13.5: fake-clock harness via freezegun; 10 new tests; one existing test migrated as proof.
- T13.128: deploy artifacts (Fly.io fly.toml, smoke script, runbook) — staging stand-up still requires `fly deploy` from a user-authed shell. Runbook AC checked; "deployed at URL" + "smoke 200s" ACs pending user action.

Backend suite: 3267 pass / 2 pre-existing fails (test_contract_credit_api JWT, test_evidence_collector UTC midnight) — neither touched by Wave 0A. Frontend: 946/946.

Wave 0A progress: 5/6 (T13.1 + T13.2 + T13.4 + T13.5 done; T13.128 partial). Wave 0B: T13.3 reset CLI is the last foundation piece.

### 2026-04-24 — T13.2 driver session — Demo Seed Extension (compliance + weekly + advisor + reminders)

Extended `app/demo_seed_s12b.py` so every demo session carries QC-coverage state for compliance, weekly review, advisor inbox, and reminder modules. Decomposed into hub-and-spoke to satisfy arch limits.

**Files created:**
- `backend/app/_demo_seed_qc.py` (80L) — QC hub: orchestrates compliance + engagement spokes per session.
- `backend/app/_demo_seed_compliance.py` (90L) — `feedback_tokens` (active + expired) + `compliance_audit` baseline rows (`export_requested` + `export_downloaded` per session, hashed session id matches `app.modules.compliance._audit`).
- `backend/app/_demo_seed_engagement.py` (249L) — engagement window (varied by stall state), sendgrid `open` events, reminder cooldowns + opt-out (`reminders_auto_disabled`), and one `advisor_tokens` row per city (deterministic plaintext exposed via `advisor_token_plaintext` for QC harness use).
- `backend/app/_demo_seed_rows.py` (187L) — extracted per-row insert helpers (appointments, applications, resume + cover letter, snapshots, outcomes) so the seed hub stays under arch limits. Resume helper now plants BOTH a `resume` and a `cover_letter` row so `cover_letter_builder.nightly_status` reports non-`unknown` for QC coverage.
- `backend/tests/test_demo_seed_qc.py` (313L) — 14 new tests for cycles 7-12 (compliance, weekly, advisor, reminders, module-status coverage, determinism + idempotency).
- `backend/tests/_demo_seed_qc_helpers.py` (104L) — shared fixture + snapshot helpers (`fresh_db`, `apply_m005`, `apply_through_m007`, `qc_seed_snapshot`).

**Files modified:**
- `backend/app/demo_seed_s12b.py` — collapsed to hub (170L). Per-row helpers moved out; QC seed spoke called per session via `_seed_qc_state_if_schema_ready` (gated on m006 + m007 table presence so legacy callers without those migrations still work).
- `backend/tests/test_demo_seed_s12b.py` — slimmed to base S12b cycles 1-6 (267L), now imports fixtures from `_demo_seed_qc_helpers`.

**Test results:** 26 tests across the two files, all passing in 0.46s. Full backend suite: 3257 pass / 2 fail (both pre-existing carry-overs documented in state.md: `test_contract_credit_api` JWT import + `test_evidence_collector` UTC midnight flake) / 2 skipped. Net delta: +14 tests.

**Acceptance criteria (T13.2 spec):**
- Each of the 10 demo sessions carries state for every module required by any QC suite (verified via `test_module_status_keys_have_at_least_one_nonunknown_session`).
- Seed is deterministic (`test_seed_is_deterministic_across_fresh_dbs` passes — two fresh DBs seeded with the same `now` produce byte-identical row tuples).
- Seed is idempotent (`test_seed_is_idempotent_on_qc_state` passes — re-runs into the same DB do not mutate any payload).
- Coverage assertion: every module the live `status_collector.collect_all` reports has at least one demo session whose health is non-`unknown` (`resume_builder`, `cover_letter_builder`, `applications`, `reminder_engine`).
- `bpsai-pair arch check` passes (zero errors across all 8 files; three warnings on file size, all comfortably under the 300-line error threshold).

**Schema gaps hit:** None. All required tables (feedback_tokens, compliance_audit, advisor_tokens, engagement_events, reminder_cooldowns, sendgrid_events) already exist in m001 + m002 + m006 + m007.

**Module status keys covered:** `resume_builder`, `cover_letter_builder` (NEW — required cover_letter doc_type seeding), `applications`, `reminder_engine`. The aggregator iterates these from `status_collector._MODULES`; the test reads the live list so any future module addition automatically ratchets the assertion forward.

### 2026-04-24 — T13.5 done — fake-clock harness

Built `backend/tests/_fake_clock.py` (test-only) on top of `freezegun==1.5.5` (added to `requirements.txt` under a "test-only dependencies" comment). Public API: `freeze_time(iso_str_or_dt)` context manager yielding a `FrozenClock` controller with `.advance(seconds_or_timedelta, scheduler=None)`, `.move_to(instant, scheduler=None)`, and `.fire_pending(scheduler)`. APScheduler integration walks `scheduler.get_jobs()` and synchronously fires any trigger whose next-fire-time falls inside the (start, now] window of the advance — no scheduler thread needed, deterministic by construction. Verified with cron (`Sun 23:59`) + DateTrigger smoke tests. Tests: 10 in `tests/test_fake_clock.py` (all green, stable across 3 reps). Migrated `test_export_token_expires_after_24h` in `test_compliance.py` from `now=` injection to `freeze_time + clock.advance(timedelta(hours=25))` — exercises the production `datetime.now(timezone.utc)` code path directly. Authoring docs in `backend/tests/README_fake_clock.md`. arch check clean on harness + harness tests; pre-existing `test_compliance.py` size/function violations are unchanged (645→646 line delta from migration). Wave 0 progress: 2/6.

**What's next:** Wave 0 remaining tasks (T13.2 demo seed extension, T13.3 reset CLI, T13.4 axe-core install, T13.128 stand up staging) can run in parallel as independent driver sessions. Once Wave 0 lands, Tier-1 browser suite authoring (T13.10–T13.52) unblocks.

### 2026-04-24 — T13.1 done — QC foundation files

Created `.paircoder/qc/config.yaml` (dev/staging/prod environment profiles), `.paircoder/qc/suites/_template.qc.yaml` (full schema reference with all six step types documented inline), and `.paircoder/qc/suites/README.md` (authoring conventions, canonical tag list, invocation paths). Divona smoke-load passed all four schema checks. arch check clean. Wave 0 progress: 1/6.

### 2026-04-24 — S13 QC + Submission Readiness planned (/pc-plan)

Authored `plans/backlogs/backlog-sprint-s13-platform-qc.md` (126 tasks across 12 phases, 1,497 Cx, dry-run clean). Created plan `plan-2026-04-s13-platform-qc` and registered all 126 tasks with full task files under `.paircoder/tasks/T13.*.task.md`.

**Scope:** QC infra (8), Tier-1 browser suites (43 — worker 30 / advisor 5 / admin 4 / unauth 4), Tier-2 backend e2e (18), Tier-3 exploratory sweeps (7), Tier-4 cross-cutting quality (15), Tier-5 security+compliance (12), Tier-6 cross-module integrity (6), Tier-7 submission readiness (13), continuous QC wiring (4).

**Budget:** 671K token estimate → bpsai-pair recommends splitting into ~21 batches of ≤50K tokens. Priority split: P0=27 / P1=65 / P2=34.

**Decisions locked (2026-04-24):** staging in scope (T13.128 added), submission targets judges + prod, error tracking now (Sentry), visual regression in scope, BOTH divona + Playwright headless (T13.129 added), WCAG AAA target, legal pages authored fresh. Tasks T13.79–T13.82 escalated to AAA criteria; T13.115/T13.121/T13.123 scope expanded; T13.6/T13.83 priority raised.

### 2026-04-24 — /reviewing-and-fixing pipeline on S12b branch

Ran full review-and-fix pipeline across the S12b branch. Landed:
- Doc cleanup (c7767c6): archived S12a session detail, collapsed state.md 549→105 lines.
- Stage-2 fix bundle (9f88bc0, 75c2895, 95f35d7, 4c8207a): unsubscribe signer + GET handler (CAN-SPAM), async offload of reminder scan, injection-filter scope expansion, logging/defaults/sanitization/audit-ordering fixes.
- Simplify pass (18f7df2): stripped narrative comments from review output, reused `hash_session_id` helper, renamed misleading log key, collapsed SELECT+INSERT to `INSERT OR IGNORE`.
- Test TTL fix (91dc9e0): `_NOW` in `test_compliance` now uses `datetime.now(timezone.utc)` to avoid hardcoded-date drift.

Deferred to S13: APP_HOST helper extraction, shared builder free-text helpers, token-system unification, advisor-audit schema consolidation, rate-limiter consolidation, unsubscribe double-connection refactor.

### 2026-04-23 — Sprint S12b complete (25/25 tasks, 510 Cx, GATE green, production GA UNBLOCKED)

**Top-level deliverables:**

- **PDF rendering** (T12.4): SSRF-guarded WeasyPrint pipeline + print-friendly default template; weasyprint + markdown pinned in `requirements.txt`; native deps wired in `Dockerfile`.
- **Worker voice + document templates** (T12.14): `apply_worker_voice` rule chain (dash/hedge/quote/hyphen stripping + dignified substitutions, F-K grade <9), Jinja2 resume + cover-letter templates with autoescape.
- **Resume builder** (T12.15) and **cover-letter builder** (T12.16): LLM-gated (default off) behind `ENABLE_AI_GENERATION`, injection-defended via `injection_filter`, fair-chance branch reads `criminal.fair_chance_index`, persisted to `resume_versions` with monotonic per-doc-type counters.
- **Reminder engine** (T12.19): wired into nightly orchestrator with cooldown + opt-out (audit-row pattern) + kill-switch preflight; ports the legacy ops/lib templates.
- **Plan refresher** (T12.24): trigger detection (`stall_hard` or `barrier_resolved` window), checklist carry-forward by `(phase, category, title)` triple, `plan_history` archive with 20-row per-session cap, dual-write to `sessions.previous_plan` (deprecation bridge for S13).
- **Past-appointment auto-advance** (T12.25a): nightly step 2.5; `scheduler.mark_missed` + audit + worker notice + outcome record (filtered out of stall clock by T12.18).
- **Module status contracts** (T12.25b): `nightly_status` on documents/jobs/engagement; `status_collector.collect_all` aggregator; `DigestResult.module_status`.
- **Weekly review composer** (T12.22a): per-session 7-day window; funnel + engagement + barriers-cleared sections; Sunday branch in nightly orchestrator dispatches via `reminder_engine.send_digest`.
- **Transactional appointment emails** (T12.10a): scheduler job handler factored to `scheduler_jobs.appointment_reminders_handler`; 24h + 1h reminders.
- **Signed manage-appointment links** (T12.10b): `appointments_manage` router registered before `appointments` to dodge the `/{appointment_id}` catch-all; HMAC-SHA256 + kid + 7-day overlap window for key rotation.
- **Engagement API** (T12.21): `/api/engagement/{events, preferences, send-now, unsubscribe}`; admin-rate-limited send-now; uniform 401 on token failures.
- **Documents API** (T12.17): 7 endpoints under `/api/documents`; PDF streaming; use-counter hook from `jobs_applications.create()`.
- **Jobs Tracker page** (T12.27): dnd-kit kanban with funnel sidebar + conversion rates; resume-version PDF link + `generation_method` badge.
- **Documents pages** (T12.28): `/documents/resume` + `/documents/cover-letters` over T12.17 API; markdown preview + version history + download.
- **Navigation + stall alert banner** (T12.30): shared `NavBar` (5 links), HARD-only `StallAlertBanner` with 24h localStorage dismiss.
- **Advisor inbox** (T12.31 + T12.31a): city-scoped stalled-session list + drill-through + personal-note dispatch; advisor auth model (mw_adv_<base58>, row-backed `advisor_tokens` with instant revoke); cross-city → 403; per-advisor rate limit; SHA256 audit hash.
- **Compliance gate** (T12.36): worker data export + full delete + selective tombstone + retention sweep wired into nightly; `compliance_audit` table with hashed `session_id_hash`; `confirm: "DELETE"` speed-bump; `COMPLIANCE_TOKEN_SECRET` rotation; `docs/ops/compliance-operations.md` runbook. **Unblocks production GA.**
- **Worker-companion demo seed** (T12.34): 5 sessions × 2 cities spanning none/soft/medium/hard/breakthrough; activates the T12.12 community-funnel `demo` guard.
- **S12b end-to-end gate** (T12.32b): 11 city-symmetric flows + 6 cross-cutting security assertions; 19 tests in 2.15s.
- **S12b integration gate + rollout runbook** (T12.35b): 26 gate assertions across 4 test files; admin-key scan; `docs/ops/s12b-rollout.md` (13 sections including Production GA Confirmation).

**Migrations added (4):**
- `m004_used_tokens` — atomic single-use registry for HMAC tokens (appointment manage-links, compliance export links).
- `m005_sessions_demo` — `sessions.demo BOOLEAN NOT NULL DEFAULT FALSE`; activates pre-existing T12.12 funnel guard.
- `m006_compliance_tombstones` — `compliance_audit` table + `deleted_at` / `deleted_reason` tombstones on `record_profiles`, `resume_versions`, `engagement_events`.
- `m007_advisor_tokens` — `advisor_tokens` table + partial active-token index `WHERE revoked_at IS NULL`.

All four round-trip cleanly (apply → rollback → re-apply); `schema_migrations` tops out at version 7.

**Test count delta:**
- Backend: **3018 → 3226 pass** (1 skipped, 2 pre-existing carry-overs unchanged: `test_contract_credit_api` JWT import, `test_evidence_collector` outcomes UTC/local-date midnight flake — both fail on clean checkout).
- Frontend: **911 → 946 pass**.

**GATE outcome:** 25 pass / 1 skip / 0 fail. Admin-key scan clean across all 20 new S12b files. Production GA UNBLOCKED as of 2026-04-23.

**Carry-overs (10) — do not block GA, tracked for S13:**

1. `app/routes/__init__.py` has 27+ imports (pre-existing arch warning; warning-only).
2. `sessions.reminders_enabled` / `.email` / `.city` not first-class columns — handled via row patterns; promote to columns + indexes.
3. `sessions.previous_plan` deprecated by `plan_history` dual-write; drop in S13.
4. `_call_llm` placeholders (resume + cover-letter) gated by `ENABLE_AI_GENERATION=false`; flip requires DPA per runbook §3.
5. `test_evidence_collector::test_outcomes_logged_in_range` — UTC/local-date midnight flake; own ticket.
6. `test_contract_credit_api::test_provider_simple_input_fields_unchanged` — sibling repo missing `jwt` import; environmental.
7. `DigestResult.module_status` exposed but not yet rendered into digest body — advisor-inbox seam consumes it.
8. Advisor token operator CLI — currently SQL-only; CLI is a future ticket.
9. Frontend has no `test` script in `package.json` — invoke vitest directly; script-add chore deferred.
10. Stall banner uses `counts.stall > 0` proxy — awaits backend exposing `stall_level` on digest preview.

Per-task one-liners are no longer in this file — see git history (`sprint/s12b-value-extensions`) and `.paircoder/tasks/plan-2026-04-s12b-value-extensions/`.

## What's Next

S12b is complete and production GA is unblocked. Recommended next steps:

- **Merge `sprint/s12b-value-extensions` to `main`** after PR review.
- **Scope S13** to drain the 10 carry-overs above. Best candidates for first wave:
  - Promote `sessions.reminders_enabled` / `.email` / `.city` to first-class columns + indexes (carry-over #2).
  - Drop `sessions.previous_plan` after migrating readers off the dual-write (carry-over #3).
  - Expose `stall_level` on the digest preview endpoint and swap the banner mapping (carry-over #10).
  - Add `npm test` script in `frontend/package.json` (carry-over #9).
  - Advisor token issuance/revocation operator CLI (carry-over #8).
  - Render `DigestResult.module_status` into the digest body (carry-over #7).
  - Fix `test_evidence_collector` UTC/local-date midnight flake (carry-over #5).
- **Post-Hackathon:** Dallas expansion (DFW unification). Texas state-level modules (benefits, criminal) are already built. Dallas needs `cities/dallas.yaml`, `data/cities/dallas/` seed data, DART transit data, Dallas career centers/resources/employers, fair-chance index. No new code — just data curation and a new city config. See ROADMAP.md "Dallas Expansion" phase and `hackfw-2026-proposal.md` "Post-Hackathon" section.

## Blockers

- T28.3: Requires findhelp.org API partnership (external dependency).
