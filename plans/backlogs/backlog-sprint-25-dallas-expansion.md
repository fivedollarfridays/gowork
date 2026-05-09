# Sprint 25 — Dallas Expansion (DFW Unification)

**Plan type:** feature
**Sprint:** 25
**Total Cx:** 201
**Tasks:** 9 (P0: 7, P1: 2, P2: 0)
**Brief:** `.paircoder/plans/briefs/brief-sprint-25-dallas-expansion.md`
**Builds on:** Sprint S2 (Fort Worth seed shape, transit JSON contract, employer index pattern). Sprint S5 (Texas state-level modules — HHSC benefits, Art. 55 expunction, Gov Code Ch. 411 E-1 nondisclosure — Dallas inherits via `city.state == "TX"` dispatch). Sprint S22 (anonymous-first invariant; Dallas adds zero auth-gated routes). Sprint S23 (`<RoleGate>` + `useAccountRoles` + `require_role("admin")` — used by T25.7 DFW summary page). Sprint S24 (charter integrity assertion pattern — T25.9 carries it forward).

## Goal

Bring up Dallas, TX as the second city in the Texas state-share. The existing city architecture (`get_city_config()` + `city.state == "TX"` dispatch across `main.py`, `core/database.py`, `barrier_intel/`, `core/day_boundary.py`, `integrations/brightdata/precrawl.py`, `integrations/job_aggregator.py`, `ai/client.py`, `ai/providers.py`, `ai/prompt_router.py`) is **already plug-and-play** — adding Dallas requires zero per-city branching. This sprint is *additive*: new city yaml, new module under `backend/app/cities/dallas/`, new seed JSON files under `data/cities/dallas/`, plus a reusable DART GTFS importer that emits the canonical Fort Worth transit JSON shape.

The sprint caps with a read-only DFW cross-metro summary page (admin-gated) that surfaces resource counts, transit coverage, and employer counts side-by-side. This is a **diagnostic** view, not a matching change.

## What ships in S25 vs deferred

**S25 (this sprint):** `cities/dallas.yaml` config; `backend/app/cities/dallas/{__init__.py, eligibility.py}` module; full `data/cities/dallas/` seed (community resources, career centers, employers, employer policies, honestjobs listings, barrier graph, training programs, childcare providers); reusable `scripts/import_gtfs.py` GTFS-to-FW-JSON-shape importer with DART import committed; DFW bounding-box test extension; full city-aware router validation suite for Dallas; Dallas E2E assessment-flow integration test; frontend `useDemoMode` Dallas plumbing + i18n; admin-gated DFW cross-metro summary page (read-only diagnostic). Charter integrity assertion holds (matching engine reads ZERO Dallas-specific signals).

**Deferred to S26+:** Cross-city *matching* (a Dallas resident seeing FW jobs in `/api/jobs` — requires matcher + employer-index changes). DFW employer-index unification (employers tagged with metros). Manual city selector UI on `/assess` (breaks ZIP-derived canonical resolution). Houston / 3rd-state expansion. BrightData crawl tuning for Dallas (config inclusion only this sprint). Per-city geocoder proximity refinement (current DFW shared bias covers Dallas). Cross-metro sharing of `verification_tier` / S24 listing claims (verification stays per-listing).

## Architectural principles

- **Additive only — zero invasive refactor.** No file in `backend/app/modules/matching/`, no file in `backend/app/cities/config.py`, no file in `backend/app/core/config.py` is modified by this sprint. Dispatch already keys on `city.state == "TX"`; Dallas inherits.
- **City data shape is the contract.** All `data/cities/dallas/*.json` files mirror the FW shape exactly — loaders are city-agnostic. Schema drift breaks Dallas + FW symmetrically and surfaces in T25.6 validation.
- **GTFS importer is the contract boundary** between any future GTFS feed and the canonical FW JSON shape. T25.5 ships the script + runbook + test fixture. Future cities (Houston METRO, etc.) get the path for free.
- **Anonymous-first invariant (S22) holds.** No new auth-gated routes for end users. T25.7's DFW summary page is `require_role("admin")`-gated only; not in the candidate funnel.
- **Charter integrity (S24) holds.** Matching engine reads ZERO Dallas-specific signals. T25.9 grep-asserts at the gate. The DFW summary page is **display-only**; it does not write to any matching table.
- **Geocoder DFW proximity already covers Dallas.** `_DFW_PROXIMITY = "-97.32,32.75"` (downtown FW) is a ranking hint, not a filter; Dallas ZIPs sit ~30 mi east, well within bias radius. No geocoder change.
- **No selector UI.** ZIP→city resolution stays canonical. Adding a manual override would break the anonymous-first invariant and require an entire UX design pass.

