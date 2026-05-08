# MontGoWork Roadmap

Current state as of May 2026. Organized by what's done, what's in progress, and what's next.

> **Note on sprint numbering.** This roadmap mixes two tracks. The Montgomery, AL hackathon era (Sprints 3–30 below) used sequential numbering. The Fort Worth visual-rebirth and post-rebirth feature work (S1–S13, then S22+) is tracked separately by bpsai-pair under `.paircoder/context/state.md`; recent cross-track sprints are listed at the end of this section.

---

## Completed

### Core Pipeline (Sprints 3-4)
- [x] Database layer -- async SQLAlchemy, raw DDL, JSON seed loader
- [x] 5-factor scoring engine (barrier alignment, proximity, transit, schedule, industry)
- [x] Matching filters (credit, transit, childcare, certification)
- [x] Matching engine orchestrator (`generate_plan()`)
- [x] Assessment route with session creation
- [x] Plan route with session lookup

### Frontend (Sprint 5)
- [x] Multi-step assessment wizard (WizardShell, BarrierForm, CreditForm)
- [x] Plan results page (barrier cards, job matches, comparison view)
- [x] Credit results display
- [x] Error boundary and empty states

### BrightData Integration (Sprint 7)
- [x] BrightData HTTP client (trigger crawl, get snapshot status)
- [x] Exponential backoff polling (2-60s, 30 retries, jitter)
- [x] Job listing cache (parse, deduplicate, bulk insert)
- [x] Pre-crawl Montgomery jobs (Indeed + LinkedIn)
- [x] Crawl and status REST endpoints

### Export and Polish (Sprint 8)
- [x] PDF export via html2pdf.js
- [x] Email export via EmailJS
- [x] Styled print-ready layout

### Documentation (Sprint 9)
- [x] API reference (`docs/api.md`)
- [x] Architecture documentation (`docs/architecture.md`)
- [x] Setup guide (`docs/setup.md`)

### Accessibility and Demo (Sprint 10)
- [x] ARIA labels and keyboard navigation
- [x] Demo script with Maria persona (`docs/demo-script.md`)

### Launch Prep (Sprint 11)
- [x] Dockerfile + Dockerfile.frontend + docker-compose.yml
- [x] Health check endpoints (liveness, readiness, general)
- [x] Rate limiting on assessment endpoint
- [x] Startup warnings for missing optional services
- [x] Security hardening pass

### Monday Morning UX (Sprint 12)
- [x] AI-generated "Monday Morning" narrative via Claude
- [x] Template-based fallback when API unavailable
- [x] Key actions extraction

### Intelligent Job Matching (Sprint 13)
- [x] Three-bucket job display (strong, possible, after repair)
- [x] Job relevance scoring
- [x] Transit-aware job filtering

### Feedback Loop (Sprint 14)
- [x] Feedback tokens (cryptographically random, 30-day expiry)
- [x] Resource feedback API (POST /api/feedback/resource, upsert per session)
- [x] Resource feedback UI (thumbs up/down on barrier card resources)
- [x] Visit feedback API (POST /api/feedback/visit, token-gated, one per session)
- [x] Visit feedback form (`/feedback/[token]`, mobile-first, 3 questions)
- [x] QR code in PDF export linking to feedback form
- [x] Resource health decay (HEALTHY > WATCH > FLAGGED > HIDDEN)
- [x] Rate limiting on feedback endpoint

### Career Center Ready Package (Sprint 15)
- [x] WIOA eligibility screener (Adult Program, Supportive Services, ITA)
- [x] Career Center Package data model and assembler
- [x] GET /api/plan/{session_id}/career-center endpoint
- [x] WIOA eligibility wired into generate_plan()
- [x] CareerCenterPackage print layout component (staff summary + resident plan)
- [x] Career Center Ready PDF export button
- [x] Frontend types and API client

