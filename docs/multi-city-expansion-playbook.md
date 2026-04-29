# GoWork — Multi-City Expansion Playbook

> **Authored:** W5 Driver D (Spotlight invention).
> **Audience:** Contributors deploying GoWork in a new city — Dallas,
> Houston, Birmingham, Atlanta, Memphis, Indianapolis, anywhere.
> **Status:** Codified from the Fort Worth + Montgomery deployment
> patterns (W1–W5).
>
> The framework is multi-city by **architecture**, not by branding.
> Adding a new city is configuration + data + a Mapbox style URL.
> Estimated time for a developer familiar with the codebase: **2-4
> hours** for a basic deployment, **2-3 days** for production polish
> (tested barriers, real GTFS, real benefits API integration).

---

## What "deploying a new city" actually means

GoWork's framework is composed of:

| Layer | Source | Per-city |
|---|---|---|
| **City config** | `frontend/src/lib/cities/` | YES |
| **Mapbox style URL** | Mapbox Studio | YES |
| **Barrier graph DAG** | `frontend/src/data/barriers/` | YES |
| **State-level modules** | `frontend/src/lib/states/` | Per state |
| **GTFS transit layer** | `frontend/src/lib/wall/layers/` | YES |
| **Benefits API integration** | `backend/app/services/benefits/` | Per state |
| **Expungement statute** | `backend/app/services/expungement/` | Per state |
| **EN + ES translations** | `frontend/src/lib/translations/` | Mixed |
| **Wall chapters** | `frontend/src/components/wall/chapters/` | NO (city-agnostic) |
| **Press kit + Devpost copy** | `docs/` | Mixed |

The **Wall chapters themselves are city-agnostic** — they walk through
"a worker", "the wall", "the math", "the path", "the graph". The
*data* and *Mapbox imagery* swap when the city config swaps.

---

## Step-by-step: Adding "Dallas, TX"

This is a worked example for adding the third city. Adapt for any.

### Step 1 — Generate the scaffold (1 command)

```bash
node scripts/new-city-scaffold.mjs --slug=dallas --name="Dallas, TX" --state=TX
```

The scaffold creates:

- `frontend/src/lib/cities/dallas.ts` — city config stub
- `frontend/data/dallas/barriers.json` — barrier graph stub
- `frontend/src/lib/translations/cities/dallas.en.json` + `.es.json`
- `frontend/src/__tests__/cities/dallas.test.ts` — guard test

You commit those, then fill them in. Without the scaffold script you'd
hand-create ~7 files; the script enforces the directory shape.

### Step 2 — Fill the city config (~30 min)

`frontend/src/lib/cities/dallas.ts`:

```ts
import type { CityConfig } from "./types";

export const DALLAS_CONFIG: CityConfig = {
  slug: "dallas",
  name: "Dallas, TX",
  state: "TX",
  centerLng: -96.7970,
  centerLat: 32.7767,
  defaultZoom: 11,
  mapboxStyleUrl: "mapbox://styles/<your-account>/<style-id>",
  // Reference key landmarks — chapters reference these by id.
  landmarks: {
    "downtown": { lng: -96.7970, lat: 32.7767 },
    "warehouse-district": { lng: -96.823, lat: 32.778 },
    // ...
  },
  // Trinity Metro analog: DART for Dallas.
  transitProvider: "DART",
  // ...
};
```

The `CityConfig` type is the contract. TypeScript will enforce every
required field.

### Step 3 — Mapbox style (15 min)

1. Go to https://studio.mapbox.com/.
2. Create a new style based on the existing GoWork dark editorial
   style (`docs/architecture-decisions/0003-mapbox-custom-dark-style.md`
   has the recipe).
3. Set the center to your city. Tune zoom defaults.
4. Publish. Copy the style URL into your city config.
5. (Optional) Custom labels / 3D buildings / hillshade if your city
   has the data.

### Step 4 — Barrier graph (~1 hour, depends on data)

`frontend/data/dallas/barriers.json`:

```json
{
  "barriers": [
    { "id": "B-CREDIT-DAL-1", "type": "credit", "city": "dallas", "data": { ... } },
    { "id": "B-TRANSIT-DAL-1", "type": "transit", "city": "dallas", "data": { ... } },
    ...
  ],
  "edges": [
    { "from": "B-TRANSIT-DAL-1", "to": "B-EMPLOYMENT-DAL-1", "weight": 0.7 },
    ...
  ]
}
```

Reuse types from Fort Worth's barrier set. The DAG shape is:

- Nodes: barriers (credit, transit, custody, record, childcare, etc.)
- Edges: which barrier unblocks which next
- Weights: probabilistic completion ordering

The `path completeness` score derives from this graph.

### Step 5 — State modules (~30 min if state already supported)

If Dallas: Texas state modules already exist (HHSC benefits, Article
55 expunction). No new state code needed.

If you're adding a city in a new state (say, Florida, Tampa):

- `backend/app/services/benefits/florida.py` — Florida benefits API
  integration
- `backend/app/services/expungement/florida.py` — Florida expungement
  statute
- Add the state to `backend/app/services/states/registry.py`

### Step 6 — GTFS transit layer (~1 hour, depends on GTFS quality)

`frontend/src/lib/wall/layers/dartLight.ts`:

```ts
import { GTFS_DAL } from "@/data/dallas/gtfs/dart-light";
// ... build a GeoJSON feature collection of DART rail stations + buses
export const DART_LIGHT_LAYER = { ... };
```

Mapbox renders this as an additional layer on the city style.

