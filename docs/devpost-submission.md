# GoWork — Devpost Submission Content

> Pre-fill content for the HackFW 2026 Devpost form
> (`https://fwtx.devpost.com/`). Authored 2026-04-28 by W5 Driver A.
> Editorial voice locked in `docs/copy-thesis.md`.

---

## Project name

**GoWork**

## Tagline

**Workforce navigation infrastructure — demonstrated in Fort Worth, ready for any American city.**

---

## Project description

GoWork is an open-source workforce navigator that asks the question
nobody else asks: **what's standing between you and a job?** It walks
the resident through real Fort Worth geography — bus routes, county
offices, fair-chance employers, neighborhood ZIP boundaries — and
renders the wall of barriers between them and employment as a
cinematic, scroll-driven Mapbox visualization with a 3D barrier graph
hovering above the city.

A career-center intake takes two hours and ends with a list of jobs.
GoWork takes ten minutes and ends with a sequenced plan: which barrier
unblocks which next, what each step costs, where each office is, which
bus route gets you there, what the benefits-cliff math looks like at
the offered wage. The resident walks into the Workforce Solutions
office on Monday morning with a printable Career Center Ready Package
that staff can act on immediately.

The reference deployment is **Fort Worth, Texas**. The framework
(city config + barrier graph DAG + Texas state modules + Trinity Metro
GTFS layer) is multi-city by architecture — Montgomery, Alabama is the
second city demonstrated, with the same pluggable city framework used
to render both. Carlos, the protagonist persona walking through the
Wall, is research-backed but not a real person: ZIP 76119, recently
released, no vehicle, 540 credit, single father, four years warehouse
experience. The demographics, geography, and barriers are real — the
person is composite.

