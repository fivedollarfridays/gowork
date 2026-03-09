# WorkPath Full Pipeline — Implementation Backlog

> Research document for `/pc-plan`. Covers benefits cliff integration, job board
> aggregation, resource matching, criminal record routing, transit access, and
> personalized action plan generation.
>
> **Goal:** Connect credit assessment API with all external data sources into a
> unified workforce readiness platform. WorkPath is the first platform that maps
> credit, criminal record, transit access, benefits risk, and resource eligibility
> simultaneously — and turns that into a personalized action plan.

---

## Current State (What's Built)

MontGoWork already has a sophisticated matching engine (449 backend / 141 frontend
tests). The following capabilities are **production-ready**:

| Capability | Module | Status |
|-----------|--------|--------|
| Multi-barrier assessment (7 types) | `modules/matching/engine.py` | Done |
| 5-factor resource scoring + affinity | `modules/matching/scoring.py` | Done |
| Job matching with credit/transit filters | `modules/matching/job_matcher.py` | Done |
| Practical Value Score (earnings/proximity/time) | `modules/matching/salary_parser.py`, `proximity_scorer.py`, `time_fit_scorer.py` | Sprint 24 (T24.1-T24.3 done, T24.4-T24.6 pending) |
| Credit assessment proxy | `routes/credit.py` → `credit-api.montgowork.com` | Done, live |
| BrightData job crawling | `integrations/brightdata/` | Done |
| WIOA eligibility screening | `modules/matching/wioa_screener.py` | Done |
| Barrier Intelligence chat (RAG + SSE) | `barrier_intel/` | Done |
| Career Center Ready Package | `modules/matching/career_center_package.py` | Done |
| Transit routes + stops (MATS) | `data/transit_routes.json`, `transit_stops.json` | Done (14 routes, 44 stops) |
| Feedback loop + resource health decay | `modules/feedback/` | Done |

### What's NOT Built Yet

| Gap | Impact | Priority |
|-----|--------|----------|
| Benefits cliff calculator | Users can't see opportunity cost of taking a job | **P0 — differentiator** |
| Job board aggregation beyond BrightData | Missing Indeed/LinkedIn/Glassdoor real-time, Honest Jobs fair-chance | **P0 — coverage** |
| Criminal record routing | No charge-type → job eligibility mapping | **P0 — core promise** |
| Resource auto-matching (findhelp.org) | Users browse 602 Montgomery programs manually | **P1 — depth** |
| Transit real-time / schedule matching | Static schedule data, no live arrival times | **P2 — polish** |
| Benefits program eligibility engine | No SNAP/TANF/Medicaid threshold checking | **P1 — cliff context** |

---

## Pipeline Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              User Assessment                 │
                    │  barriers, credit, criminal, schedule, zip   │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │           Enrichment Layer (NEW)             │
                    │                                              │
                    │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
                    │  │ Benefits │ │ Criminal │ │  Resource    │ │
                    │  │  Cliff   │ │  Record  │ │  Eligibility│ │
                    │  │Calculator│ │  Router  │ │  Matcher    │ │
                    │  └────┬─────┘ └────┬─────┘ └──────┬──────┘ │
                    │       │            │              │         │
                    └───────┼────────────┼──────────────┼─────────┘
                            │            │              │
                    ┌───────▼────────────▼──────────────▼─────────┐
                    │           Matching Engine (EXISTING)         │
                    │  5-factor scoring + PVS + affinity routing   │
                    │                                              │
                    │  + NEW: cliff-aware job ranking              │
                    │  + NEW: record-filtered job matching         │
                    │  + NEW: auto-matched programs                │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │         Job Aggregation Layer (NEW)          │
                    │                                              │
                    │  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
                    │  │BrightData│ │  JSearch  │ │ Honest Jobs │ │
                    │  │(existing)│ │   API     │ │  Fair-Chance│ │
                    │  └──────────┘ └──────────┘ └─────────────┘ │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │          Personalized Action Plan            │
                    │                                              │
                    │  • Jobs ranked by net income (wages - cliff) │
                    │  • Criminal record compatibility per job     │
                    │  • Benefits transition timeline              │
                    │  • Matched programs (auto, not manual)       │
                    │  • Credit repair pathway (existing)          │
                    │  • Transit-aware scheduling (existing)       │
                    └─────────────────────────────────────────────┘
