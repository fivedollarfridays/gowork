# Feature Brief: Sprint 26 — Admin Dashboard

## Idea

Build the operator-facing admin surface that compounds on three sprints of trust substrate (S22 identity → S23 reviewer roles → S24 listing claim review → S25 cross-metro diagnostic). Four sub-features, all gated by `require_role("admin")` (or one of the broader S23 reviewer roles where appropriate), accessible under `/admin/*`:

1. **Resource management (CRUD with seed-respecting persistence).** Add new resources, edit existing seed-loaded resources, soft-hide via the existing `health_status='hidden'` value, restore from hidden. Adds `resources.user_curated_at TIMESTAMP NULL` so the seed loader skips admin-edited rows on reseed (otherwise admin writes would clobber on the next deploy).
2. **Flagged-resource review queue.** Read-side over the existing S14 health-decay output: list resources with `health_status='flagged'`, show the underlying feedback rationale (negative `resource_feedback` rows), admin actions to approve-back-to-healthy / confirm-hide / dismiss-feedback.
3. **Visit-feedback inbox.** Paginated browse of `visit_feedback` submissions with the existing `reviewed`/`action_taken` columns (already in m001 — no migration needed). Filter by reviewed state + outcome flags; mark-reviewed inline.
4. **BrightData manual pre-crawl trigger.** The endpoint `POST /api/brightdata/crawl` already exists in `routes/brightdata.py` but is gated by the legacy `require_admin_key` (header-based). Migrate it to `require_role("admin")` so the cookie-session admin UI can call it; add a small frontend trigger panel with last-run status.

**Scope boundary — what this sprint is NOT:**
- Mass / bulk operations (single-row only this sprint; bulk is S27+)
- Resource provenance audit trail (who-changed-what-when — out of scope; could land in S27 with a small `resources_audit_log` table)
- BrightData status streaming (poll-on-demand only; no SSE / websocket)
- Mobile-optimized admin (desktop-first; admin is for operators, not candidates)
- Migration of the OTHER `require_admin_key` callers (`admin_flags.py`, `demo.py`) — those are different concerns; only `brightdata.py` is in scope (because the new admin UI needs to call it)
- Resource categorization rebalancing or barrier-tag editing

## Codebase Context

- **Stack:** FastAPI (backend) + Next.js 14 / React Query / shadcn (frontend), async SQLAlchemy + Alembic (S22+), Pydantic config schemas, vitest + pytest.
- **Size:** ~2.6k Python files, ~3k TS/TSX files. Healthy test infra after S22-S25 substrate.
- **Current sprint:** None active. Last shipped: Sprint 25 — Dallas Expansion (PR #126, merged 2026-05-08, squash-merge ca99f68). Branch = main.
- **Conflicting in-progress tasks:** None. The 5 stale `in_progress` (T1.7, T12.5, T12.16, T12.21, T12.24) — none touch admin/feedback/brightdata/resources paths.
- **Charter context (carried from S25):** matching engine remains city-symmetric; admin dashboard is operator-facing only and does not surface in the matching pipeline. T25.9 charter test should remain green throughout S26.

## Sprint-Level Constraints

### Two coexisting auth-gate patterns

Inventory of the existing admin auth gates:
- **`require_admin_key` (legacy header):** `routes/brightdata.py`, `routes/admin_flags.py`, `routes/demo.py` (3 callers)
- **`require_role("admin")` (S22 cookie):** `routes/employers_admin.py`, `routes/cities_admin.py`, `routes/assessments_review.py` (publish endpoint), `routes/assessments_admin.py` (3+ callers)

The S22+ pattern is canonical going forward (per integrity charter). T26.4 migrates `brightdata.py` only — the others are out-of-scope concerns. After T26.4 the admin dashboard's frontend can call BrightData via the same cookie session as everything else. **Test impact (cross-task):** anonymous-first invariant test (S22) re-runs to confirm no new auth-gated user routes; cross-session isolation contract (S24) needs `_cross_session_fixtures.PUBLIC_ENDPOINTS` updated for every new admin endpoint (regression caught in S25 — same pattern this sprint).

### Resource reseed-clobber problem

`resources` table is seeded on init via `seed_resources_all_cities` (per-city scan of `data/cities/<slug>/resources.json`). Without intervention, admin writes (add/edit) would be wiped on the next reseed (fresh deploy or test fixture). T26.1 adds `resources.user_curated_at TIMESTAMP NULL`; the seed loader checks this column and skips overwriting rows where `user_curated_at IS NOT NULL`. Admin INSERT and UPDATE both stamp this timestamp.

**Cross-task contract:** T26.1 produces the column + loader respect logic; T26.2 (CRUD) consumes it (every write stamps the timestamp). The seed-loader change (in `seed_helpers.py`) is the cross-task edit point — `/pc-plan` for T26.1 must coordinate with the existing loader.

### Per-city positional resource_id translation (S25 carryforward)

S25 added `_build_positional_id_map` in `barrier_graph/seed.py` to translate per-city positional resource_ids to global DB ids. **This sprint must not break that.** When admin adds a NEW resource via T26.2 CRUD, it gets a new global id but is NOT referenced by any city's barrier_graph_seed.json (it's user-curated, not seed-derived). So no impact on the positional translation. But the test_dallas_e2e + test_rag_ingestion suites rerun in T26.12 to confirm.