### Step 7 — EN + ES translations (~30 min)

`frontend/src/lib/translations/cities/dallas.en.json` already exists
from the scaffold. Fill in city-specific strings:

```json
{
  "city": "Dallas",
  "cityFull": "Dallas, Texas",
  "transitProvider": "DART",
  "landmarks": {
    "downtown": "downtown Dallas",
    "warehouseDistrict": "the Stemmons / Trinity industrial corridor"
  },
  ...
}
```

Mirror in `dallas.es.json`. The parity test will catch any drift.

### Step 8 — Wire it in (~15 min)

Register the city in `frontend/src/lib/cities/registry.ts`:

```ts
import { DALLAS_CONFIG } from "./dallas";
import { FORT_WORTH_CONFIG } from "./fort-worth";
import { MONTGOMERY_CONFIG } from "./montgomery";

export const CITIES = {
  "fort-worth": FORT_WORTH_CONFIG,
  "montgomery": MONTGOMERY_CONFIG,
  "dallas": DALLAS_CONFIG,
} as const;
```

Add `?city=dallas` route handling in the Wall (already supported by
`useCityConfig` from W1).

### Step 9 — Verify (~10 min)

```bash
cd frontend
npx vitest run src/__tests__/cities/dallas.test.ts
npx tsc --noEmit
npm run lint
npm run audit:tokens
```

Browse to `http://localhost:3000/?city=dallas`. The Wall should
render with Dallas geography.

### Step 10 — Production polish (~1-3 days)

- Real GTFS feed with Tuesday-pulled live data (cache invalidation
  policy)
- Real benefits API integration (TX HHSC if Texas city, equivalent
  for new state)
- Real fair-chance employer list (curated, not scraped)
- ADA / a11y audit for the new map style
- Lighthouse perf check on the new city's tile load
- Spanish copy review with a native speaker
- (Optional) Per-city Mapbox style polish — building extrusions,
  hillshade, custom labels

---

## What NOT to do

**Don't fork the chapter components per city.** Chapters are
city-agnostic. They take a `cityConfig` prop and render the right
landmarks. If you find yourself copying `Chapter02CityArrival.tsx` to
`Chapter02DallasArrival.tsx`, stop — that's a regression in the
framework.

**Don't hardcode coordinates in chapter components.** Coordinates
live in `cameraChoreography.ts` (camera targets) or `landmarks` in
the city config. The `useCityConfig()` hook resolves them at render
time.

**Don't translate the hero thesis per city.** The hero question and
framework tagline are *brand-level* (locked in `docs/copy-thesis.md`).
The city's role is to localize the *concrete examples* (downtown
Dallas vs downtown Fort Worth, DART vs Trinity Metro, etc.) — not to
re-pitch the framework.

**Don't deploy without the parity test.** EN/ES parity is a civic
obligation, not a courtesy. The test will fail your build if a key
exists in `en.json` but not `es.json`. Fix the gap; don't suppress
the test.

---

## Cost calibration

For a developer familiar with React + Mapbox + TypeScript:

| Phase | Time | Notes |
|---|---|---|
| Scaffold + city config | 30-45 min | Mostly boilerplate |
| Mapbox style | 15-30 min | Studio UI |
| Barrier graph | 1-3 hours | Depends on data availability |
| State modules | 30 min – 1 day | 30 min if state supported |
| GTFS layer | 1-2 hours | Depends on feed quality |
| Translations | 30-60 min | + native speaker review |
| Wire-in + verify | 30 min | Mostly mechanical |
| **Basic deploy** | **2-4 hours** | If no new state |
| **Production polish** | **2-3 days** | Real data + a11y + perf |

---

## Real-world examples

### Adding Fort Worth (the reference deployment)

Implemented across W1-W5. `docs/visual-rebirth-briefs.md` documents
the per-sprint work. Major decisions in
`docs/architecture-decisions/`. The ZIP-76119 + Bus 4 + Tarrant
County District Clerk + Amazon DFW5 anchors are real.

### Adding Montgomery, Alabama (the second city)

Implemented in S2-S6 (pre-visual-rebirth). Required new state
modules: 7 Alabama benefits programs, Act 2021-507 expungement.
Mapbox style adapted from FW with adjusted center + zoom defaults.
Trinity Metro-like transit layer became Montgomery's MAX bus
analog.

### What a third city looks like (Dallas)

Outline above. Texas state modules already done. New scope: city
config + Mapbox style + DART layer + Dallas barrier graph + EN/ES
translations. Estimated: 4-6 hours for a basic deploy.

---

## See also

- [`docs/contributors-onboarding.md`](contributors-onboarding.md) — getting started
- [`docs/architecture.md`](architecture.md) — system shape + scoring
- [`docs/architecture-decisions/`](architecture-decisions/) — ADRs
- [`scripts/new-city-scaffold.mjs`](../scripts/new-city-scaffold.mjs) — scaffold CLI
- `frontend/src/lib/cities/types.ts` — `CityConfig` type definition
- `frontend/src/hooks/useCityConfig.ts` — how chapters resolve city config

---

> **C4 honest uncertainty:** Time estimates above assume the new
> state's benefits API has a documented schema and the city's GTFS
> feed is well-formed. Some states' workforce APIs are PDF-only;
> some city GTFS feeds drop schedule updates without a version bump.
> If the data layer fights you, the city expansion takes a week, not
> a day. Open an issue tagged `city-expansion-friction` if you hit a
> wall — we'll probably learn something we can codify here.
