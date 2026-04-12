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

- **Sprint S3 Phase 2 -- Evolution + Hardening** (2026-04-11): S2 routing audit and S3 feature evolution. Fixed all Alabama bypasses in cliff_calculator (uses TX AMI $78K for Fort Worth), eligibility_screener (HHSC disclaimer), types.py (dynamic ZIP validation), pvs_scorer, scoring.py, commute_estimator, barrier_cards, affinity, career_center_package, filters, phase_generators, job_readiness_pathway -- all now route through city-aware routers. Built barrier sequencing engine (topological sort of 33 barriers, 53 edges). Evolved ProgressTracker (localStorage persistence), BenefitsCliffSimulator (loading/error states, ARIA), ResourceMap (category filtering), i18n (locale persistence). 28 new tests. 1742 backend / 630 frontend tests passing. Zero regressions.

- **Sprint S2 complete** (2026-04-12) -- Fort Worth Data + Texas Rules: Full multi-city port for HackFW 2026. Created Texas benefits screener with HHSC programs (CHIP replaces ALL_Kids at 200% FPL, CEAP replaces LIHEAP, TX TANF at ~$308/mo vs AL $215), Texas expunction (Art. 55) + nondisclosure (Gov Code Ch. 411 E-1) dual record clearing, Fort Worth geo data (36 ZIP centroids, Trinity Metro hours), city-aware module routing (benefits, criminal, geo, resources, AI prompts), live TWC and USAJobs API adapters replacing stubs, Fort Worth seed data (10 community resources, 12 employers with fair-chance index), and frontend city-aware constants. 112 new S2 tests + 1707 total backend tests passing (zero regressions). 512 frontend tests passing.

## What's Next

Sprint S3 Phase 2 remaining -- SharedPlanView backend endpoints (POST /api/plan/{session_id}/share, GET /api/plan/shared/{token}), share plan frontend wiring, remaining matching module routing (prompts.py -- already has prompt_router.py), push test coverage to 95%+, hackathon demo polish.

## Blockers

- T28.3: Requires findhelp.org API partnership (external dependency).
