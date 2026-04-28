# lib/wall — Wall library

> Single import surface for everything below the UI layer: design tokens, audio, env validation, types, network helpers, storage, logging, feature detection, brand assets, cinematic timing, and landmark map.

## Public API

```ts
import {
  // Tokens (TS mirrors of CSS tokens)
  SPRING_SOFT, SPRING_SNAPPY, SPRING_ELASTIC,
  EASE_LINEAR_SIG, EASE_OUT, DURATION_BASELINE_MS,
  STAGGER_CHILD_OFFSET_S, FONT_AXES,
  // Env validation
  validateMapboxToken, isMapboxAvailable, getMapboxToken,
  // Types
  type ChapterId, type TimePhase, type AccentShift, type SoundId,
  // Audio (namespaced — `sound.play(...)`)
  sound,
  // Network detection
  getNetworkProfile, isSaveDataOn, isSlowConnection,
  // Storage (Wave 2 cross-driver fix)
  STORAGE_KEYS, getStored, setStored, removeStored,
  // Feature detection (Spotlight)
  hasViewTransitions, hasContainerQueries, hasColorMix,
  hasOklch, hasVibration, hasBatteryAPI, detectFeatures,
  // Brand asset registry (Spotlight)
  BRAND_ASSETS, getAsset,
  // Cinematic timing (Spotlight)
  CINEMATIC_STEPS, CINEMATIC_TOTAL_MS, getCinematicStep,
  // Landmark map (Spotlight)
  LANDMARKS, getLandmark,
  // Logger (Spotlight)
  log,
} from "@/lib/wall";
```

## Modules

### `tokens.ts`
TS-side mirrors of motion + axis tokens declared in `app/styles/tokens/*.css`. Spring presets (SOFT/SNAPPY/ELASTIC), easings (LINEAR_SIG/OUT), durations, stagger, font axes (wght/opsz/slnt). Never use a magic ms/stiffness number — always reach for these.

### `env.ts`
Mapbox public-token validator. `getMapboxToken()`, `validateMapboxToken()`, `isMapboxAvailable()`. Rejects `sk.*` secret tokens loud-and-early.

### `sound.ts` (namespace: `sound`)
Howler-backed audio singleton. Lazy-imports Howler on first unmuted play. Default state: muted (`gowork.muted` localStorage). API: `sound.play()`, `stop()`, `setMuted()`, `isMuted()`, `setVolume()`, `getVolume()`, `unlock()`. Five sound IDs: `footstep`, `paper-rustle`, `calculator-click`, `chime`, `wind-ambient`.

### `types.ts`
Shared types: `ChapterId` (1..10), `TimePhase`, `AccentShift`, `SoundId`, `LocaleCode`, `BarrierType`, `BarrierGraphNode`, `RumSessionId` (branded), `CameraState`, `MapboxLayer`.

### `network.ts`
`getNetworkProfile()` from `navigator.connection`; effectiveType normalized to `2g|3g|4g|unknown`; `isSaveDataOn()`, `isSlowConnection()` helpers.

### `storage.ts` (Wave 2)
Canonical localStorage / sessionStorage key namespace. Single export `STORAGE_KEYS` + typed helpers `getStored<T>()`, `setStored()`, `removeStored()`. Never declare a raw key in a component.

### `featureDetect.ts` (Spotlight)
Centralizes browser feature probes that components scatter inline. `hasViewTransitions()`, `hasContainerQueries()`, `hasColorMix()`, `hasOklch()`, `hasVibration()`, `hasBatteryAPI()`. Aggregate: `detectFeatures()` returns `FeatureFlags`.

### `brandAssets.ts` (Spotlight)
Registry of every brand asset (svg, raster, font, audio) with paths + descriptions. `BRAND_ASSETS` array + `getAsset(name)` lookup. Powers `/dev/tokens` + audit scripts.

### `cinematic.ts` (Spotlight)
First-paint timing tokens. `CINEMATIC_STEPS` array with `{id, delayMs, durationMs, easing, intent}` for `presenter | title | subtitle | handoff`. Total: 4.6s. `getCinematicStep(id)` lookup.

### `landmarks.ts` (Spotlight)
Keyboard-skip landmark map. `LANDMARKS` array with `{id, anchor, labelKey}` for `main | header | footer | chapters`. SkipToContent v2 (W4) renders a menu sourced from this.

### `log.ts` (Spotlight)
Structured logger. `log.{debug,info,warn,error}` + `log.withScope(name)`. Dev-only debug/info; warn/error always fire. Pipes through error-reporter for production telemetry.

## Architecture compliance

Every module is < 200 lines, every function < 50 lines, every file < 15 functions. Run `bpsai-pair arch check frontend/src/lib/wall/` to verify.

## Test surface

Every public API has paired tests under `__tests__/`. Coverage gate: >= 95% statements. Run with:

```sh
cd frontend && npx vitest run src/lib/wall/__tests__/
```

## See also

- `frontend/src/components/wall/README.md` — UI components
- `frontend/src/hooks/` — React hooks built on top of these primitives
- `frontend/src/app/styles/tokens/*.css` — paired CSS token partials