Built with Next.js 15.5.9, Mapbox GL JS, react-three-fiber, FastAPI,
and Python 3.13. Tested at depth: **3,428 frontend tests + ~4,080
backend tests = ~7,500+ total**, all green. Lighthouse performance
floor 0.90 on simulated 4G. WCAG AAA contrast everywhere. Spanish
parity (35% of Fort Worth's population). MIT licensed. The home page,
the press-kit stills, and the submission video all derive from the
same Mapbox-driven scrollytelling artifact — one asset, four uses.

---

## Inspiration

We lost a previous hackathon because the winner had Google
Earth-tier visual gravitas. The response was the Wall: a Mapbox-driven
3D scrollytelling artifact that makes the **worker visible** and the
**framework provable** — at 60fps, in real geography, in two languages.

The deeper inspiration is structural. Career centers see the same
pattern every day: someone walks in needing a job, but it's never just
about the job. No vehicle means no commute. A criminal record means
half the listings disqualify them up front. The wrong job triggers a
benefits cliff that leaves them poorer than before. Staff spend hours
cross-referencing benefits thresholds, transit routes, expungement
eligibility, and local resources — for one person at a time. GoWork
replaces that manual cross-referencing with a structured pipeline so
staff can spend the hour on the human part.

Carlos was built from research, not biography. ZIP 76119 is east of
downtown Fort Worth. Tarrant County District Clerk is 4.8 miles from
him. Bus 4 plus Bus 6 is 71 minutes. Amazon DFW5 is a real fulfillment
center. Texas Article 55 expunction is a real legal pathway. The wall
is real; the persona is the lens.

---

## What we learned

**AI-augmented pair programming at scale.** GoWork was built by Team
PairCoder using a multi-driver dispatch pattern — four parallel
Claude-driven worktrees per phase, each owning a constrained scope
(life layers, edge states, accessibility, maximization). Worktree
isolation made parallel work safe. SubagentStop hooks fed token
telemetry into a calibration engine that learned how long each driver
class took for each task class.

**Scrollytelling architecture for civic data.** Mapbox storytelling +
react-three-fiber + framer-motion + the View Transitions API
(currently Chrome-only, with graceful fallback) compose into a
camera-choreography system where every chapter has its own zoom,
pitch, bearing, and atmosphere. Editorial overlays, persistent
path-line, time-aware sky color, and per-chapter dynamic OG cards
(Vercel Satori) all fall out of the same chapter scaffold.

**Bundle-budget contract testing.** Three.js plus Mapbox plus the
Wall scaffold is heavy. We solved it with a bundle-size contract test
that fails CI if `/` First Load JS exceeds 200 kB. Current value: 150
kB. Lazy-loading the BarrierConstellation 3D layer was the unlock.

**Spanish parity as a civic obligation.** Fort Worth is 35% Hispanic.
Eight `[ES-pending-review]` flags in W4 closed every translation gap;
the EN/ES toggle re-skins the entire Wall with equal craft. The
Spanish copy is not a courtesy — it is the standard.

---

## Challenges we ran into

**Three.js + Mapbox bundle weight.** Initial implementations ran the
First Load JS over 220 kB. Fixed by:
- Lazy-loading the 3D barrier graph behind a Chapter-08 viewport
  trigger.
- Splitting the Mapbox style import out of the initial bundle.
- A bundle-budget contract test (Spotlight, W3) that gates the build.

**Spanish parity sweep.** W4 inherited eight `[ES-pending-review]`
flags from W3. Each one was a translation gap; closing them required
re-reading every chapter editorial in both languages. Solved by a
locale audit script that lists every pending flag, plus a
content-comparison test asserting EN/ES key parity.

**WCAG AAA contrast tuning.** Dark base + warm amber + cool cyan looks
beautiful in Figma; on the actual page, AAA contrast forced multiple
OKLCH adjustments (especially `--fg-secondary` against
`--bg-elevated`). A `verify-contrast.mjs` script + `audit:tokens`
command guard the palette.

**Lighthouse 0.90 hard gate on simulated 4G.** Negotiated by Phase N
(W3): inline critical CSS, font-display swap, image lazy-loading,
deferred non-critical JS. The gate now holds at every PR.

**View Transitions browser support.** The View Transitions API ships
in Chrome but not Firefox. Solved with a graceful no-op fallback
(`document.startViewTransition` feature-detected before invocation;
plain navigation when absent) plus a reduced-motion bypass.

---

## Built with

Next.js, TypeScript, Mapbox GL JS, react-three-fiber, Three.js,
Vercel Satori (`@vercel/og`), FastAPI, Python 3.13, Tailwind CSS,
OKLCH color, View Transitions API, framer-motion, SQLAlchemy,
SQLite (aiosqlite), FAISS, Anthropic Claude, OpenAI, Google Gemini,
JSearch, BrightData, Honest Jobs, html2pdf.js, EmailJS, Vercel,
Railway.

---

## Categories

- **Reindustrialization** (HackFW track)
- **Workforce**
- **AI / ML**
- **Civic Tech**
- **Open Source**
- **Public Interest Tech**

---

## Team members

- **Shawn Sanchez** — Team PairCoder lead, co-developer
- **Claude (Anthropic)** — Augmented pair-programming partner
  (multi-driver dispatch, all four parallel worktrees per phase)
- **Kevin Masterson** — Original creator (acknowledged in press kit)

GoWork was built using PairCoder's enforcement workflow — the
~7,500-test suite is not afterthought coverage. Every feature started
as a failing test, including the Mapbox chapter scaffold, the barrier
graph traversal, the benefits-cliff calculator, and the per-chapter
OG image generator.

---

## Try it now

- **Production deployment:** _Driver C will fill on deploy._
- **Source code:** `https://github.com/fivedollarfridays/montgowork`
- **License:** MIT (`LICENSE` at repo root)

---

## Editorial reference

This document derives its voice from `docs/copy-thesis.md` (single
source of truth for the GoWork editorial fingerprint). When the form
on `https://fwtx.devpost.com/` is filled, paste sections verbatim from
above. Do not paraphrase the locked phrases.
