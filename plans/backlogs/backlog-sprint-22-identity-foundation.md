# Sprint 22 — Identity Foundation

**Plan type:** feature
**Sprint:** 22
**Total Cx:** 225
**Tasks:** 13 (P0: 12, P1: 1, P2: 0)
**Brief:** `.paircoder/plans/briefs/brief-sprint-22-identity-foundation.md`
**Supersedes:** in-progress T12.0 (Migration Infrastructure) and T12.1 (Database Schema Migrations) — close on Sprint 22 completion with supersede note.

## Goal

Establish the persistent identity layer for GoWork. Migrate the database from SQLite (hand-rolled m001-m010 chain) to Postgres on Alembic, add account / session-binding tables, ship passwordless email magic-link login, and enforce the **anonymous-first invariant** — every API route must continue to work for both anonymous sessions and account-claimed sessions. Lock the integrity charter as v1 so revenue and verification decisions in Sprints 24+ inherit binding constraints.

This sprint is foundation. Nothing downstream (assessment authoring → S23, two-sided verification → S24, candidate competency → S25/S26, gamification → S27, DFW unification → S28, DAO integration → S29, government contract readiness → S30) can be cleanly built on the current substrate.

## What ships in S22 vs deferred

**S22 (this sprint):** Alembic migration runner with async support, dual-engine sqlite+postgres, Postgres CI service, port of m001-m010 to alembic versions, `accounts` / `account_sessions` / `account_credentials` tables, `account_roles` reviewer scaffold (admin tier working; full per-role tests deferred), magic-link issuance + claim endpoints, anonymous-first invariant test covering all 35+ session-using endpoints, frontend login + claim pages, account-aware client + "save your progress" CTAs, integrity charter v1.

**Deferred to S23+:** Phone-OTP login (S23/S25), OAuth providers (S23/S25), wallet linkage (S29), account merge UI, password-based login (never — charter principle), multi-tenancy / multi-org accounts (S30), reviewer dashboard UI (S23 — role scaffold lands here, dashboard consuming it next sprint), assessment authoring pipeline (S23), two-sided employer / listing verification (S24), gamification mechanics (S27), DFW unification + Dallas data curation (S28), DAO bounty integration (S29).

## Architectural principles

- **Anonymous-first invariant.** `session_id` remains the matching engine's primary key forever. `account_id` is a thin layer that *binds* sessions to a durable identity. One account claims many sessions; one session at most one account. Every API route works whether the session is claimed or not.
- **Passwordless only.** Magic-link is the entry point; phone-OTP and OAuth land in S23+. Password-based login is permanently out of scope per integrity charter.
- **No email enumeration.** `/auth/magic-link` always returns 202 regardless of whether the email exists. Claim-error responses are uniform 401.
- **Dual-engine first-class.** Every test parameterized to run against both sqlite and postgres in CI. No "postgres comes later" — it ships in this sprint or it never ships cleanly.
- **Charter-binding.** From the moment T22.12 lands, every Sprint 24+ revenue feature must be checked against the integrity charter before merge.
- **400-line files, arch-check clean.** All target files are <200 lines today; sprint must not push them over.

---

## Phase 1: Foundation — Postgres migration & charter

### T22.1 — Alembic infrastructure + async env | Cx: 15 | P0

**Description:**
Set up Alembic at `backend/alembic/` with async-engine support. Establish the migration runner that will replace the hand-rolled `m001`–`m010` chain. No schema changes in this task — purely the runner. Migration ordering convention: numeric (`0001_`, `0002_`, ...) to mirror the existing `m00X` shape.

**AC:**
- [ ] `backend/alembic.ini` configured with `script_location = alembic/`
- [ ] `backend/alembic/env.py` supports both sqlite and postgres via DATABASE_URL
- [ ] `backend/alembic/env.py` uses async engine (matches existing `aiosqlite` pattern)
- [ ] `backend/alembic/script.py.mako` template uses `0001_`-style filenames
- [ ] `backend/alembic/versions/.gitkeep` committed (empty until T22.3)
- [ ] `alembic upgrade head` runs clean against fresh empty DB on both engines
- [ ] `bpsai-pair arch check backend/alembic/env.py` passes

