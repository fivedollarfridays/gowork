# Feature Brief: Sprint 22 — Identity Foundation

## Idea

Establish the persistent identity layer for GoWork: migrate the database from
SQLite (hand-rolled m001-m010 chain) to Postgres on Alembic, add account /
session-binding tables, ship passwordless email magic-link login, and enforce
the **anonymous-first invariant** (every API route must work for both
anonymous and account-claimed sessions). Lock the integrity charter as v1 so
revenue and verification decisions in Sprints 24+ inherit binding constraints.

This sprint is the foundation for Sprints 23–30. Nothing downstream
(assessment authoring, two-sided verification, gamification, DFW unification,
DAO integration, government contract readiness) can be cleanly built on the
current substrate.

This sprint **supersedes** in-progress T12.0 (Migration Infrastructure) and
T12.1 (Database Schema Migrations) per the 2026-05-06 user decision (option
b: roll into Sprint 22 scope). Both should be marked done with a note
referencing this brief once Sprint 22 lands.

## Codebase Context

- **Stack:** Python 3.11+ / FastAPI / Uvicorn (backend), Next.js 15 / React /
  TypeScript / Tailwind / shadcn (frontend), SQLite via aiosqlite + SQLAlchemy
  (target: dual-engine sqlite+postgres), Alembic (already a transitive dep,
  not yet wired)
- **Size:** 666 source files / 667 test files (~1:1 ratio, deep test coverage)
- **Current sprint:** S13 Platform-Wide QC + Submission Readiness (55/128
  done; remainder deferred to S13b — does not block Sprint 22)
- **Conflicting in-progress tasks:** T12.0, T12.1 — superseded; close on
  Sprint 22 completion. Other stale `in_progress` tasks (T1.7, T12.5, T12.16,
  T12.21, T12.24) are unrelated noise to triage separately.

## Sprint-Level Constraints

- **Cross-task arch constraints:** None blocking. `bpsai-pair arch check .`
  is clean across the feature path. Target files small (database.py 180,
  queries.py 182, auth.py 39, m001_initial.py 189). No oversized-file split
  prerequisites.
- **Cross-task contract edges:**
  - T22.3 (Alembic-managed schema) → T22.5 (accounts migration is the next
    alembic revision)
  - T22.5 (account_id schema) → T22.6, T22.7, T22.9
  - T22.7 (magic-link tokens) → T22.8 (claim validates them)
  - T22.8 (session-claim semantics) → T22.10, T22.11 (frontend consumes)
- **Anonymous-first invariant** is the load-bearing semantic constraint. 35
  files in `backend/app/{core,routes}` use `session_id`. The invariant must
  be auditable (T22.9 test asserts every existing endpoint still works for
  both anonymous and claimed sessions).
- **TODOs that become tasks:** None. Found one TODO in m001_initial.py
  (`montgomery_area` rename) that is orthogonal to Sprint 22 and stays
  deferred.

## Tasks

### T22.1 — Alembic infrastructure + async env
- **Cx:** 15 / **Priority:** P0 / **Depends on:** none
- **Files:** `backend/alembic.ini`, `backend/alembic/env.py`,
  `backend/alembic/script.py.mako`, `backend/alembic/versions/.gitkeep`
- **AC template:** schema (migration runner, idempotent baseline)
- **Custom AC:**
  - [ ] alembic env supports both sqlite and postgres via DATABASE_URL
  - [ ] async engine compatible (matches existing aiosqlite pattern)
  - [ ] `alembic upgrade head` runs clean on a fresh DB

### T22.2 — Postgres driver + dual-DB config
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T22.1
- **Files:** `backend/app/core/database.py`, `backend/app/core/config.py`,
  `backend/pyproject.toml` (or requirements), `backend/tests/conftest.py`
