# Sprint 26 — Admin Dashboard

**Plan type:** feature
**Sprint:** 26
**Total Cx:** 192
**Tasks:** 12 (P0: 9, P1: 3, P2: 0)
**Brief:** `.paircoder/plans/briefs/brief-sprint-26-admin-dashboard.md`
**Builds on:** Sprint S22 (`require_role("admin")` cookie-session gate, `<RoleGate>` component, anonymous-first invariant). Sprint S23 (admin layout pattern, role-aware nav, typed API client convention). Sprint S24 (admin claim-review dashboard, cross-session isolation contract, `_throwOnError` lifted to `_client.ts` post-S25). Sprint S25 (cities-admin diagnostic page, `fetchWithCookie` + `throwOnApiError` lift in `_client.ts`, charter integrity test, `_cross_session_fixtures.PUBLIC_ENDPOINTS` registration discipline).

## Goal

Build the operator-facing admin surface that compounds on three sprints of trust substrate (S22 identity → S23 reviewer roles → S24 listing claim review → S25 cross-metro diagnostic). Four sub-features under `/admin/*`: resource management with seed-respecting CRUD, flagged-resource review queue, visit-feedback inbox, manual BrightData pre-crawl trigger. One small migration unlocks real CRUD persistence without clobber-on-reseed; one small auth-gate migration on `routes/brightdata.py` lets the cookie-session admin UI call the existing trigger endpoint.

## What ships in S26 vs deferred

**S26 (this sprint):** Migration 0015 adds `resources.user_curated_at` + seed-loader respect logic; resource CRUD backend with hide/restore via `health_status='hidden'`; admin feedback backend (flagged-queue + visits-inbox over existing m001 columns); BrightData gate migrated from legacy `require_admin_key` to S22 `require_role("admin")`; 3 typed frontend API clients mirroring S25 `cities_admin.ts` shape; 3 admin pages (`/admin/resources`, `/admin/feedback`, `/admin/brightdata`); `/admin` landing page indexing all admin sections (S23-S26); integration gate carrying forward all charter assertions (anonymous-first invariant, cross-session isolation contract with allowlist registration as a per-route AC, display-only matching engine).

**Deferred to S27+:** Bulk operations (single-row only this sprint). Resource provenance audit trail (who-changed-what-when — useful for SOC2; new table). BrightData status streaming (poll-on-demand only). Mobile-optimized admin (desktop-first; operators use desktop). Migration of the OTHER `require_admin_key` callers (`admin_flags.py`, `demo.py`) — different concerns. Resource categorization rebalancing or barrier-tag editing on resources. Self-service admin signup (admins provisioned via `account_roles` table directly per S22). Cross-city matching (the deliberate S25 boundary remains; T25.9 charter test stays green).

## Architectural principles

- **Additive backend, additive frontend.** No file in `backend/app/modules/matching/` is modified. T25.9's charter integrity test re-runs green at the S26 gate. Money never moves position.
- **Cross-session allowlist registration is a per-route AC.** S25's CI-only failure (T25.7's `/api/admin/cities/summary` not registered in `_cross_session_fixtures.PUBLIC_ENDPOINTS`) was preventable. Every new admin route in S26 carries an explicit AC line: "registered in `_cross_session_fixtures.PUBLIC_ENDPOINTS` with rationale". T26.12 re-asserts at the gate.
- **Anonymous-first invariant (S22) holds.** Admin routes are operator-facing and exempt from the invariant by design (they're outside `REQUIRES_AUTH_ALLOWLIST`'s session-id-route auto-discovery scope). T26.12 re-runs the invariant test.
- **Frontend cookie-session, not API-key.** `routes/brightdata.py` migrates from `require_admin_key` (legacy header) to `require_role("admin")` (S22 cookie) so the admin UI calls every endpoint via the same auth path. The new admin pages are wrapped in `<RoleGate>` (already inherited from `/admin/layout.tsx`).
- **Seed-loader respects user curation.** New `resources.user_curated_at TIMESTAMP NULL` column; the existing `seed_from_file` checks it and skips upserts where set. Without this, admin add/edit gets wiped on the next reseed (deploy or test fixture). One migration unlocks real CRUD.
- **Single owner per shared file.** T26.2 owns the `routes/__init__.py` registration for all 3 new routers (resources, feedback, brightdata) — bundles the soft collision so Wave 0 can stay parallel.