**Depends on:** none

---

### T22.2 — Postgres driver + dual-DB config | Cx: 20 | P0

**Description:**
Add `asyncpg` (and `psycopg[binary]` for Alembic sync ops) to project dependencies. Update `backend/app/core/database.py` to accept both `sqlite+aiosqlite://` and `postgresql+asyncpg://` URLs via `DATABASE_URL`. Update `backend/app/core/config.py` to expose `DB_DIALECT` (inferred from URL). Parameterize `backend/tests/conftest.py` so the entire 279-test backend suite runs against both engines.

**AC:**
- [ ] `asyncpg` and `psycopg[binary]` pinned in `backend/pyproject.toml` (or requirements equivalent)
- [ ] `DATABASE_URL` accepts `sqlite+aiosqlite:///` and `postgresql+asyncpg://`
- [ ] `DB_DIALECT` config inferred from URL prefix
- [ ] `backend/tests/conftest.py` exposes a `db_engine` fixture parameterized over both engines
- [ ] All 279 backend tests pass against both engines locally
- [ ] No callsite changes outside `database.py` / `config.py` / `conftest.py`
- [ ] `bpsai-pair arch check` passes on touched files

**Depends on:** T22.1

---

### T22.3 — Port m001-m010 hand-rolled DDL into Alembic versions | Cx: 30 | P0

**Description:**
Replay all 10 hand-rolled migrations as Alembic revisions in `backend/alembic/versions/`. Each `m00X_*.py` becomes `000X_*.py` with the same DDL semantics. After this task, `runner.py` is deprecated — calls forward to `alembic upgrade head` with a deprecation warning. Existing tests continue passing untouched. Both engines.

**AC:**
- [ ] 10 alembic revisions created: `0001_initial.py` through `0010_geocode_resources_jobs.py`
- [ ] Each revision's `upgrade()` produces schema byte-equivalent to `runner.apply_pending` on a fresh sqlite DB
- [ ] Same equivalence on postgres (with type-mapping notes documented in PR if any)
- [ ] `backend/app/core/migrations/runner.py` deprecated: emits `DeprecationWarning`, forwards to alembic
- [ ] `backend/app/core/schema.py` `DDL_SQL` re-export still works (backward-compat)
- [ ] All 279 tests still pass
- [ ] `bpsai-pair arch check backend/alembic/versions/` passes

**Depends on:** T22.1, T22.2

---

### T22.4 — Postgres schema parity + CI service | Cx: 20 | P0

**Description:**
Add a Postgres service container to GitHub Actions CI. Add `backend/tests/test_db_parity.py` that writes the same row to sqlite and postgres via the SQLAlchemy layer and asserts equality on read-back across all major tables. Run the full backend suite against postgres in CI as a separate job (or matrix axis).

**AC:**
- [ ] `.github/workflows/ci.yml` declares a `postgres:16` service container with health check
- [ ] CI job (or matrix axis) runs the backend suite against postgres
- [ ] `backend/tests/test_db_parity.py` covers every major table from m001–m010 (employers, transit_routes, transit_stops, resources, job_listings, sessions, feedback_tokens, visit_feedback, resource_feedback, barriers, barrier_relationships, barrier_resources, employer_policies, record_profiles, share_tokens) — round-trip equal
- [ ] All 279 tests pass against postgres in CI
- [ ] `bpsai-pair arch check` passes on the new test file

**Depends on:** T22.3

---

### T22.12 — Integrity charter v1 | Cx: 5 | P0

