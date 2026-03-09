# MontGoWork -- Workforce Navigator for Montgomery, Alabama

> Helping residents overcome the real barriers between them and employment.

MontGoWork is a full-stack workforce navigation platform built for Montgomery, Alabama. A resident completes a barrier assessment (credit, transportation, childcare, housing, health, training, criminal record), and the system generates a personalized re-entry plan: jobs ranked by a Practical Value Score, benefits eligibility screening across 7 Alabama programs, criminal record routing with expungement guidance, AI-powered barrier intelligence chat, and a printable Career Center Ready Package. The result is a comprehensive plan the resident takes to the Montgomery Career Center on Monday morning.

---

## Features

### Assessment & Matching
- [x] **Multi-step assessment wizard** -- ZIP validation (361xx), barrier selection with live severity badge, conditional credit self-assessment, criminal record form, benefits data, industry preferences, work history
- [x] **7 barrier types** -- credit, transportation, childcare, housing, health, training, criminal record
- [x] **Practical Value Score (PVS)** -- 4-factor scoring: net income (35%), proximity (25%), time fit (20%), barrier compatibility (20%) -- replaces legacy 5-factor system
- [x] **Benefits cliff detection** -- calculates net income (wages + benefits - taxes) at each wage step, identifies cliff points where benefits drop sharply
- [x] **Criminal record routing** -- employer policy matching, fair-chance job filtering, expungement eligibility screening (Alabama Act 2021-507)

### AI & Intelligence
- [x] **Multi-provider LLM** -- supports Anthropic Claude, OpenAI, and Google Gemini with automatic fallback to mock provider
- [x] **Barrier intelligence chat** -- SSE streaming AI chat with RAG-powered context, topic guardrails, and response caching
- [x] **RAG knowledge base** -- FAISS vector store built from Montgomery resource data, hybrid retrieval combining barrier graph traversal with vector search
- [x] **Barrier graph** -- directed acyclic graph modeling causal relationships between barriers; identifies root barriers and prioritizes interventions
- [x] **AI narrative** -- LLM generates a personalized "Monday Morning" summary; template-based fallback when API is unavailable

### Jobs & Resources
- [x] **Job aggregation** -- three sources: BrightData dataset crawls (Indeed/LinkedIn), JSearch API (RapidAPI), and Honest Jobs (fair-chance employer listings)
- [x] **Job filters and sort** -- filter by barrier type, transit accessibility, industry, fair-chance status; sort by PVS relevance
- [x] **Benefits eligibility screening** -- automated screening for 7 Alabama programs: SNAP, TANF, Medicaid, ALL Kids, Childcare Subsidy, Section 8, LIHEAP
- [x] **findhelp.org integration** -- barrier-specific deep links to findhelp.org resource directories for Montgomery
- [x] **Resource affinity routing** -- specialized resources (MATS, DHR, MRWTC) claim their designated barrier card; career center moved to next steps
- [x] **Resource health decay** -- feedback drives HEALTHY > WATCH > FLAGGED > HIDDEN status; HIDDEN resources filtered from matching

### Plan & Export
- [x] **Career Center Ready Package** -- two-part PDF: staff summary (barriers, WIOA, next steps) and resident action plan (document checklist, what to say, what to expect)
- [x] **WIOA eligibility screening** -- automated screening for Adult Program, Supportive Services, Individual Training Accounts, and Dislocated Worker
- [x] **PDF export** -- html2pdf.js with barriers, job matches, next steps, credit info, and QR code linking to feedback form
- [x] **Email export** -- EmailJS sends plan summary to the resident's inbox
- [x] **Comparison view** -- "Today vs. In 3 Months" side-by-side projection
- [x] **Benefits cliff chart** -- visual wage-step chart showing net income trajectory and cliff severity

### Feedback & Quality
- [x] **Resource feedback** -- thumbs up/down on barrier card resources with optimistic UI updates
- [x] **Post-visit feedback** -- QR code in PDF links to `/feedback/[token]` form; token-authenticated, one submission per session
- [x] **PII-safe audit logging** -- JSONL audit trail for LLM interactions with hashed session IDs; no user content logged

