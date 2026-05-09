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

### Dallas Expansion / DFW Unification (Sprint S25) — merged 2026-05-08 (PR #126)
- [x] `cities/dallas.yaml` config (state=TX, zip 75201-75398, appointment_services byte-identical to FW); `backend/app/cities/dallas/` module with `DALLAS_ELIGIBILITY_RULES` (9 entries)
- [x] Dallas seed under `data/cities/dallas/`: community_resources (17), career_centers (1), resources (10), employers (35), employer_policies (35), barrier_graph (33 barriers + 53 relationships, structurally identical to FW), training_programs (9), childcare_providers (12). honestjobs_listings.json (26 entries) under `backend/data/cities/dallas/`.
- [x] **Reusable GTFS importer** (Spotlight invention): `scripts/import_gtfs.py` + `import_gtfs_calendar.py` + `import_gtfs_stops.py` — stdlib-only, contract boundary between any GTFS feed and the canonical FW JSON shape. Handles `calendar_dates.txt` (DART pattern) + sat/sun aggregation across multiple service_ids per route. 16 fixture tests; reusable for Houston METRO + future cities.
- [x] **Live DART feed shipped:** 92 routes / 8270 stops via the importer (replaces initial synthetic Option-A seed after user pushback in Wave 6)
- [x] City-aware router validation: parametrized tests over 10+ city-aware modules confirm Dallas dispatches correctly via existing `get_city_config()` + `city.state == "TX"` guards (zero per-city branching added)
- [x] DFW bounding-box test extended for embedded Dallas ZIPs (75201/75204/75215/75216/75217/75224/75227/75228/75232/75241); all FW assertions still green
- [x] Dallas E2E assessment-flow integration test (POST /api/assessment ZIP 75201 → GET /api/plan surfaces ≥1 Dallas resource + DART transit + Dallas employer)
- [x] S22 anonymous-first invariant test green with `CITY=dallas`
- [x] Frontend Dallas plumbing: `DEMO_ZIPS["dallas"] = "75201"`; useDemoMode-cityaware test parametrized over both cities; en.json + es.json `chapter09.cityDallas` mirroring `chapter09.cityFW`
- [x] DFW cross-metro summary admin page (`/admin/cities/dfw`, P1): read-only diagnostic; reads counts from JSON seed files via `load_city_config(slug).data_dir` — ZERO DB queries; gated via `<RoleGate roles={["admin"]}>`. Header copy "Read-only diagnostic. Cross-city matching is not enabled." (design-review trigger)
- [x] Charter integrity assertion (`test_charter_integrity_dallas.py`): in-Python + subprocess grep + ZIP-specific tests confirm ZERO references to `dallas`/`DART`/`DFW`/embedded Dallas ZIPs across `backend/app/modules/matching/`. Matching engine remains city-symmetric.
- [x] Production fix surfaced: `temporal_types.TIMEZONE_BY_CITY` Dallas entry added (T25.1 oversight; T25.6 validation surfaced the latent KeyError)

### Admin Dashboard (Sprint S26) — merged 2026-05-09 (PR #127)
- [x] alembic 0015 (T26.1): `resources.user_curated_at TIMESTAMP NULL` + `seed_helpers.py:seed_from_file` skips upsert when set. Without this, admin add/edit would be wiped on the next reseed.
- [x] Resource CRUD backend (T26.2): 6 admin-gated routes + `queries_admin_resources.py` (5 fns; sole-writer set_health_status). Soft-hide via `health_status='hidden'`; restore reverses to `'healthy'`. WRITABLE_COLUMNS allowlist prevents stray fields from poisoning curation marker. Empty-patch still stamps timestamp (touch-as-curation).
- [x] Admin feedback backend (T26.3): 5 admin-gated routes — flagged-queue read + approve/confirm-hide actions, visit-inbox read + mark-reviewed mutation. No schema changes (visit_feedback already has reviewed + action_taken from m001).
- [x] BrightData gate migration (T26.4): `routes/brightdata.py` migrated from legacy `require_admin_key` (header) to S22 `require_role("admin")` (cookie). Admin UI now calls every endpoint via the same auth path.
- [x] Cross-session allowlist (S24 carryforward): every new admin endpoint registered in `_cross_session_fixtures.py:PUBLIC_ENDPOINTS` with rationale at write time per per-route AC discipline (S25 lesson).
- [x] Audit-integrity allowlist: 7 mutating endpoints triaged in `_audit_integrity_fixtures.py:AUDIT_ALLOWLIST` (3 from T26.3 carryover + 4 from T26.2). T26.2 driver caught the engage-shipped gap.
- [x] Frontend admin pages (T26.8 + T26.9 + T26.10 + T26.11): `/admin/resources` (table + filters + edit/add modals + ResourceForm), `/admin/feedback` (tabbed Flagged + Visits with hash-sync deep links), `/admin/brightdata` (trigger + 4-state status display + AlertDialog confirmation), `/admin` landing (6 section cards + 4 quick-stats badges with graceful per-badge degradation).
- [x] Frontend API clients (T26.5 + T26.6 + T26.7): `admin_resources.ts`, `admin_feedback.ts`, `admin_brightdata.ts` — all use the lifted `fetchWithCookie` + `throwOnApiError` from S25's `_client.ts`. Zero per-domain transport duplication.
- [x] Reality-check (T26.7): backend mounts BrightData at `/api/brightdata` (not `/api/admin/brightdata`); CrawlStatus has 4 enum states (`starting | running | ready | failed`), not 3. Driver matched backend reality.
- [x] Charter assertions held: anonymous-first invariant (S22), display-only matching engine (S25 charter test re-runs green; admin dashboard adds zero matching-engine references), money never moves position (charter principle 1).
- [x] Backend 4824 → 4882 (+58); frontend 3629 → 3712 (+83). Zero new failures.

