# Current State

> Last updated: 2026-03-08

## Active Plan

**Plan:** plan-2026-03-barrier-graph-rag
**Type:** feature
**Title:** Barrier Graph + RAG — Barrier Intelligence Assistant
**Status:** Planned (pending Trello sync)
**Current Sprint:** 19

## Previous Active Plan

**Plan:** plan-2026-03-security-hardening
**Type:** bugfix
**Title:** Security Hardening — Issue #20 Remediation
**Status:** Complete
**Sprint:** 18

## Previous Plans

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

Sprint 23: Barrier Graph + RAG — Barrier Intelligence Assistant. Adds graph-aware AI assistant to `/plan` page with root cause analysis, step-by-step action plans, and explainability UI.

## Task Status

### Sprint 23 — Barrier Graph + RAG (Barrier Intelligence Assistant)

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T23.1 | Barrier graph DB schema: Alembic migration + seed data | P0 | 55 | done | -- |
| T23.2 | Barrier-resource mapping: join table, impact scores, top-N query | P0 | 45 | done | T23.1 |
| T23.3 | RAG knowledge base: document schema + FAISS ingestion pipeline | P0 | 60 | done | T23.1, T23.2 |
| T23.4 | Hybrid retrieval layer: vector + metadata filter + graph context assembly | P0 | 50 | done | T23.2, T23.3 |
| T23.5 | LLM orchestration + guardrails: POST /api/barrier-intel/chat + SSE streaming | P0 | 70 | done | T23.4 |
| T23.6 | Frontend: BarrierIntelChat + SSE streaming + explainability UI | P1 | 70 | done | T23.5 |
| T23.7 | NFRs: caching, observability, rate limiting + eval suite | P2 | 55 | pending | T23.5, T23.6 |

**Total: 7 tasks, 405 complexity points (6/7 done)**

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

### Sprint 24 T24.6 (2026-03-08) — Frontend BarrierIntelChat

- **T24.6** Frontend barrier intel chat: Created `SuggestedQuestions` (3 default chips), `EvidenceChips` (secondary badge chips), `ChatMessage` (user/assistant bubbles + streaming indicator), `ExplainSteps` (numbered list with collapsible "Why this step?" and Badge barrier tags), `BarrierIntelChat` wrapper (suggested questions, Explain this plan button with mode=explain_plan, error alert). Created `useBarrierIntelStream` hook (SSE reader: context→token→done events, status machine idle/streaming/done/error). Wired into `/plan` page as sticky sidebar (desktop) / inline (mobile) using responsive grid. Fixed vitest ESM compat by switching to `happy-dom`. 19 new tests, 223 total passing. All arch checks clean.

### Sprint 24 T24.5 (2026-03-08) — LLM Orchestration + SSE Streaming

- **T24.5** LLM orchestration: Created `app/barrier_intel/` module — `schemas.py` (ChatRequest with Literal mode validation), `guardrails.py` (topic filter: legal/medical/immigration patterns, hallucination check), `prompts.py` (SYSTEM_PROMPT, build_user_prompt serializing RetrievalContext), `audit_log.py` (PII-safe JSONL: sha256[:12] session hash), `stream.py` (async generator: context→token→done SSE events, Claude streaming). Added `POST /api/barrier-intel/chat` to router with 10/min rate limiter, 404 on missing session, guardrail short-circuit. 13 new tests, 599 total. All arch checks clean.

### Sprint 24 T24.4 (2026-03-08) — Hybrid Retrieval Layer

- **T24.4** Hybrid retrieval layer: Created `barrier_graph/traversal.py` with `find_root_barriers()` (BFS detecting barriers with no incoming CAUSES edges within user's set, priority-sorted: childcare=1, transportation=2...). Added `RagStore.search()` (embed query → FAISS top-k*2 → post-filter by barrier_tags overlap → top-k). Created `rag/retrieval.py` with `retrieve_context()` (assembles RetrievalContext: root barriers, chain summary, top resources, FAISS docs, latency_ms). Added `RetrievalContext` model to `document_schema.py`. 10 new tests, 586 total. All arch checks clean.

### Sprint 24 T24.3 (2026-03-08) — RAG Knowledge Base

- **T24.3** RAG knowledge base: Created `app/rag/` module with `document_schema.py` (RagDocument Pydantic model with barrier_tags validator), `corpus_builder.py` (loads resources+playbooks from DB → RagDocuments), `ingestion.py` (sentence-transformers/all-MiniLM-L6-v2, 384-dim IndexFlatIP, build/save/load), `store.py` (RagStore singleton with build_or_load+rebuild). Created `POST /api/barrier-intel/reindex` (admin-only via X-Admin-Key). Wired `init_rag_store` into `main.py` lifespan after barrier graph seed. Added `*.faiss` to .gitignore, `backend/data/rag_index/.gitkeep`. 14 new tests, 576 total. All arch checks clean.

### Sprint 24 T24.2 (2026-03-08) — Barrier-Resource Mapping

- **T24.2** Barrier-resource mapping: Added `barrier_resource_rules` array (11 rules) to `data/barrier_graph_seed.json` mapping all resource categories/subcategories to barrier node IDs with impact scores. Extended `seed.py` with `_upsert_barrier_resources()` that queries resources by category/subcategory and inserts barrier_resources rows via INSERT OR IGNORE. Created `backend/app/barrier_graph/queries.py` with `get_top_resources_for_barriers()` (SUM aggregation, HIDDEN exclusion, top-N limit) and `_build_top_resources_query()` helper. 9 new tests (minimum count ≥50, all resources linked, impact range, idempotency, top-N ranking, HIDDEN exclusion, required fields, empty input). All arch checks clean. 562 total tests pass.

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


## What's Next

1. Start T24.7 (NFRs: caching, observability, rate limiting + eval suite)
2. Commit and push T24.6 changes to repo


## Blockers

None.
