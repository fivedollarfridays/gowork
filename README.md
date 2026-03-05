# MontGoWork -- Workforce Navigator for Montgomery, Alabama

> Helping residents overcome the real barriers between them and employment.

MontGoWork is a full-stack workforce navigation tool built for Montgomery, Alabama. A resident completes a barrier assessment (credit, transportation, childcare, housing, health, training, criminal record), and the system generates a personalized action plan: matched local resources ranked by a 5-factor scoring engine, filtered job listings, credit repair guidance from a sibling microservice, and an AI-generated narrative summary powered by Claude. The result is a printable PDF or emailable plan the resident can take to a career center on Monday morning.

---

## Features

- [x] **Multi-step assessment wizard** -- ZIP validation, barrier selection, work history, and conditional credit self-assessment form
- [x] **7 barrier types** -- credit, transportation, childcare, housing, health, training, criminal record
- [x] **5-factor scoring engine** -- barrier alignment (40%), proximity (20%), transit (15%), schedule (15%), industry (10%)
- [x] **Matching engine** -- `generate_plan()` orchestrator queries resources, ranks them, builds barrier cards with action steps, and filters jobs
- [x] **Credit integration** -- proxy to sibling microservice at `/v1/assess/simple`; FICO score, readiness score, dispute pathway, and product eligibility returned to frontend
- [x] **BrightData live jobs** -- trigger crawls, poll status, auto-cache results to SQLite; precrawl endpoint for seeding Montgomery listings
- [x] **AI narrative** -- Claude API generates a personalized plan summary; template-based fallback when API is unavailable
- [x] **PDF export** -- client-side PDF generation via html2pdf.js with styled barriers, job matches, next steps, and credit info
- [x] **Email export** -- EmailJS integration sends plan summary, barriers, jobs, and next steps to the resident's inbox
- [x] **Comparison view** -- "Today vs. In 3 Months" side-by-side projection of barriers, job eligibility, credit status, and transit access
- [x] **Error boundary** -- React class component catches render errors with retry and start-over actions

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 18, shadcn/ui (Radix primitives), Tailwind CSS, TanStack Query |
| Backend | FastAPI, Python 3.11+, SQLAlchemy (async), SQLite via aiosqlite |
| AI | Claude API via Anthropic SDK (`anthropic>=0.40.0`) |
| Credit | Sibling microservice proxied at `/api/credit/assess` to `/v1/assess/simple` |
| Jobs | BrightData Web Scraper API -- trigger, poll, and cache job listings |
| PDF | html2pdf.js (client-side generation) |
| Email | EmailJS (`@emailjs/browser`) |
| Testing | pytest -- 235 tests, 100% backend coverage; Vitest -- 58 tests, frontend components |

---

## Quick Start

Full setup instructions are in [`docs/setup.md`](docs/setup.md). The short version:

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

You will need a `.env` file in `backend/` with `ANTHROPIC_API_KEY`, `CREDIT_API_URL`, `CREDIT_API_KEY`, `BRIGHTDATA_API_KEY`, and `BRIGHTDATA_DATASET_ID`. The frontend optionally uses `NEXT_PUBLIC_EMAILJS_SERVICE_ID`, `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID`, and `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` for email export.

---

## Architecture

The backend is a FastAPI application with four route modules (`assessment`, `plan`, `jobs`, `credit`, `brightdata`) and a matching engine package (`engine.py`, `scoring.py`, `filters.py`, `types.py`). The frontend is a Next.js 15 app with a wizard-based assessment flow (`/assess`), a plan results page (`/plan`), and a standalone credit page (`/credit`). The assessment route creates a session, runs the matching pipeline, and returns a plan; the plan route retrieves it and triggers AI narrative generation. See [`docs/architecture.md`](docs/architecture.md) for full architecture documentation.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/assessment/` | Submit barrier form, create session, run matching pipeline |
| GET | `/api/plan/{session_id}` | Retrieve existing plan for a session |
| POST | `/api/plan/{session_id}/generate` | Generate AI narrative for a plan |
| GET | `/api/jobs/` | List jobs with barrier, transit, and industry filters |
| GET | `/api/jobs/{job_id}` | Get single job with transit info and application steps |
| POST | `/api/credit/assess` | Proxy to credit assessment microservice |
| POST | `/api/brightdata/crawl` | Trigger a BrightData crawl job |
| GET | `/api/brightdata/status/{snapshot_id}` | Check crawl status, auto-cache results |
| POST | `/api/brightdata/precrawl` | Pre-populate Montgomery job listings |

See [`docs/api.md`](docs/api.md) for full API documentation with curl examples.

---

## Screenshots

Coming soon.

---

## Built For

**World Wide Vibes Hackathon** -- March 5-9, 2026

---

## License

MIT
