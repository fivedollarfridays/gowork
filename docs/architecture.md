# MontGoWork Architecture

Technical architecture documentation for MontGoWork, a workforce navigator for Montgomery, Alabama.

---

## System Overview

MontGoWork is a full-stack application that helps Montgomery residents identify employment barriers and generate personalized re-entry plans. The system matches users with local resources and jobs using Practical Value Score (PVS) scoring, screens benefits eligibility with cliff detection, routes criminal records through fair-chance employer matching and expungement guidance, and provides AI-powered barrier intelligence chat via RAG-augmented LLM streaming.

```mermaid
graph TB
    subgraph Frontend ["Frontend (Next.js 15)"]
        UI[React UI / App Router]
    end

    subgraph Backend ["Backend (FastAPI)"]
        API[FastAPI Application]
        ME[Matching Engine]
        AI[AI Client]
        RAG[RAG / FAISS Store]
        BGraph[Barrier Graph]
    end

    subgraph Data ["Data Layer"]
        DB[(SQLite via aiosqlite)]
    end

    subgraph External ["External Services"]
        Claude[Claude API]
        OpenAI[OpenAI API]
        Gemini[Gemini API]
        Credit[Credit Microservice]
        BD[BrightData API]
        JSearch[JSearch API]
        HonestJobs[Honest Jobs]
    end

    UI -- "HTTP (JSON)" --> API
    API --> ME
    API --> AI
    API --> RAG
    API --> BGraph
    API --> DB
    API --> JSearch
    ME --> DB
    AI -- "Anthropic SDK" --> Claude
    AI --> OpenAI
    AI --> Gemini
    API -- "httpx proxy" --> Credit
    API -- "httpx async" --> BD
    BD -- "crawl results" --> DB
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js (App Router) | 15 |
| UI Library | React + Tailwind CSS + shadcn/ui | -- |
| State Management | TanStack React Query | -- |
| Backend | FastAPI + Uvicorn | 0.1.0 |
| ORM / DB Driver | SQLAlchemy (async) + aiosqlite | -- |
| Database | SQLite | -- |
| AI | Multi-provider: Anthropic Claude, OpenAI, Google Gemini | -- |
| RAG | FAISS + sentence-transformers | -- |
| Jobs | BrightData + JSearch (RapidAPI) + Honest Jobs | -- |
| HTTP Client | httpx (async) | -- |
| Config | pydantic-settings (.env) | -- |

---

## Request Flow

The primary user flow: a resident completes the assessment wizard, the backend creates a session, runs the matching engine, and returns a personalized plan.

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as Next.js Frontend
    participant API as FastAPI Backend
    participant ME as Matching Engine
    participant DB as SQLite
    participant Claude as Claude API

    U->>FE: Fill assessment wizard (zip, barriers, work history)
    FE->>API: POST /api/assessment/
    API->>DB: INSERT session (uuid, barriers, qualifications)
    API->>ME: generate_plan(profile, db)
    ME->>DB: Query resources by barrier categories
    ME->>DB: Query all job listings
    ME-->>ME: compute_pvs() (4-factor PVS scoring)
    ME-->>ME: apply_credit_filter() (split eligible now / after repair)
    ME-->>ME: build_barrier_cards() + build_next_steps()
    ME-->>API: ReEntryPlan
    API->>DB: UPDATE session SET plan = ...
    API-->>FE: {session_id, profile, plan}
    FE->>U: Redirect to /plan?session=<id>

    FE->>API: GET /api/plan/<session_id>
    API->>DB: SELECT session by id
    API-->>FE: {session_id, barriers, plan}
    FE->>U: Render MondayMorning, BarrierCards, JobMatches

    Note over FE,Claude: Optional: AI narrative generation
    FE->>API: POST /api/plan/<session_id>/generate
    API->>Claude: messages.create (system + user prompt)
    Claude-->>API: JSON {summary, key_actions}
    API->>DB: UPDATE session plan with resident_summary
    API-->>FE: PlanNarrative
    FE->>U: Display Monday Morning summary
```

### Credit Assessment Side-Flow

