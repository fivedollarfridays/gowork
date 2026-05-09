# Feature Brief: Sprint 25 — Dallas Expansion (DFW Unification)

## Idea

Bring up Dallas, TX as the second city in the Fort Worth state-share, by adding `cities/dallas.yaml` config, `data/cities/dallas/` seed (community resources, employers, fair-chance index, training programs, childcare), `backend/app/cities/dallas/` module (eligibility rules), and a DART GTFS importer that emits the existing `transit_routes.json` + `transit_stops.json` shape. Cap with a read-only DFW cross-metro summary page (admin-gated) that surfaces resource counts, transit coverage, and employer counts side-by-side.

**Scope boundary — what this sprint is NOT:**
- Cross-city *matching* (a Dallas resident seeing FW jobs in `/api/jobs`) — deserves its own sprint, requires matching-engine + employer-index changes.
- DFW employer-index unification (employers tagged with metros instead of cities) — out of scope.
- Manual city selector UI on `/assess` — ZIP-derived city resolution stays canonical (anonymous-first invariant).
- Houston / 3rd-state expansion — sprint = DFW only.
- BrightData crawl tuning for Dallas — config inclusion only; tuning is a follow-up.

## Codebase Context

- **Stack:** FastAPI (backend) + Next.js 14 / React Query / shadcn (frontend), async SQLAlchemy + Alembic (S22-onward), Pydantic config schemas, vitest + pytest.
- **Size:** ~2.6k Python files, ~3k TS/TSX files. Test-to-source ratio healthy after S13's QC sprint and S22-S24 backend e2e additions.
- **Current sprint:** None active. Last shipped: Sprint 24 — Two-Sided Listing Verification (PR #125, merged 2026-05-08). Branch = main.
- **Conflicting in-progress tasks:** None. Five stale `in_progress` (T1.7, T12.5, T12.16, T12.21, T12.24) — all Worker Companion / S1 era; none touch `cities/`, `data/cities/`, `backend/app/cities/`, transit, or matching paths.

## Sprint-Level Constraints

### City architecture is already plug-and-play

**Critical finding:** the existing city dispatch is exemplary. `app/cities/config.py` loads any `cities/<slug>.yaml` via `_CITY_SLUG_RE`-gated `load_city_config()` with `lru_cache` + `ContextVar` for per-request override. Consumers (`main.py`, `core/database.py`, `barrier_intel/prompts.py`, `barrier_intel/guardrails.py`, `core/day_boundary.py`, `integrations/brightdata/precrawl.py`, `integrations/job_aggregator.py`, `ai/client.py`, `ai/providers.py`, `ai/prompt_router.py`) all dispatch via `city.state == "TX"` guards — **zero per-city branching to add**. Dallas inherits all TX state-level work (HHSC benefits, Art. 55 expunction, Gov Code Ch. 411 E-1 nondisclosure) for free.

→ This sprint is *additive*, not invasive. No refactor prerequisites. No oversized-file splits required. Per-task `arch check` is `/pc-plan`'s job; nothing here forces a cross-task structural change.

### Data shape contracts (cross-task)

- `cities/dallas.yaml` produces a `CityConfig` (Pydantic) consumed by ALL Dallas-aware code paths. Schema is fixed by `app/cities/config.py:CityConfig` — fields: `name`, `state`, `location`, `zip_ranges` (list[str]), `job_adapters` (list[str]), `data_dir`. Plus `appointment_services` (per-service booking windows; the FW yaml is the canonical reference at 39 lines).
- `data/cities/dallas/*.json` files must mirror the FW shape exactly (10 files): `barrier_graph_seed.json`, `career_centers.json`, `childcare_providers.json`, `community_resources.json`, `employer_policies_seed.json`, `employers.json`, `resources.json`, `training_programs.json`, `transit_routes.json`, `transit_stops.json`. Loaders are city-agnostic — schema drift breaks Dallas + FW symmetrically.
- DART GTFS → `transit_routes.json` + `transit_stops.json` must emit the FW JSON shape: `{route_number, route_name, weekday_start, weekday_end, saturday, sunday}` for routes; `{route_id, stop_name, lat, lng, sequence}` for stops. The importer is the contract boundary between GTFS feeds and the seed format.

### Geocoder DFW proximity already covers Dallas

`backend/app/integrations/mapbox/geocoder.py:39` hard-codes `_DFW_PROXIMITY = "-97.32,32.75"` (downtown FW). This is a *ranking hint*, not a filter — Dallas ZIPs (75201-75398) sit ~30 mi east, well within the bias radius. **No geocoder change required.** Per-city proximity refinement is a future optimization, not an S25 blocker.

### Bounding-box test must extend

`backend/tests/test_distance.py:59` asserts "All embedded FW ZIPs must land in the DFW bounding box." The test is geographic, not city-specific — Dallas ZIPs land in the same DFW box. **Mild extension only:** add a parallel assertion for embedded Dallas ZIPs. Single test file edit, low risk.

### TODOs / FIXMEs in feature path

Spot check across `cities/`, `data/cities/`, `backend/app/cities/`, transit data: none surfaced that need to become tasks. Per-task TODOs are `/pc-plan`'s problem during engage.

## Tasks

### T25.1 — Dallas city config + module skeleton
- **Cx:** 12
- **Priority:** P0
- **Depends on:** none
- **Files:** `cities/dallas.yaml`, `backend/app/cities/dallas/__init__.py`, `backend/app/cities/dallas/eligibility.py`, `backend/tests/test_dallas_city_config.py`
- **AC template:** Schema task
- **Custom AC:**
  - `load_city_config('dallas')` returns a valid `CityConfig` with `state="TX"`, `zip_ranges` covering Dallas (75201-75398), `job_adapters` ⊇ {twc, usajobs} (honestjobs added once Dallas employer index lands in T25.3), `data_dir="data/cities/dallas"`, `appointment_services` matching FW schema
  - `app.cities.dallas.eligibility.DALLAS_ELIGIBILITY_RULES` follows the same `{"type": "open" | "income" | "enrollment" | "compound"}` shape as FW
  - `__init__.py` carries the gate-on-`city.state=="TX"` warning verbatim from FW's

### T25.2 — Dallas community resources + career centers seed
- **Cx:** 28
- **Priority:** P0
- **Depends on:** T25.1
- **Files:** `data/cities/dallas/community_resources.json`, `data/cities/dallas/resources.json`, `data/cities/dallas/career_centers.json`
- **AC template:** Migration (data) task
- **Custom AC:**
  - `community_resources.json` includes Workforce Solutions Greater Dallas (comprehensive + at least 2 satellites), Dallas Public Library job centers, Catholic Charities Dallas, North Texas Food Bank
  - Legal aid: Legal Aid of NorthWest Texas (Dallas branch), Dallas Volunteer Attorney Program
  - Housing: Dallas Housing Authority, Family Gateway, Dallas LIFE
  - 211: North Texas 211
  - All entries include `lat`/`lng` (geocoded), `phone`, `url`, `category`, `subcategory` matching FW JSON shape
  - Eligibility entries for any new resource names added to `DALLAS_ELIGIBILITY_RULES` (T25.1)

### T25.3 — Dallas employer index (fair-chance + general)
- **Cx:** 30
- **Priority:** P0
- **Depends on:** T25.1
- **Files:** `data/cities/dallas/employers.json`, `data/cities/dallas/employer_policies_seed.json`, `backend/data/cities/dallas/honestjobs_listings.json`
- **AC template:** Migration (data) task
- **Custom AC:**
  - ≥ 30 Dallas-area employers from open sources (DFW Hire Reentry, Workforce Solutions Greater Dallas employer directory, public fair-chance pledge lists)
  - `employer_policies_seed.json` schema mirrors FW exactly
  - At least 15 honestjobs listings for Dallas (Amazon DFW Air Hub, Whataburger DFW already present in FW seed are tagged DFW-shared — Dallas-specific listings can be added without dedupe)
  - Updates `cities/dallas.yaml` `job_adapters` to add `honestjobs` once seed lands

### T25.4 — Dallas barrier graph + training + childcare seed
- **Cx:** 18
- **Priority:** P0
- **Depends on:** T25.2
- **Files:** `data/cities/dallas/barrier_graph_seed.json`, `data/cities/dallas/training_programs.json`, `data/cities/dallas/childcare_providers.json`
- **AC template:** Migration (data) task
- **Custom AC:**
  - Barrier graph: structurally identical to FW (same nodes/edges); only resource references swapped to Dallas equivalents from T25.2
  - Training: Dallas College (formerly DCCCD) campuses, Texans Can Academies, Dallas Workforce Development apprenticeships
  - Childcare: ChildCareGroup centers, Dallas-area Texas Rising Star providers
  - Schema parity with FW seed (loaders are city-agnostic)

### T25.5 — DART GTFS importer + Dallas transit seed
- **Cx:** 35
- **Priority:** P0
- **Depends on:** T25.1
- **Files:** `scripts/import_gtfs.py`, `scripts/__tests__/test_import_gtfs.py`, `data/cities/dallas/transit_routes.json`, `data/cities/dallas/transit_stops.json`, `docs/import-gtfs-runbook.md`
- **AC template:** Custom (importer + data)
- **Custom AC:**
  - Importer accepts a GTFS zip path + city slug, emits the FW JSON shape: routes = `{route_number, route_name, weekday_start, weekday_end, saturday, sunday}`; stops = `{route_id, stop_name, lat, lng, sequence}`
  - Importer derives `weekday_start`/`weekday_end` from `stop_times.txt` MIN/MAX over `service_id` weekday calendar entries
  - `saturday`/`sunday` derived from `calendar.txt` boolean flags
  - Sequencing preserves GTFS `stop_sequence` per route
  - Idempotent: re-running on the same GTFS produces byte-identical JSON output (sorted keys, stable iteration)
  - Dallas import uses the public DART GTFS feed; output committed under `data/cities/dallas/`
  - Reusable: runbook documents how to use it for future cities (Houston, etc.)
  - Importer test feeds a fixture mini-GTFS and asserts schema match

### T25.6 — City-aware router validation + DFW bounding-box extension
- **Cx:** 25
- **Priority:** P0
- **Depends on:** T25.1, T25.2, T25.3, T25.4, T25.5
- **Files:** `backend/tests/test_dallas_city_routers.py`, `backend/tests/test_distance.py` (extend), `backend/tests/test_dallas_e2e.py`
- **AC template:** Integration gate (per-feature)
- **Custom AC:**
  - Parametrized tests over `(city_slug, expected_state)`: assert `geo_router`, `resource_router`, `eligibility`, `barrier_intel/prompts`, `brightdata/precrawl`, `job_aggregator`, `ai/prompt_router` all return Dallas-correct values when `set_city_context('dallas')` is active
  - `test_distance.py` DFW bounding-box assertion extends to include embedded Dallas ZIPs (75201, 75204, 75215, 75216, 75217, 75224, 75227, 75228, 75232, 75241)
  - `test_dallas_e2e.py`: full assessment flow — POST `/api/assessment` with ZIP 75201, GET `/api/plan/{session_id}`, assert plan returns Dallas resources + DART transit + Dallas employers
  - Anonymous-first invariant test (S22) re-runs green for `CITY=dallas`

### T25.7 — DFW cross-metro summary admin page
- **Cx:** 28
- **Priority:** P1
- **Depends on:** T25.6
- **Files:** `backend/app/routes/cities_admin.py`, `backend/tests/test_cities_admin.py`, `frontend/src/app/admin/cities/dfw/page.tsx`, `frontend/src/app/admin/cities/dfw/__tests__/page.test.tsx`, `frontend/src/lib/api/cities_admin.ts`
- **AC template:** Schema (read-only) + frontend
- **Custom AC:**
  - `GET /api/admin/cities/summary` — admin-gated via S23 `<RoleGate>`/`require_role("admin")`. Returns per-metro: resource count by category, employer count + fair-chance %, transit route count + total stops, career center count
  - Read-only: derives counts from JSON seed files via `load_city_config(slug).data_dir`. No DB writes.
  - Frontend `/admin/cities/dfw` renders side-by-side cards (Fort Worth | Dallas) with a "DFW total" footer row
  - Wrapped in `<RoleGate roles={["admin"]}>` (S23 pattern)
  - No claim that this is "matching across cities" — the page header explicitly states "Read-only diagnostic. Cross-city matching is not enabled."
  - Display-only: NO writes to matching tables, NO additions to verification tables. Charter integrity assertion (grep across `backend/app/modules/matching/` confirms ZERO Dallas-specific references)

### T25.8 — Frontend Dallas plumbing + i18n
- **Cx:** 15
- **Priority:** P1
- **Depends on:** T25.1
- **Files:** `frontend/src/hooks/useDemoMode.ts` (extend), `frontend/src/hooks/__tests__/useDemoMode-cityaware.test.ts` (extend), `frontend/src/lib/translations/en.json` (extend), `frontend/src/lib/translations/es.json` (extend)
- **AC template:** Refactor (additive)
- **Custom AC:**
  - `DEMO_ZIPS["dallas"] = "75201"` (or canonical Dallas demo ZIP)
  - `useDemoMode` test parametrized over `(city, zip, expectedAdapters)` for both fort-worth + dallas
  - Translation strings for any Dallas-specific copy (city display name, region label) — keep symmetric with FW; ES catalog parity
  - No new selector UI (anonymous-first invariant); ZIP→city resolution stays canonical

### T25.9 — Sprint integration gate
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T25.6, T25.7, T25.8
- **Files:** `.paircoder/context/state.md`, PR description
- **AC template:** Integration gate
- **Custom AC:**
  - Backend pytest suite green (no regressions vs S24 baseline 4700 passed / 4 baseline failed)
  - Frontend vitest suite green (no regressions vs S24 baseline 3620 passed)
  - `ruff check .` clean
  - `bpsai-pair arch check .` no new violations
  - Charter integrity assertion — grep across `backend/app/modules/matching/` for Dallas-specific references returns ZERO matches (matching engine remains city-symmetric, no metro-special-case)
  - Postgres CI service container exercise — Dallas migrations (none in S25; alembic 0014 from S24 stays at head)
  - state.md reconciled (Current Focus updated; S22-S24 demoted to Previous Sprints; What's Next reset)
  - PR pushed; CI green on all jobs

## Dependency Graph

```
Wave 0 (P0 entry — no deps):
  T25.1   Dallas city config + module skeleton

Wave 1 (P0 — parallel, all depend on T25.1):
  T25.2   community_resources + career_centers seed
  T25.3   employer index + honestjobs
  T25.5   DART GTFS importer + transit seed
  T25.8   Frontend plumbing + i18n      [P1, can slip]

Wave 2 (P0 — depends on Wave 1):
  T25.4   barrier graph + training + childcare seed   (deps: T25.2)

Wave 3 (P0 — depends on all data):
  T25.6   City-aware router validation + DFW box     (deps: T25.1-T25.5)

Wave 4 (P1 — DFW view, can defer if budget tight):
  T25.7   DFW cross-metro summary admin page         (deps: T25.6)

Wave 5 (P0 — final gate):
  T25.9   Integration gate                           (deps: T25.6, T25.7, T25.8)
```

## File Collision Matrix

For each parallel-wave pair:

| Wave | Pair | Shared files | Status |
|---|---|---|---|
| Wave 1 | T25.2 ⊥ T25.3 | none (different JSON files in `data/cities/dallas/`) | clean |
| Wave 1 | T25.2 ⊥ T25.5 | none (resources vs transit) | clean |
| Wave 1 | T25.2 ⊥ T25.8 | none (backend seed vs frontend hooks) | clean |
| Wave 1 | T25.3 ⊥ T25.5 | none (employers vs transit) | clean |
| Wave 1 | T25.3 ⊥ T25.8 | none | clean |
| Wave 1 | T25.5 ⊥ T25.8 | none | clean |
| Wave 1 | All ⊥ T25.1 | `cities/dallas.yaml` — but T25.1 produces it; T25.3 *appends* `honestjobs` to `job_adapters` | **soft collision: serialize T25.3's yaml-edit step or use a `Depends on: T25.1` edge plus an explicit `job_adapters` patch step** |

**Resolution for the soft collision:** T25.3's AC updates `cities/dallas.yaml` to add `honestjobs` to `job_adapters` *after* its seed file lands. Because T25.3 `Depends on: T25.1`, the edit is sequential, not parallel — no actual file collision. Engage will schedule T25.3 strictly after T25.1.

All other waves serialize via `Depends on:` edges. No further collisions.

## Sprint Budget

- **Total Cx:** 201
- **Task count:** 9
- **P0 count / P1 count / P2 count:** 7 P0 / 2 P1 / 0 P2
- **Calibration vs prior sprints:** S22 = 13 tasks / 225 Cx; S24 = 11 tasks / ~340 Cx. S25 sits comfortably below both — *additive* sprint shape, no schema migrations, no engine changes.
- **Cut-list (if budget overflows):** T25.7 (P1, DFW view) → defer to S26. T25.8 (P1, frontend plumbing) → minimal version (DEMO_ZIPS only, skip i18n). Sprint still ships a working Dallas city config + seed + DART transit + validated routers without these.

## Integration Points (cross-task only)

- **T25.1 → all** — `cities/dallas.yaml` is the cross-task contract. CityConfig schema fixes the shape; downstream tasks consume via `load_city_config('dallas')`.
- **T25.5 → T25.6** — DART transit seed feeds the city-aware router validation tests. `test_distance.py` extension reads `data/cities/dallas/transit_stops.json` for ZIP coverage assertions.
- **T25.2 + T25.3 + T25.5 → T25.7** — DFW summary page reads counts from each seed file. Schema parity with FW guaranteed by AC `mirror FW shape exactly`.
- **T25.6 → T25.7 + T25.9** — validation gate must be green before DFW view ships (else page surfaces stale/incomplete counts).
- **T25.6 → T25.9** — anonymous-first invariant + charter integrity assertion (S22 + S24 patterns) carry forward; integration gate re-runs them.

## Out of Scope (explicit boundaries)

These are deliberately deferred. Engage should reject any task that drifts here:

1. **Cross-city *matching*** — a Dallas user seeing FW jobs in `/api/jobs` requires matcher changes (employer-index unification, geo-radius extension). Future sprint.
2. **DFW employer-index unification** — employers tagged with metros instead of cities. Schema change touching matching tables; out of scope for an additive city sprint.
3. **City selector UI on `/assess`** — manual override of ZIP→city resolution. Breaks the canonical resolution path; UX deviation requires its own design pass.
4. **Houston / 3rd-state expansion** — sprint scope strictly = DFW.
5. **BrightData crawl tuning for Dallas** — Dallas yaml will declare adapters; tuning per-adapter for the new market is a follow-up.
6. **Per-city geocoder proximity refinement** — current DFW shared proximity bias covers Dallas; per-city refinement is a future optimization.
7. **CitySelector.tsx component / city picker** — see #3.
8. **Cross-metro sharing of `verification_tier` / S24 listing claims** — verification is per-listing, not per-metro. No metro-aware logic enters the verification path.

## Charter Integrity Assertions (S22 + S24 carryforward)

- **Money never moves position** (charter principle 1) — adding Dallas does not change scoring weights. Existing tests guard.
- **Anonymous-first invariant** (S22) — `set_city_context('dallas')` is per-request, opt-in via ZIP resolution. Test re-runs in T25.6.
- **Display-only badge invariant** (S24) — DFW summary page is read-only; charter grep across `backend/app/modules/matching/` for Dallas-specific references must return ZERO matches at integration gate.

---

Brief ready. To generate the backlog:

  /draft-backlog .paircoder/plans/briefs/brief-sprint-25-dallas-expansion.md
