# Feature Brief: Sprint 23 — Assessment Authoring Pipeline

## Idea

Stand up the Mercor-style assessment authoring substrate. Claude drafts an assessment (from a job description, topic prompt, or skill probe spec), it lands in a reviewer queue, an approved reviewer (case_manager / sme_reviewer / dao_reviewer) edits or approves it, and the publish action locks a version with full provenance. Public fetch returns only published versions; candidates' future scores reference the locked version they took.

This sprint is the **substrate**. It does not ship:
- Candidate-side assessment-taking UI (Sprint 25/26)
- Scoring engine that consumes responses → competency vector (Sprint 25/26)
- Matching engine integration of competency vectors (Sprint 25/26)
- Vocational question bank (Sprint 25) or DAO-tech question bank (Sprint 26)

What it does ship: the authoring pipeline + reviewer dashboard + publish flow + a postgres test isolation rebuild that unblocks the deferred S22 follow-up.

## Codebase Context

- **Stack:** Python 3.11+ / FastAPI (backend), Next.js 15 / React / TypeScript (frontend), Postgres on Alembic (S22 substrate), Anthropic Claude API for draft generation (existing `app.ai` client).
- **Size:** 684 source files / 686 test files (~1:1 ratio) post-S22.
- **Current sprint:** Sprint 22 (Identity Foundation) merged on 2026-05-06 / 07. PR #123 closed. 5 stale `in_progress` tasks (T1.7, T12.5, T12.16, T12.21, T12.24) noise — none touch Sprint 23 surface.
- **Sprint 22 deliverables this sprint relies on:** `accounts` / `account_sessions` / `account_credentials` / `account_roles` tables; `require_role(role)` FastAPI dependency (now cookie-based per the review fix); magic-link auth so reviewers can sign in; anonymous-first invariant test guarding the rest of the app; alembic chain through 0012; `legacy_ddl_translator` for postgres dialect handling.

## Sprint-Level Constraints

- **Cross-task arch constraint — `backend/app/routes/auth.py` is at 301 lines** (warn threshold 200, error 400). S22 grew it to host `/auth/magic-link`, `/auth/claim`, `/auth/me`. Sprint 23 must NOT extend it further — admin/assessment routes land in their own modules (`routes/assessments_admin.py` and `routes/assessments_review.py`). This is a cross-task constraint because multiple S23 tasks would naturally want to drop endpoints into auth.py and they must not.
- **Anonymous-first invariant must hold for `T23.6` public fetch.** The `tests/test_anonymous_first_invariant.py` auto-discovery picks up new session-id routes; if T23.6 takes a `session_id` it must continue to work for anonymous and claimed sessions equivalently. If T23.6 doesn't take session_id, no invariant exposure.
- **`require_role` enforcement.** All reviewer endpoints (T23.4, T23.5) gated by the now-secure cookie-based `require_role` from S22. Tests must verify 403 for missing/tampered cookies AND missing roles.
- **Charter compliance.** No commercial signals in assessment authoring. Reviewer assignments are role-based, never money-based. Drafts and reviews must carry full provenance (who-drafted, who-reviewed, who-approved, when) per integrity charter principle 4 (auditability).
- **TODOs in feature path:** none.

## Tasks

### T23.1 — Alembic migration: assessments + versions + questions + reviews tables
- **Cx:** 25 / **Priority:** P0 / **Depends on:** none
- **Files:** `backend/alembic/versions/0013_assessments.py`, `backend/app/core/assessments_schema.py`
- **AC template:** schema
- **Custom AC:**
  - [ ] `assessments(id PK, slug UNIQUE, kind ENUM[skill_probe, situational, knowledge_check, work_sample], track ENUM[vocational, dao_tech, generic], created_by FK accounts, created_at)`
  - [ ] `assessment_versions(id PK, assessment_id FK, version_number, status ENUM[draft, in_review, approved, published, retired], drafted_by FK accounts, reviewed_by FK accounts (nullable), approved_by FK accounts (nullable), published_at (nullable), retired_at (nullable))`
  - [ ] `assessment_questions(id PK, version_id FK, position, prompt, kind ENUM[mcq, freeform, code, scenario], rubric_json, scoring_weight DEFAULT 1.0)`
  - [ ] `assessment_reviews(id PK, version_id FK, reviewer_id FK accounts, action ENUM[approve, reject, request_revision], comment, created_at)`
  - [ ] SQLAlchemy Core `Table` definitions in `assessments_schema.py` (mirrors S22 accounts_schema.py pattern — dialect-aware DDL on both engines)
  - [ ] `apply_ddl(connection)` helper scoped to the four tables
  - [ ] Both sqlite and postgres run clean