---

## Phase 1: Foundation — Dallas city config + module skeleton

### T25.1 — Dallas city config + module skeleton | Cx: 12 | P0

**Description:**
Add the `cities/dallas.yaml` config plus the `backend/app/cities/dallas/` python module mirroring the FW pattern exactly. The module ships an `__init__.py` carrying the gate-on-`city.state=="TX"` warning verbatim from FW, plus an `eligibility.py` populated with Dallas resource eligibility rules (`{"type": "open" | "income" | "enrollment" | "compound"}` shape). Verifies that `load_city_config('dallas')` round-trips cleanly through the existing `CityConfig` Pydantic model. No code modifications outside the new files.

**AC:**
- [ ] `cities/dallas.yaml` declares: `name: Dallas`, `state: TX`, `location: "Dallas, TX"`, `zip_ranges: ["75201-75398"]`, `job_adapters: [twc, usajobs]` (honestjobs added by T25.3 once seed lands), `data_dir: data/cities/dallas`
- [ ] `cities/dallas.yaml` declares `appointment_services` mirroring FW exactly: `court_hearing`, `benefits_recert`, `dmv`, `childcare_intake` with same hours_local + closed_days_of_week
- [ ] `backend/app/cities/dallas/__init__.py` carries the `city.state == "TX"` gating warning verbatim from `backend/app/cities/fort_worth/__init__.py`
- [ ] `backend/app/cities/dallas/eligibility.py` defines `DALLAS_ELIGIBILITY_RULES` dict with at minimum: Workforce Solutions Greater Dallas (open), Dallas College (open), DART (open), Parkland Health (open), Legal Aid of NorthWest Texas — Dallas (open), Dallas Housing Authority (open), Texas Rising Star (open), TWC Child Care Services (compound, smi gate from `app.modules.benefits.thresholds`), North Texas 211 (open)
- [ ] `backend/tests/test_dallas_city_config.py` asserts: `load_city_config('dallas')` returns valid CityConfig; `state == "TX"`; data_dir resolves correctly; appointment_services schema parity with FW
- [ ] `bpsai-pair arch check backend/app/cities/dallas/eligibility.py` passes
- [ ] `bpsai-pair arch check backend/app/cities/dallas/__init__.py` passes

**Depends on:** none

---

## Phase 2: Seed data — parallel lanes

### T25.2 — Dallas community resources + career centers seed | Cx: 28 | P0

**Description:**
Author `data/cities/dallas/community_resources.json`, `data/cities/dallas/resources.json`, and `data/cities/dallas/career_centers.json` with curated Dallas-area entries from open sources. Schema parity with FW JSON shape — every entry includes `name`, `category`, `subcategory`, `address`, `lat`, `lng`, `phone`, `url`. All coordinates geocoded (no neutral fallback). Eligibility entries for any new resource names added via T25.1's `DALLAS_ELIGIBILITY_RULES` are confirmed present.

**AC:**
- [ ] `data/cities/dallas/community_resources.json` includes Workforce Solutions Greater Dallas (comprehensive site + 2 satellites minimum), Dallas Public Library job centers (≥2), Catholic Charities Dallas, North Texas Food Bank, Dallas County Health & Human Services, ChildCareGroup, North Texas 211
- [ ] Legal aid entries: Legal Aid of NorthWest Texas (Dallas branch), Dallas Volunteer Attorney Program
- [ ] Housing entries: Dallas Housing Authority, Family Gateway, Dallas LIFE
- [ ] `data/cities/dallas/career_centers.json` mirrors FW structure: at least the Workforce Solutions Greater Dallas comprehensive center as `subcategory: comprehensive`
- [ ] `data/cities/dallas/resources.json` follows FW schema (resources surfaced in barrier-card UI)
- [ ] All entries have non-zero `lat`/`lng` (geocoded; no `0.0` placeholders)
- [ ] All entries have non-empty `phone` and `url` (where publicly available; explicit `null` only when source provides nothing)
- [ ] Any resource name introduced here exists in `DALLAS_ELIGIBILITY_RULES` from T25.1, OR follows the implicit "open" rule via the matcher fallback
- [ ] JSON validates: parses cleanly, no trailing commas, UTF-8 encoded
- [ ] Loader smoke test: existing FW loader, when pointed at `data/cities/dallas/`, returns ≥10 community resources without error