---

## Phase 1: Foundation — schema migration + brightdata gate migration + admin feedback backend

### T26.1 — Migration 0015: resources.user_curated_at + seed-loader respect | Cx: 12 | P0

**Description:**
Alembic revision 0015 with `down_revision='0014'`. Adds `user_curated_at TIMESTAMP NULL` to the existing `resources` table. Updates `backend/app/core/seed_helpers.py:seed_from_file` to honor the flag: for each row in seed JSON, if a row with the same (city, name) exists in the DB AND has `user_curated_at IS NOT NULL`, skip the upsert (preserve admin edit). Default-NULL preserves legacy single-city behavior; existing tests pass unchanged.

The cross-task contract: T26.1 produces the column + loader logic; T26.2's CRUD writes always stamp the timestamp (admin INSERT and UPDATE both set `user_curated_at = now()`).

**AC:**
- [ ] `backend/alembic/versions/0015_resources_user_curated.py` (new) — revision 0015, down_revision 0014
- [ ] Adds `user_curated_at TIMESTAMP NULL` to `resources` (no default; nullable so existing rows stay NULL)
- [ ] `backend/app/core/seed_helpers.py:seed_from_file` modified: when processing a row from JSON for the `resources` table, look up `(city, name)` in the existing rows; if matched and `user_curated_at IS NOT NULL`, skip the upsert
- [ ] Migration runs clean on fresh sqlite + postgres
- [ ] Migration idempotent (re-run safe; alembic native check)
- [ ] `backend/tests/test_resources_user_curated.py` (new) covers:
  - Insert seed row, manually set `user_curated_at = now()`, re-run seed with modified JSON for the same (city, name) → DB row unchanged
  - Insert seed row, leave `user_curated_at = NULL`, re-run seed with modified JSON → DB row updated to JSON's content
  - Default behavior with `user_curated_at IS NULL` matches pre-migration upsert semantics
- [ ] Existing seed tests pass with the new column added (default NULL preserves legacy behavior)
- [ ] `bpsai-pair arch check backend/app/core/seed_helpers.py` passes (no error-level violations introduced)
- [ ] `bpsai-pair arch check backend/alembic/versions/0015_resources_user_curated.py` passes

**Depends on:** none

---

### T26.3 — Admin feedback inbox + flagged-queue backend | Cx: 22 | P0

**Description:**
New backend module + routes for the read-side admin surfaces over the existing S14 feedback substrate. No schema changes — `visit_feedback` already has the `reviewed INTEGER DEFAULT 0` and `action_taken TEXT` columns from m001. Two surfaces: flagged-resource queue (resources with `health_status='flagged'` joined with recent negative `resource_feedback` rows for context) and visit-feedback inbox (paginated browse with reviewed-state filter + mark-reviewed mutation).

All routes admin role-gated. Pure SQLAlchemy `text()` + named binds (driver-agnostic; sqlite + postgres). Lives in NEW route module to avoid extending `routes/feedback.py` (which is candidate-facing). Router registration handled by T26.2 (single owner of `routes/__init__.py` edit this wave).

**AC:**
- [ ] `backend/app/core/queries_admin_feedback.py` (new) — async query helpers
- [ ] `backend/app/routes/admin_feedback.py` (new) exposes:
  - `GET /api/admin/feedback/flagged?city=<slug>` — list flagged resources joined with last-30-days negative `resource_feedback` rows for context
  - `POST /api/admin/feedback/flagged/{resource_id}/approve` — clears flag (sets `health_status='healthy'`)
  - `POST /api/admin/feedback/flagged/{resource_id}/confirm-hide` — confirms removal (sets `health_status='hidden'`)
  - `GET /api/admin/feedback/visits?reviewed=<bool>&limit=<n>&offset=<n>` — paginated `visit_feedback` browse; filters by `reviewed` flag
  - `POST /api/admin/feedback/visits/{id}/mark-reviewed` — sets `visit_feedback.reviewed=1`; optional `action_taken` text body
