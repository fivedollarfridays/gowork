# MontGoWork Roadmap

Current state as of March 2026. Organized by what's done, what's in progress, and what's next.

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

---

## Known Gaps (Not Blockers)

These are documented trade-offs, not missing features. See `docs/architecture.md` "Known Limitations" for details.

### Dead Config Field
- `FEEDBACK_TOKEN_SECRET` exists in `config.py` but is no longer used -- tokens are now `secrets.token_urlsafe()`. Config field should be removed.

### Documentation Drift
- `docs/setup.md` says "277 backend / 82 frontend tests" -- actual is 449 / 141
- `docs/api.md` is missing feedback endpoints and career-center endpoint
- `docs/architecture.md` is missing: `profile` column on sessions, `health_status` column on resources, feedback/WIOA/affinity/priority modules, frontend feedback page

### Employers Seed Data
- `data/montgomery_businesses.json` is `[]` (empty array). Job matching uses `job_listings` table instead, but the employers table is effectively unused.

### Resource Coordinates
- Proximity scoring factor (20% weight) returns neutral 0.5 for all resources because `lat`/`lng` are not populated in seed data. Scoring works but proximity is not differentiated.

---

## Planned Next

### Phase: BrightData Sponsor Demo
Crawl live jobs from Indeed/LinkedIn for Montgomery, wire into plan view. Routes and infrastructure exist; needs end-to-end wiring with real API keys and frontend "Explore More Jobs" section.

### Phase: Admin Dashboard
- Resource management (add/edit/hide resources)
- Review flagged resources from feedback health decay
- View visit feedback submissions
- Manually trigger BrightData pre-crawl

### Phase: Data Quality
- Populate resource coordinates from address geocoding
- Activate proximity scoring (currently neutral)
- Populate employers seed data or remove unused table
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