- **AC template:** refactor + schema (driver swap, no behavior change)
- **Custom AC:**
  - [ ] DATABASE_URL accepts sqlite:/// and postgresql+asyncpg://
  - [ ] DB_DIALECT config inferred from URL
  - [ ] All 279 backend tests parameterized to run against both engines
  - [ ] Fixture helper in conftest.py boots correct engine per param

### T22.3 — Port m001-m010 hand-rolled DDL into Alembic versions
- **Cx:** 30 / **Priority:** P0 / **Depends on:** T22.1, T22.2
- **Files:** `backend/alembic/versions/0001_initial.py` through
  `backend/alembic/versions/0010_geocode_resources_jobs.py` (10 new files),
  `backend/app/core/migrations/runner.py` (mark deprecated; redirect to
  alembic)
- **AC template:** migration (existing schema preserved, both engines)
- **Custom AC:**
  - [ ] Each m00X migration has a corresponding alembic revision
  - [ ] `alembic upgrade head` on fresh sqlite produces schema identical to
    current `runner.apply_pending`
  - [ ] Same on postgres
  - [ ] `runner.py` deprecated; calls forward to alembic; old tests still pass

### T22.4 — Postgres schema parity + CI service
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T22.3
- **Files:** `backend/tests/test_db_parity.py`,
  `.github/workflows/ci.yml` (add postgres service)
- **AC template:** integration gate
- **Custom AC:**
  - [ ] Postgres service available in CI
  - [ ] Parity test: write same row to sqlite + postgres, query, assert equal
  - [ ] All 279 tests pass against postgres in CI

### T22.5 — accounts + account_sessions + account_credentials tables
- **Cx:** 25 / **Priority:** P0 / **Depends on:** T22.3
- **Files:** `backend/alembic/versions/0011_accounts.py`,
  `backend/app/core/queries_accounts.py` (new),
  `backend/tests/test_accounts.py`
- **AC template:** schema + CRUD
- **Custom AC:**
  - [ ] `accounts` table: id, email, created_at, last_active_at
  - [ ] `account_sessions` link table: account_id, session_id, claimed_at
  - [ ] `account_credentials` table: account_id, credential_type
    (magic_link), credential_value, expires_at, used_at
  - [ ] One account claims many sessions; one session at most one account
  - [ ] CRUD: create_account, get_by_email, claim_session, list_sessions

### T22.6 — account_roles + reviewer permission scaffold
- **Cx:** 15 / **Priority:** P1 / **Depends on:** T22.5
- **Files:** `backend/alembic/versions/0012_account_roles.py`,
  `backend/app/core/queries_roles.py`, `backend/app/core/auth_roles.py`,
  `backend/tests/test_roles.py`
- **AC template:** schema + auth dependency
- **Custom AC:**
  - [ ] `account_roles` table: account_id, role_name (enum:
    `case_manager`, `sme_reviewer`, `dao_reviewer`, `admin`)
  - [ ] `require_role(role)` FastAPI dependency raises 403 if missing
  - [ ] One account can hold multiple roles
  - [ ] Admin-only is the working tier for this sprint; full per-role tests
    deferred to Sprint 23 when reviewer dashboard ships

### T22.7 — Magic-link issuance endpoint
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T22.5
- **Files:** `backend/app/routes/auth.py` (new),
  `backend/app/core/queries_accounts.py` (extend),
  `backend/tests/test_auth_magic_link.py`
- **AC template:** API endpoint
- **Custom AC:**
  - [ ] POST /auth/magic-link {email} → 202 Accepted (always — no email
    enumeration)
  - [ ] Email sent via existing SendGrid integration with single-use opaque
    token (≥256-bit entropy)
  - [ ] Token expires in 15 min; one-time use (used_at set on claim)
  - [ ] Rate limited per email (3/hour) and per IP (10/hour)

### T22.8 — Magic-link claim + session-claim flow
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T22.7
- **Files:** `backend/app/routes/auth.py` (extend),
  `backend/app/core/queries_accounts.py` (extend),
  `backend/tests/test_auth_claim.py`
