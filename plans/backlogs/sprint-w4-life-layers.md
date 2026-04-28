# Sprint W4 — 12 Life-Layers + Spanish Parity + Performance + Accessibility Hard Gate

**Plan type:** feature
**Sprint:** W4
**Total Cx:** 1002 (P0: 778, P1: 202, P2: 22)
**Tasks:** 132 (P0: 96, P1: 32, P2: 4)
**Enrichment pass (2026-04-27):** appended T4.77–T4.134 (58 new tasks, +398 Cx) covering 8-phase TOD, weather, flashlight polish, Live Now extras, variable font axes, ES parity deeper, branded edge states, RM screenshot fallbacks, AAA per-state, forced-colors, keyboard shortcuts, mobile chapter-specific layouts, image/font budgets, compound integration tests.
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
| `frontend/src/lib/wall/timeOfDay.ts` | T4.1, T4.2, T4.3, T4.4, T4.77, T4.78, T4.80, T4.84 | **(serialize)** Single hook update task per concern; T4.1 first; T4.77 (8-phase) blocks T4.78–T4.84 |
| `frontend/src/components/wall/MapboxScene.tsx` | T4.1, T4.7, T4.8, T4.69, T4.79, T4.84, T4.85, T4.88 | **(serialize)** Each life-layer adds one effect hook block; T4.79 (weather) + T4.84 (scroll-coupled) extend sky integration |
| `frontend/src/components/wall/CursorFlashlight.tsx` | T4.7, T4.50, T4.85, T4.86, T4.87, T4.88, T4.89 | **(serialize)** All flashlight enrichments touch this; T4.85 first, then T4.86, T4.87, T4.88, T4.89 |
| `frontend/src/lib/translations/en.json` | T4.20–T4.29, T4.102, T4.105 | Each chapter pair adds its own keys (merge-friendly); T4.102 (style guide) gates re-shape edits |
| `frontend/src/lib/translations/es.json` | T4.20–T4.29, T4.100–T4.105, T4.106–T4.109 | Same as en.json; T4.100 (reviewer gate) blocks T4.21–T4.25 merges; T4.106–T4.109 add branded edge-state ES copy |
| `frontend/src/components/layout/Header.tsx` | T4.10, T4.82, T4.90, T4.92, T4.93 | Single Live Now node; T4.10 first; deeper widget enrichments in T4.82 / T4.90 / T4.92 / T4.93 layered on top |
| `frontend/src/app/layout.tsx` | T4.16, T4.30, T4.98, T4.105 | T4.16 metadata + T4.30 OG link tags + T4.98 hreflang/localized OG + T4.105 hreflang accessibility — **(serialize)**; T4.16 first, T4.30 second |
| `frontend/src/app/globals.css` | T4.43, T4.44, T4.45, T4.78, T4.95, T4.96, T4.115, T4.117 | Each adds its own `@media` block (prefers-reduced-motion / prefers-contrast / forced-colors); serialize |
| `frontend/src/lib/wall/perfBudget.ts` (new) | T4.55, T4.59, T4.60, T4.130, T4.131 | Single create then read-only consumers; T4.130 adds IMAGE/FONT_BUDGET constants — **(serialize)** with T4.55 first |
| `frontend/src/components/wall/withReducedMotion.tsx` (new) | T4.49 | Single create; downstream chapters import |
| `frontend/src/app/not-found.tsx` | T4.34, T4.106 | T4.34 wires Next.js convention; T4.106 adds editorial branded variant — **(serialize)** |
| `frontend/src/app/error.tsx` | T4.34, T4.107 | T4.34 wires; T4.107 adds calibrating motif + auto-retry — **(serialize)** |
| `frontend/lighthouserc.json` | T4.55, T4.126 | T4.55 first (4G threshold), T4.126 extends to per-chapter route list — **(serialize)** |
| `frontend/next.config.{js,ts}` | T4.128 | Single edit (bundle analyzer wiring); no other tasks touch this |
| `.github/workflows/lighthouse.yml` | T4.58, T4.126, T4.127 | T4.58 first (single route), T4.126 extends to 11 routes, T4.127 adds trend chart — **(serialize)** |

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

## Spotlight Inventions (Enrichment Pass — 2026-04-27)

These tasks emerged from the second-pass Spotlight session re-applying the 5 Awakening Conditions + 5 Lenses to the existing W4 backlog. They go beyond the original 17-category brief.

