# GoWork brand thumbnails

Three social-ready brand thumbnails for posts, decks, profiles, and embeds.

| File | Size | Use for |
|------|------|---------|
| `gowork-thumbnail-square.svg` | 1080×1080 | Instagram, LinkedIn square, Twitter cards (cropped), GitHub social preview, slide thumbnails |
| `gowork-thumbnail-wide.svg` | 1200×630 | Twitter / LinkedIn / Facebook OG cards, Slack unfurls, Discord embeds, blog headers, YouTube thumbnails |
| `gowork-thumbnail-transparent.svg` | 1080×1080 | Transparent — drop on any background (decks, photos, light/dark surfaces) |

## Convert to PNG / JPG

Most platforms accept SVG directly. If you need a raster:

**Browser** — open the `.svg` in any modern browser → right-click → "Save image as…" picks PNG.

**CLI** — with [`rsvg-convert`](https://wiki.gnome.org/Projects/LibRsvg) or ImageMagick:

```bash
# rsvg-convert
rsvg-convert -w 1080 -h 1080 gowork-thumbnail-square.svg -o gowork-thumbnail-square.png

# ImageMagick
magick gowork-thumbnail-square.svg gowork-thumbnail-square.png
```

**Figma / Sketch / Illustrator** — drag the `.svg` into the canvas, export as PNG/JPG at any DPI.

## Design language

All three follow the canonical GoWork brand:

- Background: `#0A0E1A` (paper-dark navy) → `#0F1729` (raised surface) gradient
- Mark stroke: `#F5F3EE` (warm paper white)
- Path-line: `#22D3EE` (electric cyan — "the path / intelligence")
- Wordmark: Inter weight 800, tracking -0.04em
- Atmosphere: subtle cyan + amber radial gradients (matches `tokens/colors.css`)

To regenerate any of these or add new sizes, the in-app `BrandMark` React component (`src/components/wall/BrandMark.tsx`) and the existing OG card (`public/og-image.svg`) are the canonical source of truth — keep new artwork visually consistent.