### Fix Sprint (Sprint 16)
- [x] SQLAlchemy StaticPool alignment
- [x] Resource affinity routing (specialized resources claim barrier cards)
- [x] Barrier priority ordering (childcare first, training last)
- [x] Cloud deployment documentation (Railway + Vercel)
- [x] Architecture known limitations section

### Code Review Fixes
- [x] Cryptographically random feedback tokens (replaced deterministic SHA-256)
- [x] Full UserProfile persisted in sessions table (eliminates data loss on reconstruction)
- [x] Batch feedback stats query (eliminated N+1 in health check)
- [x] Rate limiting on feedback resource endpoint
- [x] Career center address centralized (single source of truth)
- [x] Frontend Resource type includes health_status
- [x] SSR guard on window.location in PDF QR component
- [x] Free-text feedback field length validation (max 1000 chars)

### Barrier Graph & AI Chat (Sprint 23)
- [x] Barrier graph DAG (barriers, relationships, resources tables)
- [x] Root barrier detection and causal chain traversal
- [x] RAG knowledge base -- FAISS vector store with barrier-filtered search
- [x] Barrier intelligence SSE streaming chat with guardrails
- [x] Response caching and rate limiting (10 req/60s)
- [x] Admin reindex endpoint for rebuilding RAG index

### PVS Scoring System (Sprint 24)
- [x] Practical Value Score (PVS) -- 4-factor: net income (35%), proximity (25%), time fit (20%), barrier compatibility (20%)
- [x] Benefits cliff detection -- wage-step analysis with severity classification (mild/moderate/severe)
- [x] No-pay ceiling (0.25 max PVS for undisclosed salary jobs)
- [x] Replaces legacy 5-factor scoring for job ranking

### Benefits Eligibility (Sprint 29)
- [x] Benefits eligibility screener for 7 Alabama programs (SNAP, TANF, Medicaid, ALL Kids, Childcare Subsidy, Section 8, LIHEAP)
- [x] Benefits cliff calculator -- net income at wage steps ($8-$25/hr), cliff point detection
- [x] Benefits step in assessment wizard
- [x] BenefitsEligibility and BenefitsCliffChart frontend components

### Criminal Record Module (Sprint 28)
- [x] Criminal record form in assessment wizard
- [x] Record profile model (charge categories, record types, years since conviction)
- [x] Expungement eligibility screening (Alabama Act 2021-507, wait periods, filing steps)
- [x] Employer policy matching -- fair-chance job filtering, background check timing
- [x] Employer policies seed data (20+ Montgomery-area employers)

### Job Aggregation (Sprint 26-28)
- [x] JSearch API integration (RapidAPI) with rate limit tracking
- [x] Honest Jobs fair-chance employer listings
- [x] BrightData dataset crawls (Indeed/LinkedIn)
- [x] Aggregated /api/jobs/ endpoint with filters (barrier, transit, industry, fair-chance)
- [x] Job detail enrichment (industry, credit check, transit, application steps)

### Multi-Provider LLM (Sprint 27)
- [x] LLM client supporting Anthropic Claude, OpenAI, Google Gemini
- [x] Auto-detection of available provider from configured API keys
- [x] Fallback to mock provider when no keys configured
- [x] PII-safe audit logging (JSONL, hashed session IDs)

### findhelp.org Integration (Sprint 28)
- [x] Barrier-to-category mapping for findhelp.org resource directories
- [x] Deep links with ZIP code validation
- [x] Frontend FindhelpLink component on barrier cards

### Security Audit (Sprint 30)
- [x] SSRF prevention on external API calls
- [x] Timing-safe admin key comparison (hmac.compare_digest)
- [x] Production config validators (audit salt, admin key, CORS localhost)
- [x] Backend SecurityHeadersMiddleware
- [x] PII exclusion -- criminal record data excluded from API responses
- [x] safeHref XSS prevention on external URLs
- [x] Prompt injection defense via XML user_input tags

