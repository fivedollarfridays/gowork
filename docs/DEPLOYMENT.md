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

---

## Deploy to Railway (Backend)

Railway deploys the backend as a Docker container from the project root `Dockerfile`.

### Setup

1. Create a new project on [Railway](https://railway.app)
2. Connect your GitHub repository (`fivedollarfridays/montgowork`)
3. Railway auto-detects the `Dockerfile` at the project root -- no build configuration needed
4. Set environment variables (see table below)
5. Deploy

### Environment Variables

Configure these in the Railway service settings:

| Variable | Required | Value / Notes |
|----------|----------|---------------|
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:///./montgowork.db` (default works; for volume persistence use `sqlite+aiosqlite:////app/data/montgowork.db`) |
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI narrative generation |
| `BRIGHTDATA_API_KEY` | Yes | BrightData API key for live job crawling |
| `BRIGHTDATA_DATASET_ID` | Yes | Dataset ID from BrightData dashboard |
| `CORS_ORIGINS` | Yes | Set to your Vercel frontend URL (e.g. `https://montgowork.vercel.app`) |
| `CREDIT_API_URL` | Optional | Defaults to `http://localhost:8001` -- update if credit service is deployed separately |
| `CREDIT_API_KEY` | Optional | `montgowork-dev` for hackathon demo |
| `ENVIRONMENT` | No | Defaults to `development`; set to `production` to disable `/docs` and `/redoc` |
| `CLAUDE_MODEL` | No | Defaults to `claude-sonnet-4-20250514` |
| `LOG_LEVEL` | No | Defaults to `INFO` |
| `FEEDBACK_TOKEN_SECRET` | No | Defaults to `montgowork-feedback-v1` -- change in production |

### SQLite Persistence

By default, SQLite writes to the container filesystem, which is ephemeral. To persist data across deploys:

1. Add a Railway **Volume** mounted at `/app/data/`
2. Set `DATABASE_URL` to `sqlite+aiosqlite:////app/data/montgowork.db` (note the four slashes -- three for the SQLite prefix plus one for the absolute path)
3. The database and seed data are created automatically on first startup

SQLite with a volume is acceptable for the current single-instance scale. See `docs/architecture.md` for the PostgreSQL migration path if horizontal scaling is needed.

### Health Check

Configure Railway's health check to poll:

```
GET /health
```

Expected response (`200 OK`):

```json
{"status": "healthy", "version": "0.1.0", "uptime_seconds": 123.4}
```

Use `/health/ready` for a deeper check that includes database connectivity (returns `503` if the database is unreachable).

### Dockerfile Reference

The `Dockerfile` at the project root builds the backend:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

No custom build command or Procfile is needed.

---

## Deploy to Vercel (Frontend)

Vercel deploys the Next.js frontend directly from the repository.

### Setup

1. Import your GitHub repository on [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend/`
3. Vercel auto-detects Next.js -- no framework configuration needed
4. Set environment variables (see table below)
5. Deploy

### Environment Variables

| Variable | Required | Value / Notes |
|----------|----------|---------------|
| `NEXT_PUBLIC_API_URL` | Yes | Railway backend URL (e.g. `https://montgowork-production.up.railway.app`) |
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | No | EmailJS service ID for "Email My Plan" feature |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | No | EmailJS template ID |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | No | EmailJS public key |

### Build

Vercel runs `npm run build` automatically. No custom build command is needed.

### Preview Deployments

When GitHub integration is enabled, Vercel automatically deploys a unique preview URL for every pull request. This is useful for reviewing frontend changes before merging.

---

## Environment Variables Reference

Complete reference of all environment variables across backend and frontend.

### Backend

All backend variables are read by `backend/app/core/config.py` using Pydantic Settings. They can be set via environment variables or a `.env` file in the `backend/` directory.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `MontGoWork` | Application name (used in metadata) |
| `ENVIRONMENT` | No | `development` | Runtime environment; set `production` to disable `/docs` and `/redoc` |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./montgowork.db` | Async SQLite connection string |
| `ANTHROPIC_API_KEY` | Yes (for AI) | (empty) | Claude API key for AI narrative generation |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-20250514` | Claude model identifier |
| `BRIGHTDATA_API_KEY` | Yes (for jobs) | (empty) | BrightData API key for live job crawling |
| `BRIGHTDATA_DATASET_ID` | Yes (for jobs) | (empty) | BrightData dataset ID |
| `CREDIT_API_URL` | No | `http://localhost:8001` | Credit microservice base URL |
| `CREDIT_API_KEY` | No | (empty) | API key for credit microservice authentication |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `FEEDBACK_TOKEN_SECRET` | No | `montgowork-feedback-v1` | HMAC secret for feedback token generation; change in production |

### Frontend

Frontend variables are set in `frontend/.env.local` (local development) or in the Vercel dashboard (production). Variables prefixed with `NEXT_PUBLIC_` are embedded at build time and visible to the browser.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API base URL |
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | No | (empty) | EmailJS service ID for "Email My Plan" |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | No | (empty) | EmailJS template ID |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | No | (empty) | EmailJS public key |
