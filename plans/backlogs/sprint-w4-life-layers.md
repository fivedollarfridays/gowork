# Sprint W4 — 12 Life-Layers + Spanish Parity + Performance + Accessibility Hard Gate

**Plan type:** feature
**Sprint:** W4
**Total Cx:** 604 (P0: 546, P1: 54, P2: 4)
**Tasks:** 74 (P0: 65, P1: 8, P2: 1)
**Branch base:** `sprint/visual-rebirth` (after W3 merge)
**HackFW deadline gate:** May 2, 2:00 PM CDT — W4 closes the build before W5 packaging

## Goal

The site is technically complete after W3 (all 10 chapters live). W4 makes it **alive**. Time-aware city lighting (Mapbox sky + accent shifts based on user's local time). Cursor flashlight on map (80px glow circle). Live Now widget (real-time time + sessions + last calibration). Variable font axis on hero (Inter Variable weight 700→900 interpolates with scroll). Per-chapter dynamic OG via Vercel Satori. **Spanish parity sweep** (every editorial string from W2 + W3 has an es.json counterpart with native-fluent voice; Fort Worth is 35% Hispanic — civic dignity is the design driver). Custom 404/500/empty/loading wired everywhere. Print stylesheet active. Reduced-motion verified. WCAG AAA contrast pass. Keyboard navigation full sweep. Screen reader pass. **Lighthouse 90+ on simulated 4G is the HARD GATE.**

## Mission framing

GoWork is barrier-removal infrastructure for any American city. The Wall is "an instrument that plays differently for every user" — time-aware, cursor-aware, data-aware, language-aware, ability-aware. W4 makes that instrument real. Judges grade on Technical Readiness, Novelty for FW Ecosystem, Tech Debt, and Code Cleanliness — accessibility + performance + i18n parity are direct evidence of all four. After W4, screenshots and video footage for W5 will show life-layers active (golden-hour FW, Spanish toggle in header, AAA contrast everywhere).

## What ships in W4 vs descope ladder

**W4 (this sprint):** 12 life-layers wired (time-of-day, cursor flashlight on map, Live Now widget, variable font axis, per-chapter OG, view-transition polish, custom edge states wired, print stylesheet polish, reduced-motion sweep, WCAG AAA pass, keyboard nav sweep, Spanish parity sweep), Lighthouse 90+ gate, mobile fallback verification, screen reader pass, scroll-velocity reactive (P1), idle state (P1).

**Descope ladder (apply if Lighthouse < 90 on simulated 4G):**
1. Drop sound system / audio narration assets (~10KB)
2. Drop `--temperature-multiplier` motion shifts (revert to static accent)
3. Drop 3D barrier graph (Chapter 8) — replace with 2D SVG fallback
4. Drop view transitions to /assess (revert to standard Next.js navigation)
5. **KEEP no matter what:** Mapbox foundation, Carlos avatar, all 10 chapters, Spanish toggle, all 10 chapters' editorial copy

**Out of W4 scope (deferred to W5 or later):** README rewrite, press kit refresh, submission video, Devpost form, Storybook scaffold (post-hackathon), backend ML changes, schema migrations.

## Architectural principles

- **Permanent constraints (every task):** 95% test coverage on new code; TDD only (failing test first); files <400 lines, functions <50 lines, max 15 functions per file, max 20 imports; full wiring, nothing orphaned; ZERO LLM calls in the Wall render path; `bpsai-pair arch check` must pass; reviewer agent review required.
- **prefers-reduced-motion respected at every animation site.** W4 enforces this — every animation task has an explicit reduced-motion AC line.
- **WCAG AAA contrast everywhere.** W4 verifies this with axe-core + a token-pair contrast script.
- **Brand:** GoWork only. No "MontGoWork" leakage in any new copy.
- **Slogan locked:** see `docs/visual-rebirth-plan.md` "Decisions LOCKED". Do not redraft.
- **Lighthouse 90+ on simulated 4G is the hard gate.** If we miss, descope per the ladder above.
- **Backend untouched** in W4 — exception: a tiny `/api/now` endpoint MAY be added if T4.6 decision selects server-side computation. Surface this as a design escalation in T4.6.
- **Spanish translations are not machine-translated.** Use the existing `es.json` voice (formal-but-warm) as the style reference. Each chapter pair's translation is reviewed by reviewer agent against the EN source for tone, register, and dignity. C4 confidence: no native speaker on team — we accept the risk and document it.

## Decisions locked (2026-04-27, this sprint)

1. **Live Now widget data source** — decision deferred to T4.6 (first task in Live Now block); choices are a tiny `/api/now` backend endpoint OR client-side computation from existing data. T4.6 picks one and the rest of the block builds against it.
2. **Spanish translation review** — reviewer agent + Shawn read each chapter pair before sign-off. Confidence C4 documented.
3. **Mobile fallback** — chapters 7, 8, 10 (Carlos avatar, 3D graph, view transitions) drop to static images on `window.innerWidth < 768` OR Mapbox-supported flag false. Graceful degradation, never broken.
4. **Reduced-motion HOC vs inline** — extract a `withReducedMotion` HOC (T4.49) so every chapter component uses the same fallback path. Applies the Wisdom lens from Spotlight.
5. **OS-language auto-detect** — on first load, if user's `navigator.language` starts with `es`, default toggle to ES (T4.27 + T4.28). High-empathy task; surfaced from Spotlight Multiple-Selves lens.
6. **Compound life-layers integration test** — verify all 12 layers firing simultaneously do not conflict (T4.69 + T4.70). Cliff slider must work while time-of-day shifts AND cursor flashlight AND variable font are active.

---

## File collision matrix (within W4)

The Wall touches these files repeatedly. Engage should serialize them; cross-task collisions are flagged with **(serialize)**.

| File | Tasks touching it | Resolution |
|---|---|---|
| `frontend/src/lib/wall/timeOfDay.ts` | T4.1, T4.2, T4.3, T4.4 | **(serialize)** Single hook update task per concern; T4.1 first |
| `frontend/src/components/wall/MapboxScene.tsx` | T4.1, T4.7, T4.8, T4.69 | **(serialize)** Each life-layer adds one effect hook block |
| `frontend/src/lib/translations/en.json` | T4.20–T4.29 | Each chapter pair adds its own keys (merge-friendly), but pairs serialize within their chapter |
| `frontend/src/lib/translations/es.json` | T4.20–T4.29 | Same as en.json |
| `frontend/src/components/layout/Header.tsx` | T4.10 | Single update task adds Live Now widget node |
| `frontend/src/app/layout.tsx` | T4.16, T4.30 | T4.16 metadata + T4.30 OG link tags merge — **(serialize)**; T4.16 first |
| `frontend/src/app/globals.css` | T4.43, T4.44, T4.45 | Each adds its own `@media (prefers-reduced-motion: reduce)` block; serial |
| `frontend/src/lib/wall/perfBudget.ts` (new) | T4.55, T4.59, T4.60 | Single create then read-only consumers |
| `frontend/src/components/wall/withReducedMotion.tsx` (new) | T4.49 | Single create; downstream chapters import |
| `frontend/lighthouserc.json` | T4.55 | Single update task tightens 4G threshold |

---

## Cross-task contract edges (W4 internal)

- `useTimeOfDay` (W1) → `getMapboxSkyConfig(phase)` + `getAccentForPhase(phase)` — consumed by T4.1 (Mapbox sky), T4.4 (accent shift), T4.13 (variable font weight optionally tinted)
- `useCursorPosition` (W1) → consumed by T4.7 (cursor flashlight on map) and T4.61 (idle detector — no cursor for 30s = idle)
- `useLiveNow` (W1) → consumed by T4.10 (header widget) and T4.11 (Chapter 9 stat band live re-render)
- `useVariableFontWeight` (W1) → consumed by T4.12, T4.13, T4.14, T4.15 (every chapter heading)
- `withReducedMotion` HOC (T4.49) → consumed by all chapter components (T4.43–T4.48)
- `lib/wall/perfBudget.ts` (T4.55) → consumed by T4.59 (LCP budget enforcement), T4.60 (CLS budget), T4.55 itself (Lighthouse threshold)
- Spanish toggle (T4.27) → consumed by every chapter's `useTranslation()` call; OS-language detect (T4.28) sets initial state

---

## Spotlight Inventions (≥3, mandated)

These tasks are NOT in the original 17-category brief. They emerged from the 5 Awakening Conditions + 5 Lenses applied during planning.

1. **T4.28 — OS-language auto-detect on first load** (Multiple-Selves: Maria, Spanish-speaker visiting at 7am, deserves the page in Spanish without hunting for a toggle). Reads `navigator.language`; if starts with `es-`, sets initial locale to ES, persists choice. High-empathy fusion task (Spanish toggle × OS detect = automatic dignity).

2. **T4.49 — `withReducedMotion` HOC extraction** (Wisdom lens: extract reduced-motion fallback HOC so every chapter component uses it instead of duplicate inline checks). Single source of truth for animation gating; refactors all chapter components to consume it. Reduces duplication and prevents reduced-motion regressions in future chapters.

3. **T4.55 — `lib/wall/perfBudget.ts` explicit thresholds module** (Structural lens: descope priority isn't fully wired; add explicit perf budget thresholds module). Centralizes LCP / CLS / TBT / TTI / bundle-size thresholds; T4.59 + T4.60 + Lighthouse CI consume it. Without this, descope decisions are ad-hoc; with it, descope is data-driven.

4. **T4.69 + T4.70 — Compound life-layers integration test** (Compound lens: what's the COMPOUND interaction of all 12 life-layers active simultaneously? Add an integration test that verifies they don't conflict — e.g., temperature multiplier × variable font axis × cursor flashlight all firing on the cliff slider). Without this, chapters appear to work in isolation but break in production when a user scrolls fast at 7pm with Spanish toggle on.

5. **T4.62 — KSAO-aware error copy in custom 404/500** (Honesty lens, beyond brief: every visible error must serve the worker, not the engineer; copy uses anticipatory tone consistent with Carlos's experience — "There's no path to this URL, but there's still a path for you. Start here.")

6. **T4.42 — Print stylesheet smoke test in CI** (Legacy lens, beyond brief: print is a legitimate accessibility surface; without a smoke test it bitrots. CI runs Playwright print preview and asserts page count + heading hierarchy.)

7. **T4.65 — Latitude calibration unit test for FW vs Montgomery sun position** (Multiple-Selves + Honesty: the 0.4° latitude difference matters for verisimilitude; without a test it's unverifiable.)

---

## Honest Uncertainty (C-rating where applicable)

| Uncertainty | Confidence | Mitigation |
|---|---|---|
| Lighthouse 90+ on simulated 4G achievable with all 12 life-layers active | **C5 (low)** | Measure pre-life-layers (T4.55 baseline) and post (T4.66 final). Descope ladder applied if miss. Budget surfaced explicitly in T4.55. |
| Spanish translation review without native speaker on team | **C4 (medium)** | Reviewer agent reads each pair against EN source for tone consistency. Shawn second-pass. T4.20–T4.26 each has reviewer-approved gate. |
| Per-chapter OG generation reliability under judging-day load | **C5 (low)** | Static fallback OG images generated at build-time (T4.32). Satori endpoint has graceful failure to static. |
| `/api/now` backend addition vs client-side computation tradeoff | **C3 (decided in T4.6)** | T4.6 makes the call after measuring; rest of block follows. |
| Reduced-motion fallback for 3D barrier graph (Chapter 8) renders well | **C4 (medium)** | Static screenshot of constellation as PNG fallback prepared in T4.46. Visual review by Shawn. |
| Variable font axis renders smoothly across browsers (Safari font-variation-settings quirks) | **C4 (medium)** | Cross-browser test (T4.67) on Safari + Firefox; fallback to weight 800 if interpolation fails. |
| Mobile fallback for chapters 7, 8, 10 visually acceptable on $50 Android | **C5 (low)** | T4.51 + T4.52 + T4.53 each verifies; if a chapter looks broken, mobile users see static image + editorial scroll. |
| Compound life-layer interaction (12 layers firing simultaneously) | **C4 (medium)** | T4.69 + T4.70 integration test; if conflicts surface, isolate the offending pair and add a feature flag. |

---

## Phase 1: Time-Aware System (5 tasks, 44 Cx)

### T4.1 — Time-aware Mapbox sky setter | Cx: 12 | P0

**Description:**
Wire `useTimeOfDay` hook (W1) to Mapbox `sky.skyType` setter on `MapboxScene.tsx`. Map's sky atmosphere shifts smoothly between 4 phases (morning, day, evening, night) based on user's local time. Each phase has accent color override (`--accent-current` CSS variable). Latitude-aware sun position calculation: Fort Worth (32.7555°N) and Montgomery (32.3792°N) use slight latitude difference (~0.4°). Reduced-motion: instant phase swap, no smooth transition.

**AC:**
- [ ] `frontend/src/lib/wall/timeOfDay.ts` exports `getMapboxSkyConfig(timePhase)` returning Mapbox sky-layer config
- [ ] `frontend/src/lib/wall/timeOfDay.ts` exports `getAccentForPhase(timePhase)` returning hex/oklch token
- [ ] `MapboxScene.tsx` subscribes to `useTimeOfDay` and updates sky layer on phase change
- [ ] Smooth transition uses framer-motion spring `--spring-soft` (NOT instant) when reduced-motion is OFF
- [ ] Reduced-motion: instant phase swap (no transition)
- [ ] WCAG AAA contrast verified for `--fg-primary` on each phase's accent (manual + script check via T4.40)
- [ ] Vitest: 4-phase transitions, reduced-motion fallback, accent override, latitude-difference assertion (FW vs Montgomery sun positions differ by ≥0.4°)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `useTimeOfDay` hook, W2 `MapboxScene.tsx`

---

### T4.2 — Sun position calculation (latitude-aware) | Cx: 6 | P0

**Description:**
Implement `calculateSunPosition(lat, lon, datetime)` in `lib/wall/timeOfDay.ts` returning `{azimuth, elevation}` for Mapbox sky.sun-position. Use NOAA-equivalent formula (no external API call — deterministic). Verify FW (32.7555°N) and Montgomery (32.3792°N) produce different sun positions at the same UTC instant.

**AC:**
- [ ] `calculateSunPosition(lat, lon, date)` exported
- [ ] Returns `{azimuth: 0-360, elevation: -90 to 90}`
- [ ] Pure function (no I/O, deterministic, no LLM)
- [ ] Vitest: known-instant assertions for FW noon, Montgomery noon, both at midnight (sun below horizon)
- [ ] Vitest: latitude difference of ≥0.4° between FW and Montgomery at the same UTC instant
- [ ] No external API calls (verified via test mock)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.3 — Smooth time-phase transitions (cron-based, not instant) | Cx: 10 | P0

**Description:**
When the user's local time crosses a phase boundary (e.g., evening → night at 21:00), the Mapbox sky must transition smoothly over 30s, NOT instantly snap. Implement transition queue in `useTimeOfDay`: when phase boundary detected, schedule a 30s tween of sky parameters. Reduced-motion: skip tween, snap.

**AC:**
- [ ] `useTimeOfDay` exposes `phase` and `transitioning: boolean`
- [ ] On phase boundary, `transitioning=true` for 30s
- [ ] Mapbox sky parameters interpolate during transition (cubic-bezier easing per design tokens)
- [ ] Reduced-motion: snap (no tween), `transitioning` always false
- [ ] Vitest: phase boundary fires transition, transition duration is 30s, reduced-motion bypass
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.1, T4.2

---

### T4.4 — Accent color shift token application | Cx: 6 | P0

**Description:**
On phase change, set CSS variable `--accent-current` on `<html>` to the phase-specific accent (morning=warm amber, day=cyan, evening=rose, night=deep cyan). Every component referencing `--accent-current` re-renders with new tint. Verify ALL existing references work; if any component uses a hardcoded `--accent-cyan`, refactor to `--accent-current`.

**AC:**
- [ ] CSS variable `--accent-current` set on `<html>` element by `useTimeOfDay` effect
- [ ] All 4 phases produce visibly different accents (snapshot test)
- [ ] No hardcoded `--accent-cyan` remains in chapter components (grep audit)
- [ ] WCAG AAA contrast verified for `--fg-primary` over each accent (script check)
- [ ] Vitest: phase change updates `--accent-current`; component using token re-renders
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.1

---

### T4.5 — Reduced-motion: instant time-phase swap | Cx: 4 | P0

**Description:**
Codify the reduced-motion fallback for the entire time-aware system in one place. When `prefers-reduced-motion: reduce` is set, the smooth tween in T4.3 is bypassed, the accent in T4.4 snaps, and Mapbox sky is set instantly. Verify with Playwright + emulated reduced-motion.

**AC:**
- [ ] Playwright test sets `prefers-reduced-motion: reduce` and asserts no transition class on `<html>` during phase boundary
- [ ] Vitest unit: `useTimeOfDay` returns `transitioning: false` when matchMedia returns reduce
- [ ] Manual smoke documented in PR description
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.3, T4.4

---

## Phase 2: Cursor Flashlight on Map (3 tasks, 20 Cx)

### T4.7 — Wire CursorFlashlight to MapboxScene | Cx: 10 | P0

**Description:**
Wire `CursorFlashlight` component (W1) to `MapboxScene.tsx` as a soft 80px glow circle following the cursor. Elements within the circle (Mapbox markers, layers) brighten by ~15% opacity; elements outside dim by ~10%. Active only on chapters where the map is the primary visual (1, 2, 3, 4, 5, 6, 7, 9). Reduced-motion: flashlight static center, no follow.

**AC:**
- [ ] `MapboxScene.tsx` mounts `<CursorFlashlight />` only on map-primary chapters
- [ ] Glow circle is 80px diameter, soft cyan with 0.4 alpha
- [ ] Markers within glow brighten (manual visual + snapshot diff)
- [ ] Markers outside glow dim by ~10% (snapshot diff)
- [ ] Reduced-motion: cursor flashlight disabled, all markers full opacity
- [ ] No-pointer (touch only): flashlight disabled, full opacity
- [ ] Vitest: pointer-position prop drives marker opacity computation
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `CursorFlashlight`, W2 `MapboxScene`

---

### T4.8 — Marker proximity opacity computation | Cx: 6 | P0

**Description:**
Implement `computeMarkerOpacity(markerPos, cursorPos, radius)` in `lib/wall/cursorEffects.ts` returning opacity 0–1. Used by T4.7. Pure function, deterministic. Threshold: within radius → +0.15, outside → -0.10 (clamped to 0–1).

**AC:**
- [ ] `computeMarkerOpacity` exported, pure function
- [ ] Vitest: marker at cursor center → 1.0; marker far away → 0.85; marker at edge → ~1.0
- [ ] No DOM access in the function
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.9 — Reduced-motion / no-pointer fallback for flashlight | Cx: 4 | P0

**Description:**
When `prefers-reduced-motion` or `(pointer: coarse)` matches, disable cursor flashlight. All map elements render at full opacity. Verify keyboard users see consistent rendering (no proximity dimming when navigating via tab).

**AC:**
- [ ] `usePrefersReducedMotion` and `useMatchMedia('(pointer: coarse)')` checked in `CursorFlashlight`
- [ ] When either is true, component returns null
- [ ] Markers render at full opacity (no dim)
- [ ] Playwright: emulate touch device, assert no flashlight in DOM
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7

---

## Phase 3: Live Now Widget (5 tasks, 42 Cx)

### T4.6 — Live Now data source decision (api/now vs client-side) | Cx: 4 | P0

**Description:**
**FIRST TASK in this block.** Decide: (a) tiny `/api/now` backend endpoint returning `{server_time, sessions_today, last_calibration_age_minutes}`, OR (b) client-side computation from `useLiveNow` hook + cached counts. Document trade-offs in `docs/adr/live-now-source.md`. Backend addition is a design escalation — surface in PR description if option (a) is chosen.

**AC:**
- [ ] ADR `docs/adr/live-now-source.md` written
- [ ] Decision rationale documented (latency, freshness, backend touch policy)
- [ ] If option (a): backend endpoint scope documented (read-only, no auth required, public)
- [ ] If option (b): cache strategy + polling interval documented
- [ ] Decision communicated to user before implementation tasks proceed
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.10 — Live Now widget UI in header | Cx: 10 | P0

**Description:**
Add `<LiveNowWidget />` (W1) to `Header.tsx` rendering "2:17 PM CST · 6 sessions · last calibrated 14m ago". Time format respects user locale (en: "2:17 PM"; es: "14:17"). Hidden on Chapter 1 hero for visual cleanliness; visible from Chapter 2 onward. Smooth fade-in.

**AC:**
- [ ] Widget renders in header right side
- [ ] Time format is locale-aware (Intl.DateTimeFormat)
- [ ] Hidden on `chapter === 1` (CSS class controlled by `useChapterProgress`)
- [ ] Fade-in spring on visibility change (`--spring-soft`)
- [ ] Reduced-motion: snap (no fade)
- [ ] WCAG AAA contrast verified
- [ ] Vitest: locale switching renders correct format; chapter-1 hides widget
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.6, W1 `useLiveNow`, W1 `Header.tsx`

---

### T4.11 — Live Now polling with TanStack Query | Cx: 8 | P0

**Description:**
Wire `useLiveNow` to TanStack Query with 10s polling (or 30s if T4.6 chose client-side cached). Stale-while-revalidate. On error, show last-known value with a subtle dim (no UI explosion). Debounce re-renders.

**AC:**
- [ ] TanStack Query `useQuery` with `refetchInterval: 10000`
- [ ] Stale-while-revalidate (no flash on refresh)
- [ ] On fetch error: last-known value persists, widget gets `data-stale="true"` for CSS dim
- [ ] No React re-render storm (verified via React DevTools profiler manual check)
- [ ] Vitest: polling fires at interval; error path keeps last value
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.6, T4.10

---

### T4.12 — Live Now stat band on Chapter 9 | Cx: 10 | P0

**Description:**
Chapter 9 ("Any City") already shows a static stat band ("5,189 tests · 13 sprints · 2 cities deployed · MIT"). Add a second row that re-renders live: "{sessions_today} sessions today · last calibration {age_minutes}m ago". Same data source as the header widget (TanStack Query cache shared).

**AC:**
- [ ] Chapter 9 has a second live stat row below the static one
- [ ] Live data sourced from same TanStack Query (cache hit, no second fetch)
- [ ] Locale-aware number formatting
- [ ] WCAG AAA contrast
- [ ] Reduced-motion: no count-up animation, instant value
- [ ] Vitest: live row consumes same query as header; locale switch updates format
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.11, W3 Chapter 9

---

### T4.65 — `/api/now` endpoint OR client-side fallback (per T4.6) | Cx: 10 | P0

**Description:**
Implement the chosen path from T4.6. If backend: `backend/app/routers/now.py` with `GET /api/now` returning `{server_time, sessions_today, last_calibration_age_minutes}`, no auth, cache-control `max-age=10`. If client-side: `lib/wall/liveNow.ts` reads from existing endpoints + computes locally.

**AC:**
- [ ] If option (a): pytest covers endpoint shape + cache header + no PII in response
- [ ] If option (a): SSRF-safe (no user input, deterministic query)
- [ ] If option (b): vitest covers compute logic, cache TTL, error path
- [ ] No LLM calls
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.6

---

## Phase 4: Variable Font Axis on Headlines (4 tasks, 30 Cx)

### T4.13 — Hero headline variable font weight wired | Cx: 8 | P0

**Description:**
On the Wall hero ("What's standing between you and a job?"), wire `useVariableFontWeight` (W1) to interpolate Inter Variable's `wght` axis from 700 (top of viewport) to 900 (mid-scroll). Use `font-variation-settings` CSS property. Reduced-motion: lock at weight 800 (mid).

**AC:**
- [ ] Hero `<h1>` has inline style with `font-variation-settings: 'wght' Xweight`
- [ ] Weight value comes from `useVariableFontWeight(scrollProgress)`
- [ ] Weight interpolates 700 → 900 across scroll progress 0 → 1
- [ ] Reduced-motion: locked at 800
- [ ] Vitest: scroll progress 0 → wght 700; 0.5 → wght 800; 1 → wght 900; reduced-motion → 800
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `useVariableFontWeight`

---

### T4.14 — Optical-size axis on display headings | Cx: 6 | P0

**Description:**
Inter Variable supports an optical-size axis (`opsz`). At display sizes (>4rem), set `opsz` to display value (28). At body sizes, leave at default. Apply via Tailwind plugin or CSS rule.

**AC:**
- [ ] CSS rule: `font-size > 4rem` → `font-variation-settings: 'opsz' 28, 'wght' Xweight`
- [ ] Body text uses default opsz
- [ ] Visual diff confirms slightly different rendering at display sizes
- [ ] Vitest: snapshot of computed style on display vs body element
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13

---

### T4.15 — Per-chapter heading variable font wiring | Cx: 10 | P0

**Description:**
Every chapter heading (H2 on each Chapter 1–10 component) uses `useVariableFontWeight` tied to that chapter's local scroll progress (0 at chapter top → 1 at chapter bottom). Heading "breathes" as user scrolls through.

**AC:**
- [ ] All 10 chapter components use the variable font system on their primary heading
- [ ] Each chapter's local scroll progress drives its own weight
- [ ] Reduced-motion: all locked at 800
- [ ] Vitest per chapter: scroll progress 0/0.5/1 produces 700/800/900
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13, all 10 chapters from W2/W3

---

### T4.16 — Inter Variable preload + font-display swap tuning | Cx: 6 | P0

**Description:**
In `app/layout.tsx`, ensure Inter Variable is preloaded with `font-display: swap` and a fallback metric-matched stack (Arial Variable or Inter fallback subset) to prevent CLS. Verify CLS budget < 0.05 in T4.60.

**AC:**
- [ ] Inter Variable WOFF2 preloaded with `<link rel="preload" as="font" crossorigin>`
- [ ] `font-display: swap` set in `@font-face`
- [ ] Fallback stack uses metric-matched system font
- [ ] Lighthouse CLS reported < 0.05 on hero
- [ ] Vitest: layout.tsx renders preload link
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

## Phase 5: Per-Chapter Dynamic OG (4 tasks, 28 Cx)

### T4.30 — `app/api/og/[chapter]/route.ts` with Vercel Satori | Cx: 12 | P0

**Description:**
Create dynamic OG endpoint at `app/api/og/[chapter]/route.ts` using `@vercel/og` + `satori`. Renders chapter title + locked editorial copy on dark gradient with brand mark + path mark. URL: `/api/og/01` through `/api/og/10`.

**AC:**
- [ ] Route handler at `app/api/og/[chapter]/route.ts`
- [ ] Returns 1200×630 PNG via Satori
- [ ] Each chapter (01–10) renders unique title + editorial snippet
- [ ] Dark gradient background using design tokens
- [ ] Brand G-path mark in corner
- [ ] Path-line element drawn
- [ ] Cache-control: `public, max-age=3600`
- [ ] Invalid chapter (e.g., `/api/og/99`) returns 404
- [ ] Vitest: chapter 01 renders, content includes title; invalid chapter returns 404
- [ ] No LLM calls
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 satori install

---

### T4.31 — Per-chapter OG link tags in metadata | Cx: 4 | P0

**Description:**
On each chapter URL fragment (`/?chapter=01` etc.), set `<meta property="og:image" content="/api/og/01" />` dynamically via Next.js `generateMetadata`. Twitter card uses same image.

**AC:**
- [ ] `generateMetadata` reads chapter from URL fragment / search param
- [ ] Returns appropriate OG image URL per chapter
- [ ] Default (no chapter): chapter 01 OG
- [ ] Twitter card mirrors OG
- [ ] Vitest: each chapter URL produces correct OG meta
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.30

---

### T4.32 — Static OG fallback images at build time | Cx: 8 | P1

**Description:**
At build time, generate static PNG fallbacks for all 10 chapters using same Satori template, save to `public/og/chapter-01.png`...`chapter-10.png`. If Satori endpoint fails at runtime (load spike, judging-day), Next.js metadata can fall back to static.

**AC:**
- [ ] Build script `scripts/build-og.mjs` generates all 10 PNGs
- [ ] Build script invoked in `npm run build` (postbuild step)
- [ ] Static files committed at `public/og/chapter-XX.png`
- [ ] Metadata logic: try dynamic, fallback to static on error
- [ ] Vitest: fallback path returns static URL when dynamic fails
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.30

---

### T4.33 — OG image quality verification | Cx: 4 | P1

**Description:**
Visual smoke: render each of the 10 OG images and verify (a) brand mark visible, (b) path-line visible, (c) chapter title legible, (d) locked editorial snippet present, (e) AAA contrast on text. Manual check + Playwright snapshot.

**AC:**
- [ ] Manual visual review of all 10 OG images logged in PR
- [ ] Playwright: visit each OG URL, save snapshot, compare to baseline
- [ ] Contrast verification: chapter title vs background passes AAA
- [ ] No "MontGoWork" string anywhere
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.30, T4.32

---

## Phase 6: Spanish Parity Sweep (10 tasks, 92 Cx)

### T4.20 — Audit en.json for missing es.json keys | Cx: 8 | P0

**Description:**
Scan `frontend/src/lib/translations/en.json` for every key added in W2 + W3 (chapters 1–10 editorial copy, headers, CTAs, edge-state copy, Live Now widget labels). Verify every key has an `es.json` counterpart. Report missing keys; fix in T4.21–T4.26.

**AC:**
- [ ] Script `scripts/i18n-audit.mjs` lists keys in en.json missing from es.json
- [ ] Audit run; report attached to PR
- [ ] Zero missing keys after audit fix tasks complete (this task is the inventory; fix is in subsequent tasks)
- [ ] Vitest: audit script reports zero missing on fixed branch
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.21 — Spanish translation: Chapter 1 + 2 (Continental, City Arrival) | Cx: 10 | P0

**Description:**
Translate every editorial string for Chapters 1 and 2 to Spanish. Native-fluent voice (formal-but-warm, civic dignity). NOT machine translated. Use existing `es.json` voice as style reference. Examples: "What's standing between you and a job?" → "¿Qué se interpone entre tú y un empleo?" (NOT "¿Qué está parado entre tú y un trabajo?" — too literal). Reviewer agent approves each pair against EN source.

**AC:**
- [ ] All Chapter 1 keys translated in `es.json`
- [ ] All Chapter 2 keys translated in `es.json`
- [ ] Voice consistent with existing es.json (verified by reviewer agent diff)
- [ ] No literal-translation tells (e.g., gerund-overuse, calque verbs)
- [ ] No machine-translation artifacts (e.g., "trabajo" where "empleo" fits civic register)
- [ ] Vitest: locale switch renders Chapter 1 in ES correctly
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.22 — Spanish translation: Chapter 3 + 4 (Neighborhood, The Wall sub-chapters) | Cx: 12 | P0

**Description:**
Translate Chapter 3 (Carlos intro, 60-word) and Chapter 4 sub-chapters (4a criminal record, 4b transit, 4c childcare, 4d credit). Carlos's name stays as "Carlos". "Tarrant County District Clerk" stays as "Distrito Judicial del Condado de Tarrant" with English original parenthetical for accuracy. Distance / time formats use Spanish conventions (km optionally; minutes always).

**AC:**
- [ ] Chapter 3 keys translated
- [ ] All 4 Chapter 4 sub-chapter keys translated
- [ ] Civic offices use proper Spanish nomenclature with English parenthetical
- [ ] Distance / time format consistent with locale
- [ ] Carlos's intro 60-word Spanish version reads naturally
- [ ] Vitest: locale switch on Chapter 3 + 4 sub-chapters
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.23 — Spanish translation: Chapter 5 + 6 (Labyrinth, The Math) | Cx: 10 | P0

**Description:**
Translate Chapter 5 (5 offices, 47 forms editorial) and Chapter 6 (cliff math, "$2 raise that costs $400 isn't a raise"). Money values stay in USD ($), but verbal expressions use Spanish ("dos dólares", "cuatrocientos dólares"). Cliff terminology uses "barrera de beneficios" (locked term — confirmed via reviewer with civic Spanish reference).

**AC:**
- [ ] Chapter 5 keys translated
- [ ] Chapter 6 keys translated (including slider labels, cliff zone labels)
- [ ] Money expressed naturally in Spanish
- [ ] Cliff terminology consistent with civic Spanish register
- [ ] Vitest: locale switch on Chapter 5 + 6
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.24 — Spanish translation: Chapter 7 + 8 (The Path, The Graph) | Cx: 12 | P0

**Description:**
Translate Chapter 7 (Carlos's path, week labels, footstep editorial) and Chapter 8 (33 barriers, 53 connections, breathing graph editorial). "Week 1" → "Semana 1". "33 barriers" → "33 barreras". Editorial intent preserved: "Every barrier connects. We find the order." → "Cada barrera está conectada. Encontramos el orden."

**AC:**
- [ ] Chapter 7 keys translated (week labels, footstep editorial, path editorial)
- [ ] Chapter 8 keys translated (graph editorial, 33/53 numbers stay numeric)
- [ ] Editorial voice consistent
- [ ] Vitest: locale switch on Chapter 7 + 8
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.25 — Spanish translation: Chapter 9 + 10 (Any City, Find Your Path) | Cx: 10 | P0

**Description:**
Translate Chapter 9 (Any City, "Fly to Montgomery", 5,189 tests stat band) and Chapter 10 (CTA "Start your assessment", footer). Stat numbers stay numeric. CTA: "Start your assessment" → "Comienza tu evaluación" (NOT "Empieza" — register).

**AC:**
- [ ] Chapter 9 keys translated (stat band labels, fly-to button)
- [ ] Chapter 10 keys translated (CTA, footer copy, secondary "Or read the open-source code on GitHub")
- [ ] Vitest: locale switch on Chapter 9 + 10
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.26 — Spanish translation: Edge states (404, 500, empty, loading) | Cx: 6 | P0

**Description:**
Translate the W1 edge-state copy. 404 anticipatory: "There's no path to this URL, but there's still a path for you." → "No hay un camino a esta URL, pero todavía hay un camino para ti." 500: "Something stalled. We're calibrating." → "Algo se detuvo. Estamos calibrando." Empty + loading equivalents.

**AC:**
- [ ] All edge-state strings translated
- [ ] Anticipatory tone preserved (no bureaucratic register)
- [ ] Vitest: 404 page renders ES copy when locale=es
- [ ] Reviewer agent approves
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.20

---

### T4.27 — EN/ES toggle in header (persisted) | Cx: 8 | P0

**Description:**
Add EN/ES toggle in Header (W1 should already have a `LanguageToggle` component). Verify it persists via localStorage. Toggle re-renders every chapter and the Live Now widget. Keyboard accessible (button, focus visible).

**AC:**
- [ ] Toggle visible in Header
- [ ] Click switches `useLanguage` value
- [ ] Persists in localStorage as `gowork.locale`
- [ ] Every chapter re-renders with new locale (verified via Playwright)
- [ ] Keyboard reachable (Tab order)
- [ ] Focus ring visible (W1 token)
- [ ] WCAG AAA contrast on toggle states
- [ ] Vitest: toggle changes locale; localStorage persists; Header re-renders
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `useLanguage`, W1 `Header.tsx`

---

### T4.28 — OS-language auto-detect on first load | Cx: 6 | P0

**Description:**
**Spotlight invention.** On first visit (no `gowork.locale` in localStorage), read `navigator.language`. If starts with `es-`, set initial locale to `es`. Otherwise default `en`. Subsequent visits respect explicit toggle. SSR-safe (only runs on hydration).

**AC:**
- [ ] First-load detection in `useLanguage` hook (W1) or initializer
- [ ] `navigator.language` starting with `es` → initial locale `es`
- [ ] No localStorage value: detect; with localStorage value: respect toggle
- [ ] SSR-safe (no `window` access during SSR; hydration sets value)
- [ ] Vitest: mock navigator.language=es-MX, no localStorage → locale=es; localStorage=en, navigator=es-MX → locale=en
- [ ] No flash-of-wrong-language (deferred; hydration handles)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.27

---

### T4.29 — i18n completeness CI check | Cx: 10 | P0

**Description:**
Add a CI check that runs `scripts/i18n-audit.mjs` (T4.20) on every PR. Fails if en.json has any key missing from es.json. Catches future regressions.

**AC:**
- [ ] CI workflow `.github/workflows/i18n-check.yml` runs audit script
- [ ] Failing audit blocks merge
- [ ] Local script invokable via `npm run i18n:audit`
- [ ] Vitest: audit script unit test (parses both files, reports diffs)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.20

---

## Phase 7: Custom 404 / 500 / Empty / Loading Wiring (3 tasks, 24 Cx)

### T4.34 — Verify Next.js convention wiring for 404/500 | Cx: 8 | P0

**Description:**
Confirm `app/not-found.tsx` and `app/error.tsx` (W1) are correctly placed for Next.js convention. Test 404 by visiting `/bogus-url-xyz`; test 500 by triggering an error boundary (mock a chapter that throws).

**AC:**
- [ ] `/bogus-url-xyz` returns 404 with branded copy (EN + ES per T4.26)
- [ ] Error boundary triggers `error.tsx` (test via mock chapter throw)
- [ ] Both pages have CTA back to home
- [ ] Both pages render reduced-motion safely
- [ ] Playwright: visit bogus URL, screenshot, verify branded copy
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 edge states, T4.26

---

### T4.35 — Empty + Loading state wiring per chapter | Cx: 8 | P0

**Description:**
Ensure W1 `<EmptyState />` and `<LoadingState />` are wired in every chapter that fetches data (Live Now widget, Chapter 6 cliff, Chapter 9 stat band). No spinners; skeleton screens or branded loading message.

**AC:**
- [ ] Every async chapter renders `<LoadingState />` during initial fetch
- [ ] Every async chapter renders `<EmptyState />` if data is empty
- [ ] No raw "Loading..." text or default spinner anywhere
- [ ] Reduced-motion: skeleton uses static shimmer fallback
- [ ] Vitest: each async chapter test covers loading + empty states
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 EmptyState/LoadingState, T4.10

---

### T4.62 — KSAO-aware error copy review | Cx: 8 | P1

**Description:**
**Spotlight invention.** Read every error message in 404, 500, and chapter error fallbacks. Verify anticipatory tone (Carlos-aware, not engineer-aware). No "Internal server error" — only "Something stalled. We're calibrating." Worker-first language.

**AC:**
- [ ] Manual review of all error copy strings logged in PR
- [ ] No "Error", "Failed", "Exception" strings in user-visible copy
- [ ] Every error has next-action CTA
- [ ] Reviewer agent approves tone consistency
- [ ] `bpsai-pair arch check` passes

**Depends on:** T4.34, T4.35

---

## Phase 8: Print Stylesheet Polish (2 tasks, 14 Cx)

### T4.41 — Verify print stylesheet renders cleanly | Cx: 6 | P1

**Description:**
Open the Wall in browser print preview. Verify magazine layout: serif headings, single column, page breaks at chapter transitions, brand mark on first page, footer with MIT + URL on every page. Fix any clip / overflow issues.

**AC:**
- [ ] Manual print preview screenshot for each chapter logged in PR
- [ ] Page breaks correct (no chapter cut mid-paragraph)
- [ ] Serif headings render
- [ ] Single column layout
- [ ] Brand mark on first page
- [ ] Footer MIT + URL on every page
- [ ] No images cut off
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 print stylesheet

---

### T4.42 — Print stylesheet smoke test in CI | Cx: 8 | P1

**Description:**
**Spotlight invention.** Playwright test invokes `page.pdf()` (Chromium print emulation), saves PDF, asserts: page count ≥ 9, headings present in extracted text, brand mark on first page. Catches print regressions.

**AC:**
- [ ] Playwright test in `frontend/e2e/print.spec.ts`
- [ ] Page count ≥ 9 asserted
- [ ] Extracted text contains chapter headings
- [ ] PDF generation runs in CI
- [ ] Vitest: text extractor unit test
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.41

---

## Phase 9: Reduced-Motion Sweep (5 tasks, 42 Cx)

### T4.43 — Reduced-motion audit: every animation site catalogued | Cx: 10 | P0

**Description:**
Grep all uses of `framer-motion`, `react-spring`, CSS `@keyframes`, `transition`, `animation` properties in `frontend/src/`. Catalog every animation site. For each, confirm `prefers-reduced-motion: reduce` is respected (still-image fallback or instant snap).

**AC:**
- [ ] Audit report attached to PR: list of every animation site + reduced-motion status
- [ ] Every framer-motion `motion.*` has reduced-motion check (via `useReducedMotion` from framer-motion or W1 `usePrefersReducedMotion`)
- [ ] Every CSS animation has `@media (prefers-reduced-motion: reduce)` override
- [ ] No animation site without explicit reduced-motion handling
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.44 — Reduced-motion fallback: camera flights | Cx: 8 | P0

**Description:**
Every camera fly-to (Chapters 1–9) must have an instant-cut fallback when reduced-motion is on. No 3-second cross-country fly; jump-cut to destination.

**AC:**
- [ ] All chapter `flyTo` calls check reduced-motion preference
- [ ] If reduced-motion: `jumpTo` (instant), no animation
- [ ] Playwright: emulate reduced-motion, assert no animation duration on Mapbox events
- [ ] Vitest: camera-choreography helper returns 0 duration when reduced-motion
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.43

---

### T4.45 — Reduced-motion fallback: Carlos avatar (Chapter 7) | Cx: 8 | P0

**Description:**
Carlos avatar walking the path in Chapter 7 must have static fallback: full path drawn instantly, avatar rendered at endpoint, week labels visible. No animation.

**AC:**
- [ ] When reduced-motion: full path drawn instantly on Chapter 7 mount
- [ ] Carlos rendered at endpoint position
- [ ] All week labels visible from start
- [ ] No footstep audio (audio already opt-in; reduced-motion forces opt-out)
- [ ] Vitest: Chapter 7 mount under reduced-motion → all path nodes visible
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.43, W3 Chapter 7

---

### T4.46 — Reduced-motion fallback: 3D barrier graph (Chapter 8) | Cx: 10 | P0

**Description:**
3D barrier graph (Three.js) must fall back to static 2D SVG image of the constellation when reduced-motion is on. PNG snapshot acceptable. No orbital drift, no edge illumination animation.

**AC:**
- [ ] When reduced-motion: render `<img src="/og/constellation-static.png" alt="Barrier constellation: 33 barriers, 53 connections" />`
- [ ] No Three.js Canvas mounted under reduced-motion (memory + perf win)
- [ ] Static image has accessible alt text describing structure
- [ ] Static PNG rendered at build time from canonical 3D layout
- [ ] Vitest: Chapter 8 under reduced-motion → no Canvas, image rendered
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.43, W3 Chapter 8

---

### T4.47 — Reduced-motion fallback: scroll-velocity reactive blur | Cx: 6 | P0

**Description:**
Scroll-velocity-reactive motion blur (T4.59 P1 task) is disabled entirely under reduced-motion. No filter property applied to background.

**AC:**
- [ ] Scroll-velocity blur opts out of reduced-motion
- [ ] No `filter: blur()` applied when reduced-motion
- [ ] Playwright: emulate reduced-motion, assert no filter on background element
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.43

---

## Phase 10: WCAG AAA Contrast Pass (3 tasks, 26 Cx)

### T4.40 — Token-pair contrast verification script | Cx: 10 | P0

**Description:**
`scripts/verify-contrast.mjs` (W1 placeholder) reads design tokens from `tokens/colors.css`, computes every fg-on-bg pair contrast ratio, reports passes/fails at AAA thresholds (7:1 normal text, 4.5:1 large text). Fix any failure at the token level.

**AC:**
- [ ] Script lists every token pair with computed ratio
- [ ] AAA threshold check: report fail if normal-text pair < 7:1 or large-text < 4.5:1
- [ ] Run on each phase of time-of-day (4 accents × 3 fg tokens)
- [ ] Zero AAA failures after fix
- [ ] CI invokes script on every PR
- [ ] Vitest: script unit test parses tokens, reports correct ratios
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.36 — axe-core sweep every chapter at AAA | Cx: 12 | P0

**Description:**
Run axe-core via Playwright on every chapter (1–10) in EN and ES, with `tags: ['wcag2aaa', 'wcag21aaa']`. Catalog violations. Fix each at component level.

**AC:**
- [ ] axe-core configured with AAA tag set
- [ ] Every chapter sweeped in EN and ES (20 runs)
- [ ] Zero serious/critical violations
- [ ] Moderate violations fixed or documented with rationale
- [ ] Report attached to PR
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.27

---

### T4.37 — Fix any AAA failures in muted text + glass cards | Cx: 4 | P0

**Description:**
Most likely AAA failures: `--fg-muted` on `--bg-base` may dip below 7:1; glass cards (semi-transparent) may show variable contrast. Fix by darkening muted token OR raising glass opacity, never by relaxing standard.

**AC:**
- [ ] Token adjustments made if needed
- [ ] All chapters re-sweeped post-fix → zero failures
- [ ] No "skip rule" or rationale-bypass shortcuts (fix at token level)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.36, T4.40

---

## Phase 11: Keyboard Navigation Sweep (4 tasks, 30 Cx)

### T4.38 — Tab order sweep through every interactive | Cx: 10 | P0

**Description:**
Manual + Playwright keyboard navigation from page top to footer. Tab order must be logical: header → chapter content → footer. No tabindex ≥ 1 (use source order). Every interactive reachable. Skip-to-content link works.

**AC:**
- [ ] Manual keyboard traversal logged in PR (screenshot per chapter)
- [ ] Playwright: presses Tab N times, asserts focus order matches expected DOM order
- [ ] Skip-to-content link visible on focus, jumps to main
- [ ] No focus traps
- [ ] No tabindex > 0 in code (grep audit)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.39 — Focus visible on every focusable | Cx: 6 | P0

**Description:**
Verify W1 focus ring (2px cyan offset 2px) renders on every focusable element. No `:focus { outline: none }` without `:focus-visible` replacement. Custom focus styles match across browsers (Chrome, Safari, Firefox).

**AC:**
- [ ] CSS audit: every `:focus { outline: none }` has matching `:focus-visible` style
- [ ] Manual cross-browser visual check on header buttons, chapter CTAs, toggle, slider
- [ ] Reduced-motion respected (no animated entry of ring under reduce)
- [ ] Vitest snapshot of focus-visible styles
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.38

---

### T4.50 — Keyboard alternate for cursor flashlight | Cx: 8 | P0

**Description:**
Cursor flashlight (T4.7) is mouse-driven; keyboard users get a focus-driven alternative. When user tabs onto a chapter, the flashlight follows the focused element. Works with screen reader.

**AC:**
- [ ] On focus event for chapter elements, flashlight repositions to focused element
- [ ] No flashlight under reduced-motion or coarse-pointer
- [ ] Playwright: tab through Chapter 6, assert flashlight position changes
- [ ] Screen-reader-friendly (focus events fire normal aria announcements)
- [ ] Vitest: focus event drives flashlight position
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7

---

### T4.51 — Modal + view-transition focus management | Cx: 4 | P0

**Description:**
Verify Chapter 10 view transition to /assess preserves focus (focus moves to first form field on /assess, not lost). Verify any modal in chapters has focus trap + esc-close.

**AC:**
- [ ] Chapter 10 view transition: focus moves to /assess first input
- [ ] If View Transitions unsupported, standard navigation preserves focus
- [ ] Any modal: focus trap (tab cycles inside), esc closes
- [ ] Playwright: triggers transition, asserts active element is form input on /assess
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W3 Chapter 10

---

## Phase 12: Screen Reader Pass (3 tasks, 26 Cx)

### T4.52 — VoiceOver (macOS) sweep | Cx: 10 | P0

**Description:**
VoiceOver pass on Chapters 1–10. Every interactive has accessible name. Landmarks present. Live regions announce updates (Live Now, chapter transitions). Document any issue with screenshot of VoiceOver rotor.

**AC:**
- [ ] VoiceOver enabled, rotor used to navigate chapters
- [ ] Every chapter heading is in heading rotor
- [ ] Every interactive has accessible name (announcement audible)
- [ ] Landmarks: main, header, footer, complementary
- [ ] Live region announces Live Now polling updates (or `aria-live="polite"` if too chatty)
- [ ] Issues logged + fixed
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.38

---

### T4.53 — NVDA / Windows screen reader simulation | Cx: 8 | P0

**Description:**
Manual NVDA on Windows (or simulator): same checks as T4.52. Catches Mac-specific quirks.

**AC:**
- [ ] NVDA navigation logged
- [ ] Cross-browser screen-reader behavior consistent
- [ ] Issues logged + fixed
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.52

---

### T4.54 — ARIA-live regions firing on chapter transitions | Cx: 8 | P0

**Description:**
On chapter change, an `aria-live="polite"` region announces "Now in chapter 4: The Wall" (or ES equivalent). Doesn't over-announce (debounce). Live Now polling updates use `aria-live="off"` (too noisy) but the chapter-band stat is announced once on chapter change.

**AC:**
- [ ] `<div role="status" aria-live="polite">` in chapter scaffold
- [ ] On chapter change, region updates with localized announcement
- [ ] No over-announcement (debounce on rapid scroll)
- [ ] Live Now header: `aria-live="off"` (too noisy)
- [ ] Vitest: chapter change updates live region content; debounce holds
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.52

---

## Phase 13: Lighthouse 90+ Hard Gate (5 tasks, 50 Cx)

### T4.55 — `lib/wall/perfBudget.ts` explicit thresholds module | Cx: 8 | P0

**Description:**
**Spotlight invention.** Centralize perf budget thresholds in one TS module. LCP < 2.5s, CLS < 0.05, TBT < 200ms, TTI < 3.8s, total JS bundle < 350KB. T4.59 + T4.60 + Lighthouse CI consume this. Without it, descope decisions are ad-hoc.

**AC:**
- [ ] `frontend/src/lib/wall/perfBudget.ts` exports thresholds object
- [ ] Constants: `LCP_MS`, `CLS_MAX`, `TBT_MS`, `TTI_MS`, `JS_BUNDLE_KB`
- [ ] `lighthouserc.json` updated to 4G simulated preset (replace `desktop` with `mobile` config)
- [ ] Performance assertion: `categories:performance` ["error", { minScore: 0.9 }]
- [ ] Vitest: thresholds export expected shape
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.56 — Lighthouse 4G baseline measurement | Cx: 8 | P0

**Description:**
Run `npm run lhci` against production build with `preset: mobile` + `throttling.cpuSlowdownMultiplier: 4` (4G simulation). Capture baseline scores: Performance, Accessibility, Best Practices, SEO. Document in PR.

**AC:**
- [ ] Lighthouse runs against `npm run build && npm run start`
- [ ] Mobile preset with 4G simulated throttling
- [ ] Scores documented for all 6 routes (`/`, `/daily`, `/appointments`, `/documents/resume`, `/jobs`, `/case-manager`)
- [ ] Baseline JSON committed to `frontend/lighthouse-baseline-4g.json`
- [ ] If any score < 90, descope ladder activated in T4.57
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.55

---

### T4.57 — Apply descope ladder if Lighthouse < 90 | Cx: 14 | P0

**Description:**
If T4.56 baseline shows Performance < 90 on simulated 4G, apply descope ladder in order: (1) drop sound system, (2) drop temperature multiplier motion, (3) drop 3D graph (replace with 2D SVG), (4) drop view transitions. Re-measure after each. Stop when score ≥ 90. Document final state.

**AC:**
- [ ] Descope decisions logged in PR with before/after scores
- [ ] Apply in order; stop at first ≥ 90
- [ ] If all 4 applied and still < 90, escalate to user
- [ ] KEEP no matter what: Mapbox foundation, Carlos avatar, all 10 chapters, Spanish toggle
- [ ] Final score documented
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.56

---

### T4.58 — Lighthouse threshold enforced in CI | Cx: 8 | P0

**Description:**
CI runs Lighthouse on every PR. PR fails if Performance < 90 or Accessibility < 95 (raised from 90 to match AAA pass). Performance regression gate.

**AC:**
- [ ] `.github/workflows/lighthouse.yml` invokes `npm run lhci` with 4G config
- [ ] Performance < 90 fails the job
- [ ] Accessibility < 95 fails the job
- [ ] Score posted as PR comment
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.55, T4.56

---

### T4.66 — Final Lighthouse pass + report | Cx: 12 | P0

**Description:**
After all W4 tasks complete, run Lighthouse one final time. Document final scores in PR. If any regression vs baseline > 5 points, escalate.

**AC:**
- [ ] Final Lighthouse run captured
- [ ] Scores documented for all 6 routes
- [ ] Performance ≥ 90 on simulated 4G achieved (hard gate)
- [ ] Accessibility ≥ 95 (AAA evidence)
- [ ] Best Practices ≥ 90, SEO ≥ 90
- [ ] If any regression > 5 vs baseline: investigation note
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** all W4 prior tasks

---

## Phase 14: Mobile Fallback Verification (4 tasks, 28 Cx)

### T4.50a — Mobile detection + fallback router | Cx: 8 | P0

**Description:**
`lib/wall/mobileFallback.ts` exports `useMobileFallback()` returning `{ isMobile: boolean, mapboxSupported: boolean }`. Detection: `window.innerWidth < 768` OR `mapboxgl.supported() === false`. Wall components consume this to render static-image variants on mobile.

**AC:**
- [ ] Hook exported
- [ ] Detection logic: width OR mapbox-supported flag
- [ ] SSR-safe (returns desktop default during SSR)
- [ ] Vitest: width=400 → isMobile=true; width=1200 → false; mapbox-supported=false → fallback regardless of width
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** none

---

### T4.51a — Tablet (768–1023px) scaled map | Cx: 8 | P0

**Description:**
On tablet widths, the Mapbox map renders but at scaled size (smaller pitch, wider zoom). All chapters work; cursor flashlight disabled (touch-coarse pointer). Editorial overlay scales.

**AC:**
- [ ] Width 768–1023: Mapbox renders, pitch reduced to 30°, zoom +1
- [ ] Editorial overlays scale to viewport
- [ ] Cursor flashlight off
- [ ] Playwright at 800x600: all chapters render without overflow
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.50a

---

### T4.52a — Mobile (<768px) static images + editorial scroll | Cx: 10 | P0

**Description:**
On mobile widths, the Mapbox map is replaced with pre-rendered static images per chapter (saved at `/public/wall/mobile/chapter-XX.png`). Editorial scroll with images stacked. Audio off. Live Now widget collapsed. CTA at bottom.

**AC:**
- [ ] Width < 768: no Mapbox Canvas mounted
- [ ] Static images render per chapter (alt text matches chapter editorial)
- [ ] Editorial overlays stack vertically
- [ ] Footer + CTA visible
- [ ] No layout breakage at 320px (smallest reasonable phone)
- [ ] Playwright at 360x640: all 10 chapters render, scrollable, no horizontal scroll
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.50a

---

### T4.53a — Build script: generate mobile static images | Cx: 6 | P0

**Description:**
`scripts/build-wall-mobile.mjs` uses Playwright to capture each chapter at 1080×1920 in desktop mode, saves to `public/wall/mobile/chapter-XX.png`. Runs at build time.

**AC:**
- [ ] Build script generates 10 PNGs
- [ ] Each ≤ 200KB (compressed)
- [ ] Invoked in `npm run build` postbuild
- [ ] Vitest: script unit test (mock Playwright)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.52a

---

## Phase 15: Scroll-Velocity Reactive (2 tasks, 12 Cx)

### T4.59 — Scroll-velocity motion blur | Cx: 8 | P1

**Description:**
When scroll velocity > threshold (200px/s), apply subtle `filter: blur(2px)` to background layer (NOT to text). Disabled under reduced-motion.

**AC:**
- [ ] `useScrollVelocity` (W1) drives blur
- [ ] Threshold: 200px/s; max blur: 2px; ramp via spring
- [ ] Text layer never blurred
- [ ] Reduced-motion: blur disabled
- [ ] Vitest: velocity 0 → blur 0; velocity 300 → blur 2px; reduced-motion → blur 0
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `useScrollVelocity`

---

### T4.60 — Velocity blur perf budget check | Cx: 4 | P1

**Description:**
Verify scroll-velocity blur does not regress LCP or TBT. Lighthouse re-run after T4.59. If regression > 3 points, descope (P2 → drop entirely).

**AC:**
- [ ] Lighthouse re-run before/after T4.59
- [ ] If regression > 3 points: T4.59 reverted, documented
- [ ] If acceptable: confirmed in PR
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.59

---

## Phase 16: Idle State (2 tasks, 12 Cx)

### T4.61 — Idle detection + ambient drift | Cx: 8 | P1

**Description:**
After 30s of no input (mouse, scroll, key), trigger ambient drift on barrier graph (subtle orbital) + path-line pulse. Stops on any input. Disabled under reduced-motion.

**AC:**
- [ ] `useIdleState` (W1) triggers at 30s no-input
- [ ] On idle: graph orbital drift + path-line pulse
- [ ] On any input: stops within 100ms
- [ ] Reduced-motion: idle drift disabled
- [ ] Vitest: idle fires; input cancels; reduced-motion bypass
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** W1 `useIdleState`

---

### T4.63 — Idle state perf check | Cx: 4 | P2

**Description:**
Confirm idle drift doesn't regress perf. If regression, drop entirely (idle is delight, not core).

**AC:**
- [ ] Lighthouse run with idle simulated
- [ ] If regression > 2 points: idle disabled, documented
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.61

---

## Phase 17: Tests (10 tasks, 84 Cx)

### T4.67 — Time-of-day visual regression Playwright | Cx: 8 | P0

**Description:**
Playwright test mocks `Date.now()` to 7am, noon, 7pm, 11pm. Captures screenshot of Wall hero per phase. Diffs against baseline. Catches accent / sky regressions.

**AC:**
- [ ] 4 baselines captured at 4 phases
- [ ] Playwright run produces diffs vs baselines
- [ ] Threshold: < 0.5% pixel diff
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.1, T4.4

---

### T4.68 — Spanish toggle re-renders all chapters Playwright | Cx: 10 | P0

**Description:**
Playwright loads Wall in EN, asserts hero EN copy. Toggles to ES, asserts hero ES copy. Scrolls through every chapter, asserts ES copy per chapter. Reverse to EN.

**AC:**
- [ ] All 10 chapters traversed in EN, then ES
- [ ] Each chapter's primary editorial string asserted in both locales
- [ ] No untranslated key fallback to EN string in ES mode
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.27, T4.21–T4.26

---

### T4.69 — Compound life-layers integration test | Cx: 14 | P0

**Description:**
**Spotlight invention.** Playwright test fires all 12 life-layers simultaneously: time-of-day at 7pm, ES toggle on, cursor flashlight active, variable font axis interpolating, cliff slider in motion, scroll-velocity blur active. Asserts no console errors, no React render-loop warnings, no layout shift > 0.1, all chapters reachable.

**AC:**
- [ ] Test runs through all 10 chapters with all life-layers active
- [ ] Console error count = 0
- [ ] CLS < 0.1
- [ ] No infinite re-render warnings
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** all life-layer tasks

---

### T4.70 — Cliff slider × time-of-day × variable font integration | Cx: 10 | P0

**Description:**
**Spotlight invention (compound).** Specific test: drag cliff slider during time-of-day phase change at 7pm with variable font interpolating. Verify no UI jitter, no NaN values, no audio glitches (or audio off if reduced-motion). Slider value persists.

**AC:**
- [ ] Slider drag + time transition + scroll fires together
- [ ] No jitter, NaN, glitch
- [ ] Slider final value matches drag end
- [ ] `--temperature-multiplier` updates correctly
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.69, W3 Chapter 6

---

### T4.71 — Live Now polling integration test | Cx: 6 | P0

**Description:**
Vitest + MSW mock `/api/now` (or client-side compute mock). Polling at 10s interval. Stale-on-error. Locale switch updates format.

**AC:**
- [ ] Polling fires at correct interval
- [ ] Error path keeps last value
- [ ] Locale switch reformats time
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.11

---

### T4.72 — Variable font weight interpolation test | Cx: 6 | P0

**Description:**
Vitest renders hero, simulates scroll progress 0/0.25/0.5/0.75/1.0. Asserts computed `font-variation-settings` reflects expected weight per progress.

**AC:**
- [ ] 5 progress points asserted
- [ ] Progress 0 → wght 700; 0.5 → wght 800; 1 → wght 900
- [ ] Reduced-motion → wght 800 always
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13

---

### T4.73 — Lighthouse threshold via CI test | Cx: 8 | P0

**Description:**
CI Lighthouse job (T4.58) runs as a test gate. Fails PR if any score below threshold. Smoke verifies the gate fails when intentional regression introduced.

**AC:**
- [ ] CI gate active
- [ ] Smoke: PR with deliberate regression (e.g., add 100KB unused JS) fails the gate
- [ ] Documented in `docs/runbooks/lighthouse-gate.md`
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.58

---

### T4.74 — Keyboard navigation Playwright sweep | Cx: 8 | P0

**Description:**
Playwright presses Tab through entire Wall page top-to-bottom. Asserts focus order: skip-link → header (brand → counter → Live Now → toggle → GitHub) → main → footer. Asserts focus visible at each stop.

**AC:**
- [ ] Tab traversal logged
- [ ] Focus order matches expected
- [ ] Each stop has visible focus ring
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.38, T4.39

---

### T4.75 — Reduced-motion fallback test | Cx: 8 | P0

**Description:**
Playwright sets `prefers-reduced-motion: reduce`. Asserts: no Mapbox flyTo durations, no framer-motion transitions, no Three.js Canvas mounted (Chapter 8 uses static image), no scroll-velocity blur, no idle drift.

**AC:**
- [ ] Reduced-motion enforcement verified across all chapters
- [ ] Specific assertions per task (T4.44–T4.47)
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.44, T4.45, T4.46, T4.47

---

### T4.76 — i18n audit + AAA contrast script tests | Cx: 10 | P0

**Description:**
Vitest unit tests for `scripts/i18n-audit.mjs` (T4.20) and `scripts/verify-contrast.mjs` (T4.40). Cover: missing key detection, contrast ratio computation, AAA threshold check.

**AC:**
- [ ] i18n audit script: detects missing key in fixture; reports clean fixture as zero
- [ ] Contrast script: computes correct WCAG ratio for known pairs (white-on-black = 21:1)
- [ ] AAA threshold: 7:1 normal, 4.5:1 large
- [ ] CI invokes both scripts
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.20, T4.40

---

## Sprint Cx Budget

| Phase | Tasks | Cx | Focus |
|---|---:|---:|---|
| 1 Time-Aware System | 5 | 44 | Sky setter, sun position, smooth transitions, accent shift, reduced-motion |
| 2 Cursor Flashlight | 3 | 20 | Map wiring, opacity computation, pointer-coarse fallback |
| 3 Live Now Widget | 5 | 42 | Source decision, header UI, polling, Chapter 9 stat band, endpoint impl |
| 4 Variable Font Axis | 4 | 30 | Hero wght, opsz axis, per-chapter wiring, preload |
| 5 Per-Chapter OG | 4 | 28 | Satori endpoint, metadata wiring, build-time fallback, quality |
| 6 Spanish Parity | 10 | 92 | Audit + 6 chapter-pair translation tasks + edge-state ES + toggle + OS detect + CI check |
| 7 Edge State Wiring | 3 | 24 | 404/500 wiring, empty/loading per chapter, KSAO copy review |
| 8 Print Stylesheet | 2 | 14 | Manual verify, CI smoke |
| 9 Reduced-Motion Sweep | 5 | 42 | Audit, camera, avatar, 3D graph, blur fallbacks |
| 10 WCAG AAA Contrast | 3 | 26 | Token script, axe-core sweep, fix muted/glass |
| 11 Keyboard Navigation | 4 | 30 | Tab order, focus visible, flashlight kbd alt, modal/transition focus |
| 12 Screen Reader Pass | 3 | 26 | VoiceOver, NVDA, ARIA-live |
| 13 Lighthouse Hard Gate | 5 | 50 | Perf budget module, 4G baseline, descope, CI gate, final pass |
| 14 Mobile Fallback | 4 | 28 | Detection hook, tablet scaled, mobile static, build script |
| 15 Scroll-Velocity Reactive | 2 | 12 | Blur, perf check |
| 16 Idle State | 2 | 12 | Drift, perf check |
| 17 Tests | 10 | 84 | TOD vis-reg, ES sweep, compound, cliff×TOD×font, polling, font, LH gate, kbd, RM, scripts |
| **Total** | **74** | **604** | |

## Priority order (recommended execution)

**Wave 1 (parallel, independent foundations):** T4.6 (Live Now decision — blocking), T4.20 (i18n audit), T4.40 (contrast script), T4.43 (RM audit), T4.50a (mobile detection), T4.55 (perf budget module), T4.16 (font preload), T4.30 (Satori OG endpoint).

**Wave 2 (parallel, depends on wave 1):** T4.1, T4.2, T4.7, T4.8, T4.10, T4.13, T4.21–T4.26 (Spanish translations parallelize chapter-by-chapter), T4.27, T4.28, T4.34, T4.35, T4.41, T4.44–T4.47, T4.36, T4.38, T4.39, T4.51a, T4.52a.

**Wave 3 (depends on wave 2):** T4.3, T4.4, T4.5, T4.9, T4.11, T4.12, T4.14, T4.15, T4.31, T4.32, T4.33, T4.37, T4.42, T4.50, T4.51, T4.52, T4.53, T4.54, T4.56, T4.58, T4.49 (HOC extraction; refactors chapter components), T4.62, T4.65, T4.59, T4.61, T4.53a.

**Wave 4 (gates + integration):** T4.29 (i18n CI), T4.57 (descope if needed), T4.60, T4.63, T4.66 (final Lighthouse), T4.67–T4.76 (test suite).

**Hard gate:** T4.66 must show Lighthouse Performance ≥ 90 on simulated 4G before W4 is closed.

## Cross-sprint dependencies

- **Depends on:** W3 (all 10 chapters live and functional)
- **Blocks:** W5 (submission materials need polished site for screenshots, video, OG verification)
- **Parallel with:** W1, W2, W3, W5 backlog creation (this is planning sprint creation; build sequence is W1 → W2 → W3 → W4 → W5)

## Net-new dependencies

- None expected (Vercel `@vercel/og` + `satori` installed in W1).
- If T4.6 selects backend `/api/now`: net-new file `backend/app/routers/now.py`. Single-router, no schema migration.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Lighthouse 90+ on simulated 4G unachievable with all 12 layers | Descope ladder T4.57; final gate T4.66 |
| Spanish translation quality without native speaker | Reviewer agent + Shawn second-pass; T4.21–T4.26 each gated |
| Per-chapter OG fails under load | Static fallback T4.32 generated at build |
| Variable font Safari quirks | Cross-browser smoke in T4.67; fallback to weight 800 |
| Compound life-layer interaction conflicts | T4.69 + T4.70 integration tests |
| `/api/now` backend addition policy | T4.6 ADR + design escalation |
| 3D graph reduced-motion fallback ugly | T4.46 static PNG generated from canonical layout; visual review |
| AAA contrast on muted text fails | T4.37 token-level fix, no rationale-bypass |
| Mobile static images stale on chapter copy update | Build script T4.53a regenerates on each build |

## Success criteria for W4 closure

- [ ] All 12 life-layers wired and verified
- [ ] Spanish parity sweep complete: zero missing es.json keys (T4.29 CI gate green)
- [ ] WCAG AAA contrast on all token pairs (T4.40 script green)
- [ ] axe-core AAA sweep passes (T4.36 zero serious/critical violations)
- [ ] Keyboard navigation full sweep clean (T4.74)
- [ ] Screen reader pass logged (T4.52, T4.53)
- [ ] Reduced-motion fallback verified at every animation site (T4.43–T4.47, T4.75)
- [ ] **Lighthouse Performance ≥ 90 on simulated 4G (T4.66 — HARD GATE)**
- [ ] Mobile fallback graceful at 320px, 768px, 1024px (T4.50a–T4.53a)
- [ ] Print stylesheet smoke green (T4.42)
- [ ] All 70 tasks marked done
- [ ] PR opened against `sprint/visual-rebirth` with W5 submission backlog already drafted

## KANSEI dispatch directive for W4

Identity: "Driver — accessibility + life-layers specialist". Emphasized DO NOTs:
- DO NOT skip prefers-reduced-motion in any animation task
- DO NOT translate Spanish via machine
- DO NOT regress Lighthouse score; descope per ladder
- DO NOT block keyboard users
- DO NOT use placeholder Carlos data — real fixtures from `docs/demo-script.md`
- DO NOT silently break /assess or /plan workflows (light-mode pages)
- DO NOT add Storybook in W4 (defer to post-hackathon)
- DO NOT regress test counts (1109 frontend tests must remain passing)

慣性の契約. 心を燃やせ. The Wall plays differently for every user. — GoWork team · April 2026.
