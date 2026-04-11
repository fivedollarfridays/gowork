# Feature Brief: Sprint 1 — City Framework Scaffold

## Idea

Introduce a city-framework seam so future sprints can target Fort Worth (and later cities) without touching Montgomery's working code paths. This sprint builds the *scaffold only*: a `CityConfig` YAML schema and loader, a `JobAdapter` protocol, a thin BrightData-wrapper adapter that preserves existing behavior behind `CITY=montgomery`, stub TWC and USAJobs adapter files (interface + empty-list return, no network calls), a Fort Worth config stub with no seed data, and wiring in `JobAggregator` so the active `CITY=` env var selects adapters from the city config. Montgomery behavior must be byte-for-byte unchanged after the sprint. This sprint ships the seam; S2 fills TWC/USAJobs with live calls and S3+ fill the Texas rule sets, Fort Worth seed data, and UI adaptations.

## Codebase Context

- **Stack:** FastAPI, Python 3.13, SQLAlchemy async, Pydantic settings, pytest; Next.js 15 frontend (not touched this sprint)
- **Size:** 128 files under `backend/app`, 90 under `backend/tests`, 141 under `frontend/src`
- **Current sprint:** Sprint 31 complete (BrightData multi-domain consolidation, commute estimator). Last commit on main: `51ba524`.
- **Conflicting in-progress tasks:** none after T31.1 and T23.1 cleanup this turn.
- **Relevant shipped work we'll wrap, not rewrite:** BrightData integration (`backend/app/integrations/brightdata/`, 9 files, ~1000 LOC), `JobAggregator` (77 LOC, single caller in `routes/jobs.py`), cliff engine, benefits eligibility, transit matcher, commute estimator, intelligent job matching — all Montgomery-hardcoded.
- **Montgomery/Alabama hardcoding footprint (for context, NOT this sprint's job):** 43 string references across 19 files including `backend/app/modules/{criminal,benefits,matching,resources}/...`. De-hardcoding these is S2–S4 scope; S1 only adds the seam.

## Sprint-Level Constraints

- **Cross-task arch constraints:** `brightdata/cache.py` (158 lines) and `brightdata/dataset_loader.py` (190 lines) are above the 150-line warning threshold but below the 400 error threshold. S1 wraps these files from the outside via a new adapter module — it does not modify them — so no split task is needed this sprint. Flag for S2 if live TWC/USAJobs work pushes cache.py growth.
- **Oversized files that will grow under S1:** none. `JobAggregator` goes from 77 → ~120 LOC, `config.py` from 125 → ~160 LOC, both well under thresholds. All other touched files are new.
- **TODOs that become tasks:** none blocking. S1 is greenfield scaffold + thin wrapper; the stalled barrier-graph-rag TODOs (S5 territory) do not block this path.
- **Cross-task contract edges:** T1.3 (JobAdapter protocol) is the contract that T1.4 and T1.5 consume. T1.1 (CityConfig loader) produces the type T1.6 consumes. These are the only cross-task contract surfaces.

## Tasks

### T1.1 — CityConfig schema + YAML loader
- **Cx:** 25
- **Priority:** P0
- **Depends on:** none
- **Files:**
  - `backend/app/cities/__init__.py` (new)
  - `backend/app/cities/config.py` (new — `CityConfig` pydantic model, `load_city_config(city: str) -> CityConfig`)
  - `backend/app/core/config.py` (modify — add `CITY: str = "montgomery"` setting and expose `get_city_config()` helper)
- **AC template:** schema
- **Custom AC:**
  - [ ] `CityConfig` model validates required fields: `name`, `state`, `zip_ranges`, `job_adapters` (list of adapter names), `data_dir`
  - [ ] `load_city_config("montgomery")` loads `cities/montgomery.yaml` and returns a populated `CityConfig`
  - [ ] `load_city_config("fort-worth")` loads the scaffold `cities/fort-worth.yaml` without error
  - [ ] `load_city_config("nonexistent")` raises `CityConfigNotFoundError` with a clear message
  - [ ] `CITY=montgomery` is the default; existing env-var parsing unchanged
  - [ ] `bpsai-pair arch check backend/app/cities/config.py` passes
  - [ ] `bpsai-pair arch check backend/app/core/config.py` still passes after modification

### T1.2 — Seed the cities/ and data/cities/ directory structure
- **Cx:** 10
- **Priority:** P0
- **Depends on:** none
- **Files:**
  - `cities/montgomery.yaml` (new — reflects current Montgomery hardcoding: state=AL, adapters=[brightdata, honestjobs], zip_ranges, data_dir)
  - `cities/fort-worth.yaml` (new — state=TX, adapters=[twc, usajobs], zip_ranges, empty seed data)
  - `data/cities/montgomery/.gitkeep` (new)
  - `data/cities/fort-worth/.gitkeep` (new)
- **AC template:** schema
- **Custom AC:**
  - [ ] `cities/montgomery.yaml` validates against `CityConfig` schema from T1.1
  - [ ] `cities/fort-worth.yaml` validates against `CityConfig` schema from T1.1
  - [ ] No code references to hardcoded Montgomery values leak into the yaml (use variables only)

### T1.3 — JobAdapter protocol
- **Cx:** 15
- **Priority:** P0
- **Depends on:** none
- **Files:**
  - `backend/app/integrations/adapters/__init__.py` (new)
  - `backend/app/integrations/adapters/base.py` (new — `JobAdapter` Protocol with `fetch_jobs()` method, `get_adapter(name: str) -> JobAdapter` registry)
- **AC template:** refactor
- **Custom AC:**
  - [ ] `JobAdapter` is a `typing.Protocol` with `async def fetch_jobs(self, session, query: str, location: str) -> list[dict]`
  - [ ] `get_adapter("brightdata")` returns the BrightData adapter (implemented in T1.4)
  - [ ] `get_adapter("unknown")` raises `AdapterNotFoundError`
  - [ ] No runtime imports of BrightData symbols in `base.py` — registry uses lazy imports so T1.4/T1.5 can register without circular deps

### T1.4 — BrightData adapter wrapper (preserves current behavior)
- **Cx:** 15
- **Priority:** P0
- **Depends on:** T1.3
- **Files:**
  - `backend/app/integrations/adapters/brightdata_adapter.py` (new — `BrightDataAdapter` class conforming to `JobAdapter`, delegates to existing `_brightdata_cached` logic from `JobAggregator`)
- **AC template:** refactor
- **Custom AC:**
  - [ ] `BrightDataAdapter.fetch_jobs()` returns the exact same rows as `JobAggregator._brightdata_cached()` given the same session and timestamp
  - [ ] No modifications to files inside `backend/app/integrations/brightdata/`
  - [ ] Registered in the adapter registry via T1.3's lazy-import mechanism

### T1.5 — TWC and USAJobs stub adapters
- **Cx:** 15
- **Priority:** P1
- **Depends on:** T1.3
- **Files:**
  - `backend/app/integrations/adapters/twc_adapter.py` (new — `TwcAdapter` returns `[]`, logs a `stub: live TWC integration lands in S2` warning)
  - `backend/app/integrations/adapters/usajobs_adapter.py` (new — `UsaJobsAdapter` returns `[]`, same stub log)
- **AC template:** refactor
- **Custom AC:**
  - [ ] Both adapters conform to the `JobAdapter` protocol (mypy/pyright verifies)
  - [ ] Both return `[]` on every call
  - [ ] Both log exactly once per process, not per call, to avoid log flooding
  - [ ] Registered in the adapter registry

### T1.6 — Wire CITY env var into JobAggregator adapter selection
- **Cx:** 35
- **Priority:** P0
- **Depends on:** T1.1, T1.3, T1.4, T1.5
- **Files:**
  - `backend/app/integrations/job_aggregator.py` (modify — replace hardcoded `_brightdata_cached` + `_honestjobs_cached` tasks with a loop over `city_config.job_adapters` that resolves adapters via `get_adapter()`)
  - `backend/app/core/config.py` (modify — settings already extended in T1.1; T1.6 only reads from it)
- **AC template:** refactor
- **Custom AC:**
  - [ ] With `CITY=montgomery` (default), `JobAggregator.search()` returns byte-identical results to the pre-sprint version (snapshot test with fixture DB)
  - [ ] With `CITY=fort-worth`, `JobAggregator.search()` returns `[]` (stubs only) and does not error
  - [ ] `JobAggregator` line count stays under 150 (warning threshold)
  - [ ] `"Montgomery, AL"` default location is moved into `cities/montgomery.yaml`, not hardcoded in the aggregator
  - [ ] Single caller `routes/jobs.py` unchanged — `JobAggregator.search()` signature preserved

### T1.7 — Tests: city config, adapter protocol, CITY selection
- **Cx:** 30
- **Priority:** P0
- **Depends on:** T1.1, T1.3, T1.6
- **Files:**
  - `backend/tests/test_city_config.py` (new)
  - `backend/tests/test_adapter_protocol.py` (new)
  - `backend/tests/test_job_aggregator_city.py` (new)
- **AC template:** gate
- **Custom AC:**
  - [ ] Tests written FIRST per TDD (task runs before T1.1/T1.3/T1.6 are finished is acceptable only if failing-test-then-code sequence is preserved within each task's own work)
  - [ ] `test_city_config.py` covers: load montgomery, load fort-worth, load invalid, schema validation
  - [ ] `test_adapter_protocol.py` covers: registry lookup, unknown adapter raises, BrightData adapter round-trips fixture data
  - [ ] `test_job_aggregator_city.py` covers: CITY=montgomery parity with pre-sprint behavior (snapshot), CITY=fort-worth returns empty
  - [ ] Snapshot fixture captured from the current `JobAggregator` BEFORE T1.6 lands — snapshot is the backward-compat anchor
  - [ ] `ruff check` clean on all new test files

### T1.8 — Integration gate
- **Cx:** 10
- **Priority:** P0
- **Depends on:** T1.1, T1.2, T1.3, T1.4, T1.5, T1.6, T1.7
- **Files:** none (verification only)
- **AC template:** gate
- **Custom AC:**
  - [ ] Full backend test suite green (1,391+ tests baseline, plus new S1 tests)
  - [ ] `ruff check .` clean
  - [ ] `bpsai-pair arch check backend/` → no new violations vs. pre-sprint baseline
  - [ ] `.paircoder/context/state.md` updated with S1 completion entry
  - [ ] PR pushed to `sprint/s1-framework-extraction`, CI green

## Dependency Graph

```
Wave 1 (parallel, no deps): T1.1, T1.2, T1.3
Wave 2 (parallel, needs T1.3): T1.4, T1.5
Wave 3 (needs T1.1 + T1.4 + T1.5): T1.6
Wave 4 (needs T1.1 + T1.3 + T1.6): T1.7
Wave 5 (needs all): T1.8
```

Five waves. Wave 1 and Wave 2 are the only parallelism opportunities (3-wide and 2-wide respectively). Waves 3–5 are sequential joins.

## File Collision Matrix

| Wave | Task A | Task B | Intersection |
|---|---|---|---|
| Wave 1 | T1.1 (backend/app/cities/\*, backend/app/core/config.py) | T1.2 (cities/\*.yaml, data/cities/\*) | **None** |
| Wave 1 | T1.1 (backend/app/cities/\*, backend/app/core/config.py) | T1.3 (backend/app/integrations/adapters/\*) | **None** |
| Wave 1 | T1.2 | T1.3 | **None** |
| Wave 2 | T1.4 (adapters/brightdata_adapter.py) | T1.5 (adapters/twc_adapter.py, adapters/usajobs_adapter.py) | **None** |

No collisions. Safe to schedule with `--max-parallel 3` in Wave 1 and `--max-parallel 2` in Wave 2.

## Sprint Budget

- **Total Cx:** 155 (hand-estimated; `bpsai-pair budget estimate --task` API changed, falling back to comparison with Sprints 28–31 which landed in the 130–185 Cx range)
- **Task count:** 8
- **P0:** 7 | **P1:** 1 | **P2:** 0
- **Cut-list:** T1.5 (TWC/USAJobs stubs, P1) is the only cut candidate. If budget overflows, ship T1.1–T1.4 + T1.6–T1.8 with only BrightData registered; add TWC/USAJobs stubs at the top of S2 before the live adapters land.

## Integration Points

- **T1.3 → T1.4, T1.5:** `JobAdapter` protocol defined in T1.3 is the contract T1.4 and T1.5 implement. Changing the protocol signature after T1.4/T1.5 start is a ripple hazard — lock it in Wave 1.
- **T1.1 → T1.6:** `CityConfig.job_adapters` list type produced by T1.1 is what T1.6 iterates. Field name and type must be stable between waves.
- **T1.4 → T1.7:** Snapshot fixture for backward-compat must be captured *before* T1.6 edits `JobAggregator`. T1.7 owns capturing the snapshot as its first act.

## Out of Scope

- **Live TWC/USAJobs API integration** — S2 job.
- **De-hardcoding the 43 Montgomery/Alabama references across 19 files** in `modules/{criminal,benefits,matching,resources}` — S2–S4 job.
- **Texas benefit thresholds, HHSC rules, cliff engine Texas port** — S3.
- **Texas expunction/nondisclosure rules** — S2.
- **Trinity Metro GTFS ingestion** — S4.
- **Fort Worth seed data** (career centers, employers, childcare, legal aid) — S4.
- **Fair-chance employer index** — S4.
- **Barrier graph RAG completion** (T23.2–T23.7) — S5.
- **Spanish i18n** — S5.
- **Anonymous / no-account flow** — S6.
- **Any UI / frontend changes** — zero frontend files touched this sprint.
- **Any modifications inside `backend/app/integrations/brightdata/`** — wrap, do not rewrite.
- **Arch check fixes for `brightdata/cache.py` (158 LOC) and `dataset_loader.py` (190 LOC)** — still warnings, below the 400 error threshold. Defer unless S2 pushes them over.
