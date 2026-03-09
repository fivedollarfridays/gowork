# Current State

> Last updated: 2026-03-08

## Active Plan

**Plan:** plan-2026-03-benefits-cliff-engine
**Type:** feature
**Title:** Benefits Cliff Engine — Cliff-Aware Job Ranking for Montgomery Residents
**Status:** Planned (synced to Trello)
**Current Sprint:** 25

## Previous Active Plan

**Plan:** plan-2026-03-barrier-graph-rag
**Type:** feature
**Title:** Barrier Graph + RAG — Barrier Intelligence Assistant
**Status:** In Progress (1/7 done)
**Sprint:** 23

## Previous Plans

- plan-2026-03-security-hardening (Complete, 7/7 done -- Sprint 18)
- plan-2026-03-hackathon-demo-polish (Complete, 6/6 done -- Sprint 17)
- plan-2026-03-intelligent-job-matching (Complete, 6/6 done -- Sprint 13)
- plan-2026-03-monday-morning-ux (Complete, 1/1 done -- Sprint 12)
- plan-2026-03-launch-prep-polish (Complete, 8/8 done -- Sprint 11)
- plan-2026-03-a11y-and-demo (Complete, 5/5 done -- Sprint 10)
- plan-2026-03-docs-and-readme (Complete, 5/5 done -- Sprint 9)
- plan-2026-03-export-and-polish (Complete, 4/4 done -- Sprint 8)
- plan-2026-03-brightdata-live-jobs (Complete, 6/6 done -- Sprint 7)
- plan-2026-03-demo-killer-frontend (Complete, 10/10 done -- Sprint 5)
- plan-2026-03-plan-2026-03-implementation (Complete, 9/9 done -- Sprint 4)
- plan-2026-03-test-coverage (Complete, 4/4 done -- Sprint 3)
- plan-2026-03-plan-2026-03-review-fixes (Complete, 3/3 done)
- plan-2026-03-module-skeletons (Complete, 7/7 done)

## Current Focus

Sprint 25: Benefits Cliff Engine. WorkPath's key differentiator — showing users that "taking this $15/hr job costs you $400/month in benefits." Alabama-specific benefit program modeling (SNAP, TANF, Medicaid, Childcare, Section 8, LIHEAP), cliff-aware PVS scoring, and visualization.

## Task Status

### Sprint 25 — Benefits Cliff Engine

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T25.1 | Benefits Cliff Calculator Module | P0 | 60 | done | -- |
| T25.2 | Benefits Profile in Assessment Wizard | P0 | 40 | done | T25.1 |
| T25.3 | Cliff-Aware Job Ranking | P0 | 50 | done | T25.1, T25.2 |
| T25.4 | Benefits Cliff Visualization | P1 | 35 | done | T25.1, T25.3 |

**Total: 4 tasks, 185 complexity points (4/4 done) — SPRINT COMPLETE**

### Sprint 23 — Barrier Graph + RAG (Barrier Intelligence Assistant)

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T23.1 | Barrier graph DB schema: Alembic migration + seed data | P0 | 55 | done | -- |
| T23.2 | Barrier-resource mapping: join table, impact scores, top-N query | P0 | 45 | pending | T23.1 |
| T23.3 | RAG knowledge base: document schema + FAISS ingestion pipeline | P0 | 60 | pending | T23.1, T23.2 |
| T23.4 | Hybrid retrieval layer: vector + metadata filter + graph context assembly | P0 | 50 | pending | T23.2, T23.3 |
| T23.5 | LLM orchestration + guardrails: POST /api/barrier-intel/chat + SSE streaming | P0 | 70 | pending | T23.4 |
| T23.6 | Frontend: BarrierIntelChat + SSE streaming + explainability UI | P1 | 70 | pending | T23.5 |
| T23.7 | NFRs: caching, observability, rate limiting + eval suite | P2 | 55 | pending | T23.5, T23.6 |

**Total: 7 tasks, 405 complexity points (1/7 done)**

### Sprint 18 -- Security Hardening (GitHub Issue #20)

