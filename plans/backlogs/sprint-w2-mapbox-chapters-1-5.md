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

## Phase 14: Enrichment Pass — Real-Data Verification

> Tasks T2.68–T2.122 added in the Apex Spotlight enrichment pass (2026-04-27). They sharpen real-world fidelity, Mapbox polish, interactive map elements, editorial details, FW landmark references, camera polish, labyrinth deep polish, time-of-day prefiguration, Bus 4 detail accuracy, cross-chapter integration, and visual-regression tests. Existing T2.1–T2.67 are unchanged; enrichment tasks weave into the existing waves via explicit `Depends on` edges.

### T2.68 --- Verify Tarrant County District Clerk address + hours + phone | Cx: 6 | P0

**Description:**
Phase 3 / Phase 7 (4a) commit a District Clerk pin and the editorial "4.8 miles. 71 minutes" stat band. The committed coordinates and stat band are only credible if the address is verified. Forensic-truth task: verify Tarrant County District Clerk's actual public address (200 E Weatherford St, Fort Worth, TX 76196), hours (Mon–Fri 8 AM – 5 PM), and main phone (817-884-1574) against the official Tarrant County Government website. Document source URL + access date. Update `tarrant-offices.geojson` properties.

**AC:**
- [ ] `tarrant-offices.geojson` District Clerk feature has verified address (200 E Weatherford St, FW 76196), hours, phone, sourceUrl, sourceDate
- [ ] Source URL committed in feature properties (e.g., `https://www.tarrantcountytx.gov/`)
- [ ] Coordinates verified within ±50m of building address (geocoded via Mapbox geocoding API or OSM Nominatim — document tool used)
- [ ] Vitest: District Clerk feature properties pass schema check
- [ ] Reviewer agent confirms data is from a primary government source (not a third-party aggregator)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.69 --- Verify HHSC Fort Worth office (pick best location) | Cx: 6 | P0

**Description:**
HHSC has multiple Fort Worth-area offices. Pick the one closest to ZIP 76119 + accessible by Bus 4 to keep editorial truth: that's the office Carlos would actually go to. Likely candidate: HHSC office at 1200 E Lancaster Ave or the office on E Berry St (verify both, choose). Verify address, hours, phone, services offered (Medicaid, SNAP, CHIP, childcare). Source: https://www.hhs.texas.gov/. Update `tarrant-offices.geojson`.

**AC:**
- [ ] HHSC feature in `tarrant-offices.geojson` has verified address (single office picked), hours, phone, services list, sourceUrl, sourceDate
- [ ] Selection rationale documented in commit message: "closest HHSC to 76119 reachable by Bus 4"
- [ ] Coordinates geocoded ±50m of building
- [ ] Vitest: HHSC feature passes schema
- [ ] Reviewer confirms primary source
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.70 --- Verify Legal Aid of NorthWest Texas FW office | Cx: 6 | P0

**Description:**
Legal Aid of NorthWest Texas operates multiple Fort Worth locations. Pick the primary intake office (likely 600 E Weatherford St or West Lancaster). Verify address, intake hours, intake phone (LANWT main: 817-336-3943), services. Source: https://www.lanwt.org/. Update `tarrant-offices.geojson`.

