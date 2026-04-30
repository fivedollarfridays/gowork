# Sprint W1 — Foundation Summary

> Authored: 2026-04-28  
> Branch: `sprint/w1-foundation`  
> Status: Ready for souji-sweep + merge to `sprint/visual-rebirth`

## Mission

W1 is the foundation that W2 (Mapbox + chapters 1–5), W3 (interactive chapters 6–10), W4 (life-layers + Spanish + perf + a11y), and W5 (submission) depend on. The sprint had to deliver:
- Brand: GoWork retired the legacy MontGoWork M-shape mark and shipped the new G + cyan path-line.
- Tokens: Color (OKLCH), Typography (fluid clamp + variable axes), Motion (springs + easings), Space, Layout, Forced-Colors, Animations, Z-Stack.
- Hooks: 14 utility hooks (time-of-day, cursor, scroll, language, performance, etc.).
- Audio: Lazy-Howler singleton with mute persistence.
- Cursor: Trail + flashlight overlays with reduced-motion fallbacks.
- Edge states: Branded 404, 500, empty, loading, error.
- Layout: Header, Footer, SkipToContent, AriaLiveRegion, MuteToggle, LanguageToggle, ChapterCounter, BrandMark, PathLineHeader, TitleSequence.
- A11y: Skip-to-content, ARIA-live, prefers-reduced-motion, prefers-contrast, forced-colors mode.
- PWA: manifest.json, install prompt, OG image, favicons, app icons.

## What shipped

### Driver A — Style + Tokens
- 6-partial token split: `colors.css`, `typography.css`, `motion.css`, `space.css`, `layout.css`, `forced-colors.css`
- TS-side `lib/wall/tokens.ts` — springs + easings + stagger + font axes
- Print stylesheet (`print.css`)
- `verify-contrast.mjs` — WCAG AAA gate
- SVGO config + `npm run svgo`

### Driver B — Hooks + Audio + Cursor
- 14 hooks: `useTimeOfDay`, `useCursorPosition`, `useLiveNow`, `useScrollProgress`, `useVariableFontWeight`, `useScrollVelocity`, `usePrefersReducedMotion`, `useIdleState`, `useViewTransitionsSupport`, `useLanguage`, `useBatteryAware`, `useDeviceCapability`, `usePerformanceBudget`, `useMemoryProfiler`
- `lib/wall/{env,sound,types,index,network}.ts`
- `lib/error-reporter.ts` (PII-scrubbed)
- `lib/analytics/session-id.ts` (SHA-256 RUM session id)
- Cursor system: `CursorTrail`, `CursorFlashlight`, `SectionErrorBoundary`
- 5 placeholder MP3s in `public/sounds/`

### Driver C — Brand + UI + Edge States + A11y
- New `icon.svg` (G + cyan path) + raster pipeline (`generate-brand-rasters.mjs`)
- `og-image.svg`, `manifest.json`
- Layout.tsx full rewrite with metadata, viewport, providers wiring
- Edge states: `EmptyState`, `ErrorState`, `LoadingState`, `not-found`, `error.tsx`
- `TitleSequence`, `PathLineHeader`, `Header` rewrite
- `ChapterCounter`, `MuteToggle`, `LanguageToggle`, `Footer` rewrite
- A11y scaffolding: `SkipToContent`, `AriaLiveRegion`
- `BrandMark` inline SVG component
- Accessibility page, `CookieBanner`, `PWAInstallPrompt`
- 21 EN+ES translation keys + `chapter-divider.svg`

### Driver D — Maximization (this pass)
- **Wave 1 carry-overs:** TitleSequence × audio (T1.48), brand-mark hover path-draw (T1.107), `/dev/tokens` gallery (T1.76), legacy-brand audit (T1.77), Web Vitals reporter (T1.79), FpsOverlay (T1.82)
- **Wave 2 cross-driver:** STORAGE_KEYS namespace (fixed silent mute bug), Z-stack token system, MuteToggle ↔ sound integration, Spanish translation review checklist
- **Wave 3 editorial:** `editorial-dropcap` + `editorial-pullquote` + `editorial-link` gradient underline + branded `::selection`
- **Wave 4 architectural:** BrandMark loading + interactive props, layout-composition integration test, brand-loading cinematic compose test
- **Wave 5 tooling:** brand-integrity sweep + token-usage audit + `npm run audit:brand` + `npm run audit:tokens`
- **Wave 7 Spotlight (6 inventions):** `lib/wall/storage.ts`, `lib/wall/log.ts`, `lib/wall/featureDetect.ts`, `lib/wall/brandAssets.ts`, `lib/wall/cinematic.ts`, `lib/wall/landmarks.ts`

## Test coverage

- **Pre-W1 baseline:** 1290 tests (288 frontend + 1002 backend)
- **W1 merged (A+B+C):** 1634 tests (frontend)
- **W1 closed (Driver D):** 1772 tests (frontend, target +50, delivered +138)
- **Coverage gate:** All new modules at >95% statement coverage; no production code shipped without paired tests.

## Architecture compliance

- `bpsai-pair arch check` clean across `frontend/src/lib/wall/`, `frontend/src/hooks/`, `frontend/src/components/wall/`, `frontend/src/app/dev/`, `frontend/src/lib/analytics/`
- Largest source file: `lib/wall/sound.ts` (207 lines, well under 400 limit)
- Largest function: `useEffect` body in `useScrollProgress` (29 lines, well under 50 limit)
- All token partials under 200 lines

## Key files

| Path | Purpose |
|------|---------|
| `frontend/src/app/styles/tokens/*.css` | 7-partial design system |
| `frontend/src/lib/wall/index.ts` | Public API barrel |
| `frontend/src/lib/wall/storage.ts` | Canonical localStorage namespace |
| `frontend/src/components/wall/` | All Wall UI components |
| `frontend/src/hooks/` | 14 utility hooks |
| `frontend/src/app/dev/tokens/page.tsx` | Token gallery (dev-only) |
| `frontend/scripts/audit-*.mjs` | Brand + token audit gates |

## Honest uncertainty (carried forward to W2)

- **C4** Battery API drops in Firefox; iOS Safari never supported. `useBatteryAware` returns null gracefully but consumers must check.
- **C4** `performance.memory` is Chrome-only; `usePerformanceBudget` reports 0 heap on Safari/Firefox.
- **C4** `useViewTransitionsSupport` reads `document.startViewTransition` once on mount — accurate today but the API surface has been moving.
- **C5** Vitest 4 default `pool: 'forks'` ran out of memory during W1 with framer-motion mock returning fresh objects on every render — fixed by hoisting the mock to a stable singleton.
- **C3** Howler iOS audio-context-resume is genuinely flaky on real devices; the `unlock()` API surface is correct but real hardware testing is W2 work.
- **C3** Mapbox style URL not yet pinned (W2 task).

## What's next (W2 readiness)

- Souji-sweep on `sprint/w1-foundation`
- Merge to `sprint/visual-rebirth`
- Engage `sprint/w2-mapbox-chapters`

## Final closure entry (state.md)

```
## 2026-04-28 — W1 Foundation closed via Driver D maximization. Tests: 1772/1772. Next: souji-sweep + merge.
```
