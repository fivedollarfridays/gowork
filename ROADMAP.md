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

---

## Known Gaps (Not Blockers)

These are documented trade-offs, not missing features. See `docs/architecture.md` "Known Limitations" for details.

### Documentation Drift
- Documentation is current as of Sprint 30. Test counts and endpoint references may drift between sprints.

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
