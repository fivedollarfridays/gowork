# Mapbox Studio — Custom Dark Editorial Style Runbook

> **Owner:** GoWork Visual Rebirth · The Wall · Sprint W2 · Driver A lane
> **Audience:** anyone setting up the GoWork Mapbox Studio account from
> scratch (Shawn, future maintainer, judge demo recovery path).
> **Time budget:** ~30 minutes (one-time, manual).

---

## Why this runbook exists

The Wall's editorial dark map style is the difference between "looks like
a default Mapbox demo" and "looks like a piece of journalism." Mapbox
Studio is a manual GUI tool — without a written procedure, every rebuild
drifts. This runbook is the contract: the same steps produce the same
style, every time.

**If you have to rebuild from scratch** (Studio account loss, vendor
rotation, multi-city expansion), the JSON export at
`frontend/data/mapbox-style-export.json` is your recovery artifact —
import it as a new style and skip to step 7.

---

## Prerequisites

- Mapbox account with Studio access (free tier is fine for W2 demo)
- A public access token (`pk.…`) — already wired via
  `NEXT_PUBLIC_MAPBOX_TOKEN`
- W1 design-token reference at `frontend/src/app/styles/tokens/colors.css`
  for the OKLCH values referenced below

---

## Step 1 — Create the dark base

1. Sign in at https://studio.mapbox.com/
2. Click **New style**
3. Pick the **Mapbox Dark v11** template
4. Name it **GoWork Wall — Dark Editorial v1**
5. Set the description to a single line citing this runbook so future
   maintainers can find it: `Built per docs/runbooks/mapbox-style-setup.md`

## Step 2 — Streets in `--bg-elevated`

1. Open the **Land** group → all street layers (`road-*`)
2. Set color to **OKLCH(0.30 0.02 250)** — matches W1 `--bg-elevated`
3. Set casing color to **OKLCH(0.25 0.02 250)** — slightly darker (subtle
   1px casing keeps streets legible at zoom 14)
4. Reduce road label visibility — labels appear only at zoom 12+

## Step 3 — Water in `--bg-surface` (Trinity River call-out)

1. Open the **Water** layer
2. Set fill color to **OKLCH(0.22 0.04 250)** (W1 `--bg-surface`, with a
   touch of cyan saturation for water mood)
3. (Optional) Add a subtle grain texture via Mapbox's `raster` overlay if
   the design plan requests it. Trinity River runs through downtown FW —
   make sure it's visible at zoom 11 without competing with the Wall's
   editorial overlay.

## Step 4 — Parks / green spaces

1. Open the **Land use** group → `landuse_overlay-park` + `landuse-park`
2. Tint with **OKLCH(0.32 0.04 145)** — muted green, low saturation
3. Forest Park, Trinity Park, Gateway Park should all read as parks at
   zoom 13–14 without dominating the composition

## Step 5 — 3D buildings (extruded, amber edges)

1. In the **Layers** panel, click **+** → **Add layer**
2. Source: `composite` → `building` (the standard Mapbox building tiles)
3. Type: **Fill extrusion**
4. Set `fill-extrusion-color` to **OKLCH(0.30 0.02 250)** (matches
   streets — buildings are part of the same surface)
5. Set `fill-extrusion-height` to a data-driven property:
   `["interpolate", ["linear"], ["zoom"], 13, 0, 15.05, ["get", "height"]]`
6. Set `fill-extrusion-opacity` to **0.75**
7. (Editorial detail) Add a thin amber rim using `fill-extrusion-edge` if
   the Mapbox Studio version supports it; otherwise overlay the amber
   accent at the React layer

## Step 6 — Labels in `--fg-primary` at -0.04em tracking

1. Open the **Place labels** group
2. Set text color to **OKLCH(0.94 0.005 250)** (W1 `--fg-primary` warm
   white)
3. Set letter-spacing to **-0.04em** (Mapbox uses `text-letter-spacing`,
   in em)
4. Apply to country/state/city/neighborhood labels uniformly
5. Set `text-allow-overlap` to **false** and `text-ignore-placement` to
   **false** to prevent flicker on zoom (T2.80 collision avoidance)

## Step 7 — Boundary lines

1. Open the **Admin** group
2. State/country boundaries: **OKLCH(0.55 0.01 250)** (W1 `--fg-muted`)
3. County boundaries: same color, `line-dasharray: [2, 4]`, width 1px,
   visible only at zoom 9–13 (T2.97)
4. ZIP-level boundaries: hide entirely — the W2 layer composer adds 76119
   as a custom highlight (T2.13)

## Step 8 — Publish + capture URL

1. Click **Publish** in Studio
2. After publishing, click **Share, develop & use** → copy the
   **Style URL** under **Use this style in your app**
3. URI format: `mapbox://styles/<account-id>/<style-id>`
4. Paste this URI into `frontend/.env.local` as
   `NEXT_PUBLIC_MAPBOX_STYLE_URL`
5. (Production) Add the same value to your Vercel/host env vars

## Step 9 — Export JSON for archival

1. In Studio, click **More options** → **Download style** → **JSON**
2. Save to `frontend/data/mapbox-style-export.json` (commit to repo)
3. This is your recovery artifact — see "Recovery from JSON" below

## Step 10 — Verify in dev

1. `npm run dev` from `frontend/`
2. Navigate to `/`
3. The Wall should render with the editorial dark style — no jarring
   default-Mapbox blue water, no default road styling
4. Check console: no warnings about missing layers/styles
5. (Smoke) Briefly remove the env var and reload — the page should fall
   back to the stock dark style without breaking

---

## Recovery from JSON (if Studio account lost)

1. Sign in to a new Mapbox Studio account
2. Click **New style** → **Upload style** → select
   `frontend/data/mapbox-style-export.json`
3. Review the imported style — coordinates may need re-publishing
4. Continue from Step 8 (publish + capture URL)

---

## Light variant (W3 reuse — `/assess` + `/plan`)

Repeat steps 1–9 with the **Mapbox Light v11** template instead of dark.
Use the same OKLCH values where possible — W1 tokens have light/dark
parity. Wire the resulting URI as a separate env var
`NEXT_PUBLIC_MAPBOX_STYLE_URL_LIGHT` (W3 will define this contract).

---

## Open polish (deferred from W2 enrichment phase)

These polish items are tracked in the W2 backlog but are non-blocking
for the demo. Wire them in a second Studio session if there's time:

- **T2.80 Label collision avoidance** — confirm Step 6 setting holds
  across zooms 11/12/13/14
- **T2.81 Water grain texture** — optional raster overlay
- **T2.83 Boundary lines** — re-verify county dashed style after publish
- **T2.105 Trinity River specific styling** — slight cyan boost vs other
  water bodies

---

## Reviewer agent verification

This runbook MUST be unambiguous to someone unfamiliar with Mapbox
Studio. If a reviewer cannot follow it from a cold start, file a
follow-up issue against this file.

慣性の契約.
