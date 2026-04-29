# GoWork — Post-HackFW Post-Mortem Template

> **Authored:** W5 Driver D (Spotlight invention).
> **Audience:** Future Shawn / Kevin / contributors, post-judging.
> **When to fill:** 2026-05-09 (one week after submission deadline).
> **Voice:** Honesty Lens. Reverse-the-direction-of-effort: write the
> things you'd defend least loudly first. Vague reads as cope; specific
> reads as gold.

---

## Snapshot

| Field | Value |
|---|---|
| Submission date | _2026-05-02 (or T-tag of `v0.1.0-hackfw-submission`)_ |
| Devpost URL | _<DEVPOST_PROJECT_URL>_ |
| Production URL at submit | _<DEMO_URL>_ |
| Git tag | `v0.1.0-hackfw-submission` |
| Final test count (frontend) | _<vitest passing>_ |
| Final test count (backend) | _<pytest expanded>_ |
| Final `/` First Load JS | _<value> kB_ |
| Final Lighthouse scores | perf _<X>_, a11y _<X>_, BP _<X>_, SEO _<X>_ |
| HackFW result | _<placement / outcome / "judged" / "won" / etc.>_ |

---

## What worked

> Be specific. "TDD worked" is not specific. "Bundle-budget contract
> test caught the recharts regression on the W3 cliff chart before
> Driver B even started recording" is specific.

### Process

- _Multi-driver dispatch pattern (4 parallel worktrees per phase):_ ___
- _SubagentStop telemetry feeding the calibration engine:_ ___
- _bpsai-pair enforcement (state.md non-negotiable, arch check on every task):_ ___
- _Test-driven development discipline (every feature started as a failing test):_ ___

### Architecture

- _Pluggable city framework (Fort Worth + Montgomery from same scaffold):_ ___
- _Barrier graph DAG + path completeness scoring:_ ___
- _Mapbox + react-three-fiber + framer-motion composition:_ ___
- _Spanish parity sweep (W4 closed 8 ES-pending-review flags):_ ___
- _Bundle-budget contract test (`/` First Load JS < 200 kB despite Three.js + Mapbox):_ ___
- _OKLCH design tokens + AAA contrast guard + temperature multiplier:_ ___

### Editorial / submission

- _Locked editorial voice via `docs/copy-thesis.md`:_ ___
- _Wall as the deliverable (home page IS the press kit):_ ___
- _Per-chapter dynamic OG cards via Vercel Satori:_ ___
- _Submission readiness guard test:_ ___

---

## What didn't work / what we'd do differently

> Be honest. The judging panel reads what worked; the team reads what
> didn't. Worth more.

### Process

- _<Insert 1-3 specific friction points, each one in 1-2 sentences>_

### Architecture

- _<Did we pick the right framework? What dragged?>_

### Editorial / submission

- _<Did the video runtime cap drift through 4 drafts? Did the press
  kit lose a screenshot in the merge? Be specific about the thing
  that almost broke at T-1h.>_

### Things we cut and shouldn't have

- _<List items deferred / descoped that we now think were under-valued>_

### Things we shipped and shouldn't have

- _<Be brave. List items that took team time but didn't move the
  judging needle.>_

---

## What we'd do differently

> Concrete deltas for the next sprint, the next hackathon, the next
> open-source ship.

1. _Process change #1:_ ___
2. _Architecture change #2:_ ___
3. _Editorial change #3:_ ___
4. _Tooling change #4:_ ___
5. _Communication change #5:_ ___

---

## Honest open questions

> Things we still don't know.

- _Did the multi-driver dispatch produce better code than a single
  driver would have, or just more code?_ ___
- _Did the Spanish parity sweep actually move judging weight?_ ___
- _What did Carlos-as-composite cost us? Would a real partner
  organization (Workforce Solutions Tarrant) have changed
  positioning?_ ___
- _What's the real cost of the ~7,500-test suite over the next 6
  months of contributor onboarding?_ ___

---

## Calibration

> If we ran the same hackathon again with the same tools, what would
> the calibration engine learn?

| Driver class | Task class | Initial estimate | Actual | Delta |
|---|---|---|---|---|
| Driver A | Submission narrative | _<W5 estimate>_ | _<W5 actual>_ | _<delta>_ |
| Driver B | Cinematic asset spec | _<W5 estimate>_ | _<W5 actual>_ | _<delta>_ |
| Driver C | Submission readiness | _<W5 estimate>_ | _<W5 actual>_ | _<delta>_ |
| Driver D | Final maximization | _<W5 estimate>_ | _<W5 actual>_ | _<delta>_ |

---

## Forward map

> Post-mortem isn't autopsy — it's a compass for the next sprint.

### Immediate (week 1 post-judging)

- [ ] Reddit + Twitter + LinkedIn announcement (drafts in
      `docs/post-submission/`)
- [ ] Devpost project page review for typos / link rot
- [ ] Production smoke test once a day for the judging window
- [ ] Update `LAST_CALIBRATED` env var

### Short term (weeks 2–4)

- [ ] FW DAO bounty research follow-through (per
      `docs/fw-dao-bounty-research.md`)
- [ ] Contributor onboarding doc (per W5-D Spotlight)
- [ ] Multi-city expansion playbook (per W5-D Spotlight)
- [ ] Architecture Decision Records for the major W1-W5 decisions

### Medium term (months 2–3)

- [ ] Third city (Dallas? Houston? other-Texas? other-Alabama?)
- [ ] Career-center field test with a real Workforce Solutions
      partner
- [ ] Live-data integration audit (BrightData, JSearch, Honest Jobs
      reliability)

---

## Sign-off

- Filled by: ________________________________
- Date filled: ________________________________
- Reviewed by (Kevin / Shawn): ________________________________

---

## See also

- `docs/copy-thesis.md` — locked editorial voice
- `docs/submission-checklist.md` — T-1h checklist for next time
- `docs/visual-rebirth-briefs.md` — phase-by-phase brief log
- `.paircoder/context/state.md` — sprint-by-sprint history
- `.paircoder/feedback/calibration.json` — driver calibration ledger

---

> **C4 honest uncertainty:** This template is the *shape*. The actual
> post-mortem is the team's reflection — don't fill it in performatively.
> If a section is "nothing significant," write that. The compass works
> only if the bearings are honest.