### Existing admin route file sizes (no oversized-file blockers)

| File | Lines | S26 impact |
|---|---|---|
| `routes/brightdata.py` | ~80 | T26.4 modifies (gate migration) |
| `routes/employers_admin.py` | 111 | unchanged |
| `routes/cities_admin.py` | 203 | unchanged |
| `routes/assessments_admin.py` | 162 | unchanged |
| `routes/__init__.py` | ~impact +3 lines (3 new router registrations) | already 40 imports >15 warning threshold; same as S25; no error ceiling |

No file needs a split task as a prerequisite.

### TODOs / FIXMEs in feature path

Spot check across `routes/`, `modules/feedback/`, `integrations/brightdata/`: nothing surfaced that needs to become its own task.

## Tasks

### T26.1 — Migration 0015: resources.user_curated_at + seed-loader respect
- **Cx:** 12
- **Priority:** P0
- **Depends on:** none
- **Files:** `backend/alembic/versions/0015_resources_user_curated.py`, `backend/app/core/seed_helpers.py` (modify `seed_from_file` to honor the flag), `backend/tests/test_resources_user_curated.py`
- **AC template:** Schema task
- **Custom AC:**
  - alembic 0015 with `down_revision='0014'`; adds `user_curated_at TIMESTAMP NULL` to `resources`
  - `seed_from_file` (in `seed_helpers.py`) checks for the column; for each row in seed JSON, if a row with the same (city, name) exists in the DB AND has `user_curated_at IS NOT NULL`, skip the upsert (preserve admin edit)
  - Test: insert a seed row → set `user_curated_at` → re-run seed → row unchanged
  - Test: insert a seed row → leave `user_curated_at = NULL` → re-run seed with modified JSON → row updated to JSON's content
  - Existing seed tests pass with the column added (default NULL preserves legacy behavior)

### T26.2 — Resource CRUD backend (queries + routes)
- **Cx:** 25
- **Priority:** P0
- **Depends on:** T26.1
- **Files:** `backend/app/core/queries_admin_resources.py` (new), `backend/app/routes/admin_resources.py` (new), `backend/app/routes/__init__.py` (register router), `backend/tests/test_admin_resources.py` (new)
- **AC template:** Schema (CRUD) task
- **Custom AC:**
  - Routes: `GET /api/admin/resources?city=<slug>` (list, paginated), `GET /api/admin/resources/{id}` (detail), `POST /api/admin/resources` (create — stamps `user_curated_at=now()`), `PATCH /api/admin/resources/{id}` (edit — stamps `user_curated_at=now()`), `DELETE /api/admin/resources/{id}` (soft-hide — sets `health_status='hidden'`), `POST /api/admin/resources/{id}/restore` (sets `health_status='healthy'`)
  - All gated by `require_role("admin")`
  - CRUD module pure SQLAlchemy `text()` + named binds (driver-agnostic; sqlite + postgres)
  - Queries: `list_resources(session, city, limit, offset)`, `get_resource(session, id)`, `create_resource(session, **fields) -> int`, `update_resource(session, id, **fields)`, `set_health_status(session, id, status)` — sole writer to `health_status` for admin actions
  - Pagination: limit ≤ 100; default 50; offset returned in response
  - Hidden resources excluded from default list; opt-in via `?include_hidden=true`
  - Unit tests cover: create stamps timestamp, edit stamps timestamp, hide sets status, restore reverses, pagination, admin-only gate (403/401)

