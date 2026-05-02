# Handoff — HackFW 2026 Submission-Eve Remediation

**Branch:** `fix/montgomery-purge-fw-seeds`
**Status:** Tier 1 + Tier 2 work landed. Three smaller fixes + deploy left for tonight, plus a `/pc-plan` sprint for the deeper cleanup.

---

## What's already done on this branch

| Layer | Result |
|-------|--------|
| Data | 8 root `data/*.json` files moved → `data/cities/montgomery/`. 8 matching FW seed files created at `data/cities/fort-worth/`. Loader (`backend/app/core/seed_helpers.py`) no longer falls back to `/data/` root — per-city only. |
| Backend AI prompts | 5 hardcoded MGM refs purged in `ai/client.py`, `ai/providers.py`, `barrier_intel/prompts.py`, `barrier_intel/guardrails.py`. New retained module `backend/app/cities/montgomery/prompts.py` holds the AL literals. |
| Frontend | Chapter 8 city rotation flipped to FW (`en.json`, `es.json`, `Chapter08FindYourPath.tsx`, `Ch08Wordmark.tsx`). |
| Tests | Backend 4132/4136 pass (2 unrelated pre-existing fails). Frontend `tsc --noEmit` + `npm run lint` clean. |

---

## Your local setup (Dallas — no Qwen access)

You don't have rig in Dallas, and exposing rig's Ollama publicly turned into a sudo-required pain. **Use Anthropic Claude Haiku instead.** It's faster than Qwen anyway (~3s vs ~107s) and removes rig as a dependency.

### One-time

1. Get a free Anthropic API key: https://console.anthropic.com/ — $5 free credit on signup, way more than enough for dev + judging.

2. Pull and set up:
   ```bash
   git fetch origin
   git checkout fix/montgomery-purge-fw-seeds
   cd backend && pip install -e . # or whatever your venv setup is
   cd ../frontend && npm install
   ```

3. Create `backend/.env` (it's gitignored — won't conflict):
   ```bash
   ENVIRONMENT=development
   DATABASE_URL=sqlite+aiosqlite:///./montgowork.db
   CITY=fort-worth
   ADMIN_API_KEY=dev-admin-key-local
   AUDIT_HASH_SALT=dev-salt-local
   CORS_ORIGINS=http://localhost:3000

   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-...your-key-here...
   CLAUDE_MODEL=claude-haiku-4-5-20251001
   ```

4. Create `frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1IjoiamRvZ3NoYXduIiwiYSI6ImNtb2pndnozOTBjdTQycW9kOHpsM2ZtMjIifQ.Nb6SByXgNlHWIh7wHefDqQ
   ```

5. Run:
   ```bash
   # Terminal 1
   cd backend && CITY=fort-worth uvicorn app.main:app --reload --port 8000
   # Terminal 2
   cd frontend && npm run dev
   ```

---

## Tonight's punch list (~1 hour total)

### 1. `eligibility.py:37` `"OneAlabama"` literal (5 min)

```python
# backend/app/modules/resources/eligibility.py
# Line 37 currently has:
#   "OneAlabama": {"type": "open"},
# Replace with city-aware routing:
```

Pattern from the AI-prompt agent: lazy-import from `app/cities/montgomery/prompts.py` (which we already created) for AL, define a TX equivalent for FW (`"Tarrant County 211"` is a good FW analog).

### 2. Rebuild the FAISS RAG index (15-30 min)

The actual leak source for "Run 2" of the LLM output was `backend/data/rag_index/metadata.json` — built from the OLD root-level Montgomery data. Now that we've split data per-city, rebuild against `data/cities/fort-worth/`:

```bash
# Find the build script — likely one of:
ls backend/scripts/build_rag* backend/scripts/index*.py 2>/dev/null
grep -rn "FAISS\|build_index\|rag_index" backend/scripts/ backend/app/rag/ 2>/dev/null

# Run it with CITY=fort-worth pointing at the new seed files.
# Verify after:
python3 -c "import json; d = json.load(open('backend/data/rag_index/metadata.json')); leaks = [r for r in d if 'Montgomery' in str(r) or 'OneAlabama' in str(r)]; print(f'leaks: {len(leaks)}')"
# Should print 0.
```

### 3. E2E verification (3 runs, no Montgomery)

```bash
cat > /tmp/carlos.json <<'EOF'
{
  "zip_code": "76119",
  "employment_status": "unemployed",
  "barriers": {"credit": true, "transportation": true, "childcare": true, "criminal_record": true, "housing": false, "health": false, "training": false},
  "work_history": "4 years warehouse at Amazon FC.",
  "target_industries": ["logistics"],
  "has_vehicle": false,
  "resume_text": "Carlos Martinez. Fort Worth, TX 76119.",
  "certifications": ["OSHA Forklift"]
}
EOF

for i in 1 2 3; do
  echo "=== Run $i ==="
  RESP=$(curl -s -X POST http://localhost:8000/api/assessment/ -H "Content-Type: application/json" -d @/tmp/carlos.json)
  S=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['session_id'])")
  T=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['feedback_token'])")
  curl -s -X POST "http://localhost:8000/api/plan/$S/generate?token=$T" -H "Content-Type: application/json" -d '{}' \
    | python3 -c "import sys,json;d=json.load(sys.stdin);s=d.get('summary','');print(s[:300]);print();leaks=[w for w in ['Montgomery','Alabama','Carter Hill','334-','OneAlabama'] if w in s];print('LEAKS:',leaks)"
done
```

