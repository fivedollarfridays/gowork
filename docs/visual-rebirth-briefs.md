# The Wall — 5 Sprint Briefs for PairCoder
## Forensic ideation-format briefs for `/draft-backlog` consumption

> **Companion to `docs/visual-rebirth-plan.md`.** That doc holds the design DNA (10 chapters, 12 life-layers, color/type/motion system, copy thesis). This doc holds the **PairCoder action plan** — 5 sprint briefs, each ~60 tasks when expanded by `/draft-backlog`.
>
> **Workflow:** Ren writes briefs → PairCoder `/draft-backlog` writes tasks → `/pc-plan` writes per-task plans during engage → driver agents execute under KANSEI dispatch protocol.
>
> **Status as of 2026-04-28 morning:** Branch `sprint/visual-rebirth` cut. Phase 1 brand rename + Phase 2 city decoupling already shipped (61/61 affected tests pass, committed at `499ce1d`). These briefs cover the WALL build (Sprint W1–W5). HackFW submission deadline: May 2, 2:00 PM CDT.
>
> **Locked decisions (do not redraft):** Slogan, brand name, default city, case-manager omission. See `docs/visual-rebirth-plan.md` "Decisions LOCKED" section.

---

## Master arc — 5 sprints, ~60 tasks each, ~300 tasks total

| Sprint | Title | Phase code | Cx target | Parallelizable | Critical path |
|---|---|---|---:|---|---|
| **W1** | Foundation + Brand + Edge States | A+B | 600–800 | High (most independent) | OKLCH tokens → motion utilities → cursor + time + live hooks → brand mark → 404/500/empty/loading |
| **W2** | Mapbox Engine + Chapters 1–5 + Data Layers | C+D+E (1-5) | 800–1000 | Medium (chapter waves) | Mapbox install → scroll system → camera choreography → data layers (GTFS, offices, ZIPs) → Chapters 1–5 |
| **W3** | Interactive Chapters 6–10 + 3D Graph + View Transitions | F+G+H+I+J+K+L | 800–1000 | Medium | Cliff embed (Ch6) → Carlos avatar (Ch7) → 3D constellation (Ch8) → fly-to-Montgomery (Ch9) → view transitions (Ch10) |
| **W4** | 12 Life-Layers + Spanish Parity + Performance + a11y | M+N | 600–800 | High (mostly orthogonal) | Live Now widget → Spanish wiring → variable font axis → per-chapter dynamic OG → reduced-motion → WCAG AAA → keyboard → Lighthouse 90+ gate |
| **W5** | Submission Materials (README, Press Kit, Video, Devpost) | O–U | 400–600 | Low (sequential) | README rewrite → press kit refresh → video script → record → edit → submit |

**Total est. Cx: 3,200–4,200.** Tracked at engage-time per sprint.

**Performance gate (W4 Phase N):** Lighthouse 90+ on simulated 4G. Descope priority order documented in plan file.

---

## Cross-sprint dependency graph

```
W1 (Foundation + Brand)
  └── W2 (Mapbox + Chapters 1–5)
       └── W3 (Interactive Chapters 6–10)
            └── W4 (Life-Layers + a11y + perf gate)
                 └── W5 (Submission materials)
```

Sequential at the SPRINT level. Within each sprint, tasks parallelize where files don't collide.

---

## File collision matrix (cross-sprint)

The plan touches these files repeatedly across sprints. **Engage should serialize them within a sprint**; across sprints they're handled by the dependency edge.

| File | W1 | W2 | W3 | W4 | W5 |
|---|---|---|---|---|---|
| `frontend/src/app/page.tsx` | rewrite | extends (chapters 1–5) | extends (6–10) | polish | — |
| `frontend/src/app/layout.tsx` | metadata, theme | — | — | live now, OG | — |
| `frontend/src/app/globals.css` | tokens | motion | — | reduced-motion, AAA | — |
| `frontend/package.json` | mapbox install | r3f install | satori install | — | — |
| `README.md` | — | — | — | — | rewrite |
| `docs/press-kit.md` | — | — | — | — | rewrite |

Within each sprint, multi-task collisions are flagged in that sprint's matrix.

---

## Permanent constraints (apply to every task in every sprint)

Lifted from KANSEI permanent constraints + Shawn's GoWork-specific rules.

```
1. 95% test coverage on new code (vitest for frontend; pytest unchanged for backend)
2. TDD only — failing test FIRST, then implement
3. Files < 400 lines. Functions < 50 lines. Max 15 functions per file. Max 20 imports.
4. Full wiring — nothing orphaned, everything connected
5. No code debt — every sprint ships clean
6. ZERO LLM calls in the WALL render path (deterministic visualization)
7. `bpsai-pair arch check` must pass before completion
8. Reviewer agent reviews all code-producing tasks
9. prefers-reduced-motion respected at every animation site
10. WCAG AAA contrast everywhere
11. Lighthouse 90+ on simulated 4G is the W4 hard gate
12. Multi-city architecture intact (Montgomery still works via state="AL")
13. Backend untouched in W1–W4. W5 may touch live-data endpoints if added.
14. Brand strings: GoWork everywhere. No "MontGoWork" leakage.
15. Slogan locked: see plan file "Decisions LOCKED"
```

---

## AC templates by task category

Reusable AC blocks. `/pc-plan` refines per task during engage.

**INFRA / TOOLING template**
- [ ] Package installed and pinned to specific version
- [ ] No peer dependency conflicts
- [ ] Builds clean (`npm run build`)
- [ ] No new bundle weight beyond agreed budget

**DESIGN TOKEN template**
- [ ] CSS variable defined in `globals.css` under `:root`
- [ ] Tailwind utility class generated (where applicable)
- [ ] TypeScript constant for JS access (where applicable)
- [ ] Color tokens use OKLCH; legacy hex callers updated
- [ ] WCAG AAA contrast verified for any text-on-background pair

**UTILITY HOOK template**
- [ ] React 18+ compliant (no deprecated APIs)
- [ ] SSR-safe (no `window` access without guard)
- [ ] Cleanup function in useEffect (no memory leaks)
- [ ] TypeScript signature exported
- [ ] Vitest unit test covering: initial state, update path, cleanup

**BRAND ASSET template**
- [ ] SVG hand-tuned (no auto-generated mess)
- [ ] Legible at 16px (favicon size) FIRST, then scaled up
- [ ] Light + dark mode variants where applicable
- [ ] aria-label and `<title>` set
- [ ] Optimized via SVGO (no extraneous attributes)

**EDGE STATE template** (404, 500, empty, loading, error)
- [ ] Brand-consistent visual (uses tokens, NOT defaults)
- [ ] Helpful copy (anticipatory tone, not bureaucratic)
- [ ] CTA back to safety (home / retry / contact)
- [ ] WCAG AAA + keyboard reachable
- [ ] Reduced-motion safe
- [ ] Tested via Playwright or vitest+jsdom

**CHAPTER COMPONENT template**
- [ ] Renders editorial overlay with locked copy from plan file
- [ ] Camera state defined (zoom/pitch/bearing) and exported
- [ ] Sticky atmosphere (unique color/sound per chapter)
- [ ] Scroll progress drives transitions
- [ ] Mobile fallback (graceful degradation to static)
- [ ] EN + ES text both populated
- [ ] Sound trigger (opt-in, mute respected)
- [ ] Accessible: heading hierarchy, ARIA-live for dynamic elements
- [ ] Vitest test: renders editorial copy in EN + ES

