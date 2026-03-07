# Current State

> Last updated: 2026-03-06

## Active Plan

**Plan:** plan-2026-03-feedback-loop
**Type:** feature
**Title:** Feedback Loop & Continuous Improvement
**Status:** In Progress
**Current Sprint:** 14

## Previous Plans

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

Sprint 14: Feedback loop — token auth, resource feedback, visit feedback, resource health decay.

## Task Status

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

## What Was Just Done

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


## What's Next

1. ~~T16.1 (StaticPool fix)~~ done
2. ~~T16.2 (Resource affinity routing)~~ done
3. ~~T16.3 (Barrier priority ordering)~~ done
4. ~~T16.5 (Architecture known limitations)~~ done
5. ~~T16.4 (Cloud deployment documentation)~~ done
6. Sprint 16 complete.
7. T14.4 (Resource feedback UI) — done
8. ~~T14.5 (Visit feedback API)~~ done
9. ~~T14.6 (Visit feedback form)~~ done
10. ~~T14.7 (QR code in PDF)~~ done
11. ~~T14.8 (Resource health check)~~ done
12. ~~Sprint 14 complete (8/8).~~
13. ~~T15.1 (WIOA screener)~~ done
14. ~~T15.2 (Career Center Package data model + assembler)~~ done
15. ~~T15.4 (Wire WIOA into generate_plan)~~ done
16. ~~T15.7 (Frontend types + API client)~~ done
17. ~~T15.3 (Career center route)~~ done
18. ~~T15.5 (Frontend component)~~ done
19. ~~T15.6 (PDF export button)~~ done
20. Sprint 15 complete (7/7).


## Blockers

None.