### T26.3 — Admin feedback inbox + flagged-queue backend
- **Cx:** 22
- **Priority:** P0
- **Depends on:** none (reads existing feedback tables; no schema changes)
- **Files:** `backend/app/core/queries_admin_feedback.py` (new), `backend/app/routes/admin_feedback.py` (new), `backend/app/routes/__init__.py` (register router), `backend/tests/test_admin_feedback.py` (new)
- **AC template:** Schema (read-side + small mutation)
- **Custom AC:**
  - Routes (all admin role-gated):
    - `GET /api/admin/feedback/flagged?city=<slug>` — list resources where `health_status='flagged'` joined with recent negative `resource_feedback` rows (last 30 days) for context
    - `POST /api/admin/feedback/flagged/{resource_id}/approve` — clears flag (sets `health_status='healthy'`)
    - `POST /api/admin/feedback/flagged/{resource_id}/confirm-hide` — confirms removal (sets `health_status='hidden'`)
    - `GET /api/admin/feedback/visits?reviewed=<bool>&limit=<n>&offset=<n>` — paginated `visit_feedback` browse; filters by `reviewed` flag
    - `POST /api/admin/feedback/visits/{id}/mark-reviewed` — sets `visit_feedback.reviewed=1` and optional `action_taken` text
  - Pagination: limit ≤ 100; default 50
  - Test: flagged-queue returns expected resources; approve/confirm-hide actions update health_status; visits inbox paginates correctly; mark-reviewed updates the row; admin-only gate

### T26.4 — Migrate `brightdata.py` from `require_admin_key` to `require_role("admin")`
- **Cx:** 10
- **Priority:** P0
- **Depends on:** none
- **Files:** `backend/app/routes/brightdata.py` (modify), `backend/tests/test_brightdata.py` (extend or create — confirm cookie-session admin succeeds; api-key callers no longer pass)
- **AC template:** Refactor task
- **Custom AC:**
  - All BrightData routes gated by `require_role("admin")` (not `require_admin_key`)
  - The `require_admin_key` import removed from this file
  - Test confirms admin role with cookie session can call the endpoints; non-admin role returns 403; anonymous returns 403 (or whatever the canonical require_role contract returns — same as S25 cities_admin)
  - Cross-session allowlist: `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` updated for the BrightData endpoints (T26.12 also touches this; coordinate)
  - Honest doc note: this is a breaking change for any external scripts that were calling these endpoints with the legacy api-key. Document in the commit message; the endpoints are admin-only operator surface, so external usage is unlikely.

### T26.5 — Frontend admin_resources API client
- **Cx:** 12
- **Priority:** P0
- **Depends on:** T26.2
- **Files:** `frontend/src/lib/api/admin_resources.ts` (new), `frontend/src/lib/api/__tests__/admin_resources.test.ts` (new)
- **AC template:** Refactor (additive)
- **Custom AC:**
  - Typed client mirrors S25 `cities_admin.ts` shape post-/reviewing-and-fixing lift: imports `fetchWithCookie` + `throwOnApiError` from `_client.ts`; defines `AdminResourcesApiError`; one function per endpoint
  - Functions: `listResources(city, opts)`, `getResource(id)`, `createResource(payload)`, `updateResource(id, patch)`, `hideResource(id)`, `restoreResource(id)`
  - vitest unit tests stub fetch + assert URL/method/body for each function

### T26.6 — Frontend admin_feedback API client
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T26.3
- **Files:** `frontend/src/lib/api/admin_feedback.ts` (new), `frontend/src/lib/api/__tests__/admin_feedback.test.ts` (new)
- **AC template:** Refactor (additive)
- **Custom AC:**
  - Same shape as T26.5 (uses `fetchWithCookie` + `throwOnApiError`); typed `AdminFeedbackApiError`
  - Functions: `listFlagged(city)`, `approveFlagged(id)`, `confirmHide(id)`, `listVisits(opts)`, `markVisitReviewed(id, action)`
  - vitest unit tests for URL/method/body

