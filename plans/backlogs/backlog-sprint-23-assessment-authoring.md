# Sprint 23 — Assessment Authoring Pipeline

**Plan type:** feature
**Sprint:** 23
**Total Cx:** 190
**Tasks:** 10 (P0: 9, P1: 1, P2: 0)
**Brief:** `.paircoder/plans/briefs/brief-sprint-23-assessment-authoring.md`
**Builds on:** Sprint 22 (Identity Foundation) — accounts/sessions/credentials/roles tables, magic-link auth, anonymous-first invariant test, alembic chain through 0012, `legacy_ddl_translator` helpers.

## Goal

Stand up the Mercor-style assessment authoring substrate. Claude drafts an assessment from a job description / topic prompt / skill spec. It lands in a reviewer queue. An approved reviewer (case_manager / sme_reviewer / dao_reviewer) edits or approves it. The publish action locks a version with full provenance (drafted_by + reviewed_by + approved_by + published_at). Public fetch returns only published versions; future candidate scores reference the locked version they took.

This is the **substrate**. Sprints 25/26 fill the pipeline with content (vocational + DAO-tech question banks) and ship the candidate-side taking UI, scoring engine, and competency-vector consumption by the matching engine. Sprint 23 also rebuilds the postgres test isolation deferred from S22 so identity-layer tests can run on postgres CI again.

## What ships in S23 vs deferred

**S23 (this sprint):** Schema for assessments / versions / questions / reviews. CRUD module. Claude-draft generation endpoint with rate limiting and structured output validation. Reviewer queue API (list / detail / approve / reject / request_revision). Publish endpoint with provenance lock. Public fetch endpoint with anonymous-first compliance and HTTP caching. Frontend reviewer dashboard (list + detail + action buttons + admin-only publish). `<RoleGate>` component + role-aware nav. `useAccountRoles()` hook + `/api/auth/me` extension to return roles. Postgres test transaction-per-test isolation rebuild + identity tests re-added to postgres CI.

**Deferred to S24+:** Two-sided employer / listing verification (S24). Vocational question bank — CDL, customer-service, numeracy (S25). DAO-tech question bank — coding, civic-tech, AI/ML (S26). Candidate-side assessment-taking UI (S25/S26). Scoring engine + competency-vector matching (S25/S26). Phone-OTP login (S25). OAuth providers (S25). Reviewer pilot with TCC + FW DAO partners (S25/S26 — content-driven, not infra). Wallet linkage (S29). Multi-tenant cohort dashboards (S30).

## Architectural principles

- **`auth.py` is at 301 lines (warn=200, error=400).** Sprint 23 must NOT extend it. Admin/assessment routes land in their own modules: `routes/assessments_admin.py`, `routes/assessments_review.py`, `routes/assessments_public.py`. The integration gate (T23.10) verifies auth.py line count is unchanged.
- **Anonymous-first invariant.** The public fetch endpoint (T23.6) must work for both anonymous and account-claimed sessions. The auto-discovery test from S22 enforces this on every session-id route; T23.6 must pass without exemption.
- **Reviewer endpoints gated by `require_role`.** Use the cookie-based version from S22 (post-review-fix). All routes verify 403 for missing/tampered cookies AND missing roles.
- **Charter compliance.** Provenance preserved on every published version: drafted_by + reviewed_by + approved_by + published_at all populated. Reviewer assignments are role-based, never money-based. Drafts never publicly fetchable.
- **Dialect-aware schema.** New schema uses SQLAlchemy Core MetaData (mirrors S22 accounts_schema.py pattern) so DDL is correct on both sqlite and postgres without dialect translation.
- **400-line file ceiling, arch-check clean.** The new route modules must not cross the threshold; new core modules under 400 lines.

---

## Phase 1: Foundation — schema + CRUD + postgres test isolation

### T23.1 — Alembic migration: assessments + versions + questions + reviews tables | Cx: 25 | P0