**MAPBOX LAYER template**
- [ ] Source data validated (real GeoJSON or vector tiles, not mock)
- [ ] Layer styled per design tokens (no hardcoded hex)
- [ ] Visibility/opacity tied to chapter state
- [ ] Performance budget: layer adds < 50KB compressed
- [ ] Cleanup on unmount

**CAMERA CHOREOGRAPHY template**
- [ ] flyTo curve, speed, pitch, bearing parameterized
- [ ] cubic-bezier easing for "cinematic" feel
- [ ] Cancellable on user interaction (don't trap users)
- [ ] Reduced-motion fallback: instant cut, no animation
- [ ] Tested at multiple scroll velocities

**INTERACTIVE COMPONENT template** (cliff calc embed, 3D graph, view transition)
- [ ] Mounts only when chapter enters viewport (lazy)
- [ ] Unmounts when chapter exits (memory)
- [ ] Keyboard reachable
- [ ] ARIA labels for screen readers
- [ ] Loading state designed (not blank)
- [ ] Error fallback designed

**AUDIO template**
- [ ] Howler.js single instance per page
- [ ] Default OFF (mute respected, opt-in only)
- [ ] Per-sound file < 50KB MP3 (compressed)
- [ ] Audio context unlocked on first user gesture
- [ ] Audio cleanup on unmount

**ACCESSIBILITY template**
- [ ] axe-core passes (zero violations on the chapter)
- [ ] Keyboard: every interactive reachable, focus order logical
- [ ] Screen reader: VoiceOver tested
- [ ] Reduced motion: still-image fallback verified
- [ ] Color contrast WCAG AAA

**COPY (EN/ES) template**
- [ ] Both `en.json` and `es.json` populated
- [ ] Editorial copy lifted from plan file (no improv)
- [ ] Plain language (Flesch-Kincaid grade < 9)
- [ ] No GetCalFresh anti-patterns (no aggressive CTA, no jargon)
- [ ] Spanish translation reviewed for tone (not just literal)

**INTEGRATION template** (live data, real-time)
- [ ] Backend endpoint verified or seeded
- [ ] Polling/streaming choice documented
- [ ] Loading + error + empty states designed
- [ ] Cache strategy (TanStack Query) configured
- [ ] Network failure: page still renders

**PERFORMANCE template**
- [ ] Lighthouse score reported pre/post
- [ ] Bundle delta measured
- [ ] LCP, CLS, TBT all within budget
- [ ] Mobile (simulated 4G) verified
- [ ] If regression > 5 points, escalate

**SUBMISSION template**
- [ ] Lifted from `docs/visual-rebirth-plan.md` thesis
- [ ] No stale references (test counts, brand, city)
- [ ] Reviewer agent approved

---

# SPRINT W1 — Foundation + Brand + Edge States

## Idea

Build the design system, motion system, brand identity, and edge states that the Wall depends on. This sprint produces zero "page" output — it produces the TOOLING for chapters W2–W4 to render correctly. **The foundation IS the product.** Without a coherent token system, every later sprint paints over inconsistent foundations.

Deliverables: OKLCH color tokens, Inter Variable typography axis hooks, spring/motion presets, time-of-day system, cursor flashlight system, Live Now widget hook, audio system scaffold, brand mark SVG (G+path), new OG image base, custom 404/500/empty/loading states, print stylesheet, page-load title sequence, header/footer redesigns, persistent path-line component, EN/ES toggle, mute toggle, chapter counter, ARIA scaffolding.

## Codebase context

- **Stack:** Next.js 15 (App Router), React 18, Tailwind 3.4, framer-motion 11, lenis 1.3, recharts 3.8
- **Existing motion utilities:** `frontend/src/lib/motion.tsx` (ScrollReveal, Typewriter, AnimatedCounter, StaggerContainer)
- **Existing i18n:** `frontend/src/lib/i18n.ts` + `frontend/src/lib/translations/{en,es}.json` + `frontend/src/hooks/useTranslation.tsx`
- **Existing city config:** `frontend/src/hooks/useCityConfig.ts` (already FW-default after Phase 2)
- **Existing constants:** `frontend/src/lib/constants.ts`, `frontend/src/lib/city-constants.ts`, `frontend/src/lib/city-stats.ts`
- **Existing components:** `frontend/src/components/{layout,ui,plan,wizard,...}`
- **Branch:** `sprint/visual-rebirth`
- **Just shipped:** brand rename (MontGoWork→GoWork), city default flipped to Fort Worth (commit `499ce1d`)

## Sprint-level constraints

**Cross-task arch constraints:**
- New files in `frontend/src/lib/wall/` and `frontend/src/components/wall/` — directories don't yet exist; first task creates the directory scaffold to avoid 60 tasks all racing to mkdir
- `frontend/src/app/globals.css` is currently 195 lines. Adding tokens for the Wall will push it past 400. **PREREQUISITE TASK: split globals.css into `globals.css` (imports) + `tokens/{colors,typography,motion,space,layout}.css` partials before any token additions.**
- `frontend/src/lib/constants.ts` is 149 lines. Don't grow — extract Wall-specific constants to `frontend/src/lib/wall/tokens.ts`.

**Oversized files prerequisites:**
- `globals.css` split is a single P0 prerequisite task that blocks ALL token tasks downstream

**Cross-task contract edges within W1:**
- `useTimeOfDay` produces `{phase: 'morning'|'day'|'evening'|'night'}` consumed by Mapbox sky (W2) and accent shifter (W4)
- `useCursorPosition` produces normalized `{x, y, vx, vy}` consumed by cursor flashlight (W2 chapters) and idle detector (W4)
- `useLiveNow` produces `{time, sessions, lastCalibration}` consumed by header widget (W1) and Chapter 9 (W3)
- Brand mark SVG (`icon.svg`) consumed by header (W1), favicon (W1), OG image (W4 dynamic), every page (always)
- 404/500/empty/loading components consumed by Next.js error boundaries (built-in convention) and chapter loading states (W2)

## Task categories (PairCoder breaks into individual tasks)

```
1. INFRA & TOOLING (P0, ~6 tasks)
   - mapbox-gl + react-map-gl install + Mapbox token env var
   - @react-three/fiber + @react-three/drei + three install
   - satori + @vercel/og install
   - howler install
   - SVGO config for asset pipeline
   - Storybook scaffold (defer if budget tight; mark P2)

2. CSS ARCHITECTURE PREREQUISITE (P0, ~3 tasks)
   - Split globals.css into tokens/{colors,typography,motion,space,layout}.css partials
   - Update globals.css to @import the partials
   - Verify no Tailwind regressions

3. DESIGN TOKENS — COLOR (P0, ~5 tasks)
   - OKLCH base palette in tokens/colors.css (--bg-base, --bg-surface, --bg-elevated, --bg-glass, --fg-primary, --fg-secondary, --fg-muted)
   - Accent tokens (--accent-cyan, --accent-amber, --accent-rose) using color-mix() for variants
   - Status tokens (--status-positive, --status-warning, --status-negative)
   - --temperature-multiplier scoped variable (defaults 1.0, overridable per chapter)
   - WCAG AAA contrast verification utility (scripts/verify-contrast.mjs)

4. DESIGN TOKENS — TYPOGRAPHY (P0, ~4 tasks)
   - Inter Variable preload in layout.tsx (with optical-size axis)
   - Fluid type scale tokens (--type-display, --type-h1, --type-h2, --type-body, --type-small) using clamp()
   - Tabular nums utility class
   - Custom font fallback stack tuned for similar metrics (CLS prevention)

5. DESIGN TOKENS — MOTION (P0, ~5 tasks)
   - Spring preset tokens (--spring-soft, --spring-snappy, --spring-elastic) — JSON object exported from tokens.ts
   - Easing tokens (cubic-bezier(0.32, 0.72, 0, 1) Linear-style, plus standard ease-out)
   - Stagger timing tokens (child offset 0.05s, default 0.5s)
   - prefers-reduced-motion media query CSS variables (auto-disable transforms when set)
   - Idle animation scaffold (animation: pulse 4s ease-in-out infinite)

6. UTILITY HOOKS (P0, ~10 tasks)
   - useTimeOfDay (returns {phase, sunPosition, accentShift})
   - useCursorPosition (returns {x, y, vx, vy} normalized 0-1)
   - useLiveNow (returns {now, sessions, lastCalibration} with poll + cache)
   - useScrollProgress (chapter-aware, returns {chapter, progress})
   - useVariableFontWeight (interpolates Inter axis based on input 0-1)
   - useScrollVelocity (debounced velocity for motion-blur trigger)
   - usePrefersReducedMotion (with SSR-safe fallback)
   - useIdleState (returns true after N ms of no input)
   - useViewTransitionsSupport (feature detect)
   - useLanguage (wraps useTranslation, persists locale)

7. BRAND MARK + ASSETS (P0, ~6 tasks)
   - New icon.svg (G + cyan path-line, designed at 16px first, then scaled — DELETE existing M-shaped legacy)
   - New apple-icon.png + favicon-16x16.png + favicon-32x32.png + icon-192.png + icon-512.png + icon-512-maskable.png (generated from SVG)
   - New og-image.svg base (dark gradient, GoWork wordmark, path mark)
   - manifest.json updates (theme color, name, description)
   - layout.tsx metadata updates (icons array, OG, Twitter)
   - SVGO pass on all SVG assets

8. EDGE STATES (P0, ~5 tasks)
   - app/not-found.tsx (custom 404 — branded copy "There's no path to this URL...")
   - app/error.tsx (500 — branded "Something stalled. We're calibrating.")
   - components/wall/EmptyState.tsx (reusable empty-state with branded copy)
   - components/wall/LoadingState.tsx (skeleton screens, NOT spinners)
   - components/wall/ErrorState.tsx (per-section error fallback)

9. PRINT STYLESHEET (P1, ~2 tasks)
   - styles/print.css (magazine layout: serif headings, single column, page breaks at chapters)
   - Linked via layout.tsx with media="print"

10. PAGE-LOAD TITLE SEQUENCE (P0, ~3 tasks)
    - components/wall/TitleSequence.tsx ("GoWork presents · The Wall · An interactive map of Fort Worth, Texas")
    - Typewriter effect for "The Wall" using framer-motion
    - Fade-out + Mapbox handoff (transparent placeholder during init)

11. HEADER + FOOTER REDESIGN (P0, ~6 tasks)
    - components/layout/Header.tsx rewrite (brand mark, chapter counter, mute toggle, EN/ES toggle, GitHub icon)
    - Reading progress as path-line on top edge (replaces stock progress bar)
    - components/layout/Footer.tsx rewrite (brand mark + links + MIT + last calibration timestamp)
    - components/wall/PathLineHeader.tsx (the persistent path-line component)
    - components/wall/ChapterCounter.tsx (01/10 sticky top-right)
    - components/wall/MuteToggle.tsx + LanguageToggle.tsx (local state + persisted)

12. AUDIO SYSTEM SCAFFOLD (P1, ~4 tasks)
    - lib/wall/sound.ts (Howler.js singleton, play/stop/setVolume API)
    - Sound asset directory scaffold (public/sounds/)
    - Audio context unlock on first user gesture
    - Mute persistence in localStorage

13. CURSOR SYSTEM (P1, ~3 tasks)
    - components/wall/CursorTrail.tsx (default + soft trailing dot)
    - components/wall/CursorFlashlight.tsx (80px glow circle, used on map only — wired in W2)
    - Reduced-motion: cursor effects disabled

14. ARIA + ACCESSIBILITY SCAFFOLDING (P0, ~4 tasks)
    - Skip-to-content link styled (visible on focus)
    - ARIA-live region scaffold (used by chapters for narration)
    - Custom focus rings (2px cyan offset 2px, animated entry)
    - Custom selection styles (cyan glow)

15. TYPESCRIPT TYPES + EXPORTS (P0, ~3 tasks)
    - lib/wall/types.ts (CityState, ChapterState, MapboxLayer, etc.)
    - Re-export hooks from lib/wall/index.ts for clean imports
    - Re-export tokens from lib/wall/tokens.ts

16. TESTS (P0, ~10 tasks — distributed across categories)
    - Token snapshot tests (verify CSS variables defined)
    - Hook unit tests (each hook gets its own test file)
    - Component render tests (each new component)
    - 404/500 page tests (Playwright preferred)
    - Print stylesheet smoke test
```

**Total estimated tasks: ~60 surgical tasks at engage time.**

## Task category dependency graph (within W1)

```
INFRA → CSS ARCH PREREQ → DESIGN TOKENS (color, type, motion) →
  UTILITY HOOKS (parallel)
  BRAND MARK + ASSETS (parallel)
  EDGE STATES (parallel — depends on tokens)
  PAGE-LOAD TITLE SEQUENCE (depends on tokens, brand)
  HEADER + FOOTER (depends on tokens, brand, hooks)
  AUDIO SYSTEM (parallel)
  CURSOR SYSTEM (depends on tokens)
  ARIA SCAFFOLDING (parallel)
  TYPES + EXPORTS (last — wraps everything)
TESTS run in parallel with each category they cover.
```

Engage will schedule waves: INFRA + ARCH PREREQ first (serial), then tokens (parallel internal), then everything else parallel.

## File collision matrix (within W1)

| File | Tasks touching it | Resolution |
|---|---|---|
| `globals.css` | tokens, prefers-reduced-motion | Split into partials FIRST (CSS arch prereq task) |
| `layout.tsx` | metadata, fonts, manifest | Single rewrite task touches all metadata |
| `manifest.json` | theme color, name | Single task |
| `package.json` | mapbox + r3f + satori + howler | Single install task |
| `Header.tsx` | rewrite + chapter counter + mute + lang | Single rewrite, components imported |
| `Footer.tsx` | rewrite + brand + links | Single rewrite |
| `tokens.ts` (new) | tokens consumers | Single create task |

## Sprint Cx budget

- **Estimated total Cx:** 600–800 (medium-heavy)
- **Task count target:** ~60
- **P0 / P1 / P2:** ~45 / ~12 / ~3
- **Wave count est.:** 3–5 (infra → tokens → everything else)

## Integration points

- Output of W1 → consumed by W2: `useScrollProgress`, `useTimeOfDay`, design tokens, header/footer, edge states, audio scaffold
- Output of W1 → consumed by W3: `useCursorPosition`, `useLiveNow`, `useVariableFontWeight`
- Output of W1 → consumed by W4: all 12 life-layer hooks, edge states, print stylesheet

## Out of scope for W1

- Mapbox map rendering (W2)
- Any chapter component (W2/W3)
- Live Now widget UI on the map (W2 — only the hook is built in W1)
- Carlos avatar / 3D graph (W3)
- Spanish content translation (just toggle scaffold; copy is W4)
- Lighthouse measurement (W4)
- README / press kit / video (W5)

## KANSEI dispatch directive for W1

Every task in W1 MUST be dispatched with full KANSEI 8-section dispatch (see appendix at end of this doc for full skill). Specifically:
- IDENTITY: "Driver agent — frontend foundation specialist"
- INTENT: "Build foundation tokens/hooks/edge-states for The Wall scrollytelling experience"
- WHY: "The Wall depends on a coherent design system; without it, chapters will paint over inconsistent foundations"
- SCOPE: file paths from category, line counts where files exist
- AC: lifted from category templates above
- CONSTRAINTS: 14 permanent constraints
- NEGATIVE: "DO NOT skip the globals.css split. DO NOT add hex colors. DO NOT bypass prefers-reduced-motion. DO NOT introduce new motion library (use existing framer-motion)."
- TEST PATTERNS: existing vitest patterns in `frontend/src/__tests__/` and component-test directories

---

# SPRINT W2 — Mapbox Engine + Chapters 1–5 + Data Layers

## Idea

Stand up the Mapbox foundation, scroll-driven camera system, and Chapters 1 through 5 (Continental → City Arrival → Neighborhood → The Wall (4 sub-chapters) → The Labyrinth). Wire real geographic data: Trinity Metro GTFS routes, Tarrant County offices, FW ZIP boundaries, Carlos's neighborhood pin. **By the end of W2, scrolling the page should fly the camera through real Fort Worth from continent down to neighborhood, with editorial overlays appearing per chapter.**

## Codebase context

- **W1 outputs available:** all design tokens, motion system, hooks, brand assets, edge states, header/footer
- **Existing data sources:** `cities/fort-worth.yaml`, `data/cities/fort-worth/` (resources), Trinity Metro GTFS in `backend/app/integrations/`
- **Mapbox account required:** Shawn must register and provide `NEXT_PUBLIC_MAPBOX_TOKEN`. Custom dark style URL also required (built in Mapbox Studio, ~30 min one-time).
- **react-map-gl** wraps Mapbox GL JS in React; this is the binding we use.

## Sprint-level constraints

**Cross-task arch constraints:**
- New `frontend/src/components/wall/` directory will hold one component per chapter + map subsystem; risks bloating. **CONSTRAINT: each chapter component in its own file under `chapters/`. Camera state extracted to `lib/wall/cameraChoreography.ts`. Data layers extracted to `lib/wall/layers/`.**
- `frontend/src/app/page.tsx` rewrites entirely to render `<WallContainer />`. Pre-existing home page content is replaced.
- Mapbox token must be present in production env; add validation in `WallContainer` for missing token (fall back to static).

**Oversized files prerequisites:**
- None new (W1 already split globals.css)

**Cross-task contract edges within W2:**
- `cameraChoreography.ts` exports per-chapter camera state — consumed by every chapter component
- `lib/wall/paths.ts` exports Carlos's GPS coordinates — consumed by Ch7 in W3
- `lib/wall/layers/{trinityMetro,offices,zipBoundaries,carlosPath}.ts` — each layer is a separate module; imported by `MapboxScene.tsx`
- `WallContainer.tsx` orchestrates scroll + map + chapters; chapters subscribe to scroll progress

## Task categories

```
1. MAPBOX FOUNDATION (P0, ~5 tasks)
   - WallContainer.tsx scaffold (orchestrator)
   - MapboxScene.tsx (react-map-gl integration, custom style URL config)
   - Mapbox token validation + static fallback
   - Mapbox initial camera state (Fort Worth overview as default)
   - Mapbox cleanup on unmount

2. SCROLL + CHAPTER ENGINE (P0, ~6 tasks)
   - lib/wall/cameraChoreography.ts (per-chapter zoom/pitch/bearing)
   - components/wall/ChapterScaffold.tsx (sticky atmosphere + scroll-tied opacity)
   - useChapterProgress hook (which chapter, how far through)
   - Camera flyTo orchestrator (cubic-bezier timing)
   - Reduced-motion fallback (instant cuts instead of fly)
   - useScrollPin (sticky pinning per chapter)

3. DATA LAYERS (P0, ~8 tasks)
   - lib/wall/layers/trinityMetro.ts (GTFS → GeoJSON, real route polylines)
   - lib/wall/layers/offices.ts (Tarrant County office point markers with custom symbols)
   - lib/wall/layers/zipBoundaries.ts (FW ZIP polygons from Census TIGER/Line)
   - lib/wall/layers/carlosPath.ts (GPS coordinates between real locations)
   - lib/wall/layers/jobsByZip.ts (employer markers, color-coded by fair-chance status)
   - lib/wall/layers/index.ts (composer)
   - Custom marker symbols (SVG sprites for office, transit, job)
   - Layer style follows design tokens (no hardcoded color)

4. CHAPTER 1 — CONTINENTAL (P0, ~4 tasks)
   - components/wall/chapters/Chapter01Continental.tsx
   - Camera state: zoom 3, pitch 0, top-down America
   - Editorial overlay: "What's standing between you and a job?" (locked copy)
   - City lights layer (FW + Montgomery brighter)

5. CHAPTER 2 — CITY ARRIVAL (P0, ~4 tasks)
   - Chapter02CityArrival.tsx
   - Camera dolly: zoom 3 → zoom 11, pitch 0 → 60
   - 3D buildings layer fade in
   - Trinity Metro layer fade in (cyan)
   - Editorial overlay locked copy

6. CHAPTER 3 — NEIGHBORHOOD (P0, ~4 tasks)
   - Chapter03Neighborhood.tsx
   - Camera: zoom 14, pitch 60, bearing tilted toward 76119
   - Neighborhood pin (PII-safe representative block, NOT Carlos's exact address)
   - Editorial overlay (60-word Carlos intro)
   - Sound trigger: single footstep on enter

7. CHAPTER 4 — THE WALL (P0, ~10 tasks — 4 sub-chapters × ~2.5 tasks each)
   - Chapter04TheWall.tsx (parent orchestrator)
   - Chapter04aCriminalRecord.tsx (Tarrant County District Clerk pin lit, distance overlay)
   - Chapter04bNoTransit.tsx (Bus 4 highlighted, 87-minute commute drawn)
   - Chapter04cNoChildcare.tsx (HHSC pin, $1,200/mo overlay)
   - Chapter04dBadCredit.tsx (30% job markers go dark)
   - Sub-chapter transitions (camera tilts, layer toggles)
   - Editorial overlays for each (locked copy)
   - Sound triggers per sub-chapter

8. CHAPTER 5 — THE LABYRINTH (P0, ~5 tasks)
   - Chapter05Labyrinth.tsx
   - Camera: zoom 11, pitch 30 (mid-altitude)
   - Animated chaotic path between 5 offices (custom SVG-on-map layer)
   - 47-form counter ticks 0 → 47 with scroll
   - Sound trigger: paper rustle, sequenced

9. MAPBOX STYLE — DARK EDITORIAL (P0, ~3 tasks)
   - Mapbox Studio style document (manual setup, but committed config)
   - Streets, buildings, water, labels styled per design tokens
   - Light + dark variants (dark default; light for /assess and /plan in W3)

10. PAGE.TSX REWRITE (P0, ~2 tasks)
    - frontend/src/app/page.tsx replaces existing landing with <WallContainer />
    - Existing landing content archived to /archive (in case rollback needed)

11. EN/ES COPY POPULATION (P0, ~5 tasks — one per chapter 1–5)
    - en.json: chapter-by-chapter editorial copy from plan file
    - es.json: parallel Spanish translations (high-quality, not Google-translated)

12. ACCESSIBILITY PASS — CHAPTERS 1–5 (P0, ~3 tasks)
    - axe-core scan on each chapter
    - Heading hierarchy verification
    - ARIA-live for camera transitions

13. PERFORMANCE — LAZY LOADING (P0, ~2 tasks)
    - Each chapter component code-split
    - Mapbox style + layers lazy-loaded after title sequence

14. TESTS (P0, ~8 tasks)
    - Camera choreography unit tests (verify state per chapter)
    - Layer composer test (verify all layers register)
    - Chapter render tests (each chapter has its own test)
    - Scroll progression integration test (Playwright preferred)
```

**Total estimated tasks: ~65 at engage time.**

## File collision matrix (within W2)

| File | Touched by | Resolution |
|---|---|---|
| `app/page.tsx` | rewrite + chapter wiring | Single rewrite task; chapters import via WallContainer |
| `WallContainer.tsx` | orchestrator + each chapter | Container scaffolded first; chapters wired serially after |
| `MapboxScene.tsx` | 5 chapters | Scene built once; chapters consume via context |
| `cameraChoreography.ts` | 5 chapters | One file per chapter range; export shared |
| `en.json` / `es.json` | 5 chapters | Each chapter task adds its own keys; merge-friendly |

## Sprint Cx budget

- **Estimated total Cx:** 800–1000 (heavy)
- **Task count target:** ~65
- **P0 / P1 / P2:** ~55 / ~8 / ~2
- **Wave count est.:** 5–7 (Mapbox foundation → scroll engine → layers → chapters in parallel pairs → tests)

## Integration points

- W1 outputs (tokens, hooks, header/footer, edge states) consumed throughout
- W2 outputs (Mapbox foundation, layers, chapters 1–5) consumed by W3 chapters 6–10
- Carlos's path GPS data (`lib/wall/paths.ts`) used by W3 Ch7

## Out of scope for W2

- Cliff calculator inline (W3 Ch6)
- Carlos avatar walking (W3 Ch7)
- 3D barrier graph (W3 Ch8)
- Fly-to-Montgomery (W3 Ch9)
- View transitions to /assess (W3 Ch10)
- Time-of-day Mapbox sky (W4)
- Variable font axis on hero (W4)
- Live Now widget UI (W4 — hook from W1, UI in W4)

## KANSEI dispatch directive for W2

Identical structure to W1, with stage-specific identity ("Driver — Mapbox + scrollytelling specialist") and emphasized DO NOTs:
- DO NOT hardcode Mapbox style colors
- DO NOT skip lazy-loading (LCP budget)
- DO NOT use mock data — real Trinity Metro GTFS
- DO NOT skip reduced-motion fallback
- DO NOT translate Spanish via Google Translate; use the existing es.json voice (formal-but-warm)

---

# SPRINT W3 — Interactive Chapters 6–10 + 3D Graph + View Transitions

## Idea

Build Chapters 6 through 10 — the interactive heart of the Wall. Embed the cliff calculator at Chapter 6 (Amazon FC marker, wage slider drives temperature multiplier). Chapter 7: Carlos avatar walks his real GPS path with footstep audio. Chapter 8: 3D barrier graph constellation hovers over the city using react-three-fiber, edges illuminate as Carlos resolves them. Chapter 9: cross-country fly-to-Montgomery proving the framework. Chapter 10: View Transitions API morphs the map into the assessment form.

## Codebase context

- **W1+W2 outputs available:** full Mapbox engine, chapters 1–5, layers, hooks, tokens
- **Existing components to embed:** `BenefitsCliffChart.tsx` (already built), barrier graph data (backend)
- **react-three-fiber installed in W1:** ready to use for Ch8
- **View Transitions API:** new CSS spec; `frontend/src/components/ViewTransitionsProvider.tsx` already exists but needs route-specific configuration

## Sprint-level constraints

**Cross-task arch constraints:**
- 3D barrier graph (Ch8) MUST be lazy-loaded (Three.js bundle ~150KB). Mount only when Ch8 enters viewport, unmount when it exits.
- View Transitions API has uneven browser support; hard fallback to standard navigation must work.
- Cliff calculator embed (Ch6) must NOT duplicate the existing component; import and re-mount.

**Cross-task contract edges within W3:**
- `BenefitsCliffChart` consumes `--temperature-multiplier` (W1) updated by Ch6 wage slider
- Carlos avatar (Ch7) consumes Carlos's GPS path (W2)
- 3D barrier graph (Ch8) consumes barrier DAG data — needs new endpoint OR build-time JSON import
- Fly-to-Montgomery (Ch9) consumes city configs from `useCityConfig` (W1) and Mapbox style from W2

## Task categories

```
1. CHAPTER 6 — THE MATH (P0, ~6 tasks)
   - Chapter06TheMath.tsx
   - Camera state: fly to Amazon FC DFW5 marker (real coords)
   - BenefitsCliffChart embed (overlay, not standalone page)
   - Wage slider drives --temperature-multiplier (cliff zone shifts amber → rose)
   - Trinity Metro Bus 4 highlighted to DFW5 (71-min commute display)
   - Sound: calculator clicks tied to slider drag

2. CHAPTER 7 — THE PATH + CARLOS AVATAR (P0, ~8 tasks)
   - Chapter07ThePath.tsx
   - Camera: pulls to neighborhood altitude
   - components/wall/CarlosAvatar.tsx (silhouette SVG, animates along path)
   - Sequential path-draw animation (5 segments, week 1/4/8/10/12)
   - Carlos walks in scroll-tied increments, pauses at each office
   - Trinity Metro routes used per leg highlighted
   - Footstep sound tied to scroll progress (rate-limited)
   - Editorial overlay (locked copy)

3. CHAPTER 8 — THE 3D BARRIER GRAPH (P0, ~8 tasks)
   - Chapter08TheGraph.tsx (lazy-loaded entry)
   - components/wall/BarrierConstellation.tsx (react-three-fiber Canvas)
   - Lazy chunk: Three.js bundle isolated
   - Force-directed layout for 33-node DAG (use d3-force or simple physics)
   - Constellation breathes (subtle orbital drift, low frequency)
   - Edges illuminate sequentially as Ch7 path completes
   - Camera tilts up to reveal constellation above city
   - Reduced-motion: still image of constellation

4. CHAPTER 9 — ANY CITY + FLY TO MONTGOMERY (P0, ~6 tasks)
   - Chapter09AnyCity.tsx
   - Camera pulls to America (zoom 3)
   - Two cities lit (FW, Montgomery), 6 dotted (Dallas, Houston, Atlanta, Memphis, Charlotte, Birmingham)
   - "Fly to Montgomery" button with 3-second cross-country flyTo
   - Drop into Montgomery Mapbox style (light variant or alternate)
   - Stat band: 5,189 tests · 13 sprints · 2 cities deployed · MIT
   - Return-to-FW button

5. CHAPTER 10 — FIND YOUR PATH + VIEW TRANSITIONS (P0, ~5 tasks)
   - Chapter10FindYourPath.tsx
   - Camera: back to FW overhead
   - Single primary CTA "Start your assessment" → triggers View Transitions
   - View Transitions API: map zoom-into-Carlos's-home morph into /assess
   - Fallback: if View Transitions unsupported, standard navigation
   - "Or read the open-source code on GitHub →" secondary

6. EN/ES COPY POPULATION (P0, ~5 tasks)
   - en.json + es.json keys for each chapter

7. ACCESSIBILITY (P0, ~5 tasks)
   - axe-core pass per chapter
   - Cliff calc keyboard-reachable
   - 3D graph: keyboard alternate + screen reader description
   - Fly-to-Montgomery button reachable, label clear
   - View Transitions doesn't break focus management

8. PERFORMANCE (P0, ~4 tasks)
   - Lazy-load 3D graph (Three.js)
   - Lazy-load Cliff component (already in /plan; ensure no duplication)
   - Bundle delta measurement post-chapters
   - LCP/CLS check on each chapter

9. TESTS (P0, ~8 tasks)
   - Each chapter render test
   - Cliff slider drives temperature multiplier (integration)
   - Carlos avatar progression (Playwright preferred)
   - Barrier graph mount/unmount lifecycle
   - Fly-to-Montgomery completes
   - View Transitions fallback path

10. INTEGRATION POLISH (P0, ~5 tasks)
    - Chapter transitions (cross-chapter camera fades)
    - Audio sync verification across all 10 chapters
    - Path-line header (W1) progresses correctly through all 10
    - Chapter counter accurate

11. DEFERRED EDGE CASES (P1, ~5 tasks)
    - Mobile fallback: chapters 7, 8, 10 may need static mode
    - Slow 3G test
    - Tab-blur behavior (pause animations when not visible)
    - Long-scroll: no memory leaks
    - User dragging Mapbox manually: ensure scroll handoff
```

**Total estimated tasks: ~65 at engage time.**

## File collision matrix (within W3)

| File | Touched by | Resolution |
|---|---|---|
| `WallContainer.tsx` | adds 5 chapters | Single update task wires all 5 |
| `BenefitsCliffChart.tsx` | Ch6 embeds; existing in /plan | DO NOT modify; import only |
| `en.json` / `es.json` | 5 chapters | Per-chapter add (merge-friendly) |
| `CarlosAvatar.tsx` (new) | Ch7 owns | Single task creates |
| `BarrierConstellation.tsx` (new) | Ch8 owns | Single task creates |

## Sprint Cx budget

- **Estimated total Cx:** 800–1000 (heavy — 3D graph + view transitions are nontrivial)
- **Task count target:** ~65
- **P0 / P1 / P2:** ~55 / ~8 / ~2

## Integration points

- W3 outputs feed W4: every chapter must work with life-layers (time-of-day, cursor, Spanish)
- View Transitions ties to existing `/assess` route
- Cliff calc connects to existing `BenefitsCliffChart` (no duplication)

## Out of scope for W3

- Time-of-day lighting (W4)
- Spanish content polish (W4 audit)
- Variable font on headings (W4)
- Per-chapter dynamic OG (W4)
- Live Now widget on map (W4)
- Final Lighthouse measurement (W4)

## KANSEI dispatch directive for W3

Identity: "Driver — interactive 3D + scroll specialist". Emphasized DO NOTs:
- DO NOT duplicate `BenefitsCliffChart` — import the existing component
- DO NOT skip lazy-loading the 3D graph (Three.js is heavy)
- DO NOT skip View Transitions fallback (browser support is partial)
- DO NOT trap user in scroll-driven animations (let user override with manual map drag)

---

# SPRINT W4 — 12 Life-Layers + Spanish Parity + Performance + Accessibility Gate

## Idea

The site is technically complete after W3. W4 makes it **alive** — the 12 life-layers from the plan + Spanish parity + the Lighthouse 90+ hard gate. **By the end of W4, the page plays differently for every user.**

Time-aware city lighting. Cursor flashlight on map. Live Now widget rendering real-time data. Variable font axis on hero. Per-chapter dynamic OG via Vercel Satori. View Transitions polish. Spanish toggle full re-skin (audio if recorded). Custom 404/500/empty/loading wired everywhere. Print stylesheet active. Reduced-motion verified. WCAG AAA contrast pass. Keyboard navigation full sweep. Lighthouse 90+ on simulated 4G.

## Codebase context

- **W1–W3 outputs available:** entire 10-chapter Wall live; foundation, hooks, brand all in place
- **Backend:** may need a small `/api/now` endpoint or compute live data client-side
- **Vercel Satori:** installed in W1; per-chapter OG endpoint is new

## Sprint-level constraints

**Cross-task arch constraints:**
- Live Now widget polls `/api/now` or computes locally — decision needed first task
- Spanish parity is a SWEEP — every editorial string in en.json must have ES counterpart
- Per-chapter OG via Satori requires `/api/og/[chapter]/route.ts` — new directory

**Cross-task contract edges:**
- Time-of-day output → Mapbox sky setter + accent color shift + variable font weight
- Live Now → header widget AND Chapter 9 stat band
- Spanish toggle → every chapter component re-renders with localized copy
- View Transitions polish → also affects /assess page (W2 already wired the boundary)

## Task categories

```
1. TIME-AWARE SYSTEM (P0, ~5 tasks)
   - Mapbox sky.skyType setter from useTimeOfDay output
   - Accent color shift token application (--accent-current)
   - Sun position calculation (latitude-aware for FW/Montgomery)
   - Smooth transitions between time phases (cron-based, not instant)
   - Reduced-motion: instant time-phase swap

2. CURSOR FLASHLIGHT ON MAP (P0, ~3 tasks)
   - Wire CursorFlashlight (W1) to MapboxScene
   - Adjust map element opacity based on cursor proximity
   - Reduced-motion / no-pointer fallback (always full opacity)

3. LIVE NOW WIDGET (P0, ~5 tasks)
   - Decide: /api/now endpoint OR client-side computation
   - Header bar UI displays time + sessions + last calibration
   - Time format respects user locale
   - 10s polling with TanStack Query
   - Visible-only-when-needed (hide on Ch1 hero for cleanliness)

4. VARIABLE FONT AXIS ON HEADLINES (P0, ~4 tasks)
   - useVariableFontWeight (W1) wired to hero headline
   - Weight interpolates 700 → 900 with scroll progress
   - Optical-size axis at large display sizes
   - Each chapter heading uses the system

5. PER-CHAPTER DYNAMIC OG (P1, ~4 tasks)
   - app/api/og/[chapter]/route.ts using Vercel Satori
   - Renders chapter title + locked copy on dark gradient
   - Uses brand mark + path mark
   - Linked from per-chapter URL fragments

6. SPANISH PARITY SWEEP (P0, ~10 tasks)
   - Audit every editorial string in en.json
   - Translate to es.json with native-fluent voice (not literal)
   - Locale-aware EN/ES toggle in header (persists in localStorage)
   - Every chapter component re-renders correctly with ES copy
   - Audio: defer ES narration unless time permits (P2)

7. CUSTOM 404 / 500 / EMPTY / LOADING WIRING (P0, ~3 tasks)
   - Verify W1 components are correctly wired in Next.js conventions
   - Test 404 by visiting bogus URL
   - Test 500 by triggering error boundary
   - Empty state used by chapters with no data

8. PRINT STYLESHEET POLISH (P1, ~2 tasks)
   - Verify magazine layout renders cleanly
   - Test with browser print preview

9. REDUCED-MOTION SWEEP (P0, ~5 tasks)
   - Audit every animation site for prefers-reduced-motion respect
   - Provide still-image fallback for camera flights
   - Provide static path-draw for Carlos avatar
   - Static constellation for 3D graph

10. WCAG AAA CONTRAST PASS (P0, ~3 tasks)
    - Run axe-core on every chapter (full sweep)
    - Run scripts/verify-contrast.mjs (W1) across all token combos
    - Fix any AAA failures (likely in muted text + glass cards)

11. KEYBOARD NAVIGATION FULL SWEEP (P0, ~4 tasks)
    - Tab order through every interactive (header → chapters → footer)
    - Focus visible on every focusable
    - Skip-to-content link works
    - Keyboard alternate for cursor flashlight (focus-driven)

12. SCREEN READER PASS (P0, ~3 tasks)
    - VoiceOver on macOS sweep
    - NVDA simulation
    - ARIA-live regions firing correctly on chapter transitions

13. LIGHTHOUSE 90+ HARD GATE (P0, ~5 tasks)
    - Run Lighthouse on production build, simulated 4G
    - Audit LCP, CLS, TBT, TTI
    - Descope per priority order if score < 90 (audio → temperature multiplier → 3D graph → view transitions)
    - Re-measure after each descope
    - Document final score in PR description

14. MOBILE FALLBACK VERIFICATION (P0, ~4 tasks)
    - Detect mobile via window.innerWidth + Mapbox-supported flag
    - Tablet: scaled map experience
    - Mobile: static images of map + editorial scroll
    - Critical: NEVER broken; always graceful

15. SCROLL-VELOCITY REACTIVE (P1, ~2 tasks)
    - Motion-blur on background at velocity > threshold
    - Disabled with reduced-motion

16. IDLE STATE (P1, ~2 tasks)
    - After 30s no input, ambient drift on barrier graph + path-line pulse
    - Stops on any input

17. TESTS (P0, ~10 tasks)
    - Time-of-day visual regression
    - Spanish toggle re-renders all chapters
    - Live Now polling
    - Variable font weight interpolates
    - Lighthouse threshold via CI
    - Keyboard navigation Playwright
    - Reduced-motion fallbacks
```

**Total estimated tasks: ~70 at engage time.** (Slightly above 60 — descope idle state or scroll-velocity to P2 if needed.)

## File collision matrix (within W4)

| File | Touched by | Resolution |
|---|---|---|
| `MapboxScene.tsx` | time-of-day sky, cursor flashlight | Single update task per concern |
| `useTimeOfDay.ts` | sun position, smooth transition | Single hook update task |
| `en.json` / `es.json` | Spanish parity sweep | One PR audit, then one task per chapter pair |
| `Header.tsx` | Live Now widget | Single task adds widget |

## Sprint Cx budget

- **Estimated total Cx:** 600–800 (medium-heavy)
- **Task count target:** ~70 (descope to ~60 if idle/scroll-velocity drop to P2)
- **P0 / P1 / P2:** ~55 / ~10 / ~5

## Integration points

- W4 outputs all roll into W5 submission materials (screenshots show life-layers active)

## Out of scope for W4

- README rewrite (W5)
- Press kit refresh (W5)
- Submission video (W5)

## KANSEI dispatch directive for W4

Identity: "Driver — accessibility + life-layers specialist". Emphasized DO NOTs:
- DO NOT skip prefers-reduced-motion respect
- DO NOT translate Spanish via machine; use existing es.json voice
- DO NOT regress Lighthouse score; descope animations if needed
- DO NOT block keyboard users
- DO NOT use placeholder Carlos data — real fixtures from `docs/demo-script.md`

---

# SPRINT W5 — Submission Materials (README, Press Kit, Video, Devpost)

## Idea

The home page IS the artifact. W5 packages it for HackFW. README opens with a Wall screenshot, leads with the locked copy thesis. Press kit refreshes to current numbers (5,189 tests, FW positioning, MIT, demo URLs). Submission video is a screen recording of the Wall scroll with voiceover — essay IS the script. Devpost submission text + tags. Final smoke + Lighthouse final pass + deploy to staging.

## Codebase context

- **W1–W4 outputs available:** the entire Wall, polished, performant
- **Existing docs to refresh:** `README.md`, `docs/press-kit.md`, `docs/press-kit/`, `docs/submission-demo.md`
- **Existing demo script:** `docs/demo-script.md` (Carlos persona) — useful for video voiceover
- **Backend:** unchanged in W5 (mostly docs/video work)

## Sprint-level constraints

- README is the FIRST thing judges read per Devpost rule. Lead with copy thesis and Wall screenshot.
- Video must be 3–4 minutes. Compression target: < 50MB. Captions required.
- Press kit must drop stale "1,808 tests" and Worldwide-Vibes-as-headline; reposition WV as supporting credit.

## Task categories

```
1. README REWRITE (P0, ~5 tasks)
   - Hero section: copy thesis + Wall screenshot
   - "What it is" paragraph: lifted from plan file
   - "Quick start" updated for current dependencies (mapbox, r3f, satori)
   - HackFW positioning (Reindustrialization track, workforce augmentation)
   - "Built with" credit (PairCoder, Claude, team)

2. PRESS KIT REFRESH (P0, ~6 tasks)
   - docs/press-kit.md: full rewrite with FW positioning
   - Test counts updated to 5,189
   - Cinematic stills from Chapters 2, 6, 7, 8 (screenshot Wall)
   - Worldwide Vibes credited as supporting (not headline)
   - Team section updated
   - GitHub link, MIT license, contact

3. SUBMISSION DEMO SCRIPT UPDATE (P0, ~4 tasks)
   - docs/submission-demo.md: Wall walkthrough overlay
   - Beat timing locked to chapter transitions
   - Backup paths preserved
   - Pre-demo checklist with Mapbox token check

4. SUBMISSION VIDEO (P0, ~6 tasks)
   - Video script lifted from Wall editorial copy
   - Voiceover script (90 seconds intro + 3min walkthrough)
   - Screen recording: scroll the Wall on desktop (1920×1080 60fps)
   - Multiple takes for camera flights (Chapter 9 fly-to-Montgomery especially)
   - Captions (.srt or burned-in)
   - Final video < 4 min, < 50MB

5. DEVPOST SUBMISSION CONTENT (P0, ~4 tasks)
   - Project description (lift from README first paragraph)
   - Tags / categories: Workforce, AI/ML, Civic Tech, Open Source, Reindustrialization
   - Team members
   - Built with: Next.js, Mapbox, Three.js, FastAPI, Python 3.13, etc.
   - Inspiration / What we learned / Challenges sections

6. PER-CHAPTER OG IMAGES (P1, ~3 tasks)
   - Verify W4 dynamic OG endpoints work
   - Generate static fallback OG images for every chapter (in case Satori fails)
   - Upload to /public/og/

7. FINAL POLISH PASSES (P0, ~5 tasks)
   - Re-run Lighthouse on production build
   - Final accessibility sweep
   - Cross-browser test (Chrome, Safari, Firefox, Edge)
   - Mobile devices (iPhone, Android) test
   - Slow 3G simulation

8. DEPLOYMENT (P0, ~5 tasks)
   - NEXT_PUBLIC_MAPBOX_TOKEN in production env (Vercel)
   - Custom Mapbox style URL in production
   - Deploy to staging
   - Smoke test staging
   - Production deploy or final staging URL for Devpost

9. FW DAO BOUNTY RESEARCH (P1, ~3 tasks)
   - Investigate `dao.fwtx.city/bounties` portal
   - Identify any workforce-related bounties
   - Document claim path if applicable

10. SUBMISSION CHECKLIST + BUFFER (P0, ~4 tasks)
    - Devpost form filled
    - GitHub repo public
    - README polished
    - Video uploaded
    - Final smoke
    - SUBMIT before May 2, 2:00 PM CDT

11. POST-SUBMISSION (P1, ~3 tasks)
    - Reddit post draft (existing in docs/press-kit/)
    - Social media announcement
    - Backup of submission state to git tag (e.g., `v0.1.0-hackfw-submission`)

12. TESTS (P1, ~3 tasks)
    - README links validated (no broken)
    - Press kit images load
    - OG image endpoints respond
```

**Total estimated tasks: ~50 at engage time.** Lower than other sprints because most work is documentation/video, not code.

## File collision matrix (within W5)

Minimal collisions — most tasks touch separate documentation files. Video record is a single multi-take task; multiple takes don't collide because they output to different filenames.

## Sprint Cx budget

- **Estimated total Cx:** 400–600 (medium)
- **Task count target:** ~50
- **P0 / P1 / P2:** ~35 / ~12 / ~3

## Integration points

- W5 closes the loop: README, video, press kit, Devpost all reference and showcase the Wall built in W1–W4.

## Out of scope for W5

- New code in /frontend or /backend (build is done at W4)
- New design changes (W4 was the polish gate)

## KANSEI dispatch directive for W5

Identity: "Driver — submission readiness specialist". Emphasized DO NOTs:
- DO NOT regress test count display
- DO NOT submit before Lighthouse final pass
- DO NOT edit video after Devpost upload (unless rebuilding from scratch)
- DO NOT forget the May 2 2:00 PM CDT deadline buffer (submit by 9 AM, not 1 PM)

---

# Dispatch instruction for Shawn

To launch the build sequence:

```bash
# For each sprint W1 → W5, in order:
/draft-backlog docs/visual-rebirth-briefs.md  # use the relevant W# section

# Then per sprint:
bpsai-pair engage <generated-backlog-file>
# OR
/start-task <task-id>  # to step through tasks individually

# KANSEI dispatch is automatic per-task during engage.
# The skill at C:\Dev\INERTIA-SERVICE\.claude\skills\kansei-no-keiyaku\SKILL.md
# is the dispatch quality standard. PairCoder injects this at engage time.
```

Recommended order:
1. Hand W1 brief to /draft-backlog → get backlog → engage W1 → merge or branch-checkpoint
2. Repeat for W2 → W3 → W4 → W5
3. May 2 morning: final smoke + submit

Each sprint is its own commit-able branch off `sprint/visual-rebirth`, OR all sprints are stacked sequentially on the same branch. Recommend stacking on `sprint/visual-rebirth` and merging to main only at W5 completion.

---

# APPENDIX A — Full KANSEI NO KEIYAKU skill

For dispatch-time injection. Source: `C:\Dev\INERTIA-SERVICE\.claude\skills\kansei-no-keiyaku\SKILL.md`.

> KANSEI NO KEIYAKU — The Covenant of Inertia
> *"I will give you everything you need. You will deliver A+ work. Neither of us breaks this pact."*
>
> The dispatch is a CONTRACT. The agent receives complete context. The agent delivers complete work. Neither side breaks the pact.
>
> **8 non-negotiable sections** (every dispatch must include):
> 1. IDENTITY — stage-appropriate role description
> 2. INTENT + WHY — sprint intent + 50+ char rationale
> 3. SCOPE — exact file paths with line counts + headroom
> 4. ACCEPTANCE CRITERIA — testable checkboxes (≥2 items)
> 5. CONSTRAINTS — 95% coverage, TDD, <400 lines, <50 line fns
> 6. NEGATIVE CONSTRAINTS — battle scars, DO NOT list
> 7. TEST PATTERNS — exemplar test file reference
> 8. DEPENDENCY GRAPH — what blocks what, with status
>
> **7 adaptive sections** (included based on sprint type/complexity):
> 9. Exploration results (feature sprints)
> 10. Algorithm specs (when AC references algorithms)
> 11. Prior stage context (when Death Note active)
> 12. Engage configuration (Stage 7 parallel HeadlessSession)
> 13. Smart scope content (complex tasks: imports + signatures)
> 14. Reviewer notice (code-producing stages 3+)
> 15. Forge status (remaining gates awareness)
>
> **10-point validation gate** (every dispatch runs through this; BLOCK = rejected):
> 1. IDENTITY section present (BLOCK)
> 2. INTENT + WHY with >50 char rationale (BLOCK)
> 3. SCOPE with file paths (BLOCK)
> 4. AC with ≥2 checkboxes (BLOCK)
> 5. CONSTRAINTS section present (BLOCK)
> 6. NEGATIVE CONSTRAINTS with DO NOT items (BLOCK)
> 7. TEST PATTERN reference (BLOCK)
> 8. Total length ≥1500 chars (BLOCK)
> 9. Total length ≤80000 chars (WARN — trim adaptives)
> 10. Sprint type declared (WARN)
>
> **Permanent constraints (Shawn's non-negotiables, every dispatch):**
> 1. 95% test coverage on new code
> 2. TDD ONLY — failing test first, then implement
> 3. Nothing over 400 lines — architecture limit enforced
> 4. Functions under 50 lines — extract helpers
> 5. Max 15 functions per file — hub-and-spoke decomposition
> 6. Full wiring — nothing orphaned, everything connected
> 7. No code debt — every sprint ships clean
> 8. ZERO LLM calls (in INERTIA; for GoWork: zero LLM in Wall render path)
> 9. bpsai-pair arch check must pass before completion
> 10. Reviewer agent reviews all code-producing stages
>
> **Sprint type adaptation:**
> - feature: all 8 + exploration + algorithm specs (deep)
> - bugfix: all 8 (test pattern WARN not BLOCK) (standard)
> - refactor: all 8 + architecture headroom emphasis (standard)
> - chore: all 8 (lighter scope) (light)
>
> **Anti-patterns to avoid:**
> 1. Lazy one-liner dispatch
> 2. Missing WHY
> 3. No negative constraints
> 4. Stale scope data
> 5. No test exemplar
> 6. Skipping validation
> 7. Over-trimming for token budget

---

# APPENDIX B — Sources

- `docs/visual-rebirth-plan.md` — design DNA (10 chapters, 12 life-layers, system tokens)
- `docs/demo-script.md` — Carlos persona reference
- `cities/fort-worth.yaml` — city configuration
- `frontend/src/lib/translations/{en,es}.json` — existing i18n
- `frontend/src/components/plan/BenefitsCliffChart.tsx` — existing cliff component (Ch6 embed)
- `C:\Dev\INERTIA-SERVICE\.claude\skills\kansei-no-keiyaku\SKILL.md` — dispatch quality standard
- `.claude/skills/ideation/SKILL.md` — this brief follows that format
- `.claude/commands/draft-backlog.md` — receives this brief
- `.claude/commands/pc-plan.md` — runs per-task during engage

---

慣性の契約. The dispatch is a contract. Both sides deliver. **The Wall · April 2026 · GoWork team.**