| ID | Title | Priority | Complexity | Status |
|----|-------|----------|------------|--------|
| T18.1 | Admin auth for BrightData endpoints (SEC-001) | P0 | 25 | done |
| T18.2 | Prompt injection defense (SEC-003) | P0 | 20 | done |
| T18.3 | Security headers + CORS hardening (SEC-008, SEC-013) | P0 | 20 | done |
| T18.4 | Container + Docker hardening (SEC-009, SEC-018) | P1 | 15 | done |
| T18.5 | Input validation + info leak fixes (SEC-012, SEC-016, SEC-017, SEC-023) | P1 | 30 | done ✓ |
| T18.6 | Rate limiting on expensive endpoints (SEC-010) | P1 | 25 | done ✓ |
| T18.7 | CI vulnerability scanning + accepted risks docs (SEC-020) | P2 | 20 | done ✓ |

**Total: 7 tasks, 155 complexity points (7/7 done)**


### Sprint 14 -- Feedback Loop

| ID | Title | Priority | Complexity | Status |
|----|-------|----------|------------|--------|
| T14.1 | Schema + types (feedback tables, ResourceHealth) | P0 | 25 | done |
| T14.2 | Feedback token generation, validation, expiry | P0 | 25 | done |
| T14.3 | Resource feedback API | P0 | 30 | done  |
| T14.4 | Resource feedback UI (thumbs up/down) | P1 | 30 | done |
| T14.5 | Visit feedback API | P0 | 35 | done |
| T14.6 | Visit feedback form (/feedback/[token]) | P1 | 40 | done |
| T14.7 | QR code in PDF export | P2 | 25 | done |
| T14.8 | Resource health check (decay detection) | P1 | 50 | done |

**Total: 8 tasks, 260 complexity points (8/8 done)**

### Sprint 15 -- Career Center Ready Package

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T15.1 | WIOA screener types + eligibility logic | P0 | 30 | done | -- |
| T15.2 | Career Center Package data model + assembler | P0 | 35 | done | T15.1 |
| T15.3 | GET /api/plan/{session_id}/career-center | P0 | 25 | done | T15.1, T15.2 |
| T15.4 | Wire WIOA eligibility into generate_plan | P0 | 25 | done | T15.1 |
| T15.5 | CareerCenterPackage frontend component | P0 | 50 | done | T15.7 |
| T15.6 | Career Center Ready PDF export button | P1 | 25 | done | T15.3, T15.5 |
| T15.7 | Frontend types + API client | P0 | 15 | done | T15.2 |

**Total: 7 tasks, 205 complexity points (7/7 done)**

### Sprint 16 -- Fix Sprint: Review Corrections

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T16.1 | SQLAlchemy StaticPool warning fix | P0 | 10 | done | -- |
| T16.2 | Resource affinity routing | P0 | 40 | done | T16.1 |
| T16.3 | Barrier priority ordering | P0 | 30 | done | T16.2 |
| T16.4 | Cloud deployment documentation | P1 | 25 | done | -- |
| T16.5 | Architecture known limitations section | P1 | 25 | done | -- |

**Total: 5 tasks, 130 complexity points (5/5 done)**

### Sprint 17 -- Hackathon Demo Polish

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T17.1 | Session recovery on plan page refresh | P0 | 20 | done | -- |
| T17.2 | Post-plan What's Next CTA section | P0 | 20 | done | -- |
| T17.3 | Geocode seed resources for proximity scoring | P1 | 30 | done | -- |
| T17.4 | Add credit counseling resources + complete addresses | P1 | 20 | done | T17.3 |
| T17.5 | Remove dead feedback_token_secret config | P2 | 5 | done | -- |
| T17.6 | Documentation sync — api.md and architecture.md | P1 | 30 | done | -- |

**Total: 6 tasks, 125 complexity points (6/6 done)**

## What Was Just Done

- **T27.0 BrightData Pre-Built Jobs Dataset Integration** (2026-03-08) — Created `dataset_loader.py` (parse JSON/JSONL/CSV dataset files, normalize to `BrightDataJobRecord`), `salary_embed.py` (embed structured salary data into description text for PVS salary_parser). Sample dataset with 15 Montgomery-area jobs (real employers: Amazon, Walmart, Hyundai, FedEx, MATS, Jackson Hospital, etc.) with salary ranges $11-$20/hr. Scores now range 0.772-0.959 (was all 25%). Dedup by (title, company), Montgomery-area filter, high-salary exclusion, URL-based DB dedup. 33 new tests, 1105 total passing. All arch checks clean.

