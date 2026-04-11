# Sprint S1 — City Framework Scaffold

**Plan type:** refactor
**Sprint:** S1
**Total Cx:** 155
**Tasks:** 8 (P0: 7, P1: 1, P2: 0)

## Goal

Introduce a city-framework seam so future sprints can target Fort Worth (and later cities) without touching Montgomery's working code paths. This sprint builds the scaffold only: a `CityConfig` YAML schema and loader, a `JobAdapter` protocol, a thin BrightData-wrapper adapter that preserves existing behavior behind `CITY=montgomery`, stub TWC and USAJobs adapter files (interface + empty-list return, no network calls), a Fort Worth config stub with no seed data, and wiring in `JobAggregator` so the active `CITY=` env var selects adapters from the city config. Montgomery behavior must be byte-for-byte unchanged after the sprint.

## Phase 1: Foundation (parallel, no dependencies)

### T1.1 — CityConfig schema + YAML loader | Cx: 25 | P0

**Description:**
Define a Pydantic `CityConfig` model and a `load_city_config(city: str) -> CityConfig` loader that reads `cities/{city}.yaml`. Add a `CITY: str = "montgomery"` setting to `backend/app/core/config.py` and expose a `get_city_config()` helper that uses the active `CITY` env var. This task creates the new `backend/app/cities/` package.

**AC:**
- [ ] `CityConfig` model validates required fields: `name`, `state`, `zip_ranges`, `job_adapters` (list of adapter names), `data_dir`
- [ ] `load_city_config("montgomery")` loads `cities/montgomery.yaml` and returns a populated `CityConfig`
- [ ] `load_city_config("fort-worth")` loads the scaffold `cities/fort-worth.yaml` without error
- [ ] `load_city_config("nonexistent")` raises `CityConfigNotFoundError` with a clear message
- [ ] `CITY=montgomery` is the default; existing env-var parsing unchanged
- [ ] `bpsai-pair arch check backend/app/cities/config.py` passes
- [ ] `bpsai-pair arch check backend/app/core/config.py` still passes after modification

**Depends on:** none

---

### T1.2 — Seed cities/ and data/cities/ directory structure | Cx: 10 | P0

**Description:**
Create `cities/montgomery.yaml` reflecting the current Montgomery hardcoding (state=AL, adapters=[brightdata, honestjobs], zip ranges, data_dir pointer) and `cities/fort-worth.yaml` as a scaffold (state=TX, adapters=[twc, usajobs], zip ranges, empty seed data). Create `data/cities/montgomery/` and `data/cities/fort-worth/` directories with `.gitkeep` placeholders so later sprints can drop seed files without touching repo structure.

**AC:**
- [ ] `cities/montgomery.yaml` validates against `CityConfig` schema from T1.1
- [ ] `cities/fort-worth.yaml` validates against `CityConfig` schema from T1.1
- [ ] No code references to hardcoded Montgomery values leak into the YAML (use variables only)
- [ ] `data/cities/montgomery/.gitkeep` and `data/cities/fort-worth/.gitkeep` present

**Depends on:** none

---

### T1.3 — JobAdapter protocol and registry | Cx: 15 | P0

**Description:**
Create `backend/app/integrations/adapters/` package. Define a `JobAdapter` Protocol with `async def fetch_jobs(self, session, query: str, location: str) -> list[dict]`. Implement a `get_adapter(name: str) -> JobAdapter` registry with lazy imports so concrete adapter modules can register without circular dependencies. Raise `AdapterNotFoundError` for unknown adapter names.

**AC:**
- [ ] `JobAdapter` is a `typing.Protocol` with `async def fetch_jobs(self, session, query: str, location: str) -> list[dict]`
- [ ] `get_adapter("brightdata")` returns the BrightData adapter (implemented in T1.4)
- [ ] `get_adapter("unknown")` raises `AdapterNotFoundError`
- [ ] No runtime imports of BrightData symbols in `base.py` — registry uses lazy imports so T1.4/T1.5 can register without circular deps

**Depends on:** none

---

