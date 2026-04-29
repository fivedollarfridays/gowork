# Press Kit Screenshots — Cinematic Stills

> Cinematic stills captured from the rendered Wall. Driver B is the
> owner of this directory. Driver A authored the press kit + README
> contracts that reference these files; this README documents the
> contract those files must satisfy.

---

## Contract

The press kit (`docs/press-kit.md`) and the README (`README.md`) both
forward-reference cinematic stills under this directory. The
press-kit-paths and README-link validator tests
(`frontend/src/__tests__/submission/`) accept either:

- A real PNG (`<name>.png`), OR
- A sibling `<name>.png.placeholder` marker file

The placeholder convention lets the docs ship before screenshots are
captured. Driver B replaces each `.placeholder` with a real PNG;
nothing in the docs needs to change.

---

## Required stills

| Filename | Source chapter | Composition |
|---|---|---|
| `hero-fort-worth-overhead.png` | Title sequence | FW skyline with locked thesis "What's standing between you and a job?" overlaid in display weight |
| `ch2-fort-worth-arrival.png` | Chapter 02 (City Arrival) | Atmospheric flight from continent → Fort Worth at altitude. 3D buildings rising. Trinity Metro routes drawn in cyan. |
| `ch6-the-math.png` | Chapter 06 (The Math) | Camera at Amazon DFW5. BenefitsCliffChart overlay. Wage slider in cliff zone. |
| `ch7-the-path.png` | Chapter 07 (The Path) | Carlos avatar walking the GPS path. Glowing amber-to-cyan path line. Trinity Metro highlights. |
| `ch8-barrier-graph.png` | Chapter 08 (The Graph) | 3D barrier constellation hovering above the city, breathing. |
| `ch10-find-your-path.png` | Chapter 10 (Find Your Path) | "Start your assessment" CTA over Carlos's home pin. |

---

## Capture spec (for Driver B)

- 2880 × 1620 (3:9 ratio) for full-frame stills
- 1200 × 630 for OG fallbacks
- PNG, sRGB
- Run `verify-contrast.mjs` before export to confirm overlay text
  contrast is AAA against the underlying map gradient
- Capture from Chrome with reduced-motion OFF and a pre-warmed Mapbox
  cache (style + tiles) so the still represents the live render

---

## Provenance

- **Owner:** Driver B (W5 lane), with W5 Driver A consuming via press
  kit + README references.
- **Test gate:** `frontend/src/__tests__/submission/press-kit-paths.test.ts`
  + `readme-links.test.ts`.
- **Placeholder convention:** sibling `.placeholder` file (zero-byte or
  metadata-only) marks intentional gap.
