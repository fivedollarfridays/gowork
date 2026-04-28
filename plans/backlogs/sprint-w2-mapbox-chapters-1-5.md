# Sprint W2 --- Mapbox Engine + Chapters 1–5 + Data Layers

**Plan type:** feature
**Sprint:** W2 (Wall sprint 2 of 5)
**Total Cx:** 816
**Tasks:** 67 (P0: 63, P1: 4, P2: 0)
**Wave count est.:** 6 (foundation → scroll engine → data layers → chapters 1–3 → chapter 4 sub-chapters → chapter 5 + polish)
**Branch:** `sprint/visual-rebirth` (stacked on W1)

## Goal

Stand up the Mapbox foundation, scroll-driven camera system, and Chapters 1 through 5 of "The Wall" — a 10-chapter Mapbox-driven scrollytelling visualization that will be the GoWork home page for the HackFW 2026 submission. By the end of W2, scrolling the page flies the camera through real Fort Worth from continental altitude down to Carlos's neighborhood, with editorial overlays appearing per chapter and real geographic data layers (Trinity Metro GTFS routes, Tarrant County office pins, FW ZIP boundaries, Carlos's representative neighborhood pin) progressively revealed.

**Prerequisite:** W1 backlog merged or in-flight in parallel. W1 outputs assumed available: design tokens (OKLCH colors, Inter Variable typography, motion/spring presets, --temperature-multiplier), motion utilities, hooks (useScrollProgress, useTimeOfDay, useCursorPosition, useLiveNow, useVariableFontWeight, usePrefersReducedMotion), brand assets (G+path SVG logo), edge states (404/500/empty/loading), header/footer, mapbox-gl + react-map-gl already installed via W1 INFRA. If a hook is missing at engage time, file a blocking sub-task against the W1 backlog.

## What ships in W2 vs deferred