## Phase 2: Adapter implementations (parallel after T1.3)

### T1.4 — BrightData adapter wrapper | Cx: 15 | P0

**Description:**
Create `backend/app/integrations/adapters/brightdata_adapter.py` implementing a `BrightDataAdapter` class that conforms to the `JobAdapter` protocol. It must delegate to the existing `_brightdata_cached` query logic from `JobAggregator` so that results are byte-identical to the pre-sprint behavior. Do not modify any files inside `backend/app/integrations/brightdata/` — wrap, do not rewrite.

**AC:**
- [ ] `BrightDataAdapter.fetch_jobs()` returns the exact same rows as `JobAggregator._brightdata_cached()` given the same session and timestamp
- [ ] No modifications to files inside `backend/app/integrations/brightdata/`
- [ ] Registered in the adapter registry via T1.3's lazy-import mechanism

**Depends on:** T1.3

---

### T1.5 — TWC and USAJobs stub adapters | Cx: 15 | P1

**Description:**
Create `backend/app/integrations/adapters/twc_adapter.py` and `backend/app/integrations/adapters/usajobs_adapter.py` as stub implementations. Each returns an empty list on every call and logs a single `stub: live <adapter> integration lands in S2` warning at process start (not per call). Both conform to the `JobAdapter` protocol and register in the adapter registry. No network calls, no external dependencies.

**AC:**
- [ ] Both adapters conform to the `JobAdapter` protocol (mypy/pyright verifies)
- [ ] Both return `[]` on every call
- [ ] Both log exactly once per process, not per call, to avoid log flooding
- [ ] Registered in the adapter registry

**Depends on:** T1.3

---

## Phase 3: Wiring (sequential after adapters)

### T1.6 — Wire CITY env var into JobAggregator | Cx: 35 | P0

**Description:**
Refactor `backend/app/integrations/job_aggregator.py` to replace the hardcoded `_brightdata_cached` + `_honestjobs_cached` parallel tasks with a loop over `city_config.job_adapters` that resolves adapters via `get_adapter()`. The default `"Montgomery, AL"` location string must move out of the aggregator and into `cities/montgomery.yaml`. The single caller at `backend/app/routes/jobs.py` must continue to work unchanged — the `JobAggregator.search()` signature is preserved. Behavior for `CITY=montgomery` must be byte-for-byte identical to the pre-sprint version.

**AC:**
- [ ] With `CITY=montgomery` (default), `JobAggregator.search()` returns byte-identical results to the pre-sprint version (verified via snapshot test with fixture DB)
- [ ] With `CITY=fort-worth`, `JobAggregator.search()` returns `[]` (stubs only) and does not error
- [ ] `JobAggregator` line count stays under 150 (warning threshold)
- [ ] `"Montgomery, AL"` default location is moved into `cities/montgomery.yaml`, not hardcoded in the aggregator
- [ ] Single caller `routes/jobs.py` unchanged — `JobAggregator.search()` signature preserved

**Depends on:** T1.1, T1.3, T1.4, T1.5

---

## Phase 4: Tests (sequential after wiring)

### T1.7 — Tests: city config, adapter protocol, CITY selection | Cx: 30 | P0

**Description:**
Write three new test files under `backend/tests/`: `test_city_config.py`, `test_adapter_protocol.py`, and `test_job_aggregator_city.py`. The critical test is the `JobAggregator` snapshot: capture the exact output of the pre-sprint `JobAggregator.search()` against a fixture DB *before* T1.6's edits land, then assert that the post-sprint `CITY=montgomery` path produces identical output. This snapshot is the backward-compat anchor for the entire sprint.

**AC:**
- [ ] Tests written FIRST per TDD — failing-test-then-code sequence preserved within each covered task
- [ ] `test_city_config.py` covers: load montgomery, load fort-worth, load invalid, schema validation
- [ ] `test_adapter_protocol.py` covers: registry lookup, unknown adapter raises, BrightData adapter round-trips fixture data
- [ ] `test_job_aggregator_city.py` covers: CITY=montgomery parity with pre-sprint behavior (snapshot), CITY=fort-worth returns empty
- [ ] Snapshot fixture captured from the current `JobAggregator` BEFORE T1.6 lands — snapshot is the backward-compat anchor
- [ ] `ruff check` clean on all new test files