When a user selects the credit barrier, the wizard includes an additional credit form step. The frontend calls the credit proxy before submitting the main assessment.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI Backend
    participant CS as Credit Microservice

    FE->>API: POST /api/credit/assess {credit_score, utilization, ...}
    API->>CS: POST /v1/assess/simple (proxied via httpx)
    CS-->>API: {barrier_severity, readiness, thresholds, eligibility, ...}
    API-->>FE: CreditAssessmentResult
    FE-->>FE: Store in sessionStorage for plan page
```

---

## Backend Modules

### Route Layer

| Route | File | Endpoints | Purpose |
|-------|------|-----------|---------|
| `/api/assessment` | `routes/assessment.py` | `POST /` | Intake form, session creation, matching pipeline |
| `/api/plan` | `routes/plan.py` | `GET /{session_id}`, `POST /{session_id}/generate` | Plan lookup, AI narrative generation |
| `/api/credit` | `routes/credit.py` | `POST /assess` | Thin proxy to credit microservice |
| `/api/jobs` | `routes/jobs.py` | `GET /`, `GET /{job_id}` | Job listings with barrier/transit/industry filters |
| `/api/feedback` | `routes/feedback.py` | `POST /resource`, `GET /validate/{token}`, `POST /visit` | Resource helpfulness and post-visit feedback |
| `/api/plan` | `routes/plan.py` | `GET /{session_id}/career-center` | Career Center Ready Package assembly |
| `/api/barrier-intel` | `routes/barrier_intel.py` | `POST /chat`, `POST /reindex` | AI barrier intelligence chat (SSE streaming), RAG reindex |
| `/api/plan` | `routes/career_center.py` | `GET /{session_id}/career-center` | Career Center Ready Package |
| `/api/brightdata` | `routes/brightdata.py` | `POST /crawl`, `GET /status/{id}`, `POST /precrawl` | BrightData crawl lifecycle |
| `/health` | `health/checks.py` | `GET /health`, `GET /health/live`, `GET /health/ready` | Service health checks |

### Matching Engine

| Module | File | Responsibility |
|--------|------|---------------|
| Engine | `modules/matching/engine.py` | Orchestrates the full matching pipeline via `generate_plan()`. Queries resources and jobs, applies scoring and filters, builds barrier cards and next steps, returns a `ReEntryPlan`. |
| Scoring | `modules/matching/scoring.py` | 5-factor weighted scoring: barrier alignment (40%), proximity (20%), transit (15%), schedule (15%), industry (10%). Ranks resources by relevance to a `UserProfile`. |
| Filters | `modules/matching/filters.py` | Eligibility filters applied before or after scoring. Credit filter (splits jobs by severity), transit filter (M-Transit schedule constraints), childcare filter (proximity-based), certification renewal lookup. |
| Types | `modules/matching/types.py` | Pydantic models: `AssessmentRequest`, `UserProfile`, `Resource`, `JobMatch`, `BarrierCard`, `ReEntryPlan`, `WIOAEligibility`, enums for `BarrierType`, `BarrierSeverity`, `EmploymentStatus`, `AvailableHours`. |
| WIOA Screener | `modules/matching/wioa_screener.py` | WIOA eligibility screening: `screen_wioa_eligibility()` evaluates adult program, supportive services, ITA, and dislocated worker eligibility. `has_expired_certification()` helper for certification renewal detection. |
| Affinity | `modules/matching/affinity.py` | Resource affinity routing: `assign_resources()` maps barriers to specific resources using `RESOURCE_AFFINITY` and `BARRIER_PROCESSING_ORDER`. Routes Career Center to `immediate_next_steps`. |
| Barrier Priority | `modules/matching/barrier_priority.py` | Static barrier priority ordering: `get_barrier_priority()` returns a numeric priority (childcare=1 through training=7) for deterministic barrier card ordering. |
| PVS Scorer | `modules/matching/pvs_scorer.py` | Practical Value Score: 4-factor weighted scoring -- net income (35%), proximity (25%), time fit (20%), barrier compatibility (20%). Includes benefits cliff impact tracking. |
| Career Center Package | `modules/matching/career_center_package.py` | `assemble_package()` builds a Career Center Ready Package with staff summary, document checklist, what-to-say scripts, and credit pathway. |

### AI Module

| Module | File | Responsibility |
|--------|------|---------------|
| Client | `ai/client.py` | Calls Claude API via `AsyncAnthropic` to generate plan narratives. Includes `build_fallback_narrative()` for template-based output when the API is unavailable. |
| Prompts | `ai/prompts.py` | System prompt (Montgomery-specific workforce navigator persona) and user prompt template (barriers, qualifications, plan data). |
| Types | `ai/types.py` | `PlanNarrative` (summary + key_actions) and `AnalysisResult` models. |

### Feedback Module

| Module | File | Responsibility |
|--------|------|---------------|
| Tokens | `modules/feedback/tokens.py` | `generate_token()` creates cryptographically random 16-character URL-safe tokens via `secrets.token_urlsafe()`. `create_feedback_token()` and `validate_token()` handle DB storage with 30-day expiry. |
| Health | `modules/feedback/health.py` | `check_resource_health()` evaluates helpfulness signals (HEALTHY/WATCH/FLAGGED thresholds). `get_feedback_stats()` aggregates within a 30-day window. `update_all_health_statuses()` batch updates. |
| Types | `modules/feedback/types.py` | `ResourceHealth` enum (healthy/watch/flagged/hidden), `ResourceFeedbackRequest`, `VisitFeedbackRequest`, and response models. |
| Queries | `core/queries_feedback.py` | Async query helpers: `insert_resource_feedback` (upsert), `token_exists`, `validate_token`, `has_visit_feedback`, `insert_visit_feedback`, `session_exists`. |

### BrightData Integration

| Module | File | Responsibility |
|--------|------|---------------|
| Client | `integrations/brightdata/client.py` | Async HTTP wrapper around BrightData Datasets API v3. Supports `trigger_crawl()` and `get_snapshot_status()`. |
| Polling | `integrations/brightdata/polling.py` | Exponential backoff poller with jitter. `poll_until_ready()` retries up to 30 times (max 60s delay). |
| Cache | `integrations/brightdata/cache.py` | Parses raw BrightData JSON into `BrightDataJobRecord`, deduplicates by URL, and bulk-inserts into `job_listings`. |
| Pre-crawl | `integrations/brightdata/precrawl.py` | Admin utility to pre-populate Montgomery job data. Targets Indeed and LinkedIn searches for Montgomery, AL. Skips if data less than 24 hours old exists. |
| Types | `integrations/brightdata/types.py` | `CrawlStatus`, `CrawlProgress`, `CrawlResult`, `BrightDataJobRecord`, request/response models, custom exceptions. |

### Barrier Graph

| Module | File | Responsibility |
|--------|------|---------------|
| Queries | `barrier_graph/queries.py` | Barrier graph queries: get barriers by category, find root barriers, get top resources by impact strength. |
| Traversal | `barrier_graph/traversal.py` | DAG traversal: identify root barriers (not caused by other user barriers), build causal chain summaries. |
| Seed | `barrier_graph/seed.py` | Idempotent upsert of barrier graph data (barriers, relationships, resources) from JSON seed file. |

### Barrier Intelligence

| Module | File | Responsibility |
|--------|------|---------------|
| Router | `barrier_intel/router.py` | SSE streaming chat endpoint with rate limiting (10/60s). Admin reindex endpoint. |
| Streaming | `barrier_intel/streaming.py` | Assembles retrieval context, streams LLM response chunks, emits audit log entries. |
| Guardrails | `barrier_intel/guardrails.py` | Filters disallowed topics, returns safe fallback responses when guardrails trigger. |

### RAG Store

| Module | File | Responsibility |
|--------|------|---------------|
| Store | `rag/store.py` | In-memory FAISS index + metadata. Build from database or load from disk. Barrier-filtered vector search. |
| Retrieval | `rag/retrieval.py` | Hybrid context assembly: root barriers from graph + top resources + vector search (8 docs). Returns `RetrievalContext`. |
| Corpus Builder | `rag/corpus_builder.py` | Builds document corpus from database resources and barrier graph for FAISS indexing. |

### Benefits Module

| Module | File | Responsibility |
|--------|------|---------------|
| Eligibility Screener | `modules/benefits/eligibility_screener.py` | Screens eligibility for 7 Alabama programs (SNAP, TANF, Medicaid, ALL Kids, Childcare Subsidy, Section 8, LIHEAP). |
| Cliff Calculator | `modules/benefits/cliff_calculator.py` | Net income at wage steps ($8-$25/hr, $0.50 increments). Detects cliff points: severe (>=$200 loss), moderate (>=$50), mild (<$50). |
| Program Calculators | `modules/benefits/program_calculators.py` | Per-program benefit amount calculators using Alabama-specific thresholds and phase-out rates. |

### Criminal Record Module

| Module | File | Responsibility |
|--------|------|---------------|
| Record Profile | `modules/criminal/record_profile.py` | `RecordProfile` model: charge categories, record types, years since conviction, sentence completion. |
| Expungement | `modules/criminal/expungement.py` | Alabama Act 2021-507 eligibility: wait periods (misdemeanor 3yr, felony 5yr), never-expungeable categories, filing steps. |
| Job Filter | `modules/criminal/job_filter.py` | Enriches jobs with fair_chance, record_eligible, background_check_timing. Matches employer policies. |
| Employer Policy | `modules/criminal/employer_policy.py` | `EmployerPolicy` model and `matches_record()` logic. `query_eligible_employers()` filters and sorts by fair-chance status. |
| Employer Seed | `modules/criminal/employer_seed.py` | Idempotent seed loader for employer_policies from JSON. |

### Resources Module

| Module | File | Responsibility |
|--------|------|---------------|
| findhelp.org | `modules/resources/findhelp.py` | Maps barrier types to findhelp.org category URLs. ZIP code validated. |

### Job Integrations

| Module | File | Responsibility |
|--------|------|---------------|
| JSearch | `integrations/jsearch/client.py` | Async JSearch (RapidAPI) client. Montgomery, AL default. Rate limit tracking with monthly quota warnings. |
| Honest Jobs | `integrations/honestjobs/client.py` | Queries fair-chance employer job listings from local database. |

### Core Layer

| Module | File | Responsibility |
|--------|------|---------------|
| Config | `core/config.py` | `Settings` via pydantic-settings. Reads from `.env`. Holds database URL, API keys, CORS origins, Claude model selection. |
| Database | `core/database.py` | Async SQLAlchemy engine + session factory. Raw DDL for table creation. JSON seed loader for Montgomery data (resources, transit routes, employers). |
| Queries | `core/queries.py` | Async query helpers: `get_all_resources`, `get_resources_by_category`, `get_all_transit_routes`, `get_all_employers`, `create_session`, `get_session_by_id`, `update_session_plan`, `get_all_job_listings`, `insert_job_listings`. |
| Credit Types | `modules/credit/types.py` | `SimpleCreditRequest` and `CreditAssessmentResult` Pydantic models for the credit proxy route. |

---

## Database Schema

All tables are created via raw DDL in `core/database.py` and use SQLite (async via aiosqlite).

### Tables

#### sessions

Stores assessment sessions with a 24-hour expiry. The `plan` column holds the full `ReEntryPlan` as serialized JSON.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | Primary key (UUID) |
| created_at | TEXT | ISO 8601 timestamp |
| barriers | TEXT | JSON array of barrier type strings |
| credit_profile | TEXT | Optional JSON |
| qualifications | TEXT | Free-text work history |
| plan | TEXT | Serialized `ReEntryPlan` JSON |
| profile | TEXT | Serialized `UserProfile` JSON (for career center package reconstruction) |
| expires_at | TEXT | ISO 8601 timestamp (created_at + 24h) |

#### resources

Montgomery-area support resources seeded from JSON files.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| name | TEXT | Resource name |
| category | TEXT | One of: `social_service`, `career_center`, `childcare`, `training` |
| subcategory | TEXT | Optional specialization |
| address | TEXT | Street address |
| lat, lng | REAL | Coordinates |
| phone | TEXT | Contact phone |
| url | TEXT | Website |
| eligibility | TEXT | Eligibility criteria |
| services | TEXT | JSON array of services offered |
| hours | TEXT | Operating hours |
| notes | TEXT | Additional notes |

#### employers

Montgomery businesses (seeded from `montgomery_businesses.json`).

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| name | TEXT | Business name |
| address | TEXT | Street address |
| lat, lng | REAL | Coordinates |
| license_type | TEXT | Used for credit check determination |
| industry | TEXT | Industry classification |
| active | INTEGER | 1 = active, 0 = inactive |

#### job_listings

Job listings from BrightData crawls or manual seed.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| title | TEXT | Job title |
| company | TEXT | Employer name |
| location | TEXT | Job location |
| description | TEXT | Job description |
| url | TEXT | Application URL |
| source | TEXT | Origin (e.g., `brightdata:<snapshot_id>`) |
| scraped_at | TEXT | ISO 8601 timestamp |
| expires_at | TEXT | Listing expiration |

#### feedback_tokens

Feedback tokens for post-visit follow-up. Generated during assessment, expire after 30 days.

| Column | Type | Notes |
|--------|------|-------|
| token | TEXT | Primary key (16-char cryptographically random URL-safe) |
| session_id | TEXT | FK to sessions |
| created_at | TEXT | ISO 8601 timestamp |
| expires_at | TEXT | ISO 8601 timestamp (created_at + 30 days) |

#### visit_feedback

Post-visit feedback submitted via the `/feedback/[token]` page.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| session_id | TEXT | FK to sessions |
| submitted_at | TEXT | ISO 8601 timestamp |
| made_it_to_center | INTEGER | 0=no, 1=yes, 2=plan to |
| outcomes | TEXT | JSON array of outcome labels |
| plan_accuracy | INTEGER | 1-3 rating |
| free_text | TEXT | Optional comment (max 1000 chars) |
| reviewed | INTEGER | 0=unreviewed, 1=reviewed (default 0) |
| action_taken | TEXT | Staff notes on follow-up |

#### resource_feedback

Per-resource helpfulness votes. One vote per resource per session (upsert).

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| resource_id | INTEGER | FK to resources |
| session_id | TEXT | FK to sessions |
| helpful | INTEGER | 1=helpful, 0=not helpful |
| barrier_type | TEXT | Barrier context for the feedback |
| submitted_at | TEXT | ISO 8601 timestamp |
| | | UNIQUE(resource_id, session_id) |

#### transit_routes

Montgomery M-Transit bus routes.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| route_number | INTEGER | Route number |
| route_name | TEXT | Route name |
| weekday_start | TEXT | e.g., "05:00" |
| weekday_end | TEXT | e.g., "21:00" |
| saturday | INTEGER | 1 = runs Saturday |
| sunday | INTEGER | 0 = no Sunday service |

#### transit_stops

Individual stops along transit routes.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| route_id | INTEGER | FK to transit_routes |
| stop_name | TEXT | Stop name |
| lat, lng | REAL | Coordinates |
| sequence | INTEGER | Stop order on route |

#### barriers

Barrier nodes in the causal graph. Seeded from barrier graph JSON.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT | Primary key |
| name | TEXT | Barrier name |
| category | TEXT | One of: childcare, transportation, credit, housing, health, training, criminal, employment |
| description | TEXT | Barrier description |
| playbook | TEXT | Intervention playbook text |

#### barrier_relationships

Directed edges between barriers (causal relationships).

| Column | Type | Notes |
|--------|------|-------|
| source_barrier_id | TEXT | FK to barriers |
| target_barrier_id | TEXT | FK to barriers |
| relationship_type | TEXT | Relationship classification |
| weight | REAL | Edge weight |

#### barrier_resources

Links barriers to resources with impact strength.

| Column | Type | Notes |
|--------|------|-------|
| barrier_id | TEXT | FK to barriers |
| resource_id | INTEGER | FK to resources |
| impact_strength | REAL | How strongly this resource addresses the barrier |
| notes | TEXT | Additional context |

#### employer_policies

Employer hiring policies for criminal record screening.

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | Primary key (auto) |
| employer_name | TEXT | UNIQUE employer name |
| fair_chance | INTEGER | 1 = fair-chance employer |
| excluded_charges | TEXT | JSON array of excluded charge categories |
| lookback_years | INTEGER | Years of criminal history considered |
| bg_check_timing | TEXT | `pre_offer` or `post_offer` |
| industry | TEXT | Industry classification |
| source | TEXT | Data source |
| montgomery_area | INTEGER | 1 = Montgomery area employer |

### Seed Data

The database is seeded on first startup from JSON files in the `data/` directory:

| File | Target Table |
|------|-------------|
| `montgomery_businesses.json` | employers |
| `transit_routes.json` | transit_routes |
| `career_centers.json` | resources (category: career_center) |
| `training_programs.json` | resources (category: training) |
| `childcare_providers.json` | resources (category: childcare) |
| `community_resources.json` | resources (category: social_service) |
| `job_listings.json` | job_listings |
| `barrier_graph_seed.json` | barriers, barrier_relationships, barrier_resources |
| `employer_policies_seed.json` | employer_policies |

---

## Frontend Architecture

### Pages (App Router)

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Landing page with hero, how-it-works steps, Montgomery stats, and CTA |
| `/assess` | `app/assess/page.tsx` | Multi-step assessment wizard (basic info, barriers, optional credit, review/submit) |
| `/plan` | `app/plan/page.tsx` | Plan results page with barrier cards, job matches, credit results, comparison view, and export options |
| `/credit` | `app/credit/page.tsx` | Standalone credit assessment form and results display |
| `/feedback/[token]` | `app/feedback/[token]/page.tsx` | Post-visit feedback form (mobile-first, token-validated) |

### Component Hierarchy

```
app/
  layout.tsx
    Header
    page.tsx                        -- Landing page
    assess/page.tsx                 -- Assessment wizard
      WizardShell                   -- Step navigation, progress, next/back/submit
        BarrierForm                 -- Barrier checkbox grid with descriptions
        CreditForm                  -- Credit self-assessment sliders and inputs
        CriminalRecordForm          -- Criminal record self-assessment
        BenefitsStep                -- Household income and benefits data
        IndustryForm                -- Target industry preferences
    plan/page.tsx                   -- Plan results
      MondayMorning                 -- AI narrative hero section (summary + key actions)
      BarrierCardView               -- Individual barrier card (actions + matched resources)
      JobMatchCard                  -- Job match with eligibility badge and apply link
      ComparisonView                -- Side-by-side eligible now vs after repair comparison
      CreditResults                 -- Credit assessment results (severity, thresholds, eligibility)
      PlanExport                    -- Download plan as formatted PDF
      EmailExport                   -- Email plan via mailto link
      CareerCenterExport            -- Download Career Center Ready Package as PDF
      PdfFeedbackQR                 -- QR code linking to feedback page
      BenefitsEligibility           -- Benefits program eligibility cards
      BenefitsCliffChart            -- Wage-step net income chart with cliff markers
      JobFilters                    -- Filter pills for barrier, transit, industry, fair-chance
      FindhelpLink                  -- Deep link to findhelp.org for a barrier type
      EligibilityBadge              -- Status badge for eligibility (likely/check/unknown)
    credit/page.tsx                 -- Standalone credit form
    feedback/[token]/page.tsx       -- Post-visit feedback form
      FeedbackForm                  -- Mobile-first 3-question form with token validation
    ErrorBoundary                   -- Global error boundary
    EmptyState                      -- Empty state placeholder
