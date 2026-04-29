# GoWork — LinkedIn Announcement Draft

> **Authored:** W5 Driver D (post-submission narrative).
> **Status:** Draft. Shawn does the actual posting.
> **Target audience:** workforce development professionals, civic-tech
> practitioners, public-interest tech leaders, career-center directors,
> Fort Worth + DFW + Alabama workforce ecosystem, fellow open-source
> contributors.
> **Voice anchor:** `docs/copy-thesis.md` — locked editorial fingerprint.
> **Length target:** 700–1000 words (LinkedIn long-form sweet spot).

---

## Headline

**GoWork — open-source workforce navigation infrastructure for any
American city. Demonstrated in Fort Worth. Built for HackFW 2026.**

---

## Body

What's standing between you and a job?

That's the question every career center in America hears every day,
and it almost never has anything to do with the job itself. It's the
five offices the resident has to visit before Monday. It's the
forty-seven forms. It's the bus that takes seventy-one minutes when
the schedule says forty-five. It's the credit score that closes doors
they never knocked on. It's the misdemeanor that means half the
listings disqualify them up front. It's the wage that triggers a
benefits cliff and leaves them poorer than before.

Career-center staff spend hours cross-referencing benefits thresholds,
transit routes, expungement eligibility, employer background-check
policies, and local resources — for one person at a time. Then the
next person walks in. The math is the same; only the names change.

**GoWork is the structured pipeline that replaces the manual
cross-referencing.**

A two-hour intake becomes a ten-minute personalized plan. The resident
walks into the Workforce Solutions office on Monday morning with a
printable Career Center Ready Package — staff briefing on one page,
resident action plan on the other. Bus routes, fair-chance employer
matching, benefits-cliff math, expungement eligibility, county-office
locations. The wall, mapped and routed around.

---

### Approach

The home page IS the deliverable. Not a marketing site that links to
a product — the product. Ten chapters of scroll-driven Mapbox
visualization render real Fort Worth geography (Trinity Metro bus 4,
Tarrant County District Clerk, Amazon DFW5 fulfillment center,
Workforce Solutions Tarrant) at 60fps with a 3D barrier graph
hovering above the city. Per-chapter dynamic OG cards via Vercel
Satori. View Transitions API on the close CTA. WCAG AAA contrast
everywhere. Reduced-motion respected. Spanish parity throughout —
because Fort Worth is 35% Hispanic and Spanish parity is a civic
obligation, not a courtesy.

The protagonist is a research-backed persona, not a real person —
ZIP 76119, recently released, no vehicle, 540 credit, single father,
four years of warehouse experience. Demographics, geography, and
barriers are real. The person is composite. The wall is real.

The framework is multi-city by architecture. City config + barrier
graph DAG + state-level modules + transit GTFS layer. Texas state
modules cover the HHSC benefits screener and Article 55 expunction.
Alabama state modules cover seven Alabama benefits programs and Act
2021-507 expungement. The framework already supports Fort Worth,
Texas (reference deployment) and Montgomery, Alabama (second city).
Same scaffold. Drop in a new city configuration and you get a
workforce navigator — with editorial polish — on Monday.

---

### Outcome

Open source. MIT licensed. ~7,500 tests across the frontend (vitest)
and backend (pytest), all green. Lighthouse performance floor 0.90
on simulated 4G. The bundle stays under 200 kB First Load JS even
with Three.js + Mapbox + a 3D barrier graph. The Spanish-parity
re-skin has equal craft to the English. The Career Center Ready
Package is a printable two-page artifact; staff can act on it on
Monday morning without further translation.

The submission video, the press kit cinematic stills, and the home
page all derive from the same Mapbox-driven scrollytelling artifact.
One asset. Four uses. Editorial discipline locked in
`docs/copy-thesis.md` so the hero question, the subhead, and the
framework tagline don't drift across surfaces.

---

### Built with

GoWork was built by Team PairCoder using a multi-driver dispatch
pattern: four parallel Claude-driven worktrees per phase, each owning
a constrained scope (life layers, edge states, accessibility,
maximization). Worktree isolation made parallel work safe. SubagentStop
hooks fed token telemetry into a calibration engine that learned how
long each driver class took for each task class.

The ~7,500-test suite is not afterthought coverage. Every feature
started as a failing test, including the Mapbox chapter scaffold, the
barrier graph traversal, the benefits-cliff calculator, and the
per-chapter OG image generator. The enforcement layer required it
before any code shipped.

---

### Why this matters

The metaphor is the data structure. The wall is real. The barrier
graph is a directed acyclic graph; path completeness is calculated;
benefits-cliff math is the federal poverty guideline plus state
program tables. None of this is vibes. The visualization is the
receipt that the math is solved.

If you run a career center, run a city, work in workforce development
or civic tech, or want to fork an open-source civic-data
scrollytelling artifact and re-skin it for your municipality — the
repo is yours.

🔗 **Live deployment:** <DEMO_URL>
🔗 **Repository:** https://github.com/fivedollarfridays/montgowork
🔗 **Press kit:** /docs/press-kit.md
🔗 **Devpost submission:** /docs/devpost-submission.md
🔗 **License:** MIT

Built for HackFW 2026 (Reindustrialization track). Reference deployment
in Fort Worth, Texas. Second city: Montgomery, Alabama.

— Shawn Sanchez (Team PairCoder)
With Claude (Anthropic), in a multi-driver dispatch pattern.

#civictech #workforce #publicinterest #fortworth #opensource
#hackathon #reindustrialization #publicpolicy

---

> **Posting notes (do not publish):**
>
> - **Best time:** Wednesday 8–9 AM CDT, after the Reddit + Twitter
>   launch waves. LinkedIn rewards the long-form professional voice.
> - **Voice check:** Re-read against `docs/copy-thesis.md` — the
>   hero question, the subhead, and the framework tagline are
>   verbatim. Locked phrases stay locked.
> - **Image:** Lead with `docs/press-kit/screenshots/hero-fort-worth-overhead.png`
>   (when Driver B captures it). Backup: Ch2 arrival.
> - **Tags:** Tag Fort Worth Workforce Solutions, Workforce Solutions
>   for North Central Texas, City of Fort Worth Economic Development,
>   if Shawn has working LinkedIn relationships there. If not, leave
>   the tags off — better than spamming.
> - **Comment-seeding:** Prepare a one-paragraph reply about why MIT
>   (forking-friendly), one about the multi-driver dispatch pattern
>   (PairCoder), one about why the wall is the metaphor (because the
>   barrier graph is the data structure).
> - **Do NOT lead with** Worldwide Vibes (it's the prequel, not the
>   headline — per W5 brief and `docs/visual-rebirth-briefs.md`).

---

> **C4 honest uncertainty:** Drafted from sandbox env without
> LinkedIn analytics; tone calibration for the workforce-development
> professional audience is partly inferred. Shawn's pre-post pass
> should re-read paragraph 5 ("Outcome") for promotional language —
> LinkedIn audiences in this lane reward modesty. The technical depth
> in "Built with" reads to engineers; if the post is going to a
> non-technical audience, drop the SubagentStop / multi-driver
> paragraph and keep the workforce-development frame.