**Depends on:** T25.1

---

### T25.3 — Dallas employer index (fair-chance + general) | Cx: 30 | P0

**Description:**
Author `data/cities/dallas/employers.json`, `data/cities/dallas/employer_policies_seed.json`, and `backend/data/cities/dallas/honestjobs_listings.json` with curated Dallas-area employer entries from open sources (DFW Hire Reentry, Workforce Solutions Greater Dallas employer directory, public fair-chance pledge lists). Schema parity with FW. Append `honestjobs` to `cities/dallas.yaml` `job_adapters` list once the seed file lands so the JobAggregator path picks it up.

**AC:**
- [ ] `data/cities/dallas/employers.json` includes ≥30 Dallas-area employers from open sources, including reentry-friendly + general
- [ ] `data/cities/dallas/employer_policies_seed.json` mirrors FW schema (background-check timing, fair-chance flags, application steps)
- [ ] `backend/data/cities/dallas/honestjobs_listings.json` includes ≥15 Dallas-specific listings (FW honestjobs entries already tagging "DFW" remain in FW seed; do not duplicate)
- [ ] `cities/dallas.yaml` `job_adapters` list updated to add `honestjobs` after seed lands
- [ ] All employer entries include `name`, `category`, `lat`, `lng`, `address`, `phone`, `url`, `fair_chance: bool`, `background_check_timing` (matching FW employer_policies fields)
- [ ] No duplication with FW seed (verify by intersecting `name`+`address` across `data/cities/fort-worth/employers.json` and `data/cities/dallas/employers.json` — empty intersection or explicit cross-metro tag)
- [ ] JobAggregator smoke test: `get_city_config('dallas').job_adapters` includes `honestjobs`; loader resolves the listings file via the city `data_dir` path

**Depends on:** T25.1

---

### T25.4 — Dallas barrier graph + training programs + childcare providers seed | Cx: 18 | P0

**Description:**
Author `data/cities/dallas/barrier_graph_seed.json`, `data/cities/dallas/training_programs.json`, and `data/cities/dallas/childcare_providers.json`. The barrier graph is structurally identical to FW (same nodes/edges); only resource references swap to Dallas equivalents from T25.2's seed. Training programs and childcare providers are Dallas-specific from open sources.

**AC:**
- [ ] `data/cities/dallas/barrier_graph_seed.json` is structurally identical to `data/cities/fort-worth/barrier_graph_seed.json` (same barrier IDs, same edges, same relationship types) with only resource references swapped to Dallas names from T25.2
- [ ] Diff between `barrier_graph_seed.json` files (FW vs Dallas, ignoring whitespace + resource_name fields) is empty for structural keys
- [ ] `data/cities/dallas/training_programs.json` includes Dallas College (formerly DCCCD) campuses, Texans Can Academies (Dallas), Dallas Workforce Development apprenticeships
- [ ] `data/cities/dallas/childcare_providers.json` includes ChildCareGroup centers, Dallas-area Texas Rising Star providers (≥10 entries)
- [ ] All entries follow FW JSON shape (loaders are city-agnostic)
- [ ] Resource references in `barrier_graph_seed.json` ALL appear in `community_resources.json` from T25.2 (verifiable via cross-file name-match)

**Depends on:** T25.2

---

### T25.5 — DART GTFS importer + Dallas transit seed | Cx: 35 | P0

**Description:**
Ship `scripts/import_gtfs.py` — a reusable GTFS-to-FW-JSON-shape importer. Accepts a GTFS zip path + city slug; emits `transit_routes.json` + `transit_stops.json` matching the canonical FW shape. Routes carry `{route_number, route_name, weekday_start, weekday_end, saturday, sunday}`; stops carry `{route_id, stop_name, lat, lng, sequence}`. Run the importer against the public DART GTFS feed; commit the output under `data/cities/dallas/`. Ship a runbook so future cities (Houston METRO, etc.) get the same path for free.