- [ ] All 5 routes gated by `require_role("admin")` (S22 cookie pattern)
- [ ] Pagination: limit ≤ 100; default 50; offset returned in response shape
- [ ] All 5 routes added to `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` with rationale (T26.12 re-asserts at gate; this is a per-route AC, not a gate-time fixup)
- [ ] `backend/tests/test_admin_feedback.py` (new) covers each endpoint: admin happy path, non-admin 403, anonymous 403, pagination semantics, action mutations update the correct columns
- [ ] Queries portable on sqlite + postgres (text() + named binds + `RETURNING` where needed)
- [ ] `bpsai-pair arch check backend/app/routes/admin_feedback.py` passes
- [ ] `bpsai-pair arch check backend/app/core/queries_admin_feedback.py` passes
- [ ] `ruff check` clean on touched files

**Depends on:** none

---

### T26.4 — Migrate brightdata.py from require_admin_key to require_role("admin") | Cx: 10 | P0

**Description:**
Refactor `backend/app/routes/brightdata.py` to drop the legacy `require_admin_key` (header-based) gate and use S22's `require_role("admin")` (cookie-based) instead. The endpoint surface (`POST /api/brightdata/crawl`, status endpoints, etc.) stays identical; only the auth mechanism changes. After T26.4, the new admin UI (T26.10) can call BrightData via the same cookie session as every other admin surface.

Honest doc note in the commit message: this is a breaking change for any external script that called these endpoints with the legacy api-key. The endpoints are admin-only operator surface; external usage is unlikely but should be communicated.

**AC:**
- [ ] All routes in `backend/app/routes/brightdata.py` gated by `require_role("admin")` (not `require_admin_key`)
- [ ] The `from app.core.auth import require_admin_key` import removed from this file
- [ ] All routes added to `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` with rationale (per-route AC discipline)
- [ ] `backend/tests/test_brightdata.py` (extend or create) covers: admin role with cookie session succeeds; non-admin role returns 403; anonymous returns 403 (matches S25 cities_admin contract — distinguished via `detail` string)
- [ ] No regression: existing brightdata tests still pass (mock the actual brightdata client; only the gate behavior changes)
- [ ] `bpsai-pair arch check backend/app/routes/brightdata.py` passes (no new violations; line count likely shrinks slightly from removing the api-key dependency)
- [ ] `ruff check` clean on touched files

**Depends on:** none

---

## Phase 2: Resource CRUD backend (registers all 3 new routers)

### T26.2 — Resource CRUD backend (queries + routes + router registrations) | Cx: 25 | P0