### Fort Worth Visual Rebirth + Worker Companion (Sprints S1–S13)
City framework + Fort Worth substrate + Worker Companion (Foundation + Value Extensions) + Platform-Wide QC. Detail in `.paircoder/context/state.md` "Previous Sprints (summary)" and `.paircoder/archive/state-s12a.md` / `.paircoder/archive/state-s13.md`.
- [x] S1 — City Framework Scaffold (8/8); S2 — Fort Worth Data + Texas Rules (18/18); S3 — Texas/Fort Worth audit
- [x] S4 — Hackathon polish (share, sequence viz, what-if simulator, voice input, i18n)
- [x] S5 — Employment Pathway Engine (cliff-aware multi-step); S6 — Backend hardening + Montgomery leak remediation
- [x] S7 — Outcome-Informed Barrier Intelligence (N+1 loop); S8 — Cross-module integration verify
- [x] S9 — Intelligence loop end-to-end (calibrated_weeks → pathway); S10 — Demo seed + pipeline verification
- [x] S11 — "People Like You" Community Insights (deterministic, city-aware, no-LLM)
- [x] S12a — Worker Companion Foundation (26/26): migrations, feature flags + audit, APScheduler, appointments/jobs/documents/plan modules, digest composer, nightly orchestrator
- [x] S12b — Value Extensions (25/25): PDF rendering, resume + cover-letter builders, reminder engine, jobs kanban, advisor inbox, weekly review, compliance gate (export + right-to-delete)
- [x] S13 — Platform-Wide QC + Submission Readiness (55/128): QC infra (Playwright, visual baseline, Lighthouse CI, bundle gate, Dependabot), 15 production fixes (injection-filter, PII retention, advisor PII leak, scheduler grace, etc.). Browser-driven remainder deferred to S13b.

### Identity Foundation (Sprint S22) — merged 2026-05-07 (PR #123)
- [x] Alembic migration runner + async env (sqlite + asyncpg)
- [x] Identity layer: `accounts`, `account_sessions`, `account_credentials`, `account_roles` (alembic 0011 + 0012)
- [x] Magic-link auth: `POST /api/auth/magic-link` (always 202, no enumeration), `GET /api/auth/claim` (signed `gw_account` cookie)
- [x] Account-aware UI: `useAccount()` hook + `<SaveProgressCTA />` at 3 funnel insertion points
- [x] Anonymous-first invariant test (auto-discovers session-id routes; 0 in REQUIRES_AUTH_ALLOWLIST)
- [x] Postgres CI service container + dual-engine config + 15-test parity suite
- [x] Integrity charter v1 (`docs/integrity-charter.md`, 10 binding principles led by "money never moves position")

### Assessment Authoring Pipeline (Sprint S23) — merged 2026-05-08 (PR #124)
- [x] Schema: `assessments`, `assessment_versions`, `assessment_questions`, `assessment_reviews` (alembic 0013)
- [x] Claude-draft endpoint + reviewer queue API + publish endpoint with provenance lock
- [x] Public fetch with rubric exclusion + Cache-Control
- [x] Admin dashboard: `/admin/assessments` list + detail with filter dropdowns, comment textarea, approve / reject / request-revision actions
- [x] Role substrate: `/api/auth/me` extended with roles, `useAccountRoles` hook, `<RoleGate>`, role-aware nav, `/admin/layout.tsx`
- [x] Postgres test isolation rebuild (session-scoped engine + per-test transaction-rollback) — closed S22 follow-up