The importer is the contract boundary between GTFS feeds and the seed format — schema drift surfaces here, not in downstream consumers.

**AC:**
- [ ] `scripts/import_gtfs.py` accepts `--gtfs-zip <path>` and `--city <slug>` flags
- [ ] Outputs `data/cities/<slug>/transit_routes.json` matching shape: `[{route_number: int, route_name: str, weekday_start: "HH:MM", weekday_end: "HH:MM", saturday: bool, sunday: bool}, ...]`
- [ ] Outputs `data/cities/<slug>/transit_stops.json` matching shape: `[{route_id: int, stop_name: str, lat: float, lng: float, sequence: int}, ...]`
- [ ] `weekday_start`/`weekday_end` derived from `stop_times.txt` MIN/MAX over `service_id` weekday calendar entries (calendar.txt with monday/tuesday/.../friday flag)
- [ ] `saturday`/`sunday` derived from `calendar.txt` boolean flags for the route's primary service_id
- [ ] Stop sequence preserves GTFS `stop_sequence` per route
- [ ] Idempotent: re-running on the same GTFS produces byte-identical JSON (sorted keys, stable iteration, deterministic floats — round to 4 decimals)
- [ ] `scripts/__tests__/test_import_gtfs.py` feeds a fixture mini-GTFS (3-route, 8-stop) and asserts: route count, stop count, schema match, weekday boundary derivation, sat/sun flag mapping, idempotency byte-match across two runs
- [ ] Dallas DART import: `python scripts/import_gtfs.py --gtfs-zip <DART_GTFS> --city dallas` produces non-empty seed files committed under `data/cities/dallas/`
- [ ] DART output: ≥80 routes, ≥1000 stops (DART operates ~120 routes; sanity floor)
- [ ] `docs/import-gtfs-runbook.md` documents: where to fetch each city's GTFS feed, license/attribution requirements, importer invocation, expected output shape
- [ ] `bpsai-pair arch check scripts/import_gtfs.py` passes

**Depends on:** T25.1

---

## Phase 3: Validation — city-aware routers + DFW bounding box + E2E

### T25.6 — City-aware router validation + DFW bounding-box extension + Dallas E2E | Cx: 25 | P0

**Description:**
Single validation task covering three concerns: (1) parametrized tests over `(city_slug, expected_state)` asserting every city-aware backend module dispatches correctly when `set_city_context('dallas')` is active; (2) `test_distance.py`'s DFW bounding-box assertion extends to embedded Dallas ZIPs; (3) full E2E assessment-flow integration test with a Dallas ZIP. Re-runs the S22 anonymous-first invariant test for `CITY=dallas`.

**AC:**
- [ ] `backend/tests/test_dallas_city_routers.py` (new) parametrizes over `(city_slug, expected_state)` and asserts the following modules return Dallas-correct values when `set_city_context('dallas')` is active: `geo_router`, `resource_router`, `eligibility` (resources module), `barrier_intel/prompts`, `barrier_intel/guardrails`, `integrations/brightdata/precrawl`, `integrations/job_aggregator`, `ai/client`, `ai/providers`, `ai/prompt_router`
- [ ] Each parametrized assertion verifies the module either: (a) returns Texas-state-shared output unchanged from FW, OR (b) routes through Dallas-specific data (e.g. `job_aggregator` finds Dallas employers in `data/cities/dallas/`)
- [ ] `backend/tests/test_distance.py` DFW bounding-box assertion extends to include embedded Dallas ZIPs: 75201, 75204, 75215, 75216, 75217, 75224, 75227, 75228, 75232, 75241 — all must land inside the existing DFW bounding box (no box widening required)
- [ ] `backend/tests/test_dallas_e2e.py` (new): POST `/api/assessment` with ZIP 75201 + barrier profile → GET `/api/plan/{session_id}` → assert plan returns: ≥1 Dallas community resource, DART transit references in transit-related sections, ≥1 Dallas employer in job matches, Texas-state-shared barrier intel (HHSC benefits / Art. 55 expunction references where applicable)
- [ ] S22 anonymous-first invariant test re-runs green when `CITY=dallas`: zero Dallas-specific routes added to `REQUIRES_AUTH_ALLOWLIST`
- [ ] All new tests pass on both sqlite + postgres axes
- [ ] No regression: full backend pytest suite green vs S24 baseline (4700 passed / 4 baseline failed / 2 skipped)
- [ ] `bpsai-pair arch check` passes on touched test files