**Description:**
Add the four-table identity-of-content layer. Alembic revision 0013 with `down_revision='0012'`. Uses SQLAlchemy Core MetaData mirroring S22's `accounts_schema.py` pattern so DDL is dialect-correct on both engines without translation. The `assessments` row is the durable identity (slug, kind, track); each `assessment_version` is a frozen-on-publish snapshot; `assessment_questions` belong to a version (not the assessment) so revisions can change question content without breaking past scores; `assessment_reviews` records the review trail.

**AC:**
- [ ] `backend/alembic/versions/0013_assessments.py` (revision 0013, down_revision 0012)
- [ ] `backend/app/core/assessments_schema.py` defines four `Table` objects on a shared `MetaData`
- [ ] `assessments(id PK, slug VARCHAR(160) UNIQUE, kind ENUM, track ENUM, created_by FK accounts(id), created_at, retired_at NULL)`
- [ ] `assessment_versions(id PK, assessment_id FK, version_number INT, status ENUM, drafted_by FK accounts, reviewed_by FK accounts NULL, approved_by FK accounts NULL, published_at NULL, retired_at NULL, created_at)` with UNIQUE(assessment_id, version_number)
- [ ] `assessment_questions(id PK, version_id FK, position INT, prompt TEXT, kind ENUM, rubric_json TEXT, scoring_weight REAL DEFAULT 1.0)` with UNIQUE(version_id, position)
- [ ] `assessment_reviews(id PK, version_id FK, reviewer_id FK accounts, action ENUM[approve, reject, request_revision], comment TEXT, created_at)`
- [ ] ENUMs enforced via CHECK constraints (portable across sqlite + postgres — same pattern as S22 `account_roles`)
- [ ] `apply_ddl(connection)` helper scoped to the four tables for test fixtures
- [ ] Indexes: `(track, status)` on assessment_versions for the reviewer-queue hot path; `slug` already unique on assessments
- [ ] `alembic upgrade head` runs clean on fresh sqlite + postgres
- [ ] `bpsai-pair arch check backend/app/core/assessments_schema.py` passes

**Depends on:** none

---

### T23.2 — queries_assessments.py CRUD module | Cx: 20 | P0

**Description:**
The CRUD surface consumed by every backend endpoint in this sprint. Async SQLAlchemy with named bind params (driver-agnostic). Status transitions enforced at the query layer (you can't publish a non-approved version; you can't review a published version). Track-aware reviewer-queue filtering: case_manager sees vocational + generic, dao_reviewer sees dao_tech + generic, sme_reviewer sees all.

**AC:**
- [ ] `backend/app/core/queries_assessments.py` with the following async functions:
  - [ ] `create_assessment(session, slug, kind, track, created_by) -> int`
  - [ ] `create_draft_version(session, assessment_id, drafted_by, questions: list[dict]) -> int` — atomic insert of version + questions
  - [ ] `list_pending_reviews(session, *, reviewer_role: str) -> list[dict]` — track-aware filter; status in (draft, in_review, request_revision)
  - [ ] `get_version_with_questions(session, version_id) -> dict | None` — version row + questions ordered by position
  - [ ] `record_review(session, version_id, reviewer_id, action, comment) -> int` — inserts review row + transitions version status (draft → in_review → approved | request_revision; rejected terminates)
  - [ ] `publish_version(session, version_id, approved_by) -> None` — guards status==approved; sets status=published + published_at; raises ValueError otherwise
  - [ ] `get_published_version(session, slug) -> dict | None` — latest published version + questions for public fetch
  - [ ] `retire_version(session, version_id) -> None` — admin-only; status → retired, retired_at = now (no route this sprint, just the query)
- [ ] `backend/tests/test_queries_assessments.py` covers happy-path + invalid-status-transition guards (24+ tests)
- [ ] All queries work on both sqlite and postgres

**Depends on:** T23.1

---

### T23.9 — Postgres test transaction-per-test isolation | Cx: 20 | P1

**Description:**
Closes the deferred S22 follow-up. Replaces the `DROP SCHEMA public CASCADE` teardown (which lost races against pooled connections in CI) with a transaction-per-test pattern: each test runs inside `BEGIN ... ROLLBACK`, schema setup happens once per session via a session-scoped fixture. Identity-layer tests (test_accounts, test_roles, test_auth_*) get re-added to the postgres CI scope.

