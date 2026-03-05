# Deployment Guide

How to deploy MontGoWork for a demo or staging environment.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./montgowork.db` | SQLite connection string |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `ANTHROPIC_API_KEY` | No | (empty) | Claude API key for AI narrative generation |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-20250514` | Claude model to use |
| `CREDIT_API_URL` | No | `http://localhost:8001` | Credit microservice base URL |
| `CREDIT_API_KEY` | No | (empty) | API key for credit microservice |
| `BRIGHTDATA_API_KEY` | No | (empty) | BrightData API key for live job crawling |
| `BRIGHTDATA_DATASET_ID` | No | (empty) | BrightData dataset ID |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | No | (empty) | EmailJS service ID |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | No | (empty) | EmailJS template ID |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | No | (empty) | EmailJS public key |

No backend variables are strictly required. The app runs with defaults (SQLite, no AI, no live jobs). Add API keys to enable optional features.

---

## Startup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The database is created and seeded automatically on first startup. No manual seed step is needed.

For development with auto-reload:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run build
npm start
```

For development:

```bash
npm run dev
```

---

## Health Checks

### Liveness

```bash
curl http://localhost:8000/health/live
# {"alive": true, "uptime_seconds": 123.4}
```

### Readiness (includes database connectivity)

```bash
curl http://localhost:8000/health/ready
# {"ready": true, "checks": [{"name": "database", "status": "up", ...}]}
```

Returns `503` if the database is unreachable.

### General Health

```bash
curl http://localhost:8000/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 123.4}
```

---

## Startup Warnings

The backend logs warnings at startup if optional services are not configured:

- `ANTHROPIC_API_KEY` not set: AI narrative generation will use fallback templates
- `BRIGHTDATA_API_KEY` not set: Live job crawling disabled
- `CREDIT_API_KEY` not set: Credit microservice proxy may not authenticate

These are warnings, not errors. The core assessment and matching pipeline works without any external services.

---

## Database

SQLite is used with no external database server required.

- **File location:** `backend/montgowork.db` (relative to working directory)
- **Auto-creation:** Tables created on startup via DDL
- **Auto-seeding:** Montgomery resources, transit routes loaded from `backend/data/*.json` on first run
- **Sessions:** Expire after 24 hours (enforced by query filter)
- **Reset:** Delete `montgowork.db` and restart to recreate

---

## Rate Limiting

The assessment endpoint (`POST /api/assessment/`) enforces a rate limit of 10 requests per minute per client IP. Exceeding this returns `429 Too Many Requests`.

---

## Optional Services

| Service | Env Vars | What It Enables |
|---------|----------|-----------------|
| Claude API | `ANTHROPIC_API_KEY` | AI-generated "Monday Morning" narrative summaries |
| Credit Microservice | `CREDIT_API_URL`, `CREDIT_API_KEY` | Credit barrier assessment step in wizard |
| BrightData | `BRIGHTDATA_API_KEY`, `BRIGHTDATA_DATASET_ID` | Live job crawling from Indeed/LinkedIn |
| EmailJS | `NEXT_PUBLIC_EMAILJS_*` (3 vars) | "Email My Plan" button on plan page |

All optional. The core flow (assessment, matching, plan generation) works without any of these.

---

## Verification

After startup, verify the deployment:

```bash
# Backend is running
curl http://localhost:8000/
# {"message": "MontGoWork API", "status": "running"}

# Database is ready
curl http://localhost:8000/health/ready
# {"ready": true, ...}

# Frontend is accessible
curl -s http://localhost:3000 | head -1
# <!DOCTYPE html>

# Submit a test assessment
curl -X POST http://localhost:8000/api/assessment/ \
  -H "Content-Type: application/json" \
  -d '{"zip_code":"36104","employment_status":"unemployed","barriers":{"credit":true},"work_history":"test"}'
# Returns 201 with session_id, profile, and plan
```
