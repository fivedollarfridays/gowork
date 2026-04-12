# Sprint S2 --- Fort Worth Data + Texas Rules

**Plan type:** feature
**Sprint:** S2
**Total Cx:** 350
**Tasks:** 18 (P0: 10, P1: 5, P2: 3)

## Goal

Port MontGoWork from Montgomery, Alabama to Fort Worth, Texas for HackFW 2026. Build Texas-specific benefits screener (HHSC programs + thresholds), Texas expunction/nondisclosure rules, Fort Worth seed data (career centers, childcare, legal aid, employers), live TWC and USAJobs API adapters, city-aware module routing so CITY env var selects the correct state rules, and update frontend to be city-aware.

## Phase 1: City-Aware Module Routing (parallel, no dependencies)

### T2.1 --- Texas Benefits Thresholds | Cx: 20 | P0

**Description:**
Create `backend/app/modules/benefits/texas/thresholds.py` with Texas-specific monetary values: TANF amounts (~$308/mo family of 3), CHIP at 200% FPL, Texas SMI, Fort Worth AMI (~$78K for 4-person), childcare cost ($1,100/mo), FMR ($1,350), CEAP values. Also create `texas/__init__.py`.

**AC:**
- [ ] `backend/app/modules/benefits/texas/thresholds.py` exists with all TX constants
- [ ] All values documented with sources
- [ ] `bpsai-pair arch check backend/app/modules/benefits/texas/thresholds.py` passes

**Depends on:** none

---

### T2.2 --- Texas Benefits Eligibility Checks | Cx: 25 | P0

**Description:**
Create `backend/app/modules/benefits/texas/eligibility_checks.py` with TX program check functions: SNAP (same federal rules), TANF (TX amounts), Medicaid (TX has not expanded either), CHIP (replaces ALL_Kids), Childcare Subsidy (TWC-managed), Section 8 (Fort Worth Housing Solutions AMI), CEAP (replaces LIHEAP). Export TX `PROGRAM_CHECKS` dict.

**AC:**
- [ ] 7 TX program check functions implemented
- [ ] CHIP replaces ALL_Kids with TX-specific thresholds
- [ ] CEAP replaces LIHEAP with TX-specific thresholds
- [ ] `PROGRAM_CHECKS` dict exported
- [ ] Tests written and passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.1

---

### T2.3 --- Texas Application Data | Cx: 15 | P0

**Description:**
Create `backend/app/modules/benefits/texas/application_data.py` with Fort Worth/Tarrant County office addresses, phone numbers, and URLs for all 7 TX programs. HHSC at yourtexasbenefits.com, Tarrant County HHSC, Workforce Solutions, Fort Worth Housing Solutions.

**AC:**
- [ ] All 7 TX programs have application data
- [ ] All addresses, phones, URLs are real Fort Worth/Tarrant County offices
- [ ] `get_application_info()` function exported
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.4 --- Texas Benefits Types + Program Calculators | Cx: 25 | P0

**Description:**
Create `backend/app/modules/benefits/texas/program_calculators.py` using TX thresholds. Create `backend/app/modules/benefits/texas/types.py` with TX-specific VALID_PROGRAMS (replacing ALL_Kids with CHIP, LIHEAP with CEAP). Wire up the calculator dispatch map.

**AC:**
- [ ] TX program calculators for all 7 programs
- [ ] TX VALID_PROGRAMS with CHIP and CEAP
- [ ] Calculator dispatch map matches TX program names
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.1

---

### T2.5 --- Benefits Module Router | Cx: 25 | P0

**Description:**
Create `backend/app/modules/benefits/router.py` that selects AL or TX modules based on `CITY` env var. Factory functions: `get_thresholds()`, `get_program_checks()`, `get_application_data()`, `get_program_calculators()`, `get_valid_programs()`, `get_screener_disclaimer()`. Update `eligibility_screener.py`, `cliff_calculator.py`, and `program_calculators.py` to use router instead of direct AL imports.