```

### Key Components

| Component | File | Responsibility |
|-----------|------|---------------|
| `WizardShell` | `components/wizard/WizardShell.tsx` | Generic multi-step wizard with step indicators, validation gates, and configurable complete action. |
| `BarrierForm` | `components/wizard/BarrierForm.tsx` | Renders barrier type checkboxes (credit, transportation, childcare, housing, health, training, criminal record) with descriptions. |
| `CreditForm` | `components/wizard/CreditForm.tsx` | Credit self-assessment with score slider, utilization, payment history, account age, and negative item selection. |
| `MondayMorning` | `components/plan/MondayMorning.tsx` | Displays the AI-generated "Monday Morning" narrative and immediate next steps from the plan. |
| `BarrierCardView` | `components/plan/BarrierCardView.tsx` | Renders a single barrier card: type, severity, action steps, and matched Montgomery resources. |
| `JobMatchCard` | `components/plan/JobMatchCard.tsx` | Displays a job match with company, location, eligibility status, credit check indicator, and apply link. |
| `ComparisonView` | `components/plan/ComparisonView.tsx` | Side-by-side view comparing jobs eligible now vs. eligible after credit repair. |
| `CreditResults` | `components/plan/CreditResults.tsx` | Renders credit assessment output: severity badge, thresholds timeline, product eligibility, and dispute pathway. |
| `PlanExport` | `components/plan/PlanExport.tsx` | Generates a downloadable PDF of the plan via html2pdf.js. |
| `EmailExport` | `components/plan/EmailExport.tsx` | Sends the plan via the EmailJS API to the resident's email address. |
| `CareerCenterExport` | `components/plan/CareerCenterExport.tsx` | Fetches Career Center Ready Package, renders `CareerCenterPrintLayout` offscreen, exports as date-stamped PDF. |
| `CareerCenterPrintLayout` | `components/plan/CareerCenterPackage.tsx` | 3-page print layout: staff summary, resident plan, credit pathway. Uses forwardRef. Exported from `CareerCenterPackage.tsx`. |
| `PdfFeedbackQR` | `components/plan/PdfFeedbackQR.tsx` | QR code (level M, 100px) encoding the feedback page URL for inclusion in PDF exports. |
| `FeedbackForm` | `app/feedback/[token]/feedback-form.tsx` | Mobile-first 3-question post-visit feedback form with token validation, conditional outcomes, large touch targets. |

### Data Fetching

The frontend uses TanStack React Query for server state management:

| Hook | API Call | Trigger |
|------|----------|---------|
| `useMutation` | `POST /api/assessment/` | Wizard submit button |
| `useQuery` | `GET /api/plan/{session_id}` | Plan page load |
| `useMutation` | `POST /api/plan/{session_id}/generate` | Auto-triggered on plan load (once) |
| `useQuery` | `GET /api/jobs/?barriers=...` | Plan page load (after plan data available) |
| `useMutation` | `POST /api/credit/assess` | Credit form submit (wizard or standalone) |
| `useMutation` | `POST /api/feedback/resource` | Thumbs up/down on resource cards |
| `useQuery` | `GET /api/feedback/validate/{token}` | Feedback page load (token validation) |
| `useMutation` | `POST /api/feedback/visit` | Visit feedback form submit |
| `useQuery` | `GET /api/plan/{session_id}/career-center` | Career Center export button click |

---

## External Services

| Service | Base URL | Purpose | Auth Method |
|---------|----------|---------|-------------|
| Claude API | `https://api.anthropic.com` | Generate personalized plan narratives ("Monday Morning" summary and key actions) | Bearer token (`ANTHROPIC_API_KEY`) via Anthropic SDK |
| Credit Microservice | Configurable (`CREDIT_API_URL`, default `http://localhost:8001`) | Credit barrier assessment: severity scoring, threshold analysis, product eligibility, dispute pathways | API key header (`X-API-Key`) |
| BrightData Datasets API v3 | `https://api.brightdata.com/datasets/v3` | Async web crawling of job boards (Indeed, LinkedIn) for Montgomery, AL job listings | Bearer token (`BRIGHTDATA_API_KEY`) |