- **AC template:** API endpoint + integration
- **Custom AC:**
  - [ ] GET /auth/claim?token=… → validates token, returns 401 if
    invalid/expired/used
  - [ ] On valid claim: any session_id present in request claims itself to
    the account; subsequent visits with same browser auto-attach
  - [ ] Returns account+session binding for client-side state
  - [ ] Pre-existing anonymous sessions can be claimed retroactively (the
    "save your progress" path)

### T22.9 — Anonymous-first invariant test
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T22.5
- **Files:** `backend/tests/test_anonymous_first_invariant.py`
- **AC template:** integration gate (test-only)
- **Custom AC:**
  - [ ] Property test: for every API route currently using session_id,
    fixture A (anonymous session) and fixture B (claimed session linked to
    an account) produce equivalent outputs (modulo account-aware response
    fields)
  - [ ] Covers all 35+ session_id-using endpoints
  - [ ] Fails CI if any endpoint regresses to require authentication

### T22.10 — Frontend login surface (magic-link UX)
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T22.7, T22.8
- **Files:** `frontend/src/app/auth/login/page.tsx`,
  `frontend/src/app/auth/claim/page.tsx`, `frontend/src/lib/api/auth.ts`,
  `frontend/src/__tests__/auth/`
- **AC template:** page + API client
- **Custom AC:**
  - [ ] /auth/login: email input → POST → "check your email" confirmation
  - [ ] /auth/claim: consumes ?token=, calls API, shows success or
    invalid-token state
  - [ ] vitest coverage for both pages + API client

### T22.11 — Account-aware client + session-claim CTAs
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T22.10
- **Files:** `frontend/src/lib/api/client.ts` (extend),
  `frontend/src/components/auth/SaveProgressCTA.tsx` (new),
  `frontend/src/app/plan/page.tsx` (insertion),
  `frontend/src/app/assess/page.tsx` (insertion)
- **AC template:** integration
- **Custom AC:**
  - [ ] React Query client surfaces `useAccount()` state
  - [ ] `<SaveProgressCTA />` rendered post-assessment, post-plan-generation,
    pre-share
  - [ ] Doesn't gate functionality — purely opt-in upgrade
  - [ ] Dismissed CTA doesn't re-show in same session

### T22.12 — Integrity charter v1
- **Cx:** 5 / **Priority:** P0 / **Depends on:** none (independent doc work)
- **Files:** `docs/integrity-charter.md`,
  `docs/integrity-charter.draft.md` (delete), `README.md` (CHARTER section)
- **AC template:** docs
- **Custom AC:**
  - [ ] User-reviewed and locked from v0.1 draft
  - [ ] Linked from README under prominent CHARTER section
  - [ ] Amendment process documented (PR + 14-day comment + maintainer +
    external partner sign-off)

### T22.13 — Sprint 22 integration gate
- **Cx:** 10 / **Priority:** P0 / **Depends on:** T22.4, T22.6, T22.9, T22.11, T22.12
- **Files:** integration check across multiple
- **AC template:** integration gate
- **Custom AC:**
  - [ ] Full backend test suite green on both sqlite + postgres
  - [ ] Frontend vitest green
  - [ ] `ruff check .` clean
  - [ ] `bpsai-pair arch check .` no new violations
  - [ ] state.md reconciled (Sprint 22 marked complete; T12.0 + T12.1 closed
    with supersede note)
  - [ ] PR pushed; CI green on both engines

## Dependency Graph

```
Wave 0 (entry):     T22.1 ──┐    T22.12 (independent doc)
                            │
Wave 1:             T22.2 ──┘
                            │
Wave 2:             T22.3 ──┤
                            │
Wave 3:             T22.4 ──┘    T22.5 ──┐
                                          │
Wave 4:                          T22.6 ───┤    T22.7 ───┐    T22.9 (test-only) ──┐
                                                         │                         │
Wave 5:                                                  T22.8 ──┐                 │
                                                                  │                 │
Wave 6:                                                           T22.10 ──┐       │
                                                                            │       │
Wave 7:                                                                     T22.11 ─┤
                                                                                    │
Wave 8 (gate):                                                                      T22.13
```