**AC:**
- [ ] Router selects correct state module based on city config
- [ ] `CITY=montgomery` loads AL modules (backward compatible)
- [ ] `CITY=fort-worth` loads TX modules
- [ ] Existing AL tests still pass
- [ ] New TX routing tests pass
- [ ] `bpsai-pair arch check` passes on all modified files

**Depends on:** T2.2, T2.4

---

### T2.6 --- Texas Expunction + Nondisclosure Rules | Cx: 25 | P0

**Description:**
Create `backend/app/modules/criminal/texas_expunction.py` implementing TX expunction (Art. 55) and nondisclosure (Gov Code Ch. 411 E-1). Two mechanisms: full expunction for arrests without conviction / pardons / acquittals, and nondisclosure for deferred adjudication. Different wait periods, $280 filing fee, Legal Aid of NorthWest Texas contact info.

**AC:**
- [ ] Expunction eligibility check implemented
- [ ] Nondisclosure eligibility check implemented
- [ ] Correct wait periods per charge level
- [ ] Legal Aid of NorthWest Texas contact info (817-336-3943)
- [ ] Tests passing for both mechanisms
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.7 --- Criminal Module Router | Cx: 15 | P0

**Description:**
Create `backend/app/modules/criminal/router.py` that selects AL expungement or TX expunction/nondisclosure based on city config state. Update `barrier_cards.py` to use router.

**AC:**
- [ ] Router selects correct state's record clearing rules
- [ ] AL expungement still works when CITY=montgomery
- [ ] TX expunction/nondisclosure works when CITY=fort-worth
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6

---

## Phase 2: Fort Worth Geo + Transit Data (parallel after Phase 1 core)

### T2.8 --- Fort Worth ZIP Centroids + Geo Data | Cx: 15 | P0

**Description:**
Create `backend/app/modules/matching/fort_worth_geo.py` with Fort Worth ZIP centroids (76101-76199 range), downtown coordinates, Trinity Metro schedule hours. Create geo router in `backend/app/modules/matching/geo_router.py` that selects Montgomery or Fort Worth geo data based on city config.

**AC:**
- [ ] Fort Worth ZIP centroids for major ZIPs (76101-76140 range)
- [ ] DOWNTOWN_FORT_WORTH coordinates
- [ ] Trinity Metro hours (5am-10:30pm weekdays)
- [ ] Geo router selects correct city data
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.9 --- City-Aware ZIP Validation | Cx: 15 | P0

**Description:**
Update `AssessmentRequest.zip_code` validation in `backend/app/modules/matching/types.py` to accept both 361xx and 761xx ZIPs dynamically based on city config. Create a validator function that checks against the active city's zip_ranges. Update frontend `constants.ts` to support both cities.

**AC:**
- [ ] Backend accepts 761xx ZIPs when CITY=fort-worth
- [ ] Backend still accepts 361xx ZIPs when CITY=montgomery
- [ ] Frontend ZIP validation is city-aware
- [ ] Tests passing for both cities
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.10 --- Fort Worth Barrier Cards + Career Center | Cx: 20 | P0

**Description:**
Create `backend/app/modules/matching/fort_worth_resources.py` with Fort Worth barrier actions (Trinity Metro, HHSC, TX Pre-K/Head Start, Fort Worth Housing Solutions), career center info (Workforce Solutions Tarrant County), resource affinity keywords, and certification bodies (TX Board of Nursing, TX DPS, Tarrant County College). Create router to select city resources.

**AC:**
- [ ] Fort Worth barrier actions for all 7 barrier types
- [ ] Workforce Solutions Tarrant County career center info
- [ ] TX certification bodies (Board of Nursing, DPS)
- [ ] Resource affinity keywords for FW resources
- [ ] City-aware routing for barrier cards
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 3: API Adapters + AI (parallel)

### T2.11 --- Live TWC Job Adapter | Cx: 30 | P1

**Description:**
Replace TWC stub in `backend/app/integrations/adapters/twc_adapter.py` with a real adapter that searches the Texas Workforce Commission job board. Use httpx async client, parse response into standard job dict format, handle pagination, rate limiting, and errors gracefully. Degrade to empty list if API unavailable.