**Depends on:** T1.1, T1.3, T1.6

---

## Phase 5: Integration gate

### T1.8 — Integration gate | Cx: 10 | P0

**Description:**
Run the full verification suite and reconcile bookkeeping. Confirm the backend test suite is green, `ruff check` is clean, `bpsai-pair arch check backend/` shows no new violations versus the pre-sprint baseline, `.paircoder/context/state.md` is updated with a Sprint S1 completion entry, and a PR is pushed to the `sprint/s1-framework-extraction` branch with CI green.

**AC:**
- [ ] Full backend test suite green (1,391+ tests baseline, plus new S1 tests)
- [ ] `ruff check .` clean
- [ ] `bpsai-pair arch check backend/` → no new violations vs. pre-sprint baseline
- [ ] `.paircoder/context/state.md` updated with S1 completion entry
- [ ] PR pushed to `sprint/s1-framework-extraction`, CI green

**Depends on:** T1.1, T1.2, T1.3, T1.4, T1.5, T1.6, T1.7

---

## Delivery Summary

| ID | Title | Cx | Priority | Depends on | Phase |
|----|-------|----|----------|------------|-------|
| T1.1 | CityConfig schema + YAML loader | 25 | P0 | none | 1 |
| T1.2 | Seed cities/ and data/cities/ directory structure | 10 | P0 | none | 1 |
| T1.3 | JobAdapter protocol and registry | 15 | P0 | none | 1 |
| T1.4 | BrightData adapter wrapper | 15 | P0 | T1.3 | 2 |
| T1.5 | TWC and USAJobs stub adapters | 15 | P1 | T1.3 | 2 |
| T1.6 | Wire CITY env var into JobAggregator | 35 | P0 | T1.1, T1.3, T1.4, T1.5 | 3 |
| T1.7 | Tests: city config, adapter protocol, CITY selection | 30 | P0 | T1.1, T1.3, T1.6 | 4 |
| T1.8 | Integration gate | 10 | P0 | T1.1, T1.2, T1.3, T1.4, T1.5, T1.6, T1.7 | 5 |

**Total:** 8 tasks, 155 Cx

## Priority Order (engage cut-list)

1. T1.1 — CityConfig schema + YAML loader (P0, foundation)
2. T1.3 — JobAdapter protocol and registry (P0, foundation)
3. T1.2 — Seed cities/ and data/cities/ directory structure (P0, foundation)
4. T1.4 — BrightData adapter wrapper (P0, preserves Montgomery)
5. T1.6 — Wire CITY env var into JobAggregator (P0, core wiring)
6. T1.7 — Tests: city config, adapter protocol, CITY selection (P0, backward-compat anchor)
7. T1.8 — Integration gate (P0, ship gate)
8. T1.5 — TWC and USAJobs stub adapters (P1, sole cut candidate — defers to top of S2 if budget overflows)

## Out of Scope

- Live TWC/USAJobs API integration (S2)
- De-hardcoding the 43 Montgomery/Alabama references across 19 files in `modules/{criminal,benefits,matching,resources}` (S2–S4)
- Texas benefit thresholds, HHSC rules, cliff engine Texas port (S3)
- Texas expunction/nondisclosure rules (S2)
- Trinity Metro GTFS ingestion (S4)
- Fort Worth seed data — career centers, employers, childcare, legal aid (S4)
- Fair-chance employer index (S4)
- Barrier graph RAG completion — T23.2–T23.7 (S5)
- Spanish i18n (S5)
- Anonymous / no-account flow (S6)
- Any UI / frontend changes
- Any modifications inside `backend/app/integrations/brightdata/` — wrap, do not rewrite
- Arch check fixes for `brightdata/cache.py` (158 LOC) and `dataset_loader.py` (190 LOC) — still warnings, below the 400 error threshold
