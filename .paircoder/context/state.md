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

- **T13.68 done** (auto-updated by hook)

- **T13.67 done** (auto-updated by hook)

- **T13.67 done** — Demo Seed Every-Feature Check. New `backend/tests/test_demo_seed_coverage.py` (503L, 6 tests) generalises and strengthens the T13.2 status-collector coverage assertion into a four-layer drift guard: (1) `test_status_collector_modules_have_demo_coverage` — every module wired into `status_collector._MODULES` (resume_builder, cover_letter_builder, applications, reminder_engine) returns non-`unknown` for ≥1 of the 10 demo sessions after `seed_worker_companion_sessions`; pre-asserts session count == 10 and that the collector returns the expected module-name set; (2) `test_session_scoped_tables_seeded` — introspects every session-scoped table (the same `session_id`-column / FK-to-sessions(id) inventory T13.70 uses, 14 tables on a fully migrated DB), asserts each is either populated by the seed (8 tables: `appointments`, `daily_progress_snapshots`, `engagement_events`, `feedback_tokens`, `job_applications`, `outcomes_records`, `reminder_cooldowns`, `resume_versions`) OR explicitly listed in `UNSEEDED_TABLE_ALLOWLIST` with a one-line rationale (6 allowlisted: `plan_history`, `record_profiles`, `resource_feedback`, `share_tokens`, `visit_feedback`, `worker_unavailability` — all are flows the worker companion seed deliberately does not exercise because they require live worker action); also asserts no overlap between the seeded set and the allowlist; (3) `test_canonical_module_directories_documented` — walks `backend/app/modules/` and pins the production-module list at 17 directories: `advisor`, `appointments`, `benefits`, `common`, `compliance`, `credit`, `criminal`, `data`, `documents`, `engagement`, `feedback`, `jobs`, `matching`, `outcomes`, `pathway`, `plan`, `resources`. Adding a new `backend/app/modules/<name>/` dir without an entry in the test's `PRODUCTION_MODULES` dict fails this test (verified by smoke-creating a `zzdrifttest` dir and confirming the assertion fires). Removing a documented module without removing it from disk also fails (drift-in-the-other-direction guard). (4) `test_every_production_module_seeded_or_excluded` — every `PRODUCTION_MODULES` entry must be classified by `_module_seed_classification` as one of {`feature` (8 dirs whose tables get seed rows: appointments / compliance / documents / engagement / jobs / outcomes / plan / criminal), `status` (3 dirs whose modules are wired into status_collector: documents / jobs / engagement — overlaps with `feature`), `infrastructure` (8 dirs on `INFRASTRUCTURE_MODULES` allowlist: `common` types-only, `data` types-only, `credit` legacy stub, `matching` pure compute over shared tables, `pathway` reads via profile + outcomes, `benefits` reads sessions.benefits_profile, `feedback` token table seeded but module flow not in nightly, `resources` shared lookup, `advisor` advisor_tokens seeded but inbox demo state via outcomes city tag)}; uncovered modules surface in the failure message. Plus (5) `test_inventory_documentation_quality` — defensive guard that every PRODUCTION_MODULES / INFRASTRUCTURE_MODULES / UNSEEDED_TABLE_ALLOWLIST entry has a non-trivial reason (>5 chars for descriptions, >20 chars for rationales); (6) `test_status_collector_modules_belong_to_documented_dirs` — cross-check that every status_collector module's backing directory is in `PRODUCTION_MODULES`. **No coverage gaps found** — the existing seed already exercises every status_collector module (resume_builder green via cover_letter spoke, cover_letter_builder green via the same insert, applications green via insert_application, reminder_engine green via seed_engagement_window + seed_reminder_state). No demo seed extension was required. **Test results:** 6/6 new tests pass in 0.07s; full demo-seed regression `tests/test_demo_seed*.py` 49/49 pass with no regressions. arch check: 0 errors (warning only at 503L > 400, well under the 600 test-file error ceiling — see `.claude/rules/architecture.md`); all functions ≤50L after extracting `_classify_table_seed_state` + `_module_seed_classification` + `_module_directories` helpers + lifting the inventory dicts to module-level constants. Files: `backend/tests/test_demo_seed_coverage.py` (new, 503L). The drift guard now means a future PR cannot add a `backend/app/modules/<new_module>/` directory without either (a) extending the seed to cover it, (b) wiring it into status_collector, or (c) adding an explicit `INFRASTRUCTURE_MODULES` allowlist entry with a documented "no seed needed" reason.