**AC:**
- [ ] TWC adapter fetches real jobs from TWC API
- [ ] Results normalized to standard job dict format
- [ ] Graceful degradation on API failure
- [ ] Rate limiting respected
- [ ] Tests with mocked HTTP responses
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.12 --- Live USAJobs Adapter | Cx: 30 | P1

**Description:**
Replace USAJobs stub in `backend/app/integrations/adapters/usajobs_adapter.py` with real adapter hitting `https://data.usajobs.gov/api/search`. Requires API key via env var. Parse USAJobs JSON response into standard job dict. Handle auth, pagination, and graceful degradation.

**AC:**
- [ ] USAJobs adapter fetches real federal jobs
- [ ] API key configured via USAJOBS_API_KEY env var
- [ ] Results normalized to standard job dict format
- [ ] Graceful degradation when API key missing or API down
- [ ] Tests with mocked HTTP responses
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.13 --- City-Aware AI Prompts | Cx: 15 | P1

**Description:**
Update `backend/app/ai/prompts.py` to be city-aware. Create prompt templates for Fort Worth (Trinity Metro, Workforce Solutions Tarrant County, JPS Health Network, Lockheed Martin, Bell Textron, BNSF Railway, NAS JRB, Texas Health Resources, Cook Children's). Use city config to select correct prompt.

**AC:**
- [ ] Fort Worth system prompt with local context
- [ ] Fort Worth user prompt template
- [ ] Prompt router selects by city config
- [ ] Montgomery prompts unchanged
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 4: Frontend + Seed Data

### T2.14 --- Frontend City-Aware Constants | Cx: 20 | P1

**Description:**
Update frontend to be city-aware: create city config API endpoint, update `constants.ts` with Fort Worth career center + ZIP regex + program labels (CHIP/CEAP), update `findhelp.ts` for Fort Worth, update `useDemoMode.ts` with FW demo data, update `TimelinePhaseCard.tsx` with TX benefit URLs.

**AC:**
- [ ] Frontend constants support Fort Worth
- [ ] ZIP validation works for both cities
- [ ] Benefit URLs point to TX sites when in FW mode
- [ ] Career center info shows Workforce Solutions when in FW mode
- [ ] Demo mode uses FW ZIP when CITY=fort-worth
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.15 --- Frontend City-Aware UI Text | Cx: 15 | P1

**Description:**
Update `assess/page.tsx`, `page.tsx` (home), `layout.tsx`, `MondayMorning.tsx` to use city-aware text. Replace hardcoded "Montgomery, Alabama" with dynamic city name from API/config.

**AC:**
- [ ] Assessment page shows correct city name
- [ ] Home page shows correct city name
- [ ] Layout metadata is city-aware
- [ ] Monday Morning component shows correct city
- [ ] Tests passing

**Depends on:** T2.14

---

### T2.16 --- Fort Worth Seed Data | Cx: 20 | P2

**Description:**
Create `data/cities/fort-worth/` with seed JSON files: community resources, employer policies (fair-chance employers), career centers. Include real Fort Worth organizations: Workforce Solutions, Legal Aid of NW Texas, Tarrant County United Way 211, Catholic Charities Fort Worth, ACH Child and Family Services.

**AC:**
- [ ] `data/cities/fort-worth/resources.json` with community resources
- [ ] `data/cities/fort-worth/employers.json` with fair-chance employers
- [ ] All organizations are real Fort Worth entities
- [ ] Data loads correctly
- [ ] Tests passing

**Depends on:** none

---

### T2.17 --- Fair-Chance Employer Index | Cx: 15 | P2

**Description:**
Create `backend/app/modules/criminal/fair_chance_index.py` with a registry of Fort Worth fair-chance employers (Ban the Box, second chance employers). Include major FW employers known for fair-chance hiring. Create city-aware employer seed loader.

**AC:**
- [ ] Fair-chance employer registry for Fort Worth
- [ ] City-aware employer loading
- [ ] Tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.18 --- Integration Gate | Cx: 10 | P2

**Description:**
End-to-end test that sets `CITY=fort-worth` and runs a full assessment through the pipeline: ZIP validation, benefits screening, expunction check, job matching, barrier cards, career center package. Verify all Texas-specific content appears.

**AC:**
- [ ] E2E test with CITY=fort-worth passes
- [ ] TX benefits programs returned (CHIP, CEAP)
- [ ] TX expunction/nondisclosure rules applied
- [ ] FW career center info in package
- [ ] All backend tests pass (zero regressions)

**Depends on:** T2.5, T2.7, T2.8, T2.9, T2.10

---

## Delivery Summary

| Phase | Tasks | Cx | Priority |
|-------|-------|----|----------|
| Phase 1: Module Routing | T2.1-T2.7 | 150 | P0 |
| Phase 2: Geo + Transit | T2.8-T2.10 | 50 | P0 |
| Phase 3: API + AI | T2.11-T2.13 | 75 | P1 |
| Phase 4: Frontend + Seed | T2.14-T2.18 | 80 | P1-P2 |
| **Total** | **18** | **355** | |

## Priority Order (engage cut-list)

1. T2.1 (TX thresholds) - foundation
2. T2.3 (TX application data) - no deps
3. T2.6 (TX expunction) - no deps
4. T2.8 (FW geo) - no deps
5. T2.9 (ZIP validation) - no deps
6. T2.10 (FW barrier cards) - no deps
7. T2.2 (TX eligibility checks) - needs T2.1
8. T2.4 (TX calculators) - needs T2.1
9. T2.5 (benefits router) - needs T2.2, T2.4
10. T2.7 (criminal router) - needs T2.6
11. T2.11 (TWC live) - independent
12. T2.12 (USAJobs live) - independent
13. T2.13 (AI prompts) - independent
14. T2.14 (FE constants) - independent
15. T2.15 (FE text) - needs T2.14
16. T2.16 (seed data) - independent
17. T2.17 (fair-chance) - independent
18. T2.18 (integration gate) - needs Phase 1+2

## Dependency Graph

```
Wave 1 (parallel): T2.1, T2.3, T2.6, T2.8, T2.9, T2.10, T2.11, T2.12, T2.13, T2.14, T2.16, T2.17
Wave 2 (after T2.1): T2.2, T2.4
Wave 3 (after T2.2+T2.4): T2.5
Wave 4 (after T2.6): T2.7
Wave 5 (after T2.14): T2.15
Wave 6 (after Phase 1+2): T2.18
```

## File Collision Matrix

| File | Tasks |
|------|-------|
| benefits/texas/* (new) | T2.1, T2.2, T2.3, T2.4 |
| benefits/router.py (new) | T2.5 |
| criminal/texas_expunction.py (new) | T2.6 |
| criminal/router.py (new) | T2.7 |
| matching/fort_worth_geo.py (new) | T2.8 |
| matching/types.py | T2.9 |
| matching/fort_worth_resources.py (new) | T2.10 |
| integrations/adapters/twc_adapter.py | T2.11 |
| integrations/adapters/usajobs_adapter.py | T2.12 |
| ai/prompts.py | T2.13 |
| frontend constants.ts | T2.14 |

## Sprint Budget

- Cx budget: 355
- Task count: 18
- P0 cut line: T2.1-T2.10 (200 Cx, 10 tasks)
- P1 cut line: T2.11-T2.15 (110 Cx, 5 tasks)
- P2 stretch: T2.16-T2.18 (45 Cx, 3 tasks)

## Integration Points

- T2.5 (benefits router) must not break existing AL tests
- T2.7 (criminal router) must not break existing expungement tests
- T2.9 (ZIP validation) touches shared types.py - careful with regex
- T2.13 (AI prompts) must preserve existing prompt structure

## Out of Scope

- Trinity Metro GTFS data ingestion (complex, deferred to S3)
- Modifying any Alabama-specific files (create parallel TX files)
- Fort Worth Open Data Portal integration
- 211 Texas API integration
- Real employer verification/scraping