**AC:**
- [ ] `backend/tests/conftest.py` `db_engine` postgres axis rebuilt:
  - [ ] Session-scoped fixture creates schema via alembic once per pytest session
  - [ ] Per-test fixture wraps the test in `BEGIN ... ROLLBACK` so data state never leaks
  - [ ] Sqlite axis behavior unchanged (still per-test tmp file)
- [ ] `.github/workflows/ci.yml` postgres job adds `test_accounts.py`, `test_roles.py`, `test_auth_magic_link.py`, `test_auth_claim.py`, `test_auth_me.py`, `test_anonymous_first_invariant.py` to the run list
- [ ] CI passes both axes locally + on push
- [ ] Comment in `ci.yml` updated to remove the deferred-follow-up note (since it's now closed)

**Depends on:** none — independent of the assessment-authoring chain; can run in parallel with T23.1

---

## Phase 2: Backend pipeline — draft / review / publish / fetch

### T23.3 — Claude-draft generation endpoint | Cx: 25 | P0

**Description:**
`POST /api/admin/assessments/draft` accepts a slug + kind + track + source_prompt. Calls Claude via the existing `app.ai.client` to generate questions matching the assessment kind. Validates the structured response (Pydantic schema), persists the assessment + draft version, returns the version_id. Rate-limited per account. Mock provider used in tests for determinism.

**AC:**
- [ ] `backend/app/routes/assessments_admin.py` (new) exposes `POST /api/admin/assessments/draft`
- [ ] Request body: `{slug, kind, track, source_prompt}`; response: `{assessment_id, version_id, status: "draft", question_count}`
- [ ] Gated by `require_role("admin")` OR `require_role("sme_reviewer")` (drafters); 403 otherwise
- [ ] `backend/app/ai/assessment_drafter.py` (new): `draft_questions(kind, track, source_prompt) -> list[QuestionDraft]` — calls `app.ai.client` with a structured prompt routed via the existing `prompt_router`
- [ ] Pydantic `QuestionDraft` model validates `{prompt, kind, rubric, scoring_weight}` from Claude output; malformed → 502 with sanitized error
- [ ] Rate limit: 10/hour per account (reuses `app.core.rate_limit.RateLimiter`)
- [ ] `Settings.assessment_drafter_model` defaults to `claude-sonnet-4-6` (configurable to Haiku for cost)
- [ ] `backend/tests/test_assessment_drafter.py` covers: happy path with mock provider, rate-limit, malformed Claude response, role enforcement
- [ ] Live Claude call deferred to manual verification (no API key required for the mocked tests)

**Depends on:** T23.2

---

### T23.4 — Reviewer queue API | Cx: 25 | P0

**Description:**
The reviewer-side surface: list pending drafts visible to the requesting reviewer's role, fetch one for review, record a review action. Publish is its own endpoint (T23.5) since publish authority is narrower than review authority. State machine enforced at the query layer (T23.2): draft → in_review → approved | request_revision; rejected terminates.

**AC:**
- [ ] `backend/app/routes/assessments_review.py` (new) exposes:
  - [ ] `GET /api/admin/assessments/pending` — track-aware filter via `list_pending_reviews(reviewer_role)`
  - [ ] `GET /api/admin/assessments/{version_id}` — full version + questions
  - [ ] `POST /api/admin/assessments/{version_id}/review` — body `{action: approve|reject|request_revision, comment}`
- [ ] All routes gated by `require_role(any of case_manager, sme_reviewer, dao_reviewer)` — uses an `any_of` helper or three-way dependency
- [ ] `backend/tests/test_assessments_review.py` covers: anonymous-403, wrong-role-403, correct-role-200 for each action, invalid-state-transition rejected
- [ ] Track filtering verified: case_manager seeing dao_tech draft returns empty; dao_reviewer seeing vocational returns empty; sme_reviewer sees all

**Depends on:** T23.2

---

### T23.5 — Publish endpoint with provenance lock | Cx: 15 | P0

**Description:**
`POST /api/admin/assessments/{version_id}/publish` triggered ONLY when status=approved. Admin-only (publish authority is narrower than review). Sets `published_at`, status=published, locks the version (subsequent edits return 409). Returns the public URL the candidate-side will eventually consume.

**AC:**
- [ ] `backend/app/routes/assessments_review.py` extends with `POST /api/admin/assessments/{version_id}/publish`
- [ ] Gated by `require_role("admin")` — strict admin tier
- [ ] Guards: status must be approved (409 with explicit reason if not); already-published returns 409 (no double-publish)
- [ ] Sets `published_at` (utcnow) + status=published via `queries_assessments.publish_version`
- [ ] Returns `{assessment_id, version_id, slug, version_number, published_at, public_url}` where `public_url = f"/api/assessments/{slug}"`
- [ ] Provenance assertion: drafted_by, reviewed_by, approved_by, published_at all non-null on the published row
- [ ] `backend/tests/test_assessments_publish.py` covers: approve-then-publish happy path, publish-without-approve-409, double-publish-409, role-enforcement (sme_reviewer trying to publish → 403), provenance row inspection

**Depends on:** T23.4

---

### T23.6 — Public assessment-fetch endpoint | Cx: 10 | P0

**Description:**
`GET /api/assessments/{slug}` returns the latest published version + questions. Anonymous-friendly (the route MUST work for both anonymous and account-claimed sessions per the integrity charter). Drafts are never publicly fetchable — only `status=published` versions appear. Cacheable for 60s so frequent re-fetches don't hit the DB.

**AC:**
- [ ] `backend/app/routes/assessments_public.py` (new) exposes `GET /api/assessments/{slug}`
- [ ] No auth required; the route is fully public
- [ ] Anonymous-first invariant test (`test_anonymous_first_invariant.py`) auto-discovers this route and asserts equivalence between anonymous and claimed sessions
- [ ] Returns `{slug, kind, track, version_number, published_at, questions: [{position, prompt, kind, scoring_weight}]}` — note rubric_json EXCLUDED from public response (rubrics are reviewer-internal)
- [ ] 404 if no published version exists for the slug
- [ ] Sets `Cache-Control: public, max-age=60`
- [ ] `backend/tests/test_assessments_public.py` covers: published-200, draft-only-404, anon-vs-claimed-equivalence, rubric-not-leaked, cache-header

**Depends on:** T23.5

---

## Phase 3: Frontend reviewer dashboard

### T23.7 — Frontend reviewer dashboard pages | Cx: 30 | P0

**Description:**
Three pages under `/admin/assessments`: list of pending drafts (with track / kind / status filters), detail view of a single version (questions + review actions + admin-only publish button), and an API client. Styled with shadcn/Tailwind matching the existing GoWork palette (cyan/amber/rose). Hidden / 403-redirected if `useAccount()` returns null or the account lacks any reviewer role.

**AC:**
- [ ] `frontend/src/app/admin/assessments/page.tsx` — list pending drafts; filter dropdowns for track / kind / status; row click → detail
- [ ] `frontend/src/app/admin/assessments/[versionId]/page.tsx` — detail view: questions ordered by position, comment textarea, action buttons (approve / reject / request_revision), admin-only publish button visible when status=approved
- [ ] `frontend/src/lib/api/assessments.ts` — typed client: `listPendingAssessments()`, `getAssessmentVersion(versionId)`, `reviewAssessment(versionId, action, comment)`, `publishAssessment(versionId)`
- [ ] Both pages 403-redirect to `/auth/login` if `useAccount()` is null
- [ ] Both pages render "insufficient permissions" card if account lacks any reviewer role
- [ ] vitest coverage: list rendering + filters, detail rendering + action submission, API client (request/response shapes + error states)
- [ ] `npx tsc --noEmit` clean; `npx next build` green; both pages prerender or render on-demand cleanly

**Depends on:** T23.6

---

### T23.8 — Reviewer dashboard auth + role-aware nav | Cx: 10 | P0

**Description:**
Extends the S22 `useAccount()` hook with a roles list (requires backend `/api/auth/me` to start returning roles). Adds `<RoleGate roles={[...]}>` wrapper component for protected page content. Top nav shows the "Reviewer Dashboard" link only for accounts with at least one reviewer role.

**AC:**
- [ ] Backend: `/api/auth/me` extended to return `{account_id, email, roles: [...]}` — tests in `test_auth_me.py` updated
- [ ] `frontend/src/lib/api/auth.ts` `getAccountMe` return type extended with `roles: string[]`
- [ ] `frontend/src/components/auth/RoleGate.tsx` — `<RoleGate roles={["admin", "sme_reviewer"]}>` renders children only if the account has any of the listed roles; otherwise renders nothing (or a documented "permission denied" state)
- [ ] `frontend/src/components/nav/RoleAwareNav.tsx` — top-nav component that shows reviewer links only for reviewer-role accounts
- [ ] `frontend/src/app/admin/layout.tsx` extends to mount RoleGate around all admin pages
- [ ] `useAccountRoles()` convenience hook returning the roles list (or empty array)
- [ ] vitest coverage for RoleGate (allowed / denied / loading states); RoleAwareNav (rendered links per role set)

**Depends on:** T23.7

---

## Phase 4: Integration gate

### T23.10 — Sprint 23 integration gate | Cx: 10 | P0

**Description:**
Final gate. Runs the full backend test matrix on sqlite + postgres (with T23.9's transaction-per-test isolation). Frontend vitest. Lint + arch + tsc + build. Verifies `auth.py` line count is unchanged from sprint start (the cross-task constraint). End-to-end smoke: drives a draft → review → approve → publish → public-fetch path through the actual route handlers in a single integration test.

**AC:**
- [ ] Full backend test suite green on sqlite locally + in CI
- [ ] Full backend test suite green on postgres in CI (with T23.9 in place — identity-layer tests included)
- [ ] Frontend vitest green
- [ ] `ruff check .` clean on touched files
- [ ] `bpsai-pair arch check .` no new violations
- [ ] `auth.py` line count unchanged from S23 entry (assert via line-count diff in PR description)
- [ ] `tsc --noEmit` 0 errors; `next build` green
- [ ] `backend/tests/test_assessments_e2e.py` (new): end-to-end test driving draft → review → approve → publish → public fetch through the FastAPI TestClient with realistic role fixtures
- [ ] `.paircoder/context/state.md` reconciled: Sprint 23 complete entry; closed-follow-up note removed for postgres-test-isolation (since T23.9 closes it)
- [ ] PR pushed; CI green on both engine matrix axes

**Depends on:** T23.4, T23.6, T23.8, T23.9

---

## Delivery Summary

| Phase | Tasks | Cx | Output |
|---|---|---|---|
| 1. Foundation — schema + CRUD + postgres test isolation | T23.1, T23.2, T23.9 | 65 | 4 new tables, CRUD module, transaction-per-test postgres axis |
| 2. Backend pipeline — draft / review / publish / fetch | T23.3, T23.4, T23.5, T23.6 | 75 | Claude-draft endpoint, reviewer queue, publish lock, public fetch |
| 3. Frontend reviewer dashboard | T23.7, T23.8 | 40 | List + detail pages, RoleGate, role-aware nav, /api/auth/me roles extension |
| 4. Integration gate | T23.10 | 10 | E2E smoke + multi-runner verification + state.md reconcile |
| **Total** | **10** | **190** | Assessment authoring substrate ready for S25/S26 to fill with content |

## Priority Order

Engage cut-list (in order P2 → P1 → P0; cut from the top if budget overflows):

1. **P0 (cannot cut — substrate):** T23.1, T23.2, T23.3, T23.4, T23.5, T23.6, T23.7, T23.8, T23.10
2. **P1 (cuttable — postgres test infra):** T23.9 — closes a S22 follow-up but the dialect-portability layer is already proven; identity tests can stay sqlite-only one more sprint
3. **P2 (none):** This sprint has no cuttable scope beyond T23.9. The pipeline either ships end-to-end or it isn't useful.

If budget pressure surfaces, T23.9 is the only descope. Everything else is the load-bearing chain.
