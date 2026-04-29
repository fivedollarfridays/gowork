# GoWork

# What's standing between you and a job?

> **You shouldn't have to figure out the wall.
> We do the math, sequence the path, and hand you the plan.**
>
> *Workforce infrastructure for any American city.*

![GoWork — Chapter 02: Fort Worth Arrival](docs/press-kit/screenshots/ch2-fort-worth-arrival.png.placeholder)

---

## What it is

GoWork is an open-source workforce navigator that asks the question
nobody else asks. It walks the resident through real Fort Worth
geography — bus routes, county offices, fair-chance employers,
neighborhood ZIP boundaries — and renders the wall of barriers between
them and a job as a cinematic, scroll-driven Mapbox visualization with
a 3D barrier graph hovering above the city. Carlos, the protagonist
persona, is research-backed but not a real person: ZIP 76119, recently
released, no vehicle, 540 credit score, single father, four years
warehouse experience. The demographics, geography, and barriers are
real — the person is composite.

The reference deployment is Fort Worth, Texas. The framework — city
config + barrier graph DAG + Texas state modules + Trinity Metro GTFS
layer — is multi-city by architecture, not by branding. Montgomery,
Alabama is the second city demonstrated. The same pluggable city
framework renders both. **3,428 frontend tests + ~4,080 backend tests
(~7,500+ total)**, all green. Lighthouse performance floor 0.90 on
simulated 4G. WCAG AAA contrast everywhere. EN/ES parity. MIT
licensed.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/fivedollarfridays/montgowork.git
cd montgowork

# 2. Frontend
cd frontend
npm install
cp .env.local.example .env.local
# Required: NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...
# Get a free public token at https://account.mapbox.com/access-tokens/
npm run dev
# Wall renders at http://localhost:3000

# 3. Backend (separate terminal)
cd ../backend
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# API at http://localhost:8000
```

> **Mapbox token note.** When `NEXT_PUBLIC_MAPBOX_TOKEN` is unset, the
> Wall falls back to a static branded placeholder — useful for CI, but
> the cinematic render needs a real token. The token is checked at boot
> by `validateMapboxToken()` and probed against the CDN at runtime by
> `isMapboxAvailable()` (2-second timeout).

Full setup: [`docs/setup.md`](docs/setup.md).

---

## HackFW positioning

GoWork was built for HackFW 2026 (Reindustrialization track). The
reference deployment is Fort Worth; the framework ships ready for any
American city — Montgomery is the second city demonstrated. Carlos is
a research-backed persona, not a real person.

- **Track:** Reindustrialization (Convergent Technology / workforce
  augmentation)
- **Devpost:** see [`docs/devpost-submission.md`](docs/devpost-submission.md)
  for the form pre-fill
- **Demo:** see [`docs/submission-demo.md`](docs/submission-demo.md)
  for the live judges' walkthrough
- **Press kit:** see [`docs/press-kit.md`](docs/press-kit.md) for
  cinematic stills + media-ready stats
- **Editorial voice:** locked in [`docs/copy-thesis.md`](docs/copy-thesis.md)

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15.5.9, React, TypeScript, Tailwind, shadcn/ui |
| Map + 3D | Mapbox GL JS, react-map-gl, react-three-fiber, Three.js |
| Motion | framer-motion, OKLCH tokens, View Transitions API |
| Edge | Vercel Satori (`@vercel/og`) for per-chapter dynamic OG |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), SQLite (aiosqlite) |
| AI | Anthropic Claude, OpenAI, Google Gemini (multi-provider auto-fallback) |
| RAG | FAISS vector store + barrier graph DAG traversal |
| Jobs | BrightData Datasets API v3, JSearch (RapidAPI), Honest Jobs |
| PDF | html2pdf.js + qrcode.react |
| Email | EmailJS |

---

## Test coverage

| Suite | Count | Runner |
|---|---|---|
| Frontend (vitest) | 3,428 | `cd frontend && npx vitest run` |
| Backend (pytest, expanded) | ~4,080 | `cd backend && python -m pytest tests/ -q` |
| **Total** | **~7,500+** | |

The test suite is not afterthought coverage. Every feature started as a
failing test. The Mapbox chapter scaffold, barrier graph traversal,
benefits-cliff calculator, per-chapter OG image generator, View
Transitions polish, scroll-velocity motion-blur, idle ambient drift,
and the Spanish-parity re-skin all have deterministic tests because
the enforcement layer required it before any code shipped.

---

## Cities deployed

| City | State | Status |
|---|---|---|
| Fort Worth, TX | Reference deployment (HackFW 2026) | Production-ready |
| Montgomery, AL | Second city — same framework | Deployed |

Texas state-level modules (HHSC benefits screener, Article 55
expunction) are shared across Fort Worth and any future Texas city
(Dallas, Houston). Alabama state modules (7 Alabama programs, Act
2021-507 expungement) cover Montgomery + future Alabama cities.

---

## Built with

GoWork is the work of **Team PairCoder**, augmented by Claude (Anthropic)
in a multi-driver dispatch pattern: four parallel worktrees per phase,
each owning a constrained scope (life layers, edge states,
accessibility, maximization). SubagentStop hooks fed token telemetry
into a calibration engine that learned how long each driver class took
for each task class.

- **Lead:** Shawn Sanchez (Team PairCoder)
- **Co-developer / original creator:** Kevin Masterson
- **Augmented pair-programming:** Claude (Anthropic) — multi-driver dispatch
- **Map rendering:** Mapbox
- **Hosting:** Vercel (frontend) + Railway (backend)

The format is the innovation. Civic tech doesn't have its NYT
*Snow Fall* yet. We're shipping it.

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/copy-thesis.md`](docs/copy-thesis.md) | Locked editorial voice — single source of truth |
| [`docs/press-kit.md`](docs/press-kit.md) | Press kit with cinematic stills + stats |
| [`docs/devpost-submission.md`](docs/devpost-submission.md) | Devpost form pre-fill content |
| [`docs/submission-demo.md`](docs/submission-demo.md) | Live judges' demo script (Driver B) |
| [`docs/visual-rebirth-plan.md`](docs/visual-rebirth-plan.md) | The Wall plan + 12 life-layers |
| [`docs/setup.md`](docs/setup.md) | Local development setup |
| [`docs/api.md`](docs/api.md) | Backend API reference with curl examples |
| [`docs/architecture.md`](docs/architecture.md) | System architecture + scoring + known limits |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security posture + threat model |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Railway + Vercel deployment guides |
| [`docs/fw-dao-bounty-research.md`](docs/fw-dao-bounty-research.md) | FW DAO claim path investigation |
| [`ROADMAP.md`](ROADMAP.md) | Feature roadmap and known gaps |

---

## Demo URLs

- **Production:** _Driver C will fill on deploy._
- **Staging:** see [`docs/submission-demo.md`](docs/submission-demo.md)
- **Source:** https://github.com/fivedollarfridays/montgowork

---

## License

MIT — see [`LICENSE`](LICENSE).

The 7,500-test suite, the Wall, the barrier graph, the city framework,
the Spanish-parity re-skin, and every piece of the pipeline ship under
MIT. Take it. Run it in your city. Hand the plan to the worker on
Monday morning.

---

*Built for HackFW 2026. Made possible by Team PairCoder + Claude (Anthropic) + Mapbox + Vercel.
Worldwide Vibes Hackathon (March 2026 — 2nd place) was the prequel.*