### Two-Sided Listing Verification (Sprint S24) — merged 2026-05-08 (PR #125)
- [x] Schema: `employer_accounts`, `listing_claims`, `listing_verifications`, `listing_reputation_events` (alembic 0014)
- [x] `POST /api/employers/claim` — magic-link-style domain-email proof, 202 always, anti-rotation rate-limit
- [x] `GET /api/employers/claim/verify` — uniform 401, 409 cross-employer, `gw_employer_account` HMAC cookie
- [x] `POST /api/employers/{eid}/listings/{lid}/intake` — Pydantic-validated, cookie-or-admin gated
- [x] `GET /api/jobs` verification-tier extension (display-only; `intake_json` excluded)
- [x] `POST /api/listings/{lid}/events` — case_manager + admin gated; ghosted-counted-but-not-surfaced invariant
- [x] Admin claim-review dashboard: `/admin/listings` queue + detail with approve/reject (`employers_admin.py`)
- [x] Frontend `<VerifiedBadge tier intakeComplete />` with three tiers + amber sub-badge; integrated into `/jobs`
- [x] E2E smoke (claim → verify → intake → public summary → reputation event through real HTTP layer)
- [x] Charter integrity assertion — explicit grep across `backend/app/modules/matching/` confirms ZERO references to verification fields (display-only badge invariant)

---

## Known Gaps (Not Blockers)

These are documented trade-offs, not missing features. See `docs/architecture.md` "Known Limitations" for details.

### Documentation Drift
- Documentation is current as of Sprint S24 (2026-05-08). Test counts and endpoint references may drift between sprints.

### Employers Seed Data
- `data/montgomery_businesses.json` is `[]` (empty array). Job matching uses `job_listings` table instead. The `employer_policies` table has 20+ records for fair-chance employer matching.

### Resource Coordinates
- Proximity scoring factor (20% weight) returns neutral 0.5 for all resources because `lat`/`lng` are not populated in seed data. Scoring works but proximity is not differentiated.

---

## Planned Next

### Phase: Admin Dashboard
- Resource management (add/edit/hide resources)
- Review flagged resources from feedback health decay
- View visit feedback submissions
- Manually trigger BrightData pre-crawl

### Phase: Dallas Expansion (DFW Unification)
- [ ] Create `cities/dallas.yaml` config (ZIP ranges, coordinates, Workforce Solutions Greater Dallas info)
- [ ] Create `data/cities/dallas/` seed directory (community resources, employers, fair-chance index)
- [ ] Add DART (Dallas Area Rapid Transit) transit data — GTFS feed, stop coordinates, route hours
- [ ] Dallas-specific career center and resource seed data (legal aid, childcare, housing)
- [ ] Dallas fair-chance employer index from open sources
- [ ] No new state-level work needed — Texas benefits (HHSC), expunction (Art. 55), and nondisclosure (Gov Code Ch. 411 E-1) modules already built for Fort Worth
- [ ] Frontend city selector or `CITY=dallas` env var support (same pattern as `fort-worth`)
- [ ] Consider DFW-level view that spans both cities (shared employer index, cross-city job matches)
- [ ] Validate all city-aware routers (benefits, criminal, geo, resources, AI prompts) work with Dallas config
- [ ] Integration tests: end-to-end Dallas assessment flow

### Phase: Data Quality
- Populate resource coordinates from address geocoding
- Activate proximity scoring (currently neutral -- returns 0.5 for all resources)
- Add transit stop coordinates for route-to-resource distance calculation

### Phase: Infrastructure Scaling
- SQLite to PostgreSQL migration (swap driver, no schema changes)
- Redis caching layer (job listings 24h TTL, resources 1h TTL)
- Circuit breaker pattern on external APIs (`tenacity` + `pybreaker`)
- `slowapi` for per-route rate limiting coverage
- Separate API and crawl worker Railway services

### Phase: User Experience
- Session persistence (currently ephemeral, 24h expiry)
- Multi-language support (Spanish priority for Montgomery demographics)
- Progressive Web App (offline plan access)
- SMS delivery of plan link (alternative to email/PDF)

### Phase: Integrations
- Alabama JobLink direct integration
- Montgomery Housing Authority API
- MATS real-time bus tracking
- 211 resource directory sync
- findhelp.org expanded category coverage