- **T13.66 done** (auto-updated by hook)

- **T13.64 done** (auto-updated by hook)

- **T13.62 done** (auto-updated by hook)

- **T13.61 done** (auto-updated by hook)

- **T13.62 done** — Key Rotation Overlap. New `backend/tests/test_key_rotation_overlap.py` (369L, 7 tests) pins the kid-based 7-day overlap contract for `app.modules.appointments.tokens` (S12b T12.10b). Tests: (1) `test_current_kid_always_accepts` — sign with current kid, verify immediately + 6 days later (within TTL); (2) `test_old_kid_accepts_within_overlap` — hand-mint a `kid="old"` token signed under `APPOINTMENT_TOKEN_SECRET_OLD`, verify with both env vars set; (3) `test_old_kid_rejects_after_overlap` — same old-kid token, OLD env var unset → `TokenInvalid` (not expiry); (4) `test_both_kids_accept_during_overlap` — current-kid + old-kid tokens both verify while both secrets set; (5) `test_unknown_kid_rejected` — `kid="future"` token signed under NEW secret must reject; (6) `test_kid_in_payload_not_signature` — flipping `kid="old"` → `kid="current"` in JSON without re-signing must invalidate the signature; (7) `test_rotation_window_documented` — pins `KEY_ROTATION_OVERLAP_DAYS = 7` constant aligned to `_DEFAULT_TTL_SEC`. **Bug found & fixed:** the original `_decode_and_verify_signature` accepted ANY non-"old" kid (including unknown values like `"future"`) via fall-through to the full active-secret pool, which means an attacker who could stamp a forged kid would ride on whichever active secret matched their signature. Added `_KNOWN_KIDS = frozenset({"current", "old"})` whitelist + early `TokenInvalid("unknown kid")` reject; the `kid="current"` fall-through to all active secrets is preserved (required so a token minted seconds before rotation cutover still verifies under what is now OLD). Also added the `KEY_ROTATION_OVERLAP_DAYS = 7` module-level constant to pin the runbook value (`docs/ops/appointment-token-rotation.md` §2 step 5) so docs and code cannot drift. **Sibling kid-rotation modules audited:** `app/modules/compliance/_export_tokens.py` and `app/modules/engagement/unsubscribe_tokens.py` carry the same kid-fall-through pattern — they are NOT modified here (out of task scope; T13.62 is appointment-tokens-specific) but should get parallel hardening + parallel tests in a follow-up. Modules without kid rotation: `app/core/advisor_auth.py` (DB-row tokens, separate revocation model). **Test results:** 7/7 new tests pass; 17/17 existing `test_appointment_tokens.py` still pass (no regression — kid-missing-defaults-to-current + old-secret-set-rotation-still-valid + missing-old-invalidates all green); 46/46 across all token-suite tests. arch check on test file: 0 violations. arch check on `tokens.py`: 0 errors (1 pre-existing warning at 288L re. project's 150L warn threshold; well under 400L error). Files modified: `backend/app/modules/appointments/tokens.py` (+24L net for constant + whitelist + tightened verify); `backend/tests/test_key_rotation_overlap.py` (new, 369L).

- **T13.66 done** — Weekly Review Window Boundaries. New `backend/tests/test_weekly_review_boundaries.py` (422L, 9 tests; 1 of which is parametrized 2x for 10 collected cases) pins boundary policy of the T12.22a composer (`backend/app/modules/plan/weekly_review.py`) at edges that `test_weekly_review.py` does not cover: full-window happy path (5/7 days engagement → all 3 sections populated, no quiet-week fallback), no-engagement-data graceful empty digest (returns valid `WeeklyReview` object with zeroed sections + "quiet week" markdown — never None / KeyError / missing attribute), mid-week session created Wed (composer trusts caller's `date_range` and does NOT truncate by `sessions.created_at`; earlier events simply don't exist due to FK), inclusive-on-both-ends boundary (events at exactly `window_start 00:00:00 UTC` and `window_end 23:59:59 UTC` both counted, parametrized lower+upper), event-1-second-before-start + 8-days-ago both excluded, DST spring-forward 2026-03-08 + DST fall-back 2026-11-01 both yield 8 calendar days seeded = 8 events counted (a buggy `now - timedelta(hours=168)` would drop one event in the missing 02:00→03:00 spring-forward slot or over-count by one in the fall-back gain — UTC date bounds are DST-safe by construction), plus a 24-hour-per-transition-day belt-and-suspenders that asserts every UTC hour of the spring-forward day is captured. **Boundary policy pinned by these tests:** `date_range = (window_start, window_end)` is closed on both ends at the calendar-date level; composer's `_to_window_start_iso` (uses `time.min`) and `_to_window_end_iso` (uses `time.max`) expand to UTC start-of-day and end-of-day microseconds; SQL uses `created_at >= start_iso AND created_at <= end_iso`. **DST handling: calendar-day based via UTC** — never 24-hour-rolling, never local-time-anchored. `send_weekly_review` (the orchestrator spoke `backend/scripts/_nightly_weekly.py`) computes `window_start = for_date - timedelta(days=7)` so the inclusive window is always 8 calendar days; this 8-day-not-7-day choice is covered by the spring-forward + fall-back tests' "8 events seeded → 8 counted" assertion. **No bugs found in the composer.** Every test wraps its time-sensitive setup in `_fake_clock.freeze_time` (T13.5) so the suite is deterministic regardless of when CI runs. Test results: 9 pass / 0 fail in 0.18s; combined `test_weekly_review.py` + `test_weekly_review_boundaries.py` + `test_orchestrator_full_run.py` = 31/31 pass / no regressions. arch check exit 0 (file 422L > 400 warn but well under 600 error threshold; warning is informational, not blocking — see `.claude/rules/architecture.md`). Composer + spoke unchanged — no production code modifications were necessary; the existing UTC-day-bounds implementation already handles every edge case the brief flagged.

- **T13.64 done** — Feature Flag State Machine Race. New `backend/tests/test_flag_race.py` (310L, 6 tests) pins concurrent-toggle + concurrent-read invariants on `app.core.feature_flags`. Architecture confirmed via source audit: `_RUNTIME_OVERRIDES` is a plain dict guarded by a single `threading.Lock` (`_LOCK`), `is_enabled` reads under the lock, `set_flag_runtime` writes under the lock then writes one row to `feature_flag_audit` (sqlite, `id INTEGER PRIMARY KEY AUTOINCREMENT`). **No TTL cache exists** — the dict IS the cache, every read is live. Test 5 documents this and asserts the module exposes no `TTL`/`CACHE_TTL` constant; if a future refactor adds one, the test fails until the constant is pinned ≤30s. Tests: (1) single toggle = 1 audit row + flag flipped; (2) 100 reader threads + 1 toggler synced via `threading.Barrier` — all reads return real bools, never garbage, set ⊆ {True, False}, final state matches the writer; (3) 8 concurrent toggles → audit-row count == 8 (last-writer-wins on flag value, but every attempt audited); (4) toggle-then-read in same process → no stale read; (5) no-TTL invariant pinned via `vars(ff)` introspection; (6) 50-toggle burst with rate-limiter patched out → 50 audit rows + every reason string accounted for. **No bugs found.** Probed default-config sqlite at 100 concurrent inserts → 0 errors / 100 rows; CPython GIL + sqlite3's internal serialization keeps the audit path safe at burst sizes the production rate limiter (10/hour) would never allow anyway. The audit-write-outside-lock pattern is benign because the dict update happens under the lock and audit ordering by row id is consistent with insertion order. **Test results:** 6/6 pass in 2.5s, stable across 5 consecutive runs; combined with existing `test_feature_flags.py` 29/29 pass with no regression. arch check: 0 violations on the new test file.

- **T13.69 done** (auto-updated by hook)

- **T13.60 done** (auto-updated by hook)

- **T13.58 done** (auto-updated by hook)

- **T13.54 done** (auto-updated by hook)

- **T13.118 done** (auto-updated by hook)

- **T13.8 done** (auto-updated by hook)

- **T13.7 done** (auto-updated by hook)

- **T13.6 done** (auto-updated by hook)

- **T13.118 done** — Production Env Audit. Inventoried every env var read by backend (`backend/app/core/config.py` Settings + 17 `os.environ.get` callsites) + frontend (`process.env` callsites in app/lib/components + Next config + Playwright config) + scripts (`scripts/staging-smoke.sh` + `.paircoder/qc/config.yaml`). New `backend/app/core/env_validation.py` (110L) — `validate_required_env()` reads `os.environ` directly (test-fixture friendly), raises `RuntimeError` naming any missing required var, warns once per missing optional. Required-on-boot trio: `DATABASE_URL`, `ADMIN_API_KEY`, `AUDIT_HASH_SALT` (the production GA blockers). 11 optional-but-behavior-affecting vars warn-log: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `APPOINTMENT_TOKEN_SECRET`, `COMPLIANCE_TOKEN_SECRET`, `UNSUBSCRIBE_TOKEN_SECRET`, `BRIGHTDATA_API_KEY`, `BRIGHTDATA_DATASET_ID`, `CORS_ORIGINS`. Wired into `app.main.lifespan` as the FIRST runtime call after `configure_logging()` — fail-fast before `get_settings()` can silently default. New `backend/app/core/lifespan_helpers.py` (60L) extracted `log_startup_warnings`, `register_db_listeners`, `start_scheduler_with_guard`, `stop_scheduler` from main.py to bring main.py imports back under the 15 arch limit. `.env.example` rewritten as the canonical inventory: 10 sections (app config / LLM / SendGrid / token signers / job boards / credit / feature flags / frontend / dev tooling / QC harness), every entry tagged required|optional + default. Runbook `docs/runbooks/staging-deploy.md` §2.3 secrets table expanded to a 16-row required/optional matrix with a "Boot-time validator" callout. New `backend/tests/test_env_validation.py` (155L, 9 tests): happy path, each missing required var (DATABASE_URL/ADMIN_API_KEY/AUDIT_HASH_SALT, plus empty-string ADMIN_API_KEY), optional-missing-warns-but-doesn't-raise, optional-present-no-warn, validator-reads-os-environ-not-Settings-cache, secret-value-never-leaks-into-error-message. **fly secrets list cross-check:** staging has `ADMIN_API_KEY` + `AUDIT_HASH_SALT` + `CORS_ORIGINS`; `DATABASE_URL` is in `fly.backend.toml [env]` — all 3 required vars covered. **Test results:** 9/9 new tests pass; 51/51 across the 3 impacted test files (test_main.py + test_env_validation.py + test_config_security.py); full backend suite 3888 pass / 1 fail (pre-existing test_contract_credit_api JWT carry-over) / 2 skipped — net delta +9 tests. arch check: 0 errors on all 7 touched files (env_validation, lifespan_helpers, main, test_env_validation, test_main, test_config_security, test_s12b_gate). **Risk fixed:** `audit_hash_salt` previously defaulted silently to `montgowork-default-salt` outside production — boot validator now hard-fails on empty string in any env, complementing the existing post-Settings production-only validator.

- **T13.8 done** — QC Run Dashboard. Hackathon-grade visibility into divona / Playwright suite results: latest verdict per suite, flake indicator, 7-day trend. New Next.js page at `frontend/src/app/admin/qc/page.tsx` (71L) — server component, `dynamic = "force-dynamic"` + `revalidate = 0` so re-running a suite shows on next refresh without redeploy. Reads `.paircoder/qc/runs/` at request time; runs dir resolves from `QC_RUNS_DIR` env var if set, else `path.resolve(process.cwd(), "..", ".paircoder", "qc", "runs")` (Next runs with cwd = `frontend/`). Auth gate is fail-closed in prod: dev/test always allow; prod requires `X-Admin-Key` header to match `QC_DASHBOARD_ADMIN_KEY` env var, returns `notFound()` if env var unset or header doesn't match. Logic extracted to pure helper `frontend/src/app/admin/qc/access.ts` (28L, `isAccessAllowed({nodeEnv, headerKey, adminKey})`) for unit testability. Presentational component `frontend/src/app/admin/qc/QcDashboard.tsx` (135L) — props-driven, header + 3 stat cards (total suites / runs 7d / overall pass rate) + per-suite table with badge (✓ Pass / ✗ Fail / ⚠ Flake / ⏭ Skipped), suite_id, last run, 7d pass rate, 7d run count. Sort order: failing/error first, then flaky, then by `latest_run_at` desc. Empty state: "No QC runs yet. Run a suite via `/run-qc <suite-id>` to populate this dashboard." No charting libs added (plain HTML + emoji + percentages per scope). Six pure helper modules under `frontend/src/lib/qc/`: `types.ts` (52L) — `QcRun` / `QcScenario` / `SuiteSummary` / `ScenarioVerdict`; `flakes.ts` (69L) — `suiteVerdict` (worst-wins precedence: failed > error > skipped-only > passed), `latestVerdict`, `scenarioVerdicts`, `isFlaky` (last-5-runs window, skipped runs ignored, both pass+fail must appear); `trend.ts` (64L) — `runsInLastDays`, `passRateLast7Days` (skipped excluded from denominator, null when no runs in window), `summarizeSuite`; `dashboard.ts` (66L) — `sortSummaries`, `dashboardStats` (run-count-weighted overall pass rate), `verdictLabel` + `verdictBadge`; `loader.ts` (79L) — `suiteIdFromFilename` parses `<suite-id>-YYYY-MM-DDTHH-MM-SS.json` (numbered capture groups, ES2017 target compat — named groups need ES2018), `parseRunFile` hydrates `suite_id` + `timestamp` from filename (divona's documented JSON omits both), `groupBySuite`; `runs_dir.ts` (46L) — `loadRunsFromDir` reads top-level `*.json` only (no recursion), skips malformed JSON without crashing, returns `[]` for missing dir. **Tests:** 55 new vitest tests across 7 files, all passing in 0.7s — `flakes.test.ts` (13: identical-pass-streak not flaky, alternating IS flaky, all-fails not flaky, skipped-runs ignored, 5-run window respected); `trend.test.ts` (9: 7-day window inclusion, null when empty window, ignores skipped); `loader.test.ts` (7: filename pattern parsing, malformed JSON returns null, decoy non-`.json` files rejected); `runs_dir.test.ts` (5: missing dir → `[]`, empty dir → `[]`, mixed valid/decoy files, malformed JSON skipped, no recursion into subdirs); `dashboard.test.ts` (11: sort priority fail > flaky > clean, error-verdict treated as failing, run-weighted overall pass rate, label/badge precedence); `QcDashboard.test.tsx` (4: empty state, three suites with right indicators, sort order verified, stat-card values); `access.test.ts` (6: dev open, prod fail-closed when env unset, header-match required). Full vitest suite: **107/107 files, 1043/1043 tests pass** (no regressions). `npm run build` clean — `/admin/qc` correctly listed as `ƒ (Dynamic) server-rendered on demand`. **Manual smoke:** dev server on port 3201 with `QC_RUNS_DIR=/tmp/qc-smoke-runs` (one passing + one failing fixture JSON) returned 200; rendered HTML contained `QC Dashboard`, both suite IDs, `>Pass<` + `>Fail<` badges, `stat-total-suites = 2`. `bpsai-pair arch check` passes on all 9 source files + 7 test files (largest source: QcDashboard.tsx at 135L < 200 warn; all functions <50L, all files <15 functions, all imports <20). **Prod-deploy contract:** the runs dir is NOT shipped in the Next.js bundle; production deploys must either mount `.paircoder/qc/runs/` as a volume + set `QC_RUNS_DIR=<volume-path>`, or accept that the page will report empty until divona pushes results to a known location. Dashboard is fail-closed if `QC_DASHBOARD_ADMIN_KEY` is unset, so a public prod deploy without explicit opt-in shows 404. Files: 9 new source (`page.tsx`, `QcDashboard.tsx`, `access.ts` under `frontend/src/app/admin/qc/`; `types.ts`, `flakes.ts`, `trend.ts`, `loader.ts`, `runs_dir.ts`, `dashboard.ts` under `frontend/src/lib/qc/`); 7 new tests (5 under `frontend/src/lib/qc/__tests__/`, 2 under `frontend/src/app/admin/qc/__tests__/`). No backend routes added (read-from-FS in dev, env-var-pointed in prod, per task scope).