### Failure Modes

| Service | Failure Behavior |
|---------|-----------------|
| Claude API | Falls back to `build_fallback_narrative()` -- template-based summary built from plan data. Logged as warning. |
| Credit Microservice | Returns HTTP 503 (unavailable), 504 (timeout), or 502 (network error) to the frontend. Frontend shows error and continues without credit data. |
| BrightData API | Returns HTTP 502 with error detail. Pre-crawl skips if recent data exists (24h cache). Polling times out after 30 retries with exponential backoff. |

---

## Configuration

All configuration is managed via environment variables loaded by pydantic-settings from `.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./montgowork.db` | SQLite database path |
| `CREDIT_API_URL` | `http://localhost:8001` | Credit microservice base URL |
| `CREDIT_API_KEY` | (empty) | API key for credit microservice |
| `ANTHROPIC_API_KEY` | (empty) | Anthropic API key for Claude |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model identifier |
| `BRIGHTDATA_API_KEY` | (empty) | BrightData API key |
| `BRIGHTDATA_DATASET_ID` | (empty) | BrightData dataset identifier |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `OPENAI_API_KEY` | (empty) | OpenAI API key |
| `GEMINI_API_KEY` | (empty) | Google Gemini API key |
| `LLM_PROVIDER` | (auto-detect) | Force LLM provider: `anthropic`, `openai`, `gemini`, `mock` |
| `JSEARCH_API_KEY` | (empty) | JSearch (RapidAPI) key |
| `ADMIN_API_KEY` | (empty) | Admin endpoint authentication |
| `ENVIRONMENT` | `development` | Environment: development, test, staging, production |
| `AUDIT_LOG_PATH` | (empty) | JSONL audit log file path |
| `AUDIT_HASH_SALT` | `montgowork-default-salt` | Salt for session ID hashing in audit logs |
| `DATA_DIR` | (empty) | Custom seed data directory path |

