# Architecture Decision Records

> **Authored:** W5 Driver D (Spotlight invention).
> **Format:** Lightweight ADRs documenting the major design decisions
> made across W1–W5 of the visual-rebirth sprint. Future contributors
> read these instead of doing git archaeology.

---

## What an ADR is

An Architecture Decision Record captures:

- **What** decision was made
- **When** it was made (sprint / week)
- **Why** it was made (tradeoffs considered)
- **What we'd revisit** if circumstances change

ADRs are immutable history. New decisions get new ADR numbers; existing
ADRs are amended only if the rationale itself was wrong (rare). To
reverse a decision, write a new ADR that supersedes the old one.

---

## ADRs

| # | Title | Date | Sprint | Status |
|---|---|---|---|---|
| 0001 | [The Wall as the deliverable](0001-wall-as-deliverable.md) | 2026-04-21 | W1 | Accepted |
| 0002 | [Mapbox + react-three-fiber composition over plain Three.js](0002-mapbox-three-fiber.md) | 2026-04-21 | W1 | Accepted |
| 0003 | [Custom Mapbox dark editorial style](0003-mapbox-custom-dark-style.md) | 2026-04-21 | W1 | Accepted |
| 0004 | [OKLCH color tokens with temperature multiplier](0004-oklch-tokens.md) | 2026-04-21 | W1 | Accepted |
| 0005 | [View Transitions API on the close CTA](0005-view-transitions.md) | 2026-04-22 | W3 | Accepted |
| 0006 | [Bundle-budget contract test (`/` < 200 kB First Load JS)](0006-bundle-budget-contract.md) | 2026-04-23 | W3 | Accepted |
| 0007 | [Per-chapter dynamic OG via Vercel Satori](0007-per-chapter-og.md) | 2026-04-26 | W4 | Accepted |
| 0008 | [Multi-driver dispatch pattern (4 parallel worktrees per phase)](0008-multi-driver-dispatch.md) | 2026-04-21 | W1 | Accepted |
| 0009 | [Spanish parity as a civic obligation](0009-spanish-parity.md) | 2026-04-26 | W4 | Accepted |
| 0010 | [Locked editorial voice via copy-thesis.md](0010-copy-thesis-lock.md) | 2026-04-28 | W5 | Accepted |

---

## Format template

Every ADR follows this shape:

```markdown
# ADR-NNNN: <Title>

- **Date:** YYYY-MM-DD
- **Sprint:** WN (e.g., W3)
- **Status:** Proposed | Accepted | Superseded | Deprecated

## Context

What's the problem? What forces are at play?

## Decision

What did we decide?

## Consequences

What does this enable? What does it foreclose? What's the cost?

## Alternatives considered

What other paths did we look at? Why did we reject them?

## What we'd revisit

If condition X changes, this ADR may need amendment.

## See also

Links to other ADRs, code, docs.
```

---

## Why these ADRs and not others

These are the ten decisions that, if reversed, would invalidate
substantial chunks of the codebase or the editorial voice. Smaller
decisions (which font, which icon library, which test runner, etc.)
either have a single canonical answer (vitest because Next.js + jsdom)
or aren't load-bearing enough to warrant an ADR.

If a future contributor asks "why X?" and the answer is "because we
tried Y and Z and they didn't work for these reasons", that's an ADR
candidate.

---

## See also

- [`docs/contributors-onboarding.md`](../contributors-onboarding.md) — read this first
- [`docs/architecture.md`](../architecture.md) — system shape
- [`docs/visual-rebirth-plan.md`](../visual-rebirth-plan.md) — Wall design intent
- [`docs/visual-rebirth-briefs.md`](../visual-rebirth-briefs.md) — per-sprint briefs (the *what*; ADRs are the *why*)
