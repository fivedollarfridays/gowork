# GoWork — Press Kit

> **Workforce navigation infrastructure for any American city,
> demonstrated in Fort Worth.**

> **Tagline:** What's standing between you and a job?

> **Subhead:** You shouldn't have to figure out the wall. We do the
> math, sequence the path, and hand you the plan.

---

## One-liner

Open-source workforce navigator that turns a 2-hour career-center
intake into a 10-minute personalized plan, rendered as a cinematic
3D scrollytelling map of Fort Worth.

---

## Cinematic stills

The home page IS the press kit. The same Mapbox-driven scrollytelling
artifact that judges read also generates the cinematic stills below.
One asset, four uses (home page, README hero, press kit, submission
video).

| Frame | Source | File |
|---|---|---|
| Hero — Fort Worth overhead with locked thesis | Title sequence | ![](docs/press-kit/screenshots/hero-fort-worth-overhead.png.placeholder) |
| Chapter 02 — City arrival | Atmospheric flight to FW altitude | ![](docs/press-kit/screenshots/ch2-fort-worth-arrival.png.placeholder) |
| Chapter 06 — The Math (cliff calculator at Amazon DFW5) | Camera lands at Amazon FC | ![](docs/press-kit/screenshots/ch6-the-math.png.placeholder) |
| Chapter 07 — The Path (Carlos walks his GPS route) | Sequenced path-line draw | ![](docs/press-kit/screenshots/ch7-the-path.png.placeholder) |
| Chapter 08 — The Graph (3D barrier constellation) | Constellation hovers above FW | ![](docs/press-kit/screenshots/ch8-barrier-graph.png.placeholder) |
| Chapter 10 — Find your path (CTA close) | Camera back overhead | ![](docs/press-kit/screenshots/ch10-find-your-path.png.placeholder) |

> Driver B is the owner of the cinematic-still capture pass. Each
> file above either resolves to a real PNG or to a sibling
> `.placeholder` marker (Driver B replaces in-place). See
> [`docs/press-kit/screenshots/README.md`](docs/press-kit/screenshots/README.md)
> for the capture spec.

---

## Numbers (live)

| | |
|---|---|
| Frontend tests (vitest) | **3,428** |
| Backend tests (pytest, expanded) | **~4,080** |
| **Total tests, all green** | **~7,500+** |
| Cities deployed | 2 (Fort Worth + Montgomery) |
| Sprints completed | 17 (S1–S13 + W1–W4 visual rebirth) |
| Barrier types modeled | 7 |
| Alabama benefits programs screened | 7 (SNAP, TANF, Medicaid, ALL Kids, Childcare Subsidy, Section 8, LIHEAP) |
| Texas benefits programs (HHSC) | 7 |
| LLM providers (auto-fallback) | 3 (Claude, OpenAI, Gemini) |
| Job sources | 3 (BrightData, JSearch, Honest Jobs) |
| `/` First Load JS | 150 kB (bundle budget contract: < 200 kB) |
| Lighthouse performance floor | 0.90 on simulated 4G |
| WCAG contrast | AAA everywhere |
| License | MIT |

---

## What it actually does

**Barrier Assessment Wizard.** Multi-step guided assessment. ZIP
validation, resume upload, barrier selection (7 types), benefits data,
schedule constraints, industry preferences, review.

**Practical Value Score.** Jobs ranked by what actually matters: net
income after benefits impact (35%), proximity + transit access (25%),
schedule fit (20%), barrier compatibility (20%). Not "here are jobs in
your area." **Jobs you can get to, keep, and live on.**

**Benefits Cliff Detection.** Calculates net income at every wage
step. Shows exactly where a raise triggers a benefits drop that
leaves you worse off. Residents see the math before they accept an
offer.

**Criminal Record Routing.** Employer background-check policy
matching. Fair-chance employer filtering. Expungement eligibility
under Alabama Act 2021-507 (Montgomery) and Texas Article 55
expunction / nondisclosure (Fort Worth).

**AI Barrier Intelligence Chat.** Multi-provider LLM with RAG-powered
context from city-specific resource data. FAISS vector store +
barrier graph DAG traversal. Topic guardrails. SSE streaming.