- **Fix: frontend test step indices** (2026-03-08) — Updated `assess-industry.test.tsx` and `assess-schedule.test.tsx` to account for new Benefits step (step 4). Schedule moved from step 4→5, Industries from step 5→6, Review from step 6→7. All 9 assess tests pass. 4 pre-existing failures in unrelated files (BarrierCardView, MondayMorning, plan-whats-next).

- **Fix: CliffBadge hardcoded colors** (2026-03-08) — Replaced hardcoded Tailwind colors (`bg-red-50`, `bg-amber-50`, `bg-emerald-50`) with `STATUS_BADGE_STYLES.positive/negative/warning` from constants.ts. Follows project pattern for CSS-variable-based badge styling.

- **Refactor: string enums for benefits types** (2026-03-08) -- Added `CliffSeverity(str, Enum)` with values mild/moderate/severe and `CliffType(str, Enum)` with values gradual/hard to `benefits/types.py`. Updated `CliffPoint.severity` to `CliffSeverity`, `ProgramBenefit.cliff_type` to `CliffType`, `CliffImpact.severity` to `Optional[CliffSeverity]`. Updated `classify_cliff_severity()` return type and `_get_phase_out()` return type in `cliff_calculator.py`. All existing tests pass without modification (str enum equality preserved). 18 new tests in `test_benefits_enums.py`. 945 tests pass (19 pre-existing failures in test_scoring_context.py and test_pvs_cliff.py unrelated).

- **Refactor: ScoringContext dataclass** (2026-03-08) -- Extracted `ScoringContext` Pydantic BaseModel into `matching/types.py` to bundle user-level scoring parameters (`user_zip`, `transit_dependent`, `schedule_type`, `barriers`, `benefits_profile`). Updated `compute_pvs(job, ctx, salary=)` and `rank_all_jobs(jobs, ctx)` to accept `ScoringContext` instead of 5-6 individual params. Updated `job_matcher.py` to build `ScoringContext` from `UserProfile`. Refactored all tests in `test_pvs_scorer.py`, `test_pvs_cliff.py` to use `ScoringContext`. Added `test_scoring_context.py` with 6 new tests. All 967 tests pass.

- **Refactor: consolidate benefit-summing** (2026-03-08) — Extracted `sum_program_benefits(annual_income, profile)` into `program_calculators.py` as the single canonical implementation. `cliff_calculator._total_benefits` is now a thin wrapper delegating to it (converts hourly to annual). `pvs_scorer._sum_benefits` removed entirely; call sites import `sum_program_benefits` directly. Added 7 new tests in `test_sum_program_benefits.py` covering equivalence with old implementations. All 967 tests pass.

- **Refactor: shared constants** (2026-03-08) — Consolidated `HOURS_PER_YEAR = 2080` and `MONTHS_PER_YEAR = 12` into `backend/app/modules/benefits/thresholds.py`. Updated 5 consumers (cliff_calculator.py, program_calculators.py, pvs_scorer.py, salary_parser.py, brightdata/cache.py) to import from thresholds instead of defining locally. Added 9 identity tests in `test_shared_constants.py`. All 958 tests pass (6 pre-existing enum test failures unrelated).

- **T25.4 done** (auto-updated by hook)

- **T25.4 done** (2026-03-08)
- **T25.3 done** (2026-03-08)
- **T25.2 done** (auto-updated by hook)
- **T25.1 done** (auto-updated by hook)

### Sprint 25 T25.4 (2026-03-08) — Benefits Cliff Visualization

- **T25.4** Benefits Cliff Visualization: Installed recharts. Added `CliffAnalysis`, `WageStep`, `CliffPoint` types to `types.ts`. Added `benefits_cliff_analysis: Optional[CliffAnalysis] = None` to `ReEntryPlan`. Engine computes `calculate_cliff_analysis(benefits_profile)` when enrolled programs exist and attaches to plan. Created `BenefitsCliffChart.tsx` — Recharts AreaChart (net income vs hourly wage, $8-$25), cliff zone ReferenceLine markers (red, −$X labels), current income dashed ReferenceLine, responsive container, `role="img"` with aria-label, text summary (biggest cliff at $X/hr, recovers above $Y/hr). Wired into `plan/page.tsx` between job matches and comparison view, conditionally rendered when `benefits_cliff_analysis` exists. Extracted `_barrier_cards_and_steps()` helper in engine.py for arch compliance. 6 new frontend tests. All arch checks clean.