**Depends on:** T25.1, T25.2, T25.3, T25.4, T25.5

---

## Phase 4: Frontend plumbing + DFW summary view

### T25.7 — DFW cross-metro summary admin page | Cx: 28 | P1

**Description:**
Read-only admin-gated summary page comparing Fort Worth and Dallas side-by-side: resource count by category, employer count + fair-chance percentage, transit route count + total stops, career center count. Backend route reads counts from JSON seed files via `load_city_config(slug).data_dir` — no DB queries, no matching-engine touch. Frontend renders side-by-side cards with a "DFW total" footer row. Page header explicitly states "Read-only diagnostic. Cross-city matching is not enabled." to prevent misinterpretation.

Charter integrity: page is **display-only**. No writes to matching tables. T25.9's grep gate confirms zero Dallas-specific references in `backend/app/modules/matching/`.

**AC:**
- [ ] `backend/app/routes/cities_admin.py` (new) exposes `GET /api/admin/cities/summary` — admin-gated via `require_role("admin")` (S23 pattern)
- [ ] Response shape: `{cities: [{slug, name, state, resource_counts: {...}, employer_count, fair_chance_count, fair_chance_pct, transit_route_count, transit_stop_count, career_center_count}, ...], dfw_total: {...}}`
- [ ] Backend reads counts from JSON seed files via `load_city_config(slug).data_dir`; **no DB queries**, no `select(...)` against any matching table
- [ ] `backend/tests/test_cities_admin.py` covers: admin happy path returns 200 with both FW + Dallas summaries; non-admin returns 403; anonymous returns 401; counts match the seed-file content via direct file-read in the test
- [ ] `frontend/src/lib/api/cities_admin.ts` typed API client following the S23 assessments client pattern (credentials:include, `_fetchWithTimeout`, single typed `CitiesAdminApiError`)
- [ ] `frontend/src/app/admin/cities/dfw/page.tsx` renders side-by-side cards (Fort Worth | Dallas) with a "DFW total" footer row
- [ ] Page wrapped in `<RoleGate roles={["admin"]}>` (S23 pattern)
- [ ] Page header copy explicitly states: "Read-only diagnostic. Cross-city matching is not enabled."
- [ ] `frontend/src/app/admin/cities/dfw/__tests__/page.test.tsx` covers: renders both city cards, footer total = sum, role-gate blocks non-admin (RoleGate denied state visible)
- [ ] `npx tsc --noEmit` clean; `npx next build` green
- [ ] No imports from `backend/app/modules/matching/` in either backend or frontend code on this path

**Depends on:** T25.6

---

### T25.8 — Frontend Dallas plumbing + i18n | Cx: 15 | P1

**Description:**
Wire Dallas into the frontend demo-mode hooks and translation catalogs. Add Dallas to `DEMO_ZIPS`. Parametrize the existing city-aware demo-mode test over both fort-worth and dallas. Add Dallas display-name translations to en.json + es.json. NO new selector UI — ZIP→city resolution stays canonical.

**AC:**
- [ ] `frontend/src/hooks/useDemoMode.ts` adds `DEMO_ZIPS["dallas"] = "75201"` (canonical Dallas demo ZIP)
- [ ] `frontend/src/hooks/__tests__/useDemoMode-cityaware.test.ts` parametrized over `(city, expectedZip)` for both `fort-worth` and `dallas`; both pass
- [ ] `frontend/src/lib/translations/en.json` adds Dallas display strings (city name, region label) — keep symmetric with FW entries
- [ ] `frontend/src/lib/translations/es.json` adds matching Spanish translations
- [ ] No selector UI added; no new component file under `frontend/src/components/` for city picking
- [ ] Translation key audit (existing `missingKeysAudit`) passes — both EN + ES catalogs have equal Dallas-key coverage
- [ ] `npx tsc --noEmit` clean; `npx next build` green
- [ ] vitest suite green vs S24 baseline (3620 passed / 3 skipped / 0 failed)

**Depends on:** T25.1