- **T13.129 done** (auto-updated by hook)

- **T13.116 done** (auto-updated by hook)

- **T13.114 done** (auto-updated by hook)

- **T13.129 done** — Playwright Headless Harness. Installed `@playwright/test@^1.59.1` + `playwright@^1.59.1` in `frontend/package.json` devDependencies; downloaded chromium-only (skipped firefox/webkit per scope) into `~/Library/Caches/ms-playwright/chromium-1217/` (~330 MB). Three new npm scripts: `test:e2e` / `test:e2e:headed` / `test:e2e:debug`. New `frontend/playwright.config.ts` (53L) — chromium-only project, headless 1280x720, `baseURL` honors `STAGING_FRONTEND_URL` else `localhost:3000`, `webServer` boots `npm run dev` with `reuseExistingServer: !process.env.CI`, `retries: 2` + `workers: 1` under CI, line + html reporters. New `frontend/e2e/worker-onboarding.spec.ts` (109L) — three `@critical`-tagged tests mirroring the (yet-to-be-authored) divona `worker-onboarding.qc.yaml`: home hero + How-It-Works renders, "Get Your Plan" CTA navigates to `/assess` and exposes ZIP / Employment / Next-button, and a console-error filter that catches application errors while filtering known dev-server noise (HMR, React DevTools hint, CSP `connect-src` denials, MIME warnings from stale `.next/`, CORS denials when backend at `:8000` is offline). `frontend/vitest.config.ts` updated to `exclude: ["**/node_modules/**", "**/dist/**", "**/.next/**", "e2e/**"]` so vitest's default `*.spec.ts` glob doesn't try to load Playwright bindings inside jsdom. `.gitignore` extended with `frontend/test-results/`, `frontend/playwright-report/`, `frontend/blob-report/`, `frontend/playwright/.cache/`. `.paircoder/qc/suites/README.md` got a new "Divona vs. Playwright — when to use which" section: tabular when-to-use guide, source-of-truth contract (`.qc.yaml` is canonical, Playwright is the lockstep CI mirror, only top-five paths get `@critical`), and a 5-step "adding a new Playwright spec" recipe. **Verification:** `npx playwright test --list` shows 3 tests in 1 file under `[chromium]`; `--grep '@critical' --list` returns the same 3; `npx playwright test --grep '@critical'` against a fresh `next dev` on port 3100 = **3 passed (1.6s)**. Existing vitest still green: 100/100 files, 979/979 tests. arch check: 0 violations on both new TS files (109L spec < 200 limit, 53L config < 100 limit). Unblocks T13.6 (visual regression) and T13.125 (PR-gating CI workflow). **Note for the user:** the running production-mode `next start` on port 3000 was serving stale `.next/` chunks during testing — restart the dev server with `cd frontend && npm run dev` for a clean local Playwright run.