### Security
- [x] **Rate limiting** -- per-endpoint limits on all route groups (assessment, jobs, plan, credit, feedback, AI chat)
- [x] **Production validators** -- Pydantic model validators reject default secrets, weak admin keys, and localhost CORS in production
- [x] **Security headers** -- backend `SecurityHeadersMiddleware` + frontend CSP, X-Frame-Options, nosniff, referrer policy
- [x] **Input sanitization** -- `safeHref` blocks javascript:/data: URLs, zip code regex validation, prompt injection defense via XML tag wrapping
- [x] **SSRF prevention** -- URL allowlisting on external API calls
- [x] **Timing-safe auth** -- `hmac.compare_digest` for admin key comparison

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15 (App Router), React, Tailwind CSS, shadcn/ui, TanStack Query |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), SQLite via aiosqlite |
| AI | Claude, OpenAI, Gemini (multi-provider with auto-fallback) |
| RAG | FAISS vector store + barrier graph traversal |
| PDF | html2pdf.js + qrcode.react |
| Jobs | BrightData Datasets API v3, JSearch (RapidAPI), Honest Jobs |
| Credit | Sibling microservice proxy |
| Email | EmailJS |
| Testing | pytest (1,391 tests) + Vitest (417 tests) |

---

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Optional: add API keys
uvicorn app.main:app --reload
# Runs at http://localhost:8000

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
# Runs at http://localhost:3000
```

The SQLite database and Montgomery seed data (resources, transit routes, barrier graph, employer policies) are created automatically on first startup. No API keys are required for the core assessment and matching pipeline.

### Docker Compose

```bash
docker compose up --build
```

Backend at :8000, frontend at :3000. SQLite data persisted via Docker volume.

Full setup instructions: [`docs/setup.md`](docs/setup.md)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/assessment/` | Submit assessment, create session, run matching pipeline |
| GET | `/api/plan/{session_id}` | Retrieve existing plan |
| POST | `/api/plan/{session_id}/generate` | Generate AI narrative |
| POST | `/api/plan/{session_id}/refresh` | Re-run matching pipeline with stored profile |
| GET | `/api/plan/{session_id}/career-center` | Career Center Ready Package |
| POST | `/api/credit/assess` | Proxy to credit microservice |
| GET | `/api/jobs/` | Aggregated job listings with filters (barriers, transit, industry, fair-chance) |
| GET | `/api/jobs/{job_id}` | Single job detail with enriched info |
| POST | `/api/feedback/resource` | Resource helpfulness feedback |
| GET | `/api/feedback/validate/{token}` | Validate feedback token |
| POST | `/api/feedback/visit` | Post-visit feedback submission |
| POST | `/api/barrier-intel/chat` | AI barrier intelligence chat (SSE streaming) |
| POST | `/api/barrier-intel/reindex` | Force rebuild RAG index (admin) |
| POST | `/api/brightdata/crawl` | Trigger job crawl (admin) |
| GET | `/api/brightdata/status/{snapshot_id}` | Check crawl status (admin) |
| POST | `/api/brightdata/precrawl` | Pre-populate Montgomery jobs (admin) |
| GET | `/health` | Health check with version |

Full API documentation with curl examples: [`docs/api.md`](docs/api.md)

---

## Frontend Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing page with hero, how-it-works, Montgomery stats |
| `/assess` | Multi-step wizard (basic info, barriers, credit, criminal record, benefits, industry, review) |
| `/plan` | Plan results: AI narrative, barrier cards, benefits eligibility, cliff chart, job matches, exports |
| `/credit` | Standalone credit assessment form |
| `/feedback/[token]` | Post-visit feedback form (linked via QR code in PDF export) |

---

## Environment Variables

All optional. The app runs with defaults (SQLite, no AI, no live jobs, no email).