### T23.2 — queries_assessments.py CRUD module
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T23.1
- **Files:** `backend/app/core/queries_assessments.py`, `backend/tests/test_queries_assessments.py`
- **AC template:** CRUD
- **Custom AC:**
  - [ ] `create_assessment(slug, kind, track, created_by)` returns id
  - [ ] `create_draft_version(assessment_id, drafted_by, questions: list[dict])` creates assessment_version + questions atomically
  - [ ] `list_pending_reviews(reviewer_role)` filters by track-relevant role (case_manager + vocational; sme_reviewer + any; dao_reviewer + dao_tech)
  - [ ] `record_review(version_id, reviewer_id, action, comment)` inserts into assessment_reviews + transitions version status
  - [ ] `publish_version(version_id, approved_by)` sets status=published + published_at, locks the version (subsequent edits blocked)
  - [ ] `get_published_version(slug)` returns latest published version + its questions for public fetch
  - [ ] All queries work on both sqlite and postgres (uses SQLAlchemy text() with named binds)

### T23.3 — Claude-draft generation endpoint
- **Cx:** 25 / **Priority:** P0 / **Depends on:** T23.2
- **Files:** `backend/app/routes/assessments_admin.py` (new), `backend/app/ai/assessment_drafter.py` (new), `backend/tests/test_assessment_drafter.py`
- **AC template:** API endpoint + AI integration
- **Custom AC:**
  - [ ] `POST /api/admin/assessments/draft` accepts `{slug, kind, track, source_prompt}` (source_prompt = job description text or skill spec)
  - [ ] Gated by `require_role("admin")` or `require_role("sme_reviewer")` (drafters); 403 otherwise
  - [ ] Calls `app.ai.client` with a structured prompt that returns `{questions: [...]}` JSON (use existing prompt_router pattern)
  - [ ] Validates Claude output schema (Pydantic) — rejects malformed responses with 502
  - [ ] Persists via `queries_assessments.create_assessment` + `create_draft_version`; returns `{assessment_id, version_id, status: "draft"}`
  - [ ] Rate-limited 10/hour per account (uses existing `RateLimiter`)
  - [ ] Tests use mock provider for deterministic output; live Claude call deferred to manual verification

### T23.4 — Reviewer queue API
- **Cx:** 25 / **Priority:** P0 / **Depends on:** T23.2
- **Files:** `backend/app/routes/assessments_review.py` (new), `backend/tests/test_assessments_review.py`
- **AC template:** API endpoint
- **Custom AC:**
  - [ ] `GET /api/admin/assessments/pending` returns drafts visible to the requesting reviewer's role (filtered via `list_pending_reviews`)
  - [ ] `GET /api/admin/assessments/{version_id}` returns full version + questions for review
  - [ ] `POST /api/admin/assessments/{version_id}/review` accepts `{action: approve|reject|request_revision, comment}`; records review + transitions status
  - [ ] All routes gated by `require_role` for one of `case_manager` / `sme_reviewer` / `dao_reviewer`
  - [ ] Tests cover anonymous-403, wrong-role-403, correct-role + each action

### T23.5 — Publish endpoint (lock + provenance)
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T23.4
- **Files:** `backend/app/routes/assessments_review.py` (extend), `backend/tests/test_assessments_publish.py`
- **AC template:** API endpoint
- **Custom AC:**
  - [ ] `POST /api/admin/assessments/{version_id}/publish` triggered ONLY when status=approved
  - [ ] Gated by `require_role("admin")` (publish authority is narrower than review authority)
  - [ ] Sets `published_at`, status=published, locks version (subsequent question/version edits return 409)
  - [ ] Returns `{assessment_id, version_id, slug, published_at, public_url}` where public_url is the path consumed by T23.6
  - [ ] Provenance preserved on the version row: drafted_by, reviewed_by, approved_by, published_at — all four populated

