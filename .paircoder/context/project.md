# Project Context

## What Is This Project?

**Project:** MontGoWork
**Primary Goal:** Give a Montgomery resident a clear, actionable path from "I can't get a job" to employment by connecting barrier assessment, credit building tools, local job matching, and community resources into a personalized re-entry plan.

## Repository Structure

```
montgowork/
├── .paircoder/              # PairCoder system files
│   ├── config.yaml          # Project configuration
│   ├── capabilities.yaml    # LLM capability manifest
│   ├── context/             # Project memory (project.md, state.md, workflow.md)
│   ├── plans/               # Plan files (11 plans, all complete)
│   └── tasks/               # Task files (68 tasks across 11 sprints)
├── .claude/                 # Claude Code integration
│   ├── agents/              # Custom agent definitions
│   ├── skills/              # Model-invoked skills
│   └── settings.json        # Hooks configuration
├── backend/                 # FastAPI backend
│   ├── app/                 # Application source
│   │   ├── core/            # Config, database, queries
│   │   ├── routes/          # API endpoints
│   │   ├── modules/         # Matching engine, credit types
│   │   ├── ai/              # Claude API client + prompts
│   │   ├── integrations/    # BrightData web scraping
│   │   └── health/          # Health check endpoints
│   ├── data/                # Montgomery seed data (JSON)
│   └── tests/               # pytest test suite (279 tests)
├── frontend/                # Next.js 15 frontend
│   └── src/
│       ├── app/             # Pages (landing, assess, plan, credit)
│       ├── components/      # UI components (wizard, plan, shared)
│       └── lib/             # API client, types, constants
├── docs/                    # Documentation
│   ├── api.md               # API reference
│   ├── architecture.md      # System architecture
│   ├── demo-script.md       # 3-minute demo walkthrough
│   ├── DEPLOYMENT.md        # Deployment guide
│   └── setup.md             # Local setup guide
├── Dockerfile               # Backend container
├── Dockerfile.frontend      # Frontend container
└── docker-compose.yml       # Demo deployment
```

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / Uvicorn
- **Frontend:** Next.js 15 (App Router) / React / TypeScript / Tailwind CSS / shadcn/ui
- **Database:** SQLite (async via aiosqlite + SQLAlchemy)
- **AI:** Anthropic Claude API (narrative generation)
- **State Management:** TanStack React Query
- **Testing:** pytest (279 backend tests) / Vitest (82 frontend tests)
- **External Services:** BrightData (job scraping), Credit Microservice, EmailJS

## Key Constraints

| Constraint | Requirement |
|------------|-------------|
| **Architecture** | Max 400 lines/file, 50 lines/function, 12 functions/file, 20 imports/file |
| **Testing** | TDD required; all tests must pass before task completion |
| **Security** | No hardcoded keys; session expiry enforced; rate limiting on assessment |
| **Dependencies** | All Python deps pinned to exact versions |
| **Secrets** | Never commit .env files or credentials |

## Architecture Principles

1. **TDD** — Write failing tests before implementation
2. **Arch Constraints** — Run `bpsai-pair arch check` before completing code tasks
3. **Graceful Degradation** — App works without optional services (Claude, BrightData, Credit API)
4. **Montgomery-Specific** — Resources, transit, employers seeded from local data

## How to Work Here

1. Read `.paircoder/context/state.md` for current plan/task status
2. Check `.paircoder/capabilities.yaml` to understand available actions
3. Follow the active skill for structured work
4. Update `state.md` after completing significant work

## Key Files

| File | Purpose |
|------|---------|
| `.paircoder/config.yaml` | Project configuration |
| `.paircoder/capabilities.yaml` | What LLMs can do here |
| `.paircoder/context/state.md` | Current status and active work |
| `backend/app/core/config.py` | Environment variable definitions |
| `backend/app/modules/matching/engine.py` | Core matching pipeline |
| `frontend/src/app/assess/page.tsx` | Assessment wizard |
| `frontend/src/app/plan/page.tsx` | Plan results page |