**Description:**
New CRUD module + routes for resource management (add/edit/hide/restore/list/get). Stamps `resources.user_curated_at = now()` on every INSERT and UPDATE (consumes T26.1's column + loader contract). Soft-delete via `health_status='hidden'`; restore reverses to `'healthy'`. Hard delete deliberately NOT supported in this sprint (admin can hide instead; hard delete defers to S27+ if needed).

**Bundled scope (resolves Wave-0 soft collision):** T26.2 also owns the `backend/app/routes/__init__.py` edit that registers ALL THREE new routers from this sprint: `admin_resources_router` (this task), `admin_feedback_router` (T26.3), `brightdata_router` (T26.4 — re-registration after gate change is a no-op, but the import path stays). Single owner of `routes/__init__.py` keeps Wave 0 parallel-safe.

**AC:**
- [ ] `backend/app/core/queries_admin_resources.py` (new):
  - `list_resources(session, *, city, limit, offset, include_hidden) -> list[dict]` — paginated; default excludes hidden
  - `get_resource(session, resource_id) -> dict | None`
  - `create_resource(session, **fields) -> int` — INSERT + stamps `user_curated_at = now()`; returns new id
  - `update_resource(session, resource_id, **patch) -> None` — UPDATE + stamps `user_curated_at = now()`
  - `set_health_status(session, resource_id, status)` — sole writer to `health_status` for admin actions; allowed values: `'healthy' | 'watch' | 'flagged' | 'hidden'`
- [ ] `backend/app/routes/admin_resources.py` (new) exposes:
  - `GET /api/admin/resources?city=<slug>&limit=<n>&offset=<n>&include_hidden=<bool>`
  - `GET /api/admin/resources/{id}`
  - `POST /api/admin/resources` (body = resource fields; returns `{id, ...}` of created row)
  - `PATCH /api/admin/resources/{id}` (body = patch)
  - `DELETE /api/admin/resources/{id}` (soft-hide via set_health_status)
  - `POST /api/admin/resources/{id}/restore` (sets `health_status='healthy'`)
- [ ] All 6 routes gated by `require_role("admin")`
- [ ] All 6 routes added to `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` with rationale (per-route AC discipline)
- [ ] Pagination: limit ≤ 100; default 50; offset + total returned in response
- [ ] Hidden resources excluded from default list; opt-in via `?include_hidden=true`
- [ ] `backend/app/routes/__init__.py` registers `admin_resources_router`, `admin_feedback_router` (from T26.3), and the migrated `brightdata_router` import path (T26.4) — single owner edit point this wave
- [ ] `backend/tests/test_admin_resources.py` (new) covers: create stamps timestamp, edit stamps timestamp, hide sets `health_status='hidden'`, restore reverses, pagination semantics, `include_hidden=true` returns hidden rows, admin-only gate (403/anon-403), city filter works
- [ ] After T26.1 lands: re-run seed against a row with `user_curated_at` set by `create_resource` — row must NOT be overwritten (integration test in this file)
- [ ] Queries portable on sqlite + postgres
- [ ] `bpsai-pair arch check` passes on touched files
- [ ] `ruff check` clean on touched files

**Depends on:** T26.1, T26.3, T26.4

---

## Phase 3: Frontend API clients (parallel)

### T26.5 — Frontend admin_resources API client | Cx: 12 | P0

**Description:**
Typed API client for the resource CRUD endpoints. Mirrors the S25 `cities_admin.ts` shape post-/reviewing-and-fixing lift: imports `fetchWithCookie` + `throwOnApiError` from `_client.ts` (the shared helpers added in the post-PR-#126 simplify pass); defines a single typed `AdminResourcesApiError`; one function per endpoint. Each per-domain client subclass keeps only its typed error subclass.

**AC:**
- [ ] `frontend/src/lib/api/admin_resources.ts` (new):
  - `import { fetchWithCookie, throwOnApiError } from "./_client"`
  - Typed wire interfaces: `Resource`, `ResourceListResponse` (with pagination), `CreateResourcePayload`, `UpdateResourcePatch`
  - `AdminResourcesApiError extends Error` with `status` + `detail`
  - Functions: `listResources(opts: {city, limit?, offset?, includeHidden?})`, `getResource(id)`, `createResource(payload)`, `updateResource(id, patch)`, `hideResource(id)` (DELETE), `restoreResource(id)` (POST /restore)
- [ ] All functions delegate to `fetchWithCookie` + `throwOnApiError(res, AdminResourcesApiError, "admin-resources")`
- [ ] `frontend/src/lib/api/__tests__/admin_resources.test.ts` (new) — vitest stubs `fetch` and asserts URL + method + body for each function; verifies typed error throws on non-2xx
- [ ] `npx tsc --noEmit` clean
- [ ] vitest suite green (no regressions)
- [ ] No new files under `frontend/src/components/` (per task scope; UI components belong to T26.8)

**Depends on:** T26.2

---

### T26.6 — Frontend admin_feedback API client | Cx: 10 | P0

**Description:**
Typed API client for the admin feedback endpoints (flagged-queue + visits-inbox). Same shape as T26.5 — imports the shared helpers; one typed error class.

**AC:**
- [ ] `frontend/src/lib/api/admin_feedback.ts` (new):
  - Imports `fetchWithCookie` + `throwOnApiError` from `_client.ts`
  - Typed wire interfaces: `FlaggedResource`, `VisitFeedback`, `VisitFeedbackListResponse` (with pagination)
  - `AdminFeedbackApiError extends Error` with `status` + `detail`
  - Functions: `listFlagged(city)`, `approveFlagged(resourceId)`, `confirmHide(resourceId)`, `listVisits(opts: {reviewed?, limit?, offset?})`, `markVisitReviewed(visitId, actionTaken?)`
- [ ] All functions delegate to shared helpers (same pattern as T26.5)
- [ ] `frontend/src/lib/api/__tests__/admin_feedback.test.ts` (new) — vitest URL/method/body assertions per function
- [ ] `npx tsc --noEmit` clean

**Depends on:** T26.3

---

### T26.7 — Frontend admin_brightdata API client | Cx: 8 | P1

**Description:**
Thin typed API client for the BrightData admin trigger endpoints. Same shape; smallest of the three clients (one trigger + one status function).

**AC:**
- [ ] `frontend/src/lib/api/admin_brightdata.ts` (new):
  - Imports `fetchWithCookie` + `throwOnApiError` from `_client.ts`
  - Typed wire interfaces: `TriggerCrawlPayload`, `TriggerCrawlResponse`, `CrawlStatus` — match the existing `routes/brightdata.py` Pydantic types 1:1
  - `AdminBrightDataApiError extends Error`
  - Functions: `triggerCrawl(payload)`, `getCrawlStatus(snapshotId)` — exact endpoint names confirmed against T26.4's migrated routes
- [ ] `frontend/src/lib/api/__tests__/admin_brightdata.test.ts` (new) — vitest URL/method/body
- [ ] `npx tsc --noEmit` clean

**Depends on:** T26.4

---

## Phase 4: Frontend pages (parallel)

### T26.8 — /admin/resources page | Cx: 28 | P0

**Description:**
Next.js page at `/admin/resources` with table view, filters, edit modal, hide/restore actions, and add-resource modal. Reuses the S23 `<RoleGate>` (inherited from `/admin/layout.tsx`). The shared `<ResourceForm>` component lives under `frontend/src/components/admin/` and is consumed by both add and edit modals.

**AC:**
- [ ] `frontend/src/app/admin/resources/page.tsx` (new):
  - Table with columns: name, category, city, health_status, last edited (`user_curated_at` formatted)
  - Filter dropdowns: city (FW, Dallas, Montgomery), category (from a static enum), health_status (healthy/watch/flagged/hidden — opt-in via "Show hidden" toggle)
  - Pagination controls: page-size 50, prev/next + page indicator
  - Row actions: Edit (opens modal with `<ResourceForm>` pre-filled), Hide (with confirmation dialog), Restore (only shown for hidden rows)
  - "Add Resource" button → modal with `<ResourceForm>` (empty state)
- [ ] `frontend/src/components/admin/ResourceForm.tsx` (new):
  - Fields: name, category, subcategory, address, lat (number), lng (number), phone, url, services (multi-select or comma-string), eligibility, city (dropdown)
  - Client-side validation: required = name, category, city; lat/lng must be numeric and within US-continental range
  - Uses shadcn `Input`, `Select`, `Textarea`
  - Submit handler accepts `(payload, mode: "create" | "edit", resourceId?)` — internally calls `createResource` or `updateResource` from T26.5
- [ ] `frontend/src/app/admin/resources/__tests__/page.test.tsx` (new) — vitest covers: table renders with mocked API response, filters trigger refetch with correct params, edit modal opens + populates + submits, hide action confirms + calls `hideResource`, add modal validates required fields + lat/lng numeric
- [ ] Page wrapped in `<RoleGate>` (already inherited from `/admin/layout.tsx`; explicit at page level for clarity is OPTIONAL)
- [ ] `npx tsc --noEmit` clean
- [ ] `npx next build` green
- [ ] No imports from `backend/app/modules/matching/` (charter integrity assertion)

**Depends on:** T26.5

---

### T26.9 — /admin/feedback page (tabbed: Flagged + Visits) | Cx: 25 | P0

**Description:**
Single Next.js page at `/admin/feedback` with two tabs (shadcn `Tabs`): "Flagged Resources" and "Visit Feedback". Each tab paginates independently. Shared layout via the existing admin shell.

**AC:**
- [ ] `frontend/src/app/admin/feedback/page.tsx` (new):
  - shadcn `Tabs` component with two `TabsTrigger`s: "Flagged Resources" and "Visit Feedback"
  - Default tab = "Flagged Resources"; URL hash sync (`#flagged` / `#visits`) so deep links work
- [ ] `frontend/src/components/admin/FeedbackTabs.tsx` (new — splits the two tabs into separate components for testability):
  - `FlaggedResourcesTab`: card-per-resource showing name + recent negative `resource_feedback` excerpts; row actions = Approve (calls `approveFlagged`) + Confirm Hide (calls `confirmHide`); refetches on action
  - `VisitFeedbackTab`: table with columns (submitted_at, made_it_to_center badge, plan_accuracy stars, free_text excerpt, reviewed badge, action_taken summary); filter dropdown (all/reviewed/unreviewed); row action = "Mark Reviewed" with optional `action_taken` textarea; submits via `markVisitReviewed`
  - Both tabs paginate independently; default 50 per page; prev/next controls
- [ ] `frontend/src/app/admin/feedback/__tests__/page.test.tsx` (new) — vitest covers: tabs switch correctly, both lists render with mocked API, hash sync works, approve/confirm-hide actions call correct API client functions, mark-reviewed submits action_taken
- [ ] Page wrapped in `<RoleGate>` (inherited)
- [ ] `npx tsc --noEmit` clean
- [ ] `npx next build` green

**Depends on:** T26.6

---

### T26.10 — /admin/brightdata trigger page | Cx: 18 | P1

**Description:**
Next.js page at `/admin/brightdata` with a trigger panel (city selector + trigger button + confirmation dialog) and a status display (last triggered snapshot id + current status with manual refresh). Confirmation dialog blocks accidental clicks (BrightData calls cost money).

**AC:**
- [ ] `frontend/src/app/admin/brightdata/page.tsx` (new):
  - City selector (FW / Dallas / Montgomery — same set as resource page)
  - "Trigger Pre-Crawl" button → opens confirmation dialog (shadcn `AlertDialog`) → on confirm, calls `triggerCrawl(payload)` from T26.7
  - Button disabled while in-flight (loading spinner)
  - Status panel below: shows last triggered snapshot id + current status (`running` / `done` / `failed`) + last refreshed timestamp
  - "Refresh Status" button → calls `getCrawlStatus(snapshotId)` (manual poll; no auto-refresh this sprint per Out-of-Scope #3)
  - Last triggered snapshot persists in localStorage (so page-reload preserves the id; no backend session)
- [ ] `frontend/src/app/admin/brightdata/__tests__/page.test.tsx` (new) — vitest covers: button disabled while in-flight, confirmation dialog blocks accidental clicks, trigger calls API with correct payload, status display renders all 3 status states, refresh button polls API
- [ ] Page wrapped in `<RoleGate>` (inherited)
- [ ] `npx tsc --noEmit` clean
- [ ] `npx next build` green

**Depends on:** T26.7

---

## Phase 5: /admin landing page

### T26.11 — /admin landing page (index of admin sections + quick stats) | Cx: 12 | P1

**Description:**
Index page at `/admin` listing all admin sections (S23 Assessments, S24 Listings, S25 Cities/DFW, S26 Resources/Feedback/BrightData) with quick-stats badges. Replaces the current URL-only navigation. Reads count badges from the existing endpoints (cities-admin summary, listings-admin pending-claims, assessments-admin pending-reviews, plus this sprint's new flagged-resource + pending-visit-feedback counts).

**AC:**
- [ ] `frontend/src/app/admin/page.tsx` (new):
  - Quick-stats row at top: total flagged resources (T26.3 endpoint), total unreviewed visit-feedback (T26.3 endpoint), total pending claims (S24 endpoint), total pending assessments (S23 endpoint)
  - Section cards (one per admin sub-area):
    - Assessments → `/admin/assessments` (S23)
    - Listings → `/admin/listings` (S24)
    - Cities / DFW → `/admin/cities/dfw` (S25)
    - Resources → `/admin/resources` (T26.8)
    - Feedback → `/admin/feedback` (T26.9)
    - BrightData → `/admin/brightdata` (T26.10)
  - Each card: section name, brief description, count badge (when applicable), `<Link>` to the page
- [ ] `frontend/src/app/admin/__tests__/page.test.tsx` (new) — vitest covers: section cards render, count badges fetch from APIs (mock all 4 endpoints), links navigate to correct paths
- [ ] Page wrapped in `<RoleGate>` (inherited)
- [ ] `npx tsc --noEmit` clean
- [ ] `npx next build` green

**Depends on:** T26.8, T26.9, T26.10

---

## Phase 6: Integration gate

### T26.12 — Sprint 26 integration gate | Cx: 10 | P0

**Description:**
Final gate. Re-runs all suites on both sqlite + postgres axes. Re-asserts every charter invariant carried forward from prior sprints. Reconciles state.md + ROADMAP.md. Pushes PR; CI green on all 5 jobs. The cross-session allowlist registration was supposed to happen at write time per each route's per-route AC (S25 lesson) — this gate verifies it actually happened by running the contract test.

**AC:**
- [ ] Full backend pytest suite green on sqlite + postgres axes (no regressions vs S25 baseline 4824 passed / 4 baseline failed / 2 skipped)
- [ ] Frontend vitest suite green (no regressions vs S25 baseline 3629 passed / 3 skipped)
- [ ] `ruff check .` clean on touched files
- [ ] `bpsai-pair arch check .` no new violations
- [ ] **Cross-session isolation contract holds:** `tests/test_cross_session_isolation.py::test_every_endpoint_is_either_flagged_or_allowlisted` re-runs green. Every new admin endpoint shipped in S26 (T26.2's 6 routes + T26.3's 5 routes + T26.4's brightdata routes) is in `_cross_session_fixtures.PUBLIC_ENDPOINTS` with rationale.
- [ ] **Charter integrity assertion (S25 carryforward):** `backend/tests/test_charter_integrity_dallas.py` re-runs green (admin dashboard adds zero matching-engine references)
- [ ] **Anonymous-first invariant carryforward (S22):** `backend/tests/test_anonymous_first_invariant.py` re-runs green; zero new auth-gated USER routes (admin routes are operator-only and exempt)
- [ ] `tsc --noEmit` 0 errors; `next build` green
- [ ] Postgres axis green (S22 dual-engine + S23 isolation rebuild)
- [ ] `.paircoder/context/state.md` reconciled: Sprint 26 complete entry under "What Was Just Done"; Current Focus updated; S25 demoted to Previous Sprints summary; What's Next reset for S27
- [ ] `ROADMAP.md` reconciled: "Phase: Admin Dashboard" items checked off under Planned Next; new entry added under Completed → "Admin Dashboard (Sprint S26) — merged YYYY-MM-DD (PR #N)"
- [ ] PR pushed; CI green on all 5 jobs (Backend Python, Backend Postgres, Frontend, Security Checks, Lighthouse CI)

**Depends on:** T26.2, T26.8, T26.9, T26.10, T26.11

---

## Delivery Summary

| Phase | Tasks | Cx | Output |
|---|---|---|---|
| 1. Foundation — schema + brightdata gate + admin feedback backend | T26.1, T26.3, T26.4 | 44 | alembic 0015 + seed-loader respect; admin-feedback queue/inbox routes; brightdata gate migrated to require_role |
| 2. Resource CRUD backend (registers all 3 new routers) | T26.2 | 25 | 6 admin/resources routes + queries; bundles `routes/__init__.py` registration for all 3 new routers |
| 3. Frontend API clients — parallel | T26.5, T26.6, T26.7 | 30 | 3 typed clients (admin_resources, admin_feedback, admin_brightdata); all use S25's lifted `fetchWithCookie` + `throwOnApiError` |
| 4. Frontend pages — parallel | T26.8, T26.9, T26.10 | 71 | `/admin/resources` (CRUD), `/admin/feedback` (tabbed flagged + visits), `/admin/brightdata` (trigger panel) |
| 5. /admin landing page | T26.11 | 12 | `/admin` index with quick stats + 6 section cards (S23-S26 surface) |
| 6. Integration gate | T26.12 | 10 | Charter assertions hold; state.md + ROADMAP reconciled; PR green |
| **Total** | **12** | **192** | Operator-facing admin surface for resource curation, feedback triage, and BrightData control |

## Priority Order

Engage cut-list (in order P2 → P1 → P0; cut from the top if budget overflows):

1. **P0 (cannot cut — load-bearing chain):** T26.1, T26.2, T26.3, T26.4, T26.5, T26.6, T26.8, T26.9, T26.12
2. **P1 (cuttable in budget pressure):**
   - T26.11 (/admin landing page) — sprint still ships at 180 Cx with all 4 sub-features functional via direct URLs. Defer to S27.
   - T26.10 + T26.7 (/admin/brightdata page + its API client) — must descope as a pair (T26.10 has no consumer without T26.7). Sprint ships at 162 Cx (10 tasks). Legacy `require_admin_key` curl still works for ops. T26.4 (gate migration) becomes optional in this scenario but recommended to keep (small Cx; future-proof).
3. **P2 (none):** No truly cuttable scope below P1.

If both P1 cuts (T26.11 + T26.10/T26.7 pair): minimum-viable S26 = **9 tasks / 154 Cx** with Resources CRUD + Feedback admin surface + BrightData gate migration shipped. Still a real sprint that compounds on the trust substrate.