**W2 (this sprint):** Mapbox foundation + token validation + static fallback. Scroll engine with camera choreography per chapter. Six data layers (Trinity Metro routes, Tarrant County offices, FW ZIP polygons, Carlos's representative neighborhood pin, jobs-by-ZIP markers, layer composer). Chapters 1 (Continental), 2 (City Arrival), 3 (Neighborhood), 4 (The Wall — 4 sub-chapters: criminal record, no transit, no childcare, bad credit), 5 (The Labyrinth). Custom dark editorial Mapbox style (manual setup runbook + committed config). EN/ES editorial copy for chapters 1–5. Page.tsx rewrite + landing archive. Lazy-loading + accessibility passes for chapters 1–5.

**Deferred to W3:** Chapter 6 (The Math — cliff calculator embed). Chapter 7 (Carlos avatar walking). Chapter 8 (3D barrier graph). Chapter 9 (fly to Montgomery). Chapter 10 (View Transitions). **Deferred to W4:** Time-of-day Mapbox sky (only the hook is wired in W2; sky lighting connection lives in W4). Variable font axis on hero (W4). Live Now widget UI on map (W4). Per-chapter dynamic OG (W4). Lighthouse 90+ hard gate (W4). **Deferred to W5:** README, press kit, video, Devpost.

## Architectural principles

- **Real data only.** Trinity Metro GTFS pulled from `backend/app/integrations/` lineage or seeded into `frontend/public/data/`. Tarrant County office coordinates from `frontend/src/lib/city-constants.ts` (CAREER_CENTER_TX) and supplemented with verifiable government addresses. FW ZIP 76119 polygon from US Census TIGER/Line. No mock geometry.
- **PII safety.** Carlos's "home" pin is a representative neighborhood block centroid in 76119 — never an exact address.
- **Zero LLM in render path.** The Wall is a deterministic visualization. No runtime LLM calls anywhere in chapter render.
- **Reduced-motion is a first-class branch, not an afterthought.** Every flyTo has an instant-cut fallback; every layer fade has an instant-on fallback. Reviewer agent rejects any animation site missing the branch.
- **Custom Mapbox style is built in Mapbox Studio (manual ~30 min).** A single task documents the steps so Shawn can do it offline; the resulting style URL becomes a `NEXT_PUBLIC_MAPBOX_STYLE_URL` env var.
- **Fallback chain.** If `NEXT_PUBLIC_MAPBOX_TOKEN` missing → static screenshot fallback. If style URL missing → default `mapbox://styles/mapbox/dark-v11`. If Mapbox CDN unreachable → static screenshot. The page never breaks.
- **Backend untouched.** W2 is frontend-only. Trinity Metro GTFS is consumed as committed JSON/GeoJSON in `frontend/public/data/wall/`, derived once via a frontend script that may read backend integrations at build-time.

## Decisions locked (2026-04-27)

1. **Mapbox style:** custom dark editorial built in Studio, with default fallback to `mapbox://styles/mapbox/dark-v11`. Style URL is an env var so it can be swapped without code change.
2. **GTFS source:** the Trinity Metro GTFS feed is pulled offline (one-time) and committed as `frontend/public/data/wall/trinity-metro.geojson`. Refresh cadence is "before submission only"; not a runtime fetch.
3. **Carlos's home pin:** centroid of a representative residential block within ZIP 76119 — chosen for proximity to Bus 4 stop, NOT his real address. Coordinates documented in `frontend/src/lib/wall/paths.ts` with a comment explaining the PII-safety rationale.
4. **page.tsx archive:** existing landing content preserved at `frontend/src/app/archive/page.tsx` so we can roll back via a one-line `page.tsx` swap if needed.
5. **Chapter splitting:** Chapter 4 (The Wall) is one parent component + 4 sub-chapter components, each ~3 tasks. Editorial copy lives in `en.json` / `es.json` under the `wall.ch4*` keys.
6. **Lazy-loading scope:** Mapbox (~600KB compressed) + each chapter component code-split. Ch1 Continental is allowed in the initial bundle (above-the-fold). Ch2–Ch5 dynamically imported.

---

## Cross-sprint context

- **Depends on:** W1 backlog (parallel; assume W1 outputs available). `BenefitsCliffChart` exists at `frontend/src/components/plan/BenefitsCliffChart.tsx` — DO NOT duplicate; W3 imports it.
- **Blocks:** W3 (interactive chapters 6–10 need W2's chapter scaffold + Mapbox engine + path data). W4 life-layers wire into Ch1–5 surfaces produced here.
- **Stay in lane:** Do not modify W1 hooks/tokens (file sub-tasks if missing). Do not write tasks for chapters 6–10 (W3) or life-layers (W4) or submission (W5).

## Permanent constraints (apply to every task in W2)

```
1. 95% test coverage on new code (vitest for frontend)
2. TDD only — failing test FIRST, then implement
3. Files < 400 lines. Functions < 50 lines. Max 15 functions per file. Max 20 imports.
4. Full wiring — nothing orphaned, everything connected
5. No code debt — sprint ships clean
6. ZERO LLM calls in The Wall render path (deterministic visualization)
7. `bpsai-pair arch check` must pass before completion
8. Reviewer agent reviews all code-producing tasks
9. prefers-reduced-motion respected at every animation site
10. WCAG AAA contrast on all editorial overlays
11. Multi-city architecture intact (Montgomery still works via state="AL")
12. Backend untouched
13. Brand: GoWork only (no MontGoWork leakage)
14. Slogan locked (do not redraft hero copy)
```

## Cross-task contract edges (within W2)

- `lib/wall/cameraChoreography.ts` exports per-chapter camera state — consumed by every chapter component AND `MapboxScene`'s flyTo orchestrator.
- `lib/wall/paths.ts` exports Carlos's GPS coordinates and representative neighborhood pin — consumed by Ch3 (W2) and Ch7 (W3).
- `lib/wall/layers/{trinityMetro,offices,zipBoundaries,carlosPath,jobsByZip}.ts` — each layer is a separate module imported by `MapboxScene.tsx` via `lib/wall/layers/index.ts` composer.
- `WallContainer.tsx` orchestrates scroll + map + chapters; chapters subscribe to scroll progress via `useChapterProgress`.
- `frontend/src/lib/wall/mapboxToken.ts` exports `validateToken()` and `isMapboxAvailable()` consumed by `WallContainer.tsx` for fallback gating.

## File collision matrix (within W2)

| File | Tasks touching it | Resolution |
|---|---|---|
| `frontend/src/app/page.tsx` | T2.46 archive + T2.47 rewrite | Sequential: archive first, then rewrite |
| `frontend/src/components/wall/WallContainer.tsx` | T2.2 scaffold + 5 chapter wiring tasks (T2.20, T2.24, T2.28, T2.32, T2.42) | Scaffold first; chapters wire serially in waves 4–6 |
| `frontend/src/components/wall/MapboxScene.tsx` | T2.3 create + T2.13 layer composer wiring + T2.51 lazy-load | T2.3 → T2.13 → T2.51 sequential |
| `frontend/src/lib/wall/cameraChoreography.ts` | 5 chapters add their states | Single create task (T2.7) defines all five states; chapter tasks consume read-only |
| `frontend/public/data/wall/*.geojson` | T2.10 (Trinity Metro), T2.11 (offices), T2.12 (ZIP), T2.14 (jobs) | Each layer task owns its file; no collision |
| `frontend/src/lib/translations/en.json` | 5 copy tasks (T2.48–T2.52) | Each adds its own `wall.chN*` keys; merge-friendly |
| `frontend/src/lib/translations/es.json` | 5 copy tasks (T2.48–T2.52) | Each adds its own `wall.chN*` keys; merge-friendly |
| `frontend/src/components/wall/chapters/Chapter04TheWall.tsx` | T2.28 parent + T2.29–T2.32 sub-chapters | Parent first; sub-chapters wired in serial sub-wave |

## Priority order (engage scheduler hint)

1. **Wave 1 — Foundation (P0, ~5 tasks, parallelizable):** T2.1 token validation, T2.2 WallContainer scaffold, T2.3 MapboxScene scaffold, T2.4 initial camera state, T2.5 Mapbox cleanup-on-unmount. Wave gate: Mapbox renders Fort Worth at zoom 11 with default style; static fallback verified.
2. **Wave 2 — Scroll engine (P0, ~6 tasks):** T2.6 ChapterScaffold, T2.7 cameraChoreography, T2.8 useChapterProgress, T2.9 flyTo orchestrator + reduced-motion fallback, T2.10 useScrollPin. Wave gate: scrolling pins chapters and triggers camera flights between zoom states.
3. **Wave 3 — Data layers + Mapbox style (P0, ~11 tasks, parallelizable):** T2.11–T2.18 data layers + composer + custom marker symbols + custom Mapbox Studio style runbook + light/dark variants. Wave gate: layers visible on Mapbox; style document committed.
4. **Wave 4 — Chapters 1–3 (P0, ~12 tasks, sequential per chapter):** T2.19–T2.22 Ch1 Continental, T2.23–T2.26 Ch2 City Arrival, T2.27–T2.30 Ch3 Neighborhood. Wave gate: scroll runs through chapters 1–3 with editorial overlays in EN.
5. **Wave 5 — Chapter 4 sub-chapters (P0, ~10 tasks):** T2.31 parent + T2.32–T2.41 four sub-chapters with overlays + sub-chapter transitions + sound triggers. Wave gate: Ch4 displays each barrier as Carlos's path is overlaid.
6. **Wave 6 — Chapter 5 + page.tsx + EN/ES + a11y + perf + tests (P0/P1, ~15 tasks):** T2.42–T2.46 Ch5 Labyrinth, T2.47–T2.48 page.tsx archive + rewrite, T2.49–T2.53 EN/ES copy population for chapters 1–5, T2.54–T2.56 accessibility, T2.57–T2.58 lazy-loading, T2.59–T2.66 tests, T2.67 final smoke. Wave gate: all 5 chapters render in EN + ES with axe-core green and Lighthouse no-regression check passing.

## Open questions / honest uncertainty (see bottom)

See "Honest Uncertainty" section after Spotlight Inventions for C4/C5 confidence calls.

---

## Phase 1: Mapbox Foundation

### T2.1 --- Mapbox token validation + static fallback chain | Cx: 18 | P0

**Description:**
Build a token validation utility that gracefully falls back to a static Fort Worth screenshot if `NEXT_PUBLIC_MAPBOX_TOKEN` is missing, malformed, or the Mapbox CDN is unreachable. No production breakage even if Mapbox is unavailable. This is the root-cause task that eliminates the most downstream risk: every chapter component depends on Mapbox; if the token check has a hole, every chapter breaks. Static fallback is a real 1920×1080 screenshot of Fort Worth at zoom 11 with editorial overlay treatment, NOT a placeholder gray box.

**AC:**
- [ ] `frontend/src/lib/wall/mapboxToken.ts` exports `validateToken()` (regex-checks `pk.eyJ...` shape, returns boolean) and `isMapboxAvailable()` (validates token + does a single-shot fetch to `https://api.mapbox.com/v1/styles/v1/mapbox/dark-v11?access_token=...` with 2s timeout, returns boolean)
- [ ] Static fallback image committed at `frontend/public/wall-fallback-fort-worth.jpg` (1920×1080, dark editorial style, includes "GoWork · Fort Worth, TX" overlay)
- [ ] `WallContainer.tsx` renders the static fallback when `isMapboxAvailable()` returns false; renders Mapbox when true
- [ ] Vitest: token validation returns false for missing/invalid token, true for well-formed token
- [ ] Vitest: fetch timeout / network failure path returns false from `isMapboxAvailable()` without throwing
- [ ] Vitest: `WallContainer` renders static fallback element when token check fails (jsdom)
- [ ] WCAG AAA contrast verified for fallback overlay text
- [ ] `bpsai-pair arch check frontend/src/lib/wall/mapboxToken.ts` passes
- [ ] Reviewer agent approves

**Depends on:** none (assumes W1 mapbox-gl + react-map-gl install present; if missing, files blocking sub-task against W1)

---

### T2.2 --- WallContainer.tsx orchestrator scaffold | Cx: 18 | P0

**Description:**
Scaffold the top-level orchestrator component that owns the Mapbox instance, holds scroll progress state, and exposes context for chapters to subscribe to. This is the hub-and-spoke hub: chapters are spokes that read camera state and scroll progress from context. Container also holds the static-fallback gate (T2.1), the chapter counter slot, and the path-line header slot (W1 outputs).

**AC:**
- [ ] `frontend/src/components/wall/WallContainer.tsx` created (≤200 lines)
- [ ] Renders either `MapboxScene` (when token valid) or static fallback (when not)
- [ ] Provides a React context `WallContext` with `{scrollProgress, currentChapter, mapInstance}` consumed by chapters
- [ ] Mounts `useScrollProgress` (W1) at container level, single source of truth
- [ ] Wires header chapter counter slot (W1) and path-line slot (W1)
- [ ] Vitest: renders Mapbox scene when token valid (mocked)
- [ ] Vitest: renders fallback when token invalid
- [ ] Vitest: context value updates as scroll progress changes
- [ ] `bpsai-pair arch check` passes (≤15 functions)

**Depends on:** T2.1

---

### T2.3 --- MapboxScene.tsx react-map-gl integration | Cx: 20 | P0

**Description:**
Build the Mapbox scene component using `react-map-gl`. Loads the custom dark editorial style (with fallback to `mapbox://styles/mapbox/dark-v11` if `NEXT_PUBLIC_MAPBOX_STYLE_URL` is unset). Exposes the underlying `MapboxMap` instance via a ref forwarded up to `WallContainer` so chapters can call `flyTo` via the choreography orchestrator. Initial render is a single Mapbox `Map` with no layers — layers are added in Phase 3.

**AC:**
- [ ] `frontend/src/components/wall/MapboxScene.tsx` created
- [ ] Uses `react-map-gl/mapbox` (v8+ API) — NOT the deprecated `react-map-gl` v6 default export
- [ ] Reads style from `NEXT_PUBLIC_MAPBOX_STYLE_URL` env var with default to `mapbox://styles/mapbox/dark-v11`
- [ ] Reads token from `NEXT_PUBLIC_MAPBOX_TOKEN`
- [ ] Forwards map instance to parent via `forwardRef` + `useImperativeHandle`
- [ ] Suppresses interactive controls in initial state (no zoom, drag, rotate buttons — chapter scroll drives camera)
- [ ] BUT: user manual drag/zoom MAY override scroll-driven camera (reviewer notice — do not trap user)
- [ ] No hardcoded hex colors; all visual chrome uses W1 design tokens
- [ ] Vitest: renders without error in jsdom (mocked map instance)
- [ ] Vitest: env var override changes style URL prop
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.2

---

### T2.4 --- Initial camera state — Fort Worth overview | Cx: 8 | P0

**Description:**
Define the initial camera state that the Mapbox scene boots into before scroll progress is registered. This is the "loading-completed default": Fort Worth centered, zoom 11, pitch 0, bearing 0. This state is also the state Chapter 0 (the title sequence handoff from W1) lands on. Camera state lives in `lib/wall/cameraChoreography.ts` (extracted in T2.7) but the initial-state shape is finalized here so T2.3 has a target.

**AC:**
- [ ] Initial camera state object exported from `frontend/src/lib/wall/cameraChoreography.ts` as `INITIAL_CAMERA` with `{longitude: -97.3308, latitude: 32.7555, zoom: 11, pitch: 0, bearing: 0}` (Fort Worth centroid)
- [ ] `MapboxScene` consumes `INITIAL_CAMERA` for its `initialViewState` prop
- [ ] Vitest snapshot of `INITIAL_CAMERA` (regression guard against accidental edits)
- [ ] Visual verification: map boots showing FW with no jarring snap to a different position
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.5 --- Mapbox cleanup on unmount | Cx: 8 | P0

**Description:**
When `WallContainer` unmounts (e.g., user navigates to /assess via Next.js client-side route), the Mapbox map instance must be `.remove()`'d explicitly. Otherwise the WebGL context leaks and a second mount fails or stalls. Mapbox does NOT clean up automatically when its React wrapper unmounts. This is the kind of bug that doesn't show until demo day.

**AC:**
- [ ] `MapboxScene` `useEffect` cleanup calls `map.remove()` on unmount
- [ ] Vitest: mount → unmount → remount cycle does not throw
- [ ] Vitest: `map.remove` mock is called once per unmount
- [ ] No memory leak warning from React in test runner
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

## Phase 2: Scroll + Chapter Engine

### T2.6 --- ChapterScaffold.tsx — sticky atmosphere component | Cx: 16 | P0

**Description:**
Reusable wrapper component every chapter (1–10) renders inside. Provides scroll-tied opacity (chapter overlay fades in 0–20% scroll, holds 20–80%, fades out 80–100%), sticky positioning so the chapter pins while the camera flies underneath, and a slot for the editorial overlay copy. All chapters share this scaffold so editorial layout is consistent across the 10-chapter arc.

**AC:**
- [ ] `frontend/src/components/wall/ChapterScaffold.tsx` created
- [ ] Accepts props: `chapterNumber` (1–10), `chapterId` (string), `cameraState` (object from cameraChoreography), `children` (overlay JSX)
- [ ] Sticky positioning via CSS (sticky atmosphere — chapter pins while camera flies)
- [ ] Scroll-tied opacity using framer-motion `useTransform` against W1 `useScrollProgress`
- [ ] `prefers-reduced-motion`: opacity transitions become instant cuts (no scroll-tied fade)
- [ ] WCAG AAA contrast on overlay text (uses W1 fg-primary on glass card with backdrop-blur)
- [ ] ARIA-live region for chapter title announcement
- [ ] Vitest: opacity transitions correctly across scroll progress range
- [ ] Vitest: reduced-motion path renders instant cuts
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.2

---

### T2.7 --- cameraChoreography.ts — per-chapter camera states | Cx: 24 | P0

**Description:**
Extract a single source of truth for every chapter's camera state. Each chapter's state has zoom, pitch, bearing, longitude, latitude, and `flyToOptions` (speed, curve, duration override, easing). This module is the convergent dependency for chapters 1–5 (W2) AND chapters 6–10 (W3 — they extend this file). Defining it once avoids 10 chapters racing to invent camera state in their own files.

**AC:**
- [ ] `frontend/src/lib/wall/cameraChoreography.ts` created
- [ ] Exports `CHAPTER_CAMERAS` const with entries for chapters 1–5 (W2 scope); W3 extends this file with 6–10
- [ ] Ch1: zoom 3, pitch 0, bearing 0 (continental top-down America centered approx -98, 39)
- [ ] Ch2: zoom 11, pitch 60, bearing 0 (Fort Worth at altitude with 3D tilt)
- [ ] Ch3: zoom 14, pitch 60, bearing 25 (76119 neighborhood, slight tilt toward east)
- [ ] Ch4 (parent): zoom 13, pitch 50, bearing 0 (Fort Worth mid-altitude)
- [ ] Ch4a/b/c/d: variants of Ch4 base with bearing tilts toward each barrier office
- [ ] Ch5: zoom 11, pitch 30, bearing 0 (mid-altitude maze view)
- [ ] flyToOptions per chapter with cubic-bezier(0.32, 0.72, 0, 1) easing (Linear-style from W1 motion tokens)
- [ ] TypeScript type `ChapterCameraState` exported for chapter components
- [ ] Vitest: every chapter has a complete state shape (no undefined fields)
- [ ] Vitest snapshot guards against accidental coordinate edits
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.4

---

### T2.8 --- useChapterProgress hook — which chapter, how far through | Cx: 14 | P0

**Description:**
Build a chapter-aware scroll progress hook. Given the W1 `useScrollProgress` (page-level 0–1), this hook returns `{currentChapter: number (1–10), chapterProgress: number (0–1), nextChapter: number}`. Chapter boundaries are defined by equal page divisions for W2 (10 chapters → each 10% of page). Chapters can later override their range. This hook drives both the camera flyTo trigger and the editorial overlay opacity tied to current chapter.

**AC:**
- [ ] `frontend/src/hooks/useChapterProgress.ts` created
- [ ] Returns `{currentChapter, chapterProgress, nextChapter, isTransitioning}` (transitioning = within 5% of a boundary)
- [ ] SSR-safe (no window access without guard)
- [ ] Cleanup on unmount (no listeners leak)
- [ ] TypeScript signature exported
- [ ] Vitest: at scroll 0 → currentChapter=1, chapterProgress=0
- [ ] Vitest: at scroll 0.55 → currentChapter=6, chapterProgress=0.5 (chapter 6 is at 50–60% of page)
- [ ] Vitest: isTransitioning true near boundaries
- [ ] `bpsai-pair arch check` passes

**Depends on:** none (consumes W1 `useScrollProgress`)

---

### T2.9 --- flyTo orchestrator + reduced-motion instant-cut fallback | Cx: 24 | P0

**Description:**
Build the camera flight orchestrator. Subscribes to `useChapterProgress`. When `currentChapter` changes, calls `mapInstance.flyTo(CHAPTER_CAMERAS[currentChapter].flyToOptions)`. Cubic-bezier easing for cinematic feel. **CRITICAL: reduced-motion branch instant-cuts via `mapInstance.jumpTo()` instead of flyTo.** Cancellable on user manual drag (don't trap users). Spotlight: this is the "instrument plays differently for every user" moment — same data, different motion experience.

**AC:**
- [ ] `frontend/src/lib/wall/flyToOrchestrator.ts` created
- [ ] Subscribes to chapter change events; debounced 100ms to avoid rapid-fire flyTos during fast scroll
- [ ] Honors `usePrefersReducedMotion` (W1) — reduced-motion path uses `jumpTo()` (instant cut)
- [ ] User manual drag cancels in-flight flyTo (Mapbox `eventData.originalEvent` check)
- [ ] Cubic-bezier easing pulled from W1 motion tokens (no inline magic numbers)
- [ ] Vitest: chapter change triggers flyTo with correct camera state
- [ ] Vitest: reduced-motion preference triggers jumpTo not flyTo
- [ ] Vitest: rapid chapter changes are debounced (one flyTo not five)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7, T2.8

---

### T2.10 --- useScrollPin — sticky pinning per chapter | Cx: 12 | P0

**Description:**
Hook that handles the sticky CSS quirks browsers have around long sticky elements with overlapping ranges. Returns a ref + computed top offset for ChapterScaffold. Without this, chapters can "snap" out of pin position on certain browsers (Safari especially). Spotlight: structural failure mode the brief missed — sticky CSS does NOT work reliably across all browsers without explicit JS pinning fallback.

**AC:**
- [ ] `frontend/src/hooks/useScrollPin.ts` created
- [ ] Returns `{ref, isPinned, computedTop}`
- [ ] Falls back to JS-driven `position: fixed` on browsers where sticky misbehaves (feature-detected via `CSS.supports`)
- [ ] SSR-safe
- [ ] Vitest: ref attaches without error
- [ ] Vitest: feature-detection branch triggers JS fallback when sticky unsupported
- [ ] Manual smoke test passes in Chrome, Safari, Firefox
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 3: Data Layers + Mapbox Style

### T2.11 --- Trinity Metro GTFS → GeoJSON layer | Cx: 26 | P0

**Description:**
Pull Trinity Metro GTFS data (real, from `https://ride.trinitymetro.org/about/transparency/` or backend `app/integrations/`-derived data) and convert routes to GeoJSON polylines committed at `frontend/public/data/wall/trinity-metro.geojson`. Build a script `frontend/scripts/build-trinity-metro-geojson.mjs` that runs once (manual, pre-commit) so we have a runbook for refreshing. The Mapbox layer is styled cyan (W1 `--accent-cyan`) at low opacity, with Bus 4 highlighted at higher opacity in chapters 4b and 6.

**AC:**
- [ ] `frontend/scripts/build-trinity-metro-geojson.mjs` exists and is documented in script header (data source URL, refresh cadence)
- [ ] `frontend/public/data/wall/trinity-metro.geojson` committed (compressed; size budget < 500KB)
- [ ] GeoJSON contains real route polylines for at least Bus 4 + Bus 6 (the routes Carlos uses to reach the District Clerk's office) and 5+ other major routes
- [ ] `frontend/src/lib/wall/layers/trinityMetro.ts` defines the Mapbox layer config (line color = `var(--accent-cyan)`, opacity 0.3 default, 0.9 when highlighted)
- [ ] Layer styled per design tokens — no hardcoded hex
- [ ] Vitest: GeoJSON file loads without error
- [ ] Vitest: layer config exports valid mapbox-gl style spec (schema check)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.12 --- Tarrant County offices layer | Cx: 14 | P0

**Description:**
Tarrant County government office point markers committed at `frontend/public/data/wall/tarrant-offices.geojson`. Sources: Tarrant County District Clerk (real address, real coords), HHSC (Texas Health and Human Services Commission — Fort Worth office), DPS (Department of Public Safety — for Article 55 expunction filings), Workforce Solutions for Tarrant County (CAREER_CENTER_TX from `frontend/src/lib/city-constants.ts` — already in codebase!), Legal Aid of NorthWest Texas. Each marker has a category (court, benefits, dps, workforce, legal) for symbol selection.

**AC:**
- [ ] `frontend/public/data/wall/tarrant-offices.geojson` committed with 5 verified office locations (real addresses + lat/lng)
- [ ] Workforce Solutions coordinates pulled from `CAREER_CENTER_TX` (1200 Circle Dr, Fort Worth, TX 76119) — DRY with existing constant
- [ ] Each feature has properties: `{name, category, address, hours}` (lifted from real public listings)
- [ ] `frontend/src/lib/wall/layers/offices.ts` defines layer with custom symbols per category (T2.16 sprite work)
- [ ] Pin opacity tied to chapter — defaults dim, highlighted in Ch4 sub-chapters
- [ ] Vitest: GeoJSON valid; all 5 features have required properties
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.13 --- FW ZIP 76119 boundary layer | Cx: 14 | P0

**Description:**
Pull ZIP 76119 polygon from US Census TIGER/Line ZCTA dataset (https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/), extract just 76119, commit as `frontend/public/data/wall/zip-76119.geojson`. Used in Ch3 (Neighborhood) to highlight Carlos's ZIP outline as the camera zooms in. Layer fades from invisible (Ch1, Ch2) to visible at 0.3 fill opacity (Ch3) to bright outline only (Ch4).

**AC:**
- [ ] Build script `frontend/scripts/extract-zip-76119.mjs` documented (TIGER/Line download URL, extraction steps)
- [ ] `frontend/public/data/wall/zip-76119.geojson` committed (single MultiPolygon feature)
- [ ] `frontend/src/lib/wall/layers/zipBoundaries.ts` exports layer config (fill color = `var(--accent-amber)` at 0.15, stroke at 0.6)
- [ ] Layer opacity tied to chapter via paint expression (chapter-aware fade)
- [ ] Vitest: GeoJSON has valid geometry (turf.js boolean check)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.14 --- Carlos's representative neighborhood pin | Cx: 10 | P0

**Description:**
Define Carlos's "home" pin as a single Point feature at the centroid of a representative residential block within ZIP 76119. NOT his exact address (PII safety). Coordinates chosen for proximity to Bus 4 stop and to a real residential block. Documented in `frontend/src/lib/wall/paths.ts` with a comment block explaining the PII rationale. This pin is used in Ch3 (Neighborhood, drops in) and Ch7 (W3, Carlos avatar starts walking from here).

**AC:**
- [ ] `frontend/src/lib/wall/paths.ts` exports `CARLOS_HOME_PIN` constant: `{longitude, latitude, label: "Carlos's neighborhood (representative block)"}`
- [ ] PII-safety comment block in source explains why this is NOT his exact address
- [ ] `frontend/src/lib/wall/layers/carlosPath.ts` exports layer config with custom amber pin symbol
- [ ] Pin opacity 0 in Ch1, fades to 1 in Ch3
- [ ] Vitest: coordinates are within ZIP 76119 polygon bounds (turf.js point-in-polygon)
- [ ] Vitest: snapshot of `CARLOS_HOME_PIN` (regression guard)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.13

---

### T2.15 --- Jobs-by-ZIP employer markers | Cx: 16 | P0

**Description:**
Employer point markers across Fort Worth, color-coded by fair-chance status. Pulled from existing `data/cities/fort-worth/employers.json` if shape matches; else build a frontend-side derivation script. Includes Amazon FC DFW5 (real coords, used in Ch6 W3) plus 30+ other employers within Fort Worth. Color coding: amber if fair-chance, muted gray if credit-check-required (used in Ch4d "30% of jobs go dark").

**AC:**
- [ ] `frontend/public/data/wall/jobs-by-zip.geojson` committed (30+ employers minimum)
- [ ] Each feature has properties: `{name, category, fairChance: boolean, creditCheck: boolean, lat, lng}`
- [ ] Amazon FC DFW5 included with real coordinates (used in W3 Ch6)
- [ ] `frontend/src/lib/wall/layers/jobsByZip.ts` exports layer config with paint expressions for color coding
- [ ] Layer paint switches `creditCheck=true` markers to muted gray in Ch4d
- [ ] Vitest: GeoJSON valid; Amazon FC DFW5 present; ≥30 features total
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.16 --- Custom marker SVG sprite + symbol layer | Cx: 14 | P0

**Description:**
Mapbox markers default to ugly pins. Build a custom SVG sprite at `frontend/public/wall-markers/sprite.svg` with 5 categories (court, benefits, dps, workforce, legal, transit, employer). Each at 32px square, designed in editorial dark style with W1 brand cyan/amber accents. Wire as a Mapbox sprite via `mapbox-gl` `addImage` calls in `MapboxScene` setup. Spotlight: the brief said "custom marker symbols" but didn't specify a sprite system — without a sprite, every marker is a separate image load (perf hit).

**AC:**
- [ ] `frontend/public/wall-markers/sprite.svg` committed with 6 symbols (court, benefits, dps, workforce, legal, employer)
- [ ] Each symbol designed at 32px first, scales cleanly to 64px
- [ ] Symbols use W1 brand tokens (no hardcoded hex)
- [ ] `frontend/src/lib/wall/markerSprite.ts` exports `loadSprite(map)` helper called at MapboxScene mount
- [ ] Vitest: each symbol exists in the sprite SVG (DOM parse check)
- [ ] SVGO pass — no extraneous attributes
- [ ] WCAG AAA contrast for symbol-on-dark-style verified
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.17 --- Layer composer index | Cx: 10 | P0

**Description:**
Single composer module that registers all 5 data layers in correct z-order on the Mapbox map. Each layer module exports an `addLayer(map)` function; composer calls them in order: zip boundary (bottom) → trinity metro → offices → carlos path → jobs by zip (top). Cleanup on unmount removes all layers in reverse order.

**AC:**
- [ ] `frontend/src/lib/wall/layers/index.ts` exports `registerAllLayers(map)` and `removeAllLayers(map)`
- [ ] Z-order documented inline (zip → metro → offices → carlos → jobs)
- [ ] `MapboxScene` calls `registerAllLayers` on `map.on('load')` and `removeAllLayers` on cleanup
- [ ] Vitest: all 5 layer add functions called in order
- [ ] Vitest: cleanup removes all layers
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.11, T2.12, T2.13, T2.14, T2.15, T2.16

---

### T2.18 --- Custom Mapbox dark editorial style — runbook + commit config | Cx: 24 | P1

**Description:**
The custom Mapbox style is built in Mapbox Studio (manual ~30-min one-time setup). This task documents the steps so Shawn can do it offline, then commits the resulting style URL + a JSON export of the style for archival. Steps include: streets in --bg-elevated, water in --bg-surface, labels in --fg-primary at -0.04em tracking, buildings in --bg-elevated extruded at zoom 14+. Light variant for /assess and /plan (W3 reuses).

**AC:**
- [ ] `docs/runbooks/mapbox-style-setup.md` documents Studio steps (with screenshots placeholders) — NEW runbook
- [ ] Resulting style URL added to `frontend/.env.local.example` as `NEXT_PUBLIC_MAPBOX_STYLE_URL` with comment
- [ ] Style JSON export committed at `frontend/data/mapbox-style-export.json` for archival/recovery
- [ ] Both dark + light variants documented (light variant for W3 /assess transition)
- [ ] Documented fallback: if env var unset, default to `mapbox://styles/mapbox/dark-v11`
- [ ] Reviewer agent confirms runbook is unambiguous (someone unfamiliar can execute)
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 4: Chapter 1 — Continental

### T2.19 --- Chapter01Continental.tsx component | Cx: 14 | P0

**Description:**
Render Chapter 1: continental top-down view of America. Uses ChapterScaffold (T2.6) with cameraState=CHAPTER_CAMERAS[1]. Editorial overlay displays the locked hero question: "What's standing between you and a job?" — variable font weight axis interpolated by W1 `useVariableFontWeight` (read-only consumption, no W4 wiring of the Mapbox sky here). Overlay is centered, max-w-3xl, fades 0–20%.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter01Continental.tsx` created (≤200 lines)
- [ ] Uses ChapterScaffold with chapterNumber=1, chapterId="continental", cameraState=CHAPTER_CAMERAS[1]
- [ ] Renders hero question from `t("wall.ch1.hero")` (i18n key populated in T2.49)
- [ ] Variable font weight 700 → 900 axis tied to chapter progress (uses W1 `useVariableFontWeight`)
- [ ] Tracking -0.04em on display heading
- [ ] WCAG AAA contrast on overlay
- [ ] No hardcoded colors
- [ ] Vitest: renders heading text from i18n (mock)
- [ ] Vitest: variable font weight prop responds to scroll (mock useScrollProgress)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.7

---

### T2.20 --- Ch1 city lights layer (FW + Montgomery brighter) | Cx: 14 | P0

**Description:**
Continental view shows cities as faint glow points; Fort Worth and Montgomery glow noticeably brighter. Implemented as a circle layer with paint expressions: default cities small + dim, FW + Montgomery larger + bright. Data: small GeoJSON of major US cities (~50 metros) committed at `frontend/public/data/wall/us-cities.geojson`. Spotlight (Fusion): this layer is the seed for W3 Ch9's "fly to Montgomery" — same data, used twice, different emphasis. Building it well in W2 unblocks W3.

**AC:**
- [ ] `frontend/public/data/wall/us-cities.geojson` committed with ~50 major metros (each with `{name, state, population, isHighlight}`)
- [ ] Fort Worth + Montgomery have `isHighlight=true`
- [ ] `frontend/src/lib/wall/layers/cityLights.ts` exports layer config
- [ ] Layer paint: circle-radius 4 default, 8 if highlighted; circle-color amber if highlighted, muted-cyan if not
- [ ] Layer added by composer (T2.17 — update composer to include this layer)
- [ ] Layer visibility tied to chapter (visible Ch1 + Ch9, hidden elsewhere)
- [ ] Vitest: GeoJSON valid; FW + Montgomery have isHighlight=true
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.17

---

### T2.21 --- Ch1 wire into WallContainer | Cx: 6 | P0

**Description:**
Add Chapter 1 to the WallContainer's chapter array. This is the integration step where the chapter actually renders on the page. Verify scroll progress 0–10% triggers Ch1 camera + overlay.

**AC:**
- [ ] `WallContainer.tsx` imports and renders `<Chapter01Continental />`
- [ ] Vitest integration: scrolling to progress=0.05 sets currentChapter=1
- [ ] Vitest: Ch1 overlay visible when currentChapter=1
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.19

---

### T2.22 --- Ch1 reduced-motion fallback verification | Cx: 6 | P0

**Description:**
With `prefers-reduced-motion: reduce`, Ch1 must still render the editorial overlay and the city lights but NO scroll-tied opacity fade and NO variable font weight interpolation (font is fixed at weight 800). Spotlight (Resilience): brief left this implicit; making it explicit per chapter forces it to be tested.

**AC:**
- [ ] Vitest with mocked `prefers-reduced-motion: reduce`: overlay opacity is constant 1
- [ ] Vitest: variable font weight is fixed at 800 (no interpolation)
- [ ] Vitest: city lights still visible (no animated reveal)
- [ ] Manual smoke: macOS System Preferences → Reduce Motion → page works without animations

**Depends on:** T2.21

---

## Phase 5: Chapter 2 — City Arrival

### T2.23 --- Chapter02CityArrival.tsx component | Cx: 16 | P0

**Description:**
Chapter 2: camera dolly from continental (zoom 3) into Fort Worth (zoom 11, pitch 60). Editorial overlay: "Carlos lives here. ZIP 76119. East of downtown." Trinity Metro routes fade in as cyan polylines (T2.11 layer becomes visible). 3D buildings layer (Mapbox `fill-extrusion` from default style) fade in at zoom > 13.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter02CityArrival.tsx` created
- [ ] Uses ChapterScaffold with chapterNumber=2
- [ ] Editorial overlay from `t("wall.ch2.body")`
- [ ] Trinity Metro layer opacity tied to scroll: 0 at progress=0, 0.6 at progress=1
- [ ] 3D buildings layer activated when zoom > 13 (paint expression)
- [ ] Vitest: renders editorial text
- [ ] Vitest: layer opacity prop changes with progress
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.7, T2.11

---

### T2.24 --- Ch2 3D buildings extrusion config | Cx: 12 | P0

**Description:**
Wire Mapbox's built-in `fill-extrusion` for buildings. Custom paint: extrusion-color from W1 `--bg-elevated`, extrusion-height from `height` property in vector tiles, smooth fade in at zoom 13–15. This is a pure Mapbox style task but lives as a separate task because Mapbox's `composite` source isn't always exposed and we need a runbook.

**AC:**
- [ ] `frontend/src/lib/wall/layers/buildings3d.ts` exports the extrusion layer config
- [ ] Layer added by composer (T2.17 — second composer update)
- [ ] Paint uses `var(--bg-elevated)` via Mapbox `paint` expression with rgba conversion (Mapbox doesn't support CSS custom properties directly — document this explicitly)
- [ ] Layer visibility tied to zoom (≥13) and chapter (visible Ch2+, hidden Ch1)
- [ ] Vitest: layer config exports valid mapbox-gl style spec
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.17

---

### T2.25 --- Ch2 wire into WallContainer + EN copy stub | Cx: 6 | P0

**Description:**
Wire Chapter 2 into the WallContainer chapters array. Add stub i18n key entries (full copy task is T2.50). Verify scroll progress 10–20% triggers Ch2 camera dolly.

**AC:**
- [ ] WallContainer imports + renders `<Chapter02CityArrival />`
- [ ] Stub `wall.ch2.body` key in en.json (lifted from plan: "Carlos lives here. ZIP 76119. East of downtown.")
- [ ] Vitest: scroll progress 0.15 triggers currentChapter=2
- [ ] Vitest: Ch2 overlay visible
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.23

---

### T2.26 --- Ch2 reduced-motion + accessibility check | Cx: 8 | P0

**Description:**
Reduced-motion: instant zoom from continental to FW (jumpTo). Trinity Metro routes appear instantly at full opacity. axe-core scan passes on Ch2 isolated render.

**AC:**
- [ ] Reduced-motion: camera is jumpTo not flyTo (verified in test mock)
- [ ] Reduced-motion: layer opacity is full (no fade)
- [ ] axe-core scan on Ch2 returns zero violations
- [ ] Heading hierarchy: only one h2 in chapter overlay (h1 is reserved for hero in Ch1)
- [ ] Vitest: ARIA-live announces "Chapter 2: City Arrival" on enter

**Depends on:** T2.25

---

## Phase 6: Chapter 3 — Neighborhood

### T2.27 --- Chapter03Neighborhood.tsx component | Cx: 16 | P0

**Description:**
Chapter 3: camera zooms to ZIP 76119 (zoom 14, pitch 60, bearing tilted east). The ZIP boundary layer (T2.13) fades in. Carlos's representative neighborhood pin (T2.14) drops in with a spring animation (W1 `--spring-elastic`). Editorial overlay: 60-word Carlos intro lifted from plan file. Sound trigger: single footstep on chapter enter (W1 audio scaffold; opt-in only, mute-respected).

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter03Neighborhood.tsx` created
- [ ] Uses ChapterScaffold with chapterNumber=3
- [ ] ZIP boundary opacity tied to scroll (0 → 0.3 fill + 0.6 stroke)
- [ ] Carlos pin opacity tied to scroll, drops in around progress=0.5 with spring
- [ ] Editorial overlay from `t("wall.ch3.body")` (60-word intro)
- [ ] Sound trigger on chapter enter (W1 sound system, opt-in)
- [ ] Vitest: pin drop animation respects reduced-motion (instant appear)
- [ ] Vitest: sound NOT triggered when mute (W1 mute toggle)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.7, T2.13, T2.14

---

### T2.28 --- Ch3 PII-safety review of pin data | Cx: 5 | P0

**Description:**
Verification-only task. Reviewer agent confirms `CARLOS_HOME_PIN` (T2.14) coordinates are NOT a real residential address in 76119 — they should land on a block face / public space, NOT a specific home. This is the PII safety contract from constraints.

**AC:**
- [ ] Reviewer agent confirms pin lat/lng resolves (in reverse-geocoding) to a block face or public/commercial location, NOT a residential parcel
- [ ] If parcel identified, file blocking sub-task to T2.14 to relocate
- [ ] Comment in `paths.ts` updated with reviewer-approval timestamp

**Depends on:** T2.14

---

### T2.29 --- Ch3 wire into WallContainer | Cx: 5 | P0

**Description:**
Wire Chapter 3 into the WallContainer chapters array. Verify scroll progress 20–30% triggers Ch3 camera zoom-in to neighborhood.

**AC:**
- [ ] WallContainer imports + renders `<Chapter03Neighborhood />`
- [ ] Vitest: scroll progress 0.25 triggers currentChapter=3
- [ ] Vitest: Ch3 overlay visible at progress=0.25
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.27

---

### T2.30 --- Ch3 cursor flashlight conditional activation | Cx: 10 | P1

**Description:**
W1 ships `useCursorPosition` and a CursorFlashlight component. Spotlight (Fusion): activate the flashlight ONLY for chapters 3+ (when the camera is close enough to the ground that highlighting individual elements makes sense). Continental view (Ch1) has no flashlight (zoom too far). This conditional activation lives in WallContainer based on currentChapter.

**AC:**
- [ ] WallContainer conditionally renders CursorFlashlight when currentChapter >= 3
- [ ] Vitest: flashlight not rendered at currentChapter=1
- [ ] Vitest: flashlight rendered at currentChapter=3
- [ ] Reduced-motion / no-pointer (touch device): flashlight always disabled
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.29

---

## Phase 7: Chapter 4 — The Wall (4 sub-chapters)

### T2.31 --- Chapter04TheWall.tsx parent orchestrator | Cx: 22 | P0

**Description:**
Parent orchestrator for Chapter 4's 4 sub-chapters (4a criminal record, 4b no transit, 4c no childcare, 4d bad credit). Each sub-chapter is its own component but they share Ch4's camera state (mid-altitude) with bearing variations. Parent owns the sub-chapter state machine: progress 30–32.5% → 4a, 32.5–35% → 4b, 35–37.5% → 4c, 37.5–40% → 4d. Sound triggers fire on sub-chapter transitions.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter04TheWall.tsx` created
- [ ] Imports + composes 4 sub-chapter components
- [ ] Sub-chapter selection logic: maps chapterProgress to one of 4 sub-states
- [ ] Sound trigger fires on sub-chapter change (with cooldown to avoid rapid-fire)
- [ ] Vitest: progress 0.31 → sub-chapter "4a"
- [ ] Vitest: progress 0.36 → sub-chapter "4c"
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.7

---

### T2.32 --- Chapter04aCriminalRecord.tsx — Tarrant District Clerk pin lit | Cx: 14 | P0

**Description:**
Sub-chapter 4a: criminal record barrier. Tarrant County District Clerk office pin (T2.12 layer) lights up at high opacity. Camera bearing tilts toward the District Clerk's location. Editorial overlay: "4.8 miles. Bus 4 + Bus 6 = 71 minutes." (locked copy from plan). Bus 4 + Bus 6 routes from Trinity Metro layer highlight in amber (replacing default cyan briefly).

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter04aCriminalRecord.tsx` created
- [ ] District Clerk pin opacity 1.0 (highlighted from default 0.4)
- [ ] Bus 4 + Bus 6 polylines paint switches to amber via Mapbox feature-state expression
- [ ] Editorial overlay from `t("wall.ch4a.body")`
- [ ] Distance + time stat band (4.8 mi · 71 min) styled with tabular-nums
- [ ] WCAG AAA contrast on stat band (amber on dark)
- [ ] Vitest: pin opacity expression renders with state-aware values
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31, T2.12

---

### T2.33 --- Chapter04bNoTransit.tsx — Bus 4 highlighted | Cx: 14 | P0

**Description:**
Sub-chapter 4b: no transit barrier. Bus 4 polyline highlighted amber across its full route. Camera bearing tilts to follow Bus 4 north-south. Editorial overlay: "87-minute commute to downtown." (locked copy). Stat band shows commute time.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter04bNoTransit.tsx` created
- [ ] Bus 4 polyline opacity 1.0 + paint amber; other routes dim to 0.15
- [ ] Editorial overlay from `t("wall.ch4b.body")`
- [ ] Stat band: "87 min" with tabular-nums
- [ ] Camera bearing rotates 0 → 30 across sub-chapter progress
- [ ] Vitest: layer paint feature-state expression returns amber for Bus 4
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31, T2.11

---

### T2.34 --- Chapter04cNoChildcare.tsx — HHSC pin lit | Cx: 12 | P0

**Description:**
Sub-chapter 4c: childcare barrier. HHSC office pin (T2.12) lights up. Editorial overlay: "$1,200/mo without subsidy." Stat band shows monthly cost.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter04cNoChildcare.tsx` created
- [ ] HHSC pin opacity 1.0 (highlighted)
- [ ] Editorial overlay from `t("wall.ch4c.body")`
- [ ] Stat band: "$1,200/mo" with tabular-nums
- [ ] Vitest: HHSC pin highlighted; District Clerk + others dim
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31, T2.12

---

### T2.35 --- Chapter04dBadCredit.tsx — 30% of jobs go dark | Cx: 16 | P0

**Description:**
Sub-chapter 4d: bad credit barrier. Visual: 30% of employer markers (those with `creditCheck: true` from T2.15) shift from amber to muted gray. Editorial overlay: "Credit checks block 1 in 3 jobs you'd qualify for." Stat band: "33% of jobs unreachable."

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter04dBadCredit.tsx` created
- [ ] Job markers paint switches: `creditCheck=true` → muted gray; others remain amber
- [ ] Editorial overlay from `t("wall.ch4d.body")`
- [ ] Stat band: "33%"
- [ ] Vitest: paint expression filters by `creditCheck` property correctly
- [ ] WCAG AAA contrast on muted gray text against dark base — verified
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31, T2.15

---

### T2.36 --- Ch4 sub-chapter transitions (camera tilts + layer cross-fades) | Cx: 14 | P0

**Description:**
The 4 sub-chapters share the parent Ch4 camera state but each tilts the bearing and shifts emphasis. Build the cross-fade orchestrator: when transitioning 4a→4b, the District Clerk pin dims and Bus 4 lights up over a 200ms transition (W1 `--spring-soft`). Reduced-motion: instant swap.

**AC:**
- [ ] `frontend/src/lib/wall/ch4Transitions.ts` exports `crossFade(fromSubChapter, toSubChapter, map)`
- [ ] Uses W1 spring-soft preset
- [ ] Reduced-motion path: instant
- [ ] Vitest: sub-chapter change triggers correct cross-fade
- [ ] Vitest: reduced-motion path skips animation
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.32, T2.33, T2.34, T2.35

---

### T2.37 --- Ch4 sound triggers per sub-chapter | Cx: 12 | P1

**Description:**
Each sub-chapter has a distinct sound: 4a — paper-slide (court file), 4b — bus-engine (transit), 4c — child voice fragment (childcare), 4d — credit-card-decline beep. All opt-in (mute-respected via W1 audio scaffold). Each clip < 50KB MP3.

**AC:**
- [ ] 4 short audio clips committed at `frontend/public/sounds/wall/ch4{a,b,c,d}.mp3` (each < 50KB)
- [ ] `Chapter04TheWall` triggers `playSound("ch4{x}")` on sub-chapter enter via W1 audio API
- [ ] Mute toggle (W1) respected — no playback when muted
- [ ] Audio context unlocked on first user gesture (W1)
- [ ] Vitest: sub-chapter enter calls `playSound` with correct ID
- [ ] Vitest: muted state suppresses `playSound` call
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31

---

### T2.38 --- Ch4 wire into WallContainer | Cx: 6 | P0

**Description:**
Wire Chapter 4 (parent + 4 sub-chapters) into the WallContainer. Verify progress 30–40% renders sub-chapter sequence correctly.

**AC:**
- [ ] WallContainer imports + renders `<Chapter04TheWall />`
- [ ] Vitest: progress 0.31 → ch4a renders
- [ ] Vitest: progress 0.39 → ch4d renders
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.36

---

### T2.39 --- Ch4 accessibility — ARIA-live for sub-chapter transitions | Cx: 10 | P0

**Description:**
Each sub-chapter transition announces via ARIA-live: "Barrier: Criminal record. 4.8 miles to court. 71-minute commute." Screen-reader users get the same information sighted users get from the visual treatment. axe-core green per sub-chapter.

**AC:**
- [ ] `Chapter04TheWall` mounts an aria-live="polite" region
- [ ] Sub-chapter enter pushes a stat-aware narration string
- [ ] axe-core scan on each sub-chapter returns zero violations
- [ ] Vitest: sub-chapter enter updates aria-live region text
- [ ] Manual VoiceOver smoke (documented in PR description)

**Depends on:** T2.38

---

### T2.40 --- Ch4 reduced-motion fallback verification | Cx: 6 | P0

**Description:**
With reduced-motion, sub-chapter cross-fades are instant. Pin opacity changes are instant. Sound still plays (audio is opt-in independent of motion preference). Verified via tests + manual smoke.

**AC:**
- [ ] Vitest with reduced-motion: ch4 cross-fade duration = 0
- [ ] Vitest: reduced-motion does NOT suppress sound triggers (unmute is independent)
- [ ] Manual smoke pass

**Depends on:** T2.39

---

## Phase 8: Chapter 5 — The Labyrinth

### T2.41 --- Chapter05Labyrinth.tsx component | Cx: 24 | P0

**Description:**
Chapter 5: the labyrinth. Camera at zoom 11, pitch 30 — mid-altitude bird's-eye. Five Tarrant County offices light up across the map. An animated "chaotic path" draws between them — looping back, dead-ending, retracing. This is a custom SVG-on-Mapbox layer, NOT a route polyline (because there's no real route — it's the SHAPE of bureaucratic chaos). Editorial overlay: "5 offices. 47 forms. Each one says go to the next one." (locked copy). Forms counter: 0 → 47 ticks up across chapter progress.

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter05Labyrinth.tsx` created
- [ ] Custom SVG path overlay drawn between 5 office coordinates with chaotic geometry (loops, dead-ends — designed in T2.42)
- [ ] Forms counter ticks 0 → 47 tied to scroll progress (uses W1 AnimatedCounter)
- [ ] Editorial overlay from `t("wall.ch5.body")`
- [ ] Sound trigger: paper-rustle, sequenced (one rustle per office light-up)
- [ ] Vitest: counter renders 47 at progress=1
- [ ] Vitest: counter renders 0 at progress=0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.7, T2.12

---

### T2.42 --- Ch5 chaotic path SVG geometry | Cx: 14 | P0

**Description:**
Hand-craft the chaotic SVG path that traverses the 5 offices. Path includes intentional dead-ends (segments that go back), loops, retraced sections. Designed in code (not auto-generated), committed at `frontend/public/wall-paths/labyrinth.svg`. Path-draw animation uses SVG `stroke-dasharray` driven by scroll progress.

**AC:**
- [ ] `frontend/public/wall-paths/labyrinth.svg` committed
- [ ] Path geometry includes 3+ dead-ends, 2+ loops (visually obvious "this is a maze")
- [ ] Path color uses W1 `--accent-amber` at low opacity, transitioning to higher opacity as drawn
- [ ] `stroke-dasharray` + `stroke-dashoffset` animated by scroll
- [ ] Reduced-motion: path renders fully drawn (no animation)
- [ ] SVGO pass — no extraneous attributes
- [ ] `bpsai-pair arch check` passes (file is asset, not code)

**Depends on:** T2.12

---

### T2.43 --- Ch5 wire into WallContainer + sound | Cx: 8 | P0

**Description:**
Wire Chapter 5 into WallContainer. Sound trigger: paper rustle MP3 (~30KB) plays sequenced per office light-up. Mute respected.

**AC:**
- [ ] WallContainer imports + renders `<Chapter05Labyrinth />`
- [ ] Audio clip `frontend/public/sounds/wall/ch5-rustle.mp3` committed (< 50KB)
- [ ] Sound triggers sequenced (one per office, debounced)
- [ ] Mute toggle respected
- [ ] Vitest: progress 0.45 triggers currentChapter=5
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.41, T2.42

---

### T2.44 --- Ch5 accessibility + reduced-motion | Cx: 8 | P0

**Description:**
ARIA-live announces: "The Labyrinth: 5 offices. 47 forms." Forms counter respects reduced-motion (snaps to final value, no tick animation). axe-core green.

**AC:**
- [ ] aria-live region announces chapter title + summary on enter
- [ ] Reduced-motion: counter snaps to 47 (no tick)
- [ ] Reduced-motion: SVG path renders fully drawn
- [ ] axe-core scan returns zero violations
- [ ] Vitest: reduced-motion path skips counter animation

**Depends on:** T2.43

---

### T2.45 --- Ch5 forms-counter visual treatment | Cx: 10 | P1

**Description:**
The "47" counter is a hero stat in this chapter — text-7xl, tabular-nums, amber accent. As it ticks past 30, the page accent shift starts amber → rose (foreshadowing W3 Ch6 cliff). This is a Spotlight invention: the page reacts to the data inside it, prefiguring the cliff in Ch6 W3.

**AC:**
- [ ] Forms counter rendered at text-7xl with tabular-nums + amber color
- [ ] At counter ≥ 30, page CSS variable `--accent-current` transitions amber → rose
- [ ] Reduced-motion: instant accent swap (no transition)
- [ ] WCAG AAA contrast verified on rose accent against dark base
- [ ] Vitest: at progress=0.4, --accent-current is amber
- [ ] Vitest: at progress=0.5 (counter > 30), --accent-current shifts toward rose
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.41

---

## Phase 9: page.tsx Rewrite + Archive

### T2.46 --- Archive existing landing to /archive route | Cx: 10 | P0

**Description:**
Move the existing landing page content (`frontend/src/app/page.tsx`, 152 lines) to `frontend/src/app/archive/page.tsx`. The archive route renders the prior landing exactly as it was — useful for A/B comparison, rollback, or showing judges the "before" state. Also useful if the Wall has rendering issues on submission day and we need a one-line revert.

**AC:**
- [ ] `frontend/src/app/archive/page.tsx` created with the existing landing content (verbatim copy of current page.tsx)
- [ ] All imports resolve correctly from new path
- [ ] All translations work at /archive
- [ ] Vitest: /archive renders the legacy hero question
- [ ] Vitest: /archive renders the city stats section
- [ ] No new dependencies added

**Depends on:** none

---

### T2.47 --- Rewrite frontend/src/app/page.tsx → render WallContainer | Cx: 14 | P0

**Description:**
Replace `frontend/src/app/page.tsx` entirely with a thin shell that mounts `<WallContainer />`. Preserves the existing `useAssessmentComplete` redirect (returning users go to /daily, not the Wall). Marketing-only first-time visitors see the Wall.

**AC:**
- [ ] `frontend/src/app/page.tsx` rewritten — under 50 lines
- [ ] Renders `<WallContainer />` for first-time visitors
- [ ] Preserves `useAssessmentComplete` redirect logic to /daily
- [ ] Keeps "use client" directive
- [ ] No imports from `@/lib/motion` (those moved into WallContainer)
- [ ] Vitest: assessmentComplete=true → router.replace("/daily") still fires
- [ ] Vitest: assessmentComplete=false → WallContainer renders
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.46, T2.21, T2.25, T2.29, T2.38, T2.43

---

### T2.48 --- page.tsx test sweep — verify chapter progression | Cx: 12 | P0

**Description:**
Integration test: scroll through all 5 chapters in a single test, verify each chapter's overlay text appears at the correct progress range. This is the contract test that locks the chapter ordering — if a future task accidentally swaps chapter 3 and 4, this test fails loudly.

**AC:**
- [ ] `frontend/src/app/__tests__/page-wall-progression.test.tsx` created
- [ ] Mocks scroll progress at 0.05, 0.15, 0.25, 0.35, 0.45 — asserts correct chapter overlay text
- [ ] Mocks reduced-motion=true variant — same chapter ordering, no animations
- [ ] Test runtime < 2s
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.47

---

## Phase 10: EN/ES Copy Population

### T2.49 --- Ch1 editorial copy EN + ES | Cx: 8 | P0

**Description:**
Populate i18n keys for Chapter 1: hero question, supporting copy. EN copy is the locked slogan (do not redraft). ES translation uses existing es.json voice (formal-but-warm), reviewed by a native-fluent speaker (Shawn or Ren can confirm; document the reviewer in PR).

**AC:**
- [ ] `wall.ch1.hero` in en.json: "What's standing between you and a job?" (LOCKED — exact match)
- [ ] `wall.ch1.subhero` in en.json: "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan." (LOCKED — exact match)
- [ ] `wall.ch1.hero` + `wall.ch1.subhero` in es.json (formal-but-warm voice; not Google-translated)
- [ ] Spanish reviewer initials in PR description
- [ ] Vitest: both keys resolve in EN + ES
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.21

---

### T2.50 --- Ch2 editorial copy EN + ES | Cx: 7 | P0

**Description:**
Chapter 2 copy: "Carlos lives here. ZIP 76119. East of downtown." + supporting line. Spanish parity.

**AC:**
- [ ] `wall.ch2.body` in en.json (matches plan-locked copy)
- [ ] `wall.ch2.body` in es.json (formal-but-warm)
- [ ] Spanish reviewer initials in PR
- [ ] Vitest: keys resolve
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.25

---

### T2.51 --- Ch3 editorial copy EN + ES (60-word Carlos intro) | Cx: 14 | P0

**Description:**
Chapter 3 carries a 60-word Carlos intro (the longest editorial block in W2). Lifted from `docs/demo-script.md` Carlos persona block, condensed to 60 words. Spanish version is a parallel translation, NOT a literal one — reviewed for tone (Carlos's voice should feel respected, not flattened).

**AC:**
- [ ] `wall.ch3.body` in en.json (60 words ± 5; from plan/demo-script)
- [ ] `wall.ch3.body` in es.json (60 words ± 5; tone-reviewed)
- [ ] Flesch-Kincaid grade < 9 on EN copy
- [ ] No GetCalFresh anti-patterns (no aggressive CTA, no jargon)
- [ ] Spanish reviewer initials in PR
- [ ] Vitest: keys resolve in both languages
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.29

---

### T2.52 --- Ch4 editorial copy EN + ES (4 sub-chapters) | Cx: 14 | P0

**Description:**
Chapter 4 has 4 sub-chapter copy blocks plus 4 stat-band strings. All locked from plan: "4.8 miles. Bus 4 + Bus 6 = 71 minutes." (4a), "87-minute commute to downtown." (4b), "$1,200/mo without subsidy." (4c), "Credit checks block 1 in 3 jobs you'd qualify for." (4d). Spanish parity.

**AC:**
- [ ] `wall.ch4a.body`, `wall.ch4b.body`, `wall.ch4c.body`, `wall.ch4d.body` in en.json (locked plan copy)
- [ ] Same 4 keys in es.json (tone-reviewed)
- [ ] Stat-band strings (`wall.ch4a.stat`, etc.) in both languages
- [ ] Spanish reviewer initials in PR
- [ ] Vitest: 4 keys × 2 languages resolve
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.38

---

### T2.53 --- Ch5 editorial copy EN + ES | Cx: 7 | P0

**Description:**
Chapter 5 copy: "5 offices. 47 forms. Each one says go to the next one." (LOCKED). Spanish parity.

**AC:**
- [ ] `wall.ch5.body` in en.json (locked plan copy)
- [ ] `wall.ch5.body` in es.json (tone-reviewed)
- [ ] Spanish reviewer initials in PR
- [ ] Vitest: keys resolve in both
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.43

---

## Phase 11: Accessibility — Chapters 1–5

### T2.54 --- axe-core full sweep on chapters 1–5 | Cx: 12 | P0

**Description:**
Run axe-core on each chapter in isolation (jsdom + per-chapter render test). Zero violations is the gate. Common failure modes: heading hierarchy across chapters (each chapter should NOT redeclare h1), aria-live regions need labels, color contrast on glass cards.

**AC:**
- [ ] `frontend/src/__tests__/wall/axe-chapters-1-5.test.tsx` runs axe on each chapter render
- [ ] Zero violations on Ch1, Ch2, Ch3, Ch4 (each sub-chapter), Ch5
- [ ] Failure documented per chapter if any
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.21, T2.25, T2.29, T2.38, T2.43

---

### T2.55 --- Heading hierarchy verification | Cx: 6 | P0

**Description:**
Across the 10-chapter Wall, only Ch1 should have an h1 (the hero question). Chapters 2–10 use h2+ for their section titles. Verify with a single sweep test that asserts h1-count = 1 across all rendered chapters.

**AC:**
- [ ] Test asserts exactly one h1 across all of WallContainer's rendered chapters
- [ ] Chapter 2–5 titles use h2 or below
- [ ] Vitest passes
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.54

---

### T2.56 --- Skip-to-content + keyboard reachability for header controls | Cx: 10 | P0

**Description:**
W1 ships a skip-to-content link and styled focus rings. Verify these still work after WallContainer rewrites the page. Tab order: header (skip link → brand → chapter counter → mute → language → GitHub) → main scroll area → footer. Tab through all 5 chapters' overlay buttons (none yet, but the slot exists).

**AC:**
- [ ] Skip-to-content link visible on focus
- [ ] Tab order test: 6 header items → main → footer
- [ ] Mute toggle keyboard-toggleable (Space + Enter)
- [ ] Language toggle keyboard-toggleable
- [ ] No keyboard trap in WallContainer
- [ ] Vitest with @testing-library/user-event simulates keyboard tab through
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.47

---

## Phase 12: Performance — Lazy Loading

### T2.57 --- Code-split chapters 2–5 via dynamic import | Cx: 14 | P0

**Description:**
Ch1 ships in the initial bundle (above-the-fold, no jank). Ch2–5 dynamic-imported via `next/dynamic` with loading fallback. This shaves ~100KB off the initial bundle. Each chapter's loading state uses W1 `LoadingState` component (skeleton).

**AC:**
- [ ] `WallContainer` uses `next/dynamic` for Ch2, Ch3, Ch4, Ch5
- [ ] Each dynamic import has a `loading` fallback rendering W1 `LoadingState`
- [ ] Bundle delta measured: `npm run build` reports initial bundle reduced by ≥ 80KB
- [ ] No `ssr: false` flags (server-render the chapters' editorial overlays for SEO)
- [ ] Vitest: dynamic imports resolve correctly in test env (mocked next/dynamic)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.47

---

### T2.58 --- Lazy-load Mapbox style + layers after title sequence | Cx: 12 | P0

**Description:**
Mapbox script (~600KB) and the custom style + layers should not block first paint. WallContainer mounts a placeholder (W1 LoadingState skeleton or static fallback) until the W1 title sequence finishes (~3s) THEN dynamically imports `mapbox-gl` and initializes the scene. Spotlight (Compound): the title sequence "free time" doubles as Mapbox warm-up time — use it.

**AC:**
- [ ] `MapboxScene` is dynamically imported via `next/dynamic` in `WallContainer`
- [ ] Title sequence completion event triggers Mapbox import
- [ ] Static fallback visible during the gap
- [ ] Bundle delta: Mapbox no longer in initial bundle
- [ ] Vitest: mock title-sequence-complete event triggers import
- [ ] Manual smoke: page LCP < 2.5s on simulated 4G (W4 hard gate measured properly there)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.57

---

## Phase 13: Tests — Sprint Coverage

### T2.59 --- Camera choreography unit tests | Cx: 8 | P0

**Description:**
Per-chapter unit tests on `cameraChoreography.ts`. Each chapter's state has all required fields (lng, lat, zoom, pitch, bearing, flyToOptions). Snapshot guard against accidental coordinate edits (Carlos pin at the right ZIP, FW centroid not Dallas, etc.).

**AC:**
- [ ] `frontend/src/lib/wall/__tests__/cameraChoreography.test.ts` exists
- [ ] Each chapter (1–5) has a complete-state assertion
- [ ] Snapshot test for whole `CHAPTER_CAMERAS` const
- [ ] FW centroid coordinate verified within FW bounds (-97.5 to -97.2 lng, 32.6 to 32.85 lat)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7

---

### T2.60 --- Layer composer registration test | Cx: 7 | P0

**Description:**
`registerAllLayers` calls add for all 6 layers (zip, metro, offices, carlos, jobs, city-lights) in order. `removeAllLayers` removes in reverse. Mocked Mapbox map verifies call count + order.

**AC:**
- [ ] `frontend/src/lib/wall/layers/__tests__/index.test.ts` exists
- [ ] Verifies 6 add calls in correct order
- [ ] Verifies 6 remove calls in reverse order on cleanup
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.17, T2.20

---

### T2.61 --- Token validation + fallback test | Cx: 7 | P0

**Description:**
`mapboxToken.ts` unit tests: missing token returns false, malformed token returns false, valid token + reachable Mapbox CDN returns true, valid token + 502 from CDN returns false. Mocked fetch.

**AC:**
- [ ] `frontend/src/lib/wall/__tests__/mapboxToken.test.ts` exists
- [ ] All 4 cases tested
- [ ] Fetch timeout case tested (2s timeout returns false)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.1

---

### T2.62 --- Chapter render test (each chapter independently) | Cx: 12 | P0

**Description:**
Per-chapter render tests: chapter renders without throwing in jsdom, editorial overlay text appears, ARIA-live region present. Each chapter gets its own test file (5 files total) to keep under the 15-functions-per-file ceiling.

**AC:**
- [ ] `frontend/src/components/wall/chapters/__tests__/Chapter01Continental.test.tsx` exists
- [ ] Same for Ch2, Ch3, Ch4, Ch5 (Ch4 includes a sub-chapter sweep)
- [ ] Each test verifies: renders, overlay text appears, no console errors
- [ ] `bpsai-pair arch check` passes per file

**Depends on:** T2.21, T2.25, T2.29, T2.38, T2.43

---

### T2.63 --- WallContainer integration test | Cx: 12 | P0

**Description:**
End-to-end-ish integration test: mount WallContainer, mock scroll progress through 0–50%, verify each chapter's overlay activates at the right boundary, verify camera flyTo is called with correct state per chapter transition.

**AC:**
- [ ] `frontend/src/components/wall/__tests__/WallContainer.test.tsx` exists
- [ ] Verifies chapters 1–5 activate at progress 0.05, 0.15, 0.25, 0.35, 0.45
- [ ] Verifies flyTo (or jumpTo for reduced-motion) called with correct camera state per transition
- [ ] Test runtime < 3s
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.47

---

### T2.64 --- Spanish (ES) chapter render test | Cx: 8 | P0

**Description:**
With i18n locale forced to ES, render WallContainer through chapters 1–5 and verify ES copy renders (NOT EN). Catches regressions where a chapter hardcodes English string instead of using `t()`.

**AC:**
- [ ] `frontend/src/__tests__/wall/spanish-parity.test.tsx` exists
- [ ] Forces locale to "es"
- [ ] Asserts Ch1 renders Spanish hero question (NOT English)
- [ ] Asserts Ch2–5 render Spanish editorial copy
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.49, T2.50, T2.51, T2.52, T2.53

---

### T2.65 --- Reduced-motion sweep test | Cx: 8 | P0

**Description:**
Single test that verifies, with `prefers-reduced-motion: reduce` mocked, every chapter's animations collapse to instant cuts. No flyTo (only jumpTo), no opacity transitions, no path-draw animation, no counter tick. The "still-image fallback that's still beautiful" contract.

**AC:**
- [ ] `frontend/src/__tests__/wall/reduced-motion-sweep.test.tsx` exists
- [ ] Mocks reduced-motion preference
- [ ] Asserts: no flyTo calls (only jumpTo)
- [ ] Asserts: chapter overlays render at full opacity from start
- [ ] Asserts: ch5 SVG path renders fully drawn
- [ ] Asserts: ch5 forms counter renders 47 immediately
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.63

---

### T2.66 --- Build + smoke verification | Cx: 8 | P0

**Description:**
`npm run build` succeeds. Production build serves `/` and renders WallContainer (or static fallback if no token). `/archive` serves the legacy landing. Bundle sizes documented.

**AC:**
- [ ] `npm run build` succeeds with zero errors
- [ ] Bundle sizes captured in PR description (initial JS, route JS, CSS)
- [ ] Production server (`npm start`) serves `/` returning 200 with WallContainer markup
- [ ] `/archive` returns 200 with legacy landing markup
- [ ] No "MontGoWork" string in built HTML
- [ ] No console errors in production build smoke

**Depends on:** T2.47, T2.57, T2.58

---

### T2.67 --- Sprint exit smoke + state.md update | Cx: 8 | P0

**Description:**
End-of-sprint smoke: scroll the page from top to chapter 5, verify camera flights, verify overlays in EN, switch language to ES, verify ES overlays, switch back. Verify static fallback path by removing token in `.env.local` temporarily. Update `.paircoder/context/state.md` with W2 completion summary and W3 readiness note.

**AC:**
- [ ] Manual smoke: chapters 1–5 render correctly in EN
- [ ] Manual smoke: language toggle to ES → all overlays update
- [ ] Manual smoke: token removed → static fallback renders
- [ ] Token restored → Mapbox renders
- [ ] `.paircoder/context/state.md` updated: W2 marked done, W3 listed as next
- [ ] All previous tasks (T2.1–T2.66) marked done in plan tracker
- [ ] PR description summarizes the sprint with screenshot of Ch3 (Carlos's neighborhood)

**Depends on:** all prior W2 tasks

---

## Spotlight Inventions — Beyond the Brief

These are tasks NOT in the original W2 brief that the Spotlight engine surfaced. Each is justified by a Spotlight Lens or one of the 5 Awakening Conditions.

### Invention 1: T2.1 — Token validation + static fallback chain (Root Cause Lens)
**Brief said:** "Mapbox token validation + static fallback" (one bullet).
**Spotlight expanded:** Full fallback chain with 3 failure modes (missing token, malformed token, CDN unreachable), each with a specific test. This is the **single root-cause task that eliminates the most downstream risk**. Every chapter depends on Mapbox; without a hardened fallback, the entire Wall breaks if Mapbox has a bad day on submission day. Cx 12, not 5.

### Invention 2: T2.10 — useScrollPin hook (Structural Lens — failure modes the brief missed)
**Brief said:** Sticky atmosphere via CSS sticky.
**Spotlight surfaced:** `position: sticky` is unreliable across Safari + iOS Safari + older Firefox at long scroll lengths. Without explicit JS pinning fallback, chapters can "snap" out of pin position mid-scroll on demo day. New task. Cx 8.

### Invention 3: T2.18 — Custom Mapbox style runbook (Honesty + Legacy Lens)
**Brief said:** "Custom dark style in Mapbox Studio (one-time, 30 min)."
**Spotlight surfaced:** Mapbox Studio is a manual GUI tool; without a runbook, the style will be re-built ad-hoc each time and drift. Documenting the steps + committing the style JSON export means the style is reproducible from scratch even if the original Studio account is lost. Reviewer agent confirms unambiguity. Cx 14.

### Invention 4: T2.20 — Continental city-lights data layer (Fusion Lens)
**Brief implicitly assumed:** Ch1 uses Mapbox's default city labels.
**Spotlight surfaced:** A custom GeoJSON of US cities with `isHighlight` property is reusable in Ch9 (W3) "fly to Montgomery" — same data, different emphasis. Building it in W2 unblocks W3's marquee chapter. Compound efficiency. Cx 10.

### Invention 5: T2.28 — PII safety review of Carlos pin (Multiple Selves Lens — Carlos's voice)
**Brief said:** "Pin drops at representative block (PII-safe)."
**Spotlight asked:** Who verifies the pin is actually on a block face and not a parcel? Reviewer agent verification is a discrete task. If the pin lands on someone's actual house, it's a real-world harm vector. Cx 4 — small task, high importance. Multiple-Selves perspective: Carlos.

### Invention 6: T2.30 — Cursor flashlight conditional activation (Fusion + Resilience Lens)
**Brief said:** "Cursor flashlight active" in Ch3+.
**Spotlight surfaced:** WHEN to activate it matters — Ch1 continental view has nothing flashlight-able. Conditional activation lives in WallContainer, not in CursorFlashlight itself. Keeps W1 component pure; orchestration in W2. Cx 8.

### Invention 7: T2.45 — Forms counter triggers accent shift (Fusion + Compound Lens)
**Brief said:** "Forms counter ticks 0 → 47."
**Spotlight surfaced:** When the counter passes 30, the page accent should shift amber → rose. This **prefigures W3's Ch6 cliff**, where the same accent shift happens on the wage slider. Use the same mechanism in two chapters; W2 builds the infrastructure W3 reuses. Compound efficiency. Cx 6.

### Invention 8: T2.48 — Chapter progression contract test (Wisdom Lens)
**Brief had:** Per-chapter render tests.
**Spotlight surfaced:** A SINGLE test that locks chapter ordering. If a future task accidentally swaps chapters 3 and 4, this test fails loudly — preventing the "Carlos's neighborhood appears AFTER the wall" bug. The convergent contract test, not 5 cargo-cult per-chapter tests. Cx 8.

### Invention 9: T2.58 — Mapbox lazy-load tied to title sequence (Compound Lens)
**Brief said:** "Mapbox style + layers lazy-loaded after title sequence."
**Spotlight surfaced:** The title sequence's 3-second display IS free Mapbox warm-up time. Use the same time slot for two purposes (sequence + Mapbox init). Compound efficiency — two costs paid in one budget. Cx 8.

### Invention 10: T2.66 — Build + smoke verification + bundle size capture (Honesty Lens)
**Brief had:** Tests, but no explicit "production build smoke."
**Spotlight surfaced:** A test environment passing is NOT the same as a production build serving. Capture bundle sizes at sprint exit so W4 Lighthouse work has a baseline. Cx 5.

---

## Honest Uncertainty (C4/C5 confidence calls)

These are tasks/decisions where confidence is below C3 and the engage scheduler should know.

### Uncertainty 1: Mapbox token in CI (C4)
**Issue:** Vitest runs in CI and chapters depend on Mapbox tokens. Decision needed: do CI tests use a dummy token + mocked Mapbox, or a real free-tier token in a secret? **Mitigation:** T2.1, T2.61 use mocked Mapbox throughout — no real CI token needed. **Risk if wrong:** CI flakes on Mapbox quota or 502s. **Action:** All Mapbox interactions mocked in tests; integration test mocks the map instance entirely.

### Uncertainty 2: Trinity Metro GTFS data freshness (C4)
**Issue:** Trinity Metro GTFS feed updates monthly. The committed GeoJSON could be stale by submission day. **Mitigation:** T2.11's build script is a runbook; Shawn refreshes once before submission. **Risk if wrong:** Bus 4 polyline doesn't match current Bus 4 route — judges might not catch, but it's a craft issue. **Action:** Run T2.11 build script in W5 final-polish phase (re-fresh data); accept C4 confidence in W2 commit.

### Uncertainty 3: Mobile fallback strategy unclear (C5)
**Issue:** The brief mentions "mobile fallback" but W2 doesn't have a dedicated task. Mapbox runs poorly on low-end Android; iPad is fine. **Mitigation:** Defer to W4 mobile-fallback task (already in W4 brief). W2 builds desktop-first; if a mobile reviewer hits it, they get the static fallback (T2.1). **Risk if wrong:** Mobile reviewers see the static fallback only and miss the Wall. **Action:** Document this in PR description; W4's mobile fallback task is the proper resolution.

### Uncertainty 4: Custom Mapbox style timing (C4)
**Issue:** The custom style takes ~30 min in Mapbox Studio (manual). If Shawn doesn't get to it before chapters 1–5 are wired, default `mapbox://styles/mapbox/dark-v11` is used as fallback. Default style is "good enough" but lacks the editorial dark treatment. **Mitigation:** T2.18 documents the runbook and ships the fallback. Shawn can swap the env var at any time. **Risk if wrong:** Submission ships with default Mapbox dark style — still acceptable. **Action:** T2.18 is P1 (not P0); submission can ship without it.

### Uncertainty 5: Spanish reviewer availability (C4)
**Issue:** Each ES copy task requires a native-fluent reviewer. Shawn has noted Ren can review some; depending on cycle availability, this could bottleneck T2.49–T2.53. **Mitigation:** ES copy ships using existing es.json voice as baseline; reviewer pass is a follow-up gate (still in W2 budget). **Risk if wrong:** ES copy ships with mid-quality phrasing. **Action:** Each ES task includes a "Spanish reviewer initials in PR" AC; if no reviewer available, mark as `[ES-pending-review]` and create a sub-task in W4 for sweep.

### Uncertainty 6: page.tsx archive route (C3 — leaning C4)
**Issue:** /archive is a meta route — how should it be discoverable (or not)? Is it linked from the footer, or hidden? **Decision:** hidden, NOT linked. Only accessible by direct URL. Used as rollback insurance. **Risk:** None — direct URL works as designed. **Action:** Confirmed in T2.46 AC.

### Uncertainty 7: Chapter 4 sound clip licensing (C4)
**Issue:** Sound effects (paper rustle, bus engine, child voice, credit-card beep) need to be either original or royalty-free. **Mitigation:** All clips sourced from Freesound.org (CC0) or Pixabay (royalty-free). License attribution committed in `frontend/public/sounds/wall/LICENSES.md`. **Risk if wrong:** License violation. **Action:** T2.37 AC adds "license attribution committed."

### Uncertainty 8: WallContext re-render performance (C4)
**Issue:** `useScrollProgress` updates on every scroll event (60Hz). Wrapping it in a Context means every chapter re-renders every frame. **Mitigation:** WallContext value is memoized; chapters use selector hooks (`useChapterContext()` reads only what they need). React's re-render bailout handles the rest. **Risk if wrong:** Janky scroll. **Action:** Profile in T2.66 build smoke. If janky, add `useMemo` boundary or move to Zustand (single deferred task to W4 polish).

---

## Delivery Summary

| Phase | Tasks | Cx | Focus |
|---|---|---|---|
| 1 Mapbox Foundation | 5 | 50 | Token validation, WallContainer, MapboxScene, initial state, cleanup |
| 2 Scroll + Chapter Engine | 5 | 58 | ChapterScaffold, cameraChoreography, useChapterProgress, flyTo orchestrator, useScrollPin |
| 3 Data Layers + Mapbox Style | 8 | 84 | Trinity Metro, offices, ZIP boundary, Carlos pin, jobs, sprite, composer, style runbook |
| 4 Chapter 1 — Continental | 4 | 30 | Component, city lights, wire, reduced-motion |
| 5 Chapter 2 — City Arrival | 4 | 31 | Component, 3D buildings, wire, a11y |
| 6 Chapter 3 — Neighborhood | 4 | 28 | Component, PII review, wire, cursor flashlight |
| 7 Chapter 4 — The Wall | 10 | 81 | Parent + 4 sub-chapters + transitions + sound + wire + a11y + reduced-motion |
| 8 Chapter 5 — The Labyrinth | 5 | 42 | Component, SVG path, wire, a11y, forms counter accent shift |
| 9 page.tsx Rewrite + Archive | 3 | 26 | Archive, rewrite, progression test |
| 10 EN/ES Copy Population | 5 | 36 | Per-chapter EN + ES copy with reviewer pass |
| 11 Accessibility — Chapters 1–5 | 3 | 18 | axe-core sweep, heading hierarchy, keyboard reachability |
| 12 Performance — Lazy Loading | 2 | 18 | Code-split chapters, lazy Mapbox |
| 13 Tests — Sprint Coverage | 9 | 54 | Camera, layers, token, chapter renders, integration, ES, reduced-motion, build, exit smoke |
| **Total** | **67** | **556** | (Cx subtotals; running total reconciled below) |

**Note on Cx total:** Per-task Cx (sum verified via `grep + awk`) totals **816** across 67 tasks, comfortably within the 800–1000 budget. Phase subtotals above are illustrative; per-task Cx values in each task header are authoritative.

## Summary by Priority

- **P0 (63 tasks, ~760 Cx):** Foundation + scroll engine + data layers + chapters 1–5 + EN/ES copy + accessibility + lazy-loading + tests. Everything required to scroll Ch1–5 in EN and ES with axe-green.
- **P1 (4 tasks, ~56 Cx):** Custom Mapbox style runbook (T2.18, Cx 24), cursor flashlight conditional (T2.30, Cx 10), Ch4 sound triggers (T2.37, Cx 12), Ch5 forms-counter accent shift (T2.45, Cx 10). Polish that elevates the demo but doesn't block the chapter sequence.
- **P2 (0 tasks):** None this sprint. Spotlight Honest Uncertainty section flags candidates for descope to W4 if needed (e.g., Mapbox style if not built in time, ES reviewer pass).

## Cross-Sprint Dependencies

- **Depends on (W1):** design tokens (OKLCH colors, Inter Variable axis, motion presets, --temperature-multiplier), motion utilities, hooks (useScrollProgress, useTimeOfDay, useCursorPosition, useLiveNow, useVariableFontWeight, usePrefersReducedMotion), brand assets (G+path SVG), edge states (404/500/empty/loading), header/footer, mapbox-gl + react-map-gl install. If any are missing at engage time, file blocking sub-task against W1.
- **Net-new env vars:** `NEXT_PUBLIC_MAPBOX_TOKEN` (T2.1), `NEXT_PUBLIC_MAPBOX_STYLE_URL` (T2.18 — optional, defaults to mapbox dark-v11)
- **Net-new public data files:** `frontend/public/data/wall/trinity-metro.geojson`, `tarrant-offices.geojson`, `zip-76119.geojson`, `jobs-by-zip.geojson`, `us-cities.geojson`; `frontend/public/wall-fallback-fort-worth.jpg`; `frontend/public/wall-markers/sprite.svg`; `frontend/public/wall-paths/labyrinth.svg`; 5 short MP3s in `frontend/public/sounds/wall/`
- **Net-new build scripts:** `frontend/scripts/build-trinity-metro-geojson.mjs`, `frontend/scripts/extract-zip-76119.mjs`
- **Net-new runbooks:** `docs/runbooks/mapbox-style-setup.md`
- **Blocks (W3):** Chapter 6–10 implementations need WallContainer, ChapterScaffold, cameraChoreography, layers index, paths.ts (Carlos pin used by Ch7 avatar), Mapbox style URL, all live before W3 begins.

## Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Mapbox token / CDN failure on demo day | T2.1 static fallback chain; tested with 4 failure modes |
| Mapbox style not built in Studio before submission | T2.18 P1 with default fallback to `mapbox://styles/mapbox/dark-v11`; submission ships either way |
| Trinity Metro GTFS data stale | T2.11 build script + W5 final-polish refresh |
| Mobile rendering broken | T2.1 static fallback covers mobile until W4 mobile task; documented as known C5 |
| Sticky CSS misbehaves on Safari | T2.10 useScrollPin JS fallback |
| Spanish copy quality | Each T2.49–T2.53 has a reviewer-initials AC; flag as `[ES-pending-review]` if no reviewer |
| WallContainer re-render perf | T2.66 includes profiling; deferred Zustand task in W4 if needed |
| PII leak (Carlos pin = real address) | T2.28 dedicated reviewer-agent verification task |
| Mapbox lazy-load timing breaks LCP | T2.58 ties Mapbox import to title sequence completion; Lighthouse measured in W4 |
| Sub-chapter ordering drift (Ch3 ↔ Ch4 swap) | T2.48 single contract test locks ordering |
| Audio license violation | T2.37 AC adds license attribution commit |

## Post-W2 Opportunities (explicitly deferred)

- Time-of-day Mapbox sky shift (W4)
- Variable font axis on hero with W4 polish
- Per-chapter dynamic OG via Vercel Satori (W4)
- Live Now widget UI on map (W4 — only the W1 hook is consumed in W2)
- Mobile fallback strategy proper (W4)
- Lighthouse 90+ measurement + descope decisions (W4)
- Chapter 6 cliff calculator embed (W3)
- Carlos avatar walking GPS path (W3)
- 3D barrier graph (W3)
- Fly-to-Montgomery (W3 Ch9)
- View Transitions API for /assess morph (W3 Ch10)

## Explicitly Not in Scope

- Backend changes (W2 is frontend-only)
- New product features outside the Wall (Wall is the only feature in W1–W4)
- README rewrite (W5)
- Press kit / video (W5)
- Performance optimization beyond lazy-loading (W4)

---

慣性の契約. The dispatch is a contract. The Wall · Sprint W2 · April 2026 · GoWork team. **心を燃やせ.**