### T26.7 — Frontend admin_brightdata API client
- **Cx:** 8
- **Priority:** P1
- **Depends on:** T26.4
- **Files:** `frontend/src/lib/api/admin_brightdata.ts` (new), `frontend/src/lib/api/__tests__/admin_brightdata.test.ts` (new)
- **AC template:** Refactor (additive)
- **Custom AC:**
  - Same shape; typed `AdminBrightDataApiError`
  - Functions: `triggerCrawl(payload)`, `getCrawlStatus(snapshot_id)` (or whatever the existing endpoints expose — confirm in T26.4)
  - vitest unit tests for URL/method/body

### T26.8 — `/admin/resources` page
- **Cx:** 28
- **Priority:** P0
- **Depends on:** T26.5
- **Files:** `frontend/src/app/admin/resources/page.tsx` (new), `frontend/src/app/admin/resources/__tests__/page.test.tsx` (new), `frontend/src/components/admin/ResourceForm.tsx` (new — shared add/edit form)
- **AC template:** Schema (UI) + frontend
- **Custom AC:**
  - Table view of resources with columns: name, category, city, health_status, last edited (`user_curated_at`)
  - Filter dropdowns: city (FW, Dallas, Montgomery), category, health_status
  - Pagination controls (page size 50)
  - Row actions: edit (opens modal with ResourceForm), hide / restore (single-row, with confirmation)
  - "Add Resource" button → modal with ResourceForm
  - ResourceForm: fields name, category, subcategory, address, lat, lng, phone, url, services, eligibility, city — uses shadcn Input + Select; client-side validation on required + lat/lng numeric
  - Wrapped in `<RoleGate roles={["admin"]}>` (already inherited from `/admin/layout.tsx`, but explicit at page level for clarity)
  - vitest: renders table, filters work, edit modal opens + submits, hide action confirms + calls API, add modal validates required fields

### T26.9 — `/admin/feedback` page (tabbed: Flagged + Visits)
- **Cx:** 25
- **Priority:** P0
- **Depends on:** T26.6
- **Files:** `frontend/src/app/admin/feedback/page.tsx` (new), `frontend/src/app/admin/feedback/__tests__/page.test.tsx` (new), `frontend/src/components/admin/FeedbackTabs.tsx` (new — Tabs primitive wrapping flagged + visits views)
- **AC template:** Schema (UI) + frontend
- **Custom AC:**
  - Single page with shadcn `Tabs` component: "Flagged Resources" + "Visit Feedback"
  - Flagged tab: card-per-resource showing name + recent negative feedback context; actions = approve / confirm-hide
  - Visits tab: table of submissions with columns (submitted_at, made_it_to_center, plan_accuracy, free_text excerpt, reviewed badge); filter by reviewed state; row action = "Mark Reviewed" with optional action_taken textarea
  - Both tabs paginate independently; default 50 per page
  - Wrapped in `<RoleGate>` (inherited)
  - vitest: tabs switch correctly, both lists render, actions call correct API client functions

### T26.10 — `/admin/brightdata` trigger page
- **Cx:** 18
- **Priority:** P1
- **Depends on:** T26.7
- **Files:** `frontend/src/app/admin/brightdata/page.tsx` (new), `frontend/src/app/admin/brightdata/__tests__/page.test.tsx` (new)
- **AC template:** Schema (UI) + frontend
- **Custom AC:**
  - Trigger panel: city selector, "Trigger Pre-Crawl" button (kicks off `precrawl_jobs` for selected city)
  - Status display: shows last triggered snapshot id + current status (running/done/failed); refresh button to poll status
  - Confirmation dialog before triggering (BrightData calls cost money; misclick prevention)
  - Wrapped in `<RoleGate>` (inherited)
  - vitest: button disabled while in-flight, status renders correctly, confirmation dialog blocks accidental clicks

### T26.11 — `/admin` landing page
- **Cx:** 12
- **Priority:** P1
- **Depends on:** T26.8, T26.9, T26.10
- **Files:** `frontend/src/app/admin/page.tsx` (new), `frontend/src/app/admin/__tests__/page.test.tsx` (new)
- **AC template:** Refactor (additive)
- **Custom AC:**
  - Index of admin sections: Resources, Feedback, BrightData, Listings (existing S24), Assessments (existing S23), Cities/DFW (existing S25)
  - Each entry shows: section name, brief description, current count badge if applicable (e.g., flagged-resource count from T26.3 endpoint, pending-claim count from S24 endpoint, pending-assessment count from S23 endpoint)
  - Quick stats row at top: total flagged resources, total pending visit-feedback, total pending claims, total pending assessments
  - Wrapped in `<RoleGate>` (inherited)
  - vitest: section cards render, count badges fetch from APIs, links navigate