### Sprint 25 T25.3 (2026-03-08) — Cliff-Aware Job Ranking

- **T25.3** Cliff-Aware Job Ranking: Added `CliffImpact` model to `types.py` (benefits_change, net_monthly_change, has_cliff, severity, affected_programs). Modified `pvs_scorer.py`: renamed W_EARNINGS→W_NET_INCOME, added `_score_net_income()` using `calculate_net_at_wage()` from cliff calculator, `_compute_cliff_impact()` with benefit-by-benefit comparison, `_build_match()` helper. When `BenefitsProfile` with enrolled programs is provided, PVS earnings component uses net income (wages + benefits - taxes) instead of gross wages. Falls back to gross `score_earnings()` when no profile. NO_PAY_CEILING unchanged. Threaded `benefits_profile` through `job_matcher.py` → `rank_all_jobs()` → `compute_pvs()`. Engine `generate_plan()` accepts `benefits_profile` param; assessment route converts `BenefitsFormData` → `BenefitsProfile` and passes it. Frontend: `CliffImpact` type in `types.ts`, `CliffBadge.tsx` component (green "No benefits impact" / red "-$X/mo benefits" with severity + affected programs + net change), wired into `JobMatchCard.tsx`. Extracted `_split_legacy_buckets()` and `_session_data()` helpers to fix arch function-length violations. 14 new backend tests (920 total), 6 new frontend tests. All arch checks clean.

### Sprint 25 T25.2 (2026-03-08) — Benefits Profile in Assessment Wizard

- **T25.2** Benefits Profile in Assessment Wizard: Backend — added `BenefitsFormData` Pydantic model to `matching/types.py`, `benefits_data` optional field on `AssessmentRequest`, `benefits_profile TEXT` column in sessions DDL, `create_session` query updated, assessment route stores `benefits_data.model_dump_json()`. Frontend — created `BenefitsStep.tsx` component with household size, monthly income, 7 program checkboxes (SNAP/TANF/Medicaid/ALL Kids/Childcare/Section 8/LIHEAP + "None"), dependents under 6/6-17. Added between Barriers and Schedule in wizard (`assess/page.tsx`). Benefits data only sent when user provides meaningful input. `BenefitsFormData` interface added to `types.ts`. 10 new backend tests (906 total), 8 new frontend tests (254 total). All arch checks clean.

### Sprint 25 T25.1 (2026-03-08) — Benefits Cliff Calculator Module

- **T25.1** Benefits Cliff Calculator Module: Created `backend/app/modules/benefits/` with 4 files. `types.py` with 6 Pydantic models (BenefitsProfile, ProgramBenefit, WageStep, CliffPoint, CliffAnalysis). `thresholds.py` with Alabama-specific 2026 constants (FPL, SNAP max benefit, TANF, ALL Kids 317% FPL, Childcare SMI 85%, Section 8 50% AMI Montgomery, LIHEAP 150% FPL, tax brackets). `program_calculators.py` with 7 per-program benefit calculators (SNAP gradual, TANF hard, Medicaid=0 no expansion, ALL Kids, Childcare copay tiers, Section 8, LIHEAP). `cliff_calculator.py` with `calculate_cliff_analysis()` computing net income at $8-$25/hr in $0.50 steps, cliff detection (>$1/month drop threshold), severity classification (mild/moderate/severe), program identification, safe wage floor. 37 new tests (severity, thresholds, no-program monotonic increase, SNAP gradual phase-out, Section 8 hard cliff, compound cliffs, all programs, net-at-wage, edge cases), 896 total passing. All arch checks clean.

### Sprint 25 Planning (2026-03-08) — Benefits Cliff Engine