---

## Scoring Algorithm

### Practical Value Score (PVS)

The matching engine scores each job against a user profile using four weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Net income | 0.35 | Normalized to earnings benchmark. Uses net income (wages + benefits - taxes) when benefits profile available; falls back to gross earnings. No-pay jobs get a 0.55 multiplier (max 0.25 PVS). |
| Proximity | 0.25 | Distance from user ZIP to job location. Linear decay from 1.0 at 1 mile to 0.1 at 15 miles. |
| Time fit | 0.20 | Job schedule compatibility with user availability (daytime, evening, night, flexible). |
| Barrier compatibility | 0.20 | Credit barrier: 0.2 if credit-blocked. Criminal record: fair-chance=1.0, eligible=0.8, blocked=0.2, unknown=0.5. |

Jobs are ranked by descending PVS.

### Resource Scoring (Legacy)

Resources are still scored using the 5-factor system for barrier card ordering:

| Factor | Weight | Description |
|--------|--------|-------------|
| Barrier alignment | 0.40 | Resource category matches user's barriers (1.0 match, 0.1 base) |
| Proximity | 0.20 | Haversine distance, linear decay. Returns 0.5 neutral when coordinates unavailable. |
| Transit accessibility | 0.15 | Penalizes transit-dependent users needing night/Sunday access. |
| Schedule compatibility | 0.15 | Resource hours vs user schedule preference. |
| Industry alignment | 0.10 | Resource services mention user's target industries. |

