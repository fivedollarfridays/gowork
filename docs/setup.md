# Setup Guide

Get MontGoWork running locally in under 2 minutes.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your API keys (see below)
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. The SQLite database and seed data (resources, transit routes) are created automatically on first startup.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Frontend runs at http://localhost:3000.

Open http://localhost:3000 in your browser. You should see the MontGoWork landing page.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description | Default / Example |
|----------|----------|-------------|-------------------|
| `ENVIRONMENT` | No | Runtime environment | `development` |
| `DATABASE_URL` | No | SQLite connection string | `sqlite+aiosqlite:///./montgowork.db` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins | `http://localhost:3000` |
| `ANTHROPIC_API_KEY` | No | Claude API key for AI narrative generation | `sk-ant-...` |
| `CREDIT_API_URL` | No | URL to credit assessment microservice | `http://localhost:8001` |
| `CREDIT_API_KEY` | No | API key for credit microservice | `montgowork-dev` |
| `BRIGHTDATA_API_KEY` | No | BrightData API key for live job crawling | (empty) |
| `BRIGHTDATA_DATASET_ID` | No | BrightData dataset ID for job crawling | (empty) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description | Default / Example |
|----------|----------|-------------|-------------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | No | EmailJS service ID for email export | (empty) |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | No | EmailJS template ID for email export | (empty) |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | No | EmailJS public key for email export | (empty) |

None of the backend variables are strictly required. The app runs with defaults (SQLite, no AI narratives, no live jobs). Add API keys to enable optional features.

## Database

SQLite is used. No database server needed.

- The database file (`montgowork.db`) is created automatically on first startup.
- Tables are created via DDL on startup.
- Seed data (career centers, childcare providers, community resources, training programs, transit routes) loads automatically on first run from JSON files in `data/`.

To reset the database, delete `backend/montgowork.db` and restart the server.

## Optional Services

All optional. The core assessment and matching pipeline works without any of these.

**Claude API** -- Set `ANTHROPIC_API_KEY` to enable AI-generated narrative summaries in the plan view. Without it, the "Generate AI Summary" button is hidden.

**Credit Microservice** -- A sibling microservice for credit assessment. Set `CREDIT_API_URL` and `CREDIT_API_KEY` to enable the credit step in the assessment wizard. Without it, the credit step is skipped.

**BrightData** -- Set `BRIGHTDATA_API_KEY` and `BRIGHTDATA_DATASET_ID` to enable live job crawling from Indeed/LinkedIn. Without them, job matches come from the seed database only.

**EmailJS** -- Set all three `NEXT_PUBLIC_EMAILJS_*` variables to enable the "Email My Plan" button. Without them, the email export button is hidden.

## Running Tests

### Backend

```bash
cd backend
python -m pytest tests/ -q
```

235 tests, 100% coverage.

### Frontend

```bash
cd frontend
npx vitest run
```

58 tests.

## Troubleshooting

**Port 8000 already in use** -- Another service is using port 8000. Either stop it or run uvicorn on a different port:
```bash
uvicorn app.main:app --reload --port 8002
```
Update `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to match.

**Port 3000 already in use** -- Next.js will prompt you to use another port automatically, or run:
```bash
npm run dev -- --port 3001
```

**ModuleNotFoundError on backend startup** -- You are not in the virtual environment. Run `source .venv/bin/activate` from the `backend/` directory.

**CORS errors in browser console** -- The backend `CORS_ORIGINS` does not include your frontend URL. Update `CORS_ORIGINS` in `backend/.env` to match (e.g., `http://localhost:3001` if you changed the frontend port).

**Database errors after pulling new code** -- The schema may have changed. Delete `backend/montgowork.db` and restart the server to recreate it.

**Frontend build errors after pulling** -- Run `npm install` in `frontend/` to pick up new dependencies.

**"Generate AI Summary" button missing** -- `ANTHROPIC_API_KEY` is not set. This is expected if you do not have a Claude API key.

**Credit step not appearing in wizard** -- The credit microservice is not running or `CREDIT_API_URL` is not configured. The credit step is optional.