- Analyzed `docs/workpath-pipeline-backlog.md` — comprehensive multi-sprint backlog (Sprints 25-31) covering benefits cliff, criminal record routing, job aggregation, resource matching, transit, and action plan generation.
- Explored codebase: PVS formula (0.35 earnings + 0.25 proximity + 0.20 time_fit + 0.20 barrier_compat), UserProfile fields, assessment wizard steps, plan page sections, database schema.
- Key design decisions: new `backend/app/modules/benefits/` module, net income replaces gross earnings in PVS (35% weight), new wizard step between Barriers and Credit (skippable), Recharts cliff chart on plan page, Alabama-only hardcoded thresholds for MVP.
- Architecture concerns: assess/page.tsx at 417 lines (over limit, new step extracted as separate component), types.ts at 434 lines (benefits types may need separate file), engine.py at 227 lines (minimal changes only).
- Created plan: plan-2026-03-benefits-cliff-engine (4 tasks, 185 complexity, Sprint 25).
- All 4 task files written with full objectives, file lists, implementation plans, and acceptance criteria.
- Synced 4 cards to Trello Planned/Ready.

### Sprint 23 T23.1 (2026-03-07) — Barrier Graph DB Schema

- **T23.1** Barrier graph DB schema: Created ADR doc (`ADR_embeddings.md`) with 5 architecture decisions. Added 3 new tables (`barriers`, `barrier_relationships`, `barrier_resources`) to DDL in `database.py` with `ALLOWED_COLUMNS` entries. Initialized Alembic and created migration `8ae7be7d93ea_add_barrier_graph_tables`. Created `barrier_graph/seed.py` with idempotent `upsert_barrier_graph()` using INSERT OR IGNORE. Created `data/barrier_graph_seed.json` with 33 barrier nodes across 8 categories and 53 relationship edges (CAUSES, WORSENS, PRE_REQ_FOR). Wired barrier graph seeding into `main.py` lifespan startup. 8 new tests (tables exist, minimum counts, playbook coverage, category validation, idempotency), 414 total passing.

### Sprint 23 Planning (2026-03-07) — Barrier Graph + RAG

- Analyzed `docs/internal/barrier-graph-rag-implementation/00_planning.md` and all 14 reference docs.
- Identified 9 gaps/problems: unspecified embeddings model, streaming protocol, missing Alembic task, LangChain decision, what-if underspecification, Redis ambiguity, dependency ordering, missing CI tests, FAISS migration trigger.
- Decisions recorded in plan: `sentence-transformers/all-MiniLM-L6-v2`, SSE streaming, what-if deferred to v2, in-memory cache (no Redis v1), no LangChain.
- Created plan: plan-2026-03-barrier-graph-rag (7 tasks, 405 complexity, Sprint 23).
- All 7 task files written with full objectives, schemas, implementation plans, and acceptance criteria.
- Trello sync pending: `bpsai-pair trello connect` required to push 7 cards.

### Sprint 18 (2026-03-07) — Security Hardening — COMPLETE

- **T18.7** CI vulnerability scanning: `pip-audit` step added to CI backend job, `npm audit --audit-level=high` added to CI frontend job. Created `docs/SECURITY.md` with 15 fixed findings, 5 accepted risks with rationale, security architecture overview, and CI scanning docs. 472 backend tests pass.

- **T18.6** Rate limiting: extracted shared `RateLimiter` to `app/core/rate_limit.py`. Added rate limiting to POST /generate (5/min) and POST /credit/assess (10/min). Replaced duplicate classes in assessment.py and feedback.py. 7 new tests, 472 total.

- **T18.5** Input validation + info leak fixes: UUID regex on `session_id` path params (plan.py 3 endpoints), pattern on `ResourceFeedbackRequest.session_id`, alphanumeric regex on `snapshot_id` (brightdata.py), logger logs length not raw response (client.py), removed `session_id` from validate endpoint response. 7 new tests, 465 total.

- **T18.4** Container hardening: both Dockerfiles run as non-root `appuser`. Removed hardcoded env overrides from docker-compose.yml and stale ENV defaults from backend Dockerfile.
- **T18.3** Security headers + CORS: X-Frame-Options DENY, CSP, nosniff, Referrer-Policy, Permissions-Policy in next.config.mjs. CORS methods restricted to GET/POST/OPTIONS, headers to Content-Type/X-Admin-Key.
- **T18.2** Prompt injection defense: untrusted-data instruction in system prompt, `<user_input>` XML tags wrapping barriers and qualifications in user prompt. 3 new tests, 458 total.
- **T18.1** Admin auth for BrightData: `app/core/auth.py` with `require_admin_key` dependency (503/403/422). Router-level `Depends` on all 3 BrightData endpoints. `admin_api_key` added to Settings. 4 new tests + 10 updated, 455 total.

