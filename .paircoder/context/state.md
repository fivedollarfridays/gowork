# Current State

> Last updated: 2026-03-09

## Active Plan

**Plan:** plan-2026-03-benefits-program-eligibility
**Type:** feature
**Title:** Benefits Program Eligibility — Screening + Dashboard for Montgomery Residents
**Status:** Complete (4/4 done)
**Current Sprint:** 29

## Previous Active Plan

**Plan:** plan-2026-03-resource-auto-matching
**Type:** feature
**Title:** Resource Auto-Matching — findhelp.org Integration + Eligibility Engine
**Status:** Complete (2/3 done, T28.3 deferred — needs findhelp.org API partnership)
**Sprint:** 28

## Previous Active Plan (Sprint 25)

**Plan:** plan-2026-03-benefits-cliff-engine
**Type:** feature
**Title:** Benefits Cliff Engine — Cliff-Aware Job Ranking for Montgomery Residents
**Status:** Complete (PR #36 merged)
**Sprint:** 25

## Older Plans

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

Sprint 29: Benefits Program Eligibility. The "opportunity system" that complements Sprint 25's cliff "warning system." Shows users which benefit programs they qualify for but aren't enrolled in, with estimated monthly values, income headroom, and actionable application steps (URLs, docs, contacts). Alabama/Montgomery-specific.

## Task Status

### Sprint 29 — Benefits Program Eligibility

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T29.1 | Program Eligibility Screener Module | P0 | 45 | done | -- |
| T29.2 | Program Application Data (steps, URLs, contacts) | P0 | 30 | done | T29.1 |
| T29.3 | Engine Integration + Frontend Types | P0 | 25 | done | T29.1, T29.2 |
| T29.4 | Benefits Eligibility Dashboard UI | P1 | 40 | done | T29.3 |

**Total: 4 tasks, 140 complexity points (4/4 done) — SPRINT COMPLETE**

### Sprint 28 — Resource Auto-Matching

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T28.1 | findhelp.org Integration (Capability URLs) | P1 | 45 | done | -- |
| T28.2 | Resource Eligibility Engine | P1 | 50 | done | T28.1 |
| T28.3 | findhelp.org Deep Integration (V2) | P2 | 60 | deferred | API access |

**Total: 3 tasks, 155 complexity points (2/3 done, 1 deferred) — SPRINT COMPLETE**

### Sprint 25 — Benefits Cliff Engine (COMPLETE)

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

- **Merge conflict resolution** (2026-03-09) — Resolved conflicts between Sprint 29 (benefits eligibility) and Sprint 28 (resource auto-matching). engine.py: kept `_compute_benefits()` with lazy imports, adopted `build_barrier_cards_and_steps` from barrier_cards.py, `ResourceHealth` from feedback.types. state.md: merged both sprint histories.

- **T29.4 done** (2026-03-08) — Benefits Eligibility Dashboard UI: Created `BenefitsEligibility.tsx` with per-program rows (confidence badges via `STATUS_BADGE_STYLES`, monthly values, income headroom), enrolled vs additional-eligible grouping, expandable "How to apply" sections (steps, required docs, office name/address/phone, processing time, apply link). Uses shadcn Card/Badge, Lucide icons, `PROGRAM_LABELS` from constants. Wired into `plan/page.tsx` after barriers, before cliff chart. 11 frontend tests (null render, heading, values, badges, headroom, disclaimer, expand/collapse, enrolled distinction, a11y). `npx tsc --noEmit` clean.

- **T29.3 done** (2026-03-08) — Engine Integration + Frontend Types: Wired `screen_benefits_eligibility()` into `generate_plan()` via `_compute_benefits()` helper. Added `benefits_eligibility: Optional[BenefitsEligibility] = None` to `ReEntryPlan`. Added `EligibilityConfidence`, `ProgramApplicationInfo`, `ProgramEligibility`, `BenefitsEligibility` TS interfaces to `types.ts`. 3 new engine tests. Refactored engine imports to stay under arch limit (lazy imports for benefits modules). `npx tsc --noEmit` passes.

- **T29.2 done** (2026-03-08) — Program Application Data: Added `ProgramApplicationInfo` model to `types.py`. Created `application_data.py` with Montgomery-specific data for all 7 programs (SNAP/TANF/Medicaid/ALL_Kids/Childcare_Subsidy/Section_8/LIHEAP) — application URLs, steps, required documents, office names/addresses/phones, processing times. Section 8 includes waitlist note, LIHEAP includes seasonal note. Wired into screener: eligible programs get `application_info` attached, ineligible programs get `None`. 13 new tests in `test_benefits_application_data.py`. Split test file to satisfy arch check (49→36+15 functions). All 47 benefits tests pass, all arch checks clean.

- **T29.1 done** (2026-03-08) — Program Eligibility Screener Module: Created `eligibility_screener.py` (entry point) and `eligibility_checks.py` (per-program check functions). 7 program checks with income thresholds from `thresholds.py`, benefit value estimates from `program_calculators.py`, confidence levels (likely/possible/unlikely within 10% band). Added `EligibilityConfidence` enum, `ProgramEligibility`, `BenefitsEligibility` models to `types.py`. 34 tests covering all programs, confidence, edge cases. All arch checks clean.

- **T28.2 done** (2026-03-09) — Resource Eligibility Engine. Backend: `modules/resources/eligibility.py` with `ELIGIBILITY_RULES` (15+ rules: open, enrollment, compound income+dependents), `EligibilityStatus` enum (likely/check/unknown), `check_eligibility()` function. Added `eligibility_status: Optional[str]` to Resource model. Extracted barrier card builders to `matching/barrier_cards.py` (`build_barrier_cards_and_steps`, `_annotate_eligibility`, `_build_cards`, `_build_next_steps`, `BARRIER_TITLES`, `BARRIER_ACTIONS`) to fix engine.py arch violations (17→13 imports, 264→120 lines). Frontend: `EligibilityBadge.tsx` (green "Likely eligible" / yellow "Check eligibility" using semantic `bg-success/10` / `bg-warning/10` tokens), wired into `BarrierCardView.tsx` next to resource names. 20 backend tests, 6 frontend tests. All 1117 backend + 375 frontend tests pass, all arch checks clean.

- **T28.1 done** (2026-03-09) — findhelp.org capability URL integration. Backend: `modules/resources/findhelp.py` with `FINDHELP_CATEGORIES` mapping all 7 barrier types to findhelp.org category paths, `generate_findhelp_url()`. Frontend: `lib/findhelp.ts` (mirrored mapping), `FindhelpLink.tsx` component with external link, wired into `BarrierCardView` with zip code from sessionStorage. Zip stored during assessment. 26 backend tests, 10 frontend tests. All 1097 backend + 368 frontend tests pass.

## What's Next

Sprint 29 COMPLETE (4/4 tasks). PR #40 open, resolving merge conflicts with Sprint 28. Next sprint TBD.

## Blockers

- T28.3: Requires findhelp.org API partnership (external dependency).
