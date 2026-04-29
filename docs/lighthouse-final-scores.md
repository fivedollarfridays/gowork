# Lighthouse Final Scores — Submission Gate

> **Authored:** W5 Driver C, 2026-04-28
> **Source of truth for floors:** `frontend/lighthouserc.json` (W4 brief).
> **Floor (W5 Driver C hard gate):** All 4 categories ≥ 0.90.

This document records the Lighthouse scores measured against the
production build immediately before the HackFW 2026 submit. It is updated
on every promotion. The submission checklist
(`docs/submission-checklist.md`) gates on these scores.

---

## Floors (locked, do NOT lower as a shortcut)

| Category        | Floor (minScore) | Source                       |
|-----------------|------------------|------------------------------|
| performance     | 0.90             | W5 Driver C brief, §T5.C.1   |
| accessibility   | 0.90             | W4 a11y brief                |
| best-practices  | 0.90             | W4 a11y brief                |
| seo (SEO)       | 0.90             | W4 a11y brief                |

The W5 sprint backlog
(`plans/backlogs/sprint-w5-submission.md` decision lock #7) lists perf
≥ 0.85 as a relax. **The W5 Driver C brief overrides the backlog** with
a 0.90 hard gate. If Shawn decides to relax to 0.85, edit
`frontend/lighthouserc.json` AND `frontend/src/__tests__/lighthouse-config.test.ts`
in lockstep. Do NOT lower silently.

---

## How to measure (canonical run path)

Run from the `frontend/` directory of a clean checkout:

```bash
cd frontend
npm ci
npm run build
npm run lhci
```

The `lhci autorun` command launches `npm run start`, hits the 6 URLs
configured in `lighthouserc.json`, runs each 3 times (median wins), and
asserts the four floors. If any category is below floor, the command
exits non-zero and prints the offending URL + score.

For a more lifelike measurement, run Lighthouse directly in Chrome
DevTools against the production Vercel URL. Local `lhci` measures
`localhost:3000` served by `next start`; production benefits from
Vercel's CDN and is typically 2-5 points higher.

---

## Measurement log

### 2026-04-28 (W5 Driver C — local)

**Status:** **DEFERRED to CI / Shawn-run** (see honest uncertainty below).

| Category        | Score | Pass? |
|-----------------|-------|-------|
| performance     | _pending_ |   |
| accessibility   | _pending_ |   |
| best-practices  | _pending_ |   |
| seo             | _pending_ |   |

**Run path:**

```bash
cd frontend
npm ci
npm run build
npm run lhci
```

### Template for future runs

When Shawn or CI runs Lighthouse before submit, copy the template and
fill in actuals. Use ISO timestamps:

```
### YYYY-MM-DDTHH:MM:SSZ — pre-submit (Shawn-run / CI-run)

Measured at: <ISO timestamp>
URL measured: https://gowork.vercel.app
numberOfRuns: 3 (median)

| Category        | Score | Pass (≥ 0.90)? |
|-----------------|-------|----------------|
| performance     | 0.XX  | ✓ / ✗          |
| accessibility   | 0.XX  | ✓ / ✗          |
| best-practices  | 0.XX  | ✓ / ✗          |
| seo             | 0.XX  | ✓ / ✗          |

Notes: <any flake / regression / descope decision>
```

---

## Descope priority order (if a category drops below 0.90)

Apply in this exact order, re-measuring after each. Stop when all 4
categories are back ≥ 0.90. Do NOT lower the floor.

1. **Disable audio bed** (W4 Driver A) — saves ~30 KB JS + audio decode CPU.
2. **Disable temperature multiplier** on cursor accents (W4 Driver A)
   — saves ~10 KB CSS variables churn.
3. **Confirm 3D barrier graph is lazy-loaded** (already lazy via dynamic
   import; if regressed, restore the `dynamic(..., { ssr: false })`
   wrapper).
4. **Feature-detect View Transitions** more aggressively (skip the
   transition entirely, fall back to standard nav on first paint).

If after all 4 descopes the score is STILL below 0.90, it is almost
certainly environmental flake (lhci runner variance — see W2 souji
notes about `numberOfRuns: 3`). Document the median of 3 runs and
proceed. This is the **only** acceptable below-floor path, and it
must be documented in the measurement log above.

---

## Honest uncertainty

**Local measurement deferred (W5-C C4):**
Lighthouse could not run from this worktree env — port 3000 was in use
by a sibling driver agent at the time of this checkpoint. The four
scores are intentionally left as `_pending_` so a follow-up run by
Shawn or CI fills them in. The `npm run pre-deploy` Spotlight script
(`frontend/scripts/pre-deploy-gate.mjs`) automates the build + lhci
sequence so this is one command:

```bash
cd frontend
npm run pre-deploy
```

Until Shawn runs that, the **submission checklist gate**
(`docs/submission-checklist.md` step "All Lighthouse scores ≥ 0.90 on
production") is the human stop-loss.

**lhci config drift detection:** the tests `lighthouse-config.test.ts`
pin the four floors so the config cannot silently drift. If the test
fails, the config has been touched — review before unblocking.

---

## See also

- `frontend/lighthouserc.json` — actual lhci config (the floors)
- `frontend/lighthouserc.README.md` — runbook for tuning floors
- `frontend/scripts/pre-deploy-gate.mjs` — Spotlight one-command runner
- `docs/submission-checklist.md` — T-1 hour gate that consumes this
- `docs/vercel-deploy-runbook.md` — production deploy procedure