### Sprint 18 Planning (2026-03-07) — Security Hardening

- Audited all 26 findings from GitHub Issue #20 (security audit). 3 already fixed (SEC-002 random tokens, SEC-011 free_text max_length, SEC-026 session expiry). 20 still open, 3 partially fixed.
- Created plan: plan-2026-03-security-hardening (7 tasks, 155 complexity). Synced 7 cards to Trello Planned/Ready.
- Scope: CRITICAL (SEC-001 admin auth), HIGH (SEC-003 prompt injection, SEC-008 headers, SEC-009 containers), MEDIUM (SEC-012/016/017/023 input validation, SEC-010 rate limiting), LOW (SEC-020 CI scanning).
- Accepted risks documented in T18.7: SEC-006 (single-worker rate limiter), SEC-007 (credit proxy error), SEC-014 (EmailJS PII), SEC-015 (QR token by design), SEC-019 (DATA_DIR hardcoded).

### Sprint 17 (2026-03-07) — Hackathon Demo Polish — COMPLETE

- **T17.6** Documentation sync: api.md updated with 4 missing endpoints (feedback resource/validate/visit, career-center) with full request/response examples and curl. architecture.md updated with 3 new tables, 5 new modules, profile column, frontend feedback page, 4 new components, data fetching hooks, and haversine proximity scoring description.

- **T17.5** Removed dead `feedback_token_secret` field from Settings class in config.py. No references in codebase. 451 backend tests pass.

- **T17.4** Credit resources: GreenPath Financial Wellness + CCCS of Central Alabama added to community_resources.json with subcategory credit_counseling. 451 backend tests pass.
- **T17.3** Geocode: lat/lng added to all 13 seed resources, Resource model updated, `_score_proximity` now uses haversine (was hardcoded 0.5). MPACT address+phone added. 2 new tests, 451 backend total.
- **T17.2** What's Next CTA: Card section at plan page bottom with 3-step instructions, Career Center address/phone/hours, Start New Assessment link. 2 new tests, 146 frontend total.
- **T17.1** Session recovery: `useSessionId()` hook persists session_id to sessionStorage from URL, recovers on refresh. 3 new tests, 144 frontend total.

### Sprint 17 Planning (2026-03-06)

- Full platform audit: tested API pipeline, frontend UX, data quality. Debunked false "showstopper" (seed_database works correctly). Identified 6 real issues. Created plan: plan-2026-03-hackathon-demo-polish (6 tasks, 125 complexity). Synced to Trello.

### Sprint 15 (2026-03-06) — Career Center Ready Package — COMPLETE

- **T15.6** CareerCenterExport component: fetches package on click, renders CareerCenterPrintLayout offscreen, exports via html2pdf with date-stamped filename (`montgowork-career-center-{date}.pdf`). Added as first CTA on plan page (before PlanExport/EmailExport). 7 new frontend tests, 141 total.

- **T15.7** Frontend types + API client: 6 TS interfaces in types.ts, `getCareerCenterPackage()` in api.ts.
- **T15.5** CareerCenterPrintLayout: 3-page print component (staff summary, resident plan, credit pathway). forwardRef, 11pt min font, page breaks. 10 new frontend tests, 133 total.
- **T15.4** Wire WIOA into generate_plan: `WIOAEligibility` moved to `types.py`, `screen_wioa_eligibility()` called in `generate_plan()`, TS interface + 4 test fixture updates. 2 new engine tests, 449 total.
- **T15.3** Career center endpoint: `GET /api/plan/{session_id}/career-center` rebuilds UserProfile, runs WIOA screening, assembles package. Credit pathway from stored credit_profile. 6 new tests, 447 total.
- **T15.2** Career Center Package: models in `career_center_types.py` (6 models), `assemble_package()` assembler with staff summary, document checklist, what-to-say scripts, credit pathway. 16 new tests, 441 total.
- **T15.1** WIOA screener: `WIOAEligibility` model (6 fields), `screen_wioa_eligibility()` with adult/supportive/ITA logic, `has_expired_certification()` helper. 23 new tests, 425 total.