### T26.12 — Sprint integration gate
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T26.8, T26.9, T26.10, T26.11
- **Files:** `backend/tests/_cross_session_fixtures.py` (extend `PUBLIC_ENDPOINTS` for new admin routes), `.paircoder/context/state.md`, `ROADMAP.md`, PR description
- **AC template:** Integration gate
- **Custom AC:**
  - Full backend pytest suite green on sqlite + postgres axes (no regressions vs S25 baseline 4824 passed / 4 baseline failed / 2 skipped)
  - Frontend vitest suite green (no regressions vs S25 baseline 3629 passed / 3 skipped)
  - `ruff check .` clean
  - `bpsai-pair arch check .` no new violations
  - **Cross-session allowlist registration:** every new admin endpoint added to `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` with rationale (carrying forward the S25 lesson — surfacing this in the gate prevents another CI-only failure)
  - **Charter integrity carryforward:** S25's `test_charter_integrity_dallas.py` re-runs green (admin dashboard adds zero matching-engine references)
  - **Anonymous-first invariant carryforward:** S22's invariant test re-runs green (zero new auth-gated USER routes; admin routes are operator-only and exempt by design)
  - state.md reconciled (S26 complete entry; S25 demoted to Previous Sprints; What's Next reset)
  - ROADMAP.md reconciled (Admin Dashboard phase items checked off; new entry added under Completed)
  - PR pushed; CI green on all 5 jobs

## Dependency Graph

```
Wave 0 (P0 entry — no deps):
  T26.1   migration: resources.user_curated_at + loader respect
  T26.3   admin feedback inbox + flagged-queue backend (no schema deps)
  T26.4   brightdata gate migration (no schema deps)

Wave 1 (P0 — depends on Wave 0):
  T26.2   resource CRUD backend (deps: T26.1)

Wave 2 (P0 — frontend API clients, parallel, deps backend modules):
  T26.5   admin_resources.ts                        (deps: T26.2)
  T26.6   admin_feedback.ts                         (deps: T26.3)
  T26.7   admin_brightdata.ts        [P1]           (deps: T26.4)

Wave 3 (P0 — pages, parallel, deps API clients):
  T26.8   /admin/resources page                     (deps: T26.5)
  T26.9   /admin/feedback page                      (deps: T26.6)
  T26.10  /admin/brightdata page      [P1]          (deps: T26.7)

Wave 4 (P1 — landing page, deps all pages):
  T26.11  /admin landing page                       (deps: T26.8, T26.9, T26.10)

Wave 5 (P0 — final gate):
  T26.12  Integration gate                          (deps: T26.8, T26.9, T26.10, T26.11)
```

## File Collision Matrix

| Wave | Pair | Shared files | Status |
|---|---|---|---|
| Wave 0 | T26.1 ⊥ T26.3 | none (T26.1 modifies seed_helpers.py + adds migration; T26.3 adds new files) | clean |
| Wave 0 | T26.1 ⊥ T26.4 | none (T26.1 in core/; T26.4 in routes/brightdata.py) | clean |
| Wave 0 | T26.3 ⊥ T26.4 | `routes/__init__.py` — both add a router import | **soft collision: serialize the __init__.py edit OR have T26.12 do the registrations as the gate task** |
| Wave 2 | T26.5 ⊥ T26.6 ⊥ T26.7 | `lib/api/_client.ts` — read-only (already shipped); none touch it | clean |
| Wave 3 | T26.8 ⊥ T26.9 ⊥ T26.10 | none (different page directories) | clean |

**Resolution for the Wave-0 `routes/__init__.py` soft collision:** the cleanest path is to have each backend route task register its own router in `routes/__init__.py` BUT serialize the edits via dependency. Add `T26.3 Depends on: T26.4` (or vice versa) so engage runs them sequentially. Cost: small loss of parallelism in Wave 0 (one extra wave depth). Alternative: have T26.2 (Wave 1) bundle all three router registrations since it depends on T26.1 anyway. **Recommend: bundle into T26.2** — it already touches `routes/__init__.py` and runs after Wave 0; one task owns the file edit and Wave 0 stays parallel. (Update T26.2 AC to register all 3 new routers.)

## Sprint Budget

- **Total Cx:** 192
- **Task count:** 12
- **P0 count / P1 count / P2 count:** 9 P0 / 3 P1 / 0 P2
- **Calibration vs prior sprints:** S22 = 13 tasks / 225 Cx; S23 = 10 tasks; S24 = 11 tasks / ~340 Cx; S25 = 9 tasks / 201 Cx. S26 sits comfortably in the typical envelope — substrate-extending sprint shape, one schema migration, no engine changes.
- **Cut-list (if budget overflows):**
  - T26.11 (P1, /admin landing) → defer to S27. Sprint still ships at 180 Cx with all 4 sub-features functional via direct URLs.
  - T26.10 + T26.7 (P1, /admin/brightdata + its API client) → defer; legacy `require_admin_key` curl still works for ops. Sprint ships at 162 Cx (10 tasks).
  - T26.4 (brightdata gate migration) becomes P2-cuttable IF T26.10 is also cut (no consumer for the new gate). If T26.10 ships, T26.4 must ship.
  - Minimum viable S26 with all P1 cuts: 154 Cx, 9 tasks (T26.1, T26.2, T26.3, T26.5, T26.6, T26.8, T26.9, T26.12 + T26.4 if T26.10 keeps). Still a real sprint.

## Integration Points (cross-task only)

- **T26.1 → T26.2** — schema column + loader respect logic; CRUD writes consume.
- **T26.2 → T26.5 → T26.8** — backend route shape → typed API client → page consumer.
- **T26.3 → T26.6 → T26.9** — same chain for feedback.
- **T26.4 → T26.7 → T26.10** — same chain for BrightData.
- **All admin endpoints → T26.12** — every new route registered in `_cross_session_fixtures.PUBLIC_ENDPOINTS` with rationale (S25 lesson learned).
- **T26.11 → existing S22-S25 admin endpoints** — landing page reads count badges from cities-admin, listings-admin, assessments-admin endpoints. Read-only consumer; no contract changes upstream.

## Out of Scope (explicit boundaries)

These are deliberately deferred. Engage should reject any task that drifts here:

1. **Bulk operations** — single-row only this sprint. Bulk hide/restore, bulk mark-reviewed, etc. defer to S27.
2. **Resource provenance audit log** — who-changed-what-when. Useful for SOC2 but adds a new table + audit trail; out of scope.
3. **BrightData status streaming** — poll-on-demand only. SSE / websocket status defer.
4. **Mobile-optimized admin** — desktop-first. Operators use desktop.
5. **`admin_flags.py` + `demo.py` gate migration** — different concerns; only `brightdata.py` migrated this sprint (because the new admin UI needs it).
6. **Resource categorization rebalancing** — admin can edit a resource's category, but the category vocabulary itself is not editable.
7. **Barrier-tag editing on resources** — resource-to-barrier mapping is seeded via barrier_graph_seed.json + S25's per-city positional translation. Admin UI does not edit these mappings; that's a richer scope (multi-city edit semantics) for S27+.
8. **Cross-city matching surface** — the deliberate S25 boundary remains; admin dashboard adds zero matching-engine references. T25.9 charter test stays green.
9. **Self-service admin signup** — admins are provisioned via `account_roles` table directly (S22 substrate); no UI for "promote to admin" this sprint.

## Charter Integrity Assertions (S22 + S24 + S25 carryforward)

- **Anonymous-first invariant** (S22) — every new admin route is operator-facing, gated by `require_role("admin")`. Zero new routes added to `REQUIRES_AUTH_ALLOWLIST`. T26.12 re-runs the test.
- **Cross-session isolation contract** (S24) — every new admin route added to `_cross_session_fixtures.PUBLIC_ENDPOINTS` with rationale at write time, not at gate time (S25 lesson).
- **Display-only matching engine** (S25) — admin dashboard adds zero references to `backend/app/modules/matching/`. T25.9 charter test (`test_charter_integrity_dallas.py`) re-runs green.
- **Money never moves position** (charter principle 1) — admin add/edit/hide does not change scoring weights. The `health_status='hidden'` filter already excludes hidden resources from the matching pipeline (per S14 wiring); admin UI just becomes the operator-facing surface for that existing behavior.

---

Brief ready. To generate the backlog:

  /draft-backlog .paircoder/plans/briefs/brief-sprint-26-admin-dashboard.md
