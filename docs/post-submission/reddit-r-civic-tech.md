# GoWork — Reddit Post Draft (r/civic-tech, fallback r/programming)

> **Authored:** W5 Driver D (post-submission narrative).
> **Status:** Draft. Shawn does the actual posting.
> **Target subreddits:** r/civic-tech (primary), r/programming (fallback),
> r/dataisbeautiful (cross-post candidate for the Wall visual),
> r/forthworth (local), r/Alabama or r/montgomery (second-city local).
> **Voice anchor:** `docs/copy-thesis.md` — locked editorial fingerprint.

---

## Title

**[Show r/civic-tech] GoWork — open-source workforce navigator built as a 3D scrollytelling Wall (Fort Worth + Montgomery, MIT)**

> Alternate: "I built a workforce navigator that shows the wall between
> a worker and a job. Open-source, MIT, deployed in two cities."

---

## Body

What's standing between you and a job?

Every career center in America runs the same loop. Someone walks in
needing work, but it's never just about the work. No vehicle means no
commute. A criminal record means half the listings disqualify them up
front. The wrong job triggers a benefits cliff that leaves them poorer
than before. Staff spend hours cross-referencing benefits thresholds,
transit routes, expungement eligibility, and local resources — for one
person at a time. Then the next person walks in.

GoWork replaces the manual cross-referencing with a structured
pipeline. The resident gets a plan. The staff get a briefing. The
career center gets throughput.

**What it is.** A workforce navigator that maps the wall — every
barrier between a worker and a paycheck — and routes around it. A
two-hour intake becomes a ten-minute personalized plan. Bus routes,
fair-chance employer matching, benefits-cliff math, expungement
eligibility, county-office locations. The home page is a 10-chapter
scroll-driven Mapbox visualization with a 3D barrier graph hovering
above the city. The protagonist (Carlos) is research-backed but not a
real person — ZIP 76119, recently released, no vehicle, 540 credit,
single father, four years of warehouse work behind him. The
demographics, the geography, and the barriers are real; the person is
composite.

**Where it's deployed.** Fort Worth, Texas (reference deployment) and
Montgomery, Alabama (second city). Same pluggable city framework
renders both. Texas state modules cover HHSC benefits screener and
Article 55 expunction; Alabama state modules cover seven Alabama
benefits programs and Act 2021-507 expungement. The framework is
multi-city by architecture — config + barrier graph DAG + state
modules + GTFS layer. Drop in a new city and you get a workforce
navigator on the same scaffold.

**How it's built.** Next.js + Mapbox GL JS + react-three-fiber +
FastAPI + Python 3.13. ~7,500 tests across frontend (vitest) and
backend (pytest). Lighthouse performance floor 0.90 on simulated 4G.
WCAG AAA contrast everywhere. Spanish parity (35% of Fort Worth's
population). Per-chapter dynamic OG cards via Vercel Satori. View
Transitions API on the close CTA (Chrome 135+, graceful fallback
elsewhere). Reduced-motion respected. Built using PairCoder's
multi-driver dispatch pattern — four parallel Claude-driven worktrees
per phase, each owning a constrained scope.

**Open source, MIT licensed.** Take it. Run it in your city. Hand the
plan to the worker on Monday morning. The full ~7,500-test suite, the
Wall, the barrier graph, the city framework, the Spanish-parity
re-skin, every piece of the pipeline is MIT.

GitHub: https://github.com/fivedollarfridays/montgowork

Live demo: <DEMO_URL — Driver C fills on deploy>

Submission video: <VIDEO_URL — Devpost or YouTube unlisted>

Press kit (with stills + numbers + the "what we learned" notes):
https://github.com/fivedollarfridays/montgowork/blob/main/docs/press-kit.md

---

## Why post this

We just shipped GoWork into HackFW 2026 (Reindustrialization track).
The Wall is the deliverable, but the long-term thesis is the
framework. If you run a career center, run a city, work in workforce
development, work in civic tech, or just want to fork an open-source
scrollytelling civic-data artifact and re-skin it for your town — the
repo is yours.

Happy to talk about: the multi-driver dispatch pattern, the bundle-budget
contract test that holds `/` First Load JS under 200 kB while shipping
Three.js + Mapbox + a 3D barrier graph, why we treat Spanish parity as
a civic obligation rather than a courtesy, why the wall is the
metaphor and not just the data structure.

— Shawn (u/macaulay_codin)

---

## Posting notes (do not include in published post)

- **Best time:** Tuesday or Wednesday morning, 9-11 AM CDT.
- **Cross-post:** r/programming after 24h if r/civic-tech engagement
  warrants. Skip r/programming if the title looks promotional —
  reword as "Show HN-style: open-source workforce navigator with a
  Mapbox + Three.js Wall" if needed.
- **Comments to seed (Shawn replies):** "Why MIT and not AGPL?"
  (answer: this is meant to fork; AGPL would block career-center
  adoption). "How do you handle the benefits cliff math?" (answer:
  per-state HHSC API + composable barrier graph DAG; details in
  `docs/architecture.md`).
- **Voice check:** Re-read against `docs/copy-thesis.md` before
  posting. The hero question, the subhead, and the framework tagline
  are verbatim.
- **Locked phrases (do NOT paraphrase):**
  - "What's standing between you and a job?"
  - "We do the math, sequence the path, and hand you the plan."
- **Do not lead with:** Worldwide Vibes (it's the prequel, not the
  headline — per W5 brief and `docs/visual-rebirth-briefs.md`).

---

> **C4 honest uncertainty:** Reddit r/civic-tech audience research
> limited from sandbox env; this draft reads as a starting point for
> Shawn's pre-post pass. Adjust tone for the subreddit's actual
> conventions before posting (some communities want shorter intros,
> some want a TL;DR on top, some downvote anything that looks like a
> launch announcement). When in doubt, lead with the *problem* (career
> centers running the manual loop), not the product (GoWork).
