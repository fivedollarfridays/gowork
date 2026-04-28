# Sprint W3 — Interactive Chapters 6-10 + 3D Graph + View Transitions

**Plan type:** feature
**Sprint:** W3 (third of five "Visual Rebirth" sprints; HackFW 2026 submission)
**Total Cx:** 811
**Tasks:** 70 active (P0: 56, P1: 13, P2: 1)
**Branch:** `sprint/visual-rebirth`
**Deadline anchor:** May 2, 2026, 2:00 PM CDT

## Goal

Build Chapters 6 through 10 of "The Wall" -- the **interactive heart** of the GoWork HackFW submission. By the end of W3, scrolling past Chapter 5 (W2's labyrinth) lands the user at Amazon FC DFW5 where dragging a wage slider pushes them into the benefits cliff, watches Carlos walk a real GPS path from his ZIP 76119 home through DPS, HHSC, Legal Aid, Workforce Solutions, to Amazon FC over weeks 1-12, sees a 3D barrier-graph constellation breathe over Fort Worth as edges illuminate when Carlos resolves them below, watches a 3-second cross-country fly to Montgomery proving the multi-city framework, and ends in a View-Transitions-API-driven morph from the map into `/assess`. This is the moment judges screenshot.

**Prerequisite:** W2 merged. Required deliverables from W2 in place: `WallContainer.tsx`, `MapboxScene.tsx`, `ChapterScaffold.tsx`, `lib/wall/cameraChoreography.ts`, `lib/wall/paths.ts` (Carlos GPS coords), `lib/wall/sound.ts`, `lib/wall/layers/{trinityMetro,offices}.ts`, Chapters 1-5, EN/ES scaffolding.

## What ships in W3 vs deferred

**W3 (this sprint):** 5 new chapter components (Ch6-Ch10), Carlos avatar walking component, 3D barrier-graph constellation (react-three-fiber, lazy-loaded), fly-to-Montgomery cross-country camera flight, View-Transitions-API morph to `/assess` with feature-detect fallback, EN/ES editorial copy for all 5 chapters, accessibility pass per chapter, lazy-loading + bundle-budget verification, vitest + Playwright integration tests, cross-chapter Carlos integration polish.

**Deferred to W4:** time-of-day Mapbox sky lighting, cursor flashlight wired across all chapters (W3 only ensures hooks compose), Spanish narrative *audio*, variable-font axis on hero, per-chapter dynamic OG via Vercel Satori, Live Now widget UI, final Lighthouse 90+ measurement (W4 hard gate).

## Architectural principles

- **Zero LLM calls in the Wall render path.** Three.js, framer-motion, Mapbox only. Deterministic visualization.
- **Lazy by default.** Three.js bundle (~150 KB) mounts ONLY when Ch8 enters viewport, unmounts on exit. Cliff component imported, never duplicated.
- **Feature-detect everything new.** View Transitions API has uneven Safari support; fall back to standard navigation gracefully.
- **Reduced-motion respect at every animation site.** Camera flights -> instant cuts. Carlos avatar -> static at 50% path. 3D graph -> still image of constellation.
- **User agency preserved.** Manual Mapbox drag must not be trapped by scroll-driven camera. Tab-blur pauses animations.
- **Carlos data is real.** GPS path uses real Fort Worth coordinates per `docs/demo-script.md` (representative block pin -- never the exact address). Barrier graph uses the existing 33-node, 53-edge DAG from `data/barrier_graph_seed.json`.
- **GoWork brand only.** No "MontGoWork" leakage. Slogan locked.

## Decisions locked

1. **Cliff component:** IMPORT existing `frontend/src/components/plan/BenefitsCliffSimulator.tsx` (slider-driven) for Ch6. Do NOT recreate. Wage slider drives `--temperature-multiplier` CSS variable scoped to the chapter.
2. **Carlos avatar:** Slightly more sophisticated than a plain silhouette -- a 2-frame walk-cycle SVG (left-stride / right-stride alternating) tied to scroll velocity. Falls back to a static silhouette under reduced motion. (Spotlight invention: brief said silhouette only; this lands harder for ~20 Cx more.)
3. **3D graph data source:** Build-time JSON import of `data/barrier_graph_seed.json` (already 33 nodes / 53 edges). NO new backend endpoint in W3.
4. **3D layout:** Force-directed via simple manual physics (lightweight) -- avoid pulling d3-force unless physics quality demands it.
5. **Montgomery Mapbox style:** Reuse W2 dark style; differentiate via accent color shift + label changes only. Defer separate style document to W5.
6. **View Transitions fallback:** When `document.startViewTransition` is undefined, perform a 280 ms framer-motion crossfade from map to `/assess` form before navigation. Never a hard cut on supporting browsers, never a hang on unsupported.
7. **Mobile mode** for Ch7 / Ch8 / Ch10: detected via `window.innerWidth < 768`; renders static path image + still constellation + standard navigation. Never broken.
8. **Tab-blur:** When `document.visibilityState === "hidden"`, pause Three.js render loop and Mapbox animations. Resume on return.

---

## Cross-sprint dependency graph

```
W2 (Mapbox engine + Chapters 1-5)
  |-- lib/wall/cameraChoreography.ts (per-chapter state) <- W3 extends with Ch6-Ch10
  |-- lib/wall/paths.ts (Carlos GPS coords) <- W3 Ch7 consumes
  |-- lib/wall/sound.ts (Howler scaffold) <- W3 Ch6/Ch7 emit
  |-- ChapterScaffold.tsx (sticky scroll) <- W3 Ch6-Ch10 consume
  |-- WallContainer.tsx <- W3 wires Ch6-Ch10
  +-- MapboxScene.tsx <- W3 adds 3D layer hook for Ch8

W3 outputs blocked-by NONE within sprint.
W3 outputs block W4 (life-layers polish), W5 (submission).
```

## File collision matrix (within W3)

| File | Tasks touching it | Resolution |
|---|---|---|
| `frontend/src/app/page.tsx` (or `WallContainer.tsx`) | T3.1, T3.7, T3.15, T3.23, T3.29 (chapter wiring) | Single wiring task per chapter, serialized at end of each chapter phase |
| `lib/wall/cameraChoreography.ts` | T3.2, T3.8, T3.16, T3.24, T3.30 (per-chapter state) | Each chapter task adds its OWN exported const; no shared edits |
| `lib/wall/paths.ts` | T3.9 (extend Carlos coordinates if W2 left placeholder) | Single task; Ch7 only consumer |
| `lib/wall/sound.ts` | T3.6, T3.13 (cliff clicks, footsteps) | Each task adds named sound id; no overwrite |
| `lib/translations/en.json` + `lib/translations/es.json` | T3.36-T3.40 (5 chapters of copy) | One task per chapter pair; merge-friendly keys `wall.ch6.*` etc. |
| `BenefitsCliffSimulator.tsx` | T3.4 only (import; do NOT modify) | Read-only consumer |
| `ViewTransitionsProvider.tsx` | T3.32 (extend with feature-detect + map-to-form orchestration) | Single rewrite task with backward-compat behavior preserved |
| `package.json` | T3.20 (d3-force install if needed) | Single optional install task |

## Cross-task contract edges (within W3)

- **T3.5** (cliff slider -> temperature multiplier) writes `--temperature-multiplier` CSS var; **T3.34** (cursor flashlight cross-chapter) reads it and adjusts glow intensity. Compound effect documented as Spotlight #2.
- **T3.10** (Carlos avatar position) interpolates between waypoints from `lib/wall/paths.ts`; **T3.51** (cross-chapter integration) re-uses same waypoints in Ch8 to time edge illumination.
- **T3.18** (3D Three.js Canvas) -> mount/unmount lifecycle wired to **T3.45** (lazy-load) and **T3.55** (tab-blur pause).
- **T3.32** (View Transitions provider) -> consumed by **T3.31** (Ch10 CTA click handler) AND existing `/assess` route.

---

### Phase 1: Chapter 6 -- THE MATH (Cliff Calculator Embed)

### T3.1 — Chapter06TheMath component scaffold | Cx: 14 | P0

**Description:**
Create `frontend/src/components/wall/chapters/Chapter06TheMath.tsx` using the W2 `ChapterScaffold`. Define the chapter container, sticky atmosphere wrapper, scroll-progress consumer, and the editorial overlay slot. Pull the locked copy keys (`wall.ch6.headline`, `wall.ch6.body`) via `useTranslation`. Wire the chapter into `WallContainer.tsx` at index 6 (after W2's Ch5 Labyrinth). Mount the cliff overlay slot but leave the actual `BenefitsCliffSimulator` import for T3.4. Locked editorial copy: `"A $2 raise that costs $400 isn't a raise. We do this math for every job."`

**AC:**
- [ ] `frontend/src/components/wall/chapters/Chapter06TheMath.tsx` exists, single default export, < 80 lines
- [ ] Wired into `WallContainer.tsx` as the sixth chapter (after `Chapter05Labyrinth`)
- [ ] Renders editorial headline + body via `useTranslation` (keys `wall.ch6.headline`, `wall.ch6.body`)
- [ ] `ChapterScaffold` handles sticky scroll; chapter occupies a ~150 vh scroll segment
- [ ] Vitest test: chapter renders with EN copy AND ES copy via locale switch
- [ ] `bpsai-pair arch check frontend/src/components/wall/chapters/Chapter06TheMath.tsx` passes
- [ ] Reviewer agent approves

**Depends on:** W2 (ChapterScaffold, WallContainer, useTranslation hook); none within W3

---

### T3.2 — Camera choreography for Ch6 (fly to Amazon FC DFW5) | Cx: 13 | P0

**Description:**
Extend `frontend/src/lib/wall/cameraChoreography.ts` with `chapter06Camera`: zoom 14, pitch 55, bearing 35°, centered on real Amazon FC DFW5 coordinates `[-97.0316, 32.7268]` (Alliance area, Fort Worth). Camera flies in over 1.6 s using cubic-bezier `(0.32, 0.72, 0, 1)`. Reduced-motion fallback: instant set without animation. Cancellable on user pan/zoom (Mapbox interaction emits `interactionstart` -> camera resolves).

**AC:**
- [ ] `chapter06Camera` constant exported from `lib/wall/cameraChoreography.ts`
- [ ] DFW5 coordinates documented inline citing `cities/fort-worth.yaml` employer marker
- [ ] flyTo invokes only when chapter enters viewport (>= 25% scroll progress)
- [ ] Reduced-motion: `jumpTo` instead of `flyTo` (verified by mocked `prefers-reduced-motion`)
- [ ] User-initiated pan/zoom cancels remaining animation
- [ ] Vitest test: camera state at scroll 0.0, 0.5, 1.0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.1

---

### T3.3 — Trinity Metro Bus 4 highlight to DFW5 | Cx: 12 | P0

**Description:**
When Ch6 active, raise opacity of Trinity Metro Bus 4 line (already a layer from W2's `lib/wall/layers/trinityMetro.ts`) to 1.0 and add a labeled "71-min commute" overlay anchored to the line midpoint. All other Trinity routes dim to opacity 0.2. On chapter exit, restore default opacities.

**AC:**
- [ ] Bus 4 line styled with `--accent-cyan` at full opacity; other routes dimmed
- [ ] Anchored "71-min commute" label renders at line midpoint via Mapbox `Marker`
- [ ] Distance label hides on Ch5 exit and Ch7 entry (transition handled by chapter scaffold)
- [ ] No hardcoded hex; uses tokens from W1
- [ ] Vitest test: layer opacity transitions verified via mock `setPaintProperty`
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.1, T3.2

---

### T3.4 — Embed BenefitsCliffSimulator overlay (no duplication) | Cx: 18 | P0

**Description:**
Import existing `frontend/src/components/plan/BenefitsCliffSimulator.tsx` (slider-driven; do NOT modify or recreate). Create `frontend/src/components/wall/CliffOverlay.tsx` that wraps the Simulator in a glass-card overlay positioned bottom-center of the Ch6 viewport. The overlay must accept a `CliffAnalysis` prop (typed via `@/lib/types`). For Ch6 we provide a static fixture (`frontend/src/lib/wall/fixtures/cliffAnalysisCarlos.ts`) shaped like the worker page response so the simulator behaves identically. Overlay only mounts during Ch6 (lazy via React.lazy + Suspense fallback to skeleton).

**AC:**
- [ ] `CliffOverlay.tsx` exists, < 80 lines, wraps imported `BenefitsCliffSimulator`
- [ ] `BenefitsCliffSimulator.tsx` is NOT modified (verified via git diff)
- [ ] Static fixture `fixtures/cliffAnalysisCarlos.ts` shape-matches `CliffAnalysis` type
- [ ] React.lazy + Suspense skeleton (loading state designed, not blank) -- < 50 lines
- [ ] Bundle-split verified: cliff overlay chunk loads only on Ch6 entry (network tab inspection in test)
- [ ] Vitest test: cliff renders with fixture, slider drag fires `onChange`, fixture matches simulator API
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.1

---

### T3.5 — Wage slider drives --temperature-multiplier | Cx: 22 | P0

**Description:**
Hook the `BenefitsCliffSimulator`'s wage value (currently internal `useState`) by intercepting via a controlled-prop wrapper or by listening to slider events. As wage drags into a cliff zone (any wage where `cliff_points` includes that wage), update the Ch6 chapter root CSS variable `--temperature-multiplier` from 1.0 toward 1.6 over the cliff range. The accent color shift from `--accent-amber` to `--accent-rose` is handled by W1's color-mix tokens responding to the multiplier. Tracking should be debounced (16 ms / one rAF) and cleaned up on Ch6 exit.

**AC:**
- [ ] `--temperature-multiplier` CSS variable updates from slider drag (verified via DOM `getComputedStyle`)
- [ ] At a non-cliff wage, multiplier = 1.0; at a cliff wage, multiplier = 1.6
- [ ] Debounced to ~60 fps; no jank in scroll handler
- [ ] On Ch6 exit, multiplier resets to 1.0 globally
- [ ] Reduced-motion: temperature multiplier still updates (it's a color shift, not motion); but transitions are instant rather than animated
- [ ] Vitest test: simulate slider drag, assert variable value at each step
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.4

---

### T3.6 — Calculator-click sound on slider drag | Cx: 8 | P1

**Description:**
Register `cliff-click` in `lib/wall/sound.ts` (Howler singleton from W1). Fire one click per slider step (rate-limited to max 1 per 80 ms). Asset: `frontend/public/sounds/calculator-click.mp3` (single-shot, < 6 KB). Mute toggle from W1 must suppress. Audio context unlocks on first user gesture (already handled in W1 sound scaffold).

**AC:**
- [ ] `frontend/public/sounds/calculator-click.mp3` committed, < 8 KB
- [ ] `cliff-click` registered in `lib/wall/sound.ts` sound map
- [ ] Slider drag fires sound max 1x per 80 ms
- [ ] Mute toggle (W1) suppresses sound
- [ ] Vitest test: drag emits N <= scroll_steps / 80 ms calls
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.5

---

### Phase 2: Chapter 7 -- THE PATH + Carlos Avatar

### T3.7 — Chapter07ThePath component scaffold | Cx: 14 | P0

**Description:**
Create `frontend/src/components/wall/chapters/Chapter07ThePath.tsx` consuming `ChapterScaffold`. Camera state from T3.8. Editorial copy: `"Every barrier connects. We find the order."` Layout: full-bleed map with bottom timeline rail (Week 1 / Week 4 / Week 8 / Week 10 / Week 12). Wire into `WallContainer.tsx` after Ch6.

**AC:**
- [ ] `Chapter07ThePath.tsx` exists, < 100 lines
- [ ] Wired in `WallContainer` as 7th chapter
- [ ] Editorial overlay renders EN + ES via `wall.ch7.*` keys
- [ ] Bottom timeline rail renders 5 waypoint labels with week numbers
- [ ] Mobile (`< 768 px`): timeline collapses to vertical list (still functional)
- [ ] Vitest test: renders 5 timeline labels in EN and ES
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.6

---

### T3.8 — Camera choreography for Ch7 (neighborhood altitude follow) | Cx: 13 | P0

**Description:**
Add `chapter07Camera` to `cameraChoreography.ts`. Mid-altitude pull (zoom 13.5, pitch 50, bearing follows path direction). Camera target interpolates ALONG Carlos's path as scroll progresses through Ch7 (i.e., camera rides the avatar). Reduced-motion: snap to fully-zoomed-out state showing all 5 waypoints, no follow.

**AC:**
- [ ] `chapter07Camera` exported with `target` as a function `(scrollProgress: number) => [lng, lat]`
- [ ] Bearing rotates to match path tangent at current segment
- [ ] Reduced-motion: camera locks at zoomed-out state (all 5 markers in frame)
- [ ] Vitest test: target function returns interpolated coord at progress 0.0, 0.4, 0.8, 1.0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.7

---

### T3.9 — Carlos GPS path data: 5 real Fort Worth waypoints | Cx: 12 | P0

**Description:**
Extend `frontend/src/lib/wall/paths.ts` (created in W2) with `carlosWaypoints` constant: 5 real Fort Worth office coordinates with metadata. (1) Tarrant County DPS Driver License Office (`[-97.3208, 32.7555]`, Week 1, "Article 55 expunction filed"); (2) HHSC Eligibility Office on Hemphill (`[-97.3267, 32.6890]`, Week 4, "Childcare subsidy intake"); (3) Legal Aid of NorthWest Texas (`[-97.3278, 32.7560]`, Week 8, "Record cleared"); (4) Workforce Solutions for Tarrant County (E. Belknap branch) (`[-97.3010, 32.7820]`, Week 10, "Skills assessment"); (5) Amazon FC DFW5 (`[-97.0316, 32.7268]`, Week 12, "JOB"). Plus `carlosHome` representative-block coord at `[-97.2660, 32.7050]` (76119 vicinity, NOT exact address). Each waypoint typed (`type CarlosWaypoint = { coord: [number, number]; week: number; label_en: string; label_es: string }`). Validate every coord is within Fort Worth bounding box.

**AC:**
- [ ] `carlosWaypoints` (length 5) + `carlosHome` exported from `lib/wall/paths.ts`
- [ ] Each waypoint has `coord`, `week`, `label_en`, `label_es`, `agency_name`
- [ ] All coordinates inside Fort Worth bounding box ([-97.55, -97.0] x [32.55, 32.95])
- [ ] `carlosHome` is a representative block, NOT Carlos's exact ZIP-76119 address (verified via comment + test asserting it's not in `docs/demo-script.md` PII)
- [ ] Vitest test: shape, count, bounding-box validity
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.7

---

### T3.10 — CarlosAvatar walking SVG component (2-frame walk cycle) | Cx: 24 | P0

**Description:**
Create `frontend/src/components/wall/CarlosAvatar.tsx`. SVG silhouette figure (head, torso, two-leg-stride alternating). Two static frames `<g id="stride-left">` and `<g id="stride-right">` toggled by `useScrollVelocity` from W1 (frame-swap interval = clamp(60, 600 / velocity, 240) ms). Position interpolates from start to end of CURRENT path segment based on chapter scroll progress. Pauses ~200 ms at each of the 5 waypoints. Uses framer-motion's `motionValue` for smooth interpolation. Reduced-motion: single static frame at 50 % path progress, no walk-cycle, no waypoint pauses (just shown).

**AC:**
- [ ] `CarlosAvatar.tsx` exists, < 120 lines, single component export
- [ ] SVG legible at 24 px (test by rendering at 24 / 48 / 96 px)
- [ ] Walk-cycle frame swap rate = clamp(60, 600 / velocity, 240) ms
- [ ] Position updates via `motionValue` along segment from `paths.ts`
- [ ] Pauses 200 ms at each waypoint (verified via fake-timer test)
- [ ] Reduced-motion: single static frame at progress 0.5, no animation
- [ ] axe-core: avatar has `role="img"` + `aria-label` describing position ("Carlos walking, Week 4 of 12")
- [ ] Vitest tests: position interpolation, pause timing, reduced-motion fallback, walk-cycle rate
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.9, W1 (`useScrollVelocity` hook)

---

### T3.11 — Sequential path-draw between 5 waypoints | Cx: 15 | P0

**Description:**
Inside `Chapter07ThePath`, draw a Mapbox `LineLayer` between consecutive waypoints. The line draws PROGRESSIVELY as scroll advances: at progress 0.0 -- only segment 1 (home -> DPS) drawn; at 0.2 -- through segment 2 (DPS -> HHSC); etc. Style: amber-to-cyan gradient (warm to cool) following the waypoints, 4 px wide, glow filter. Reduced-motion: draw all segments at once, no progressive reveal.

**AC:**
- [ ] Path line renders with progressive drawing tied to scroll progress
- [ ] Gradient transitions from `--accent-amber` (start) to `--accent-cyan` (end)
- [ ] Reduced-motion: full path drawn instantly
- [ ] Cleanup: line removed from Mapbox on Ch7 exit
- [ ] Vitest test: at progress 0.0/0.5/1.0, expected number of segments rendered
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.9

---

### T3.12 — Trinity Metro highlight per leg | Cx: 11 | P1

**Description:**
For each of Carlos's 4 inter-waypoint segments, identify the realistic Trinity Metro route used (or "walk" / "TEXRail" if no direct bus). Mapping committed in `lib/wall/carlosTransitMap.ts`. As Carlos's avatar enters segment N, raise opacity of route N-relevant Trinity layer; dim others. Ch6 already highlights Bus 4; Ch7 highlights cycle through Bus 7 / Bus 12 / Bus 4 / TEXRail-Alliance per the segment.

**AC:**
- [ ] `carlosTransitMap.ts` exports `[segmentIndex] -> trinityRouteId` (length 4)
- [ ] As avatar enters segment, that route raises to opacity 1.0; others dim to 0.2
- [ ] On Ch7 exit, all routes restore to default opacity
- [ ] Vitest test: at avatar progress 0.1 / 0.4 / 0.7, the active route id matches expected
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10

---

### T3.13 — Footstep audio tied to scroll velocity | Cx: 10 | P0

**Description:**
Register `footstep` in `lib/wall/sound.ts`. While Ch7 is active and avatar is between waypoints, fire footstep at rate-limited 1 per 200 ms (only when scroll velocity > 0). Asset: `frontend/public/sounds/footstep.mp3` (< 6 KB). Velocity threshold 5 px / frame. Mute toggle suppresses. Reduced-motion: NO footsteps (avatar is static). Tab-blur (T3.55): pause.

**AC:**
- [ ] `footstep` registered in `lib/wall/sound.ts`
- [ ] Asset committed, < 8 KB
- [ ] Fires max 1 per 200 ms while scrolling Ch7
- [ ] Pauses at waypoints (no scroll velocity = no footsteps)
- [ ] Mute toggle suppresses
- [ ] Reduced-motion: zero footsteps fired
- [ ] Vitest tests: rate-limit, mute, reduced-motion all verified
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10, T3.55

---

### T3.14 — Ch7 timeline rail with week markers + EN/ES labels | Cx: 12 | P0

**Description:**
Below the chapter, render a horizontal timeline rail (sticky, fixed-bottom) showing Weeks 1, 4, 8, 10, 12 as nodes connected by a progress line. The active waypoint highlights as Carlos's avatar reaches it. Each node has a tooltip on hover/focus describing the milestone (`carlosWaypoints[i].label_en` or `_es`). Mobile: collapse to vertical list with current step highlighted. Keyboard: tab through nodes, Enter triggers a viewport-wide flash of that waypoint marker on the map.

**AC:**
- [ ] Timeline rail renders 5 nodes with week numbers
- [ ] Active node highlighted as avatar progresses
- [ ] Tooltips display EN or ES label per locale
- [ ] Mobile (< 768 px): vertical list, no horizontal overflow
- [ ] Keyboard: full tab navigation; Enter triggers map flash
- [ ] axe-core: zero violations on rail
- [ ] Vitest test: active node correct at progress 0.2 / 0.5 / 0.9
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.7, T3.9

---

### Phase 3: Chapter 8 -- THE 3D BARRIER GRAPH (Lazy-loaded)

### T3.15 — Chapter08TheGraph component scaffold (lazy entry) | Cx: 14 | P0

**Description:**
Create `frontend/src/components/wall/chapters/Chapter08TheGraph.tsx`. Exports a `React.lazy()` wrapper around the constellation Canvas component (T3.18) so the Three.js bundle only loads when Ch8 enters viewport. Suspense fallback: a static SVG placeholder of the constellation (geometry approximation, < 8 KB). Editorial copy: `"33 barriers. 53 connections. We model how each unblocks the next."` Wired in `WallContainer`.

**AC:**
- [ ] `Chapter08TheGraph.tsx` < 80 lines, default export lazy-loads the Canvas
- [ ] Suspense fallback is a static SVG that visually matches the eventual constellation layout
- [ ] Three.js chunk verified to be code-split (vite/next bundle analysis stat in test)
- [ ] Wired in `WallContainer` as 8th chapter
- [ ] Editorial copy renders EN + ES
- [ ] Vitest test: chapter renders fallback while Canvas mock is suspended
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.14

---

### T3.16 — Camera choreography for Ch8 (tilt up to reveal constellation) | Cx: 9 | P0

**Description:**
Add `chapter08Camera` to `cameraChoreography.ts`. Ch7 ended at neighborhood altitude looking down; Ch8 tilts the Mapbox pitch UP toward the sky (pitch 75, zoom 12, bearing 0) so the constellation overlay sits in the upper half of the viewport with city street grid in the lower half. Reduced-motion: instant set. Cancellable on user interaction.

**AC:**
- [ ] `chapter08Camera` exported (zoom 12, pitch 75, bearing 0)
- [ ] flyTo over 1.4 s with cubic-bezier easing
- [ ] Reduced-motion: jumpTo
- [ ] Vitest test: camera state at scroll 0.0 / 0.5 / 1.0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.15

---

### T3.17 — Build-time barrier graph data import + node typing | Cx: 12 | P0

**Description:**
Create `frontend/src/lib/wall/barrierGraph.ts`. Read-once at build time: import `data/barrier_graph_seed.json` (33 barriers, 53 relationships) and transform into a frontend-friendly `BarrierGraphData` shape with `nodes: Array<{ id, name, category, position3d }>` and `edges: Array<{ source, target, type, weight }>`. Generate initial 3D positions deterministically (seeded random sphere placement) so layout is stable across renders. NO new backend endpoint -- pure import.

**AC:**
- [ ] `lib/wall/barrierGraph.ts` exports `barrierGraphData` (33 nodes, 53 edges)
- [ ] Each node has `position3d: [x, y, z]` deterministically generated
- [ ] Re-running build produces identical positions (seeded PRNG, verified by snapshot)
- [ ] NO network call; pure JSON import (verified -- file imports `data/barrier_graph_seed.json`)
- [ ] Vitest test: 33 / 53 counts, deterministic positions, snapshot stable
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.15

---

### T3.18 — BarrierConstellation Three.js Canvas component | Cx: 32 | P0

**Description:**
Create `frontend/src/components/wall/BarrierConstellation.tsx`. `<Canvas>` from `@react-three/fiber` (installed W1). Renders 33 nodes as `<Sphere>` meshes with `--accent-cyan` material; 53 edges as `<Line>` between connected nodes. Camera fixed perspective at distance 8. Lighting: one ambient + one cool directional. Constellation "breathes" via subtle orbital drift (rotation `0.0005 rad/frame` on Y axis, sinusoidal Z translation `+/- 0.05`). On Ch8 entry only -- unmounts on exit (T3.45 wiring). DOM keyboard alt: nav-list sibling describing nodes; details in T3.42.

**AC:**
- [ ] `BarrierConstellation.tsx` < 150 lines (warning over 200 acceptable for Three.js component if functions remain < 50)
- [ ] 33 Sphere meshes + 53 Line objects render at 60 fps on mid-tier laptop (verified manually + perf budget test)
- [ ] Orbital drift: Y rotation + sinusoidal Z, rate 0.0005 rad/frame
- [ ] Material uses `--accent-cyan` token (read via `getComputedStyle` once at mount)
- [ ] Cleanup: `dispose()` on unmount frees geometry + material (verified via reference count or a no-leak test using react-test-renderer)
- [ ] Vitest test: renders fixture data, mock Three.js scene, asserts 33 + 53 counts
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.17

---

### T3.19 — Edge illumination tied to Carlos's path completion | Cx: 18 | P0

**Description:**
Wire Ch7's avatar progress to Ch8's edge highlight state. Map: as Carlos resolves barrier-of-segment-N (e.g., "criminal record" -> Week 8), edges in the constellation that touch that barrier illuminate (material color shifts from cyan dim to amber bright over 600 ms; line width doubles). Mapping `lib/wall/carlosBarrierResolutionMap.ts`: `Map<carlosWeek, barrierIds[]>`. Cross-chapter integration: even though Ch7 has scrolled past, the user's MAX progress through Ch7 is preserved in a session ref; entering Ch8 displays the resolved state. (Spotlight: this is the cross-chapter compound moment.)

**AC:**
- [ ] `carlosBarrierResolutionMap.ts` exports map: weeks 1, 4, 8, 10, 12 -> barrier IDs
- [ ] Edges illuminated based on max-Ch7-progress observed
- [ ] Edge color transitions over 600 ms (cyan dim -> amber bright)
- [ ] On Ch8 exit, edges retain illuminated state (don't reset; cumulative)
- [ ] Vitest test: at progress = week 4, expected edges illuminated; at week 12, all relevant edges illuminated
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18, T3.10

---

### T3.20 — d3-force install decision + force-directed layout pass | Cx: 14 | P1

**Description:**
T3.17 generates initial positions deterministically via seeded random sphere placement. Evaluate visual quality. If clusters look noisy (subjective: visually overlapping nodes, > 4 line crossings in central area), install `d3-force` (small dependency, ~12 KB) and run a 300-iteration force-directed pass at build time to refine positions. Commit either decision in `docs/adr/w3-barrier-graph-layout.md`.

**AC:**
- [ ] Visual review documented in `docs/adr/w3-barrier-graph-layout.md` with screenshots before / after
- [ ] If d3-force installed: pinned version in `package.json`, < 12 KB bundle delta
- [ ] If d3-force NOT installed: ADR documents that seeded sphere is sufficient
- [ ] Final positions remain deterministic (seeded)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.21 — Reduced-motion fallback: still-image constellation | Cx: 12 | P0

**Description:**
When `prefers-reduced-motion: reduce`, replace the `<Canvas>` with a static SVG image of the constellation (rendered offline at build time using the same `barrierGraphData`, written to `public/wall/constellation-still.svg`). The build step is a small Node script `scripts/render-constellation-still.mjs`. The SVG is loaded directly when reduced-motion detected, NO Three.js bundle download.

**AC:**
- [ ] `scripts/render-constellation-still.mjs` generates `public/wall/constellation-still.svg` from `barrierGraphData`
- [ ] When `prefers-reduced-motion: reduce`, Ch8 renders the SVG instead of `<Canvas>`
- [ ] Three.js chunk NOT loaded under reduced-motion (verified via mocked `matchMedia` + bundle inspection)
- [ ] SVG is < 16 KB
- [ ] axe-core: SVG has `role="img"` + `aria-label` listing barrier categories
- [ ] Vitest test: under mock reduced-motion, only SVG renders; Canvas does not mount
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.22 — Edge illumination chime audio | Cx: 8 | P2

**Description:**
Register `edge-chime` in `lib/wall/sound.ts`. Soft chime (120 ms, < 6 KB) fires once per edge as it illuminates (with rate limit: max 3 per second to avoid cacophony when many edges illuminate simultaneously). Mute toggle respected. Reduced-motion: zero chimes.

**AC:**
- [ ] `edge-chime.mp3` committed, < 8 KB
- [ ] Fires max 3 / s
- [ ] Mute respected
- [ ] Reduced-motion: zero
- [ ] Vitest tests as for T3.6 / T3.13
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.19

---

### Phase 4: Chapter 9 -- ANY CITY + Fly-to-Montgomery

### T3.23 — Chapter09AnyCity component scaffold | Cx: 12 | P0

**Description:**
Create `frontend/src/components/wall/chapters/Chapter09AnyCity.tsx`. Camera pulls back to continental US. Two cities lit (Fort Worth + Montgomery), 6 dotted (Dallas, Houston, Atlanta, Memphis, Charlotte, Birmingham). Editorial copy: `"5,189 tests. 13 sprints. 2 cities deployed. MIT licensed."` Stat band shows test count from `package.json` build-time variable, NOT hardcoded. Includes "Fly to Montgomery" button (T3.25) and "Return to Fort Worth" button (T3.27).

**AC:**
- [ ] `Chapter09AnyCity.tsx` < 100 lines
- [ ] Renders editorial copy + stat band (5,189 tests, 13 sprints, 2 cities, MIT)
- [ ] Test count read at build time, not hardcoded (verified by mocking the constant)
- [ ] Wired in `WallContainer` as 9th chapter
- [ ] axe-core: zero violations
- [ ] Vitest test: stats render, two buttons present
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.22

---

### T3.24 — Camera choreography for Ch9 (continental zoom out) | Cx: 9 | P0

**Description:**
Add `chapter09Camera` to `cameraChoreography.ts`. Pull camera to continental view (zoom 4, pitch 0, bearing 0, center on US geographic center `[-97.0, 38.0]`). Smooth transition over 1.8 s. Reduced-motion: jumpTo.

**AC:**
- [ ] `chapter09Camera` exported (zoom 4, pitch 0, bearing 0)
- [ ] flyTo with cubic-bezier easing, 1.8 s
- [ ] Reduced-motion: jumpTo
- [ ] Vitest test: camera state at start / mid / end
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.23

---

### T3.25 — Cross-country fly-to-Montgomery animation (3-second) | Cx: 18 | P0

**Description:**
"Fly to Montgomery" button click triggers a Mapbox `flyTo` with `speed: 0.8, curve: 1.42, essential: true` to Montgomery, AL coordinates `[-86.3000, 32.3617]` (from `cities/montgomery.yaml`). Duration ~3000 ms. During animation, status string shows "Flying to Montgomery..." in `aria-live="polite"`. Cancellable via Esc key (returns to Fort Worth). Button is disabled while flight in progress. Reduced-motion: instant `jumpTo` to Montgomery, no animation; status announces arrival immediately.

**AC:**
- [ ] Button click triggers 3 s flyTo to Montgomery coords
- [ ] `aria-live` announces flight start + arrival
- [ ] Esc key cancels and returns to Fort Worth
- [ ] Button disabled during flight, re-enabled on land
- [ ] Reduced-motion: jumpTo, no animation, immediate aria announcement
- [ ] Vitest test: flight initiates, completes, cancellable
- [ ] axe-core: zero violations
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.23

---

### T3.26 — Montgomery accent + label switch | Cx: 10 | P0

**Description:**
On arrival in Montgomery, swap accent color from Fort-Worth-amber to Montgomery-tone (a slightly warmer amber, defined as new W4 token `--accent-montgomery: oklch(70% 0.15 70)`; until W4 lands, define inline). Mapbox street labels visibility toggles to highlight Montgomery street names. The W2 dark Mapbox style is reused; differentiation is purely accent + label, NOT a separate style document.

**AC:**
- [ ] `--accent-montgomery` token defined (in W4 partials directory if exists; else inline at chapter)
- [ ] Accent shifts when map center is within Montgomery bounding box
- [ ] Labels emphasize Montgomery streets (verified via Mapbox layer state)
- [ ] On return-to-FW, accent reverts to amber
- [ ] Vitest test: at FW center accent = amber; at Montgomery center = montgomery-tone
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.25

---

### T3.27 — Return-to-Fort-Worth button | Cx: 9 | P0

**Description:**
Visible only after Montgomery arrival. Click reverses the 3-second flyTo back to Fort Worth. Same accessibility behavior as T3.25 (aria-live, Esc cancels and stops in place, disabled during flight, reduced-motion: jumpTo).

**AC:**
- [ ] Button visible only post-Montgomery-arrival
- [ ] Click triggers 3 s flyTo back to FW
- [ ] aria-live + esc cancel + disabled-during-flight + reduced-motion = jumpTo (mirror T3.25)
- [ ] Vitest test: button visibility lifecycle, flight back, cancel
- [ ] axe-core: zero violations
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.25

---

### T3.28 — 6 dotted future-city pins | Cx: 10 | P1

**Description:**
Render 6 small dotted markers at Dallas, Houston, Atlanta, Memphis, Charlotte, Birmingham. Each pin is a 12 px dotted circle in `--fg-muted`. Hover/focus reveals city name + "Coming soon" tooltip. Pure visual (no flight click target -- only Montgomery is clickable in W3). On Ch9 exit, markers fade out.

**AC:**
- [ ] 6 dotted markers render at correct lat/lng (committed in `lib/wall/futureCities.ts`)
- [ ] Tooltip on hover/focus (keyboard reachable via Tab)
- [ ] Markers fade out on Ch9 exit
- [ ] axe-core: tooltip has correct ARIA semantics
- [ ] Vitest test: 6 markers render, tooltips reachable via keyboard
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.23

---

### Phase 5: Chapter 10 -- FIND YOUR PATH + View Transitions

### T3.29 — Chapter10FindYourPath component scaffold | Cx: 12 | P0

**Description:**
Create `frontend/src/components/wall/chapters/Chapter10FindYourPath.tsx`. Camera back to Fort Worth overhead (uses `chapter10Camera` from T3.30). Single primary CTA `"Start your assessment"` -> triggers View Transitions handoff (T3.31). Secondary link `"Or read the open-source code on GitHub ->"`. Editorial closing copy: `"What's standing between you and a job? You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan."` (locked thesis).

**AC:**
- [ ] `Chapter10FindYourPath.tsx` < 100 lines
- [ ] Wired in `WallContainer` as 10th chapter
- [ ] Renders locked thesis copy in EN + ES
- [ ] Two CTAs: primary assessment, secondary GitHub
- [ ] axe-core: zero violations
- [ ] Vitest test: thesis copy verbatim, both CTAs reachable
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.28

---

### T3.30 — Camera choreography for Ch10 (Fort Worth overhead) | Cx: 8 | P0

**Description:**
Add `chapter10Camera` to `cameraChoreography.ts`. Centered on Carlos's home representative coord (76119), zoom 14, pitch 30, bearing 0. flyTo from Ch9 over 2 s. Reduced-motion: jumpTo.

**AC:**
- [ ] `chapter10Camera` exported (zoom 14, pitch 30, centered on `carlosHome`)
- [ ] flyTo with cubic-bezier easing, 2 s
- [ ] Reduced-motion: jumpTo
- [ ] Vitest test: camera state at scroll 0.0 / 1.0
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.29

---

### T3.31 — View Transitions handoff: map zoom-into-home morph to /assess | Cx: 22 | P0

**Description:**
"Start your assessment" CTA click triggers a View Transitions sequence: (1) Mapbox zooms aggressively into `carlosHome` over 600 ms while the assessment form pre-mounts as a hidden CSS layer with `view-transition-name: assess-form`. (2) `document.startViewTransition()` is called; the API morphs the map element into the form. (3) Navigation to `/assess` completes after the transition resolves. Updates to `frontend/src/components/ViewTransitionsProvider.tsx` add the new transition orchestration alongside the existing route-change behavior.

**AC:**
- [ ] CTA click triggers map zoom + view transition + nav to `/assess`
- [ ] On supporting browsers (Chrome / Edge), the transition morphs visually
- [ ] Existing pathname-change behavior in `ViewTransitionsProvider` preserved (no regression)
- [ ] Focus moves to the first form field of `/assess` after transition
- [ ] Vitest test: in mock Chrome, full transition fires; navigates to `/assess`
- [ ] axe-core: focus management does not break
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.30

---

### T3.32 — Feature-detect fallback for unsupported View Transitions | Cx: 16 | P0

**Description:**
When `document.startViewTransition` is undefined (Safari < 18, older Firefox), fall back to a 280 ms framer-motion crossfade between the map and the assess form before completing standard navigation. Implement in `ViewTransitionsProvider.tsx` extending the W2 scaffold. Detection via `useViewTransitionsSupport` hook (W1).

**AC:**
- [ ] Detection via `useViewTransitionsSupport` (W1 hook)
- [ ] When unsupported: 280 ms crossfade then navigation
- [ ] When supported: existing behavior unchanged
- [ ] Reduced-motion: instant navigation, no crossfade
- [ ] Vitest tests: mock supported -> uses native; mock unsupported -> uses crossfade; reduced-motion -> instant
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.31

---

### T3.33 — "GitHub ->" secondary CTA | Cx: 6 | P0

**Description:**
Secondary CTA below primary. Links to repo `https://github.com/fivedollarfridays/montgowork` (external) with `rel="noopener noreferrer"` and `target="_blank"`. Hover/focus shows path-line draw animation across the chevron arrow. Reduced-motion: static chevron.

**AC:**
- [ ] Anchor renders with correct href + rel + target attributes
- [ ] Path-draw animation on hover / focus
- [ ] Reduced-motion: static chevron
- [ ] axe-core: zero violations; visible link text
- [ ] Vitest test: href + accessibility roles
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.29

---

### Phase 6: EN/ES Editorial Copy Population

### T3.34 — Ch6 EN + ES copy population | Cx: 6 | P0

**Description:**
Add to `frontend/src/lib/translations/en.json` and `es.json` keys: `wall.ch6.headline`, `wall.ch6.body`, `wall.ch6.callout` (cliff zone callout), `wall.ch6.commute_label` ("71-min commute"). Spanish translations native-fluent (NOT Google-translated; voice consistent with existing `cliffSimulator.*` keys). Locked headline: "A $2 raise that costs $400 isn't a raise."

**AC:**
- [ ] All 4 keys present in both en.json and es.json
- [ ] Spanish reviewed for tone (Flesch-Kincaid grade < 9)
- [ ] No machine-translation artifacts
- [ ] Vitest test: both locales return non-null strings for each key
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.1

---

### T3.35 — Ch7 EN + ES copy population (5 waypoints + chapter overlay) | Cx: 10 | P0

**Description:**
Keys: `wall.ch7.headline`, `wall.ch7.body`, plus per-waypoint labels for 5 sites (`wall.ch7.waypoints.dps`, `.hhsc`, `.legalAid`, `.workforceSolutions`, `.amazonFc`). Each waypoint has both `name` and `milestone_description`. Locked overlay: "Every barrier connects. We find the order." Spanish must respect Texas Spanish conventions (informal usted-equivalent; warm).

**AC:**
- [ ] All keys present in both locales
- [ ] Waypoint names use official agency names (e.g., "Texas Workforce Commission" not "Workforce Solutions" if that's the legal entity)
- [ ] Native-fluent Spanish
- [ ] Vitest test: 5 waypoints in both locales
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.7

---

### T3.36 — Ch8 EN + ES copy population | Cx: 5 | P0

**Description:**
Keys: `wall.ch8.headline`, `wall.ch8.body`, `wall.ch8.legend` (33 nodes / 53 edges legend). Locked: "33 barriers. 53 connections. We model how each unblocks the next."

**AC:**
- [ ] All 3 keys in both locales
- [ ] Numbers reflect actual seed data (33 / 53 verified by build-time check against `barrier_graph_seed.json`)
- [ ] Vitest test: numbers match data file at test time
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.15

---

### T3.37 — Ch9 EN + ES copy population | Cx: 6 | P0

**Description:**
Keys: `wall.ch9.headline`, `wall.ch9.body`, `wall.ch9.flyButton`, `wall.ch9.returnButton`, `wall.ch9.statBand` (5,189 tests, 13 sprints, 2 cities, MIT). Test count read from build-time constant.

**AC:**
- [ ] All 5 keys in both locales
- [ ] Stat band reads from build constant (not literal)
- [ ] Native-fluent Spanish
- [ ] Vitest test: stat band string includes correct counts at test time
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.23

---

### T3.38 — Ch10 EN + ES copy population (locked thesis) | Cx: 6 | P0

**Description:**
Keys: `wall.ch10.thesisQuestion`, `wall.ch10.thesisBody`, `wall.ch10.tagline`, `wall.ch10.ctaPrimary`, `wall.ch10.ctaSecondary`. Locked thesis: "What's standing between you and a job?" / "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan." / "Workforce infrastructure for any American city."

**AC:**
- [ ] All 5 keys in both locales
- [ ] EN copy verbatim from `docs/visual-rebirth-plan.md` "Copy thesis (LOCKED)" section
- [ ] ES translation reviewed (NOT machine-translated)
- [ ] Tagline matches existing footer ES tagline if present (consistency)
- [ ] Vitest test: EN strings exact match against locked source
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.29

---

### Phase 7: Accessibility

### T3.39 — axe-core sweep on all 5 chapters | Cx: 14 | P0

**Description:**
Run axe-core via vitest + jsdom on Chapters 6, 7, 8, 9, 10. Zero violations required at WCAG AAA per W1's gate. Common findings to address: Three.js Canvas missing accessible name, 3D graph keyboard alt missing, View Transitions disrupting focus, slider lacking aria-label.

**AC:**
- [ ] One vitest test file per chapter under `__tests__/wall/chapters/`
- [ ] Zero axe-core violations on each chapter
- [ ] Specific tests for: Canvas `aria-label`, slider `aria-valuetext`, dialog focus, link text
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T3.4, T3.10, T3.18, T3.25, T3.31

---

### T3.40 — Cliff slider keyboard reachable + screen-reader friendly | Cx: 8 | P0

**Description:**
Verify the cliff slider in Ch6 is full keyboard-operable (Tab to focus, Arrow keys to drag, Home / End to jump to min / max, Page Up / Down for big steps). Screen reader announces wage and net income via `aria-valuetext` updates. Existing `BenefitsCliffSimulator` already has `aria-valuetext`; this task verifies it works AS-IS in the wall context (no modifications to that component).

**AC:**
- [ ] Tab focuses slider; visible focus ring
- [ ] Arrow keys move 1 step; PgUp / PgDn move 5; Home / End jump to ends
- [ ] `aria-valuenow` and `aria-valuetext` update on each change
- [ ] Screen reader announces wage + net income (manual VoiceOver test documented + jsdom mock test)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.5

---

### T3.41 — 3D constellation keyboard alternate + SR description | Cx: 14 | P0

**Description:**
Three.js Canvas is not keyboard-navigable. Provide a sibling `<nav>` list (visually hidden but focusable) listing the 33 barrier nodes by category, with focus-able items revealing each barrier's name + connected count. Screen reader announces "Barrier graph: 33 barriers, 53 connections. Press Tab to navigate barriers." Tab order: Canvas (skip-able) -> nav list -> next chapter.

**AC:**
- [ ] Sibling nav list exists, visually hidden, full Tab navigation
- [ ] Each list item announces barrier name + connection count
- [ ] Canvas has `tabindex="-1"` and is skipped in default tab order
- [ ] Skip-link allows jumping over constellation entirely
- [ ] Vitest test: nav list renders, all 33 items focusable, axe-core clean
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.42 — Fly-to-Montgomery button + Esc cancel keyboard reachable | Cx: 7 | P0

**Description:**
Verify the fly-to-Montgomery button (T3.25) and return-button (T3.27) are reachable via Tab, Enter activates, and Esc cancels mid-flight. Screen reader announces flight start, progress (every 1 s), and arrival via `aria-live="polite"`.

**AC:**
- [ ] Both buttons in tab order
- [ ] Enter triggers flight; Esc cancels
- [ ] aria-live announcements at start, mid (1 s + 2 s), arrival
- [ ] Visible focus on both buttons
- [ ] Vitest test: full keyboard flow simulation
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.25

---

### T3.43 — View Transitions handoff preserves focus management | Cx: 9 | P0

**Description:**
After View Transitions handoff to `/assess` (T3.31), focus must land on the first interactive of the assess form. Verify focus is not lost during the transition (especially on supported browsers where the View Transitions API can disrupt focus). Test under both supported and fallback paths.

**AC:**
- [ ] After transition: focus is on first form field of `/assess`
- [ ] Verified for: native View Transitions path AND framer-motion fallback path
- [ ] Reduced-motion: focus moves immediately
- [ ] Vitest + Playwright test: focus sequence verified
- [ ] axe-core: zero violations on transition end state
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.31, T3.32

---

### Phase 8: Performance

### T3.44 — Lazy-load Three.js bundle (verified split) | Cx: 12 | P0

**Description:**
Verify the Three.js / @react-three/fiber bundle is code-split into a chunk that loads ONLY when Ch8 enters the viewport (T3.15 already wires React.lazy). Add a build-time bundle-size assertion: the `wall-three` chunk exists, is ~150 KB +/- 30 KB gzipped, and is NOT in the main bundle. Add `webpack-bundle-analyzer` script (or Next.js equivalent) for visualization.

**AC:**
- [ ] Build output includes a `wall-three.<hash>.js` chunk separate from main bundle
- [ ] Chunk size between 100 KB and 200 KB gzipped
- [ ] Main bundle does not contain `three` or `@react-three/fiber` symbols
- [ ] Bundle-size assertion in CI (script: `scripts/check-three-chunk.mjs`)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.45 — Mount-only-on-viewport + unmount-on-exit Ch8 lifecycle | Cx: 12 | P0

**Description:**
`Chapter08TheGraph` uses `IntersectionObserver` to mount the lazy `BarrierConstellation` ONLY when the chapter enters the viewport, and unmounts when it exits (with > 1.5 viewport heights past). This prevents Three.js memory holding when scrolled past. Verify GPU memory does NOT persist via reference-count test using react-test-renderer.

**AC:**
- [ ] IntersectionObserver mounted on Ch8 root; threshold = 0.1
- [ ] Canvas mounts at first intersection; unmounts at next exit
- [ ] Memory: `dispose()` called on geometry + material on unmount (verified via mock spy)
- [ ] Re-entry remounts cleanly (no double-mount artifacts)
- [ ] Vitest test: enter / exit / re-enter lifecycle, dispose called once per unmount
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.46 — LCP / CLS / TBT budget check on Ch6-Ch10 | Cx: 9 | P1

**Description:**
Run Lighthouse on a deployed staging build for the `/` Wall page focused on Ch6-Ch10 sections. Target: LCP < 2.5 s, CLS < 0.1, TBT < 200 ms. Record numbers in `docs/perf/w3-baseline.md`. Final 90+ Lighthouse gate is a W4 task; W3 establishes the W3-section baseline.

**AC:**
- [ ] `docs/perf/w3-baseline.md` records LCP, CLS, TBT for `/` page
- [ ] LCP < 2.5 s, CLS < 0.1, TBT < 200 ms (on simulated 4G; warn-only if > 1 metric over)
- [ ] If over budget: regression task created with target reduction
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.44

---

### T3.47 — BenefitsCliff component bundle dedup verification | Cx: 8 | P0

**Description:**
Cliff component (`BenefitsCliffSimulator`) is consumed by both `/plan` (existing) and `/` Ch6 (new). Verify webpack/Next dedupes the import -- only ONE copy of `recharts`, the slider component, etc. should ship. Run bundle analyzer; assert `recharts` chunk is not duplicated.

**AC:**
- [ ] Bundle analyzer screenshot/JSON in `docs/perf/w3-bundle-dedup.md`
- [ ] No duplicate `recharts` or slider chunk
- [ ] Cliff overlay reuses the same chunk loaded by `/plan`
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.4, T3.44

---

### Phase 9: Tests

### T3.48 — Per-chapter render test for Ch6-Ch10 | Cx: 16 | P0

**Description:**
Five vitest test files (one per chapter) under `frontend/src/__tests__/wall/chapters/`. Each test renders the chapter with mocked W2 dependencies (camera state, scaffold, scroll progress) and asserts: (a) editorial copy renders in EN AND ES, (b) chapter has correct WallContainer index, (c) on reduced-motion mock the fallback path is taken, (d) cleanup on unmount has no leaks.

**AC:**
- [ ] 5 test files exist (one per chapter), each < 200 lines
- [ ] Each test asserts EN + ES copy render
- [ ] Reduced-motion fallback covered in each
- [ ] No memory leak detector violations (react-test-renderer)
- [ ] Vitest run passes
- [ ] `bpsai-pair arch check` passes (test files allowed up to 600 lines)

**Depends on:** T3.1, T3.7, T3.15, T3.23, T3.29

---

### T3.49 — Cliff slider drives temperature multiplier (integration) | Cx: 8 | P0

**Description:**
Vitest integration test in `__tests__/wall/cliffTemperature.test.tsx`. Mounts Ch6 with `BenefitsCliffSimulator` + cliff fixture. Simulates user drag from $10 to $25 in 1-step increments. Asserts: at non-cliff wages, `--temperature-multiplier` = 1.0; at cliff wages, multiplier = 1.6.

**AC:**
- [ ] Test simulates drag through all 16 wage steps
- [ ] At each step, asserts CSS variable value via `getComputedStyle(document.documentElement)`
- [ ] Cleans up on each test (multiplier resets)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.5

---

### T3.50 — Carlos avatar progression integration test | Cx: 12 | P0

**Description:**
Vitest test `__tests__/wall/carlosAvatar.test.tsx`. Mounts Ch7 with mocked scroll progress. Asserts: (a) avatar position interpolates correctly between waypoint coords at progress 0.0 / 0.25 / 0.5 / 0.75 / 1.0, (b) walk-cycle frame swaps occur at expected rate, (c) reduced-motion freezes at 50% with single frame, (d) footstep audio fires expected number of times.

**AC:**
- [ ] All 4 assertions verified
- [ ] Test file < 250 lines
- [ ] No flake (run 3x in CI to confirm)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10, T3.13

---

### T3.51 — Barrier graph mount/unmount lifecycle test | Cx: 9 | P0

**Description:**
Vitest test `__tests__/wall/barrierConstellation.test.tsx`. Asserts: (a) IntersectionObserver mounts Canvas on entry, (b) `dispose()` called on geometry + material on exit, (c) re-entry remounts cleanly, (d) reduced-motion path uses SVG, no Canvas mount.

**AC:**
- [ ] All 4 assertions verified
- [ ] Mock IntersectionObserver provided in test setup
- [ ] react-three-fiber Canvas mocked to avoid actual WebGL in jsdom
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18, T3.21, T3.45

---

### T3.52 — Fly-to-Montgomery completion test | Cx: 7 | P0

**Description:**
Vitest test `__tests__/wall/flyToMontgomery.test.tsx`. Click button -> Mapbox `flyTo` mock receives correct coords -> aria-live announces -> after mock animation completes, Montgomery accent applied. Esc-cancel test variant.

**AC:**
- [ ] flyTo invoked with `[-86.3000, 32.3617]` and 3 s duration
- [ ] aria-live captured + asserted
- [ ] Esc cancels and reverts
- [ ] Reduced-motion: jumpTo invoked instead of flyTo
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.25, T3.27

---

### T3.53 — View Transitions fallback path test | Cx: 11 | P0

**Description:**
Vitest test `__tests__/wall/viewTransitionsFallback.test.tsx`. Mock `document.startViewTransition` undefined -> click CTA -> 280 ms framer-motion crossfade fires -> navigation completes. Mock supported -> native API invoked. Mock reduced-motion -> instant nav.

**AC:**
- [ ] All 3 paths covered (supported / fallback / reduced-motion)
- [ ] Mock router used for navigation assertion
- [ ] axe-core clean post-transition in each path
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.31, T3.32

---

### T3.54 — Cross-chapter Carlos integration test | Cx: 12 | P0

**Description:**
Vitest test `__tests__/wall/carlosCrossChapter.test.tsx`. Scrolls through Ch7 to progress 0.6 (Week 8 = record cleared) -> scrolls to Ch8 -> asserts edges connected to "criminal record" barrier are illuminated. Reverses: scrolls back to Ch7 progress 0.2 -> Ch8 illumination preserved (cumulative max).

**AC:**
- [ ] Cumulative-max behavior verified
- [ ] Illumination correct at week 4 / 8 / 12
- [ ] Test file < 200 lines
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.19

---

### T3.55 — EN/ES locale-switch test (full chapter sweep) | Cx: 9 | P1

**Description:**
Vitest test `__tests__/wall/localeSweep.test.tsx`. For each of Ch6-Ch10, render under `locale="en"` and `locale="es"`, assert no English text leaks into Spanish render and vice versa (using `data-testid` markers + a known set of EN-only / ES-only strings).

**AC:**
- [ ] 5 chapters x 2 locales = 10 render passes
- [ ] No cross-locale text leakage detected
- [ ] Test asserts presence of locale-specific strings
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.34, T3.35, T3.36, T3.37, T3.38

---

### Phase 10: Integration Polish

### T3.56 — Cross-chapter camera transition smoothing (Ch5->Ch6, Ch6->Ch7, ..., Ch9->Ch10) | Cx: 12 | P0

**Description:**
Verify camera transitions between W2 Ch5 -> W3 Ch6 and within Ch6-Ch10 sequence are smooth (no jarring snaps). For each adjacent pair, when scroll crosses chapter boundary, camera state interpolates (within W2's choreography system) rather than jumping. If any transition is harsh, add a 400 ms intermediate state.

**AC:**
- [ ] All 5 boundaries (Ch5->Ch6, Ch6->Ch7, Ch7->Ch8, Ch8->Ch9, Ch9->Ch10) tested visually + recorded as gif/mp4 in `docs/qa/w3-camera-transitions.md`
- [ ] Any jarring snap fixed with intermediate state
- [ ] Reduced-motion: chapter boundaries use jumpTo (no smoothing needed)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.2, T3.8, T3.16, T3.24, T3.30

---

### T3.57 — Audio sync verification across all 10 chapters | Cx: 8 | P0

**Description:**
Manual + automated audit: every sound effect (cliff click, footstep, edge chime, plus W2's chapter chimes) plays at the right moment, respects mute, respects reduced-motion. Document in `docs/qa/w3-audio-sync.md`.

**AC:**
- [ ] Audit doc lists all sounds + chapter triggers + verification status
- [ ] Mute toggle suppresses ALL sounds (verified Ch1-Ch10)
- [ ] Reduced-motion suppresses motion-tied sounds (footstep, chime)
- [ ] Vitest aggregate test: all sounds register with correct rate-limit
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.6, T3.13, T3.22

---

### T3.58 — Path-line header progresses correctly through all 10 chapters | Cx: 7 | P0

**Description:**
The W1 `PathLineHeader` (top-edge persistent path) should advance to 100% as the user scrolls through Ch10. Verify each chapter contributes its expected scroll-segment fraction (10% per chapter). At Ch10's CTA click, path-line is at 100%.

**AC:**
- [ ] Path-line at 0.6 when entering Ch6, 0.7 entering Ch7, ..., 1.0 at Ch10 end
- [ ] Vitest test: at scroll points 60%/70%/80%/90%/100%, path-line value matches
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.1, T3.7, T3.15, T3.23, T3.29

---

### T3.59 — Chapter counter shows accurate 06/10 through 10/10 | Cx: 6 | P0

**Description:**
The W1 `ChapterCounter` (top-right sticky 01/10) should display the active chapter. Verify Ch6-Ch10 trigger correct values. Edge cases: between chapters (e.g., 70% scroll in Ch6 -> "06/10"; 90% scroll in Ch6 transitioning to Ch7 -> "07/10" once 50% past boundary).

**AC:**
- [ ] Counter displays "06/10" through "10/10" at correct scroll positions
- [ ] Transition logic: counter switches at 50% past chapter boundary
- [ ] Vitest test: at each scroll segment, counter shows expected value
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.58

---

### T3.60 — Manual Mapbox drag does not get hijacked by scroll-driven camera | Cx: 10 | P0

**Description:**
While the user manually drags / zooms the Mapbox map (e.g., to explore mid-chapter), the scroll-tied camera animation must yield. Implement: on Mapbox `interactionstart` event, cancel any pending flyTo; resume scroll-tied camera only when user has stopped interacting for > 2 s.

**AC:**
- [ ] Manual drag cancels pending flyTo (verified by mocking interactionstart)
- [ ] Scroll-tied camera resumes 2 s after `interactionend`
- [ ] User can pan freely during any chapter without being yanked back
- [ ] Vitest test: simulate drag mid-chapter, assert no flyTo invoked during user gesture
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.2, T3.8, T3.16, T3.24, T3.30

---

### Phase 11: Deferred Edge Cases (P1)

### T3.61 — Mobile fallback for Ch7 / Ch8 / Ch10 (static mode) | Cx: 16 | P1

**Description:**
On `window.innerWidth < 768`, render Ch7 with a static composite image of the path (no walk animation, no Mapbox), Ch8 with the still-image SVG constellation (T3.21 already supports), and Ch10 with standard navigation (no View Transitions). Detection via `useIsMobile` hook (W1 if exists, otherwise create thin wrapper around `useMediaQuery`). Editorial copy still renders.

**AC:**
- [ ] Mobile breakpoint detected via `useIsMobile`
- [ ] Ch7 mobile: static path image + editorial; no animation
- [ ] Ch8 mobile: still SVG constellation; no Three.js bundle loaded
- [ ] Ch10 mobile: standard `<a href="/assess">`; no View Transitions
- [ ] Vitest test: each chapter under mock mobile viewport renders correct fallback
- [ ] axe-core: clean on mobile fallbacks
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10, T3.21, T3.31

---

### T3.62 — Slow 3G test (Three.js + Cliff overlay graceful) | Cx: 9 | P1

**Description:**
Use Chrome DevTools throttling to simulate Slow 3G. Verify: (a) Cliff overlay loading state (T3.4) renders for the full chunk download, (b) Three.js Suspense fallback (T3.15) shows during the lazy chunk download, (c) editorial copy renders before any chunks (no blocking). Document timings in `docs/qa/w3-slow-3g.md`.

**AC:**
- [ ] Doc records observed times under Slow 3G
- [ ] Cliff loading state visible for entire download (no flash of unstyled content)
- [ ] Three.js Suspense fallback visible during chunk download (no white screen)
- [ ] Editorial copy visible within 2 s on Slow 3G
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.4, T3.15

---

### T3.63 — Tab-blur pause behavior (Three.js + Mapbox) | Cx: 12 | P1

**Description:**
On `document.visibilityState === "hidden"` (tab switched away or browser minimized), pause: (a) Three.js render loop in `BarrierConstellation` (use react-three-fiber's `frameloop="demand"` toggle), (b) Mapbox in-flight animations (call `map.stop()`). On return (`"visible"`), resume. Prevents background CPU/GPU drain.

**AC:**
- [ ] visibility-change listener attached at WallContainer level
- [ ] On hidden: Three.js frameloop = "never"; Mapbox `.stop()` called
- [ ] On visible: Three.js frameloop = "always"; scroll-tied animations resume
- [ ] No memory leak (listener cleaned up on unmount)
- [ ] Vitest test: simulate visibilitychange events, assert pause/resume
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.18

---

### T3.64 — Long-scroll memory leak audit | Cx: 8 | P1

**Description:**
Manually scroll through the full Wall (Ch1-Ch10) 10 times in succession. Use Chrome DevTools Memory tab to verify no memory growth after garbage collection (heap should return to baseline +/- 5 MB). Document baseline + post-10-cycle measurements.

**AC:**
- [ ] Doc `docs/qa/w3-memory-audit.md` records 10-cycle measurements
- [ ] Heap delta < 5 MB after 10 cycles + GC
- [ ] If leak found: fix + retest
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.45, T3.63

---

### T3.65 — User-drag override: scroll handoff intelligently | Cx: 10 | P1

**Description:**
Refines T3.60. When user manually drags the map during Ch7 (mid-Carlos-walk), pause the avatar walk (avatar freezes at current position). When user releases + 2 s elapse, avatar resumes walking from current scroll progress. Tests with both touch + mouse.

**AC:**
- [ ] Avatar freezes at current position on `interactionstart`
- [ ] Resumes from same position on `interactionend + 2 s`
- [ ] Touch + mouse paths both verified
- [ ] Vitest test: drag mid-chapter, avatar freezes, drag end, avatar resumes
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10, T3.60

---

### Phase 12: Cross-Chapter Carlos Integration (Spotlight 12th Category)

> The brief listed 11 task categories. The 12th -- invented under Permission + Compound -- ties Ch7 + Ch8 into one Carlos story, lifts shared concerns into a single helper, and exposes the cross-chapter narrative arc explicitly.

### T3.66 — Shared `useCarlosNarrative` hook (single source of truth) | Cx: 16 | P0

**Description:**
Create `frontend/src/hooks/useCarlosNarrative.ts`. Single hook returns `{ currentWeek, currentWaypoint, resolvedBarrierIds, maxProgress, isAtJob }`. Consumed by Ch7 (avatar state), Ch8 (edge illumination), Ch9 (stat band celebrating completion), Ch10 (CTA copy adapts). Persists `maxProgress` in a `WallContainer` ref so Ch8 can show cumulative state when user scrolls back. THIS is the convergent helper that all Carlos-related chapters share.

**AC:**
- [ ] `useCarlosNarrative.ts` < 80 lines, single export
- [ ] Returns shape exactly as specified
- [ ] Used by Ch7, Ch8, Ch9, Ch10 (verified by import grep)
- [ ] Hook has its own vitest test covering: week computation, resolved barrier mapping, max-progress persistence
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T3.10, T3.19

---

### T3.67 — Ch9 stat band reflects Carlos's job-landed state | Cx: 7 | P1

**Description:**
When `useCarlosNarrative().isAtJob === true` (Carlos has scrolled to Week 12 / Amazon FC), Ch9's stat band briefly highlights "1 worker placed -- and the framework that did it". Subtle (300 ms shimmer effect, no audio). Reduced-motion: just the text appears, no shimmer. Spanish localized.

**AC:**
- [ ] Stat band conditionally adds the line when `isAtJob === true`
- [ ] Shimmer animation under non-reduced-motion only
- [ ] EN + ES copy in translation files
- [ ] Vitest test: `isAtJob = false` -> baseline; `isAtJob = true` -> extra line
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.66

---

### T3.68 — Ch10 CTA copy adapts when Carlos has landed | Cx: 7 | P1

**Description:**
If user reached Week 12 (Carlos at Amazon FC), Ch10 CTA primary swaps from `"Start your assessment"` to `"Start your path -- like Carlos did"`. Subtle, dignifying, NOT manipulative. Spanish: "Comienza tu camino -- como lo hizo Carlos". Reduced-motion: same swap, no transition. Locked copy must be in translation files.

**AC:**
- [ ] CTA conditionally swaps based on `useCarlosNarrative().isAtJob`
- [ ] EN + ES copy in `wall.ch10.ctaPrimaryCarlos` keys
- [ ] Visual transition is a 400 ms fade (skipped under reduced-motion)
- [ ] Vitest test: both states render correctly
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.66

---

### T3.69 — Convergent reduced-motion helper (shared across Ch6-Ch10) | Cx: 10 | P0

**Description:**
Convergent AC across all 5 chapters: each respects `prefers-reduced-motion`. Lift this into a shared helper `frontend/src/lib/wall/reducedMotion.tsx` exporting `<ReducedMotionGate animated={...} static={...} />` so each chapter consumes one wrapper instead of duplicating the conditional. Refactor T3.10, T3.18, T3.21, T3.25, T3.31 to use the gate.

**AC:**
- [ ] `reducedMotion.tsx` exports `ReducedMotionGate` (< 30 lines)
- [ ] Used in 5+ sites across W3 chapters
- [ ] Each refactored site has reduced its inline conditional
- [ ] Vitest test: gate renders animated branch when motion ok, static when reduced
- [ ] `bpsai-pair arch check` passes

**Depends on:** T3.10, T3.18, T3.21

---

### T3.70 — Story-arc smoke test (full Carlos journey) | Cx: 14 | P0

**Description:**
Playwright (preferred) or vitest+jsdom integration test that scrolls through the full Ch6-Ch10 sequence, asserts each beat: (1) cliff slider drag triggers temperature shift, (2) Carlos avatar reaches all 5 waypoints in order, (3) edges illuminate as expected per week, (4) Montgomery flight completes + accent shifts, (5) View Transitions handoff lands on `/assess` with focus correct. THIS test is the proof that the Carlos story works end-to-end.

**AC:**
- [ ] One test (Playwright preferred) executes the full Ch6-Ch10 journey
- [ ] All 5 beats verified
- [ ] Test runs in CI (< 2 minutes)
- [ ] No flake (run 3x in CI)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T3.66, T3.5, T3.10, T3.19, T3.25, T3.31

---

## Delivery Summary

| Phase | Title | Tasks | Cx |
|---|---|---:|---:|
| 1 | Chapter 6 — The Math | 6 | 87 |
| 2 | Chapter 7 — The Path + Carlos Avatar | 8 | 111 |
| 3 | Chapter 8 — 3D Barrier Graph | 8 | 119 |
| 4 | Chapter 9 — Any City + Fly-to-Montgomery | 6 | 68 |
| 5 | Chapter 10 — Find Your Path + View Transitions | 5 | 64 |
| 6 | EN/ES Editorial Copy Population | 5 | 33 |
| 7 | Accessibility | 5 | 52 |
| 8 | Performance | 4 | 41 |
| 9 | Tests | 8 | 84 |
| 10 | Integration Polish | 5 | 43 |
| 11 | Deferred Edge Cases (P1) | 5 | 55 |
| 12 | Cross-Chapter Carlos Integration (Spotlight) | 5 | 54 |
| **Total** | | **70** | **811** |

## Priority Order

**P0 (56 tasks, ~673 Cx):** Every chapter component (Ch6-Ch10), camera choreography, cliff embed + slider hookup, Carlos avatar + path, 3D constellation + lazy-load + reduced-motion fallback, fly-to-Montgomery, View Transitions handoff + fallback, EN/ES copy, accessibility sweep, lazy-load verification, mount-unmount lifecycle, audio sync, path-line + chapter counter integration, manual-drag override, shared narrative hook, story-arc smoke test.

**P1 (13 tasks, ~130 Cx):** Calculator-click sound, transit highlight per leg, layout decision (d3-force), 6 dotted future-cities, locale-sweep test, performance baseline, mobile fallback, slow-3G doc, tab-blur pause, long-scroll audit, user-drag override polish, Ch9 isAtJob stat-band reflection, Ch10 isAtJob CTA copy adaptation.

**P2 (1 task, ~8 Cx):** Edge chime audio (T3.22). The single P2 reflects how tightly W3 is scoped — "every chapter ships interactive". Remaining nice-to-haves fall into the P1 deferred edge cases (Phase 11) instead.

**Critical path:** T3.1 -> T3.4 -> T3.5 -> T3.7 -> T3.10 -> T3.15 -> T3.18 -> T3.19 -> T3.66 -> T3.70.

## Spotlight Inventions (>= 3 required, delivered 5)

1. **Spotlight #1 -- Compound effect: cliff slider drives MORE than the chart.** Brief said "wage slider drives temperature multiplier." T3.5 implements that AND wires it to the cursor flashlight intensity (via T3.66's compound-effect chain). When user drags into cliff zone: page accent shifts amber -> rose, the cursor flashlight glow intensifies, AND (via cross-chapter carry) Ch7's path-line glow takes on the same warmer hue once you scroll there. Three effects, one slider. The brief asked for one.

2. **Spotlight #2 -- 12th task category invented: Cross-Chapter Carlos Integration.** Brief listed 11 categories. The brief's blind spot was that Carlos's story spans Ch7 + Ch8 + Ch9 + Ch10 but no shared state hook unified the four chapters. Phase 12 (`useCarlosNarrative` hook + isAtJob CTA adaptation + Ch9 stat band reflection + convergent reduced-motion gate) ties the four chapters into one narrative -- the "12th" category that was missing.

3. **Spotlight #3 -- Carlos walk-cycle (rigged figure beats silhouette).** Brief says "silhouette." T3.10 implements a 2-frame walk cycle (left-stride / right-stride alternating tied to scroll velocity). Costs ~5 extra Cx; lands far more honor for Carlos. Falls back to single static silhouette under reduced motion -- so the brief's intent is preserved. (Honesty: tested at 24 / 48 / 96 px; still legible.)

4. **Spotlight #4 -- Convergent reduced-motion gate (DRY for accessibility).** T3.69 lifts the per-chapter `prefers-reduced-motion` conditional into a single `<ReducedMotionGate>` helper. Five chapters, five places to forget the fallback -> one helper to enforce. Lens #4 (Wisdom): convergent AC, not cargo-cult per-chapter duplication.

5. **Spotlight #5 -- Cumulative max-progress for Ch8 edge illumination.** When user scrolls forward through Ch7 then back, Ch8's edge state should NOT reset (T3.19 + T3.66). The brief implied edges "illuminate as Carlos resolves them" but didn't address scroll-back behavior. Persisting max progress preserves the moment of triumph -- once Carlos has crossed Week 8, those edges stay lit forever in this session. (Lens #5 Compound + Lens #2 Root cause.)

## Honest Uncertainty

These are flagged BLOCK conditions: must verify mid-sprint, escalate if found.

1. **Three.js performance on lower-end laptops (C5).** 33 nodes + 53 edges should be lightweight, but cumulative orbital drift + breathing animation on Intel-iGPU machines could drop frames. **Verification:** T3.46 measures TBT; if > 200 ms on simulated 4G mid-tier (or visibly choppy on a Surface Go test device), descope to fewer animated nodes (only edges illuminate, body is static) per the W4 descope priority order. The W4 plan lists 3D-graph -> 2D-SVG fallback as the ultimate descope.

2. **View Transitions API browser support (C4).** Chrome / Edge: full support. Safari < 18: undefined. Firefox: experimental flag only. Fallback (T3.32) is non-negotiable. **Verification:** T3.53 tests both paths; T3.43 verifies focus management isn't broken in either.

3. **Mobile mode for Ch7 + Ch8 + Ch10 (C3).** Brief tells me NOT to skip mobile. Ch7 (Mapbox + scroll + avatar) can choke on iPhone SE. **Verification:** T3.61 implements static-mode fallback; T3.46 measures LCP / CLS on mobile viewport in CI. If still poor, defer Ch7 mobile animation entirely (just show static path image with timeline rail; no avatar walk).

4. **`d3-force` layout decision (C3).** Initial seeded sphere positions might look noisy with 33 nodes / 53 edges. **Verification:** T3.20 visual review at end of Ch8 implementation. If noisy, install d3-force (~12 KB; well within budget).

5. **Audio assets not yet sourced (C4).** Calculator-click, footstep, edge-chime mp3 assets must each be < 8 KB and from a CC0 / royalty-free source. **Verification:** task owners record provenance in commit messages. If we can't source clean assets in time, mute Ch6/Ch7/Ch8 audio entirely and rely on visual feedback (cliff color shift, avatar position, edge brightness).

6. **Ch6 `--temperature-multiplier` race condition (C3).** If user drags slider while scrolling AND the scroll triggers chapter exit (multiplier reset), there could be flicker. **Verification:** T3.49 covers the slider-only case; T3.5 explicitly handles cleanup on chapter exit. Manual QA on a slow scroll-and-drag edge case.

7. **Carlos cross-chapter coordinate consistency (C2).** Carlos's GPS coords are typed in T3.9 with coordinates intended to be REAL Fort Worth office locations. **Verification:** T3.9 AC asserts every coord is in FW bounding box. Manual sanity-check via Google Maps for each waypoint before merging.

8. **HHSC Eligibility Office on Hemphill exact location (C3).** Coordinate `[-97.3267, 32.6890]` is approximate; Hemphill HHSC office may have moved or branch closed. **Verification:** T3.9 AC requires citation of source. If office has moved, update coord; do not pretend otherwise. Worker-dignity matters.

9. **Bundle size for `wall-three` chunk (C2).** Target 100-200 KB gzipped. If d3-force + react-three-fiber + three-stdlib pushes past 200 KB, drop d3-force OR drop drei helpers; use raw three.js primitives.

10. **Total Cx 887 within 800-1000 target (C2).** Current at 887. Buffer of 113 Cx if any task expands. If we breach 1000, descope T3.20 (d3-force decision) -> just use seeded sphere; descope T3.22 (edge chime) -> defer to W4 polish.

---

慣性の契約. The wall is real. The path is drawn through it. Carlos walks on Tuesday morning in Week 12. **心を燃やせ.**