**AC:**
- [ ] Legal Aid feature in `tarrant-offices.geojson` has verified address, intake hours, phone, services, sourceUrl, sourceDate
- [ ] Coordinates geocoded ±50m
- [ ] Vitest: feature passes schema
- [ ] Reviewer confirms primary source
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.71 --- Verify Workforce Solutions on E. Belknap (Carlos's office) | Cx: 5 | P0

**Description:**
Demo script line: "Workforce Solutions office on E. Belknap." `CAREER_CENTER_TX` constant points to 1200 Circle Dr. Reconcile: are these two different offices, or is the demo-script address outdated? Verify against official Workforce Solutions for Tarrant County office locator (https://www.workforcesolutions.net/locations/). Pick canonical address; update `CAREER_CENTER_TX` if needed AND `tarrant-offices.geojson`.

**AC:**
- [ ] Demo script vs. constant reconciled (one canonical address committed)
- [ ] If `CAREER_CENTER_TX` updated, all dependent tests pass
- [ ] Workforce Solutions feature in `tarrant-offices.geojson` matches `CAREER_CENTER_TX` (DRY)
- [ ] Source URL + access date in feature properties
- [ ] Vitest: existing `city-constants.test.ts` still passes
- [ ] Reviewer confirms reconciliation
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.72 --- Verify Texas DPS Fort Worth office (for Article 55 expunction filings) | Cx: 5 | P0

**Description:**
Article 55 of the Texas Code of Criminal Procedure governs expunction; DPS receives orders. Pick the FW DPS office most likely to serve a 76119 resident (likely DPS Driver License Mega Center on Camp Bowie or McCart Ave — verify). Source: https://www.dps.texas.gov/. Add as the 5th office (court / benefits / dps / workforce / legal taxonomy is now complete).

**AC:**
- [ ] DPS feature in `tarrant-offices.geojson` has verified address, hours, phone, services, sourceUrl, sourceDate
- [ ] Coordinates geocoded ±50m
- [ ] Category="dps" matches T2.16 sprite category
- [ ] Vitest: 5 distinct categories present in offices GeoJSON (court, benefits, dps, workforce, legal)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.73 --- Trinity Metro GTFS data freshness gate | Cx: 8 | P0

**Description:**
The committed `trinity-metro.geojson` could be stale by submission day (Honest Uncertainty #2). Build a freshness gate: the build script writes `lastUpdated` (ISO 8601) and `sourceUrl` into a sibling JSON file `trinity-metro.metadata.json`. WallContainer reads the metadata at build-time and a vitest asserts `lastUpdated` is within 90 days of `process.env.BUILD_TIMESTAMP` or fails CI with a clear "GTFS data stale — re-run build script" message. Spotlight: forensic honesty made explicit.

**AC:**
- [ ] `frontend/public/data/wall/trinity-metro.metadata.json` committed with `{lastUpdated, sourceUrl, gtfsVersion, refreshScriptPath}`
- [ ] `frontend/scripts/build-trinity-metro-geojson.mjs` (T2.11) updated to write metadata
- [ ] `frontend/src/lib/wall/__tests__/gtfs-freshness.test.ts` asserts `lastUpdated` within 90 days of CI run
- [ ] Test failure message is human-readable: "Run `node scripts/build-trinity-metro-geojson.mjs` to refresh"
- [ ] Vitest: metadata schema valid
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.11

---

### T2.74 --- Article 55 statute text verification + commit | Cx: 5 | P1

**Description:**
The demo script and Ch4a editorial reference "Article 55 expunction." Commit a verbatim verified excerpt of the relevant Texas Code of Criminal Procedure Art. 55 statute text (or the official URL + section number) at `frontend/src/lib/wall/legalReferences.ts` so the editorial layer has a single source of truth. NOT legal advice — citation only. Used for future Ch4a tooltip + W3 Ch7 narrative authenticity.

**AC:**
- [ ] `frontend/src/lib/wall/legalReferences.ts` exports `ARTICLE_55_TX = {citation, sourceUrl, sourceDate, summary}` const
- [ ] Source URL points to Texas Legislature Online (https://statutes.capitol.texas.gov/) or equivalent primary source
- [ ] Summary is ≤ 200 chars, factual (no advice)
- [ ] Vitest: shape verified; sourceUrl is HTTPS and resolves at audit time (mocked check)
- [ ] Reviewer confirms primary source
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.75 --- Texas HHSC childcare program canonical name (CCS) verification | Cx: 4 | P1

**Description:**
Ch4c stat band says "$1,200/mo without subsidy." The "subsidy" is Texas Workforce Commission's Child Care Services (CCS) program — NOT HHSC. Reconcile the brief: Ch4c uses HHSC pin but the actual subsidy program is TWC/CCS. Decision: keep HHSC pin (childcare *eligibility* assistance routes through HHSC for Medicaid/SNAP household income verification), but ensure copy in T2.52 doesn't claim HHSC administers the subsidy directly. Add a docs comment in `legalReferences.ts`.

**AC:**
- [ ] `legalReferences.ts` exports `TX_CHILDCARE_PROGRAM = {agency: "Texas Workforce Commission", program: "Child Care Services (CCS)", sourceUrl}`
- [ ] T2.52 ES/EN copy reviewed: "subsidy" generic, no false claim that HHSC administers
- [ ] Reviewer confirms accuracy
- [ ] Vitest: const shape verified
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.76 --- ZIP 76119 boundary from US Census TIGER/Line — committed offline | Cx: 6 | P0

**Description:**
Augments T2.13. The TIGER/Line ZCTA download is a manual one-time step. Commit the TIGER/Line source ZIP (or filtered Shapefile) at `frontend/data/tiger-zcta-76119-source.zip` for offline reproducibility. The T2.13 extract script reads from this archived source, NOT from a live US Census URL at build-time. Forensic: locks data provenance. License: TIGER/Line is public domain.

**AC:**
- [ ] `frontend/data/tiger-zcta-76119-source.zip` committed (or filtered Shapefile if smaller)
- [ ] `frontend/scripts/extract-zip-76119.mjs` (T2.13) reads from local archive
- [ ] LICENSES.md notes TIGER/Line is U.S. Census Bureau public domain
- [ ] Source URL + download date documented
- [ ] Vitest: extracted GeoJSON matches expected feature count = 1
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.13

---

## Phase 15: Mapbox Polish

### T2.77 --- Custom Mapbox controls (zoom in/out + reset) styled per design tokens | Cx: 12 | P0

**Description:**
T2.3 suppresses default Mapbox interactive controls. Replace with custom controls: zoom-in, zoom-out, reset-to-current-chapter. Styled with W1 design tokens (no Mapbox default chrome). Positioned bottom-right with W1 spacing tokens. Reset button respects current `currentChapter` from `WallContext` — pings the camera back to that chapter's state.

**AC:**
- [ ] `frontend/src/components/wall/MapControls.tsx` created (≤120 lines)
- [ ] 3 buttons: zoom-in (+), zoom-out (−), reset (↻)
- [ ] All visual chrome uses W1 design tokens
- [ ] Reset uses `flyTo` to current chapter's camera state (jumpTo if reduced-motion)
- [ ] Keyboard reachable + ARIA labels (zoom in, zoom out, reset to current chapter)
- [ ] WCAG AAA contrast on icons
- [ ] Vitest: zoom-in calls `map.zoomIn`
- [ ] Vitest: reset calls flyTo with `CHAPTER_CAMERAS[currentChapter]`
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3, T2.7

---

### T2.78 --- Mapbox attribution placement (legal requirement) — branded | Cx: 6 | P0

**Description:**
**LEGAL:** Mapbox terms of service require attribution ("© Mapbox" + "© OpenStreetMap" links) visible and clickable on every map page. Wire the `AttributionControl` from `react-map-gl` with `customAttribution` if needed (e.g., adding "© Trinity Metro" for GTFS). Style the attribution bar with low-opacity W1 token, bottom-left, but never hidden. Spotlight (Honesty + Legacy): legal compliance is non-negotiable — failure to attribute is a Mapbox ToS violation.

**AC:**
- [ ] `react-map-gl` `<AttributionControl>` rendered in `MapboxScene` with default attribution + Trinity Metro custom attribution
- [ ] Attribution bar visible at all zoom levels (per Mapbox ToS)
- [ ] Bar styled with W1 tokens (subtle but always readable)
- [ ] Links open in new tab with `rel="noopener"`
- [ ] WCAG AAA contrast on attribution text
- [ ] Vitest: attribution element present in DOM
- [ ] Vitest: link to mapbox.com present
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.79 --- Mapbox logo positioning (legal) | Cx: 4 | P0

**Description:**
**LEGAL:** Mapbox terms also require the Mapbox logo (or text) visible on the map, bottom-left typically. `react-map-gl` shows it by default; verify it isn't hidden by overlays or the chapter scaffolding. Sibling concern to T2.78. Together they constitute legal compliance.

**AC:**
- [ ] Mapbox logo visible at all chapter states (verified manually + test)
- [ ] No overlay covers the logo (z-index audit on chapter overlays)
- [ ] Vitest: `.mapboxgl-ctrl-logo` or equivalent element rendered
- [ ] Reviewer agent confirms compliance
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.80 --- Mapbox label collision avoidance config | Cx: 8 | P1

**Description:**
At zoom 14 (Ch3), Mapbox label collisions can cause flicker/jump as labels are dropped. Configure the custom style's `text-allow-overlap` and `text-ignore-placement` for street labels and POIs. Documented in T2.18 runbook with screenshots of bad-state and fixed-state. Not a code task — Mapbox Studio config — but a stub task to track verification.

**AC:**
- [ ] T2.18 runbook updated with collision-avoidance section + screenshots placeholders
- [ ] Verified manually: Ch3 (zoom 14) labels stable across small camera tilts
- [ ] No console warnings about label collisions in dev mode
- [ ] Reviewer confirms runbook update
- [ ] No code changes (style-only)

**Depends on:** T2.18

---

### T2.81 --- Mapbox water styled per W1 design tokens | Cx: 6 | P1

**Description:**
The custom Mapbox style colors water. T2.18 documented "water in --bg-surface." Spotlight: water is a presence that matters in FW (Trinity River runs through downtown). Style water with subtle `--bg-surface` blue with optional grain texture (Mapbox `raster` source overlay if texture, or plain solid). Documented in T2.18 runbook.

**AC:**
- [ ] T2.18 runbook updated with water-styling step + Trinity River call-out
- [ ] Verified manually: water visible at zoom 11–14 with W1-aligned color
- [ ] Reviewer confirms
- [ ] No code changes (style-only)

**Depends on:** T2.18

---

### T2.82 --- Mapbox parks / green spaces styled | Cx: 4 | P1

**Description:**
Parks (Mapbox `landuse` `class=park`) styled with subtle muted green per W1 token. Important for FW: Trinity Park, Forest Park, Gateway Park visible at zoom 13–14. Documented in T2.18 runbook.

**AC:**
- [ ] T2.18 runbook updated with parks step
- [ ] Verified manually at zoom 13–14
- [ ] No console errors
- [ ] Reviewer confirms
- [ ] No code changes (style-only)

**Depends on:** T2.18

---

### T2.83 --- Mapbox boundary lines (county, ZIP) styled | Cx: 6 | P1

**Description:**
County and ZIP boundaries on the base style: thin dashed line in `--fg-muted`. Combined with T2.13's bright 76119 outline (high-emphasis), default boundaries provide spatial context without competing for attention. Documented in T2.18 runbook.

**AC:**
- [ ] T2.18 runbook updated with boundary-line step
- [ ] Verified manually at zoom 9–11 (state/county) and 13 (ZIP)
- [ ] Reviewer confirms
- [ ] No code changes (style-only)

**Depends on:** T2.18

---

### T2.84 --- Texas state outline at zoom-out + Tarrant County boundary visible | Cx: 8 | P1

**Description:**
Augments T2.83. At zoom 5–7 (Ch1 → Ch2 transition), the Texas state outline should be visible as a subtle stroke. At zoom 9–11 (Ch2 in), Tarrant County boundary appears. Both pulled from US Census TIGER/Line state + county shapefiles. Committed at `frontend/public/data/wall/texas-state.geojson` and `frontend/public/data/wall/tarrant-county.geojson`. Layered above water/parks but below offices/pins.

**AC:**
- [ ] `frontend/public/data/wall/texas-state.geojson` committed (single MultiPolygon for TX)
- [ ] `frontend/public/data/wall/tarrant-county.geojson` committed
- [ ] `frontend/src/lib/wall/layers/boundaries.ts` exports state + county layer configs (zoom-aware visibility)
- [ ] Layer composer (T2.17) registers boundaries layer
- [ ] Vitest: GeoJSON valid; Texas centroid within TX bounds
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.17

---

### T2.85 --- Mapbox terrain elevation (subtle, only at zoom-out) | Cx: 8 | P2

**Description:**
At Ch1 continental zoom (zoom 3), enable Mapbox `terrain-rgb` source for subtle elevation hillshading — gives America's topography texture without overwhelming the editorial moment. Disabled at zoom > 8 (perf). Documented in T2.18 runbook + a small code stub in `MapboxScene` for the source registration. Mapbox terrain costs additional API calls; only one source registered.

**AC:**
- [ ] `MapboxScene` registers `mapbox-dem` raster-dem source on `map.on('load')`
- [ ] Terrain enabled only when zoom < 8
- [ ] T2.18 runbook updated
- [ ] Vitest: terrain source registered exactly once
- [ ] Performance: no jank when terrain disabled (verified in build smoke)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3, T2.18

---

### T2.86 --- Mapbox 3D buildings only render in viewport (perf gate) | Cx: 8 | P1

**Description:**
T2.24 wires the 3D buildings extrusion. Without a viewport gate, Mapbox renders extrusions for buildings outside the visible area, costing GPU. Wire `filter` expression on the extrusion layer that excludes buildings outside current bounds (Mapbox does this internally to some degree, but verify). Add a perf assertion test.

**AC:**
- [ ] `frontend/src/lib/wall/layers/buildings3d.ts` updated with viewport-aware `filter` expression
- [ ] Vitest: at zoom 14, only viewport-bounded buildings in the layer's effective render set (mocked map.queryRenderedFeatures)
- [ ] Manual smoke: scrolling Ch2→Ch3 has no GPU jank
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.24

---

### T2.87 --- Mapbox console error handling | Cx: 8 | P0

**Description:**
Mapbox emits console warnings (deprecated symbols, missing sprite paths, network failures). Subscribe to `map.on('error')` and route to a single error-handling utility that logs in dev, swallows in prod (don't crash), and reports a single "Mapbox degraded — fallback in use" UI banner if errors persist. Keeps the demo from showing red console errors during a screen-share.

**AC:**
- [ ] `frontend/src/lib/wall/mapboxErrorHandler.ts` exports `attachErrorHandler(map)` + `detachErrorHandler(map)`
- [ ] Errors logged with severity in dev, swallowed in prod
- [ ] If 3+ errors in 5 seconds, render a small "Map degraded" banner (W1 toast/banner pattern)
- [ ] Vitest: triple-error within window triggers banner state
- [ ] Vitest: production build does NOT log to console (mocked NODE_ENV)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.88 --- Mapbox tile load progress indicator | Cx: 6 | P1

**Description:**
While Mapbox tiles load (especially on Ch1→Ch2 zoom-in), the map can flash blank tiles. Render a subtle progress indicator (W1 LoadingState dot or overlay shimmer) tied to `map.on('dataloading')` / `map.on('idle')`. Disappears once tiles are settled.

**AC:**
- [ ] `frontend/src/components/wall/MapTileProgress.tsx` created
- [ ] Subscribes to `dataloading` / `idle` events
- [ ] Hidden when idle, visible during data load
- [ ] Reduced-motion: shows static "Loading map" text instead of animation
- [ ] WCAG AAA contrast
- [ ] Vitest: shows on dataloading, hides on idle
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

### T2.89 --- Mapbox layer toggle (dev-only debug panel) | Cx: 10 | P2

**Description:**
Dev-only floating panel toggleable with `?debug=1` query param. Shows checkboxes for each registered layer (zip, metro, offices, carlos, jobs, city-lights, boundaries, buildings3d). Toggle visibility live. Spotlight (Wisdom): a debug panel speeds dev iteration without bloating prod bundle (gated on `process.env.NODE_ENV !== "production"` AND query param).

**AC:**
- [ ] `frontend/src/components/wall/dev/LayerDebugPanel.tsx` created
- [ ] Renders only when `NODE_ENV !== "production"` AND `?debug=1`
- [ ] One checkbox per registered layer; toggle via `map.setLayoutProperty(id, 'visibility', 'visible'|'none')`
- [ ] Vitest: panel does NOT render in production build
- [ ] Vitest: panel renders in dev with `?debug=1`
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.17

---

### T2.90 --- Camera state preview (dev-only debugger) | Cx: 8 | P2

**Description:**
Sibling to T2.89. Dev-only panel that displays current camera state (zoom, pitch, bearing, lng, lat) live. Plus a button row to "jump to" each chapter's camera state. Speeds iteration on `cameraChoreography.ts`. Gated on dev + `?debug=1`.

**AC:**
- [ ] `frontend/src/components/wall/dev/CameraDebugPanel.tsx` created
- [ ] Reads camera state from `map.on('move')` events
- [ ] Renders 5 buttons (Ch1–Ch5) that call `flyTo` to each chapter's state
- [ ] Dev-only + query param gated
- [ ] Vitest: not rendered in production
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7, T2.89

---

### T2.91 --- Pinch zoom on touch devices (Mapbox native, verified) | Cx: 5 | P1

**Description:**
T2.3 suppresses pan/zoom controls but Mapbox native touch gestures (pinch-to-zoom, two-finger rotate) should remain enabled — touch users expect them. Verify `touchZoomRotate` is enabled by default in `react-map-gl/mapbox` and add a smoke test. Reduced-motion: rotate disabled (just zoom).

**AC:**
- [ ] `MapboxScene` ensures `touchZoomRotate` enabled (default)
- [ ] Reduced-motion: `map.touchZoomRotate.disableRotation()` called
- [ ] Vitest: pinch-zoom enabled when reduced-motion=false; rotation disabled when reduced-motion=true
- [ ] Manual smoke on iPad / Android Chrome (documented in PR)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.3

---

## Phase 16: Interactive Map Elements

### T2.92 --- Hover on office marker reveals address card | Cx: 14 | P0

**Description:**
On hover over any office marker (T2.12), reveal a card with `{name, address, hours, phone}` — pulls from feature properties. Card positioned via Mapbox `popup` API (anchored to marker) but styled with W1 tokens (NOT default Mapbox popup chrome). Closes on mouse-leave with 100ms delay. Touch devices: tap-to-show, tap-elsewhere-to-dismiss.

**AC:**
- [ ] `frontend/src/components/wall/OfficeCard.tsx` created (≤200 lines)
- [ ] Hover/tap on office marker shows card
- [ ] Card content: name, address, hours, phone (from feature properties)
- [ ] Card styled with W1 design tokens
- [ ] WCAG AAA contrast on card text
- [ ] Vitest: hover triggers card render
- [ ] Vitest: mouse-leave dismisses card after 100ms
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12, T2.92 — note: this is the parent task; click variant in T2.93

---

### T2.93 --- Click office marker opens card with phone tel: + directions links | Cx: 12 | P0

**Description:**
Augments T2.92. Click (vs hover) opens a "pinned" version of the card that doesn't dismiss until escape/outside-click. Adds two link buttons: "Call" (tel:phone) and "Directions" (deep links to Apple Maps + Google Maps with the office coordinates). Spotlight (Multiple Selves — Carlos's voice): if Carlos hits an office, he wants to call or get directions immediately.

**AC:**
- [ ] Click on office marker pins the card (doesn't dismiss on mouse-leave)
- [ ] Card includes "Call" button: `<a href="tel:817-...">`
- [ ] Card includes "Directions" button: opens picker — Apple Maps (`maps://?daddr=...`) on iOS, Google Maps (`https://maps.google.com/?daddr=...`) elsewhere
- [ ] Escape key closes pinned card
- [ ] Click outside closes pinned card
- [ ] Tab order logical (Call → Directions → Close)
- [ ] Vitest: click pins, escape closes
- [ ] Vitest: tel: link present with formatted phone
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.92

---

### T2.94 --- Office hours rendering ("Mon–Fri 8–5" format) | Cx: 6 | P1

**Description:**
Office feature properties carry `hours: "Monday – Friday, 8:00 AM – 5:00 PM"` (verbose). Card UI condenses to "Mon–Fri 8–5" for editorial brevity. A pure render helper. Locale-aware: Spanish renders "Lun–Vie 8–5".

**AC:**
- [ ] `frontend/src/lib/wall/formatHours.ts` exports `formatHours(hours: string, locale: 'en'|'es'): string`
- [ ] Returns "Mon–Fri 8–5" for verbose EN input
- [ ] Returns "Lun–Vie 8–5" for ES locale
- [ ] Vitest: 4+ hour strings tested for both locales
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.95 --- Phone link tel: with formatting | Cx: 4 | P1

**Description:**
The `tel:` link uses raw digits; the displayed phone uses formatted digits ("(817) 884-1574"). Helper: `formatPhone(raw)` returns formatted string for display, `phoneToTel(raw)` returns digits-only for href. Sibling helper to T2.94.

**AC:**
- [ ] `frontend/src/lib/wall/formatPhone.ts` exports `formatPhone(raw)` + `phoneToTel(raw)`
- [ ] formatPhone("8178841574") returns "(817) 884-1574"
- [ ] phoneToTel("(817) 884-1574") returns "+18178841574"
- [ ] Vitest: 5+ phone strings tested
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.96 --- ZIP boundary highlight on hover | Cx: 8 | P1

**Description:**
When user hovers near the 76119 boundary (T2.13), the boundary stroke brightens (opacity 0.6 → 1.0) for ambient interactivity. Implemented via Mapbox feature-state. Works only in Ch3+ (where ZIP is visible). Reduced-motion: no transition (instant snap).

**AC:**
- [ ] Mouse hover near 76119 polygon sets feature-state `hover=true`
- [ ] Mapbox paint expression reads feature-state for stroke opacity
- [ ] Reduced-motion: instant on/off
- [ ] Vitest: feature-state set on hover, cleared on leave
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.13

---

### T2.97 --- Tarrant County boundary subtle dashed line | Cx: 5 | P1

**Description:**
T2.84 commits Tarrant County boundary GeoJSON. Style it as a subtle dashed line (`line-dasharray: [2, 4]`) in `--fg-muted` so the county outline is visible at Ch2/Ch4 mid-altitude without competing with the ZIP highlight.

**AC:**
- [ ] `boundaries.ts` (T2.84) layer config uses dashed stroke for Tarrant County
- [ ] Color: `--fg-muted`; width: 1px
- [ ] Visible only at zoom 9–13 (zoom-aware paint expression)
- [ ] Vitest: layer config has `line-dasharray` paint property
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.84

---

## Phase 17: Editorial Details

### T2.98 --- Drop cap on Chapter 1 hero | Cx: 8 | P1

**Description:**
W1 ships variable font infrastructure. Spotlight (Editorial): the Ch1 hero question gains a drop cap on the first letter ("W" of "What's") — Inter Variable at weight 900, font-size 5.5em, float-left, line-height 0.9. Pure CSS, no JS. Reduced-motion: drop cap renders normally (it's not animated; it's typography).

**AC:**
- [ ] `Chapter01Continental.tsx` overlay heading uses `:first-letter` CSS for drop cap
- [ ] Drop cap size, weight, line-height tied to W1 typography tokens
- [ ] Visual smoke: drop cap renders without overflow on common viewports (1280, 1440, 1920)
- [ ] WCAG AAA contrast preserved
- [ ] Vitest: drop cap class applied to heading
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.19

---

### T2.99 --- Pull quote for Carlos voice in Chapter 2 | Cx: 10 | P1

**Description:**
Editorial detail: Ch2 (city arrival) renders a Carlos pull-quote: "I came home with $300." (real quote; verifiably attributable to a recently-released-individual narrative — sourced from publicly published reentry research, NOT fabricated. Source attribution committed.) Quote rendered in serif italic at 1.5em, framed with W1 quote-mark glyph. Visible at progress 0.15–0.18.

**AC:**
- [ ] `wall.ch2.pullQuote` + `wall.ch2.pullQuoteSource` keys in en.json + es.json (T2.50 follow-up; reviewer initials)
- [ ] Source attribution: verified public source URL committed in `legalReferences.ts` (T2.74) or feature-prop
- [ ] If no verifiable real source, mark quote as "composite — illustrative" and document in PR
- [ ] Pull-quote rendered in `Chapter02CityArrival.tsx` with W1 typography
- [ ] WCAG AAA contrast verified
- [ ] Vitest: pull quote text appears at progress 0.15–0.18
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.23, T2.50

---

### T2.100 --- Chapter divider as visual art (small SVG ornament) | Cx: 8 | P1

**Description:**
Between chapters (e.g., Ch1→Ch2 transition zone), render a small SVG ornament — branded glyph (W1 G+path mark, smaller). Acts as a visual "page turn" marker. Only visible 1–2% of scroll progress at chapter boundaries. Reduced-motion: ornament renders statically (no animation).

**AC:**
- [ ] `frontend/public/wall-paths/chapter-divider.svg` committed (small ornament, ≤4KB)
- [ ] `frontend/src/components/wall/ChapterDivider.tsx` renders ornament at chapter-boundary scroll positions
- [ ] Reduced-motion: static
- [ ] WCAG AAA: decorative role, aria-hidden=true
- [ ] Vitest: ornament rendered at boundary scroll
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6

---

### T2.101 --- Branded scrollbar overlay during chapter scroll | Cx: 8 | P2

**Description:**
Spotlight (Editorial): a small branded vertical scroll progress overlay (right edge of viewport) shows current chapter position visually. Renders 6-tick scale (5 chapters + start). Active tick uses `--accent-amber`. Inspired by NYT "scrollytelling" patterns. Reduced-motion: still renders (informational, not animated).

**AC:**
- [ ] `frontend/src/components/wall/ChapterScrollIndicator.tsx` created
- [ ] 6 ticks, current chapter active (amber)
- [ ] Position: fixed right edge, vertically centered, low z-index
- [ ] WCAG AAA contrast on ticks
- [ ] Hidden on viewport width < 1024px (mobile uses other indicators)
- [ ] Vitest: active tick matches currentChapter
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.8

---

### T2.102 --- Sticky chapter title fade in/out | Cx: 6 | P1

**Description:**
Editorial: at top of each chapter, a small chapter title ("Chapter 2 — City Arrival") fades in for the first 5% of chapter progress, holds, then fades out at 95%+. Lives within `ChapterScaffold` as an opt-in slot. Reduced-motion: instant on/off.

**AC:**
- [ ] `ChapterScaffold` gains `chapterTitle` prop
- [ ] Title fades in/out per scroll progress within chapter
- [ ] Reduced-motion: instant
- [ ] WCAG AAA contrast
- [ ] Vitest: title visible at chapterProgress 0.5; opacity 0 at 0 and 1
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6

---

### T2.103 --- Editorial blockquote treatment for Carlos quotes | Cx: 6 | P1

**Description:**
Sibling to T2.99. Reusable `<EditorialQuote>` component wraps Carlos voice quotes (Ch2 pull-quote, future Ch3 + W3 chapters). Quote-mark glyph, attribution line, source URL link. Used in W2 once + reused in W3 multiple times.

**AC:**
- [ ] `frontend/src/components/wall/EditorialQuote.tsx` created (≤120 lines)
- [ ] Props: `text, attribution, sourceUrl?, lang`
- [ ] Renders quote-mark glyph + italic body + attribution
- [ ] WCAG AAA contrast
- [ ] Vitest: quote text + attribution rendered
- [ ] Vitest: optional sourceUrl renders as link
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T2.104 --- Chapter atmosphere preset library | Cx: 10 | P1

**Description:**
Each chapter has a distinct atmosphere: tone (color tint), accent (which W1 token is dominant), sound preset (rustle, bus engine, etc.). Currently scattered across chapter files. Spotlight (Compound Lens): consolidate into `frontend/src/lib/wall/chapterAtmosphere.ts` so W3 chapters 6–10 follow the same pattern. Each chapter declares: `{tint, accentToken, soundPresetId, dropCap}`.

**AC:**
- [ ] `frontend/src/lib/wall/chapterAtmosphere.ts` exports `CHAPTER_ATMOSPHERES` const for chapters 1–5
- [ ] Each entry: `{tint, accentToken, soundPresetId, dropCap}`
- [ ] Chapter components consume preset (no scattered tone/accent literals)
- [ ] Vitest: every chapter has a complete preset shape
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7

---

## Phase 18: Fort Worth Landmarks

### T2.105 --- Trinity River visualization on map | Cx: 8 | P1

**Description:**
Trinity River runs through downtown FW. T2.81 styled water generically; this task ensures the Trinity River specifically is visible at zoom 11–14 with a slightly stronger blue. Pulled from Mapbox `waterway` source via the custom style (T2.18 update). Documented in T2.18 runbook.

**AC:**
- [ ] T2.18 runbook updated: Trinity River styled with `--accent-cyan` at low opacity
- [ ] Verified manually: river visible at zoom 11–14
- [ ] Reviewer confirms
- [ ] No code changes (style-only)

**Depends on:** T2.18, T2.81

---

### T2.106 --- Sundance Square reference in Chapter 2 city arrival overlay | Cx: 4 | P1

**Description:**
Editorial detail: Ch2's city-arrival copy can reference a real downtown FW landmark. "Carlos lives here. ZIP 76119. East of downtown — past Sundance Square, past the courthouse." (only as editorial; Sundance Square is a real public-private revitalized district at 5th & Main, FW). Verify with FW Convention & Visitors Bureau. Adds geographic grounding without naming individuals.

**AC:**
- [ ] Ch2 EN copy (T2.50) includes "past Sundance Square" reference
- [ ] Source URL for Sundance Square documented in `legalReferences.ts`
- [ ] ES translation parity (Sundance Square as proper noun, not translated)
- [ ] Vitest: copy contains "Sundance Square" string
- [ ] Reviewer confirms accuracy
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.50

---

### T2.107 --- Stockyards reference (chapter background mention) | Cx: 4 | P2

**Description:**
The Fort Worth Stockyards is FW's iconic historic district. Subtle background reference in Ch2 or Ch3 supporting copy: "north of the stockyards" or similar. Geographic grounding for FW residents. Source attribution.

**AC:**
- [ ] Ch2 or Ch3 supporting copy includes Stockyards reference (TBD which fits better)
- [ ] Source URL documented in `legalReferences.ts`
- [ ] ES translation parity
- [ ] Vitest: copy contains reference
- [ ] Reviewer confirms
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.50, T2.51

---

### T2.108 --- FW DAO seal subtle on chapter 9 (deferred to W3) | Cx: 4 | P2

**Description:**
**Deferred to W3.** The FW DAO is a sponsor of HackFW; their seal/insignia would appear subtly on Chapter 9 (fly to Montgomery / civic pride moment). Stub task here in W2 so W3 doesn't have to invent the asset path. W2 commits the SVG asset; W3 wires it. Source: official FW DAO branding kit (request from sponsor or public site).

**AC:**
- [ ] `frontend/public/wall-paths/fw-dao-seal.svg` committed (placeholder if asset unavailable)
- [ ] Source attribution + license documented in PR
- [ ] If no official asset, document in `LICENSES.md` as placeholder pending sponsor asset
- [ ] No code wiring (W3 task)

**Depends on:** none

---

### T2.109 --- Texas state silhouette + America silhouette assets | Cx: 6 | P1

**Description:**
Spotlight (Editorial): Ch1 transition could feature a brief America silhouette → Texas silhouette → Tarrant County silhouette zoom-in metaphor. Commit SVG assets for all three at `frontend/public/wall-paths/silhouettes/`. Used in transitions between chapters 1→2 (subtle, decorative). Reduced-motion: silhouettes static.

**AC:**
- [ ] `frontend/public/wall-paths/silhouettes/america.svg` committed
- [ ] `frontend/public/wall-paths/silhouettes/texas.svg` committed
- [ ] `frontend/public/wall-paths/silhouettes/tarrant-county.svg` committed
- [ ] All SVGs under 8KB each (SVGO pass)
- [ ] Decorative role (aria-hidden) when used
- [ ] No code wiring yet (used in T2.110 ambient particles or later W3)
- [ ] `bpsai-pair arch check` passes (assets only)

**Depends on:** none

---

### T2.110 --- Continental ambient particles (subtle stars at zoom-out) | Cx: 8 | P2

**Description:**
At Ch1 continental zoom (zoom 3), render subtle ambient particles ("stars" — small white dots at low opacity) drifting across the screen. CSS-only animation (no JS) — `@keyframes drift`. Reduced-motion: particles static. Disappear at zoom > 6.

**AC:**
- [ ] `frontend/src/components/wall/AmbientParticles.tsx` created (≤80 lines)
- [ ] CSS-only drift animation
- [ ] Reduced-motion: static (no `@keyframes`)
- [ ] Visible only at currentChapter=1
- [ ] WCAG AAA: decorative role, aria-hidden
- [ ] Vitest: rendered at chapter 1, hidden at chapter 2
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.21

---

## Phase 19: Camera Polish

### T2.111 --- flyTo cancellable on user manual drag | Cx: 8 | P0

**Description:**
T2.9 noted user drag MAY override scroll-driven camera. Implement: subscribe to Mapbox `dragstart` and `pitchstart` events; if firing during a flyTo, abort the flyTo (Mapbox auto-aborts on user gesture, but we need to suppress the next chapter-change-triggered flyTo for 2 seconds so user has control). Counter resets on next chapter boundary.

**AC:**
- [ ] `flyToOrchestrator.ts` (T2.9) updated with user-gesture suppression window
- [ ] Drag/pitch event sets `userOverrideUntil = now + 2000` timestamp
- [ ] Subsequent flyTo calls skip if `now < userOverrideUntil`
- [ ] Suppression auto-clears after window
- [ ] Vitest: drag → next flyTo skipped
- [ ] Vitest: 2.1s after drag → flyTo resumes
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.9

---

### T2.112 --- flyTo cancellable on tab-blur (pause) | Cx: 6 | P1

**Description:**
When user tab-blurs (e.g., switches to another tab during demo), pause flyTo orchestrator. On tab-focus resume, jump to current chapter's state (no in-flight catch-up animation). Spotlight (Multiple Selves — judge on TV): if a judge tabs away mid-demo, returning shouldn't show a half-finished animation.

**AC:**
- [ ] `flyToOrchestrator.ts` subscribes to `visibilitychange`
- [ ] On hidden: cancel in-flight flyTo
- [ ] On visible: jumpTo current chapter's camera state
- [ ] Vitest: visibility change cancels and jumpTos
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.9

---

### T2.113 --- flyTo speed adapts to chapter complexity | Cx: 8 | P1

**Description:**
Some chapter transitions are short distances (Ch4a → Ch4b: same camera, bearing tilt only) while others are long (Ch1 → Ch2: continental → city, zoom 3 → 11). Vary `flyTo speed` per transition: short = 0.6, long = 1.4. Defaults to 1.0. Per-transition table lives in `cameraChoreography.ts` extension.

**AC:**
- [ ] `cameraChoreography.ts` exports `TRANSITION_SPEEDS` map (e.g., `"1->2": 1.4, "4a->4b": 0.6`)
- [ ] `flyToOrchestrator.ts` reads speed from table for current transition
- [ ] Falls back to 1.0 if pair not in table
- [ ] Vitest: speed for known transition matches table
- [ ] Vitest: unknown transition uses default 1.0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7, T2.9

---

### T2.114 --- Smooth chapter transition seams (ease across boundaries) | Cx: 10 | P1

**Description:**
When a chapter transition fires at scroll progress 0.20 (Ch1→Ch2 boundary), the overlay opacity and camera flyTo can feel "stepped" (overlay fades at 0.18–0.22, camera jumps at 0.20). Smooth the seam: overlay opacity + camera curve overlap by 5%. Spotlight (Wisdom): brief said "transitions" but didn't specify seam smoothing.

**AC:**
- [ ] `WallContainer` orchestrates 5% overlap on overlay fades around chapter boundaries
- [ ] Camera flyTo curve aligned to overlay fade (no perceptible "jump")
- [ ] Reduced-motion: instant cuts (no overlap)
- [ ] Vitest: at scroll 0.20 (boundary), Ch1 opacity ~0.5 AND Ch2 opacity ~0.5 (overlap)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.6, T2.9

---

### T2.115 --- Reduced-motion fallback keeps all data layers visible | Cx: 6 | P0

**Description:**
Spotlight (Resilience): brief said reduced-motion uses jumpTo. But the data layers (Trinity Metro, offices, ZIP boundary, jobs) can still fade — making reduced-motion users miss the data REVEAL. Fix: reduced-motion path renders ALL data layers visible from start (no fade), so users see the data immediately even if they don't see the camera flight. The "still-image fallback that's still beautiful" applies to data, not just motion.

**AC:**
- [ ] All chapter components: reduced-motion path sets all data-layer opacities to final visible value at mount
- [ ] Vitest: reduced-motion + Ch1 → all relevant layers (city-lights) visible at progress=0
- [ ] Vitest: reduced-motion + Ch3 → ZIP boundary + Carlos pin visible at progress=0
- [ ] axe-core scan still green per chapter
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.22, T2.26, T2.40

---

## Phase 20: Chapter 5 Labyrinth Deep Polish

### T2.116 --- Animated arrow glyphs between offices (not just lines) | Cx: 12 | P1

**Description:**
T2.42 commits the chaotic SVG path. Augment: along the path, render small directional arrow glyphs at intervals (every ~15% of path length) that "walk" in the path direction. The arrows convey FORCED motion through the bureaucracy (not the user's choice). Reduced-motion: arrows static at fixed positions.

**AC:**
- [ ] `frontend/public/wall-paths/labyrinth-arrows.svg` committed (arrow glyph element)
- [ ] `Chapter05Labyrinth.tsx` overlays arrow glyphs along the path at intervals
- [ ] Arrows animate along path (CSS or JS — pick one)
- [ ] Reduced-motion: arrows static
- [ ] WCAG AAA contrast on arrows against dark base
- [ ] Vitest: 5+ arrows rendered along the labyrinth path
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.42

---

### T2.117 --- Real form names on labyrinth path tooltips | Cx: 8 | P1

**Description:**
The labyrinth path connects 5 offices. At each office node, a small label shows the actual form name Carlos would file: "DPS Form CR-09" (Article 55 expunction petition), "HHSC Application H1010" (childcare/Medicaid), "Tarrant County Civil Cover Sheet", "TWC Form C-3" (workforce intake), "LANWT Intake Form". Verify each form name from official agency sites; commit source URLs in `legalReferences.ts`.

**AC:**
- [ ] `legalReferences.ts` exports `LABYRINTH_FORMS` array of 5 entries: `{office, formName, formNumber, sourceUrl}`
- [ ] Each form verified from primary source (DPS, HHSC, Tarrant County, TWC, LANWT)
- [ ] `Chapter05Labyrinth.tsx` renders form-name labels at office nodes
- [ ] Vitest: 5 form labels rendered with correct text
- [ ] Reviewer confirms primary sources
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.41, T2.74

---

### T2.118 --- Forms counter scrolling tally with branded numerals | Cx: 8 | P1

**Description:**
T2.41 ticks 0→47 forms counter. Spotlight (Editorial): use Inter Variable's tabular-nums + "scrolling tally" pattern — each digit visually rolls (CSS `transform: translateY` per digit). 47 → 50 looks like a slot machine but tasteful. Reduced-motion: snaps without scroll. Pause animation when scroll pauses (don't tick during a hold). 

**AC:**
- [ ] `frontend/src/components/wall/ScrollingTally.tsx` created (≤150 lines, tabular-nums, transform-Y per digit)
- [ ] Used in Ch5 forms counter
- [ ] Pauses animation when scroll velocity = 0
- [ ] Reduced-motion: snaps to final
- [ ] Vitest: at progress=0.5, tally renders intermediate value (e.g., 24)
- [ ] Vitest: scroll-paused state freezes counter
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.41

---

### T2.119 --- Labyrinth dead-end indicator at certain offices | Cx: 6 | P2

**Description:**
T2.42's path includes intentional dead-ends. Augment: at each dead-end node, render a small "✕" or "stop" glyph in W1 muted-red. Communicates "this office told Carlos to go elsewhere — dead end." Subtle, not loud.

**AC:**
- [ ] Dead-end glyph SVG rendered at 3 dead-end positions in the labyrinth
- [ ] Color: W1 muted-red token
- [ ] Decorative role (aria-hidden) — narration via T2.44 ARIA-live
- [ ] Reduced-motion: glyphs static
- [ ] Vitest: 3 dead-end glyphs rendered
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.42

---

## Phase 21: Time-of-Day Prefiguration

### T2.120 --- Chapter 1 lighting hint based on user's local time | Cx: 8 | P1

**Description:**
W1 ships `useTimeOfDay` hook. Spotlight (Fusion): consume the hook in Ch1's continental view to apply a subtle CSS tint — sunrise gold at 6–8am, day neutral at 8am–6pm, sunset orange at 6–8pm, night deep-blue at 8pm–6am. NOT the Mapbox sky (that's deferred to W4); just an editorial overlay tint above Ch1. Reduced-motion: tint applied (it's static, not animated).

**AC:**
- [ ] `Chapter01Continental.tsx` consumes `useTimeOfDay` and applies tint via CSS variable
- [ ] 4 time bands: dawn, day, dusk, night
- [ ] Tint applied to a ::before overlay, not blocking interaction
- [ ] WCAG AAA contrast on hero text preserved across all 4 tints
- [ ] Vitest: each time band sets correct tint variable
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.19

---

### T2.121 --- Chapter 2 city arrival sky tinted per time | Cx: 8 | P1

**Description:**
Sibling to T2.120. Ch2 (city arrival) overlay tint shifts per time-of-day same way. Day = neutral, dusk = orange, night = deep blue. NOT the Mapbox sky layer (W4); editorial overlay only.

**AC:**
- [ ] `Chapter02CityArrival.tsx` consumes `useTimeOfDay` for overlay tint
- [ ] 4 time bands match T2.120 logic
- [ ] WCAG AAA contrast preserved
- [ ] Vitest: each band sets correct tint
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.23, T2.120

---

### T2.122 --- Chapter 3 neighborhood lighting subtle shift | Cx: 6 | P1

**Description:**
Sibling to T2.120/T2.121. Ch3 (neighborhood) tint shifts per time-of-day, but more subtle (the chapter is closer-in; tint should be less prominent). Same time-band table, lower opacity.

**AC:**
- [ ] `Chapter03Neighborhood.tsx` consumes `useTimeOfDay` for subtle tint (max opacity 0.15)
- [ ] WCAG AAA contrast preserved
- [ ] Vitest: tint applied per band
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.27, T2.120

---

## Phase 22: Bus 4 + Transit Detail Accuracy

### T2.123 --- Trinity Metro Bus 4 livery accurate (real photo reference) | Cx: 6 | P1

**Description:**
Ch4b highlights Bus 4 polyline in amber. Spotlight (Multiple Selves — FW resident who knows): real Trinity Metro brand colors are blue + green, NOT amber. Tension: editorial amber matches W1 accent system, but it's not Trinity Metro accurate. Decision: Bus 4 highlight uses Trinity Metro REAL brand colors (blue) for editorial accuracy; W1 amber accent stays in editorial overlays. Verify brand colors from Trinity Metro brand guide / public site. Document in `legalReferences.ts`.

**AC:**
- [ ] `legalReferences.ts` exports `TRINITY_METRO_BRAND = {primaryColor, secondaryColor, sourceUrl}`
- [ ] T2.11 layer config updated: highlighted Bus 4 uses Trinity Metro primary blue (verified hex)
- [ ] Editorial overlay still uses W1 amber for stat band (visual hierarchy preserved)
- [ ] Vitest: Bus 4 paint expression uses Trinity Metro brand color
- [ ] Reviewer confirms primary source
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.11

---

### T2.124 --- Bus 4 route GTFS polyline accuracy verification | Cx: 6 | P0

**Description:**
T2.11 commits Trinity Metro routes. Spot-check that Bus 4's polyline matches the published route map (Trinity Metro publishes route maps as PDFs at https://ride.trinitymetro.org/). Reviewer agent compares 5+ stops along the route with the committed polyline coordinates. If mismatched, file blocking sub-task to refresh GTFS.

**AC:**
- [ ] Reviewer compares Bus 4 polyline with published route map (5+ stop checkpoints)
- [ ] Mismatches documented; file refresh sub-task if needed
- [ ] Vitest: Bus 4 LineString has ≥ 20 coordinates (sanity: real route, not simplified)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.11

---

### T2.125 --- Bus stop markers along Bus 4 + Bus 6 routes | Cx: 8 | P1

**Description:**
T2.11 commits route polylines. Augment: extract bus stop points from GTFS `stops.txt` for Bus 4 and Bus 6 specifically, commit at `frontend/public/data/wall/trinity-metro-stops-bus4-bus6.geojson`. Render as small dots in Ch4b when Bus 4 highlighted. Communicates: "Carlos's stop is HERE. Court is THERE."

**AC:**
- [ ] `frontend/public/data/wall/trinity-metro-stops-bus4-bus6.geojson` committed (stops for Bus 4 + Bus 6 only)
- [ ] `frontend/src/lib/wall/layers/busStops.ts` exports layer config (small circles)
- [ ] Layer composer registers it (visible only Ch4b)
- [ ] Vitest: GeoJSON has ≥ 10 stops total
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.11, T2.17

---

### T2.126 --- Bus 6 transfer point highlighted in Ch4a | Cx: 5 | P1

**Description:**
Ch4a editorial: "Bus 4 + Bus 6 = 71 minutes." The TRANSFER point (where Carlos changes from Bus 4 to Bus 6) is the actual time-cost. Highlight that single transfer-stop with a different glyph (a small "↻" indicator) in Ch4a.

**AC:**
- [ ] Bus 4 + Bus 6 transfer stop identified (real GTFS check, likely downtown FW transit center)
- [ ] Transfer stop glyph rendered in Ch4a only (custom icon at that coord)
- [ ] WCAG AAA: glyph + tooltip "Transfer point — 71 minutes total"
- [ ] Vitest: transfer glyph rendered in Ch4a state
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.32, T2.125

---

## Phase 23: Cross-Chapter Integration + Tests

### T2.127 --- Carlos's home pin: PII-safe representative block confirmation | Cx: 4 | P0

**Description:**
T2.28 already covers PII review. This is a follow-up: add a runtime assertion in `paths.ts` that the committed pin's reverse-geocoding result (cached at build time, NOT a runtime API call) does not match a residential parcel. Build-time check: a build script reverse-geocodes the pin via Mapbox geocoding API once and asserts result type ≠ "address" (≠ "place" ≠ "poi.residential"). Spotlight (Honesty Lens): make the verification programmatic, not just human review.

**AC:**
- [ ] `frontend/scripts/verify-carlos-pin-pii.mjs` created — build-time reverse-geocode + assertion
- [ ] Script run as part of CI (or as a pre-commit hook for `paths.ts` changes)
- [ ] Output committed at `frontend/data/carlos-pin-verification.json` for archival
- [ ] Vitest: archived verification result confirms type ≠ "address"
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.14, T2.28

---

### T2.128 --- Office state machine future-proofed for W3 Chapter 7 | Cx: 6 | P1

**Description:**
W3 Ch7 introduces a Carlos avatar walking; the offices will also enter "visited / pending / current" states. W2 ships the data layer (T2.12); add an extensible state-machine schema NOW so W3 doesn't refactor it. Each office gets a `state: "default" | "highlighted" | "visited" | "current"` property in feature properties; W2 renders only "default" + "highlighted"; W3 will use "visited" + "current".

**AC:**
- [ ] `tarrant-offices.geojson` features have `state` property (default = "default")
- [ ] `frontend/src/lib/wall/layers/offices.ts` paint expression supports all 4 states (W2 uses 2; W3 enables others)
- [ ] TypeScript type `OfficeState` exported
- [ ] Vitest: paint expression returns correct opacity for all 4 states
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.12

---

### T2.129 --- Pre-load Chapter 6 data when Chapter 5 enters viewport | Cx: 8 | P1

**Description:**
W3 Ch6 (cliff calculator) requires data + assets that aren't loaded by W2's bundle. Spotlight (Compound): pre-fetch Ch6 data (W3 will define the file paths; W2 stubs them) when scroll enters Ch5 (~10s before user sees Ch6). Ch6 then renders instantly. Stub task: defines the pre-load hook + stub file paths.

**AC:**
- [ ] `frontend/src/hooks/usePreloadNextChapter.ts` created
- [ ] Hook triggers `link rel="prefetch"` for Ch6 dynamic chunk + data files
- [ ] WallContainer mounts hook when currentChapter=5
- [ ] Vitest: prefetch link element added to head when chapter=5
- [ ] No regression to current Ch5 render
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.43, T2.57

---

### T2.130 --- Chapter scroll-back state preservation | Cx: 6 | P0

**Description:**
Spotlight (Resilience): if user scrolls to Ch4 then back to Ch1, then forward to Ch4 again, the chapter state (e.g., Ch4 sub-chapter, audio play history) should NOT reset. Audit each chapter's local state (especially Ch4 sub-chapter machine, Ch5 forms counter, Ch4 sound-played flags) for proper memoization. Tests verify scroll-back-forward doesn't replay sounds or reset counter.

**AC:**
- [ ] `Chapter04TheWall.tsx` sub-chapter state preserved on scroll-out (memoized to currentChapter)
- [ ] `Chapter05Labyrinth.tsx` counter state preserved (no reset on scroll-back)
- [ ] Audio "already-played" flags tracked across full scroll session (not chapter-local)
- [ ] Vitest: simulated scroll Ch4→Ch1→Ch4 — sub-chapter state matches expected (e.g., last-known sub-chapter restored)
- [ ] Vitest: simulated scroll Ch5→Ch1→Ch5 — sound NOT replayed
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.31, T2.41

---

### T2.131 --- Visual regression test per chapter (Playwright screenshot) | Cx: 14 | P1

**Description:**
Spotlight (Wisdom): a per-chapter Playwright screenshot test catches visual regressions (e.g., a CSS change accidentally breaks Ch3 overlay layout). Lightweight — 5 screenshots, baseline committed at `frontend/tests/__snapshots__/wall-chapters/`. Compared per CI run with pixel diff threshold 1%.

**AC:**
- [ ] `frontend/tests/wall-visual.spec.ts` (Playwright) renders each chapter at fixed viewport (1280×720)
- [ ] 5 baseline PNGs committed under `frontend/tests/__snapshots__/wall-chapters/`
- [ ] Pixel diff threshold: 1%
- [ ] CI runs Playwright on every PR
- [ ] If Playwright not in repo, this task brings it in (single setup task in `package.json` + minimal config)
- [ ] `bpsai-pair arch check` passes (test config files only)

**Depends on:** T2.66

---

### T2.132 --- Mapbox layer visibility integration test | Cx: 8 | P0

**Description:**
Single integration test: per chapter, query the map for which layer IDs are visible. Asserts: Ch1 → only city-lights + boundaries; Ch2 → + trinity-metro + buildings3d; Ch3 → + zip + carlos-path; Ch4a → + offices (district clerk highlighted); Ch5 → + labyrinth + offices (all). Catches "I forgot to fade in the offices layer for Ch4" bug.

**AC:**
- [ ] `frontend/src/__tests__/wall/layer-visibility-integration.test.tsx` exists
- [ ] Per-chapter assertion of visible layer set
- [ ] Mock Mapbox map with layer-tracking
- [ ] Vitest passes
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.63

---

### T2.133 --- Camera transition timing test | Cx: 6 | P1

**Description:**
Asserts that flyTo `duration` is sane (e.g., Ch1→Ch2 transition between 1500ms and 4000ms). Catches accidental coord-edit that triples the transition time, ruining the demo cadence.

**AC:**
- [ ] `frontend/src/lib/wall/__tests__/transition-timing.test.ts` exists
- [ ] Per-transition: assert duration within sane bounds (per pair)
- [ ] Reduced-motion: duration = 0 verified
- [ ] Vitest passes
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.7, T2.113

---

### T2.134 --- Office click-to-card interaction test | Cx: 6 | P0

**Description:**
Vitest: simulate click on an office marker, assert OfficeCard renders with correct properties (name, address, phone, hours), assert escape key closes, assert outside click closes, assert tab order. Locks the interactive contract from T2.92/T2.93.

**AC:**
- [ ] `frontend/src/components/wall/__tests__/OfficeCard.test.tsx` exists
- [ ] Tests: click opens, escape closes, outside click closes, tab order Call→Directions→Close
- [ ] All 5 office categories tested (court, benefits, dps, workforce, legal)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.92, T2.93

---

### T2.135 --- Accessibility: every interactive marker keyboard-reachable | Cx: 8 | P0

**Description:**
Audit + test: every office marker, every Carlos pin, every interactive layer is keyboard-focusable (Tab) and activatable (Enter/Space). Mapbox markers default to non-focusable; we wire `role="button"` + `tabindex="0"` via a custom marker-button overlay if needed. axe-core verifies.

**AC:**
- [ ] All office markers keyboard-focusable
- [ ] Enter/Space on focused marker opens OfficeCard (T2.92/T2.93 contract)
- [ ] axe-core scan returns zero violations on full WallContainer with markers visible
- [ ] Vitest: simulated Tab through page reaches all 5 office markers
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.92

---

### T2.136 --- Sound clip license attribution | Cx: 4 | P0

**Description:**
Honest Uncertainty #7. T2.37 + T2.43 commit MP3 clips. Add a `frontend/public/sounds/wall/LICENSES.md` listing each clip with: source URL (Freesound.org link), license (CC0 / CC-BY / royalty-free), original creator, license confirmation date. Submission compliance.

**AC:**
- [ ] `frontend/public/sounds/wall/LICENSES.md` lists all 5 clips (4 Ch4 + 1 Ch5)
- [ ] Each entry: source URL, license type, creator, date
- [ ] Reviewer agent confirms each license URL resolves (mocked check)
- [ ] `bpsai-pair arch check` passes (docs only)

**Depends on:** T2.37, T2.43

---

### T2.137 --- Spanish reviewer asynchronous batch pass | Cx: 6 | P1

**Description:**
Honest Uncertainty #5. Bottleneck risk: per-chapter ES copy each requires a reviewer. Convert to a single batch: T2.49–T2.53 ES strings collected into one document `docs/spanish-review-w2.md`, reviewer initials once at the top. Reduces blocker risk on Spanish reviewer availability.

**AC:**
- [ ] `docs/spanish-review-w2.md` aggregates all W2 ES copy with EN side-by-side
- [ ] Reviewer initials + date at document top
- [ ] Each chapter's task references this doc instead of demanding individual reviewer pass
- [ ] If reviewer unavailable by sprint end, doc marked `[ES-pending-review]` and W4 follow-up issue created
- [ ] No code changes (docs only)

**Depends on:** T2.49, T2.50, T2.51, T2.52, T2.53

---

### T2.138 --- Real Carlos quotes embedded as editorial moments | Cx: 6 | P1

**Description:**
Spotlight (Editorial). T2.99 covers Ch2 pull-quote. Add 2 more in Ch3 (neighborhood) and Ch5 (labyrinth) — each from publicly-published reentry research or, if no source available, marked "composite — illustrative" per T2.99 contract. Each rendered with `EditorialQuote` (T2.103).

**AC:**
- [ ] Ch3 pull-quote committed with EN + ES + source attribution
- [ ] Ch5 pull-quote committed with EN + ES + source attribution
- [ ] Both rendered via `EditorialQuote` component
- [ ] Both source URLs documented in `legalReferences.ts`
- [ ] If composite, marked clearly in PR + on rendered output
- [ ] Vitest: quotes rendered at correct chapter scroll positions
- [ ] `bpsai-pair arch check` passes

**Depends on:** T2.99, T2.103, T2.51, T2.53

---

### T2.139 --- W2 enrichment dry-run validation gate | Cx: 4 | P0

**Description:**
Final gate. After all enrichment tasks (T2.68–T2.138) ship, run `bpsai-pair plan validate` and `bpsai-pair task list --plan w2 --verify-edges`. Verify the DAG has no cycles (each enrichment task's `Depends on` resolves), the enrichment Cx total stays within the original W2 1000-Cx ceiling (current ~860 + enrichment ~440 = ~1300 — flagged as a known overage; document the descope plan if needed).

**AC:**
- [ ] `bpsai-pair plan validate` returns 0
- [ ] `bpsai-pair task list --plan w2 --verify-edges` returns 0 (no broken dependencies)
- [ ] Total Cx documented (original 816 + enrichment ≈ 460–500 ≈ 1280)
- [ ] If over 1000, descope plan documented in PR (which P2 tasks can move to W4)
- [ ] No code changes (validation-only)

**Depends on:** all prior W2 tasks (T2.1–T2.138)

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