---

## Known Gaps (Not Blockers)

These are documented trade-offs, not missing features. See `docs/architecture.md` "Known Limitations" for details.

### Documentation Drift
- Documentation is current as of Sprint S26 (2026-05-09). Test counts and endpoint references may drift between sprints.

### Employers Seed Data
- `data/montgomery_businesses.json` is `[]` (empty array). Job matching uses `job_listings` table instead. The `employer_policies` table has 20+ records for fair-chance employer matching.

### Resource Coordinates
- Proximity scoring factor (20% weight) returns neutral 0.5 for all resources because `lat`/`lng` are not populated in seed data. Scoring works but proximity is not differentiated.

---

## Planned Next

### Phase: Admin Dashboard — ✅ Sprint S26 (see Completed above)
- [x] Resource management (add/edit/hide resources) — `/admin/resources` (T26.8) + alembic 0015 user_curated_at flag (T26.1) + 6 admin-gated CRUD routes (T26.2)
- [x] Review flagged resources from feedback health decay — `/admin/feedback#flagged` (T26.9) + 3 backend routes (T26.3 list/approve/confirm-hide)
- [x] View visit feedback submissions — `/admin/feedback#visits` (T26.9) + 2 backend routes (T26.3 list/mark-reviewed; uses existing m001 reviewed + action_taken columns)
- [x] Manually trigger BrightData pre-crawl — `/admin/brightdata` (T26.10) + cookie-session admin gate (T26.4 migrated brightdata.py from legacy require_admin_key)
- [x] /admin landing page indexing all admin sub-areas (T26.11; 6 cards: Assessments / Listings / Cities-DFW / Resources / Feedback / BrightData) — replaces URL-only navigation
- [ ] **S27 follow-up:** bulk admin operations (bulk hide/restore on resources, bulk mark-reviewed on visits) — single-row only this sprint
- [ ] **S27 follow-up:** resource provenance audit log (who-changed-what-when on `resources` table) — needs new `resources_audit_log` table; was explicit S26 out-of-scope
- [ ] **S27 follow-up:** migrate other legacy `require_admin_key` callers (`admin_flags.py`, `demo.py`) — only `brightdata.py` migrated this sprint because the new admin UI needed it

### Phase: Dallas Expansion (DFW Unification) — ✅ Sprint S25 (see Completed above)
- [x] Create `cities/dallas.yaml` config (ZIP ranges 75201-75398, coordinates, Workforce Solutions Greater Dallas info)
- [x] Create `data/cities/dallas/` seed directory (community resources, employers, fair-chance index)
- [x] Add DART (Dallas Area Rapid Transit) transit data — live GTFS feed (92 routes / 8270 stops via reusable importer)
- [x] Dallas-specific career center and resource seed data (legal aid, childcare, housing)
- [x] Dallas fair-chance employer index from open sources (35 employers + 35 policies + 26 honestjobs listings)
- [x] No new state-level work needed — Texas benefits (HHSC), expunction (Art. 55), and nondisclosure (Gov Code Ch. 411 E-1) modules already built for Fort Worth
- [x] `CITY=dallas` env var support (same pattern as `fort-worth`); ZIP→city resolution via existing dispatch — frontend city selector intentionally NOT added (anonymous-first invariant from S22)
- [x] DFW-level read-only diagnostic view (`/admin/cities/dfw`) — admin-gated, displays per-metro counts; cross-city *matching* deliberately deferred (charter integrity assertion holds)
- [x] Validate all city-aware routers (benefits, criminal, geo, resources, AI prompts) work with Dallas config (T25.6 parametrized tests over 10+ modules)
- [x] Integration tests: end-to-end Dallas assessment flow (T25.6 `test_dallas_e2e.py`)
- [ ] **S26 follow-up**: Cross-city matching (Dallas users seeing FW jobs / vice versa) — requires matcher + employer-index changes; T25.9 charter test will fail when this work begins (intended design-review trigger)
- [ ] **S26 follow-up**: Add Dallas ZIP centroids to `_FW_ZIP_CENTROIDS` (Dallas users currently hit "no distance signal" fallback for commute-boost scoring)

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