```

---

## Sprint Breakdown

### Sprint 25: Benefits Cliff Engine (P0, HIGH IMPACT)

**Why first:** This is WorkPath's killer differentiator. Nobody else shows
"taking this $15/hr job costs you $400/month in benefits." The Atlanta Fed
built DAVID for Alabama — we integrate the same logic.

#### T25.1 — Benefits Cliff Calculator Module
**Complexity: 60** | **Priority: P0**

Create `backend/app/modules/benefits/cliff_calculator.py`:

**Input:** household size, current income, state (AL), programs enrolled
**Output:** cliff analysis per wage level ($8-$25/hr in $0.50 steps)

Programs to model (Alabama-specific thresholds):
- **SNAP** (Food Stamps): 130% FPL gross, 100% FPL net
- **TANF**: $215/month max (family of 3), 60-month lifetime
- **Medicaid** (adult): 138% FPL (expansion state: NO — Alabama didn't expand)
  - ALL Kids (children): 317% FPL
- **Childcare subsidy** (DHR): 85% SMI, copay scale
- **Section 8 / Housing**: 50% AMI, 30% income toward rent
- **LIHEAP**: 150% FPL

Federal Poverty Level 2026 (estimated):
- 1 person: ~$15,600
- 2 person: ~$21,200
- 3 person: ~$26,700
- 4 person: ~$32,300

**Key formula:**
```
net_income(wage) = gross_income(wage)
                 - taxes(wage)
                 + snap_benefit(wage, household)
                 + tanf_benefit(wage, household)
                 + medicaid_value(wage, household)
                 + childcare_subsidy(wage, household)
                 + housing_subsidy(wage, household)
```

A cliff exists where `net_income(wage + $0.50) < net_income(wage)`.

**Data sources:**
- [BenefitsCliffs.org API](https://benefitscliffs.org/api) — has an API with
  [developer docs](https://docs.benefitscliffs.org), models income/family/geography
- [Atlanta Fed CLIFF](https://www.atlantafed.org/economic-mobility-and-resilience/advancing-careers-for-low-income-families/cliff-tool) — contact cliff@atl.frb.org for tool access
- Static Alabama threshold tables as fallback

**Acceptance Criteria:**
- [ ] Calculate net income at each wage step for a given household profile
- [ ] Identify cliff points where net income drops
- [ ] Return cliff severity (mild: <$50/mo loss, moderate: $50-200, severe: >$200)
- [ ] Alabama-specific thresholds hardcoded (no external API required for MVP)
- [ ] Tests for each program's phase-out curve
- [ ] Tests for combined cliff scenarios

#### T25.2 — Benefits Profile in Assessment Wizard
**Complexity: 40** | **Priority: P0**

Add step to assessment wizard (after barriers, before credit):

**New fields in `UserProfile`:**
- `household_size: int` (1-8)
- `current_monthly_income: float`
- `enrolled_programs: list[str]` — checkboxes: SNAP, TANF, Medicaid, ALL Kids,
  Childcare Subsidy, Section 8, LIHEAP, None
- `dependents_under_6: int` (for childcare cliff)
- `dependents_6_to_17: int`

**Frontend:** New wizard step with household info form.
**Backend:** Store in session profile, pass to cliff calculator.

**Acceptance Criteria:**
- [ ] New wizard step renders between Barriers and Credit
- [ ] Fields validate (household_size >= 1, income >= 0)
- [ ] Profile stored in session
- [ ] Step is skippable (defaults to household=1, income=0, programs=[])
- [ ] Frontend + backend tests

#### T25.3 — Cliff-Aware Job Ranking
**Complexity: 50** | **Priority: P0**

Modify PVS scoring to include benefits cliff impact:

**New PVS factor: Net Income (replaces raw Earnings)**

Current:
```
Earnings weight: 35% → annual_salary / 40000
```

New:
```
Net Income weight: 35% → net_income(job_wage) / net_income(current_income)
```

Where `net_income()` includes wages + remaining benefits - lost benefits.

A job paying $15/hr that causes a $400/month cliff is worse than a job
paying $13/hr that keeps all benefits intact.

**Display:** Each job card shows:
- Gross wage: "$15.00/hr ($31,200/yr)"
- Benefits impact: "⚠ -$400/month in benefits" or "✓ No benefits impact"
- Net change: "+$200/month" or "-$50/month vs current"

**Acceptance Criteria:**
- [ ] PVS uses net income (wages + benefits) not gross wages
- [ ] Jobs sorted by actual financial improvement
- [ ] Job cards show benefits impact badge
- [ ] Cliff warnings in red, safe in green
- [ ] Tests with cliff and no-cliff scenarios

#### T25.4 — Benefits Cliff Visualization
**Complexity: 35** | **Priority: P1**

Add cliff chart to plan page (after job matches, before barrier cards):

**Chart:** Line graph showing net income (y-axis) vs hourly wage (x-axis, $8-$25).
- Green line: total net income (wages + benefits)
- Red zones: cliff drop-offs
- Markers: current income, each matched job's wage
- Tooltip on markers: "This job at $15/hr → net $2,100/mo (you currently net $2,300/mo)"

Use a lightweight charting lib (recharts is already common in Next.js).

**Acceptance Criteria:**
- [ ] Chart renders with user's cliff data
- [ ] Jobs plotted as markers on the curve
- [ ] Red shading on cliff zones
- [ ] Responsive (mobile-friendly)
- [ ] Accessible (screen reader labels)
- [ ] Tests for chart data transformation

---

### Sprint 26: Criminal Record Routing (P0)

**Why:** WorkPath promises to map criminal records to job eligibility. Currently
the barrier assessment has a "criminal_record" checkbox but no charge-level routing.

#### T26.1 — Criminal Record Profile
**Complexity: 45** | **Priority: P0**

Expand criminal record barrier from boolean to structured:

**New fields in `UserProfile`:**
- `record_type: list[str]` — felony, misdemeanor, arrest_only, expunged
- `charge_categories: list[str]` — violence, theft, drug, dui, sex_offense, fraud, other
- `years_since_conviction: int`
- `completed_sentence: bool` (probation/parole complete)

**Assessment wizard:** New conditional sub-step when criminal_record barrier selected.
Sensitive UX — reassuring language, explain why we ask, data never shared.

**Acceptance Criteria:**
- [ ] Conditional form appears only when criminal_record barrier selected
- [ ] Privacy notice displayed prominently
- [ ] Data stored in session profile only (no PII in DB beyond session)
- [ ] Fields are all optional (graceful defaults)
- [ ] Frontend + backend tests

#### T26.2 — Fair-Chance Employer Database
**Complexity: 50** | **Priority: P0**

Create `backend/app/modules/criminal/employer_policy.py`:

**Employer policy data (Alabama-specific):**
- Ban-the-box status: Alabama has NO statewide ban-the-box law
- Montgomery: NO city ban-the-box ordinance
- Federal contractors: Fair Chance Act (2020) delays background checks
- Individual employer policies (known fair-chance employers in Montgomery)

**Data model:**
```python
class EmployerPolicy:
    employer_name: str
    fair_chance: bool  # explicitly fair-chance
    excluded_charges: list[str]  # charges they won't hire for
    lookback_years: int  # how far back they check (7 typical)
    background_check_timing: str  # "pre-offer" | "post-offer" | "none"
    industry: str
    source: str  # "self-reported" | "verified" | "inferred"