1. **T4.80 — User timezone respect** (Multiple-Selves: Maria visiting from Madrid at her 2pm sees afternoon, not FW's 7am. Wall lighting reflects *the viewer's reality*, not the city's. The Wall as instrument plays in *your* key, not its own.). Spotlight catch: original T4.1 hard-coded America/Chicago.

2. **T4.81 — Manual time-phase override toggle** (Multiple-Selves + Honesty: photophobic users need force-night-mode; demo-day judges need deterministic phases. A single keyboard-discoverable shortcut serves both. Spotlight catch: a11y was implicit, demo-determinism was missing entirely.)

3. **T4.87 — Keyboard alternate flashlight: tab through markers** (Compound + Wisdom: keyboard users were getting *something* via T4.50, but the proximity-illumination model — the perceptual core of the flashlight — wasn't keyboard-equivalent. T4.87 makes focused-marker the flashlight center, so keyboard users get the same "I am illuminating this region" perception.)

4. **T4.89 — Forced-colors mode (Windows high-contrast) sweep** (Resilience + Wisdom: forced-colors strips translucent overlays. The flashlight, glass cards, gradient skies — all break silently in Windows high-contrast unless we explicitly handle. Spotlight catch: original AAA pass focused on contrast ratios, missed forced-colors mode entirely.)

5. **T4.99 — Spanish-specific OG image with cultural framing** (許可 + Multiple-Selves: literal translation of an OG image isn't enough — Hispanic civic audience deserves framing chosen *for* them, not translated *to* them. "Una infraestructura para cualquier ciudad estadounidense" carries different civic weight than "Infrastructure for any American city". Reviewer + Shawn approve cultural framing, not just linguistic.)

6. **T4.101 — Cultural review: Carlos story tone in Spanish** (正直 + Multiple-Selves: Spanish translations easily slip into pity-tone or savior-narrative. Carlos is protagonist, not victim. Active voice in ES, dignified phrasing, no "pobre Carlos". Specific cultural review gate beyond linguistic review.)

7. **T4.106 + T4.107 — Branded 404 + 500 with Wall identity** (遺産 + Wisdom: edge states are usually generic. Carlos's experience is "barriers redirect, but the path continues" — 404 says "no path to this URL, but there is one through the wall". 500 says "Something stalled. We're calibrating." The Wall's identity reaches the worst page in the app.)

8. **T4.116 — Color-blind safe palette with shape encoding** (融合 + Resilience: Chapter 6 cliff zones use red/yellow/green — the most failure-prone palette for color-blindness. Shape encoding (squares/triangles/circles) means the information survives *any* color perception. Lateral fusion: a11y constraint becomes information-design improvement everyone benefits from.)

9. **T4.118 — Chapter shortcuts (1–0, vim j/k) + ? cheat-sheet** (Compound: keyboard navigation is a category, but power-user shortcuts are a *delight* category usually skipped. Adds to keyboard a11y *and* judging-day "wow this feels alive" delight. Single feature serves both audiences.)

10. **T4.122 — Mobile chapter-specific layouts (not just static)** (Multiple-Selves + Honesty: T4.52a was "graceful degradation = static images". That's surrender. Each chapter deserves a *purposeful* mobile experience. Cliff slider works on touch. Carlos is a vertical timeline. Graph is 2D SVG. Tap-list of cities. Mobile becomes a first-class surface, not a fallback.)

11. **T4.126 + T4.127 — Lighthouse per-chapter trend chart** (Wisdom + Legacy: a single Lighthouse score is a snapshot. A trend chart per route over 30 days is *evidence of discipline*. Judges grade Tech Debt + Code Cleanliness — a published trend chart is direct proof.)

12. **T4.130 — Image + Font budget enforcement at build** (Structural + Resilience: bundle JS budgets are common; image and font budgets rarely are. Adding RM screenshots, Carlos waypoints, and OG fallbacks could silently blow past 1.5MB image budget. Hard build-time gate prevents drift.)

13. **T4.133 — 12 life-layers compound integration test (enriched)** (Compound: extends T4.69 specifically for the 12 *enriched* life-layers. Tests the system at its maximum stress: 7pm golden-hour + ES locale + cloudy weather + flashlight velocity trail + idle pulse + variable italic axis + Live Now polling + chapter shortcuts. If it survives this, it survives the demo.)

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
| 8-phase TOD smooth transitions perform under 60fps target on mid-tier mobile | **C4 (medium)** | T4.84 batches sky updates per RAF; T4.133 compound test asserts P95 frame time < 17.6ms. If miss, descope to 4-phase. |
| Open-Meteo weather API rate limiting / availability on judging day | **C5 (low)** | T4.79 caches 24h locally + graceful fallback to `cloudCover=0`. No blocking dependency on external service. |
| Vibration API silently absent on iOS Safari | **C4 (medium)** | T4.124 feature-detects `'vibrate' in navigator`; opt-in only. iOS users don't notice absence. |
| Battery API deprecated in some browsers (Firefox, Safari desktop) | **C5 (low)** | T4.125 feature-detects, no-ops where unavailable. No regression for non-supporting browsers. |
| Forced-colors mode regressions in Mapbox GL JS canvas | **C4 (medium)** | T4.89 + T4.114 disable custom flashlight glow + verify markers visible. Mapbox tile rendering not ours to control under forced-colors; document acceptable degradation. |
| Spanish reviewer-agent gate creates merge bottleneck | **C3 (decided)** | T4.100 codifies prompt template; reviewer auto-approves on PR open. If reviewer flags issue, blocking is correct (quality gate). |
| Cultural framing of Carlos story risks paternalism in Spanish | **C4 (medium)** | T4.101 specific cultural review + Shawn second-pass. If reviewers disagree, escalate to user before merge. |
| Bundle analyzer overhead on CI build time | **C5 (low)** | T4.128 runs analyzer in `npm run analyze` (separate from CI build). CI build unaffected; PR comment generated from on-demand artifact. |
| Image budget exceeded by RM screenshots + mobile statics + OG fallbacks combined | **C4 (medium)** | T4.130 hard build-fail. T4.110 (RM) + T4.53a (mobile) + T4.32 (OG) all tracked under shared budget. If exceeded, descope RM screenshots first (Carlos waypoints are higher value). |
| Per-chapter LCP measurement instability (CI cold starts) | **C4 (medium)** | T4.131 takes median-of-5 runs per chapter. If variance > 200ms, escalate. |
| Cmd-K command palette + chapter shortcuts collide with browser shortcuts | **C5 (low)** | T4.118 + T4.119 ignore shortcuts when `<input>`/`<textarea>`/`[contenteditable]` focused. Browser-level shortcuts (Cmd-K = address bar in some browsers) acknowledged; we accept the platform tradeoff. |
| Save-Data hint inconsistently set by browsers | **C5 (low)** | T4.125 respects when present; behavior unchanged when absent. |
| Italic + opsz + slant axes interpolate correctly across Chrome / Safari / Firefox | **C4 (medium)** | T4.94 cross-browser snapshot fixtures committed; if Safari quirks surface, lock affected axis at static value as fallback. |
| Spanish guillemet enforcement breaks editorial copy where mixed quotes intentional | **C5 (low)** | T4.103 lint flags but allows allow-listed strings via inline comment. Manual review per flag. |

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

## Phase 18: Time-of-Day Deeper — 8 Phases, Weather, Locale (8 tasks, 60 Cx)

### T4.77 — 8-phase time-of-day expansion (dawn → night) | Cx: 10 | P0

**Description:**
Extend `useTimeOfDay` (W1) from 4 phases to 8: `dawn` (5–7am), `morning` (7–10am), `midday` (10am–2pm), `afternoon` (2–5pm), `golden-hour` (5–7pm in summer / 4:30–6pm winter), `dusk` (7–8pm), `evening` (8–10pm), `night` (10pm–5am). Each phase has its own Mapbox sky preset + accent token + ambient audio layer hook. Boundaries are sun-elevation aware (use T4.2 `calculateSunPosition`) — golden-hour fires when sun elevation between 0° and 6°.

**AC:**
- [ ] `frontend/src/lib/wall/timeOfDay.ts` exports `TimePhase` union of 8 phases
- [ ] `getMapboxSkyConfig(phase)` returns 8 distinct configs (verified by snapshot)
- [ ] `getAccentForPhase(phase)` returns 8 distinct tokens, all WCAG AAA verified
- [ ] Golden-hour boundary uses sun elevation (not wall-clock), verified for FW summer + winter
- [ ] Existing 4-phase callers migrate without regression (T4.1, T4.4 still pass)
- [ ] Vitest: each phase boundary fires correct phase at known UTC instants for FW
- [ ] Vitest: golden-hour reproduces correctly on summer-solstice and winter-solstice fixtures
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.1, T4.2

---

### T4.78 — Golden-hour accent boost + slower motion | Cx: 8 | P0

**Description:**
During `golden-hour` phase, Wall enters a special mode: accent shifts to warm amber-gold (verified AAA on dark bg), motion springs decelerate by 1.3× (config in `--spring-soft` derived multiplier), Mapbox sky atmosphere parameter intensifies sun glow. Reduced-motion: same warm accent, no spring change.

**AC:**
- [ ] During golden-hour, `data-time-phase="golden-hour"` set on `<html>`
- [ ] `--accent-current` shifts to warm amber-gold (token `--accent-golden`); AAA contrast verified on `--bg-base`
- [ ] CSS rule scales `--spring-stiffness-multiplier` to 0.77 during golden-hour (1/1.3)
- [ ] Mapbox `sky-atmosphere-sun-intensity` set higher in golden-hour preset
- [ ] Reduced-motion: accent applies, no motion change (no spring multiplier applied)
- [ ] Vitest: phase=golden-hour produces expected accent + multiplier; reduced-motion bypasses multiplier only
- [ ] Playwright visual snapshot at golden-hour fixture
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.77

---

### T4.79 — Weather awareness scaffold (cloud cover) | Cx: 10 | P1

**Description:**
Add a `useWeather()` hook that reads cloud cover (0–1) from a free no-auth API (Open-Meteo `cloudcover_low` for FW lat/lon) with daily caching. Cloud cover dampens sky brightness in `getMapboxSkyConfig` (multiply atmosphere intensity by `(1 - 0.4*cloudCover)`). On API failure, default cloudCover=0 (clear). Disabled under reduced-data hint or when offline. C4: API key risk — Open-Meteo is keyless but rate-limited; cache 24h.

**AC:**
- [ ] `frontend/src/lib/wall/weather.ts` exports `useWeather()` returning `{cloudCover: number, stale: boolean}`
- [ ] Free no-auth API used (Open-Meteo); no API key in repo
- [ ] Cache key `gowork.weather.<yyyy-mm-dd>` in localStorage; 24h TTL
- [ ] On fetch error: returns `{cloudCover: 0, stale: true}` (graceful)
- [ ] `Save-Data` connection hint respected: returns default without fetch
- [ ] Mapbox sky config consumes cloudCover when present
- [ ] Vitest: cache hit, cache miss, error path, save-data hint, stale flag
- [ ] No PII in request (lat/lon are FW public coords)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.77

---

### T4.80 — User timezone respect (not just America/Chicago) | Cx: 6 | P0

**Description:**
Currently `useTimeOfDay` may hard-code America/Chicago. Refactor to use `Intl.DateTimeFormat().resolvedOptions().timeZone` so users in NYC, LA, or Madrid see the Wall in *their* local time, not FW local time. Site map remains FW (Mapbox center) but the lighting reflects the viewer's reality. Spotlight Multiple-Selves: Maria visiting from Madrid at her 2pm sees afternoon, not 7am dawn.

**AC:**
- [ ] `useTimeOfDay` computes phase from `new Date()` localized to viewer's resolved timezone
- [ ] No hard-coded `America/Chicago` fallback in production path (only in tests)
- [ ] Phase transitions fire correctly when system clock + timezone match boundary
- [ ] Vitest: mock viewer in `Europe/Madrid` at UTC=14:00 → phase reflects Madrid 16:00 (afternoon)
- [ ] Vitest: mock viewer in `America/Los_Angeles` at UTC=14:00 → phase reflects LA 06:00 (dawn)
- [ ] SSR-safe: server returns neutral default; client hydration corrects
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.77

---

### T4.81 — Manual time-phase override toggle (a11y + demo) | Cx: 6 | P1

**Description:**
Hidden-by-default keyboard shortcut (`Cmd+Shift+T` / `Ctrl+Shift+T`) toggles a small phase-picker dialog letting user force any phase (dawn, morning, ... night). Persists in localStorage as `gowork.forcePhase`. Used for accessibility ("force night mode for photophobia") and demo-day determinism. Hidden-by-default visible to keyboard, screen reader announced.

**AC:**
- [ ] Keyboard shortcut opens `<PhaseOverrideDialog />`
- [ ] Dialog has 9 options: 8 phases + "Auto"
- [ ] Selection persists in localStorage; clears on "Auto"
- [ ] `useTimeOfDay` respects override when set, falls back to detection when "Auto"
- [ ] Dialog: focus trap, Esc closes, ARIA-labeled, AAA contrast
- [ ] Reduced-motion: no dialog enter animation
- [ ] Vitest: shortcut opens dialog; selection persists; override returns chosen phase
- [ ] Playwright: keyboard-only flow opens, selects, closes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.77

---

### T4.82 — Time-of-day affects Live Now widget styling | Cx: 4 | P1

**Description:**
Live Now widget background and accent reflect current phase: morning gets warm-tinted card, night gets cool-tinted card, golden-hour gets amber halo. Subtle (no layout shift). All phases AAA contrast for the widget's text on its tinted bg.

**AC:**
- [ ] `<LiveNowWidget />` applies CSS class `data-time-phase="<phase>"`
- [ ] Each of 8 phases has tinted bg variation in `globals.css`
- [ ] AAA contrast verified on widget text per phase
- [ ] Reduced-motion: no transition between phases (snap)
- [ ] Vitest: phase change updates data-attribute on widget; snapshot per phase
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.77

---

### T4.83 — Time-of-day ambient audio layer hook | Cx: 8 | P2

**Description:**
Audio system (W2/W3) gets per-phase ambient layer: dawn=birdsong soft, midday=city distant, evening=traffic distant, night=hum low. Each ≤ 8KB looping ogg. Disabled under reduced-motion AND opt-in via existing audio toggle. Phase change cross-fades over 2s.

**AC:**
- [ ] 4 ambient ogg loops added under `public/audio/ambient/<phase>.ogg`, ≤8KB each
- [ ] `useAmbientAudio(phase)` hook plays appropriate loop when audio toggle ON
- [ ] Cross-fade 2s on phase change (Web Audio API gain ramp)
- [ ] Reduced-motion: no cross-fade, snap to silence then new layer
- [ ] Audio toggle OFF: no audio nodes created (perf win)
- [ ] Total audio asset budget < 40KB across all 4 layers
- [ ] Vitest: hook attaches/detaches on toggle; phase change crossfades
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.77

---

### T4.84 — Smooth sky transition during scroll (interpolated) | Cx: 8 | P1

**Description:**
When user scrolls during a transition (e.g., 6:55pm → 7:05pm boundary), the sky parameters interpolate not just on time but also weighted by scroll-progress smoothness. Prevents "snap" appearance at boundary mid-scroll. Uses RAF coalescing so 60fps cap holds. Reduced-motion: snap (no scroll-coupled interp).

**AC:**
- [ ] During phase transition, scroll events feed into a single RAF that interpolates sky params
- [ ] No more than 1 Mapbox `setPaintProperty` call per RAF tick
- [ ] Frame time profiled: P95 < 16ms with this enabled
- [ ] Reduced-motion: pre-transition snap, no scroll coupling
- [ ] Vitest: RAF batching unit test (multiple scroll events → single set call)
- [ ] Playwright: scroll fast across boundary, no console warnings, no FPS drop > 10
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.3, T4.77

---

## Phase 19: Cursor Flashlight Polish — Velocity, Idle, Keyboard, Forced-Colors (5 tasks, 36 Cx)

### T4.85 — Cursor flashlight velocity-driven trail strength | Cx: 8 | P1

**Description:**
When cursor moves fast (>500px/s), a subtle motion trail appears behind the flashlight (3 ghost circles, decaying alpha 0.3 → 0.05). When slow or stationary, no trail. Reduced-motion: no trail ever.

**AC:**
- [ ] `<CursorFlashlight />` consumes `useCursorVelocity` hook (W1 if present, else add)
- [ ] Velocity > 500px/s triggers trail render (3 ghost circles, decay)
- [ ] Velocity ≤ 500: no trail; existing markers behavior unchanged
- [ ] Reduced-motion: trail disabled
- [ ] Coarse-pointer: disabled
- [ ] No reflow / layout thrash (transform-only)
- [ ] Vitest: velocity 600 → trail elements rendered; velocity 100 → no trail
- [ ] Playwright: rapid-mouse-move shows ghost trail; stationary doesn't
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7

---

### T4.86 — Idle flashlight pulse (gentle expansion) | Cx: 6 | P1

**Description:**
After 8s of cursor not moving (and not idle-state-30s yet), flashlight gently pulses radius 80 → 90 → 80 over 2.4s loop. Communicates "still alive, ready when you are". Stops on any movement. Reduced-motion: no pulse.

**AC:**
- [ ] After 8s no cursor move, pulse animation begins (CSS keyframes via spring config)
- [ ] On any pointer move, pulse cancels within 100ms
- [ ] Reduced-motion: pulse never fires
- [ ] No CPU > 1% during pulse (transform-only animation)
- [ ] Vitest: timer-based test (vi.useFakeTimers): 8s tick → pulse; movement event → cancel
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7

---

### T4.87 — Keyboard alternate flashlight: tab through markers | Cx: 8 | P0

**Description:**
Refines T4.50: when keyboard user tabs through Mapbox markers, the focused marker becomes the "flashlight center" — markers within radius brighten as if the focused marker were a cursor at that position. Combined with W3 marker accessibility, gives keyboard users the same proximity-illumination perception as mouse users. Visible focus ring on the focused marker (AAA).

**AC:**
- [ ] Mapbox markers exposed as keyboard-focusable (tabindex="0", role="button")
- [ ] On focus, flashlight position computed from marker screen position
- [ ] Other markers' opacity computed via T4.8 with focused marker as reference
- [ ] Focus ring (W1 token) visible and AAA-contrasted
- [ ] Tab order: header → first chapter → markers in sequence → next chapter
- [ ] Vitest: focus event drives flashlight position; opacity computation runs
- [ ] Playwright: tab through Chapter 5 markers, assert opacity changes per focus
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7, T4.50

---

### T4.88 — Flashlight brand-color tint per chapter | Cx: 6 | P1

**Description:**
Flashlight glow color shifts subtly per chapter to reinforce chapter identity: Chapter 1 cyan, Chapter 4 the-Wall warm, Chapter 6 cliff red-tinted, Chapter 9 horizon golden. Drawn from chapter accent tokens. Mixes with current time-phase accent (50/50 mix).

**AC:**
- [ ] `<CursorFlashlight />` reads chapter accent via `useChapterProgress`
- [ ] Glow color = mix(chapter-accent, time-phase-accent, 0.5)
- [ ] AAA contrast verified for "marker brighten in glow" effect
- [ ] Reduced-motion: still tints (color isn't motion); only no animation
- [ ] Vitest: chapter change updates glow color; mix function correct
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7, T4.77

---

### T4.89 — Flashlight respects forced-colors (Windows high contrast) | Cx: 8 | P0

**Description:**
When `(forced-colors: active)` matches (Windows high-contrast mode), flashlight disables its custom glow and instead uses `CanvasText`/`Highlight` system colors for marker emphasis. Or disables entirely if system-color emphasis would conflict. No translucent overlays (forced-colors strips them).

**AC:**
- [ ] `(forced-colors: active)` media query checked in `<CursorFlashlight />`
- [ ] When active: glow disabled, focused marker uses `outline: 2px solid Highlight`
- [ ] Markers use `CanvasText` color, no custom alpha
- [ ] Verified visually in Windows high-contrast mode + Chrome DevTools forced-colors emulation
- [ ] Vitest: matchMedia('(forced-colors: active)') mock → glow not rendered
- [ ] Playwright: emulate forced-colors, screenshot, assert no translucent layers
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.7, T4.36

---

## Phase 20: Live Now + Variable Font + OG Deeper (10 tasks, 60 Cx)

### T4.90 — Live Now: weather, uptime, deploy ID, jurisdiction | Cx: 10 | P1

**Description:**
Extend `useLiveNow` payload to include: `weather` (sunny/cloudy/rain from T4.79), `serverUptime` (process.uptime if backend, else "client"), `deployId` (Vercel `VERCEL_GIT_COMMIT_SHA` short), `jurisdiction` ("Fort Worth, TX, USA" / "Ciudad de Fort Worth, Texas, EE. UU."). Widget shows compact form; click expands.

**AC:**
- [ ] `/api/now` (or client-side compute) includes 4 new fields
- [ ] Compact widget shows 1 of 4 fields rotating every 8s (no layout shift)
- [ ] Click on widget expands to show all fields in popover
- [ ] Locale-aware jurisdiction string (EN: "Fort Worth, TX, USA"; ES: "Ciudad de Fort Worth, Texas, EE. UU.")
- [ ] Deploy ID truncated to 7 chars (no full SHA leak)
- [ ] Reduced-motion: no rotation animation, all fields stacked
- [ ] Vitest: payload shape; locale jurisdiction format; rotation timer; reduced-motion stack
- [ ] No PII in any field
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.11, T4.65, T4.79

---

### T4.91 — Live Now: active sessions counter (privacy-safe) | Cx: 6 | P2

**Description:**
Add `activeSessions` field showing approximate number of concurrent Wall viewers in last 5 minutes. Privacy-safe: no IPs stored, only a sliding-window counter incremented on first page-view per session-cookie. If backend chosen in T4.6: implement counter; else: show static "—" with tooltip "Available with backend mode".

**AC:**
- [ ] If T4.6 backend: counter increments on `/api/now` GET with new session cookie
- [ ] Privacy: no IP, no User-Agent stored; only ephemeral counter in memory
- [ ] Counter resets at process restart (acceptable for hackathon scope)
- [ ] Widget shows "{N} viewing now" with locale-aware number
- [ ] If T4.6 client-side: shows "—" with tooltip explanation
- [ ] No GDPR concern (no PII)
- [ ] Vitest (if backend): counter logic; cookie issue; window expiry
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.6, T4.65, T4.90

---

### T4.92 — Live Now click-to-expand full system status popover | Cx: 8 | P1

**Description:**
Click on Live Now widget opens a popover with full system status: time, weather, uptime, deploy, jurisdiction, sessions, last calibration. Popover focus-trapped, Esc closes, AAA contrast, reduced-motion safe.

**AC:**
- [ ] Click opens `<LiveNowPopover />` in fixed position below widget
- [ ] Popover lists all 7 fields with labels (locale-aware)
- [ ] Focus trap: tab cycles inside; Esc closes; click outside closes
- [ ] AAA contrast on all popover text
- [ ] Reduced-motion: no enter animation, snap visible
- [ ] Keyboard: widget Enter/Space opens; popover focusable contents
- [ ] Vitest: popover renders all fields; focus trap; Esc closes
- [ ] Playwright: keyboard flow opens, navigates, closes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.90

---

### T4.93 — Live Now locale-aware time format (12h US / 24h ES) | Cx: 4 | P0

**Description:**
Refines T4.10. EN locale uses 12-hour with AM/PM ("2:17 PM CST"); ES locale uses 24-hour ("14:17 CST"). Date format also locale-appropriate when shown ("April 27, 2026" vs "27 de abril de 2026"). Use `Intl.DateTimeFormat` exclusively, no manual formatting.

**AC:**
- [ ] Hour format toggles based on locale (12h en-US, 24h es-MX/es-ES)
- [ ] Month name localized when full date displayed
- [ ] Vitest: en-US → "2:17 PM"; es-MX → "14:17"; date snapshot per locale
- [ ] No manual format string concatenation in source
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.10, T4.27

---

### T4.94 — Variable font: italic axis on emphasis | Cx: 6 | P1

**Description:**
Inter Variable supports italic axis (`ital`). Apply subtle italic (ital=1) to `<em>` tags and editorial emphasis spans (e.g., the slogan italic). Verified rendering in Chrome, Safari, Firefox. Reduced-motion: no impact (italic is static).

**AC:**
- [ ] `<em>` and `.editorial-emphasis` get `font-variation-settings: 'ital' 1, 'wght' var(--current-weight)`
- [ ] Visual diff confirms slight italic vs roman in same context
- [ ] Cross-browser snapshot (Chrome, Safari, Firefox) committed as fixtures
- [ ] Vitest: computed style on `<em>` includes `'ital' 1`
- [ ] Reduced-motion: no change (italic is non-motion)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13, T4.16

---

### T4.95 — Variable font: hover boosts weight on interactive | Cx: 4 | P1

**Description:**
On `:hover` over interactive elements (chapter CTAs, header links), weight increases by 100 (e.g., 600 → 700) with 200ms tween. Adds a subtle "lean-in" feel. Reduced-motion: weight change instant (no tween).

**AC:**
- [ ] CSS rule: `a:hover, button:hover { transition: font-variation-settings 200ms ease; font-variation-settings: 'wght' calc(var(--current-weight) + 100); }`
- [ ] AAA contrast holds at boosted weight
- [ ] Reduced-motion: 0ms transition (snap)
- [ ] Vitest snapshot: hover state computed style
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13

---

### T4.96 — Variable font: focus state weight + reduced-motion lock | Cx: 4 | P1

**Description:**
On `:focus-visible`, same weight boost as hover (T4.95). Ensures keyboard users see the same emphasis cue. Under reduced-motion, weight on hero h1 locks at 800 (already in T4.13) AND no transition on hover/focus weight changes anywhere.

**AC:**
- [ ] CSS rule: `:focus-visible` triggers same weight boost as `:hover`
- [ ] Reduced-motion: all weight transitions = 0ms; hero h1 weight pinned at 800
- [ ] Keyboard focus produces same visual emphasis as mouse hover
- [ ] Vitest: focus-visible computed style matches hover
- [ ] Playwright: tab through CTAs under reduced-motion, no animation observed
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.13, T4.95

---

### T4.97 — OG image: includes wave-time stat | Cx: 6 | P1

**Description:**
Chapter OG images (T4.30) get a small "as of {time}" stamp + a key wave stat per chapter (e.g., Chapter 6 "5,189 cliff calculations" / Chapter 9 "13 sprints"). Stamp uses current time at request time (cache 1h). Adds liveness without breaking SSR cache.

**AC:**
- [ ] Each chapter OG includes per-chapter stat (config in `lib/wall/ogStats.ts`)
- [ ] Time stamp shown ("Updated 2:17 PM CST")
- [ ] Cache-control: `public, max-age=3600`
- [ ] AAA contrast on stamp + stat text
- [ ] Vitest: each chapter renders with its stat; stamp matches request time mock
- [ ] No LLM in stat path
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.30

---

### T4.98 — Localized OG (EN vs ES) per chapter | Cx: 8 | P0

**Description:**
OG endpoint accepts `?lang=es` query param, renders Spanish version of chapter title + editorial snippet. Metadata generation (T4.31) emits both `og:image` (default lang) and `og:image:alternate` for the other locale. Hreflang link tags per chapter.

**AC:**
- [ ] `/api/og/[chapter]?lang=es` renders ES copy from translated keys (T4.21–T4.25)
- [ ] `/api/og/[chapter]?lang=en` renders EN copy
- [ ] Default (no lang): EN
- [ ] `<link rel="alternate" hreflang="es" href="...?lang=es" />` per chapter
- [ ] Twitter card uses lang-detected version
- [ ] Vitest: chapter 03 ?lang=es contains Spanish title; ?lang=en contains English
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.30, T4.21–T4.25

---

### T4.99 — Spanish-specific OG image (cultural framing) | Cx: 4 | P1

**Description:**
The hero OG (chapter 01) Spanish version uses culturally-resonant phrasing: not just literal translation but framed for Hispanic civic audience ("¿Qué se interpone entre tú y un empleo?" + "Una infraestructura para cualquier ciudad estadounidense" subline). Reviewer agent + Shawn approve framing before commit.

**AC:**
- [ ] Spanish hero OG copy reviewed for cultural resonance (not literal)
- [ ] Reviewer agent approves framing against EN intent + ES register
- [ ] Shawn second-pass logged in PR
- [ ] No "MontGoWork" leak (EN or ES)
- [ ] Visual snapshot of ES OG committed
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.98, T4.21

---

## Phase 21: Spanish Parity Deeper + Edge States Branded (10 tasks, 60 Cx)

### T4.100 — Reviewer agent ES review per chapter pair (gate) | Cx: 8 | P0

**Description:**
For each translation task T4.21–T4.25, reviewer agent reads the ES copy against the EN source and checks: tone (formal-but-warm civic register), no calque, no false-friend ("application" ≠ "aplicación" for job context — "solicitud"), distance/time/money locale conventions, anticipatory voice preserved. Reviewer comment becomes a gate — translation cannot merge until reviewer approves.

**AC:**
- [ ] Reviewer-agent prompt template at `prompts/reviewer-spanish.md` codified
- [ ] Each of T4.21–T4.25 PR has reviewer-agent comment with explicit "approved" or "needs work"
- [ ] Approval is a required CI status check (block merge if missing/failing)
- [ ] If "needs work": specific quotes flagged with suggested rewrite
- [ ] Vitest: reviewer prompt loads and includes required register guidance
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves (meta: agent reviews itself's approval flow)

**Depends on:** T4.21, T4.22, T4.23, T4.24, T4.25

---

### T4.101 — Cultural review: Carlos story tone in Spanish | Cx: 6 | P0

**Description:**
Specific cultural review of Chapters 3 and 7 (Carlos's narrative). Avoids savior-narrative. Treats Carlos as protagonist not victim. Verifies "Tarrant County District Clerk" parenthetical doesn't read condescending. Confirms Carlos's voice in Spanish is dignified, not sentimentalized. Reviewer + Shawn second-pass.

**AC:**
- [ ] Specific review comment on Chapters 3 + 7 ES translations addressing dignity / agency framing
- [ ] No "pobre Carlos" / pity-tone
- [ ] Carlos's choices highlighted (active voice in ES)
- [ ] "Distrito Judicial del Condado de Tarrant" with EN parenthetical reads functional, not condescending
- [ ] Reviewer agent approves; Shawn logs second-pass
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.22, T4.24

---

### T4.102 — "Ciudad de Fort Worth" formal naming convention | Cx: 4 | P0

**Description:**
In ES copy, formal civic naming: first reference "Ciudad de Fort Worth (City of Fort Worth)"; subsequent "Fort Worth" or "la ciudad". Style guide entry in `docs/spanish-style.md` codifies this. CI lint (`scripts/i18n-style.mjs`) flags violations in `es.json`.

**AC:**
- [ ] `docs/spanish-style.md` written with formal-naming rule + examples
- [ ] All ES references to FW use formal first-mention pattern
- [ ] `scripts/i18n-style.mjs` lints es.json for "Fort Worth" without prior "Ciudad" mention in same string block
- [ ] Vitest: lint script unit test (positive + negative fixtures)
- [ ] CI invokes lint script
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.21–T4.25

---

### T4.103 — Spanish quotes formatting (« » vs " ") | Cx: 4 | P1

**Description:**
ES copy uses Spanish guillemets (« ») for primary quotes per RAE convention, not English curly quotes. Lint script (T4.102) extended to flag `"` in es.json string values. Manual review confirms guillemet usage where appropriate.

**AC:**
- [ ] All quoted phrases in es.json use « »
- [ ] Lint flags `"…"` (English curly) in es.json
- [ ] EN files unchanged (still use English curly)
- [ ] Vitest: lint detects English quotes in ES fixture
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.102

---

### T4.104 — Locale-aware date/currency/number formatting helpers | Cx: 8 | P0

**Description:**
`lib/i18n/format.ts` exports `formatCurrency(value, locale)`, `formatNumber(value, locale)`, `formatDate(date, locale)`. Uses `Intl` APIs. Used everywhere a number/date/dollar appears (cliff math, stat band, Live Now). EN uses "$2,400.00" + "Apr 27, 2026"; ES uses "$2,400.00" but "27 de abril de 2026" + comma decimal optional ("$2.400,00" if user pref).

**AC:**
- [ ] Three functions exported from `lib/i18n/format.ts`
- [ ] Used in: cliff math output, Chapter 9 stat band, Live Now widget time/date
- [ ] EN: "$2,400.00", "Apr 27, 2026", "1,234"
- [ ] ES: "$2,400.00" (USD stays USD format), "27 de abril de 2026", "1.234"
- [ ] Vitest: 6 cases (3 functions × 2 locales)
- [ ] No manual format strings remain in chapter components (grep audit clean)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.27

---

### T4.105 — Hreflang per chapter + Spanish accessibility statement | Cx: 6 | P1

**Description:**
Add `<link rel="alternate" hreflang="en|es|x-default" href="..." />` per chapter URL. Add Spanish accessibility statement at `/accesibilidad` mirroring EN at `/accessibility` (W1 should have placeholder; verify and translate).

**AC:**
- [ ] Hreflang tags emitted in `<head>` for all routes via `generateMetadata`
- [ ] x-default points to EN
- [ ] `/accesibilidad` page renders with full ES translation of accessibility statement
- [ ] /accessibility unchanged (EN); /accesibilidad mirrors structure
- [ ] Footer link to accessibility statement uses locale-correct URL
- [ ] Vitest: route returns ES content; hreflang tags present in metadata
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.27

---

### T4.106 — Branded 404: "There's no path to this URL — but there is one through the wall" | Cx: 6 | P0

**Description:**
Refines T4.34. The 404 page becomes editorial: large path-line graphic (terminating short of destination), branded copy "There's no path to this URL — but there is one through the wall." with CTA "Start at the wall →". Spanish: "No hay camino a esta URL — pero hay uno a través del muro." Subtle: path graphic respects reduced-motion (no draw animation).

**AC:**
- [ ] `app/not-found.tsx` renders editorial layout with path-line SVG
- [ ] EN copy: "There's no path to this URL — but there is one through the wall."
- [ ] ES copy: "No hay camino a esta URL — pero hay uno a través del muro."
- [ ] CTA button: "Start at the wall →" / "Comienza en el muro →" linking to /
- [ ] Path SVG draws on mount with 1.2s spring; reduced-motion: instant render
- [ ] AAA contrast verified
- [ ] Vitest: page renders both locales correctly; reduced-motion bypasses draw
- [ ] Playwright: visit /bogus → screenshot per locale + reduced-motion
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.34, T4.26

---

### T4.107 — Branded 500: "Something stalled. We're calibrating." with calibrating motif | Cx: 6 | P0

**Description:**
Refines T4.34. The 500 page shows a subtle "calibrating" motif — a path-line whose dots pulse asymmetrically, suggesting recalibration in progress. EN/ES copy. Auto-retry button. Reduced-motion: no pulse.

**AC:**
- [ ] `app/error.tsx` renders calibrating motif (3 dots pulsing in sequence)
- [ ] EN: "Something stalled. We're calibrating."
- [ ] ES: "Algo se detuvo. Estamos calibrando."
- [ ] "Try again" button calls `reset()` (Next.js error boundary)
- [ ] Subline: "If this keeps happening, the wall remembers."
- [ ] Reduced-motion: dots static
- [ ] AAA contrast
- [ ] Vitest: error boundary renders; reset clears state
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.34, T4.26

---

### T4.108 — Branded empty + loading states | Cx: 4 | P1

**Description:**
Empty state copy: "No path to here yet" / "Aún no hay camino aquí". Loading: skeleton with subtle 2s shimmer (reduced-motion: static gray). All branded, no default Material-style spinners.

**AC:**
- [ ] `<EmptyState />` renders branded copy + path-line vestige icon
- [ ] `<LoadingState />` renders skeleton with shimmer
- [ ] Reduced-motion: shimmer static
- [ ] Both available in EN + ES
- [ ] No `<CircularProgress>` or default-spinner imports remain (grep audit)
- [ ] Vitest: both states render in both locales
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.35, T4.26

---

### T4.109 — Per-component error boundary with branded copy | Cx: 8 | P1

**Description:**
Each chapter component wrapped in a small error boundary that catches its render errors and shows the branded calibrating message inline (not whole-page replacement). Allows other chapters to still render. EN/ES.

**AC:**
- [ ] `<ChapterErrorBoundary />` HOC wraps every chapter component (1–10)
- [ ] On render error: shows inline calibrating motif + "This section stalled. Continue scrolling — the rest works." / "Esta sección se detuvo. Continúa desplazándote — el resto funciona."
- [ ] Other chapters still render
- [ ] Telemetry: error logged to console (no external) for debug
- [ ] Reduced-motion: motif static
- [ ] Vitest: throwing chapter triggers boundary; other chapters render
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.107

---

## Phase 22: Reduced-Motion + WCAG AAA + Keyboard + Screen Reader Deeper (12 tasks, 80 Cx)

### T4.110 — Reduced-motion screenshot fallbacks for camera flights | Cx: 8 | P0

**Description:**
For each Mapbox camera flight in chapters 1–9 (~15 flights), generate a destination-state screenshot at build time. Reduced-motion users see the destination screenshot instantly instead of waiting (T4.44 already does jumpTo, this adds visual confirmation if jumpTo is briefly blank). Stored at `public/wall/rm/flight-<chapter>-<n>.png`.

**AC:**
- [ ] Build script `scripts/build-rm-flights.mjs` captures ~15 destination screenshots
- [ ] Each PNG ≤ 100KB (compressed)
- [ ] Total budget < 1.5MB (under image budget T4.130)
- [ ] Reduced-motion path renders screenshot immediately, then jumpTo (so map state correct on next interaction)
- [ ] Vitest: script unit test (mock Playwright captures expected count)
- [ ] Playwright: under reduced-motion, no flight animations observed; screenshots present
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.44, T4.53a

---

### T4.111 — Carlos avatar: 5 still images at 5 path positions | Cx: 6 | P0

**Description:**
For Chapter 7 reduced-motion fallback (T4.45), create 5 still PNGs of Carlos avatar at 5 path waypoints (start, week-1, week-3, week-7, week-12 endpoint). Reduced-motion user sees avatar at endpoint, but on scroll-progress a waypoint image swaps in (no animation, just discrete swap). Conveys path progress without motion.

**AC:**
- [ ] 5 PNGs at `public/wall/rm/carlos-<position>.png`, ≤ 30KB each
- [ ] Chapter 7 reduced-motion path: discrete image swap on scroll milestones
- [ ] Endpoint state remains semantic (full path drawn, all labels)
- [ ] Alt text per image describes Carlos's progress at that waypoint
- [ ] Vitest: scroll milestones swap images; no motion props applied
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.45

---

### T4.112 — 3D barrier graph: paused PNG fallback rotation | Cx: 4 | P0

**Description:**
T4.46 already renders static PNG under reduced-motion. Extend: 3 paused PNGs at different rotation angles; on scroll milestones in Chapter 8, image swaps among the 3 (discrete, not animated). User perceives "structure has many faces" without orbital animation.

**AC:**
- [ ] 3 PNGs at `public/wall/rm/constellation-<angle>.png`, ≤ 80KB each
- [ ] Chapter 8 reduced-motion: image swaps on scroll milestones
- [ ] No Three.js mount under reduced-motion (T4.46 invariant preserved)
- [ ] Alt text varies per angle describing emphasized cluster
- [ ] Vitest: scroll milestones swap; no Canvas in DOM
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.46

---

### T4.113 — WCAG AAA per-state contrast (hover/focus/active/disabled) | Cx: 10 | P0

**Description:**
T4.40 verifies base token contrast. Extend to verify hover/focus/active/disabled states each meet AAA (7:1 normal, 4.5:1 large). Disabled states tend to fail (gray-on-gray). Token-level fix: redefine `--fg-disabled` to maintain ≥4.5:1 contrast on `--bg-disabled`. Script extended to enumerate all 4 states × all interactive components.

**AC:**
- [ ] `scripts/verify-contrast.mjs` extended to test 4 states per interactive
- [ ] Disabled state: ≥ 4.5:1 (large) verified for buttons, links, inputs
- [ ] Hover/focus/active: ≥ 7:1 verified for normal text
- [ ] Token redefinitions made if needed (no rule-skip)
- [ ] CI invokes extended script
- [ ] Vitest: per-state ratio computation; disabled-state catch
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.40

---

### T4.114 — Forced-colors mode (Windows high-contrast) full sweep | Cx: 8 | P0

**Description:**
Test every chapter in Windows high-contrast mode (or Chromium DevTools forced-colors emulation). Custom CSS using `currentColor`, `CanvasText`, `Highlight` system colors. No translucent backgrounds (forced-colors strips alpha). All gradients use system color stops or are replaced with solids.

**AC:**
- [ ] Each chapter screenshot under forced-colors emulation
- [ ] Text readable everywhere (no white-on-white)
- [ ] Borders visible on all interactive (forced-colors uses `Highlight` for focused)
- [ ] No gradient backgrounds invisible under forced-colors
- [ ] Path-line, brand mark, focus rings all visible
- [ ] Playwright: emulate forced-colors, no `pixmatch` tolerance failures > threshold
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.36

---

### T4.115 — prefers-contrast: more support | Cx: 6 | P1

**Description:**
For users requesting more contrast (`(prefers-contrast: more)`), bump body text contrast from 7:1 to 12:1 by darkening bg or lightening fg further. Disable subtle accents that may dim text. Verified per chapter.

**AC:**
- [ ] CSS `@media (prefers-contrast: more) { ... }` block bumps text contrast tokens
- [ ] Glass cards: opacity raised to 0.95 (less translucent)
- [ ] Subtle accent tints disabled (revert to base token)
- [ ] Playwright: emulate prefers-contrast: more, screenshot, manual review
- [ ] No layout shift between modes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.40, T4.113

---

### T4.116 — Color-blind safe palette verification (deuteranopia, protanopia, tritanopia) | Cx: 6 | P0

**Description:**
Verify Wall accent palette under 3 types of color-blindness simulation. Cliff zones (Chapter 6: red/yellow/green) need particular attention — add shape/pattern encoding alongside color. Use ColorOracle or Playwright + filter SVG. Document any palette adjustment.

**AC:**
- [ ] Chapter 6 cliff zones use shape encoding (squares for green, triangles for yellow, circles for red) in addition to color
- [ ] Deuteranopia simulation: cliff zones distinguishable
- [ ] Protanopia simulation: distinguishable
- [ ] Tritanopia simulation: distinguishable
- [ ] No information conveyed by color alone (anywhere)
- [ ] Playwright: 3 filter overlays, screenshot per chapter, manual diff review
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.40, W3 Chapter 6

---

### T4.117 — Underlines on body-text links + skip-to-content visible on focus | Cx: 4 | P0

**Description:**
WCAG: links in body text must be distinguishable beyond color. Add underline (2px solid, 2px offset) to all links in `prose` regions. Skip-to-content link, hidden by default, becomes visible (slides into top-left) on focus.

**AC:**
- [ ] CSS: `.prose a { text-decoration: underline; text-underline-offset: 2px; }`
- [ ] Skip-to-content: `position: absolute; top: -40px;` becomes `top: 8px` on `:focus`
- [ ] Skip jumps to `<main id="main">`
- [ ] AAA contrast on link underline
- [ ] Vitest: skip link focus moves to main; underline applied to body links
- [ ] Playwright: tab once, skip link visible, AAA contrast
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.38, T4.39

---

### T4.118 — Chapter shortcuts: 1-0 jumps to chapters; vim j/k for next/prev | Cx: 8 | P0

**Description:**
Keyboard power-user shortcuts: digit `1` jumps to Chapter 1, `2` → Chapter 2, ..., `0` → Chapter 10. Vim-style `j` = next chapter, `k` = previous. Shortcuts ignored when focus is in input/textarea. Surfaced via `?` shortcut → opens cheat-sheet dialog.

**AC:**
- [ ] `useKeyboardShortcuts()` hook in `lib/hooks/useKeyboardShortcuts.ts`
- [ ] Digits 1–9, 0 → scroll to chapter (smooth; reduced-motion: instant)
- [ ] j/k → next/prev chapter
- [ ] `?` opens `<KeyboardShortcutDialog />` listing all shortcuts (EN/ES)
- [ ] Shortcuts disabled when active element is `<input>`, `<textarea>`, `[contenteditable]`
- [ ] Esc closes dialog; focus restored to prior element
- [ ] Vitest: keypress triggers correct scroll target; input-focused state ignores
- [ ] Playwright: full keyboard journey through chapters
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.38

---

### T4.119 — Cmd-K skip-to-chapter dialog | Cx: 6 | P1

**Description:**
`Cmd-K` / `Ctrl-K` opens a command palette listing all 10 chapters by title (locale-aware). Type-to-filter. Enter jumps. Esc closes. Like Linear/GitHub command-K. Adds power-user delight + keyboard accessibility.

**AC:**
- [ ] `<CommandPalette />` component with 10 chapter entries (locale-aware titles)
- [ ] Cmd-K / Ctrl-K opens palette anywhere on Wall
- [ ] Fuzzy match on chapter title; arrow keys navigate; Enter selects
- [ ] Reduced-motion: no enter animation
- [ ] AAA contrast; focus trap; Esc closes
- [ ] Vitest: open, filter, select, close flow
- [ ] Playwright: keyboard-only happy path
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.118

---

### T4.120 — ARIA-live: chapter announcements + Live Now updates voiced | Cx: 6 | P0

**Description:**
Refines T4.54. ARIA-live polite region announces chapter changes ("Chapter 4: The Wall" / "Capítulo 4: El Muro"). For Live Now updates, the popover (T4.92) uses ARIA-live polite when expanded so a screen reader hears time updates; collapsed widget uses `aria-live="off"` (too noisy). Cliff math result (Chapter 6) voiced when slider released.

**AC:**
- [ ] Chapter band live-region announces localized chapter name on transition
- [ ] Cliff math (Chapter 6) on slider `change` (not input): live-region voices "Income: $X. After-cliff: $Y. Difference: $Z." / Spanish equivalent
- [ ] Live Now popover: aria-live polite when open, off when closed
- [ ] Debounce: no over-announcement (300ms)
- [ ] Vitest: live region content updates per chapter; cliff voicing on change
- [ ] Manual VoiceOver + NVDA verification logged
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.54, T4.92

---

### T4.121 — 3D graph + Carlos avatar: text alternative + position announced | Cx: 8 | P0

**Description:**
3D graph (Chapter 8) has full text alternative via `<details><summary>Text description of barrier graph</summary>...33 barriers, grouped into 5 categories: criminal record (8), transit (5), childcare (4), credit (7), licensing (9). 53 connections show how barriers reinforce: ...</details>`. Carlos avatar (Chapter 7): position announced via aria-live ("Carlos at week 3: appointment booked, transit pass arrived").

**AC:**
- [ ] Chapter 8 has `<details>` with full barrier graph description (locale-aware)
- [ ] Chapter 7 Carlos position: aria-live polite voices week labels on milestone cross
- [ ] Both accessible via screen reader rotor (heading or landmark)
- [ ] Reduced-motion: text alt always visible (not collapsed)
- [ ] Vitest: details renders correct content per locale; aria-live fires on Carlos milestones
- [ ] VoiceOver + NVDA verification logged
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.46, T4.45, T4.54

---

## Phase 23: Mobile Deeper + Performance Deeper + Integration (13 tasks, 102 Cx)

### T4.122 — Mobile chapter-specific layouts (not just static) | Cx: 12 | P0

**Description:**
T4.52a renders static images on mobile. Refine: each chapter gets a *purposeful* mobile layout, not just "image + text below". Chapter 6 (cliff): mobile slider component (touch-driven, larger thumb). Chapter 7 (Carlos): vertical timeline (top-to-bottom). Chapter 8 (graph): 2D SVG static (Three.js too heavy on mobile). Chapter 9 (any city): tap-to-fly card list. Chapters 1–5: static image + editorial. Chapter 10: large CTA.

**AC:**
- [ ] Mobile-specific React components for chapters 6, 7, 8, 9, 10
- [ ] Chapter 6 mobile: touch-optimized cliff slider; ARIA + math accessibility intact
- [ ] Chapter 7 mobile: vertical timeline; reduced-motion compatible
- [ ] Chapter 8 mobile: 2D SVG constellation (no Three.js)
- [ ] Chapter 9 mobile: tap-list of cities (FW + Montgomery), tap fades to that city's hero
- [ ] Chapter 10 mobile: full-width CTA, footer compressed
- [ ] Chapters 1–5 mobile: static images + scrollable editorial (T4.52a)
- [ ] All mobile components AAA contrast
- [ ] Vitest per mobile component (5 new component tests)
- [ ] Playwright at 360x640: each chapter renders correctly
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.52a

---

### T4.123 — Mobile touch gestures: swipe between chapters | Cx: 8 | P1

**Description:**
On mobile, horizontal swipe (left = next chapter, right = previous) navigates. Vertical scroll within chapter unchanged. Swipe threshold: 50px horizontal × <30px vertical. Reduced-motion: no swipe animation, instant scroll-to. Configurable in settings (off by default to avoid accidental gestures).

**AC:**
- [ ] `useSwipeGesture()` hook in `lib/hooks/useSwipeGesture.ts`
- [ ] Mobile-only attached (skipped on `pointer: fine`)
- [ ] Threshold: |dx| > 50, |dy| < 30, duration < 500ms
- [ ] Disabled by default; toggle in settings (`gowork.swipeNav` localStorage)
- [ ] On chapter change: smooth scroll (or instant under reduced-motion)
- [ ] Vitest: gesture detection unit test (synthesized touch events)
- [ ] Playwright mobile: enable swipe, swipe left, asserts chapter advanced
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.122

---

### T4.124 — Mobile vibration on chapter change (opt-in) | Cx: 4 | P2

**Description:**
On chapter change via swipe (T4.123), trigger `navigator.vibrate(8)` for subtle haptic confirmation. Opt-in only (off by default; toggle in settings). Disabled under reduced-motion (vibration is a motion equivalent for tactile users). C4: iOS Safari does not support Vibration API — degrade silently.

**AC:**
- [ ] On chapter change: `navigator.vibrate(8)` if `gowork.haptics === 'on'`
- [ ] Off by default; user enables via settings
- [ ] Reduced-motion: vibration suppressed (motion is implicit consent surface)
- [ ] iOS Safari: silent no-op (feature-detect `'vibrate' in navigator`)
- [ ] Vitest: feature-detect path; opt-in flag honored
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.123

---

### T4.125 — Save-Data hint + Battery API reduced-motion under 20% | Cx: 6 | P1

**Description:**
Respect `Save-Data: on` connection hint: skip weather fetch (T4.79), skip ambient audio (T4.83), skip OG-stat fetch (T4.97). Use Battery API (`navigator.getBattery()`): if battery < 20%, treat as reduced-motion (skip animations, smaller mobile images). C5: Battery API deprecated in some browsers — feature-detect, degrade silently.

**AC:**
- [ ] `lib/wall/connectionHints.ts` exports `useSaveData()` and `useLowBattery()`
- [ ] Save-Data: ambient audio + weather + OG-stat fetches all gated off
- [ ] Battery < 20% (where supported): treat as reduced-motion (forwards to `usePrefersReducedMotion`)
- [ ] Where Battery API unsupported (Safari, FF): no-op, no warning
- [ ] Vitest: save-data hint mock; battery-low mock; both feature-undetected fallback
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.79, T4.83

---

### T4.126 — Lighthouse per-chapter score + CI tracking | Cx: 10 | P0

**Description:**
Lighthouse run produces per-chapter score (run on `?chapter=01` URL through `?chapter=10`, plus `/`). Scores written to `frontend/lighthouse-trend.json` (timestamp + chapter + 4 categories). CI commits trend file on main; PR comment shows per-chapter delta vs main baseline.

**AC:**
- [ ] `.github/workflows/lighthouse.yml` runs on 11 routes (10 chapters + /)
- [ ] Trend JSON appended on main: `{ts, sha, route, perf, a11y, bp, seo}`
- [ ] PR comment: table of per-route deltas vs main
- [ ] Regression > 5 points on any route fails the gate (hard)
- [ ] Vitest: trend file parser unit test
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.55, T4.58

---

### T4.127 — Lighthouse trend over time (chart in docs) | Cx: 4 | P1

**Description:**
`docs/perf/lighthouse-trend.md` rendered with Mermaid line chart from `lighthouse-trend.json`. Shows performance score trajectory over last 30 days. Updated automatically by CI. Provides judging-day evidence of performance discipline.

**AC:**
- [ ] Script `scripts/render-lh-trend.mjs` reads JSON, emits Mermaid chart in markdown
- [ ] CI invokes script on main merge
- [ ] `docs/perf/lighthouse-trend.md` regenerated; commit if changed
- [ ] Chart shows last 30 days of scores per route
- [ ] Vitest: render script unit test (fixture JSON → expected Mermaid)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.126

---

### T4.128 — Bundle analyzer treemap report (per build) | Cx: 8 | P0

**Description:**
Add `@next/bundle-analyzer` (or `webpack-bundle-analyzer`). On `npm run build`, generates treemap HTML at `frontend/.next/analyze/client.html`. CI uploads as PR artifact. Compares against `baseline-bundle-sizes.json` — if any chunk grows > 10KB, comment on PR.

**AC:**
- [ ] Bundle analyzer wired into Next.js config (`@next/bundle-analyzer`)
- [ ] `npm run analyze` produces HTML treemap
- [ ] CI uploads treemap as artifact on every PR
- [ ] Diff script flags chunks > +10KB vs baseline; comment posted
- [ ] Vitest: diff script (fixture before/after sizes)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.55

---

### T4.129 — Tree-shaking + dead-code-elimination verification | Cx: 6 | P1

**Description:**
Audit imports across `frontend/src` for star imports (`import * from`) and large barrel files that prevent tree-shaking. Replace with named imports. Verify icon library imports use deep paths (e.g., `lucide-react/icons/specific` not `lucide-react`). Document audit in PR.

**AC:**
- [ ] Grep audit: zero `import * as X from` in `frontend/src` (allowlist test files only)
- [ ] Icon imports use deep paths; bundle size dropped accordingly
- [ ] Mapbox GL JS: only used modules imported (no full `mapbox-gl`)
- [ ] Bundle analyzer (T4.128) shows no unexpected large barrel imports
- [ ] Vitest: lint script flags star imports in src/
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.128

---

### T4.130 — Image budget enforcement + font budget enforcement | Cx: 8 | P0

**Description:**
`lib/wall/perfBudget.ts` (T4.55) extended with `IMAGE_BUDGET_KB` (per route ≤ 600KB) and `FONT_BUDGET_KB` (≤ 90KB). CI script `scripts/check-budgets.mjs` reads `.next/analyze/` outputs, asserts per-route image and font sizes within budget. Fails build if exceeded. OG fallback PNGs (T4.32) and mobile PNGs (T4.53a, T4.110) all counted.

**AC:**
- [ ] `IMAGE_BUDGET_KB` and `FONT_BUDGET_KB` constants exported from perfBudget.ts
- [ ] Check script computes per-route image + font weight
- [ ] Build fails if any route exceeds budget
- [ ] OG fallbacks, mobile statics, RM screenshots, Carlos waypoints all counted
- [ ] Vitest: check script (fixture under/over budget)
- [ ] CI invokes; output as PR comment
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.55, T4.110, T4.111

---

### T4.131 — Code splitting per chapter verified + LCP per chapter measured | Cx: 8 | P0

**Description:**
Each chapter component dynamically imported via `next/dynamic` (W2/W3 may already do this; verify). LCP measured per chapter via Lighthouse run (T4.126). If a chapter's LCP > 2.5s, escalate. Chapter 8 (Three.js) is highest risk.

**AC:**
- [ ] Each chapter is in its own JS chunk (verified via bundle analyzer)
- [ ] No chapter chunk > 80KB gzipped (Three.js for Chapter 8 separately bundled, ≤ 120KB)
- [ ] Per-chapter LCP recorded in trend JSON
- [ ] Chapter 8 LCP < 2.5s (or fallback to 2D SVG triggered)
- [ ] Vitest: bundle splitting structural test (parse build output)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.126, T4.128

---

### T4.132 — CLS per chapter measured + locked < 0.05 | Cx: 6 | P0

**Description:**
Per-chapter CLS measured. Most likely culprits: Live Now widget appearing late, Carlos avatar appearing without reserved space, OG image lazy-load shifts. Reserve space for all dynamic elements (`min-height` or aspect-ratio CSS). Verified via per-chapter Lighthouse + Web Vitals lib.

**AC:**
- [ ] All async-render elements have reserved layout space (`min-height` or `aspect-ratio`)
- [ ] Live Now widget reserves space in header at SSR
- [ ] Carlos avatar reserves space at chapter mount
- [ ] Per-chapter CLS recorded in trend; all chapters < 0.05
- [ ] Vitest: snapshot of reserved-space CSS for each async element
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.126

---

### T4.133 — 12 life-layers compound integration test (all firing) | Cx: 14 | P0

**Description:**
**Spotlight invention (extends T4.69).** Specifically targets the 12 enriched life-layers firing simultaneously: 8-phase TOD + golden-hour boost + weather + cursor flashlight + flashlight velocity trail + flashlight idle pulse + variable font weight + variable font italic + Live Now polling + Spanish locale + reduced-motion (subset) + chapter shortcuts active. Playwright runs the journey, asserts no interaction conflicts, no NaN, no console errors, no frame drops > 10%.

**AC:**
- [ ] Playwright test in `frontend/e2e/compound-life-layers.spec.ts`
- [ ] Test runs at 7pm fixture (golden-hour), ES locale, weather=cloudy fixture
- [ ] All 10 chapters traversed via `j` key (T4.118 vim shortcut)
- [ ] Zero console errors / warnings
- [ ] Zero NaN in computed styles
- [ ] FPS measured: P95 frame time < 16ms × 1.1 (10% headroom)
- [ ] CLS < 0.1 over the journey
- [ ] No memory leak: heap size after journey within 20% of pre
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.69, T4.77, T4.78, T4.79, T4.85, T4.86, T4.94, T4.118

---

### T4.134 — Live Now + cursor flashlight + audio compound integration test | Cx: 8 | P0

**Description:**
**Spotlight invention (extends T4.69).** Specific compound: open Live Now popover (T4.92) while cursor flashlight is active in idle pulse mode (T4.86) and ambient audio crossfading (T4.83) at golden-hour. Verify popover focus trap doesn't kill flashlight, audio doesn't glitch on focus shift, no z-index conflicts.

**AC:**
- [ ] Playwright opens popover, asserts flashlight still tracking (or paused while popover open)
- [ ] Audio crossfade not interrupted by popover focus
- [ ] Z-index: popover above map, below skip-to-content link
- [ ] Esc closes popover, focus returns to widget, flashlight resumes
- [ ] CI invokes
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T4.92, T4.86, T4.83

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
| 18 TOD Deeper (8 phases, weather, golden-hour, locale) | 8 | 60 | 8-phase, golden-hour boost, weather, timezone, override, widget tint, ambient audio, scroll-coupled sky |
| 19 Cursor Flashlight Polish | 5 | 36 | Velocity trail, idle pulse, kbd marker tab, chapter tint, forced-colors |
| 20 Live Now + Variable Font + OG Deeper | 10 | 60 | Weather/uptime/deploy/jurisdiction, sessions, popover, locale time, italic/opsz/hover/focus axes, OG stat, localized OG, ES OG |
| 21 ES Parity Deeper + Branded Edge States | 10 | 60 | Reviewer gate, Carlos cultural review, Ciudad de FW, guillemets, format helpers, hreflang, branded 404/500/empty/loading, error boundary |
| 22 RM + AAA + Keyboard + SR Deeper | 12 | 80 | RM screenshots, Carlos waypoints, paused 3D PNG, per-state contrast, forced-colors, prefers-contrast, color-blind, link underlines, 1–0/j/k, Cmd-K, ARIA-live cliff/Carlos, 3D text alt |
| 23 Mobile + Performance + Integration Deeper | 13 | 102 | Mobile chapter-specific layouts, swipe, vibration, save-data/battery, per-chapter LH score, trend chart, bundle analyzer, tree-shaking, image/font budgets, code-split verify, CLS per chapter, 12-layer compound, popover×flashlight×audio compound |
| **Total** | **132** | **1002** | |

## Priority order (recommended execution)

**Wave 1 (parallel, independent foundations):** T4.6 (Live Now decision — blocking), T4.20 (i18n audit), T4.40 (contrast script), T4.43 (RM audit), T4.50a (mobile detection), T4.55 (perf budget module), T4.16 (font preload), T4.30 (Satori OG endpoint).

**Wave 2 (parallel, depends on wave 1):** T4.1, T4.2, T4.7, T4.8, T4.10, T4.13, T4.21–T4.26 (Spanish translations parallelize chapter-by-chapter), T4.27, T4.28, T4.34, T4.35, T4.41, T4.44–T4.47, T4.36, T4.38, T4.39, T4.51a, T4.52a.

**Wave 3 (depends on wave 2):** T4.3, T4.4, T4.5, T4.9, T4.11, T4.12, T4.14, T4.15, T4.31, T4.32, T4.33, T4.37, T4.42, T4.50, T4.51, T4.52, T4.53, T4.54, T4.56, T4.58, T4.49 (HOC extraction; refactors chapter components), T4.62, T4.65, T4.59, T4.61, T4.53a.

**Wave 4 (gates + integration):** T4.29 (i18n CI), T4.57 (descope if needed), T4.60, T4.63, T4.66 (final Lighthouse), T4.67–T4.76 (test suite).

**Wave 5 — Enrichment Pass (parallel where possible, gated on respective wave-2/3 foundations):**
- *Foundations (start with wave 1):* T4.77 (8-phase TOD), T4.80 (timezone), T4.100 (ES reviewer gate template), T4.102 (ES style guide), T4.104 (format helpers), T4.118 (chapter shortcuts), T4.126 (per-chapter LH), T4.128 (bundle analyzer), T4.130 (image/font budgets).
- *Build on wave 2:* T4.78 (golden-hour), T4.79 (weather), T4.81 (override), T4.82 (widget tint), T4.85 (velocity trail), T4.86 (idle pulse), T4.87 (kbd marker tab), T4.88 (chapter tint), T4.89 (forced-colors), T4.94 (italic axis), T4.95 (hover weight), T4.96 (focus weight), T4.98 (localized OG), T4.99 (ES OG framing), T4.101 (Carlos cultural review), T4.103 (guillemets), T4.105 (hreflang + ES a11y), T4.106 (branded 404), T4.107 (branded 500), T4.108 (empty/loading), T4.110 (RM screenshots), T4.111 (Carlos waypoints), T4.112 (paused 3D), T4.113 (per-state contrast), T4.114 (forced-colors sweep), T4.115 (prefers-contrast), T4.116 (color-blind), T4.117 (link underlines + skip), T4.119 (Cmd-K), T4.122 (mobile chapter layouts), T4.123 (swipe), T4.124 (vibration), T4.125 (save-data/battery), T4.127 (LH trend chart), T4.129 (tree-shaking), T4.131 (code-split verify), T4.132 (CLS per chapter).
- *Wave 3+ build:* T4.83 (ambient audio P2), T4.84 (scroll-coupled sky), T4.90 (LN extras), T4.91 (sessions P2), T4.92 (popover), T4.93 (locale time), T4.97 (OG stat), T4.109 (per-component error boundary), T4.120 (ARIA-live cliff/Carlos), T4.121 (3D text alt).
- *Wave 4 integration:* T4.133 (12-layer compound, enriched), T4.134 (LN×flashlight×audio compound).

**Hard gate:** T4.66 + T4.126 + T4.130 + T4.133 must all pass before W4 is closed. (Lighthouse Performance ≥ 90 on simulated 4G + per-chapter LH no regression > 5pts + image/font budgets within thresholds + 12-layer compound test green.)

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
| 8-phase TOD perf regression on mid-tier mobile | T4.84 RAF batching; T4.133 compound test asserts P95 frame time; descope to 4-phase if miss |
| Open-Meteo API outage on judging day | T4.79 24h cache + graceful fallback to clear sky |
| Forced-colors mode breaks Mapbox canvas rendering | T4.89 + T4.114 disable custom overlays; document acceptable degradation for tile rendering itself |
| Image budget exceeded by RM screenshots + mobile statics + OG fallbacks combined | T4.130 hard build-fail; descope ladder: drop RM camera screenshots first |
| Spanish reviewer gate creates merge bottleneck | T4.100 codifies prompt; reviewer auto-runs on PR open |
| Carlos cultural framing in Spanish slips into paternalism | T4.101 specific cultural review + Shawn second-pass |
| Vibration / Battery API silently absent on iOS Safari / FF | T4.124 + T4.125 feature-detect, no-op silently |
| Cmd-K conflicts with browser address-bar shortcut | T4.119 ignores when input/textarea focused; platform tradeoff documented |
| Italic / opsz / slant axes interpolate inconsistently across browsers | T4.94 cross-browser fixtures; lock affected axis to static if Safari quirks surface |
| Per-chapter LCP measurement variance from CI cold-starts | T4.131 median-of-5 runs per chapter; escalate if variance > 200ms |

## Success criteria for W4 closure

- [ ] All 12 life-layers wired and verified (base + enrichment pass)
- [ ] 8-phase time-of-day live with golden-hour boost; viewer-timezone respected (T4.77, T4.78, T4.80)
- [ ] Weather scaffold present with graceful fallback (T4.79)
- [ ] Spanish parity sweep complete: zero missing es.json keys (T4.29 CI gate green)
- [ ] Spanish reviewer-agent gate passes for all chapter pairs (T4.100)
- [ ] Cultural review of Carlos story complete (T4.101); "Ciudad de Fort Worth" enforced (T4.102)
- [ ] WCAG AAA contrast on all token pairs *and* per-state (hover/focus/active/disabled) (T4.40, T4.113)
- [ ] axe-core AAA sweep passes (T4.36 zero serious/critical violations)
- [ ] Forced-colors mode + prefers-contrast: more both verified (T4.114, T4.115)
- [ ] Color-blind safe palette + shape encoding (T4.116)
- [ ] Keyboard navigation full sweep clean + chapter shortcuts (1–0, j/k) + Cmd-K (T4.74, T4.118, T4.119)
- [ ] Screen reader pass logged + ARIA-live for cliff math + Carlos position + 3D text alt (T4.52, T4.53, T4.120, T4.121)
- [ ] Reduced-motion fallback verified at every animation site + screenshot fallbacks for camera flights, Carlos waypoints, paused 3D (T4.43–T4.47, T4.75, T4.110, T4.111, T4.112)
- [ ] **Lighthouse Performance ≥ 90 on simulated 4G (T4.66 — HARD GATE)**
- [ ] **Lighthouse per-chapter score within budget; trend chart published (T4.126, T4.127)**
- [ ] **Bundle analyzer report + image/font budgets enforced (T4.128, T4.130)**
- [ ] Code splitting per chapter verified; CLS per chapter < 0.05 (T4.131, T4.132)
- [ ] Mobile fallback graceful at 320px, 768px, 1024px *and* chapter-specific layouts (T4.50a–T4.53a, T4.122)
- [ ] Mobile swipe between chapters (opt-in) + save-data/battery hints respected (T4.123, T4.125)
- [ ] Branded 404 + 500 + empty + loading states in EN + ES (T4.106–T4.108, T4.26)
- [ ] Per-component error boundary in place (T4.109)
- [ ] Print stylesheet smoke green (T4.42)
- [ ] **12-layer compound integration test green (T4.133)**; LN×flashlight×audio compound green (T4.134)
- [ ] All 132 tasks marked done
- [ ] PR opened against `sprint/visual-rebirth` with W5 submission backlog already drafted

## KANSEI dispatch directive for W4

Identity: "Driver — accessibility + life-layers specialist". Emphasized DO NOTs:
- DO NOT skip prefers-reduced-motion in any animation task
- DO NOT skip forced-colors / prefers-contrast handling in any UI surface
- DO NOT translate Spanish via machine
- DO NOT skip cultural review of Carlos's narrative in ES (T4.101 is mandatory)
- DO NOT regress Lighthouse score; descope per ladder; per-chapter regressions > 5pts also block (T4.126)
- DO NOT exceed image / font budgets (T4.130 hard build-fail)
- DO NOT block keyboard users; chapter shortcuts (1–0, j/k) and Cmd-K must work without mouse
- DO NOT use placeholder Carlos data — real fixtures from `docs/demo-script.md`
- DO NOT use color alone to convey information (T4.116 color-blind shape encoding)
- DO NOT silently break /assess or /plan workflows (light-mode pages)
- DO NOT add Storybook in W4 (defer to post-hackathon)
- DO NOT regress test counts (1109 frontend tests must remain passing; new tasks add tests, never replace)
- DO NOT add backend dependencies beyond optional `/api/now` (T4.6 ADR governs)
- DO NOT use machine-translated Spanish OG images (T4.99 cultural framing required)

慣性の契約. 心を燃やせ. The Wall plays differently for every user. — GoWork team · April 2026.
