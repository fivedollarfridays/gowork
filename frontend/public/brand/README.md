# GoWork brand thumbnails

Three social-ready brand thumbnails for posts, decks, profiles, and embeds. Each is shipped as both **SVG** (lossless / scaleable / ~2KB) and **PNG** (rasterized at native viewBox size, accepted by every social platform).

| Variant | SVG | PNG | Size | Use for |
|---------|-----|-----|------|---------|
| Square | `gowork-thumbnail-square.svg` | `gowork-thumbnail-square.png` | 1080×1080 | Instagram, LinkedIn square, Twitter cards (cropped), GitHub social preview, slide thumbnails |
| Wide | `gowork-thumbnail-wide.svg` | `gowork-thumbnail-wide.png` | 1200×630 | Twitter / LinkedIn / Facebook OG cards, Slack unfurls, Discord embeds, blog headers, YouTube thumbnails |
| Transparent | `gowork-thumbnail-transparent.svg` | `gowork-thumbnail-transparent.png` | 1080×1080 | Drop on any background (decks, photos, light/dark surfaces) — PNG keeps the alpha channel |

## Regenerating PNGs

If you edit any SVG, regenerate the matching PNGs with the project script (uses Playwright's bundled Chromium — already a dev dep):

```bash
cd frontend
node scripts/render-brand-pngs.mjs
```

Output is written next to each source SVG with the matching basename. Idempotent — safe to re-run.

## Other format conversions

**JPG** — open the PNG in any image tool ("Save as JPG" / `magick foo.png foo.jpg`). PNG is higher quality for these flat-vector graphics; only convert to JPG if a platform specifically demands it.

**Figma / Sketch / Illustrator** — drag the `.svg` into the canvas, export at any DPI.

## Design language

All three follow the canonical GoWork brand:

- Background: `#0A0E1A` (paper-dark navy) → `#0F1729` (raised surface) gradient
- Mark stroke: `#F5F3EE` (warm paper white)
- Path-line: `#22D3EE` (electric cyan — "the path / intelligence")
- Wordmark: Inter weight 800, tracking -0.04em
- Atmosphere: subtle cyan + amber radial gradients (matches `tokens/colors.css`)

To regenerate any of these or add new sizes, the in-app `BrandMark` React component (`src/components/wall/BrandMark.tsx`) and the existing OG card (`public/og-image.svg`) are the canonical source of truth — keep new artwork visually consistent.