**Engage parallelism:** Wave 0 can run T22.1 + T22.12 in parallel.
Wave 3 can run T22.4 + T22.5 in parallel. Wave 4 can run T22.6 + T22.7 + T22.9
in parallel (no file collisions; see matrix). Everything else serializes by
necessity.

## File Collision Matrix

| Wave | Tasks parallel | Shared files | Resolution |
|---|---|---|---|
| 0 | T22.1, T22.12 | none | clean |
| 3 | T22.4, T22.5 | both add new files under `backend/alembic/versions/` (different filenames) | clean — net-new files |
| 4 | T22.6, T22.7, T22.9 | T22.6 → `queries_roles.py` (new), T22.7 → `queries_accounts.py` (extend), T22.9 → tests only | clean — separated by file |

No serialization-by-collision needed beyond the dependency graph.

## Sprint Budget

- **Total Cx:** 225
- **Task count:** 13
- **P0 count:** 12 (T22.1, T22.2, T22.3, T22.4, T22.5, T22.7, T22.8, T22.9,
  T22.10, T22.11, T22.12, T22.13)
- **P1 count:** 1 (T22.6)
- **P2 count:** 0 (no cuttable scope; this is foundation work)

Comparable: S12b shipped 25 tasks at 510 Cx (avg 20). Sprint 22 averages 17 Cx
across 13 tasks — slightly leaner per task because the work is well-scoped
substrate, not green-field feature design.

## Integration Points (cross-task only)

- **T22.3 → T22.5:** Alembic chain established; T22.5 adds revision 0011
  on top.
- **T22.5 → T22.6/T22.7/T22.9:** account_id schema is the contract that
  reviewer roles, magic-link issuance, and the invariant audit all depend on.
- **T22.7 → T22.8:** magic-link tokens table populated by T22.7 is the read
  side of T22.8's claim flow.
- **T22.8 → T22.10/T22.11:** session-claim API contract is what frontend
  consumes for the upgrade UX.

## Out of Scope

Explicit boundaries — these come in later sprints, not Sprint 22:

- Phone-OTP login → Sprint 23 or 25
- OAuth (Google / Apple / Discord) → Sprint 23 or 25
- Wallet linkage (ETH / DAO membership) → Sprint 29
- Account merge UI (combining sessions for the same person) → deferred
- Password-based login → never (charter principle: passwordless only)
- Multi-tenancy / multi-org accounts → Sprint 30 (gov contract readiness)
- Reviewer dashboard UI → Sprint 23 (the role scaffold lands here; the UI
  consuming it is built next sprint)
- Assessment authoring pipeline → Sprint 23
- Two-sided employer / listing verification → Sprint 24
- Gamification mechanics → Sprint 27
- DFW unification + Dallas data → Sprint 28
- DAO bounty integration → Sprint 29

The integrity charter (T22.12) is binding from the moment it's locked. Any
Sprint 24+ revenue feature must be checked against it before merging.

## Open Questions (must resolve before draft-backlog or during)

1. **Postgres in CI:** GitHub Actions service container vs. external db
   provider? Affects T22.4 setup detail. Default: GitHub Actions service.
2. **Alembic naming convention:** `0001_initial.py` (numeric) or
   `init_xxxx.py` (alembic default hash)? Default: numeric to match
   m001-m010 convention.
3. **Magic-link email template:** new template, or reuse an existing
   transactional template family? T22.7 needs the answer.
4. **Account email collision policy:** if email already exists, behavior on
   re-issuance? Default: always issue (no enumeration; same email always
   reaches same account).

These are decisions, not blockers — pick defaults and move; revisit during
engage if anything bites.