### T23.6 — Public assessment-fetch endpoint (version-locked, anonymous-friendly)
- **Cx:** 10 / **Priority:** P0 / **Depends on:** T23.5
- **Files:** `backend/app/routes/assessments_public.py` (new), `backend/tests/test_assessments_public.py`
- **AC template:** API endpoint
- **Custom AC:**
  - [ ] `GET /api/assessments/{slug}` returns the latest published version + questions
  - [ ] Anonymous and claimed sessions both work — anonymous-first invariant test must include this route and pass
  - [ ] 404 if no published version exists for the slug (drafts are never publicly fetchable)
  - [ ] Response is cacheable (sets `Cache-Control: public, max-age=60` so frequent re-fetches don't hit DB)
  - [ ] Tests cover unpublished-404, published-200, claimed-vs-anonymous-equivalence

### T23.7 — Frontend reviewer dashboard pages
- **Cx:** 30 / **Priority:** P0 / **Depends on:** T23.6
- **Files:** `frontend/src/app/admin/assessments/page.tsx` (list pending), `frontend/src/app/admin/assessments/[versionId]/page.tsx` (detail + review actions), `frontend/src/lib/api/assessments.ts`, `frontend/src/__tests__/admin/assessments/`
- **AC template:** page + API client
- **Custom AC:**
  - [ ] List page: shows pending drafts, filters by track / kind / status, links to detail
  - [ ] Detail page: shows questions, reviewer's role-relevant action buttons (approve / reject / request_revision), comment field
  - [ ] Admin-only "publish" button on approved versions (calls T23.5 endpoint)
  - [ ] Hidden / 403-redirected if `useAccount()` returns null OR account lacks any of (case_manager, sme_reviewer, dao_reviewer, admin)
  - [ ] Styled with shadcn/Tailwind matching GoWork palette (cyan/amber/rose)
  - [ ] vitest coverage for all three pages + API client

### T23.8 — Reviewer dashboard auth + role-aware nav
- **Cx:** 10 / **Priority:** P0 / **Depends on:** T23.7
- **Files:** `frontend/src/components/auth/RoleGate.tsx` (new), `frontend/src/components/nav/RoleAwareNav.tsx` (new), `frontend/src/app/admin/layout.tsx` (extend)
- **AC template:** integration
- **Custom AC:**
  - [ ] `<RoleGate roles={[...]}>` wraps protected page content; renders nothing (or a redirect) if `useAccount()` doesn't have the role
  - [ ] Role state surfaced via a new `useAccountRoles()` hook (extends `useAccount` from S22 with a roles list — backend `/api/auth/me` extended to return roles)
  - [ ] Top nav shows "Reviewer Dashboard" link only for accounts with at least one reviewer role
  - [ ] vitest coverage for RoleGate (allowed / denied / loading states)

### T23.9 — Postgres test transaction-per-test isolation
- **Cx:** 20 / **Priority:** P1 / **Depends on:** none
- **Files:** `backend/tests/conftest.py` (rewrite db_engine fixture for postgres axis), `.github/workflows/ci.yml` (re-add identity tests to postgres axis)
- **AC template:** test infrastructure
- **Custom AC:**
  - [ ] Postgres axis fixture wraps each test in a `BEGIN ... ROLLBACK` so data state never leaks across tests
  - [ ] Schema setup happens once per session (not per test) via session-scoped fixture
  - [ ] Identity tests (test_accounts, test_roles, test_auth_*) added back to the postgres CI scope
  - [ ] CI passes both axes on the full identity layer
  - [ ] Closes the deferred follow-up noted in `.github/workflows/ci.yml` comment

### T23.10 — Sprint 23 integration gate
- **Cx:** 10 / **Priority:** P0 / **Depends on:** T23.4, T23.6, T23.8, T23.9
- **Files:** integration check across multiple
- **AC template:** integration gate
- **Custom AC:**
  - [ ] Full backend test suite green on sqlite + postgres (with T23.9 in place)
  - [ ] Frontend vitest green
  - [ ] `ruff check .` clean on touched files; `bpsai-pair arch check .` no new violations
  - [ ] `auth.py` line count unchanged (Sprint 23 invariant: don't grow it)
  - [ ] state.md reconciled
  - [ ] Smoke test: end-to-end draft → review → approve → publish → public-fetch path exercised by integration test
  - [ ] PR pushed; CI green

## Dependency Graph

```
Wave 0 (entry):     T23.1 ──┐                T23.9 (independent infra)
                            │
Wave 1:             T23.2 ──┘
                    │
Wave 2:             T23.3 ─┬─ T23.4
                           │
Wave 3:                    T23.5
                           │
Wave 4:                    T23.6
                           │
Wave 5:                    T23.7
                           │
Wave 6:                    T23.8
                           │
Wave 7 (GATE):             T23.10
```

## File Collision Matrix

| Wave | Tasks parallel | Shared files | Resolution |
|---|---|---|---|
| 0 | T23.1, T23.9 | none — alembic versions/0013 vs conftest+env+ci | clean |
| 2 | T23.3, T23.4 | none — assessments_admin.py vs assessments_review.py | clean |

No serialization-by-collision needed beyond the dependency graph.

## Sprint Budget

- **Total Cx:** 190
- **Task count:** 10
- **P0 count:** 9 (T23.1, T23.2, T23.3, T23.4, T23.5, T23.6, T23.7, T23.8, T23.10)
- **P1 count:** 1 (T23.9 — postgres test isolation; nice-to-have but not blocking the sprint substrate)
- **P2 count:** 0

If budget pressure surfaces, T23.9 is the only cuttable scope — the dialect-portability layer already verified by S22 covers the schema-portability story; the identity-layer tests stay sqlite-only until a future sprint.

## Integration Points (cross-task only)

- **T23.1 → T23.2:** schema tables backed by SQLAlchemy Core MetaData; CRUD module imports the Table objects
- **T23.2 → T23.3 / T23.4:** CRUD surface used by both draft-generation and reviewer-queue routes
- **T23.4 → T23.5:** review state-machine action `approve` is the precondition for publish
- **T23.5 → T23.6:** only published versions are publicly fetchable
- **T23.6 → T23.7:** frontend reads via the public + admin endpoints; both must exist before the dashboard can render
- **T23.7 → T23.8:** RoleGate wraps the dashboard pages; dashboard must exist first
- **`/api/auth/me` extension (T23.8):** backend `/api/auth/me` (from S22 T22.11) needs to also return `roles: [...]` so `useAccountRoles()` can read them. Small additive change inside T23.8 scope; flagged here since it crosses S22 → S23.

## Out of Scope

Explicit boundaries — these come in later sprints, not Sprint 23:

- Candidate-side assessment-taking UI → Sprint 25/26
- Scoring engine / response evaluation → Sprint 25/26
- Competency vector → matching engine integration → Sprint 25/26
- Vocational question bank (CDL, customer-service, numeracy) → Sprint 25
- DAO-tech question bank → Sprint 26
- Phone-OTP login → Sprint 25 (deferred from S22)
- OAuth providers (Google / Apple / Discord) → Sprint 25 (deferred from S22)
- Wallet linkage → Sprint 29
- Two-sided employer / listing verification → Sprint 24
- Gamification mechanics → Sprint 27
- Multi-tenant cohort dashboards → Sprint 30

The reviewer pilot (TCC + FW DAO partner sign-off) stays a sprint-25/26 conversation since it's content-driven, not infra-driven. Sprint 23 stands up the pipeline; Sprint 25/26 fills it with content.

## Open Questions (defaults picked; revisit during engage if any bites)

1. **Claude model for drafting:** `claude-sonnet-4-6` default? Or Haiku for cost? Default: Sonnet for quality, with a config flag to swap to Haiku later. T23.3 reads `Settings.assessment_drafter_model`.
2. **Publish-revoke workflow:** can a published version be retired? Default: yes (status=retired), but no UI for it in S23 — admin-only via direct DB or future endpoint. Add `retire_version()` query but skip the route until needed.
3. **Question rubric format:** free-form JSON or structured Pydantic? Default: JSON column with a Pydantic validator at write time so the structure is enforced without locking schema migrations to every rubric tweak.
4. **Track filtering on pending-queue:** strict (case_manager only sees vocational) or permissive (any reviewer sees any track)? Default: strict per the role-track mapping in T23.2 AC. SME reviewers see all (they're the cross-track tier).