```

**Seed data sources:**
- [Honest Jobs employer directory](https://www.honestjobs.com/for-employers) (1000+ fair-chance employers)
- [Jails to Jobs Second Chance Network](https://jailstojobs.org/resources/second-chance-employers-network/)
- Alabama-specific: MPACT partner employers, DHR partner employers
- Montgomery businesses with known hire-with-record policies

**Acceptance Criteria:**
- [ ] Employer policy table in database
- [ ] Seed data for Montgomery fair-chance employers (minimum 20)
- [ ] Query: given charge categories + years, return eligible employers
- [ ] Lookback window filtering (7-year, 10-year)
- [ ] Tests for each charge category filter

#### T26.3 — Record-Filtered Job Matching
**Complexity: 45** | **Priority: P0**

Integrate criminal record into job matching pipeline:

**Logic in `job_matcher.py`:**
1. If user has record → check each job's employer against policy DB
2. If employer is fair-chance → boost relevance score
3. If employer excludes user's charge category → move to "after_repair" bucket
4. If years_since_conviction > employer's lookback → treat as eligible
5. If charge is expunged → treat as no record

**Job card display:**
- "✓ Fair-Chance Employer" badge (green)
- "Background check: post-offer" info
- "Your record: eligible after [X] more years" if lookback applies

**Acceptance Criteria:**
- [ ] Jobs filtered by record compatibility
- [ ] Fair-chance badge on eligible jobs
- [ ] Lookback window calculation correct
- [ ] Expunged records treated as clean
- [ ] No PII leakage in job card display
- [ ] Tests for each filter path

#### T26.4 — Expungement / Clean Slate Pathway
**Complexity: 35** | **Priority: P1**

Add expungement eligibility check to plan:

**Alabama expungement law (Act 2021-507):**
- Nonviolent felonies: eligible after 5 years, all fines paid
- Misdemeanors: eligible after 3 years (some immediately)
- Certain charges never expungeable (Class A felonies, sex offenses)
- Filing fee: $300 (waivable for indigent)

**Output in plan:**
- "You may be eligible for expungement in [X] years"
- Link to Legal Services Alabama (already in resources)
- Estimated timeline + steps

**Acceptance Criteria:**
- [ ] Expungement eligibility calculated from charge type + years
- [ ] Timeline and steps displayed in plan
- [ ] Link to Legal Services Alabama resource
- [ ] Tests for eligible, not-yet-eligible, and never-eligible scenarios

---

### Sprint 27: Job Board Aggregation (P0)

**Why:** BrightData crawls are triggered manually and cached. For judges and
real users, we need real-time job results from multiple sources.

#### T27.0 — BrightData Pre-Built Jobs Dataset Integration
**Complexity: 30** | **Priority: P0** | **HACKATHON PRIORITY — free credits via sponsor**

Ingest BrightData's pre-built Jobs Dataset (40M+ records, JSON/CSV) to populate
Montgomery-area job listings with real salary data. This is the fastest path to
fixing our "all jobs at 25% score" problem — seed data has no pay info, so PVS
scoring can't differentiate.

**Products available (free hackathon credits):**
- **Pre-built Jobs Dataset** — ready-made JSON/CSV, $2.50/1K records. Includes
  title, company, location, salary range, description, apply URL, employment type.
- **Jobs Scraper API** — automated extraction from Indeed, LinkedIn, Glassdoor.
- **Indeed Jobs Scraper** — entry-level/hourly job focus, strong Montgomery coverage.
- **LinkedIn Jobs Scraper** — 40M+ listings, skews white-collar.

**MVP approach (T27.0):**
1. Download pre-built dataset filtered to Montgomery, AL area (36xxx zips)
2. Normalize to existing `JobListing` schema
3. Store in `aggregated_jobs` table with `source: "brightdata"`
4. Feed into PVS scorer — salary data enables real score differentiation

**Files to create/modify:**
- `backend/app/integrations/brightdata/dataset_loader.py` (NEW) — parse + normalize
  BrightData JSON/CSV into JobListing schema
- `backend/app/integrations/brightdata/models.py` (NEW) — BrightData record schema
- `backend/tests/integrations/brightdata/test_dataset_loader.py` (NEW)
- `backend/data/brightdata/` — downloaded dataset files

**Env vars:** `BRIGHTDATA_API_TOKEN` (for Scraper API, optional for pre-built)

**Acceptance Criteria:**
- [ ] Download and parse BrightData pre-built jobs dataset (Montgomery, AL)
- [ ] Normalize records to JobListing schema (title, company, location, salary, URL)
- [ ] Salary data extracted and available for PVS scoring
- [ ] Store in aggregated_jobs table with source attribution
- [ ] Dedup against existing seed data by (title, company) fuzzy match
- [ ] Tests with sample BrightData JSON fixture

---

#### T27.1 — JSearch API Integration
**Complexity: 40** | **Priority: P0**

Create `backend/app/integrations/jsearch/client.py`:

**API:** [JSearch on RapidAPI](https://www.openwebninja.com/api/jsearch)
- **Free tier:** 200 requests/month (enough for demo)
- **Endpoint:** `GET /search` with query, location, radius
- **Returns:** title, company, location, salary, description, apply link, employment type
- **500 results per query**

**Integration:**
```python
class JSearchClient:
    async def search_jobs(
        self,
        query: str = "jobs",
        location: str = "Montgomery, AL",
        radius: int = 25,  # miles
        page: int = 1,
    ) -> list[JobListing]:
        ...