---

## Barrier Types and Category Mapping

The matching engine maps each barrier type to resource categories for querying:

| Barrier Type | Resource Categories |
|-------------|-------------------|
| `credit` | career_center, social_service |
| `transportation` | career_center |
| `childcare` | childcare |
| `housing` | social_service |
| `health` | social_service |
| `training` | training, career_center |
| `criminal_record` | career_center, social_service |

Barrier severity is determined by count: 1 barrier = LOW, 2 = MEDIUM, 3+ = HIGH. Severity affects the credit filter behavior (HIGH excludes all credit-check jobs; MEDIUM excludes only finance/government credit-check jobs; LOW applies no filter).

---

## Known Limitations & Scaling Path

1. **SQLite → PostgreSQL:** Single-file database, limited concurrent writes. Migration path: swap `aiosqlite` for `asyncpg`, update `DATABASE_URL` format (`postgresql+asyncpg://...`). Railway managed Postgres or Supabase are drop-in replacements with no schema changes required — SQLAlchemy handles the abstraction.

2. **Static resource data:** Resources loaded from JSON at startup, no automated refresh. Path: nightly cron via BrightData for job listings (routes already exist at `POST /api/brightdata/precrawl`). Manual review cadence for static resources; user feedback loop (implemented — resource health decay with HEALTHY/WATCH/FLAGGED/HIDDEN statuses) handles decay detection via helpfulness signals.

3. **No caching layer:** All requests hit SQLite directly. Path: Redis for job listings (24h TTL) and resource queries (1h TTL). FastAPI middleware for cache-aside pattern.

4. **External API resilience:** BrightData polling already has exponential backoff with jitter (2-60s, 30 retries). Credit API returns 503/504/502 on failure. Claude API falls back to template narrative. Missing: circuit breaker pattern. Path: `tenacity` for retry decorators, `pybreaker` for circuit breakers on future integrations.

5. **Security hardening:** Rate limiting exists on all endpoint groups. Sprint 30 audit addressed SSRF, timing-safe auth, production config validators, PII protection, and prompt injection defense. See `docs/SECURITY.md` for full posture.

6. **Horizontal scaling:** Single process, single SQLite file. Decomposition path: API service and scraping workers as separate Railway services, PostgreSQL as managed addon, Redis as Railway plugin. No application code changes required — infrastructure decomposition only.