- **T13.116 done** — Favicon + PWA Manifest + OG/Twitter Meta. Root `layout.tsx` (96L) extended with full Next.js Metadata API: `metadataBase`, multi-size icons (SVG + 16/32/192/512 PNG references + apple-touch 180), `manifest: '/manifest.json'`, OpenGraph (`type=website`, `siteName`, 1200x630 og:image with width/height/alt), Twitter (`summary_large_image` card + image), `applicationName`, and a Next.js 15-compliant `viewport` export carrying `themeColor: '#1c3461'` (brand navy from `globals.css`). Two new server-component layouts give `"use client"` pages their own metadata: `frontend/src/app/daily/layout.tsx` (36L, override title + OG/Twitter) and `frontend/src/app/shared/[token]/layout.tsx` (69L) with `generateMetadata` that returns generic brand-safe copy and `robots: { index: false, follow: false }` — token-gated content must never be indexed and the meta tags must NOT include the raw share token (verified by test). PWA `frontend/public/manifest.json` declares name/short_name/description/start_url=`/`/display=`standalone`/background_color=`#f3f1ea`/theme_color=`#1c3461`/192/512/maskable/SVG icons. SVG stand-ins shipped at `frontend/public/icon.svg` (MGW-mark) and `frontend/public/og-image.svg` (1200x630 brand card). New `frontend/src/app/__tests__/metadata.test.tsx` (206L, 16 tests) imports the metadata exports + `generateMetadata` and asserts shape, OG image presence, Twitter card type, manifest reference, multi-size icons, viewport theme color, robots noindex on shared route, and the no-PII-leak invariant (token does not appear in description / og:title / og:description / twitter:title / twitter:description). 16/16 metadata tests pass; full vitest suite 979/979 unit tests pass (the one failed file is a pre-existing playwright e2e mis-import unrelated to this task). `npm run build` clean, no Next.js metadata warnings; rendered HTML verified to contain `<meta property="og:title">`, `<meta name="twitter:card">`, `<link rel="manifest">`, `<link rel="apple-touch-icon">` on `/` and per-page overrides on `/daily`. arch check: 0 errors across all 4 new TS files. **Asset gap (user action required):** drop real PNG/ICO bytes at `frontend/public/favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `icon-192.png`, `icon-512.png`, `icon-512-maskable.png`, `apple-icon.png`, and `og-image.png` (1200x630) — generate from the provided `icon.svg` + `og-image.svg`. Until then, modern browsers will fall back to the SVG icon and link previews will 404 the og-image.

- **T13.65 done** (auto-updated by hook)

- **T13.59 done** (auto-updated by hook)

- **T13.55 done** (auto-updated by hook)

- **T13.53 done** (auto-updated by hook)

- **T13.53 done** — Nightly Orchestrator Full Dry-Run. New `backend/tests/test_orchestrator_full_run.py` (479L, 7 tests) seeds the T13.2 worker-companion demo (10 sessions × 2 cities), freezes the wall clock via the T13.5 `freeze_time` harness, and asserts every documented step in `scripts.nightly_digest` fires once per session in the documented order. Spy/stub helpers extracted to `backend/tests/_orchestrator_spies.py` (202L) to keep the test file under the 600L ceiling. Documented step list extracted from source: retro → reconcile (T12.25a step 2.5) → refresh (T12.24) → compose (T12.20, internally invokes stall detector + T12.25b module-status collector) → send_digest (T12.19) → weekly_review (T12.22a, Sunday only) → retention_sweep (T12.36, once per run). Partial-failure policy verified: fail-soft per session — `_run_one` catches a per-session compose raise and counts it as `error=1` while other sessions continue; `_refresh_session_plan` swallows its own raises so the digest still ships. Two task-brief deviations documented in the test docstring: (1) `send_digest` fires every day including Sunday, weekly_review piggybacks on top — does not replace it; (2) stall detection is invoked inside `compose_digest`, not as a standalone orchestrator step. 7/7 tests pass in 0.21s; arch check 0 errors (test file 479L < 600 error, spies 202L clean). No orchestrator bugs found — code matches the contract documented in `nightly_digest.py`'s module docstring.

- **T13.70 done** (auto-updated by hook)

- **T13.63 done** (auto-updated by hook)

- **T13.57 done** (auto-updated by hook)

- **T13.56 done** (auto-updated by hook)

- **T13.70 done** — Compliance Cascade Verification. New `backend/tests/test_compliance_cascade.py` (520L, 6 tests) introspects `sqlite_master` + `PRAGMA foreign_key_list` to enumerate every session-scoped table, seeds one row in each, runs `full_delete`, and asserts zero rows survive (audit row exempt by allowlist). Schema-drift guard fails CI with the offending name if a future migration adds a session-scoped table without wiring it to the cascade. **Bug found & fixed:** introspection revealed 4 m001 tables (`feedback_tokens`, `visit_feedback`, `resource_feedback`, `share_tokens`) that carry a `session_id` column but no FK — `full_delete` was leaking these rows. Added them to `delete._NON_CASCADING_TABLES` (now 5 entries: `record_profiles` + the 4 newly covered). 6/6 cascade tests + 18/18 existing compliance + 16/16 qc_reset green; arch check shows warnings only (test 520L < 600 error; delete.py 163L < 300 error).

### 2026-04-24 — T13.70 driver session — Compliance Cascade Verification

Built schema-introspection-driven cascade test that locks in the `full_delete` invariant for current and future session-scoped tables.

**Files created:**
- `backend/tests/test_compliance_cascade.py` (520L) — 6 tests across 3 axes: introspection sanity, full-delete-clears-all, schema-drift guard. Module docstring documents the FK + session_id-column union strategy and the allowlist contract.

**Files modified:**
- `backend/app/modules/compliance/delete.py` — `_NON_CASCADING_TABLES` extended from `("record_profiles",)` to a 5-tuple covering all m001 session-keyed tables (`record_profiles`, `feedback_tokens`, `visit_feedback`, `resource_feedback`, `share_tokens`). Comment block above the tuple now points at this test as the lock-in mechanism for future drift.

**Tables discovered via introspection (14):** 9 FK-cascading (m002/m003: `appointments`, `daily_progress_snapshots`, `engagement_events`, `job_applications`, `outcomes_records`, `plan_history`, `reminder_cooldowns`, `resume_versions`, `worker_unavailability`) + 5 m001 session-keyed without FK (`record_profiles`, `feedback_tokens`, `visit_feedback`, `resource_feedback`, `share_tokens`).

**Allowlist (1 entry):** `compliance_audit` — written by `full_delete` itself, stores `session_id_hash` (sha256), retained as the immutable audit trail.

**Cascade gap fixed:** prior to this task, `full_delete` only manually cleared `record_profiles`. SQLite's `ON DELETE CASCADE` chain triggered by the `DELETE FROM sessions` row took care of every m002 child but did NOT touch the 4 m001 legacy tables (no FK declared). Without this fix, a worker requesting full deletion would have left `feedback_tokens`, `visit_feedback`, `resource_feedback`, and `share_tokens` rows in the DB pointing at a now-orphan session id — a real PII-retention bug. Cross-references `scripts/_qc_reset_wipe.SESSION_KEYED_TABLES` (T13.3): the QC reset script already treated these 4 as session-keyed, so the demo wipe was correct but the production right-to-delete path was incomplete. Both lists are now consistent.

**Acceptance criteria (T13.70 spec):**
- Table inventory generated via schema introspection: `_user_tables`, `_tables_with_fk_to_sessions`, `_tables_with_session_id_column`, `_session_scoped_tables`. Verified by `test_introspection_returns_expected_session_scoped_tables`.
- `full_delete` followed by `count(*)==0` on every listed table: `test_full_delete_clears_every_session_scoped_table` (introspect-driven loop, no hard-coded list).
- Audit row retained (explicit exception): `_RETAIN_ALLOWLIST` documents `compliance_audit` with reason; `test_compliance_audit_row_retained_after_full_delete` asserts the `full_delete` action row survives.
- New session-scoped table fails CI: `test_every_session_scoped_table_is_covered_or_allowlisted` walks introspection results and asserts each table is either (a) FK-cascading, (b) in `delete._NON_CASCADING_TABLES`, or (c) in the test's `_RETAIN_ALLOWLIST`. The error message names the offending table and lists the 3 fix options.
- `bpsai-pair arch check` passes: 0 errors. Test file 520L (warning at 400, error at 600 — within bounds). delete.py 163L (warning at 150 due to project-tightened threshold; error at 300 — within bounds).

**Test results:** 6/6 pass in 0.06s. Regression: 18/18 existing compliance tests + 16/16 qc_reset tests still green.

- **T13.128 done** (auto-updated by hook)

- **T13.3 done** (auto-updated by hook)

- **T13.128 staging environment LIVE on Fly.io** — https://montgowork-staging-api.fly.dev (backend, 2GB) + https://montgowork-staging-web.fly.dev (frontend). 7 migrations applied to volume DB; 10 demo sessions seeded. Smoke 15/19 PASS — 4 sub-fix findings logged (RAG index, admin/flags route path, /documents + /feedback Next.js pages). Two real fixes shipped in deploy: Dockerfile `COPY cities /cities`, backend memory 512mb→2gb.
- **Wave 0 complete (T13.1-T13.5 + T13.128).** QC foundation in place: config + suite template + README, demo seed extension, reset CLI, axe-core install, fake-clock harness, staging deploy artifacts. End-to-end smoke verified: fresh DB → migrate → qc_reset wipes & reseeds 10 demo sessions in 2.76 ms. 6/128 tasks done; Tier-1 browser suite authoring (T13.10-T13.52) is unblocked.
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
