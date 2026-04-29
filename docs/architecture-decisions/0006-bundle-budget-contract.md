# ADR-0006: Bundle-budget contract test (`/` < 200 kB First Load JS)

- **Date:** 2026-04-23
- **Sprint:** W3 (Interactive Chapters 6-10)
- **Status:** Accepted

## Context

The Wall is heavy by design. Mapbox GL JS, react-three-fiber, Three.js,
framer-motion, OKLCH tokens, per-chapter editorial copy in two
languages, a 3D barrier graph, View Transitions polish, scroll-velocity
motion-blur — every visual layer is bundle weight.

W2 saw `/` First Load JS climb to 273 kB. Lighthouse Performance
dropped to 0.78 on simulated 4G. The hackathon brief required a hard
gate of 0.90 perf.

Without an enforcement layer, every new feature would silently
re-regress the bundle. Code review can't catch a 5 kB drift; only a
contract test can.

## Decision

Pin a vitest contract test that asserts:

1. `/` First Load JS stays under **200 kB** (current value: 150 kB).
2. No chapter file statically imports `recharts`, `react-smooth`, or
   the `BenefitsCliffChart` directly. Dynamic imports only.
3. `Chapter06TheMath` uses `next/dynamic({ ssr: false })` for the
   cliff chart.

The contract is at
`frontend/src/lib/wall/__tests__/bundleBudget.test.ts` (Spotlight from
W3 Driver D).

Build emits the manifest JSON used by the test. The test parses the
manifest and asserts the budget. Any PR that pushes `/` over 200 kB
fails CI.

## Consequences

**Enables.**

- Lighthouse Performance 0.90 floor holds at every PR.
- New features can ship behind dynamic imports without breaking the
  budget.
- Contributors get an immediate, specific failure ("you added 18 kB
  to /") instead of a vague "Lighthouse went red".

**Forecloses.**

- Cannot statically import heavy libs from chapter components.
  Everything Three.js / Recharts / chart-specific must be lazy.
- Imposes the cost of writing the dynamic-import skeleton (the
  `CliffChartSkeleton`-style placeholder).

**Cost.**

- One-time engineering of the lazy-load patterns (W3 Driver D).
- Ongoing discipline of "is this static or dynamic?" at PR time.

## Alternatives considered

1. **Lighthouse-only gate.** Trust the perf score, no specific
   bundle budget. Rejected — Lighthouse is a black box; bundle is a
   white-box metric we can debug instantly.
2. **Per-component budget.** A test per chapter. Rejected as
   over-specification — the page-level budget is the contract that
   actually matters.
3. **Soft warning, not hard gate.** Log a warning if over 200 kB.
   Rejected — soft warnings are ignored.

## What we'd revisit

If we add a feature that legitimately needs more First Load JS (say,
WebGL2 shaders for a new chapter), we'd revisit. The 200 kB number
is calibrated to the current Lighthouse 0.90 floor on simulated 4G.
A future device baseline (5G median) might justify 250 kB.

## See also

- [ADR-0001](0001-wall-as-deliverable.md) — the Wall as deliverable
- [ADR-0002](0002-mapbox-three-fiber.md) — Mapbox + r3f composition
- `frontend/src/lib/wall/__tests__/bundleBudget.test.ts` — the contract test
- `frontend/src/components/wall/chapters/Chapter06TheMath.tsx` — example dynamic import
- `frontend/src/components/wall/chapters/CliffChartSkeleton.tsx` — placeholder pattern