All 3 runs must show `LEAKS: []` and contain "Workforce Solutions" / "Fort Worth".

### 4. Deploy (30-60 min)

**Railway (backend):**
- New project from GitHub `fivedollarfridays/montgowork`
- Root directory: `/` (Dockerfile is at repo root)
- Healthcheck path: `/health/live`
- Variables (Raw Editor):
  ```
  ENVIRONMENT=production
  DATABASE_URL=sqlite+aiosqlite:////tmp/montgowork.db
  CITY=fort-worth
  ADMIN_API_KEY=<generate fresh>
  AUDIT_HASH_SALT=<generate fresh>
  CORS_ORIGINS=https://gowork.city,https://www.gowork.city
  LLM_PROVIDER=anthropic
  ANTHROPIC_API_KEY=sk-ant-...
  CLAUDE_MODEL=claude-haiku-4-5-20251001
  FEATURE_EMAIL_SEND_ENABLED=false
  ENABLE_AI_GENERATION=true
  ```
- Generate Domain → copy URL.

**The SQLite write-permission gotcha is already handled** by the `////tmp/` path above — that's what bit us in earlier deploys (non-root `appuser` can't write to `/app`).

**Vercel (frontend):**
- New project from GitHub repo
- Root directory: `frontend/`
- Env vars:
  ```
  NEXT_PUBLIC_API_URL=<Railway URL from above>
  NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1IjoiamRvZ3NoYXduIiwiYSI6ImNtb2pndnozOTBjdTQycW9kOHpsM2ZtMjIifQ.Nb6SByXgNlHWIh7wHefDqQ
  NEXT_PUBLIC_SITE_URL=https://gowork.city
  ```
- Settings → Domains → Add `gowork.city` and `www.gowork.city`. Vercel will show DNS records — apply at your registrar:
  - `A` at apex `gowork.city` → `76.76.21.21`
  - `CNAME` at `www` → `cname.vercel-dns.com`
  - `TXT` for verification (Vercel shows the value)
- SSL issues automatically.

Then update Railway `CORS_ORIGINS` to include the actual Vercel preview URL too.

---

## After tonight: `/pc-plan` sprint

The deeper architectural cleanup is sprint-scope, NOT submission-eve. Kevin and I scoped it as a `/pc-plan` candidate. Brief:

> **Sprint goal**: harden city-routing so no Fort Worth (or future-city) request can ever leak Montgomery data via fallback. Architecture-level fix, not patches.
>
> **Tasks**:
> 1. 23 hardcoded Python fallbacks (`matching/affinity.py`, `matching/career_center_package.py`, `matching/scoring.py` ZIP centroids, `matching/geo_router.py` defaults, `matching/barrier_cards.py`, `modules/resources/eligibility.py`, `modules/resources/findhelp.py`, `modules/benefits/application_data.py` 7-block, `barrier_intel/*`, `ai/client.py`) → all routed via city-config or moved into `app/cities/{city}/` retained modules.
> 2. Frontend `lib/city-constants.ts` AL branch + `lib/city-stats.ts` MONTGOMERY block → keep MGM as opt-in legacy via state param, FW as default everywhere.
> 3. FAISS index must be city-tagged at build time. Either rebuild per city (preferred) or add a city field to docs and filter at query time. Document the decision as an ADR.
> 4. Seed-loader-must-error-not-fallback (already implemented locally as part of the hotfix) — formalize as ADR + add a regression test.
> 5. Migrate the 50+ frontend test fixtures off Montgomery defaults to `useCityConfig` mocks (low priority — they're intentionally MGM-flavored regression coverage).
>
> **Out of scope**: any new feature work, any UI polish.

Run `/pc-plan` after submission lands. The branch should be merged to main first, then the sprint plan can target a clean baseline.

---

## Optional: progressive-enhancement upgrade pattern (~2 hrs, post-submission)

We discussed this with Kevin — the pattern where the deterministic plan renders instantly at submit, then a background `/generate` call streams in the AI-enhanced narrative with a "✨ AI ready — apply" toast. Frames the latency as a feature, not a bug. Probably worth doing as the first task after the cleanup sprint. See chat transcript for the full pitch.

---

## Quick health checks

```bash
# Stack
curl -s -o /dev/null -w "frontend %{http_code}\n" http://localhost:3000/
curl -s -o /dev/null -w "backend %{http_code}\n" http://localhost:8000/api/city

# LLM smoke (Haiku — should respond in ~3s)
curl -s -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":50,"messages":[{"role":"user","content":"Say OK."}]}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['content'][0]['text'])"

# Backend tests, FW path
cd backend && CITY=fort-worth .venv/bin/pytest tests/ -x -q --tb=short 2>&1 | tail -10
```