```

**Normalization:** Map JSearch fields to existing `JobListing` schema.
**Caching:** Cache results in SQLite (same as BrightData pattern), 24hr TTL.
**Fallback:** If API unavailable, use cached + BrightData results.

**Env vars:** `JSEARCH_API_KEY`, `JSEARCH_HOST` (RapidAPI)

**Acceptance Criteria:**
- [ ] JSearch client with search endpoint
- [ ] Results normalized to JobListing schema
- [ ] 24hr cache in SQLite
- [ ] Graceful fallback to cached data
- [ ] Rate limit tracking (200/month)
- [ ] Tests with mocked API responses

#### T27.2 — Honest Jobs Fair-Chance Feed
**Complexity: 35** | **Priority: P0**

Create `backend/app/integrations/honestjobs/client.py`:

**Integration path:** Honest Jobs doesn't have a public API but:
1. Their job listings are on their website at `honestjobs.com/jobs`
2. They integrate with ATS providers (email employers@honestjobs.com)
3. **Acquired by Orijin in 2026** — integration may change

**MVP approach:**
- Curated seed data: scrape/maintain a list of Montgomery-area fair-chance
  postings from Honest Jobs (manual for hackathon, automated later)
- Tag all Honest Jobs listings with `fair_chance: true`
- Display "via Honest Jobs" badge on job cards

**Future:** BrightData can crawl Honest Jobs pages. Or contact Orijin for API access.

**Acceptance Criteria:**
- [ ] Honest Jobs seed data (minimum 10 Montgomery-area listings)
- [ ] `fair_chance` flag in JobListing schema
- [ ] "Via Honest Jobs" source badge on job cards
- [ ] Tests for fair-chance job display

#### T27.3 — Unified Job Aggregator
**Complexity: 40** | **Priority: P0**

Create `backend/app/integrations/job_aggregator.py`:

Merge results from all sources with deduplication:

```python
class JobAggregator:
    async def search(
        self,
        query: str,
        location: str,
        barriers: list[str],
        record: RecordProfile | None,
    ) -> list[JobListing]:
        # 1. Query all sources in parallel
        brightdata_jobs = await self.brightdata.get_cached()
        jsearch_jobs = await self.jsearch.search(query, location)
        honestjobs = await self.honestjobs.get_listings(location)

        # 2. Deduplicate by (title, company, location) fuzzy match
        # 3. Merge metadata (fair_chance from Honest Jobs, salary from JSearch)
        # 4. Apply criminal record filter
        # 5. Return unified list
