# components/wall — Wall UI components

> The Wall is the editorial home page: title sequence, brand mark, chapters, edge states, cursor effects, and chrome.

## Inventory

| Component | Purpose | Source task |
|-----------|---------|-------------|
| `BrandMark` | Inline G + cyan path mark with `interactive` + `loading` states | T1.34 + T1.107 |
| `TitleSequence` | 4-second page-load opening with audio handoff | T1.47 + T1.48 + T1.49 |
| `PathLineHeader` | Horizontal cyan path-line at the top of the page | T1.50 |
| `ChapterCounter` | Top-right "03/10" indicator for chapter progress | T1.52 |
| `MuteToggle` | aria-switch for ambient sound, persists `gowork.muted` | T1.53 |
| `LanguageToggle` | EN/ES toggle, dual-writes `gowork.locale` + legacy `montgowork-locale` | T1.54 |
| `SkipToContent` | First focusable element; jumps to `#main` | T1.63 |
| `AriaLiveRegion` + `AriaLiveProvider` | Screen-reader announcements | T1.64 |
| `CursorTrail` | 8px cyan dot with spring-lag follow | T1.60 |
| `CursorFlashlight` | 80px radial gradient cursor halo | T1.61 |
| `EmptyState`, `ErrorState`, `LoadingState` | Branded edge-state surfaces | T1.42 + T1.43 + T1.44 |
| `SectionErrorBoundary` | Class boundary with retry button | T1.115 |
| `CookieBanner` | Honest cookieless disclosure | T1.105 (Spotlight) |
| `PWAInstallPrompt` | Chromium beforeinstallprompt handler | T1.105 (Spotlight) |
| `dev/FpsOverlay` | Dev-only FPS readout (`?fps=1`) | T1.82 |

## Z-stack hierarchy

All overlay components reference tokens declared in `app/styles/tokens/layout.css`:

| Token | Value | Component |
|-------|-------|-----------|
| `--z-skip-link` | 100 | `SkipToContent` |
| `--z-modal` | 80 | `TitleSequence` |
| `--z-toast` | 70 | `dev/FpsOverlay` |
| `--z-header` | 50 | `Header` |
| `--z-banner` | 40 | `StallAlertBannerMount` |
| `--z-pwa-prompt` | 30 | `PWAInstallPrompt` |
| `--z-cookie` | 30 | `CookieBanner` |
| `--z-cursor-flashlight` | 5 | `CursorFlashlight` |

Never use a literal z-[NN] in a Wall component — always reach for `var(--z-*)`.

## Reduced-motion contract

All motion-driven components honor `prefers-reduced-motion`:
- `CursorTrail`: returns null
- `CursorFlashlight`: uniform-bright fallback (no localized gradient)
- `TitleSequence`: skips animation, fires onComplete next tick, no audio
- `PathLineHeader`: static instead of drawn
- `BrandMark`: static (no hover draw, no loading loop)

The token-level kill switch in `tokens/motion.css` collapses every animation/transition to 0.01ms when reduced-motion is active.

## Storage namespace

All localStorage / sessionStorage keys go through `lib/wall/storage.ts`:
- `STORAGE_KEYS.MUTED` (`gowork.muted`) — MuteToggle + sound
- `STORAGE_KEYS.LOCALE` (`gowork.locale`) + `STORAGE_KEYS.LOCALE_LEGACY` (`montgowork-locale`) — useLanguage
- `STORAGE_KEYS.RUM_SID` (`gowork.rum.sid`, sessionStorage) — analytics/session-id
- `STORAGE_KEYS.MAPBOX_TOKEN_VALIDATED` (`gowork.mapbox.validated`) — env validator cache

Never declare a raw string key in a component — always import STORAGE_KEYS.

## Adding a new Wall component

1. Source file under `components/wall/`
2. Companion test under `components/wall/__tests__/`
3. If interactive: respect `usePrefersReducedMotion` + `useCursorPosition` if cursor-driven
4. If overlay: reach for an existing `--z-*` token or propose a new one (then update `tokens/layout.css` + this README)
5. Run `bpsai-pair arch check frontend/src/components/wall/`
6. Run `npx vitest run src/components/wall/__tests__/`

## See also

- `lib/wall/README.md` — library + tokens + audio + types
- `app/styles/tokens/*.css` — design system partials
- `docs/sprints/w1-foundation-summary.md` — full W1 inventory