**Description:**
Lock the v0.1 charter draft (`docs/integrity-charter.draft.md`) as v1 (`docs/integrity-charter.md`) after Kevin's review. Add a prominent **CHARTER** section to `README.md` linking to it. Document the amendment process (PR + 14-day comment + maintainer + external partner sign-off). Charter is binding from this commit forward.

**AC:**
- [ ] User-reviewed and locked from v0.1 draft (Kevin's edits applied)
- [ ] `docs/integrity-charter.md` committed at v1
- [ ] `docs/integrity-charter.draft.md` removed
- [ ] `README.md` has a top-level CHARTER section linking to the charter with a 1–2 sentence summary
- [ ] Amendment process documented in the charter itself (already drafted in v0.1)
- [ ] `Authored:` and `Maintainer:` metadata updated to v1 with current date

**Depends on:** none

---

## Phase 2: Identity schema

### T22.5 — accounts + account_sessions + account_credentials tables | Cx: 25 | P0

**Description:**
Introduce the identity layer. Create `accounts` (durable identity), `account_sessions` (link table from account to one or more `session_id`s), and `account_credentials` (magic-link tokens, future credential types). Add `backend/app/core/queries_accounts.py` with the CRUD surface. `account_id` is nullable on existing tables — anonymous-first invariant enforced.

**AC:**
- [ ] `backend/alembic/versions/0011_accounts.py` creates the three tables
- [ ] `accounts(id PK, email UNIQUE, created_at, last_active_at)`
- [ ] `account_sessions(account_id FK, session_id, claimed_at, PRIMARY KEY(account_id, session_id))` with UNIQUE on `session_id` (one session belongs to at most one account)
- [ ] `account_credentials(id PK, account_id FK, credential_type, credential_value_hash, expires_at, used_at)`
- [ ] `backend/app/core/queries_accounts.py` with: `create_account`, `get_account_by_email`, `claim_session`, `list_sessions_for_account`, `get_account_for_session`
- [ ] `backend/tests/test_accounts.py` covers create + claim + list + get_for_session paths
- [ ] All queries work on both sqlite and postgres
- [ ] `bpsai-pair arch check` passes on touched files

**Depends on:** T22.3

---

### T22.6 — account_roles + reviewer permission scaffold | Cx: 15 | P1

**Description:**
Add the role enum (`case_manager`, `sme_reviewer`, `dao_reviewer`, `admin`) bound to accounts. Ship the `require_role(role)` FastAPI dependency that raises 403 if the requesting account lacks the required role. Admin-only is the working tier this sprint; full per-role test coverage and the reviewer dashboard UI ship in Sprint 23.

**AC:**
- [ ] `backend/alembic/versions/0012_account_roles.py` creates `account_roles(account_id FK, role_name, granted_at, PRIMARY KEY(account_id, role_name))`
- [ ] `role_name` constrained to enum: `case_manager` | `sme_reviewer` | `dao_reviewer` | `admin`
- [ ] `backend/app/core/queries_roles.py` with `grant_role`, `revoke_role`, `list_roles_for_account`, `account_has_role`
- [ ] `backend/app/core/auth_roles.py` exposes `require_role(role: str)` FastAPI dependency that returns 403 if account is anonymous OR lacks the role
- [ ] `backend/tests/test_roles.py` covers admin grant/revoke/check paths
- [ ] One account can hold multiple roles (no exclusivity)
- [ ] `bpsai-pair arch check` passes on touched files

**Depends on:** T22.5

---

## Phase 3: Magic-link auth & anonymous-first invariant

### T22.7 — Magic-link issuance endpoint | Cx: 15 | P0

**Description:**
Ship `POST /auth/magic-link` that accepts an email, mints a single-use opaque token (≥256-bit entropy), persists it in `account_credentials` with a 15-minute expiry, and emails it via the existing SendGrid integration. Always returns `202 Accepted` regardless of whether the email exists (no enumeration). Rate-limited per email and per IP.

**AC:**
- [ ] `backend/app/routes/auth.py` exposes `POST /auth/magic-link`
- [ ] Request body: `{email: str}`; response: `202 Accepted` (always, no body)
- [ ] Token: ≥256-bit entropy via `secrets.token_urlsafe(32)`; stored hashed (SHA-256) in `credential_value_hash`
- [ ] Token expires 15 minutes from issuance
- [ ] If the email maps to no account, create one transparently (account-on-first-use)
- [ ] SendGrid email sent with claim URL: `{FRONTEND_URL}/auth/claim?token={token}`
- [ ] Rate limits: 3/hour per email, 10/hour per IP (return 202 anyway when limited; log)
- [ ] `backend/tests/test_auth_magic_link.py` covers issuance, no-enumeration, expiry, rate-limit
- [ ] `bpsai-pair arch check` passes

**Depends on:** T22.5

---

### T22.8 — Magic-link claim + session-claim flow | Cx: 20 | P0

**Description:**
Ship `GET /auth/claim?token=…` that validates the magic-link token, marks it `used_at`, and claims any anonymous `session_id` present on the request to the underlying account. Subsequent visits with the same browser auto-attach via cookie. Pre-existing anonymous sessions can be claimed retroactively — this is the "save your progress" path.

**AC:**
- [ ] `backend/app/routes/auth.py` extends with `GET /auth/claim`
- [ ] Validates token: returns uniform `401 Unauthorized` for invalid / expired / already-used (no error oracle)
- [ ] On valid claim: marks `account_credentials.used_at`, sets a session cookie binding the browser to the account, calls `claim_session(account_id, session_id)` if a `session_id` is present in the request
- [ ] If `session_id` was previously claimed by a *different* account, returns `409 Conflict` (no silent overwrite)
- [ ] Returns `{account_id, claimed_session_ids: [...]}` JSON for client-side state
- [ ] `backend/tests/test_auth_claim.py` covers success, invalid, expired, replay, cross-account-conflict, pre-existing-anonymous-claim
- [ ] `bpsai-pair arch check` passes

**Depends on:** T22.7

---

### T22.9 — Anonymous-first invariant test | Cx: 15 | P0

**Description:**
Ship a property test that, for every API route currently using `session_id` (35+ endpoints across `backend/app/routes/`), runs the endpoint twice — once with an anonymous session, once with a session claimed by an account — and asserts the responses are equivalent (modulo account-aware response fields like `account_id`). This is the load-bearing guard that prevents future drift toward forced-login.

**AC:**
- [ ] `backend/tests/test_anonymous_first_invariant.py` enumerates all routes consuming `session_id` (auto-discovery via FastAPI route inspection — not hand-maintained list)
- [ ] For each route, runs anonymous-fixture + claimed-fixture and asserts response equivalence (excluding allowlist of account-only fields: `account_id`, `account_email`)
- [ ] Test failure on any new route that requires authentication (unless explicitly added to a documented allowlist with reason)
- [ ] CI fails if invariant breaks
- [ ] Documents the invariant in a top-of-file docstring referencing the integrity charter

**Depends on:** T22.5

---

## Phase 4: Frontend & integration gate

### T22.10 — Frontend login surface (magic-link UX) | Cx: 20 | P0

**Description:**
Ship `/auth/login` and `/auth/claim` pages in the Next.js frontend. Login page accepts an email, POSTs to `/auth/magic-link`, and shows a "check your email" confirmation. Claim page consumes `?token=`, calls `/auth/claim`, and shows success or invalid-token state. vitest coverage for both.

**AC:**
- [ ] `frontend/src/app/auth/login/page.tsx`: email form → POST → confirmation
- [ ] `frontend/src/app/auth/claim/page.tsx`: reads `?token=`, calls API, renders success or invalid-token state
- [ ] `frontend/src/lib/api/auth.ts`: typed client functions `requestMagicLink(email)` and `claimMagicLink(token)`
- [ ] Both pages styled with shadcn/Tailwind matching existing GoWork palette (cyan/amber/rose)
- [ ] vitest coverage for both pages (rendering + form submission + error states) and the API client
- [ ] No build regressions: `npx next build` green; `npx tsc --noEmit` 0 errors

**Depends on:** T22.7, T22.8

---

### T22.11 — Account-aware client + session-claim CTAs | Cx: 15 | P0

**Description:**
Extend the React Query client with a `useAccount()` hook surfacing account state. Add `<SaveProgressCTA />` component rendered at strategic points in the assessment funnel — post-assessment, post-plan-generation, and pre-share. The CTA is opt-in only; it never gates functionality.

**AC:**
- [ ] `frontend/src/lib/api/client.ts` exposes `useAccount()` returning `{accountId, email} | null`
- [ ] `frontend/src/components/auth/SaveProgressCTA.tsx`: dismissible card with "Save your progress" headline and email-form action
- [ ] Inserted at: end of `/assess` (post-assessment), middle of `/plan` (post-plan-generation), and on `/shared/[token]` page header (pre-share)
- [ ] Dismissed CTA does not re-show in the same session (localStorage-backed)
- [ ] Already-claimed sessions never see the CTA
- [ ] vitest coverage for the component + insertion points
- [ ] No build regressions

**Depends on:** T22.10

---

### T22.13 — Sprint 22 integration gate | Cx: 10 | P0

**Description:**
Final gate task. Run the full test matrix against both engines, verify arch + lint clean, reconcile state.md (mark Sprint 22 complete; close T12.0 and T12.1 with supersede note pointing to this sprint), and push the PR. CI must be green on both sqlite and postgres before merge.

**AC:**
- [ ] Full backend test suite green on sqlite locally
- [ ] Full backend test suite green on postgres locally
- [ ] Frontend vitest green
- [ ] `ruff check .` clean
- [ ] `bpsai-pair arch check .` no new violations
- [ ] `.paircoder/context/state.md` reconciled: Sprint 22 marked complete with What-Was-Just-Done entry; T12.0 and T12.1 marked done with supersede note
- [ ] Integrity charter v1 visible from README on the merged commit
- [ ] PR pushed; CI green on both engine matrix axes
- [ ] No `in_progress` task records left for Sprint 22

**Depends on:** T22.4, T22.6, T22.9, T22.11, T22.12

---

## Delivery Summary

| Phase | Tasks | Cx | Output |
|---|---|---|---|
| 1. Foundation — Postgres migration & charter | T22.1, T22.2, T22.3, T22.4, T22.12 | 90 | Alembic running on both engines; m001–m010 ported; Postgres in CI; charter v1 binding |
| 2. Identity schema | T22.5, T22.6 | 40 | Accounts + sessions + credentials tables; reviewer-role scaffold |
| 3. Magic-link auth & anonymous-first invariant | T22.7, T22.8, T22.9 | 50 | Passwordless login working; session-claim flow live; invariant test green across all 35+ session routes |
| 4. Frontend & integration gate | T22.10, T22.11, T22.13 | 45 | Login + claim pages; account-aware client + CTAs; sprint merged |
| **Total** | **13** | **225** | Identity foundation ready for Sprints 23–30 |

## Priority Order

Engage cut-list (in order P2 → P1 → P0; cut from the top if budget overflows):

1. **P0 (cannot cut — foundation):** T22.1, T22.2, T22.3, T22.4, T22.5, T22.7, T22.8, T22.9, T22.10, T22.11, T22.12, T22.13
2. **P1 (cut last; admin-only stub is enough for S23 to start):** T22.6
3. **P2 (none):** This sprint has no cuttable scope. Foundation work is binary — it lands or the sprint fails.

If budget pressure is real, the only realistic descope is T22.6 (reviewer roles) — admin-only enforcement via a hardcoded allowlist suffices to unblock Sprint 23's reviewer dashboard, and the full role tier can land there.