```

**Dedup strategy:** Normalize company names, fuzzy match titles (>85% similarity),
prefer the listing with more data (salary > no salary).

**Acceptance Criteria:**
- [ ] Parallel fetch from all sources
- [ ] Deduplication with fuzzy matching
- [ ] Source attribution preserved ("via Indeed", "via Honest Jobs")
- [ ] Criminal record filter applied
- [ ] Tests for dedup edge cases

#### T27.4 — Job Search Filters (Frontend)
**Complexity: 30** | **Priority: P1**

Add filter bar to plan page job section:

- **Source:** All, Indeed, LinkedIn, Honest Jobs, BrightData
- **Fair-chance only:** Toggle
- **Pay range:** Min/max sliders
- **Distance:** 5mi / 10mi / 25mi / 50mi
- **Schedule:** Full-time / Part-time / Flexible
- **Sort by:** Net income (cliff-aware) / Distance / Relevance

Filters apply client-side on cached results (no additional API calls).

**Acceptance Criteria:**
- [ ] Filter bar renders above job list
- [ ] Each filter updates results immediately
- [ ] Active filters shown as pills/badges
- [ ] Clear all button
- [ ] Tests for each filter

---

### Sprint 28: Resource Auto-Matching (P1)

**Why:** findhelp.org has 602 Montgomery programs but users browse manually.
WorkPath should auto-match based on the user's barrier profile.

#### T28.1 — findhelp.org Integration
**Complexity: 45** | **Priority: P1**

**Integration options (ranked by feasibility):**

1. **Capability URL embed (fastest):** findhelp supports specially-formatted URLs
   that launch into filtered program search. Generate per-user URLs:
   ```
   https://www.findhelp.org/money/financial-assistance--montgomery-al?postal=36101
   ```
   Embed as "See more programs on findhelp.org" links per barrier category.

2. **Programs API (requires partnership):** findhelp has a Programs API used by
   health systems (Single Stop integration exists). Contact findhelp for API access.
   Would allow: search programs by zip + category, get eligibility criteria, display
   inline without redirect.

3. **Scrape + cache (backup):** Cache findhelp program data for Montgomery zip codes.
   Category mapping: childcare → "Child Care", credit → "Financial Assistance",
   housing → "Housing & Shelter", etc.

**MVP (T28.1):** Capability URL generation per barrier category.
**V2 (T28.3):** Full API integration if partnership secured.

**Acceptance Criteria:**
- [ ] Generate findhelp URLs per barrier category + user zip code
- [ ] Display "More programs available" link per barrier card
- [ ] Links open in new tab with correct category filter
- [ ] Category mapping covers all 7 barrier types
- [ ] Tests for URL generation

#### T28.2 — Resource Eligibility Engine
**Complexity: 50** | **Priority: P1**

Create `backend/app/modules/resources/eligibility.py`:

Currently resources are matched by barrier category + affinity score. Add
eligibility filtering based on user profile:

**Eligibility criteria per resource:**
- Income threshold (e.g., SNAP: 130% FPL)
- Age (e.g., Head Start: children 0-5)
- Residency (Montgomery County)
- Program-specific (e.g., WIOA: already implemented)
- Household composition

**Schema update:** Add `eligibility_criteria` JSON field to resources table:
```json
{
  "max_income_pct_fpl": 130,
  "min_age": null,
  "max_age": null,
  "residency": "montgomery_county",
  "requires": ["us_citizen_or_permanent_resident"],
  "household_min_size": null
}
```

**Matching:** Given user profile, filter resources where user meets ALL criteria.
Display "You likely qualify" vs "Check eligibility" badges.

**Acceptance Criteria:**
- [ ] Eligibility criteria schema defined
- [ ] Seed data updated with eligibility rules for existing resources
- [ ] Filtering logic matches user profile to criteria
- [ ] "Likely qualify" / "Check eligibility" badges
- [ ] Tests for each criterion type

#### T28.3 — findhelp.org Deep Integration (V2)
**Complexity: 60** | **Priority: P2** (dependent on API access)

If findhelp API access secured:
- Search 602 Montgomery programs by category + zip
- Display program details inline (name, address, phone, hours, eligibility)
- "Refer" button to open findhelp with pre-filled user info
- Cache program data locally (24hr TTL)

**Acceptance Criteria:**
- [ ] API client for findhelp Programs API
- [ ] Search by zip + category
- [ ] Results displayed inline in barrier cards
- [ ] Cache with TTL
- [ ] Graceful fallback to capability URLs

---

### Sprint 29: Benefits Program Eligibility (P1)

#### T29.1 — Program Eligibility Calculator
**Complexity: 55** | **Priority: P1**

Create `backend/app/modules/benefits/eligibility.py`:

Given user profile, determine which programs they qualify for:

| Program | Key Criteria (Alabama) |
|---------|----------------------|
| SNAP | Gross income ≤ 130% FPL, net ≤ 100% FPL, assets ≤ $2,750 |
| TANF | Income ≤ AL standard, children in home, 60-month limit |
| Medicaid (children) | ALL Kids: income ≤ 317% FPL |
| Medicaid (adults) | Alabama did NOT expand — very limited (pregnant, disabled, SSI) |
| Childcare subsidy | Income ≤ 85% SMI, working/in training |
| Section 8 | Income ≤ 50% AMI, waitlist (years) |
| LIHEAP | Income ≤ 150% FPL, seasonal |
| WIOA | Already implemented in `wioa_screener.py` |

**Output:**
```python
class ProgramEligibility:
    program: str
    eligible: bool
    confidence: str  # "likely" | "possible" | "unlikely"
    estimated_monthly_value: float
    application_steps: list[str]
    application_url: str | None