---

## Phase 5: Integration gate

### T25.9 — Sprint 25 integration gate | Cx: 10 | P0

**Description:**
Final gate. Re-runs all suites on both sqlite + postgres axes. Asserts the load-bearing charter integrity invariant: matching engine reads ZERO Dallas-specific signals (carrying forward S24's grep pattern). Reconciles state.md (demote S22-S24 to Previous Sprints summary; refresh Current Focus to Dallas; reset What's Next). Pushes PR; CI green on all jobs.

**AC:**
- [ ] Full backend pytest suite green on sqlite + postgres axes (no regressions vs S24 baseline 4700 passed / 4 baseline failed / 2 skipped)
- [ ] Frontend vitest suite green (no regressions vs S24 baseline 3620 passed / 3 skipped / 0 failed)
- [ ] `ruff check .` clean on touched files
- [ ] `bpsai-pair arch check .` no new violations
- [ ] **CHARTER INTEGRITY ASSERTION:** subprocess grep across `backend/app/modules/matching/` for any reference to `dallas`, `DART`, `Dallas`, `75201`, `75398`, or any Dallas-specific resource/employer name — must return ZERO matches. The matching engine remains city-symmetric; no metro-special-case logic. Test fails as design-review trigger if a future sprint legitimately needs cross-metro matching.
- [ ] `tsc --noEmit` 0 errors; `next build` green
- [ ] Postgres CI service container exercises Dallas-aware code paths; no new alembic migrations in S25 (alembic chain stays at head 0014 from S24)
- [ ] `.paircoder/context/state.md` reconciled: Sprint 25 complete entry under "What Was Just Done"; Current Focus updated to summarize Dallas + DFW summary delivery; S22-S24 demoted to Previous Sprints summary; What's Next reset
- [ ] PR pushed; CI green on all jobs
- [ ] ROADMAP.md "Planned Next" Dallas Expansion phase items checked off; new entry added under "Completed" → "Dallas Expansion (Sprint S25) — merged YYYY-MM-DD (PR #N)"

**Depends on:** T25.6, T25.7, T25.8

---

## Delivery Summary

| Phase | Tasks | Cx | Output |
|---|---|---|---|
| 1. Foundation — city config + module skeleton | T25.1 | 12 | `cities/dallas.yaml` + `backend/app/cities/dallas/` module; CityConfig round-trips |
| 2. Seed data — parallel lanes | T25.2, T25.3, T25.4, T25.5 | 111 | Dallas community resources, career centers, employers, employer policies, honestjobs listings, barrier graph, training, childcare, DART transit (via reusable GTFS importer) |
| 3. Validation — routers + bounding box + E2E | T25.6 | 25 | All city-aware modules dispatch Dallas correctly; DFW box covers Dallas ZIPs; full Dallas assessment-flow E2E green |
| 4. Frontend + DFW summary | T25.7, T25.8 | 43 | Read-only DFW cross-metro admin summary page + Dallas demo-mode plumbing + i18n |
| 5. Integration gate | T25.9 | 10 | Charter integrity assertion holds; state.md + ROADMAP.md reconciled; PR green |
| **Total** | **9** | **201** | Dallas live as second city in TX state-share; DART transit ingested via reusable importer; DFW diagnostic surface |

## Priority Order

Engage cut-list (in order P2 → P1 → P0; cut from the top if budget overflows):

1. **P0 (cannot cut — load-bearing chain):** T25.1, T25.2, T25.3, T25.4, T25.5, T25.6, T25.9
2. **P1 (cuttable in budget pressure):**
   - T25.7 — DFW cross-metro summary admin page. Sprint still ships a working Dallas city without the diagnostic page; defer to S26 if Cx tight.
   - T25.8 — Frontend Dallas plumbing + i18n. Minimum viable cut: add `DEMO_ZIPS["dallas"]` only (5 Cx); skip i18n catalog parity until S26.
3. **P2 (none):** No truly cuttable scope below P1.

If both P1 tasks descope, the sprint ships at 161 Cx (7 tasks) with a fully functional Dallas backend + validated routers + E2E green, but no admin diagnostic surface and minimal frontend wiring. The DART importer (T25.5) and city-aware router validation (T25.6) are P0 — they are the load-bearing claims of "Dallas works" and cannot defer.