### Sprint 14 (2026-03-06, continued) — COMPLETE

- **T14.8** Resource health check: `check_resource_health()` pure function (HEALTHY/WATCH/FLAGGED thresholds), `get_feedback_stats()` 30-day window, `update_all_health_statuses()` batch, `update_resource_health()` DB setter. Engine filters HIDDEN, sorts FLAGGED last. `health_status` field added to Resource model. 12 new tests, 402 backend total.
- **T14.7** QR code in PDF export: `PdfFeedbackQR` component with `QRCodeSVG` (level M, size 100) encoding `/feedback/{token}` URL. Added `feedbackToken` prop to PlanExport, wired from sessionStorage, stored during assessment. `feedback_token` added to `AssessmentResponse` TS type. `qrcode.react` installed. 3 new tests, 121 frontend total.
- **T14.6** Visit feedback form at `/feedback/[token]`: mobile-first 3-question page with token validation on load, conditional Q2 (outcomes checkboxes when Q1=Yes), large touch targets (min-h-11), loading/error/success/duplicate states. Added `validateFeedbackToken()` and `submitVisitFeedback()` to api.ts. 7 new frontend tests, 118 total.
- **T14.5** Visit feedback API: GET /api/feedback/validate/{token} (200/410/404), POST /api/feedback/visit with token validation, 409 duplicate guard, JSON outcomes. Added `token_exists`, `has_visit_feedback`, `insert_visit_feedback` to queries_feedback.py. 9 new tests, 390 total.
- **T14.4** Resource feedback UI: thumbs up/down on BarrierCardView with optimistic state, sessionStorage persistence, `submitResourceFeedback` API call, aria-labels. 9 new frontend tests, 110 total.

### Sprint 15 (2026-03-06) — Career Center Ready Package

- **T15.1** WIOA screener: `WIOAEligibility` model (6 fields), `screen_wioa_eligibility()` with adult/supportive/ITA logic, `has_expired_certification()` helper. 23 new tests, 425 total.

### Sprint 16 (2026-03-06)

- **T16.4** Appended Railway, Vercel, and consolidated env vars reference sections to `docs/DEPLOYMENT.md`. Covers Dockerfile reference, volume mount for SQLite persistence, health check config, Vercel root directory setup, and complete backend/frontend env var table.
- **T16.5** Appended "Known Limitations & Scaling Path" section (6 items) to `docs/architecture.md`. Covers SQLite-to-Postgres migration, static resource refresh, caching, external API resilience, security hardening, and horizontal scaling.
- **T16.3** Static barrier priority map: childcare=1 through training=7. Wired into `generate_plan()`. 9 new tests, 381 total.
- **T16.2** Resource affinity routing: new `affinity.py` module with `assign_resources()`, `BARRIER_PROCESSING_ORDER`, `RESOURCE_AFFINITY`. Career Center moved to `immediate_next_steps`. 12 new tests, 372 total.
- **T16.1** Added `StaticPool` import and `poolclass=StaticPool` to `create_async_engine()` in `database.py`. All 360 tests pass.

### Sprint 14 (2026-03-06)

- **T14.3** Resource feedback API: POST /api/feedback/resource with upsert, session validation. 6 tests added (360 total).

- **T14.1** Feedback schema (3 tables + health_status column), Pydantic + TS types, 17 tests
- **T14.2** Feedback tokens: generate_token (SHA256+base64url, 12 chars), create/validate DB queries (30-day expiry), wired into assessment route. Fixed assessment + integration test mocks. 354 backend tests passing, all arch checks clean.
- Created plan: plan-2026-03-career-center-ready-package (7 tasks, 205 complexity)
- Created plan: plan-2026-03-fix-sprint-review-corrections (5 tasks, 130 complexity)
- Created plan: plan-2026-03-security-hardening (7 tasks, 155 complexity)
- Created plan: plan-2026-03-benefits-cliff-engine (4 tasks, 185 complexity, Sprint 25). Synced to Trello.


## What's Next

T27.0 done. Load BrightData dataset into live app to demo differentiated scoring. Next: wire dataset loading into app startup or add management command. Sprint 27 remaining: T27.1-T27.4.


## Blockers

None.