**Career Center Ready Package.** Two-part printable PDF — staff
summary (barriers, WIOA, next steps) + resident action plan
(document checklist, what to say, what to expect). The resident walks
into the career center on Monday morning with everything staff need.

**The Wall (home page).** 10-chapter scroll-driven Mapbox
visualization. Carlos (research-backed persona) walking real Fort
Worth geography. 3D barrier constellation hovering above the city.
Per-chapter dynamic OG cards via Vercel Satori. EN/ES parity. View
Transitions API on the close CTA. WCAG AAA.

---

## Stack

| Layer | What |
|---|---|
| Frontend | Next.js 15.5.9, React, TypeScript, Tailwind, shadcn/ui |
| Map + 3D | Mapbox GL JS, react-map-gl, react-three-fiber, Three.js |
| Motion | framer-motion, OKLCH tokens, View Transitions API |
| Edge | Vercel Satori (`@vercel/og`) — per-chapter dynamic OG |
| Backend | FastAPI, Python 3.13, SQLAlchemy (async), SQLite |
| AI | Claude, OpenAI, Gemini (multi-provider auto-fallback) |
| RAG | FAISS vector store + barrier graph DAG traversal |
| Jobs | BrightData, JSearch, Honest Jobs |
| Hosting | Vercel (frontend) + Railway (backend) |

---

## Built with PairCoder

GoWork was built using PairCoder's enforcement workflow + a
multi-driver dispatch pattern: four parallel Claude-driven worktrees
per phase, each owning a constrained scope (life layers, edge states,
accessibility, maximization). SubagentStop hooks fed token telemetry
into a calibration engine that learned how long each driver class
took for each task class. The ~7,500-test suite isn't afterthought
coverage — every feature started as a failing test.

---

## The problem

Career centers see the same pattern every day. Someone walks in
needing a job, but it's never just about the job. No vehicle means no
commute. A criminal record means half the listings disqualify them
up front. The wrong job triggers a benefits cliff that leaves them
poorer than before.

Staff spend hours cross-referencing benefits thresholds, transit
routes, expungement eligibility, employer background-check policies,
and local resources — for one person at a time. Then the next person
walks in.

GoWork replaces that manual cross-referencing with a structured
pipeline. The resident gets a plan. The staff get a briefing. The
career center gets throughput.

---

## HackFW 2026

- **Track:** Reindustrialization (Convergent Technology / workforce
  augmentation)
- **Devpost:** `https://fwtx.devpost.com/`
- **Submission deadline:** May 2, 2026, 2:00 PM CDT
- **Repo:** https://github.com/fivedollarfridays/montgowork
- **Submission deliverables:** README + cinematic press kit + 3-4 min
  video + Devpost form pre-fill
  ([`docs/devpost-submission.md`](devpost-submission.md))

---

## Team

- **Shawn Sanchez** — Team PairCoder lead, project lead
- **Kevin Masterson** — Original creator, co-developer
- **Claude (Anthropic)** — Augmented pair-programming partner
  (multi-driver dispatch, all four parallel worktrees per phase)

---

## Repository

GitHub: https://github.com/fivedollarfridays/montgowork

---

## License

MIT — see `LICENSE` at repo root.

---

## Contact

- **Project lead:** scsonnet@gmail.com
- **GitHub:** https://github.com/fivedollarfridays
- **Reddit:** u/macaulay_codin
- **Subreddit:** r/PairCoder
- **X:** @paircoder

---

## Editorial voice

Every line in this press kit derives from `docs/copy-thesis.md`
(single source of truth for GoWork's locked editorial fingerprint).
The hero question, the subhead, and the framework tagline are
verbatim — do not paraphrase.

---

## Made possible by

- **Mapbox** — map rendering + 3D buildings + custom dark editorial style
- **Vercel** — frontend hosting + Vercel Satori for per-chapter OG
- **Anthropic Claude** — augmented pair-programming
- **Worldwide Vibes Hackathon** (March 2026, 2nd place) — the prequel
  competition that prompted the visual rebirth

---

*Last updated: 2026-04-28 (W5 Driver A — submission narrative).*
