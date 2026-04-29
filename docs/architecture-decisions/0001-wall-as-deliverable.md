# ADR-0001: The Wall as the deliverable

- **Date:** 2026-04-21
- **Sprint:** W1 (Visual Rebirth — Foundation)
- **Status:** Accepted

## Context

We lost a previous hackathon (Worldwide Vibes, March 2026) where the
winner had Google Earth-tier visual gravitas. Our codebase was deep
(~7,500 tests, 17 sprints of work) but the marketing surface was a
standard tabbed product page — nothing for judges to remember after
demo day.

For HackFW 2026 Reindustrialization track, judges see three things:
the live URL, the README, and a 3-4 minute video. The deliverable
*is* the marketing surface. We needed a way to make the product walk
itself through the use case at the speed a viewer scrolls.

## Decision

Build a 10-chapter Mapbox-driven scrollytelling artifact ("The Wall")
as the home page. Cinematic camera flights. Real Fort Worth
geography. A 3D barrier graph hovering above the city. Per-chapter
dynamic OG cards. Carlos as the protagonist persona walking the
route. EN/ES parity. View Transitions API on the close CTA.

The home page IS the press kit. The same artifact generates:

- The cinematic stills in the press kit
- The OG cards for social unfurls
- The submission video screen capture
- The judges' demo URL

**One asset, four uses.**

## Consequences

**Enables.**

- Editorial gravitas at parity with the previous hackathon winner.
- The product narrates its own use case without a sales deck.
- Press kit is auto-generated rather than auto-degraded by hand.
- The judging experience is the user experience, end-to-end.

**Forecloses.**

- Cannot ship the home page as a static landing page. The Wall must
  render Mapbox + Three.js in Next.js. Bundle weight becomes a
  first-class concern (see ADR-0006).
- Adds Mapbox as a hard runtime dependency on the home page. CDN
  unreachability becomes a fallback path.
- Per-chapter editorial copy is now a *product* surface, locked to
  the editorial voice (see ADR-0010).

**Cost.**

- W1-W5 visual rebirth sprints (~4 weeks, 4 drivers in parallel per
  phase).
- Three.js + Mapbox bundle weight management (ADR-0006).
- Spanish parity sweep (ADR-0009).

## Alternatives considered

1. **Marketing site + product app.** Standard 2-page split. Rejected
   because it doesn't answer the visual-gravitas problem.
2. **Video-only Wall (recorded, embedded).** A pre-rendered video
   instead of a live experience. Rejected because judges click
   "Try it out" and want to interact, not watch a YouTube embed.
3. **AR / WebXR.** Too device-fragmented; iOS Safari support is
   uneven; AAA contrast and reduced-motion become much harder.

## What we'd revisit

If Mapbox quotas / pricing become prohibitive, we'd swap for
MapLibre + a self-hosted vector tile stack. The Wall scaffold is
abstracted enough that the swap is a layer change, not a rewrite.

If a future redesign needs to reach a non-cinematic audience (i.e.,
judges who want a text-first explanation), we'd add a
`?mode=transcript` query param that flattens the Wall into a
chapter-by-chapter long-form text article — without abandoning the
cinematic mode for everyone else.

## See also

- [`docs/visual-rebirth-plan.md`](../visual-rebirth-plan.md) — the Wall plan
- [ADR-0002](0002-mapbox-three-fiber.md) — Mapbox + react-three-fiber composition
- [ADR-0006](0006-bundle-budget-contract.md) — bundle budget contract
- [ADR-0008](0008-multi-driver-dispatch.md) — multi-driver dispatch (how we built it)