```

**Acceptance Criteria:**
- [ ] Eligibility check for each program
- [ ] Estimated monthly benefit value
- [ ] Application steps and URLs
- [ ] Confidence levels (likely/possible based on data completeness)
- [ ] Tests for each program

#### T29.2 — Benefits Dashboard in Plan
**Complexity: 35** | **Priority: P1**

Add benefits section to plan page showing:

1. **Currently enrolled:** Programs the user reported
2. **May also qualify for:** Programs they're eligible for but not enrolled
3. **Estimated total monthly value:** Sum of all program benefits
4. **Cliff warning:** "If you earn above $X/hr, you'll lose [program]"

**Acceptance Criteria:**
- [ ] Benefits section renders in plan
- [ ] Shows enrolled + additional eligible programs
- [ ] Monthly value estimates
- [ ] Cliff warnings per program
- [ ] Tests for display logic

---

### Sprint 30: Transit Enhancement (P2)

#### T30.1 — Transit Schedule-Aware Job Matching
**Complexity: 40** | **Priority: P2**

Current state: transit data exists (14 routes, 44 stops) but schedule matching
is basic. Enhance:

- **Shift start/end times** vs **first/last bus** on route
- **Transfer penalty:** Jobs requiring 2+ buses get lower transit score
- **Sunday exclusion:** MATS has NO Sunday service — flag Sunday-shift jobs
- **Walk distance:** Stop-to-workplace distance (currently neutral 0.5)

**Data needed:** Resource/employer coordinates. Currently many are 0,0.
Use geocoding (Google Maps Geocoding API or OpenCage free tier) to populate.

**Acceptance Criteria:**
- [ ] Shift time vs bus schedule validation
- [ ] Transfer penalty in scoring
- [ ] Sunday service gap flagged
- [ ] Walk distance calculated from stop to employer
- [ ] Geocoded coordinates for seed resources
- [ ] Tests for each scenario

#### T30.2 — Transit Route Visualization
**Complexity: 30** | **Priority: P2**

Add simple transit view to job card expansion:

- Show which bus route(s) serve the job location
- First/last bus times for user's shift
- Transfer info if applicable
- "Plan your trip" link to Google Maps directions (transit mode)

No map rendering needed — text + link is sufficient.

**Acceptance Criteria:**
- [ ] Route info displayed on job card
- [ ] First/last bus for shift times
- [ ] Google Maps transit link
- [ ] Tests for route matching

---

### Sprint 31: Action Plan Generation (P1)

#### T31.1 — Unified Action Plan with Timeline
**Complexity: 50** | **Priority: P1**

The crown jewel — a personalized timeline that connects all dimensions:

**Week 1-2: Immediate Actions**
- Apply to [top 3 cliff-safe jobs] (no benefits impact)
- Visit Montgomery Career Center (WIOA enrollment)
- Call GreenPath for credit counseling (if credit barrier)

**Month 1: Foundations**
- File dispute for [medical collection] (from credit assessment)
- Apply for [SNAP/childcare subsidy] (if eligible but not enrolled)
- Complete [training program] orientation (if training barrier)

**Month 2-3: Building**
- Start [specific training program] (MRWTC, Trenholm, etc.)
- Follow up on disputes (30-day response window)
- Re-assess credit score (track progress)

**Month 3-6: Advancement**
- Apply for [higher-paying jobs] (after cliff transition)
- Credit score target: [X] → eligible for [auto loan, apartment]
- Expungement filing (if eligible)

**Month 6-12: Stability**
- Transition off [program] at [wage level] (cliff-safe)
- Build emergency fund goal
- Long-term career pathway

**Implementation:** Extend the existing Claude narrative generation to include
timeline data from all modules (cliff calculator, credit assessment, criminal
record, WIOA, resource matching).

**Acceptance Criteria:**
- [ ] Timeline generated from all module outputs
- [ ] Actions are specific (not generic)
- [ ] Dates/weeks calculated from assessment date
- [ ] Credit repair steps from credit API integrated
- [ ] Benefits transition plan included
- [ ] Printable/exportable (existing PDF infrastructure)
- [ ] Tests for timeline generation logic

#### T31.2 — Progress Tracking (Stretch)
**Complexity: 45** | **Priority: P2**

Allow users to return and mark actions complete:

- Persistent user sessions (currently 24hr expiry)
- Checklist UI for action items
- Re-run assessment to see progress
- "Check-in" reminders via email (EmailJS)

**Acceptance Criteria:**
- [ ] Extended session persistence (30 days)
- [ ] Checklist state stored in DB
- [ ] Re-assessment comparison ("then vs now")
- [ ] Email check-in scheduling

---

## External API Summary

| API | Purpose | Auth | Cost | Rate Limit |
|-----|---------|------|------|------------|
| Credit Assessment | Credit score analysis | X-API-Key | Free (self-hosted) | 300/min |
| JSearch (RapidAPI) | Job aggregation (Indeed, LinkedIn, etc.) | RapidAPI key | Free: 200 req/mo, $25/mo: 10K | Per plan |
| BrightData | Job crawling | API key | Existing account | Per snapshot |
| Honest Jobs | Fair-chance job listings | None (seed data) | Free | N/A |
| findhelp.org | Resource/program search | Capability URLs (free) or API (partnership) | Free for URLs | N/A |
| BenefitsCliffs.org | Cliff calculations | API key (contact) | TBD | TBD |
| Anthropic Claude | AI narrative | API key | Per token | Existing |

---

## Data Model Additions

### New Tables

```sql
-- Benefits profile (per session)
CREATE TABLE benefits_profiles (
    id INTEGER PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    household_size INTEGER DEFAULT 1,
    current_monthly_income REAL DEFAULT 0,
    enrolled_programs TEXT DEFAULT '[]',  -- JSON array
    dependents_under_6 INTEGER DEFAULT 0,
    dependents_6_to_17 INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criminal record profile (per session, sensitive)
CREATE TABLE record_profiles (
    id INTEGER PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    record_types TEXT DEFAULT '[]',       -- JSON: ["felony", "misdemeanor"]
    charge_categories TEXT DEFAULT '[]',  -- JSON: ["theft", "drug"]
    years_since_conviction INTEGER,
    completed_sentence BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employer fair-chance policies
CREATE TABLE employer_policies (
    id INTEGER PRIMARY KEY,
    employer_name TEXT NOT NULL,
    fair_chance BOOLEAN DEFAULT FALSE,
    excluded_charges TEXT DEFAULT '[]',   -- JSON
    lookback_years INTEGER DEFAULT 7,
    background_check_timing TEXT,         -- "pre-offer" | "post-offer" | "none"
    industry TEXT,
    source TEXT,                          -- "verified" | "self-reported" | "inferred"
    montgomery_area BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cached job listings from aggregated sources
CREATE TABLE aggregated_jobs (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,                 -- "jsearch" | "brightdata" | "honestjobs"
    external_id TEXT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_type TEXT,                     -- "hourly" | "annual"
    apply_url TEXT,
    fair_chance BOOLEAN DEFAULT FALSE,
    employment_type TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

### Schema Updates

```sql
-- Add to sessions table
ALTER TABLE sessions ADD COLUMN benefits_profile TEXT;  -- JSON
ALTER TABLE sessions ADD COLUMN record_profile TEXT;     -- JSON

-- Add to resources table
ALTER TABLE resources ADD COLUMN eligibility_criteria TEXT;  -- JSON
```

---

### Bugfixes & Polish (Cross-Sprint)

These are gaps discovered during integration testing that don't belong to a
single sprint.

#### B1 — Wire `credit_readiness_score` into Plan Response
**Complexity: 10** | **Priority: P1**

The `ReEntryPlan.credit_readiness_score` field is always `None`. The credit
assessment result feeds into `job_readiness` factors but never populates the
top-level plan field. When the user submits a credit self-assessment, the plan
should reflect the computed score.

**Files to update:**
- `backend/app/modules/matching/engine.py` — populate `credit_readiness_score`
  from `credit_result` passed through the assessment
- `backend/tests/test_engine.py` — test with and without credit result

**Acceptance Criteria:**
- [ ] `credit_readiness_score` populated when credit result is provided
- [ ] Remains `None` when no credit assessment is done
- [ ] Frontend credit section renders correctly with the value
- [ ] Tests for both paths

#### B2 — Enrich `match_reason` with Resume Keywords and Target Industries
**Complexity: 20** | **Priority: P1**

Job card `match_reason` strings are generic ("Entry-level opportunity") and
don't reference the user's resume text or target industries. When a user
provides resume keywords or selects target industries, the match reason should
reflect why the job is relevant to *them*.

**Files to update:**
- `backend/app/modules/matching/pvs_scorer.py` — `_build_pvs_reason()` to
  accept resume keywords and target industries, generate specific reasons
- `backend/app/modules/matching/job_matcher.py` — pass resume/industry context
  to the scorer
- `backend/tests/test_pvs_scorer.py` — test enriched reasons

**Acceptance Criteria:**
- [ ] Match reason references matched industry (e.g., "Matches your target: manufacturing")
- [ ] Match reason references resume keywords (e.g., "Matches your forklift experience")
- [ ] Falls back to generic reason when no resume/industry data provided
- [ ] Tests for each reason path

---

## Execution Order

```
Sprint 25: Benefits Cliff Engine          ← P0, differentiator
  T25.1 → T25.2 → T25.3 → T25.4

Sprint 26: Criminal Record Routing        ← P0, core promise
  T26.1 → T26.2 → T26.3 → T26.4

Sprint 27: Job Board Aggregation          ← P0, coverage
  T27.0 (BrightData dataset) → T27.1 → T27.2 → T27.3 → T27.4

Sprint 28: Resource Auto-Matching         ← P1, depth
  T28.1 → T28.2 → T28.3

Sprint 29: Benefits Program Eligibility   ← P1, cliff context
  T29.1 → T29.2

Sprint 30: Transit Enhancement            ← P2, polish
  T30.1 → T30.2

Sprint 31: Action Plan Generation         ← P1, crown jewel
  T31.1 → T31.2
```

**Note:** Sprint 31 depends on Sprints 25-29 (needs data from all modules).
Sprints 25-27 can be parallelized. Sprint 28-29 can be parallelized.

---

## Competitive Positioning

| Dimension | Honest Jobs | AL Career Centers | findhelp.org | DAVID/CLIFF | **WorkPath** |
|-----------|-------------|-------------------|-------------|-------------|-------------|
| Credit assessment | - | - | - | - | **Full (dispute pathway, eligibility)** |
| Criminal record routing | Jobs only | - | - | - | **Charge-level → job matching** |
| Transit access | - | - | - | - | **MATS schedule-aware scoring** |
| Benefits cliff | - | - | - | Calculator only | **Cliff-aware job ranking** |
| Resource matching | - | In-person | Manual browse | Career paths | **Auto-matched to barriers** |
| Personalized plan | - | Generic | - | Career plan | **Timeline with all 5 dimensions** |
| Montgomery-specific | National | Yes | National | Alabama | **Montgomery-first** |

**WorkPath narrative for judges:**
> "Maria has a 520 credit score, a medical collection, gets SNAP and Medicaid,
> and has a misdemeanor from 6 years ago. WorkPath shows her that taking the
> $15/hr warehouse job would cost her $400/month in benefits — but the $13/hr
> fair-chance employer downtown keeps her benefits intact, is on her bus route,
> and her record is eligible. Net gain: +$800/month. Here's her 6-month plan
> to dispute the collection, complete WIOA training, and transition to
> self-sufficiency without falling off the cliff."