### Backend (`backend/.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./montgowork.db` | Database connection |
| `ANTHROPIC_API_KEY` | (empty) | Anthropic Claude API |
| `OPENAI_API_KEY` | (empty) | OpenAI API |
| `GEMINI_API_KEY` | (empty) | Google Gemini API |
| `LLM_PROVIDER` | (auto-detect) | Force LLM provider: `anthropic`, `openai`, `gemini`, `mock` |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model identifier |
| `BRIGHTDATA_API_KEY` | (empty) | BrightData job crawling |
| `BRIGHTDATA_DATASET_ID` | (empty) | BrightData dataset |
| `JSEARCH_API_KEY` | (empty) | JSearch (RapidAPI) job search |
| `CREDIT_API_URL` | `http://localhost:8001` | Credit microservice |
| `CREDIT_API_KEY` | (empty) | Credit microservice auth |
| `ADMIN_API_KEY` | (empty) | Admin endpoint authentication |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
| `ENVIRONMENT` | `development` | Environment: `development`, `test`, `staging`, `production` |
| `AUDIT_LOG_PATH` | (empty) | JSONL audit log file path for LLM interactions |
| `AUDIT_HASH_SALT` | `montgowork-default-salt` | Salt for hashing session IDs in audit logs |
| `DATA_DIR` | (empty) | Custom path for seed data directory |
| `LOG_LEVEL` | `INFO` | Logging level |

### Frontend (`frontend/.env.local`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL |
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | (empty) | EmailJS service |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | (empty) | EmailJS template |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | (empty) | EmailJS key |

---

## Project Structure

```
montgowork/
  backend/
    app/
      ai/                  # Multi-provider LLM client, prompts, audit logging
      barrier_graph/       # Barrier DAG: schema, traversal, seed data
      barrier_intel/       # AI chat: SSE streaming, guardrails, caching
      core/                # Config, database, query layers, rate limiting
      health/              # Liveness, readiness, health endpoints
      integrations/
        brightdata/        # Job crawling: client, polling, cache, precrawl
        honestjobs/        # Fair-chance employer job listings
        jsearch/           # RapidAPI JSearch job search
      modules/
        benefits/          # Eligibility screener (7 programs), cliff calculator
        credit/            # Credit proxy types
        criminal/          # Record profile, expungement, employer policies, job filter
        data/              # Data utilities
        documents/         # Document handling
        feedback/          # Token generation, health decay, feedback types
        matching/          # Engine, PVS scoring, filters, affinity, WIOA,
                           # career center package, barrier priority
        resources/         # findhelp.org integration
      rag/                 # FAISS store, retrieval, corpus builder, ingestion
      routes/              # assessment, plan, jobs, credit, feedback,
                           # brightdata, barrier-intel, career-center
    tests/                 # 1,391 tests
  frontend/
    src/
      app/                 # Pages: assess, plan, credit, feedback/[token]
      components/
        layout/            # Header
        plan/              # MondayMorning, BarrierCardView, JobMatchCard,
                           # BenefitsEligibility, BenefitsCliffChart,
                           # JobFilters, ComparisonView, CreditResults,
                           # PlanExport, EmailExport, CareerCenterExport,
                           # FindhelpLink, EligibilityBadge
        ui/                # shadcn/ui primitives
        wizard/            # WizardShell, BarrierForm, CreditForm,
                           # CriminalRecordForm, BenefitsStep, IndustryForm
      lib/                 # API client, types, constants, findhelp
    __tests__/             # 417 tests
  data/                    # Montgomery seed data (JSON)
  docs/                    # API, architecture, setup, deployment, security, demo
  Dockerfile               # Backend container
  Dockerfile.frontend      # Frontend container
  docker-compose.yml       # Full stack orchestration
```

---

## Tests

```bash
# Backend (1,391 tests)
cd backend && python -m pytest tests/ -q

# Frontend (417 tests)
cd frontend && npx vitest run
```

---

## Deployment

- **Backend**: Railway with Docker (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md))
- **Frontend**: Vercel with `frontend/` as root directory
- **Docker Compose**: `docker compose up --build` for local or self-hosted

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [`docs/setup.md`](docs/setup.md) | Local development setup and troubleshooting |
| [`docs/api.md`](docs/api.md) | Full API reference with curl examples |
| [`docs/architecture.md`](docs/architecture.md) | System architecture, schema, scoring algorithm, known limitations |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security posture, threat model, resolved findings |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Railway + Vercel deployment guides |
| [`docs/demo-script.md`](docs/demo-script.md) | 3-minute demo walkthrough (Maria persona) |
| [`ROADMAP.md`](ROADMAP.md) | Feature roadmap and known gaps |

---

## Built For

**Worldwide Vibes Hackathon** -- March 2026

---

## License

MIT
