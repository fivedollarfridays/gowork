# MontGoWork -- Workforce Navigator for Montgomery, Alabama

> Helping residents overcome the real barriers between them and employment.

MontGoWork is a full-stack workforce navigation tool built for Montgomery, Alabama. A resident completes a barrier assessment (credit, transportation, childcare, housing, health, training, criminal record), and the system generates a personalized re-entry plan: matched local resources ranked by a 5-factor scoring engine, filtered job listings, WIOA eligibility screening, credit repair guidance, and an AI-generated narrative summary powered by Claude. The result is a printable PDF the resident takes to the Montgomery Career Center on Monday morning.

---

## Features

- [x] **Multi-step assessment wizard** -- ZIP validation (361xx), barrier selection with live severity badge, conditional credit self-assessment, work history
- [x] **7 barrier types** -- credit, transportation, childcare, housing, health, training, criminal record
- [x] **5-factor scoring engine** -- barrier alignment (40%), proximity (20%), transit (15%), schedule (15%), industry (10%)
- [x] **Resource affinity routing** -- specialized resources (MATS, DHR, MRWTC) claim their designated barrier card; career center moved to next steps
- [x] **Barrier priority ordering** -- childcare first, transportation second, training last; barrier cards and next steps follow this order
- [x] **Credit filtering** -- jobs split by severity: HIGH excludes all credit-check jobs, MEDIUM excludes finance/government, LOW applies no filter
- [x] **Three-bucket job display** -- Strong Matches, Possible Matches, After Credit Repair
- [x] **WIOA eligibility screening** -- automated screening for Adult Program, Supportive Services, and Individual Training Accounts
- [x] **Career Center Ready Package** -- two-part PDF: staff summary (barriers, WIOA, next steps) and resident action plan (document checklist, what to say, what to expect)
- [x] **AI narrative** -- Claude API generates a personalized "Monday Morning" summary; template-based fallback when API is unavailable
- [x] **Credit integration** -- proxy to sibling microservice; FICO score, readiness score, dispute pathway, and product eligibility
- [x] **BrightData live jobs** -- trigger crawls, poll with exponential backoff, auto-cache to SQLite; precrawl endpoint for seeding Montgomery listings
- [x] **PDF export** -- html2pdf.js with barriers, job matches, next steps, credit info, and QR code linking to feedback form
- [x] **Email export** -- EmailJS sends plan summary to the resident's inbox
- [x] **Resource feedback** -- thumbs up/down on barrier card resources with optimistic UI updates
- [x] **Post-visit feedback** -- QR code in PDF links to `/feedback/[token]` form; token-authenticated, one submission per session
- [x] **Resource health decay** -- feedback drives HEALTHY > WATCH > FLAGGED > HIDDEN status; HIDDEN resources filtered from matching
- [x] **Comparison view** -- "Today vs. In 3 Months" side-by-side projection
- [x] **Error boundary** -- catches render errors with retry and start-over actions
- [x] **Rate limiting** -- assessment (10 req/60s) and feedback (20 req/60s) endpoints

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15 (App Router), React, Tailwind CSS, shadcn/ui, TanStack Query |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), SQLite via aiosqlite |
| AI | Claude API via Anthropic SDK |
| PDF | html2pdf.js + qrcode.react |
| Jobs | BrightData Datasets API v3 |
| Credit | Sibling microservice proxy |
| Email | EmailJS |
| Testing | pytest (449 tests) + Vitest (141 tests) |

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

The SQLite database and Montgomery seed data (resources, transit routes, job listings) are created automatically on first startup. No API keys are required for the core assessment and matching pipeline.

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
| GET | `/api/plan/{session_id}/career-center` | Career Center Ready Package |
| POST | `/api/credit/assess` | Proxy to credit microservice |
| GET | `/api/jobs/` | Job listings with barrier/transit/industry filters |
| GET | `/api/jobs/{job_id}` | Single job detail |
| POST | `/api/feedback/resource` | Resource helpfulness feedback |
| GET | `/api/feedback/validate/{token}` | Validate feedback token |
| POST | `/api/feedback/visit` | Post-visit feedback submission |
| POST | `/api/brightdata/crawl` | Trigger job crawl |
| GET | `/api/brightdata/status/{snapshot_id}` | Check crawl status |
| POST | `/api/brightdata/precrawl` | Pre-populate Montgomery jobs |
| GET | `/health` | Health check with version |

Full API documentation with curl examples: [`docs/api.md`](docs/api.md)

---

## Frontend Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing page with hero, how-it-works, Montgomery stats |
| `/assess` | Multi-step assessment wizard (basic info, barriers, credit, review) |
| `/plan` | Plan results: AI narrative, barrier cards, job buckets, credit results, exports |
| `/credit` | Standalone credit assessment form |
| `/feedback/[token]` | Post-visit feedback form (linked via QR code in PDF export) |

---

## Environment Variables

All optional. The app runs with defaults (SQLite, no AI, no live jobs, no email).

### Backend (`backend/.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./montgowork.db` | Database connection |
| `ANTHROPIC_API_KEY` | (empty) | Claude API for AI narratives |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model |
| `BRIGHTDATA_API_KEY` | (empty) | BrightData job crawling |
| `BRIGHTDATA_DATASET_ID` | (empty) | BrightData dataset |
| `CREDIT_API_URL` | `http://localhost:8001` | Credit microservice |
| `CREDIT_API_KEY` | (empty) | Credit microservice auth |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |
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
      ai/                  # Claude API client, prompts, fallback narrative
      core/                # Config, database, query layers
      health/              # Liveness, readiness, health endpoints
      integrations/
        brightdata/        # Job crawling: client, polling, cache, precrawl
      modules/
        credit/            # Credit proxy types
        feedback/          # Token generation, health decay, feedback types
        matching/          # Matching engine, scoring, filters, affinity routing,
                           # barrier priority, WIOA screener, career center package
      routes/              # assessment, plan, jobs, credit, feedback, brightdata
    tests/                 # 449 tests
  frontend/
    src/
      app/                 # Pages: assess, plan, credit, feedback/[token]
      components/
        layout/            # Header
        plan/              # MondayMorning, BarrierCardView, JobMatchCard,
                           # ComparisonView, CreditResults, PlanExport,
                           # EmailExport, CareerCenterExport, ResourceFeedback
        ui/                # shadcn/ui primitives
        wizard/            # WizardShell, BarrierForm, CreditForm
      lib/                 # API client, types, constants
  data/                    # Montgomery seed data (JSON)
  docs/                    # API, architecture, setup, deployment, demo script
  Dockerfile               # Backend container
  Dockerfile.frontend      # Frontend container
  docker-compose.yml       # Full stack orchestration
```

---

## Tests

```bash
# Backend (449 tests)
cd backend && python -m pytest tests/ -q

# Frontend (141 tests)
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
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Railway + Vercel deployment guides |
| [`docs/demo-script.md`](docs/demo-script.md) | 3-minute demo walkthrough (Maria persona) |
| [`ROADMAP.md`](ROADMAP.md) | Feature roadmap and known gaps |

---

## Built For

**Five Dollar Fridays Hackathon** -- March 2026

---

## License

MIT
