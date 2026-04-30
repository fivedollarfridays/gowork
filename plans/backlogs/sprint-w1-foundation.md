# Sprint W1 — Foundation + Brand + Edge States

**Plan type:** feature
**Sprint:** W1
**Branch:** `sprint/visual-rebirth`
**Companion docs:** `docs/visual-rebirth-plan.md`, `docs/visual-rebirth-briefs.md` (Sprint W1 section)

## Goal

Build the design system, motion system, brand identity, hooks, and edge states that the 10-chapter Mapbox Wall (W2–W4) depends on. This sprint produces ZERO "page" output — it produces the TOOLING. Without coherent foundations, every later sprint paints over inconsistent work and every judge sees the seams.

**Mission anchor:** GoWork is barrier-removal infrastructure for any American city. We're shipping for HackFW 2026 (deadline May 2, 2:00 PM CDT). The home page must signal "real infrastructure, not hackathon prototype." Every task in W1 is a vote for that signal.

## Delivery Summary

| Metric | Value |
|---|---|
| Total tasks | 123 |
| P0 / P1 / P2 | 65 / 44 / 14 |
| Total Cx | 1010 |
| Wave count | 6 (new Wave 6 = system audits + Spotlight enrichment polish) |
| Critical path | Infra install → CSS arch split → tokens (color/type/motion) → hooks/brand/edges/header parallel → wiring/types/tests → telemetry/SEO/PWA/security/a11y-beyond-AAA/editorial-polish/perf/data-verify/dev-tooling/print-extras |
| Spotlight inventions | 5 (original) + 12 (enrichment pass) = 17 total |
| Architecture compliance | every code task includes `bpsai-pair arch check passes` AC |
| TDD compliance | every code task lists failing-test-first AC |
| Engage dry-run | passes (123 tasks parsed) |
| Enrichment pass | T1.78–T1.132 — analytics, SEO/Schema.org, PWA/SW, CSP, a11y beyond AAA, editorial polish (drop caps, pull quotes, chapter dividers as ART), font subsetting, real-data verification, brand sound logo, reading-speed adapter, dev FPS overlay, Web Vitals reporter, error reporter scaffold |

## Priority Order (top 25, abbreviated)

1. T1.1 — Install mapbox-gl + react-map-gl (P0, Cx 5)
2. T1.7 — Split globals.css into token partials (P0, Cx 14) — UNBLOCKS ALL TOKEN TASKS
3. T1.8 — Wire @import statements in globals.css (P0, Cx 4)
4. T1.9 — Tailwind + token regression smoke test (P0, Cx 6)
5. T1.2 — Install @react-three/fiber + drei + three (P0, Cx 5)
6. T1.3 — Install satori + @vercel/og (P0, Cx 4)
7. T1.4 — Install howler + howler types (P0, Cx 4)
8. T1.6 — Mapbox token boot validator (P1, Cx 6)
9. T1.10 — OKLCH base palette tokens (P0, Cx 10)
10. T1.11 — Accent + status tokens (P0, Cx 8)
11. T1.12 — Temperature multiplier scoped variable (P0, Cx 6)
12. T1.13 — WCAG AAA contrast script + token snapshot lock (P0, Cx 14)
13. T1.15 — Inter Variable + optical-size + fallback (P0, Cx 12)
14. T1.16 — Fluid type scale tokens (P0, Cx 8)
15. T1.17 — Tabular nums utility class (P0, Cx 4)
16. T1.19 — Spring preset tokens (P0, Cx 8)
17. T1.20 — Easing + duration tokens (P0, Cx 6)
18. T1.21 — Stagger timing tokens (P0, Cx 6)
19. T1.22 — prefers-reduced-motion CSS variable disable (P0, Cx 8)
20. T1.24 — useTimeOfDay hook (P0, Cx 14)
21. T1.25 — useCursorPosition hook (P0, Cx 12)
22. T1.26 — useLiveNow hook (P0, Cx 14)
23. T1.27 — useScrollProgress hook (P0, Cx 14)
24. T1.34 — New `icon.svg` (G + cyan path-line) (P0, Cx 12)
25. T1.38 — layout.tsx metadata refresh (P0, Cx 8)

(Remaining 44 tasks ordered by dependency depth in the file body.)

## File Collision Matrix

Critical: multiple parallel-wave tasks must NOT race on the same file. Resolutions noted.

| File | Tasks touching | Resolution |
|---|---|---|
| `frontend/src/app/globals.css` | T1.7 (split), T1.8 (imports) | Serialize: T1.7 splits FIRST (Wave 1); all token tasks write to `tokens/*.css` partials, never globals.css directly. Only T1.8 modifies globals.css after split. |
| `frontend/src/app/styles/tokens/colors.css` | T1.7 (move), T1.10 (base), T1.11 (accents), T1.12 (temperature) | T1.7 creates file with existing content; T1.10/T1.11/T1.12 append serially via `Depends on:`. |
| `frontend/src/app/styles/tokens/typography.css` | T1.7 (create), T1.15 (font vars), T1.16 (type scale), T1.17 (tabular nums) | T1.7 creates empty file; T1.15/T1.16/T1.17 append serially. |
| `frontend/src/app/styles/tokens/motion.css` | T1.7 (create), T1.19 (springs), T1.20 (easing), T1.21 (stagger), T1.22 (reduced-motion), T1.23 (idle) | T1.7 creates empty file; T1.19→T1.23 chain serially via `Depends on:`. |
| `frontend/src/app/styles/tokens/layout.css` | T1.7 (move), T1.65 (focus rings + selection) | T1.7 creates with existing content; T1.65 appends. |
| `frontend/src/lib/wall/tokens.ts` | T1.19 (spring), T1.20 (easing), T1.21 (stagger), T1.16 (type-scale TS) | T1.19 creates the file; others append serially. |
| `frontend/package.json` | T1.1 (mapbox), T1.2 (r3f), T1.3 (satori), T1.4 (howler), T1.5 (svgo) | Sequential: each install task adds its dep + commits package-lock; chained by `Depends on: T1.{prev}`. |
| `frontend/src/app/layout.tsx` | T1.38 (single rewrite — metadata + font axis + skip-link mount) | One rewrite task. T1.15/T1.34/T1.36/T1.37/T1.63 land sub-components/assets first; T1.38 wires them. |
| `frontend/public/manifest.json` | T1.37 | Single task. |
| `frontend/public/icon.svg` | T1.34 (replace legacy M-shape) | Single task; T1.77 audits afterward. |
| `frontend/public/og-image.svg` | T1.36 | Single task. |
| `frontend/src/components/layout/Header.tsx` | T1.51 (single rewrite — imports brand + counter + mute + lang + GitHub + path-line) | T1.34/T1.50/T1.52/T1.53/T1.54 build sub-components; T1.51 imports them. No collision — Header.tsx edited once. |
| `frontend/src/components/layout/Footer.tsx` | T1.55 | Single rewrite. |
| `frontend/src/lib/wall/index.ts` | T1.68 | Single creator task. |
| `frontend/src/hooks/index.ts` | T1.68 (creates barrel for hooks too) | Same task. |
| `frontend/src/lib/translations/en.json` + `es.json` | T1.40 (404), T1.41 (500), T1.42 (empty), T1.43 (loading), T1.44 (error), T1.48 (title seq), T1.51 (header strings), T1.53 (mute strings), T1.54 (lang toggle), T1.55 (footer strings), T1.63 (skip-to-content) | Each task writes its own namespaced keyspace (`edge.404.*`, `wall.titleSequence.*`, `header.*`, `footer.*`, `a11y.*`); merge-friendly when tasks land in any order. |
| `.paircoder/context/state.md` | T1.77 (legacy retirement note) | Single task; appended subsection only. |

## Out of scope for W1

- Mapbox map rendering, custom Mapbox style URL configuration (W2)
- Any chapter component, scroll engine, camera choreography (W2)
- Carlos avatar, 3D barrier graph, view transitions (W3)
- Live Now widget UI on the map (W4 — only the hook is W1)
- Spanish editorial copy population for chapters (W4 — only edge-state + toggle keys in W1)
- Lighthouse measurement, perf gate (W4)
- README / press kit / video / Devpost (W5)
- Backend changes (none in W1)

## Permanent constraints (every code task enforces)

1. 95% test coverage on new code (vitest)
2. TDD only — failing test FIRST, then implementation
3. Files <400 lines, functions <50 lines, max 15 functions/file, max 20 imports
4. Full wiring — nothing orphaned
5. ZERO LLM calls in The Wall render path
6. `bpsai-pair arch check` passes
7. Reviewer agent reviews all code-producing tasks
8. prefers-reduced-motion respected at every animation site
9. WCAG AAA contrast verified on every text-on-background pair
10. Multi-city architecture intact (Montgomery still works via state="AL")
11. Brand strings: GoWork everywhere; no MontGoWork leakage
12. Backend untouched
13. Slogan locked: "What's standing between you and a job?" / "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan." / "Workforce infrastructure for any American city."

---

## Phase 1: Infra & Tooling

### T1.1 — Install mapbox-gl + react-map-gl | Cx: 5 | P0

**Description:**
Add `mapbox-gl@^3.x` and `react-map-gl@^7.x` to `frontend/package.json` dependencies with pinned versions. Document the `NEXT_PUBLIC_MAPBOX_TOKEN` environment variable in `frontend/.env.local.example` with a comment explaining the Mapbox account requirement. No code consumes this yet — this is W2's foundation. Existing build must remain green.

**AC:**
- [ ] `mapbox-gl` and `react-map-gl` appear in `frontend/package.json` `dependencies` with pinned major.minor (e.g., `^3.6.0`, `^7.1.0`)
- [ ] `frontend/package-lock.json` regenerated; `npm install` runs clean (zero peer-dep conflicts reported)
- [ ] `frontend/.env.local.example` contains `NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...` placeholder with comment line referencing `mapbox.com` account requirement
- [ ] `cd frontend && npm run build` exits 0 (no new errors, no new warnings beyond baseline)
- [ ] `npm audit --production` reports no new HIGH or CRITICAL vulnerabilities introduced
- [ ] `bpsai-pair arch check frontend/package.json` passes (file is JSON; manifest sanity)
- [ ] Reviewer agent approves

**Depends on:** none

---

### T1.2 — Install @react-three/fiber + @react-three/drei + three | Cx: 5 | P0

**Description:**
Add `@react-three/fiber@^8.x`, `@react-three/drei@^9.x`, and `three@^0.160.x` to dependencies for the W3 Chapter 8 3D barrier constellation. Pin versions; verify peer compat with React 18. Add `@types/three` to devDependencies.

**AC:**
- [ ] Three dependencies pinned in `frontend/package.json` dependencies; `@types/three` in devDependencies
- [ ] `npm install` resolves without `--legacy-peer-deps` flag (or document if needed)
- [ ] Bundle delta inspected: `npm run analyze` shows three.js NOT in main chunk (must lazy-load only when imported by W3 components)
- [ ] `npm run build` exits 0
- [ ] `bpsai-pair arch check frontend/package.json` passes
- [ ] Reviewer agent approves

**Depends on:** T1.1

---

### T1.3 — Install satori + @vercel/og | Cx: 4 | P0

**Description:**
Add `satori@^0.10.x` and `@vercel/og@^0.6.x` for W4's per-chapter dynamic OG image generation via Next.js Route Handlers. No endpoint yet; this is install-only.

**AC:**
- [ ] `satori` and `@vercel/og` pinned in `frontend/package.json` dependencies
- [ ] `npm install` clean
- [ ] `npm run build` exits 0; build logs show no Edge runtime warnings
- [ ] Bundle analysis confirms satori NOT in main chunk
- [ ] `bpsai-pair arch check frontend/package.json` passes
- [ ] Reviewer agent approves

**Depends on:** T1.2

---

### T1.4 — Install howler + audio types | Cx: 4 | P0

**Description:**
Add `howler@^2.2.x` and `@types/howler` for the W1 audio system scaffold (Howler.js singleton). Verify lazy-load compatibility (we want it tree-shaken when sound is muted).

**AC:**
- [ ] `howler` pinned in `frontend/package.json` dependencies; `@types/howler` in devDependencies
- [ ] `npm install` clean
- [ ] `npm run build` exits 0
- [ ] Howler not in main chunk (verified via bundle-analyze)
- [ ] `bpsai-pair arch check frontend/package.json` passes
- [ ] Reviewer agent approves

**Depends on:** T1.3

---

### T1.5 — SVGO config + npm script for asset pipeline | Cx: 4 | P1

**Description:**
Add `svgo` to devDependencies. Create `frontend/svgo.config.mjs` with conservative settings (preserve viewBox, preserve aria-label/title, no auto-removal of named colors used by tokens). Add `frontend/package.json` script `"svgo": "svgo -f public -r --config svgo.config.mjs"` that the brand-mark task (T1.30) and OG-base task (T1.31) will run after creating SVGs.

**AC:**
- [ ] `svgo` in devDependencies pinned
- [ ] `frontend/svgo.config.mjs` exists with `removeViewBox: false`, `removeTitle: false`, `removeDesc: false`, `cleanupIds: false` plugins disabled (justified inline)
- [ ] `npm run svgo` exits 0 against existing `frontend/public/og-image.svg` and `frontend/public/icon.svg` (idempotent run)
- [ ] No SVG file's `aria-label` or `<title>` is stripped by the run
- [ ] `bpsai-pair arch check frontend/svgo.config.mjs` passes
- [ ] Reviewer agent approves

**Depends on:** T1.4

---

### T1.6 — Mapbox token boot validator (frontend) | Cx: 6 | P1

**Description:**
W2 will fail loudly if `NEXT_PUBLIC_MAPBOX_TOKEN` is unset in production. Add `frontend/src/lib/wall/env.ts` with `validateMapboxToken()`: reads `process.env.NEXT_PUBLIC_MAPBOX_TOKEN`, returns `{ ok: boolean, reason?: string }`. Used by W2's `WallContainer` static-fallback decision. Vitest unit test in `frontend/src/lib/wall/__tests__/env.test.ts` covers: token absent → ok false; token starts with `pk.` → ok true; token starts with anything else → ok false. This is the entry point that creates `frontend/src/lib/wall/` directory.

**AC:**
- [ ] `frontend/src/lib/wall/` directory exists (creates the wall lib namespace)
- [ ] `frontend/src/lib/wall/env.ts` exports `validateMapboxToken(): { ok: boolean; reason?: string }`
- [ ] Failing vitest test written FIRST (asserts `ok: false` when env unset) — confirmed red before implementation
- [ ] All three test cases pass after implementation
- [ ] `bpsai-pair arch check frontend/src/lib/wall/env.ts` passes (<400 lines, <50 line fn, <15 fns, <20 imports)
- [ ] Function uses no `window` access (SSR-safe)
- [ ] Reviewer agent approves

**Depends on:** T1.1

---

## Phase 2: CSS Architecture Prerequisite

### T1.7 — Split globals.css into token partials | Cx: 14 | P0

**Description:**
`frontend/src/app/globals.css` is currently 87 lines. The brief estimated 195 — this is good news (more headroom). However, adding OKLCH palette + accent shades + status tokens + temperature multiplier + type scale + 3 spring presets + easing + stagger + reduced-motion overrides + idle animation will easily push it past 400 with token expansion in W4. **Pre-emptively split** into one entry file + 5 partials BEFORE any token addition. Create directory `frontend/src/app/styles/tokens/` with empty (or stub-comment-only) files: `colors.css`, `typography.css`, `motion.css`, `space.css`, `layout.css`. Move existing `:root` HSL block into `colors.css` (preserved exactly — Phase 3 will REPLACE not extend). Move existing `.dark` override block into `colors.css`. Move existing `@layer utilities { .text-balance }` into `layout.css`. Move existing `@layer base { * { @apply border-border... } }` block into `layout.css`. globals.css becomes a thin shell of @tailwind directives + @import statements (handled by T1.8).

**AC:**
- [ ] Failing test written FIRST: `frontend/src/__tests__/globals-tokens.test.ts` asserts each partial file exists and exports nothing (CSS files just need to exist + be readable) — fails because directory doesn't exist yet
- [ ] `frontend/src/app/styles/tokens/colors.css` contains the full pre-existing `:root { --background... }` block AND `.dark { ... }` block, byte-for-byte preserved
- [ ] `frontend/src/app/styles/tokens/typography.css` exists (empty + comment header `/* W1 typography tokens — populated by T1.15-T1.17 */`)
- [ ] `frontend/src/app/styles/tokens/motion.css` exists (empty + comment header for T1.19-T1.23)
- [ ] `frontend/src/app/styles/tokens/space.css` exists (empty + comment header — populated post-W1)
- [ ] `frontend/src/app/styles/tokens/layout.css` contains the existing `@layer utilities { .text-balance }` block AND the `@layer base { * { @apply border-border... } html, body { overscroll-behavior: none; } body { @apply bg-background text-foreground; } }` block byte-for-byte
- [ ] `globals.css` line count drops to ≤30 (just `@tailwind` directives + `@import` placeholders ready for T1.8)
- [ ] `wc -l` on every new partial reports <50 lines (room to grow)
- [ ] `bpsai-pair arch check frontend/src/app/styles/tokens/` passes (no file >400)
- [ ] Reviewer agent approves

**Depends on:** none

---

### T1.8 — Wire @import statements in globals.css | Cx: 4 | P0

**Description:**
Update `frontend/src/app/globals.css` to `@import './styles/tokens/colors.css'; @import './styles/tokens/typography.css'; @import './styles/tokens/motion.css'; @import './styles/tokens/space.css'; @import './styles/tokens/layout.css';` after the `@tailwind` directives. Order matters: tokens load before utilities. Verify Next.js + PostCSS picks up imports (Next 15 uses Lightning CSS by default — confirm @import ordering).

**AC:**
- [ ] `globals.css` has 5 `@import` statements in correct order (colors, typography, motion, space, layout) AFTER `@tailwind utilities`
- [ ] `npm run build` exits 0; CSS bundle still includes all original rules (verified via grep on `.next/static/css/*.css` for `--background` and `.text-balance`)
- [ ] No PostCSS warnings about misordered @imports
- [ ] Visual smoke test (manual or via Playwright snapshot in T1.9): existing pages render identical pre/post split
- [ ] `bpsai-pair arch check frontend/src/app/globals.css` passes
- [ ] Reviewer agent approves

**Depends on:** T1.7

---

### T1.9 — Tailwind + token regression smoke test | Cx: 6 | P0

**Description:**
After CSS split, prove zero regressions. Create `frontend/src/__tests__/css-architecture.test.ts` that:
(a) reads `globals.css` and asserts it contains 5 `@import './styles/tokens/...'` lines;
(b) reads each partial and asserts non-empty;
(c) builds the project (or invokes a CSS bundling fixture) and asserts the output CSS contains `--background:`, `--primary:`, `.text-balance`, and `bg-background`. If CSS-output-bundling assertion is too heavy for unit test, document a Playwright-level visual snapshot in `frontend/tests/e2e/visual/post-css-split.spec.ts` instead.

**AC:**
- [ ] Failing tests written FIRST — fail because either partials missing OR globals.css imports missing
- [ ] All test assertions pass after T1.7 + T1.8 land
- [ ] No visual regression on `/`, `/daily`, `/jobs`, `/appointments` (snapshot or manual)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.8

---

## Phase 3: Design Tokens — Color (OKLCH)

### T1.10 — OKLCH base palette tokens | Cx: 10 | P0

**Description:**
Add OKLCH base canvas tokens to `frontend/src/app/styles/tokens/colors.css` at `:root` AFTER the existing HSL block (preserve existing tokens for backward compat — they back the current shadcn UI). New tokens (LOCKED from `docs/visual-rebirth-plan.md` "Design system → Color"):
```
--bg-base: #0A0E1A;       /* paper-dark navy, base canvas */
--bg-surface: #0F1729;    /* raised surface */
--bg-elevated: #1A2338;   /* cards on surface */
--bg-glass: rgba(255,255,255,0.04);  /* used with backdrop-blur(12px) */
--fg-primary: #F5F3EE;    /* warm paper white — NOT pure white */
--fg-secondary: #94A3B8;
--fg-muted: #64748B;
```
Use `@supports (color: oklch(50% 0 0))` block to provide P3-capable OKLCH equivalents for browsers that support it; hex fallbacks are the defaults. Document each token with an inline comment matching the plan file.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/__tests__/tokens-color-base.test.ts` reads `colors.css` and asserts each of the 7 token names appears
- [ ] All 7 tokens defined in `colors.css` with hex values byte-matching the plan file
- [ ] `@supports (color: oklch(...))` block adds OKLCH equivalents for all 7 tokens (compute via OKLCH conversion or use plan's stated OKLCH values if any provided in design refs)
- [ ] Inline comments match plan-file token-row description (e.g., `--bg-base: #0A0E1A; /* paper-dark navy, base canvas */`)
- [ ] `colors.css` line count <100 (room for accents in T1.11)
- [ ] `bpsai-pair arch check frontend/src/app/styles/tokens/colors.css` passes
- [ ] WCAG AAA contrast: --fg-primary on --bg-base ratio >=7:1 (verified manually OR delegated to T1.13 script)
- [ ] Reviewer agent approves

**Depends on:** T1.7, T1.8

---

### T1.11 — Accent + status tokens with color-mix() shades | Cx: 8 | P0

**Description:**
Add accent and status tokens to `colors.css`:
```
--accent-cyan: #22D3EE;     /* electric — the path / intelligence */
--accent-amber: #F59E0B;    /* warm gold — Carlos / hope / progress */
--accent-rose:  #FB7185;    /* cliff / barrier severity (Ch 5/6 only) */
--status-positive: #34D399;
--status-warning:  #FBBF24;
--status-negative: #FB7185;
--accent-current: var(--accent-cyan);  /* live-shifting current accent (chapter overrides) */
```
Add CSS `color-mix()` derived shade variants for each accent: `--accent-cyan-100` through `--accent-cyan-900` using `color-mix(in oklch, var(--accent-cyan), var(--bg-base) X%)` — at minimum 5 shades per accent (100, 300, 500=base, 700, 900). Provide hex fallbacks in `@supports not (color: oklch(50% 0 0))` block.

**AC:**
- [ ] Failing test written FIRST: asserts each accent token name AND at least 5 shade variants per accent (cyan, amber, rose) appear in `colors.css`
- [ ] All 7 base accent/status tokens + `--accent-current` defined
- [ ] At least 15 `color-mix()` shade variants defined (5 per accent)
- [ ] Hex fallbacks present in `@supports not` block for browsers without color-mix support
- [ ] WCAG AAA verified for: --accent-cyan on --bg-base, --accent-amber on --bg-base, --status-positive on --bg-base
- [ ] `colors.css` <200 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10

---

### T1.12 — `--temperature-multiplier` scoped variable | Cx: 6 | P0

**Description:**
Add `--temperature-multiplier: 1.0;` to `:root` in `colors.css` (it lives with color tokens because it modulates accent color shifts — same family). This variable is overridable per-chapter via inline style or scoped class. W3 Chapter 6 (cliff calc) sets it to 1.5 when wage-slider enters cliff zone, shifting --accent-current from cyan toward rose. Document the contract: `1.0 = neutral`, `>1.0 = warmer/redder shift`, `<1.0 = cooler/bluer shift`. Add CSS `--accent-current: color-mix(in oklch, var(--accent-cyan), var(--accent-rose) calc((var(--temperature-multiplier) - 1) * 100%))` so accent-current responds automatically.

**AC:**
- [ ] Failing test written FIRST: asserts `--temperature-multiplier` and `--accent-current` exist in `colors.css`
- [ ] `--temperature-multiplier: 1.0` set at `:root`
- [ ] `--accent-current` formula uses `color-mix()` with `--temperature-multiplier`
- [ ] Inline JSDoc-style CSS comment documents the contract (1.0 neutral, >1 rose shift, <1 cyan shift)
- [ ] Visual sanity test (vitest+jsdom or Playwright): set inline `style="--temperature-multiplier: 1.5"` on a div, assert computed `--accent-current` differs from default
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.11

---

### T1.13 — WCAG AAA contrast script + token snapshot lock | Cx: 14 | P0

**Description:**
Create `frontend/scripts/verify-contrast.mjs` (Node ESM script) that:
(a) parses `frontend/src/app/styles/tokens/colors.css` extracting all hex tokens;
(b) computes relative luminance + contrast ratio for every text-on-bg pair (--fg-primary/--fg-secondary/--fg-muted vs --bg-base/--bg-surface/--bg-elevated; --accent-* vs --bg-base);
(c) reports PASS (>=7:1 for AAA normal text, >=4.5:1 for AAA large text >=24px) or FAIL with the actual ratio;
(d) exits 1 on any FAIL. Add npm script `"contrast": "node ./scripts/verify-contrast.mjs"`. ALSO add `frontend/src/__tests__/tokens-color-snapshot.test.ts` using vitest `toMatchInlineSnapshot()` to lock the exhaustive token list — any future PR removing/renaming a token fails the test. Snapshot covers: 7 base + 7 accent/status + --accent-current + --temperature-multiplier + 15+ shade variants.

**AC:**
- [ ] Failing test written FIRST: contrast-script test fixture with bad contrast → exit 1; snapshot test → fails first run (no snapshot yet)
- [ ] Both tests pass after implementation
- [ ] Script extracts at least 10 token pairs from colors.css
- [ ] Script reports actual ratios (e.g., `--fg-primary on --bg-base: 16.4:1 PASS`)
- [ ] Script exits 0 against current tokens (palette IS AAA — verified)
- [ ] `npm run contrast` works from `frontend/` directory
- [ ] Snapshot test locks 30+ token names; deliberately adding stub token causes test failure (verified, then reverted)
- [ ] Script <200 lines, <50 line fns, <15 fns
- [ ] `bpsai-pair arch check frontend/scripts/verify-contrast.mjs` passes
- [ ] Reviewer agent approves

**Depends on:** T1.12

---

## Phase 4: Design Tokens — Typography

### T1.15 — Inter Variable + optical-size axis + metric-tuned fallback | Cx: 12 | P0

**Description:**
Currently `frontend/src/app/layout.tsx` uses `Inter` from `next/font/google` (static). Replace with Inter Variable using full axis support: weight 100..900 + optical-size axis (`opsz`). Use `next/font/google` with the variable subset (`{ subsets: ['latin'], variable: '--font-inter', weight: 'variable', axes: ['opsz'], adjustFontFallback: true }`). Verify the variable font is loaded with `font-variation-settings: "wght" <weight>, "opsz" <size>` accessible to W4's `useVariableFontWeight` hook. Add `frontend/src/app/styles/tokens/typography.css` rules: `:root { --font-inter-var: var(--font-inter); --font-inter-stack: var(--font-inter-var), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }`. The `adjustFontFallback: true` ensures CLS budget <0.1 via metric-tuned fallback during font swap. **Spotlight/Honesty:** if `next/font` does NOT yet support `axes: ['opsz']` in stable Next 15, fallback path is to switch to `@fontsource-variable/inter` (devDep add) and self-host — document the pivot in PR.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/app/__tests__/font-variable.test.tsx` mounts layout and asserts `<body>` has `--font-inter` CSS variable, `<style>` declares `font-variation-settings` with both `wght` and `opsz`, and `--font-inter-stack` includes 4+ fallback families
- [ ] `layout.tsx` Inter font configured with `axes: ['opsz']`, weight `'variable'`, `adjustFontFallback: true`
- [ ] `typography.css` defines `--font-inter-var` and `--font-inter-stack`
- [ ] `npm run build` exits 0; build reports do not show legacy static-weight Inter requests
- [ ] Network panel manual check: only ONE Inter font file requested (not 9 weight files)
- [ ] Lighthouse CLS budget <0.1 on `/` route preserved from baseline (manual measurement, not CI gate)
- [ ] If `axes: ['opsz']` causes build failure: pivot to `@fontsource-variable/inter` documented in PR with reason
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.7, T1.8

---

### T1.16 — Fluid type scale tokens | Cx: 8 | P0

**Description:**
Add fluid type-scale tokens to `typography.css` using `clamp()`:
```
--type-display: clamp(3rem, 2rem + 5vw, 6.5rem);     /* hero text-7xl-equivalent */
--type-h1:      clamp(2rem, 1.4rem + 3vw, 4rem);
--type-h2:      clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem);
--type-h3:      clamp(1.25rem, 1rem + 1vw, 1.75rem);
--type-body:    clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
--type-small:   clamp(0.875rem, 0.85rem + 0.25vw, 1rem);
--type-tight-tracking: -0.04em;
--type-body-tracking: -0.01em;
--type-leading-loose: 1.7;
```

**AC:**
- [ ] Failing test written FIRST: asserts each --type-* token exists in `typography.css`
- [ ] All 9 tokens defined with `clamp()` formulas matching plan-file specs
- [ ] `--type-display` resolves to 6.5rem at 1920px viewport (manual computed-style check OR vitest+jsdom assertion)
- [ ] At 320px viewport, `--type-display` resolves >=3rem (no overflow)
- [ ] Token names exported via TS constant in `frontend/src/lib/wall/tokens.ts` (T1.19 owns the file; this task appends or coordinates)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.15

---

### T1.17 — Tabular nums + monospace utility | Cx: 4 | P0

**Description:**
Add `.tabular-nums` and `.font-mono-data` Tailwind utility-layer classes in `typography.css`:
```
@layer utilities {
  .tabular-nums { font-feature-settings: "tnum" 1; font-variant-numeric: tabular-nums; }
  .font-mono-data { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-weight: 500; }
}
```
Both consumed by W3 Chapter 6 stat displays + Live Now widget timestamps (W4).

**AC:**
- [ ] Failing test written FIRST: asserts `.tabular-nums` and `.font-mono-data` selectors compile in built CSS
- [ ] Both utilities defined under `@layer utilities` (not base)
- [ ] Vitest + jsdom snapshot of computed `font-feature-settings` on element with `.tabular-nums` class shows `"tnum" 1`
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.16

---

## Phase 5: Design Tokens — Motion

### T1.19 — Spring preset tokens (TS export) | Cx: 8 | P0

**Description:**
Create `frontend/src/lib/wall/tokens.ts` with framer-motion spring presets matching plan file:
```ts
export const SPRING_SOFT    = { stiffness: 100, damping: 20 } as const;
export const SPRING_SNAPPY  = { stiffness: 200, damping: 25 } as const;
export const SPRING_ELASTIC = { stiffness: 300, damping: 18 } as const;
```
Also add CSS variables in `motion.css` for non-framer use:
```
--spring-soft-stiff: 100; --spring-soft-damp: 20;
... etc.
```
File is sprint-shared; subsequent tasks (T1.20–T1.23, T1.41) append. Owner of file is THIS task.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/lib/wall/__tests__/tokens.test.ts` imports SPRING_SOFT/SNAPPY/ELASTIC and asserts each has `stiffness` and `damping` numeric props
- [ ] `frontend/src/lib/wall/tokens.ts` exists, exports the 3 spring constants `as const`
- [ ] `motion.css` has 6 CSS vars for the same values (consumable from CSS animations if needed)
- [ ] Constants are deeply readonly (TypeScript `as const`)
- [ ] `bpsai-pair arch check frontend/src/lib/wall/tokens.ts` passes
- [ ] Reviewer agent approves

**Depends on:** T1.7, T1.8

---

### T1.20 — Easing + duration tokens | Cx: 6 | P0

**Description:**
Append to `tokens.ts`:
```ts
export const EASE_LINEAR_SIG = [0.32, 0.72, 0, 1] as const;  // Linear's signature
export const EASE_OUT = [0.16, 1, 0.3, 1] as const;
export const DURATION_BASELINE_MS = 280;
```
And to `motion.css`:
```
--ease-linear-sig: cubic-bezier(0.32, 0.72, 0, 1);
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--duration-baseline: 280ms;
```

**AC:**
- [ ] Failing test written FIRST: asserts EASE_LINEAR_SIG is a 4-tuple of numbers; DURATION_BASELINE_MS === 280
- [ ] TS constants exported as `as const`
- [ ] CSS vars defined in `motion.css`
- [ ] Vitest test that imports EASE_LINEAR_SIG and passes it to a framer-motion `transition.ease` prop renders without runtime error (smoke)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.19

---

### T1.21 — Stagger timing tokens | Cx: 6 | P0

**Description:**
Append to `tokens.ts`:
```ts
export const STAGGER_CHILD_OFFSET_S = 0.05;
export const STAGGER_INITIAL_DEFAULT = { opacity: 0, y: 20 } as const;
export const STAGGER_ANIMATE_DEFAULT = { opacity: 1, y: 0 } as const;
```
And to `motion.css`:
```
--stagger-child-offset: 0.05s;
--stagger-default-y: 20px;
```
This standardizes the framer-motion StaggerContainer pattern already used in `motion.tsx`. Update `frontend/src/lib/motion.tsx` (existing 174-line file) to import these constants instead of hardcoded literals — DO NOT grow the file; replace existing literals only.

**AC:**
- [ ] Failing test written FIRST: asserts STAGGER_CHILD_OFFSET_S === 0.05 and that motion.tsx imports the constant
- [ ] Constants exported from `tokens.ts`
- [ ] `motion.tsx` (existing) imports STAGGER_CHILD_OFFSET_S, STAGGER_INITIAL_DEFAULT, STAGGER_ANIMATE_DEFAULT and replaces existing hardcoded equivalents
- [ ] `motion.tsx` line count does NOT grow (delta <=2 lines)
- [ ] All existing motion.tsx tests still green
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.20

---

### T1.22 — prefers-reduced-motion CSS variable disable | Cx: 8 | P0

**Description:**
Add to `motion.css` a global media-query block that DISABLES animations + transitions when the user prefers reduced motion:
```
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-baseline: 0.01ms;  /* effectively instant */
    --motion-disabled: 1;
  }
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
Add a `--motion-disabled: 0` default in `:root`. JS code (hooks in Phase 6) reads `getComputedStyle(document.documentElement).getPropertyValue('--motion-disabled')` for SSR-safe fallback when `window.matchMedia` is unavailable.

**AC:**
- [ ] Failing test written FIRST: vitest+jsdom test that mocks `prefers-reduced-motion: reduce` and asserts computed `--duration-baseline` is `0.01ms`
- [ ] `motion.css` contains the media query block exactly as specified
- [ ] `--motion-disabled: 0` defaults at `:root`
- [ ] Test verifies `--motion-disabled` flips to 1 inside the media query
- [ ] Existing `frontend/src/lib/motion.tsx` ScrollReveal animations respect the override (manually verified by toggling OS setting OR Playwright `forcedColors` emulation)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.21

---

### T1.23 — Idle animation scaffold | Cx: 6 | P1

**Description:**
Add to `motion.css` a `@keyframes idle-pulse` rule and a `.animate-idle-pulse` utility:
```
@keyframes idle-pulse {
  0%, 100% { opacity: 0.6; transform: translateY(0); }
  50%      { opacity: 1.0; transform: translateY(-2px); }
}
.animate-idle-pulse {
  animation: idle-pulse 4s cubic-bezier(0.32, 0.72, 0, 1) infinite;
}
@media (prefers-reduced-motion: reduce) {
  .animate-idle-pulse { animation: none; }
}
```
Used by W4's idle-state visual cues on path-line + barrier graph.

**AC:**
- [ ] Failing test written FIRST: vitest+jsdom asserts `.animate-idle-pulse` resolves to a defined animation in computed style
- [ ] `@keyframes idle-pulse` defined in motion.css
- [ ] `.animate-idle-pulse` utility class created under `@layer utilities`
- [ ] reduced-motion override present
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.22

---

## Phase 6: Utility Hooks (10 hooks, one task each)

### T1.24 — useTimeOfDay hook | Cx: 14 | P0

**Description:**
Create `frontend/src/hooks/useTimeOfDay.ts` (and test file). Returns `{ phase: 'morning' | 'day' | 'evening' | 'night', sunPosition: number /* 0–1 */, accentShift: 'cyan' | 'amber' | 'rose' | 'navy' }`. Phase boundaries: morning 5–10, day 10–17, evening 17–20, night 20–5. Accept `latitude` parameter (default 32.7555 for Fort Worth) for sun-position calculation. SSR-safe: returns `{ phase: 'day', sunPosition: 0.5, accentShift: 'cyan' }` on server. Updates every minute via `setInterval` cleared on unmount. Used by W2 Mapbox sky setter and W4 accent shift system.

**AC:**
- [ ] Failing test written FIRST: `__tests__/useTimeOfDay.test.ts` covers initial value at fake-time 14:00 (expects phase=day), advances clock to 21:00 (expects phase=night via re-render), unmount clears interval
- [ ] All 3 cases pass after implementation
- [ ] SSR safety: imports run without error in Node-only environment (no `window` access during module evaluation)
- [ ] TypeScript signature exported: `export function useTimeOfDay(latitude?: number): { phase: TimePhase; sunPosition: number; accentShift: AccentShift }`
- [ ] React 18+ compliant (no deprecated APIs)
- [ ] `bpsai-pair arch check frontend/src/hooks/useTimeOfDay.ts` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.25 — useCursorPosition hook | Cx: 12 | P0

**Description:**
Create `frontend/src/hooks/useCursorPosition.ts`. Returns `{ x: number, y: number, vx: number, vy: number }` all normalized 0..1 (x,y) and signed (vx,vy = velocity in normalized units/ms). Uses `pointermove` event, throttled via `requestAnimationFrame`. SSR-safe (`undefined` window guarded). Cleanup on unmount. Touch-device fallback: returns `{ x: 0.5, y: 0.5, vx: 0, vy: 0 }` static (no pointermove available).

**AC:**
- [ ] Failing test written FIRST: tests cover initial value, mouse-move event triggers update with normalized coords, cleanup on unmount, touch device returns center
- [ ] All cases pass after implementation
- [ ] SSR-safe (no window access at module level)
- [ ] Touch device path verified via mocked `'ontouchstart' in window`
- [ ] Cleanup verified by asserting no listeners after unmount (jsdom dispatchEvent + spy)
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.26 — useLiveNow hook | Cx: 14 | P0

**Description:**
Create `frontend/src/hooks/useLiveNow.ts`. Returns `{ now: Date, sessions: number, lastCalibration: Date | null }`. Polls `/api/now` (defer endpoint creation to W4 — for W1, hook MUST gracefully fall back to client-computed `new Date()` + static `sessions: 0` + `lastCalibration: null` when endpoint 404s). Polling interval: 10 seconds; uses `@tanstack/react-query` (already a dep). SSR-safe (`now: new Date(0)` placeholder on server).

**AC:**
- [ ] Failing test written FIRST: covers (a) endpoint mock returns sessions=42, hook returns 42; (b) endpoint mock returns 404, hook returns sessions=0 (graceful); (c) polling fires after 10s in fake-timer test
- [ ] All cases pass
- [ ] Uses `useQuery` from `@tanstack/react-query` (no new dep)
- [ ] SSR-safe (`typeof window === 'undefined'` guard)
- [ ] Cleanup on unmount (query observer disposed)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.27 — useScrollProgress hook | Cx: 14 | P0

**Description:**
Create `frontend/src/hooks/useScrollProgress.ts`. Returns `{ chapter: number /* 0..9 indexed for 10 chapters */, progressInChapter: number /* 0..1 */, totalProgress: number /* 0..1 */ }`. Subscribes to framer-motion's `useScroll` (already a dep). Accepts `chapterCount: number` parameter (default 10). Maps total scroll progress to per-chapter progress. SSR-safe (returns chapter=0, progress=0 placeholder).

**AC:**
- [ ] Failing test written FIRST: at scrollY=0 expect chapter=0 progress=0; at midpoint expect chapter≈4–5; at scroll bottom expect chapter=9 progress≈1
- [ ] All cases pass
- [ ] SSR-safe
- [ ] React 18+ compliant
- [ ] Cleanup on unmount
- [ ] TypeScript signature exported with proper return type
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.28 — useVariableFontWeight hook | Cx: 10 | P0

**Description:**
Create `frontend/src/hooks/useVariableFontWeight.ts`. Accepts `progress: number` (0..1, typically the scroll progress for that element). Returns CSS `font-variation-settings` string interpolating between weight 700 and 900: `"wght" ${700 + 200 * progress}, "opsz" ${14 + 18 * progress}`. Pure function; trivially memoizable. Used by W4's hero headline weight axis.

**AC:**
- [ ] Failing test written FIRST: progress=0 → `"wght" 700, "opsz" 14`; progress=1 → `"wght" 900, "opsz" 32`; progress=0.5 → `"wght" 800, "opsz" 23`
- [ ] All cases pass
- [ ] Pure function (deterministic, no side effects)
- [ ] Memoized via `useMemo` for stable string ref
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.15

---

### T1.29 — useScrollVelocity hook | Cx: 10 | P1

**Description:**
Create `frontend/src/hooks/useScrollVelocity.ts`. Returns `{ velocity: number /* px/ms */, isFast: boolean /* > threshold */ }`. Uses `requestAnimationFrame` to sample scrollY delta over 50ms windows. Threshold default: 3 px/ms. Used by W4's motion-blur-on-fast-scroll life-layer. SSR-safe (`velocity: 0, isFast: false` placeholder).

**AC:**
- [ ] Failing test written FIRST: stationary → velocity 0; simulated 100px scroll over 50ms → velocity ≈ 2 (px/ms); over threshold → isFast true
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Cleanup cancels rAF on unmount
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.27

---

### T1.30 — usePrefersReducedMotion hook | Cx: 8 | P0

**Description:**
Create `frontend/src/hooks/usePrefersReducedMotion.ts`. Returns `boolean`. Checks `window.matchMedia('(prefers-reduced-motion: reduce)').matches`, subscribes to changes. SSR-safe (returns `false` on server — fail-open to motion enabled rather than disabled, since most users have it OFF). Used by every animation site in W2/W3/W4.

**AC:**
- [ ] Failing test written FIRST: matchMedia mock returns `true` → hook returns true; user toggles preference → hook re-renders with new value; SSR fallback returns false
- [ ] All cases pass
- [ ] SSR-safe (typeof window guard)
- [ ] Subscribes via `addEventListener('change', ...)` and cleans up
- [ ] TypeScript signature exported (`useReducedMotion(): boolean`)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.31 — useIdleState hook | Cx: 10 | P1

**Description:**
Create `frontend/src/hooks/useIdleState.ts`. Returns `boolean` true after N ms of no `pointermove` / `keydown` / `wheel` / `touchstart` activity. Default N: 30000 (30s). Resets timer on any input. Used by W4's idle-state visual cues (path-line gentle pulse). SSR-safe (`false` placeholder).

**AC:**
- [ ] Failing test written FIRST: initial false; after 30s of no input → true; pointer-move event → false again
- [ ] All cases pass with vitest fake timers
- [ ] SSR-safe
- [ ] Cleanup removes all 4 listeners
- [ ] Configurable N via parameter
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.32 — useViewTransitionsSupport hook | Cx: 6 | P0

**Description:**
Create `frontend/src/hooks/useViewTransitionsSupport.ts`. Returns `boolean` — true if `'startViewTransition' in document` (View Transitions API supported). Static feature detect; runs once. SSR-safe (`false` on server). Used by W3 Chapter 10 to decide between morph-transition and standard navigation.

**AC:**
- [ ] Failing test written FIRST: jsdom-mock with `startViewTransition` defined → true; without → false; SSR → false
- [ ] All cases pass
- [ ] SSR-safe
- [ ] No re-render churn (memoized boolean, evaluated once on mount)
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.33 — useLanguage hook | Cx: 10 | P0

**Description:**
Create `frontend/src/hooks/useLanguage.ts`. Wraps existing `useTranslation` (already at `frontend/src/hooks/useTranslation.tsx`). Returns `{ locale: 'en' | 'es', setLocale: (l) => void, t: (key) => string }`. Persists to `localStorage` key `gowork.locale`. Restores on mount. Defaults to browser `navigator.language` if no stored value (en if not es-prefix). Triggers re-render of all consumers when `setLocale` is called.

**AC:**
- [ ] Failing test written FIRST: initial locale='en' (no localStorage); setLocale('es') persists to localStorage; mount with 'gowork.locale'='es' in localStorage initializes to 'es'; navigator.language='es-MX' (no localStorage) defaults to 'es'
- [ ] All cases pass
- [ ] Re-uses existing `useTranslation` for `t`; does NOT duplicate logic
- [ ] SSR-safe (typeof window + typeof navigator guards)
- [ ] localStorage failure (e.g., private browsing) falls back to in-memory state without crash
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

## Phase 7: Brand Mark + Assets

### T1.34 — New `icon.svg` (G + cyan path-line) | Cx: 12 | P0

**Description:**
**Replace** `frontend/public/icon.svg` (currently the legacy stylized M-mark — see file header for "M + path mark" comment). New design from plan file: uppercase G letterform with a cyan path-line slicing through the opening of the G. **Designed at 16px first, then scaled up**: build the SVG so the 16x16 pixel grid renders crisply (snap to pixel grid, integer stroke widths). Use plan tokens: bg `--bg-base` (#0A0E1A) background or transparent for app-icon use; G stroke `--fg-primary` (#F5F3EE); path-line `--accent-cyan` (#22D3EE). Include `<title>GoWork</title>` and `aria-label="GoWork"`. Hand-tune; do NOT use auto-generated SVG. The legacy M-shape is being explicitly retired.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/__tests__/brand-mark.test.ts` reads `frontend/public/icon.svg` and asserts (a) contains `<title>GoWork</title>`, (b) does NOT contain the legacy comment "Stylized \"M\" + path mark", (c) contains `#22D3EE` or `var(--accent-cyan)`, (d) contains a `viewBox` attribute
- [ ] All assertions pass after implementation
- [ ] SVG renders crisply at 16x16 viewport (manual screenshot OR Playwright pixel-diff against reference at 16px)
- [ ] SVG passes `npm run svgo` (T1.5) idempotently
- [ ] No external font dependencies in SVG (the G is a path, not text)
- [ ] aria-label and `<title>` preserved post-svgo
- [ ] Legacy M-shape comment block REMOVED (explicit retirement note in commit message)
- [ ] Reviewer agent approves

**Depends on:** T1.5, T1.10, T1.11

---

### T1.35 — Generate raster icons from SVG (16/32/180/192/512/maskable) | Cx: 8 | P0

**Description:**
Generate the raster icon set referenced by `layout.tsx` and `manifest.json`: `favicon-16x16.png`, `favicon-32x32.png`, `apple-icon.png` (180x180), `icon-192.png`, `icon-512.png`, `icon-512-maskable.png` (with safe area for maskable). Use `sharp` (Node-only, devDep) OR ImageMagick OR a Node script wrapping `resvg-js`. Add `frontend/scripts/generate-icons.mjs` that reads `public/icon.svg` and writes all 6 PNGs.

**AC:**
- [ ] Failing test written FIRST: `frontend/scripts/__tests__/generate-icons.test.mjs` asserts script outputs all 6 files at correct dimensions
- [ ] All 6 PNGs exist in `frontend/public/` after `node scripts/generate-icons.mjs` run
- [ ] Each PNG dimensions verified (e.g., favicon-16 is 16x16)
- [ ] Maskable variant has safe-area inset (test by rendering with browser maskable preview OR by inspecting central padding)
- [ ] Script ≤120 lines, ≤6 functions, ≤15 imports
- [ ] `bpsai-pair arch check frontend/scripts/generate-icons.mjs` passes
- [ ] Reviewer agent approves

**Depends on:** T1.34

---

### T1.36 — New `og-image.svg` base | Cx: 8 | P0

**Description:**
**Replace** `frontend/public/og-image.svg` (currently the legacy GoWork-on-navy box). New base design: dark gradient background using `--bg-base` → `--bg-surface`, GoWork wordmark (variable Inter weight 800) center-left, the G+path-mark (T1.34) center-right, slogan "Workforce infrastructure for any American city." in `--fg-secondary` below the mark. 1200x630 dimensions. Used as default OG; W4 will overlay per-chapter dynamic content.

**AC:**
- [ ] Failing test written FIRST: asserts `og-image.svg` viewBox is `0 0 1200 630`, contains "Workforce infrastructure for any American city.", contains `<title>GoWork — The Wall</title>`
- [ ] SVG renders identically across Chrome / Safari / Firefox at 1200x630 (manual screenshot per browser)
- [ ] Wordmark uses variable font weight 800
- [ ] Background gradient defined as `<linearGradient>` element
- [ ] Passes svgo idempotent run
- [ ] Reviewer agent approves

**Depends on:** T1.34

---

### T1.37 — manifest.json refresh (theme + description + maskable) | Cx: 4 | P0

**Description:**
Update `frontend/public/manifest.json`: `"theme_color"` from `#1c3461` (legacy navy) → `#0A0E1A` (`--bg-base`). `"background_color"` from `#f3f1ea` → `#0A0E1A`. Update `"description"` to "Workforce infrastructure for any American city." Add `"shortcuts"` array with one entry pointing to `/assess`.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/__tests__/manifest.test.ts` reads manifest.json and asserts theme_color = '#0A0E1A', description matches new tagline, shortcuts has 1 entry
- [ ] All assertions pass
- [ ] Manifest validates against W3C Web App Manifest spec (manual or via `web-app-manifest-validator` if dep added)
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.34

---

### T1.38 — layout.tsx metadata refresh | Cx: 8 | P0

**Description:**
Update `frontend/src/app/layout.tsx` (currently 103 lines): change `viewport.themeColor` from `#1c3461` to `#0A0E1A`. Update `SITE_DESCRIPTION` to "Workforce infrastructure for any American city." Update `openGraph.title` from "GoWork — Workforce Navigator" to "GoWork — The Wall". Update `openGraph.description` to match new SITE_DESCRIPTION. Update twitter card identically. Replace `og-image.png` references with `og-image.svg` (or keep `.png` if W4 plans to render PNG output via Satori — confirm). Mount the SkipToContent link from T1.63 as the FIRST focusable element. Mount `next/font` Inter Variable from T1.15. **Single rewrite** — no other tasks edit this file in W1.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/app/__tests__/layout-metadata.test.tsx` asserts metadata.description === 'Workforce infrastructure for any American city.', viewport.themeColor === '#0A0E1A', openGraph.title === 'GoWork — The Wall'
- [ ] All assertions pass
- [ ] Existing layout.tsx tests still green
- [ ] File line count <=130 (allows headroom; current 103 + ~20 for skip-link and font-axis additions)
- [ ] `bpsai-pair arch check frontend/src/app/layout.tsx` passes
- [ ] Reviewer agent approves

**Depends on:** T1.15, T1.34, T1.36, T1.37, T1.63

---

## Phase 8: Edge States (404, 500, empty, loading, error)

### T1.40 — Custom 404 page (`app/not-found.tsx`) | Cx: 12 | P0

**Description:**
Create `frontend/src/app/not-found.tsx` (Next.js convention). Branded layout using new tokens. Headline EN: "There's no path to this URL." ES: "No hay ruta a esta dirección." Sub: "Let's get you back on the path." CTA: button to `/`. Uses `--bg-base` background, `--fg-primary` text, `--accent-cyan` button. Reduced-motion safe (no entrance animation OR animation disabled via T1.22). Translation keys under `edge.404.*` namespace in both en.json and es.json.

**AC:**
- [ ] Failing test written FIRST: `frontend/src/app/__tests__/not-found.test.tsx` asserts headline text rendered, CTA links to `/`
- [ ] Route renders at any unmatched URL (Playwright smoke: visit `/this-does-not-exist`)
- [ ] WCAG AAA contrast verified (uses --fg-primary on --bg-base = AAA)
- [ ] Keyboard-reachable CTA (focus visible)
- [ ] EN + ES locale both render correct copy via useTranslation
- [ ] reduced-motion path verified (no animation when prefers-reduced-motion set)
- [ ] Page <100 lines, no nested components beyond top-level
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.22, T1.33

---

### T1.41 — Custom 500 / global error (`app/error.tsx`) | Cx: 12 | P0

**Description:**
Create `frontend/src/app/error.tsx` (Next.js error boundary convention). Headline EN: "Something stalled. We're calibrating." ES: "Algo se detuvo. Estamos calibrando." Sub: shows correlation ID if available. CTAs: "Try again" (calls `reset()` prop) and "Go home" (link to `/`). Branded layout. Translation keys under `edge.500.*`.

**AC:**
- [ ] Failing test written FIRST: simulates Error in child component, asserts error.tsx renders with correct headline and reset button
- [ ] Reset CTA invokes `reset` prop (verified via spy)
- [ ] WCAG AAA contrast verified
- [ ] Keyboard reachable
- [ ] reduced-motion safe
- [ ] EN + ES copy
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.22, T1.33

---

### T1.42 — Reusable `EmptyState` component | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/EmptyState.tsx`. Props: `{ title: string; description?: string; icon?: React.ReactNode; cta?: { label: string; onClick?: () => void; href?: string } }`. Branded styling. Used by chapters/dashboards with no data. Default icon: a faint version of the brand mark. Translation keys for default copy fallback in `edge.empty.*`.

**AC:**
- [ ] Failing test written FIRST: render with title/description/cta, assert each text shown; cta onClick fires; href renders <a>
- [ ] Component <120 lines
- [ ] Defaults work without props (safe-render with sensible defaults)
- [ ] Keyboard reachable
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11

---

### T1.43 — Reusable `LoadingState` (skeleton) | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/LoadingState.tsx`. **Skeleton screen, not spinner** — shimmer effect respecting reduced-motion (static shimmer when motion disabled). Props: `{ rows?: number; variant?: 'card' | 'inline' | 'block' }`. Uses `--bg-elevated` for skeleton blocks, animated cyan-tinted gradient sweep.

**AC:**
- [ ] Failing test written FIRST: render with rows=3, assert 3 skeleton rows; variant='card' renders card-shape skeleton
- [ ] reduced-motion: shimmer animation off (only static gradient)
- [ ] Component <120 lines
- [ ] Accessibility: `role="status"` + `aria-live="polite"` + `aria-label="Loading"`
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.22

---

### T1.44 — Reusable `ErrorState` (per-section fallback) | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/ErrorState.tsx`. Used by individual chapter components or sections that fail without crashing the whole page. Props: `{ message: string; retry?: () => void; correlationId?: string }`. Smaller / inline visual than the global error.tsx — fits in a card or section. Branded.

**AC:**
- [ ] Failing test written FIRST: renders message, retry button calls retry prop
- [ ] correlationId rendered when provided
- [ ] Keyboard reachable retry
- [ ] reduced-motion safe
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.22

---

## Phase 9: Print Stylesheet

### T1.45 — Print stylesheet (magazine layout) + Playwright smoke | Cx: 14 | P1

**Description:**
Create `frontend/src/app/styles/print.css`. Magazine-grade print styling: serif headings (`Georgia, "Times New Roman", serif`), single-column body, page breaks at chapter boundaries (`page-break-before: always` on `.wall-chapter`), suppressed nav/header/footer/sound-toggle, suppressed Mapbox iframe (replace with placeholder caption), printed footnote with `last-calibration` timestamp. Imports into `globals.css` via `@import` with `media="print"` (or a separate `<link>` in layout.tsx — confirm Next.js best practice). ALSO add `frontend/tests/e2e/visual/print-stylesheet.spec.ts` Playwright spec that uses `page.emulateMedia({ media: 'print' })` to verify: `header` not rendered, `body` font-family contains 'serif', `.wall-chapter` page-break rule active. No screenshot diff (too brittle); just structural assertions.

**AC:**
- [ ] Failing tests written FIRST: vitest+jsdom asserts print styles included (selectors `.wall-chapter` with `page-break-before` rule); Playwright spec asserts header hidden + serif font under print emulation
- [ ] Both tests pass after implementation
- [ ] `print.css` exists in `frontend/src/app/styles/`
- [ ] Linked from layout.tsx via `<link rel="stylesheet" href="..." media="print" />` OR @import with media query
- [ ] Manual smoke: Chrome DevTools "Emulate CSS media: print" on `/` shows magazine layout (serif, no header/footer/nav)
- [ ] Playwright spec runs in CI via `npm run test:e2e`
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.16

---

## Phase 10: Page-Load Title Sequence

### T1.47 — `TitleSequence` component + Playwright integration | Cx: 16 | P0

**Description:**
Create `frontend/src/components/wall/TitleSequence.tsx`. Renders the title sequence "GoWork presents · The Wall · An interactive map of Fort Worth, Texas" over a black canvas for ~4 seconds during initial page load. Uses framer-motion with `EASE_LINEAR_SIG` (T1.20) and variable font weight breath (T1.28 hook). Fades out on completion + emits `onComplete` callback (consumed by W2's WallContainer). Reduced-motion fallback: static title, fade-in only, total duration 1s. ALSO add `frontend/tests/e2e/visual/title-sequence.spec.ts` Playwright spec that visits `/`, verifies TitleSequence visible during first 4s, gone after 5s; with `prefers-reduced-motion: reduce` emulated, title gone after 2s.

**AC:**
- [ ] Failing tests written FIRST: vitest renders component, advances fake timers 4s, asserts onComplete called once; Playwright spec asserts both motion + reduced-motion branches
- [ ] All tests pass after implementation
- [ ] Component renders title text in correct order (presents → The Wall → interactive map)
- [ ] Variable font weight breath (700→900→700) over 4s in non-reduced-motion mode
- [ ] reduced-motion: skips animation, calls onComplete after 1s
- [ ] WCAG AAA contrast (fg-primary on bg-base)
- [ ] Component <150 lines
- [ ] Playwright spec runs reliably in CI (no flaky timing — uses awaitable selectors)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.16, T1.20, T1.22, T1.28, T1.30

---

### T1.48 — TitleSequence translations (EN/ES) | Cx: 4 | P0

**Description:**
Add translation keys `wall.titleSequence.presents`, `wall.titleSequence.title`, `wall.titleSequence.subtitle` to both `en.json` and `es.json`. EN: "GoWork presents", "The Wall", "An interactive map of Fort Worth, Texas". ES: "GoWork presenta", "El Muro", "Un mapa interactivo de Fort Worth, Texas". Component (T1.47) consumes via `useTranslation`.

**AC:**
- [ ] Failing test written FIRST: asserts keys present in both en.json and es.json with correct values
- [ ] Both locales include all 3 keys
- [ ] Spanish copy reviewed for natural tone (not literal Google translation — note in PR if AI-translated and which model)
- [ ] No regression on existing translation keys
- [ ] Reviewer agent approves

**Depends on:** T1.47

---

## Phase 11: Header + Footer Redesign

### T1.50 — `PathLineHeader` component | Cx: 10 | P0

**Description:**
Create `frontend/src/components/wall/PathLineHeader.tsx`. The persistent path-line that runs along the top edge of the viewport, rendered as an actual SVG line (NOT a stock progress bar). Connected to `useScrollProgress` (T1.27). Cyan stroke, 2px, animated `stroke-dashoffset` for draw-on effect. Reduced-motion: static line at current scroll position (no animation). Used by Header (T1.51).

**AC:**
- [ ] Failing test written FIRST: renders SVG line, scroll progress 0 → stroke-dashoffset full; progress 1 → stroke-dashoffset 0
- [ ] SVG element with `role="progressbar"` and `aria-valuenow` set to current progress percentage
- [ ] reduced-motion: static, no animation transition
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.27, T1.30, T1.11

---

### T1.51 — Header rewrite (brand + path-line + counter + toggles + GitHub) | Cx: 14 | P0

**Description:**
Rewrite `frontend/src/components/layout/Header.tsx` (currently 34 lines). New layout: left = brand mark (T1.34) + "GoWork" wordmark; center = ChapterCounter (T1.52); right = MuteToggle (T1.53) + LanguageToggle (T1.54) + GitHub icon link. Top-edge: PathLineHeader (T1.50) overlay. Sticky positioning preserved. Skip-link landing target (id="content") respected. Header height 56px (h-14). Visible-only on Wall pages (homepage); hidden on /assess, /plan, etc. via path matcher OR pass-through prop.

**AC:**
- [ ] Failing test written FIRST: renders brand wordmark "GoWork", PathLineHeader, ChapterCounter, MuteToggle, LanguageToggle, GitHub link with `aria-label="GitHub"`
- [ ] Existing Header tests still green (StallAlertBannerMount preserved)
- [ ] File <=120 lines (current 34 + ~80 additions max — keep tight by importing sub-components)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.34, T1.50, T1.52, T1.53, T1.54

---

### T1.52 — `ChapterCounter` component | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/ChapterCounter.tsx`. Sticky position top-right (or absorbed into Header). Renders `01/10` style counter using tabular-nums (T1.17). Reads chapter number from `useScrollProgress` (T1.27). Hidden on non-Wall routes. Tabular nums prevent number-jitter as digits change.

**AC:**
- [ ] Failing test written FIRST: chapter=0 → renders "01/10"; chapter=4 → "05/10"; chapter=9 → "10/10"
- [ ] Uses .tabular-nums class (T1.17)
- [ ] Renders within 1 frame of scroll-progress update (no debounce visible to user)
- [ ] Component <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.17, T1.27

---

### T1.53 — `MuteToggle` component | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/MuteToggle.tsx`. Icon button (volume-up / volume-mute lucide icons). State: muted boolean, persisted in localStorage key `gowork.muted` (default `true` — sound is OPT-IN per audio template). Calls `setMuted` from audio singleton (T1.55). Keyboard reachable; aria-label changes between "Mute sound" / "Enable sound".

**AC:**
- [ ] Failing test written FIRST: initial state muted=true; click → muted=false; localStorage updated; aria-label flips correctly
- [ ] localStorage failure (private browsing) falls back to in-memory state
- [ ] WCAG AAA focus ring visible on tab
- [ ] Component <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.55, T1.33

---

### T1.54 — `LanguageToggle` component | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/LanguageToggle.tsx`. Pill toggle "EN | ES" (or similar). Uses `useLanguage` hook (T1.33). Click flips locale; persists to localStorage. Aria-label "Switch language" with current state announced via aria-live.

**AC:**
- [ ] Failing test written FIRST: initial 'en'; click → 'es' + localStorage persisted; useLanguage state updates
- [ ] Aria-live region announces "Language: Spanish" / "Idioma: Inglés" on toggle
- [ ] Keyboard reachable, focus visible
- [ ] Component <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.33

---

### T1.55 — Footer rewrite (brand + links + MIT + last-calibration) | Cx: 8 | P0

**Description:**
Rewrite `frontend/src/components/layout/Footer.tsx` (currently 57 lines). Layout: left = brand mark (16px) + "GoWork" wordmark; center = links (Privacy, Terms, GitHub, Press Kit, Case Manager); right = "MIT-licensed · Last calibrated <timestamp>" using useLiveNow (T1.26). Replace existing legal-entity placeholder text with the new layout. Translation keys under `footer.*` namespace (most exist already; extend for "MIT-licensed", "Last calibrated", "Press Kit", "Case Manager").

**AC:**
- [ ] Failing test written FIRST: renders brand mark, GoWork wordmark, all 5 links (privacy, terms, github, press, case-manager), "MIT-licensed" string, last-calibration timestamp
- [ ] Existing Footer tests still green (legal placeholders preserved as constants if needed for backward compat)
- [ ] File <=120 lines
- [ ] EN + ES locale verified
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.26, T1.34, T1.33

---

## Phase 12: Audio System Scaffold

### T1.56 — Howler singleton + sound module | Cx: 12 | P1

**Description:**
Create `frontend/src/lib/wall/sound.ts`. Module-level singleton wrapping Howler.js (T1.4). API: `play(soundId: SoundId, volume?: number): void`, `stop(soundId: SoundId): void`, `setMuted(muted: boolean): void`, `isMuted(): boolean`. SoundId enum/union: `'footstep' | 'paper-rustle' | 'calculator-click' | 'chime' | 'wind-ambient'`. Internal: lazy-load Howler ONLY when first play() called (so muted users never download Howler). All play() no-ops when muted. Audio context unlocked on first user gesture (Howler handles).

**AC:**
- [ ] Failing test written FIRST: `frontend/src/lib/wall/__tests__/sound.test.ts` mocks Howler, tests play/stop/setMuted/isMuted; verifies muted state suppresses play; verifies lazy-load (Howler import not invoked until first play)
- [ ] All cases pass
- [ ] Module <200 lines, <15 functions, <10 imports
- [ ] SSR-safe (typeof window guard)
- [ ] Howler not in main bundle (verified via `npm run analyze`)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.4

---

### T1.57 — Sound asset directory scaffold | Cx: 4 | P1

**Description:**
Create `frontend/public/sounds/` directory. Add a `README.md` documenting the sound file naming convention (`footstep.mp3`, `paper-rustle.mp3`, etc.) and required attributes: <50KB MP3, 44.1kHz, mono. Add ONE placeholder silent MP3 (1-second silence) per soundId so the sound module (T1.56) can load without 404 in dev. Document attribution license requirements (must be CC0 or licensed) for replacement assets in W2/W3.

**AC:**
- [ ] Failing test written FIRST: asserts `frontend/public/sounds/` exists with all 5 sound files (`footstep.mp3`, `paper-rustle.mp3`, `calculator-click.mp3`, `chime.mp3`, `wind-ambient.mp3`)
- [ ] All 5 placeholder MP3s present (silent 1s)
- [ ] README.md documents replacement requirements (license, byte budget, format)
- [ ] No file >50KB
- [ ] Reviewer agent approves

**Depends on:** T1.56

---

### T1.58 — Audio context unlock listener | Cx: 6 | P1

**Description:**
In `sound.ts`, add a one-time first-user-gesture listener (`pointerdown` OR `keydown`) that calls Howler.ctx.resume() if suspended. Many browsers suspend AudioContext until user interaction; this is the unlock. Removes itself after first call.

**AC:**
- [ ] Failing test written FIRST: jsdom dispatch pointerdown, assert resume() called once; second pointerdown does NOT call resume again
- [ ] Implementation passes
- [ ] No memory leak (listener removed after first use)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.56

---

### T1.59 — Mute persistence (localStorage) | Cx: 6 | P1

**Description:**
In `sound.ts`, on module init, read `localStorage.getItem('gowork.muted')` (default 'true'). On `setMuted` calls, write to localStorage. Coordinate key with MuteToggle (T1.53) — both share key `gowork.muted`. Wrap in try/catch (private browsing).

**AC:**
- [ ] Failing test written FIRST: localStorage gowork.muted='false' on mount → isMuted() returns false; setMuted(true) → localStorage updated
- [ ] localStorage failure path doesn't crash module
- [ ] Test that MuteToggle and sound module read same value (cross-component contract)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.56, T1.53

---

## Phase 13: Cursor System

### T1.60 — `CursorTrail` component (default cursor enhancement) | Cx: 10 | P1

**Description:**
Create `frontend/src/components/wall/CursorTrail.tsx`. Renders a soft trailing dot that follows the cursor with spring lag (uses `SPRING_SOFT` from T1.19 + `useCursorPosition` from T1.25). Visible site-wide on desktop only (touch devices: returns null). Dot is 8px diameter, `--accent-cyan` with 60% opacity, mix-blend-mode: screen. Reduced-motion: static dot at center (or hidden).

**AC:**
- [ ] Failing test written FIRST: renders dot element on desktop; touch device returns null; reduced-motion hides or stills the dot
- [ ] Component <100 lines
- [ ] No layout shift (dot is `position: fixed` with `pointer-events: none`)
- [ ] WCAG: dot must NOT obscure focus indicators (verified by manual focus-on-button check + screenshot)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.19, T1.25, T1.30

---

### T1.61 — `CursorFlashlight` component (map overlay) | Cx: 12 | P2

**Description:**
Create `frontend/src/components/wall/CursorFlashlight.tsx`. The 80px glow circle that brightens map elements within. Wired to `useCursorPosition`. Used ONLY on map (W2 will mount it inside MapboxScene). For W1, build the component + a sandbox demo route (`/sandbox/flashlight`, dev-only) so it can be visually verified without Mapbox. Reduced-motion / no-pointer fallback: full-page brightness uniform (no flashlight effect).

**AC:**
- [ ] Failing test written FIRST: renders div with radial-gradient backdrop-filter; cursor at (0.3, 0.7) updates css variables `--flashlight-x` and `--flashlight-y`
- [ ] reduced-motion: gradient is full-bright (no localized effect)
- [ ] Touch device: gradient uniform
- [ ] Sandbox route renders without Mapbox dep
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.25, T1.30, T1.11

---

## Phase 14: ARIA + Accessibility Scaffolding

### T1.63 — Skip-to-content link | Cx: 6 | P0

**Description:**
Create `frontend/src/components/SkipToContent.tsx`. An anchor `<a href="#content">Skip to main content</a>` styled invisible-until-focused (`sr-only` baseline; `focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50` reveals on tab). Mounted in layout.tsx (T1.38) as the first focusable element on the page. Translation key `a11y.skipToContent` in EN+ES.

**AC:**
- [ ] Failing test written FIRST: renders link; screen-reader-only by default; focused → visible at top-left with z-50
- [ ] Anchor target #content matches the wrapping element id in layout.tsx
- [ ] EN + ES translation keys
- [ ] Tab order: SkipToContent is FIRST tab stop on every page (Playwright assert)
- [ ] Component <60 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11

---

### T1.64 — `AriaLiveRegion` scaffold | Cx: 8 | P0

**Description:**
Create `frontend/src/components/wall/AriaLiveRegion.tsx`. A globally mounted polite + assertive live region pair. Exposes context API `useAriaLive()` returning `{ announce: (msg: string, priority?: 'polite' | 'assertive') => void }`. Used by chapter components to announce camera transitions and state changes (e.g., "Now in Chapter 4: The Wall, no transit barrier"). Auto-clears region after 1 second to allow re-announcements.

**AC:**
- [ ] Failing test written FIRST: announce('hello') puts text in polite region; assertive priority puts in assertive region; auto-clears after 1s
- [ ] Both regions present in DOM (`role="status"` polite; `role="alert"` assertive)
- [ ] Provider wraps children; `useAriaLive` outside provider throws clear error
- [ ] Component <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10

---

### T1.65 — Custom focus rings + selection styles (CSS) | Cx: 8 | P0

**Description:**
Add to `frontend/src/app/styles/tokens/layout.css`:
(a) Focus ring: `*:focus-visible { outline: 2px solid var(--accent-cyan); outline-offset: 2px; transition: outline-offset 150ms cubic-bezier(0.32, 0.72, 0, 1); }` (animated entry — outline-offset 0 → 2px). Reduced-motion: instant offset.
(b) Selection: `::selection { background-color: color-mix(in oklch, var(--accent-cyan), transparent 60%); color: var(--fg-primary); }` plus `::-moz-selection` fallback.
WCAG AAA: 2px outline at 3:1 contrast minimum on every background — verified by T1.13 contrast script.

**AC:**
- [ ] Failing test written FIRST: vitest+jsdom asserts `:focus-visible` rule includes outline cyan AND `::selection` rule includes accent-cyan
- [ ] Both rules defined in layout.css
- [ ] `::-moz-selection` fallback present
- [ ] reduced-motion override removes transition on focus
- [ ] Manual test: tab through `/`, every focusable shows cyan outline; select text, see cyan-tinted background
- [ ] Contrast ratio cyan-on-base, cyan-on-surface, cyan-on-elevated all ≥3:1 (verified by T1.13)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.11, T1.13, T1.22

---

## Phase 15: TypeScript Types + Exports

### T1.67 — `lib/wall/types.ts` | Cx: 8 | P0

**Description:**
Create `frontend/src/lib/wall/types.ts`. Exports core type definitions used across W1–W4: `TimePhase`, `AccentShift`, `ChapterId` (literal union 1..10), `ChapterState`, `MapboxLayer` interface (id, type, source, paint), `CameraState` (zoom, pitch, bearing, lng, lat), `SoundId` (mirrors T1.56's union), `LocaleCode = 'en' | 'es'`. No runtime code; pure types.

**AC:**
- [ ] Failing test written FIRST: type-level test using `expectTypeOf` from vitest covers each exported type compiles correctly
- [ ] All types exported
- [ ] No `any` usage; all properly typed
- [ ] File <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.68 — `lib/wall/index.ts` hub + `hooks/index.ts` barrel | Cx: 8 | P0

**Description:**
Create TWO barrel files for clean public APIs (hub-and-spoke pattern from `architecting-modules` skill):
(a) `frontend/src/lib/wall/index.ts` re-exporting: types from `types.ts`, tokens from `tokens.ts`, `validateMapboxToken` from `env.ts`, sound module from `sound.ts`. **Hooks NOT re-exported here** — kept at their own path.
(b) `frontend/src/hooks/index.ts` re-exporting all 10 W1 hooks (T1.24–T1.33) plus existing `useTranslation` and `useCityConfig` for consistency. Allows `import { useTimeOfDay, useCursorPosition } from '@/hooks'`. Existing direct imports across codebase still work (no forced migration).

**AC:**
- [ ] Failing tests written FIRST: `import { validateMapboxToken, SPRING_SOFT, type ChapterId } from '@/lib/wall'` compiles; `import { useTimeOfDay, useCursorPosition } from '@/hooks'` compiles
- [ ] Both files exist
- [ ] All P0 exports present in lib/wall/index.ts; all 10 W1 hooks + 2 existing hooks in hooks/index.ts
- [ ] No circular imports (verified by `tsc --noEmit`)
- [ ] Each file <50 lines (just re-exports)
- [ ] Existing direct imports across the codebase still work (verified by `npm run build` exit 0)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6, T1.19, T1.56, T1.67, T1.24, T1.25, T1.26, T1.27, T1.28, T1.29, T1.30, T1.31, T1.32, T1.33

---

## Phase 16: Verification & Wiring

### T1.70 — `bpsai-pair arch check` clean sweep | Cx: 6 | P0

**Description:**
Final architecture compliance check across all NEW W1 files. Run `bpsai-pair arch check frontend/src/lib/wall/ frontend/src/hooks/ frontend/src/components/wall/ frontend/src/app/styles/ frontend/scripts/`. Fix any violations (extract helpers if needed). Document the clean check in `frontend/docs/w1-arch-check.md` with timestamp + version.

**AC:**
- [ ] All paths above pass `bpsai-pair arch check` with zero errors
- [ ] Warnings (e.g., approaching 200 lines) documented in arch-check.md
- [ ] Output appended to PR description
- [ ] Reviewer agent approves

**Depends on:** T1.61, T1.65, T1.68

---

### T1.72 — Full W1 vitest suite green | Cx: 8 | P0

**Description:**
Run `npm test` (vitest) on the full frontend test suite. All existing tests + all new W1 tests must pass. Target: 100% of new W1 tests green; 95%+ overall (existing baseline). Document any failures in PR with root cause.

**AC:**
- [ ] `cd frontend && npm test` exits 0
- [ ] No new test failures versus S13 baseline
- [ ] All W1 tests covering hooks, tokens, components, and edge states pass
- [ ] Coverage report shows ≥95% on new code
- [ ] Reviewer agent approves

**Depends on:** T1.70

---

## Phase 17: Spotlight Inventions (added beyond the brief)

These tasks are NOT in the brief's 16 categories. They emerged from the Spotlight protocol (Permission, Multiple Selves, Fusion, Honesty, Legacy). Each represents a creative addition that strengthens the foundation in a way the brief did not anticipate.

### T1.73 — `usePerformanceBudget` hook (Honesty + Resilience) | Cx: 10 | P1

**Description:**
**Spotlight invention 1 — Performance budget telemetry.** Create `frontend/src/hooks/usePerformanceBudget.ts`. Returns `{ longTasksMs: number, jsHeapUsedMb: number, droppedFrames: number, isUnderPressure: boolean }`. Uses `PerformanceObserver` for longtask entries, `performance.memory` (Chrome only — degrade gracefully on Safari/Firefox), and `requestAnimationFrame` delta heuristic for frames. `isUnderPressure` true when any threshold exceeded. **Why beyond brief:** the brief mentions Lighthouse 90+ as the W4 gate but provides no telemetry to know WHEN we're trending toward failure DURING W2/W3 builds. This hook is the canary. W2's Mapbox engine and W3's 3D graph are the riskiest perf items; this hook lets each chapter component log when it's the bottleneck. **Confidence:** C2 — clear value, well-supported APIs.

**AC:**
- [ ] Failing test written FIRST: stationary returns 0/0/0/false; mock long-task observer entry → longTasksMs > 50; chrome-memory mock → jsHeapUsedMb populated
- [ ] All cases pass
- [ ] SSR-safe (typeof PerformanceObserver guard)
- [ ] Cleanup disconnects observer on unmount
- [ ] Safari/Firefox graceful degradation (memory always 0; long tasks still work)
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.74 — Mapbox-token-missing branded fallback page (Resilience + Honesty) | Cx: 10 | P1

**Description:**
**Spotlight invention 2 — Token-missing fallback.** Create `frontend/src/components/wall/MapboxTokenMissing.tsx`. Branded full-page fallback rendered when `validateMapboxToken()` (T1.6) returns ok=false. Shows: brand mark, headline "The map is offline.", sub "GoWork's interactive Wall requires a Mapbox token. The team is reading the docs.", CTA to GitHub README setup section. **Why beyond brief:** the brief notes "fall back to static" but doesn't design the fallback. Judges who clone the repo without setting `NEXT_PUBLIC_MAPBOX_TOKEN` will see a broken page on first run — first impression cratered. This component is the first-impression rescue. Reused by W2's `WallContainer` static-fallback path. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: render with no token → renders branded fallback; render with valid token → null (i.e., does NOT mount when token present)
- [ ] WCAG AAA contrast verified
- [ ] EN + ES copy via translations
- [ ] CTA link to GitHub README anchor (#mapbox-setup)
- [ ] reduced-motion safe
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6, T1.10, T1.34, T1.33

---

### T1.75 — `useDeviceCapability` hook (Multiple Selves + Resilience) | Cx: 10 | P1

**Description:**
**Spotlight invention 3 — Device capability tier.** Create `frontend/src/hooks/useDeviceCapability.ts`. Returns `{ tier: 'low' | 'medium' | 'high', supportsWebGL: boolean, isMobile: boolean, deviceMemoryGb: number | null, hardwareConcurrency: number, prefersReducedData: boolean }`. Used by W2/W3 to select between full Mapbox + 3D graph (high), reduced-effects 2D (medium), or static-fallback images (low). Reads `navigator.deviceMemory`, `navigator.hardwareConcurrency`, `navigator.connection.saveData`. **Why beyond brief:** the brief says "mobile fallback (non-negotiable)" but only mentions `window.innerWidth` detection. That misses: low-end Android with 2GB RAM will choke on Three.js even at desktop resolution. This hook gives W3 the signal to drop the 3D graph for low-tier devices BEFORE rendering. **Confidence:** C2 (well-supported APIs, with fallbacks).

**AC:**
- [ ] Failing test written FIRST: mock high-end (8GB, 8 cores, no save-data) → tier='high'; mock low-end (2GB, 2 cores, save-data on) → tier='low'; SSR safe
- [ ] All cases pass
- [ ] Graceful degradation when navigator.deviceMemory unsupported (Safari)
- [ ] WebGL detection cached (don't re-create canvas every render)
- [ ] TypeScript signature exported
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.76 — Storybook-lite token gallery (Legacy + Wisdom) | Cx: 10 | P2

**Description:**
**Spotlight invention 4 — Token gallery for design review.** The brief lists Storybook as deferrable P2. Build a tiny non-Storybook alternative: `frontend/src/app/(dev)/tokens/page.tsx` route (dev-only via env check) that renders all W1 tokens in a single page — every color swatch with hex+oklch+contrast ratios; every type scale at every breakpoint; every spring preset previewed via a click-to-animate demo; brand mark at 16/32/64/180/512 sizes. Reviewer agent + Shawn review the gallery in 2 minutes instead of opening 10 files. **Why beyond brief:** judges will not open the source — but Shawn + Ren will need to verify the foundation in one glance before W2 builds on it. Saves dispatch round-trips on token QC. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: visiting `/tokens` (dev mode) renders, contains every color token name, every type scale name, every spring preset name, brand mark at 5 sizes
- [ ] Route only renders in dev (production returns 404 or redirects to /)
- [ ] No production bundle bloat (verified via `npm run analyze` — route is dev-only chunk)
- [ ] Page <300 lines, decomposed into sub-components if needed (each <100 lines)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.16, T1.19, T1.34

---

### T1.77 — `LegacyMShapeAlert` migration warning + state.md note (Wisdom + Honesty) | Cx: 6 | P2

**Description:**
**Spotlight invention 5 — Explicit retirement audit.** When T1.34 retires the legacy M-shape `icon.svg`, several places in the codebase may reference the old shape implicitly (PWA cache, OG image cache, social share previews already in the wild). Create `frontend/scripts/audit-legacy-mshape.mjs` that greps the entire repo for any references to "stylized M", "M + path mark", or the old hex `#1c3461` (legacy navy). Outputs report. Also append a "Legacy retirement notes" subsection to `.paircoder/context/state.md` documenting the explicit retirement (date, replacement file, places audited). **Why beyond brief:** silent retirement = forgotten ghost in a year. Explicit retirement = future-you knows what changed and why. Honesty about state. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: `frontend/scripts/__tests__/audit-legacy-mshape.test.mjs` asserts script reports any matches in fixture; reports empty on clean fixture
- [ ] Script greps for the 3 patterns above and reports matches with file:line
- [ ] After T1.34 lands, script reports zero matches in production source paths (`docs/`, `frontend/src/`, `frontend/public/` minus retired `icon.svg`'s git-history)
- [ ] state.md updated with retirement subsection (timestamp, list of audited paths, rationale)
- [ ] Script <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.34

---

## Phase 18: Analytics & Telemetry (Enrichment Pass)

The brief sets a Lighthouse 90+ gate but does not specify how we will know — during the live demo on May 2 — whether the home page is being read, where readers drop off, or which chapter is the bottleneck. Phase 18 builds a privacy-friendly analytics + RUM scaffold that costs <2KB shipped JS and reports nothing personally identifiable. **This is the difference between "we built it" and "we know how it performed."**

### T1.78 — Plausible-style privacy-first analytics scaffold | Cx: 10 | P1

**Description:**
Create `frontend/src/lib/analytics/client.ts`. Self-hosted, cookie-less analytics dispatcher. Exposes `track(event: AnalyticsEvent, props?: Record<string, string | number>)` and `pageview(path: string)`. Posts to `/api/analytics/ingest` (W4 endpoint — for W1, hook MUST gracefully no-op when endpoint 404s). **No cookies, no fingerprinting, no PII** — the whole point. Event types union: `'pageview' | 'chapter_enter' | 'chapter_exit' | 'cta_click' | 'language_toggle' | 'mute_toggle'`. Sampling rate default 100%; reads `NEXT_PUBLIC_ANALYTICS_SAMPLE_RATE` for production tuning. Respects `navigator.doNotTrack === '1'` (no-op when DNT). **Why beyond brief:** brief never names how we measure reader engagement; without this we are flying blind on demo day. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: track('cta_click', {chapter: '06'}) posts to /api/analytics/ingest with body matching schema; DNT=1 → no fetch; endpoint 404 → swallowed gracefully (no console error on caller's path)
- [ ] All cases pass after implementation
- [ ] Module <200 lines, <15 fns, <15 imports
- [ ] No cookies set (verified by document.cookie spy after track call)
- [ ] No PII in payload schema (TypeScript narrows props to string|number primitives only)
- [ ] SSR-safe (typeof window guard)
- [ ] Bundle size <2KB minified+gzipped (verified via `npm run analyze` — module is its own chunk if dynamically imported)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.79 — Web Vitals reporter (CWV → analytics) | Cx: 10 | P1

**Description:**
Create `frontend/src/lib/analytics/web-vitals.ts`. Subscribes to Core Web Vitals via the `web-vitals` npm package (add to deps; ~1KB). Reports LCP, CLS, INP, FCP, TTFB to the analytics dispatcher (T1.78) under event name `web_vital` with props `{ metric: string; value: number; rating: 'good' | 'needs-improvement' | 'poor' }`. Hook `useWebVitalsReporter()` mounted once in `layout.tsx`. **Why beyond brief:** the brief's Lighthouse gate is a single CI snapshot; this reports live RUM values from real users, which is what judges and W4 perf descope decisions actually need. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: mock onLCP fires with value 2400 → dispatcher.track('web_vital', {metric:'LCP', value:2400, rating:'good'}) called once
- [ ] All 5 vitals (LCP, CLS, INP, FCP, TTFB) wired
- [ ] Hook mounted once (idempotent — second mount in test does NOT double-subscribe)
- [ ] `web-vitals` package pinned in package.json (~v4.x)
- [ ] SSR-safe
- [ ] Bundle delta <2KB
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.78

---

### T1.80 — Chapter scroll-depth event ladder | Cx: 8 | P1

**Description:**
Create `frontend/src/hooks/useChapterScrollTelemetry.ts`. Wraps `useScrollProgress` (T1.27). Emits `chapter_enter` and `chapter_exit` events via T1.78 dispatcher when chapter index changes. Also emits `chapter_quartile` events at 25/50/75/100% within-chapter progress (deduped per chapter per session). Used by W2 chapters to feed the bounce-rate-per-chapter telemetry the brief never specified. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: simulate scroll: chapter 0→1 fires `chapter_exit` for 0 + `chapter_enter` for 1; within-chapter 0.5 fires `chapter_quartile` once; within-chapter 0.5 again does NOT re-fire (deduped)
- [ ] Cases pass
- [ ] Hook returns no value (side-effect only)
- [ ] SSR-safe
- [ ] Hook <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.27, T1.78

---

### T1.81 — RUM session ID hash utility (PII-safe) | Cx: 6 | P1

**Description:**
Create `frontend/src/lib/analytics/session-id.ts`. Generates a per-tab session ID by hashing `navigator.userAgent + screen.width + Date.now()` with SHA-256 (Web Crypto API), stored in `sessionStorage` (NOT localStorage — dies on tab close). Exposes `getSessionId(): Promise<string>`. Attached to every analytics event. **Hash, never raw** — the user agent is a fingerprint vector, the hash is not. **Why beyond brief:** brief mentions Live Now widget needs session count but never says how we count without breaching PII. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: getSessionId() returns 64-char hex string; second call within same tab returns same id; sessionStorage cleared → next call returns new id
- [ ] Cases pass
- [ ] No raw user-agent or any non-hashed PII appears in sessionStorage value
- [ ] SSR-safe (returns 'ssr' literal on server)
- [ ] Module <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.82 — Animation framerate dev overlay | Cx: 10 | P2

**Description:**
Create `frontend/src/components/dev/FpsOverlay.tsx`. Dev-only (env-guarded) bottom-left fixed overlay showing live FPS (rAF delta moving average over 1s window). Color-coded: ≥58 green, 30–57 amber, <30 rose. Toggle via `?fps=1` query string OR Ctrl+Shift+F. **Production bundle excludes the component** (verified via `npm run analyze` — chunk only present in dev). **Why beyond brief:** brief promises 60fps but provides no per-build feedback loop; this overlay tells Driver agents in real-time when an animation is dropping frames. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: rendered when env=dev AND ?fps=1 set; rendered when Ctrl+Shift+F dispatched; not rendered when env=production
- [ ] FPS computation correct (mock rAF delta of 16.67ms → reports ~60fps)
- [ ] Color-coding switches at 58 and 30 thresholds
- [ ] Production bundle does NOT include component (verified by build inspection)
- [ ] Component <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11

---

## Phase 19: SEO & Discoverability (Enrichment Pass)

The brief notes SEO 0.9 in `lighthouserc.json` but the Wall page has no editorial meta strategy. Schema.org markup, hreflang, per-route descriptions, sitemap chapter expansion, OG variants — all missing. Phase 19 closes the gap. **Why this matters for HackFW:** judges who Google "GoWork" or share the URL on Twitter/LinkedIn must see correctly-rendered cards with the locked slogan, not Next.js defaults.

### T1.83 — Schema.org JSON-LD: Article, Person, Organization, Place | Cx: 12 | P1

**Description:**
Create `frontend/src/lib/seo/jsonld.ts`. Exports four typed builders:
(a) `articleJsonLd({ headline, datePublished, author, image })` → Article schema for the Wall home page;
(b) `personJsonLd()` → Person schema for Carlos (alias name "Carlos" + structuredData persona — flagged as "fictional case study" via `description` field, NOT as real person — IMPORTANT for honesty);
(c) `organizationJsonLd()` → Organization for GoWork with logo, slogan, openSource Project, MIT license URL;
(d) `placeJsonLd()` → Place for Fort Worth, TX with geo coords, country US, addressRegion TX. Outputs `<script type="application/ld+json">` strings for layout/page injection. **Why beyond brief:** Schema.org puts the slogan in Google's knowledge panel and powers rich snippets. **Confidence:** C3 (schema correctness without SEO consultant — worst case rich-snippet won't render but no harm).

**AC:**
- [ ] Failing test written FIRST: each builder returns valid JSON-LD with required @context and @type fields; Person includes `description: "Fictional case study persona for civic-tech demonstration"` (no real-PII assertion); Article schema lifts copy thesis EXACTLY
- [ ] All 4 builders pass JSON-schema validation against Schema.org context
- [ ] No real Carlos PII (e.g., specific address) in Person schema — Place schema uses ZIP-area centroid only
- [ ] Validates clean against Google's Rich Results Test (manual run, document result in PR)
- [ ] Module <200 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.84 — Per-route meta description map | Cx: 6 | P1

**Description:**
Create `frontend/src/lib/seo/meta-map.ts`. Const map `Record<string, { title: string; description: string }>` — one entry per route (`/`, `/assess`, `/plan`, `/jobs`, `/daily`, `/appointments`, `/case-manager`, `/privacy`, `/terms`). Descriptions lifted from copy thesis where appropriate, ~155 chars each. Default fallback uses locked slogan. Function `getRouteMeta(pathname: string)` returns the entry or fallback. Used by `layout.tsx` (T1.38) and any per-route metadata. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: getRouteMeta('/') returns description containing "Workforce infrastructure for any American city."; getRouteMeta('/unknown') returns the fallback default
- [ ] All 9 routes populated
- [ ] Each description ≤160 chars (Google preferred)
- [ ] Each title ≤60 chars (Google preferred)
- [ ] Module <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.85 — Hreflang alternates for EN/ES | Cx: 6 | P1

**Description:**
Update `frontend/src/app/layout.tsx` (T1.38 owns the file; this task adds the alternates section in metadata.alternates.languages — coordinate via Depends on: T1.38). Adds `'en-US'` and `'es-MX'` hreflang alternates pointing to `/?lang=en` and `/?lang=es` (or however the language toggle wires URLs in W4 — for W1, alternate paths are placeholders documented in PR). **Why beyond brief:** Spanish parity is in the brief, but search engines need hreflang to know two languages exist; without this, the ES variant is invisible to Spanish-speaking searchers. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: layout-metadata test asserts `metadata.alternates.languages['en-US']` and `['es-MX']` set to `/?lang=en` and `/?lang=es`
- [ ] Both alternates present
- [ ] No regression on other metadata
- [ ] `bpsai-pair arch check frontend/src/app/layout.tsx` passes (file <130 lines budget upheld)
- [ ] Reviewer agent approves

**Depends on:** T1.38

---

### T1.86 — Sitemap chapter expansion + canonical URLs | Cx: 8 | P1

**Description:**
Update `frontend/src/app/sitemap.ts` (existing, untouched in W1 so far). Add per-chapter URLs as fragments — `/#chapter-01` through `/#chapter-10` — with `lastmod` set to the build timestamp. Also add `/?lang=en` and `/?lang=es` variants per chapter (link with hreflang from T1.85). Add canonical URL pattern: `<link rel="canonical">` injected via metadata.alternates.canonical = `/`. Each chapter URL gets priority 0.7; root gets 1.0. **Why beyond brief:** the chapter scroll structure is invisible to crawlers without per-chapter URLs. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: sitemap test asserts 10 chapter URLs present (each with `#chapter-NN` fragment) + 2 lang variants per chapter = 30+ entries; canonical metadata.alternates.canonical = '/'
- [ ] All assertions pass
- [ ] sitemap.ts file <100 lines
- [ ] No regression on existing sitemap entries (privacy/terms/etc still present)
- [ ] `bpsai-pair arch check frontend/src/app/sitemap.ts` passes
- [ ] Reviewer agent approves

**Depends on:** T1.85

---

### T1.87 — robots.txt extension (sitemap, allow rules, AI bot policy) | Cx: 4 | P1

**Description:**
Update `frontend/src/app/robots.ts` (existing). Verify `Sitemap` directive points to `/sitemap.xml`. Add explicit `Allow: /` for crawlers. Add policy directives for AI training bots: `User-agent: GPTBot`, `User-agent: Google-Extended`, `User-agent: anthropic-ai` — set to `Allow: /` (we ARE open-source, we DO want to be in training data — civic tech reach maximizer). Document this decision in inline comments. **Why beyond brief:** AI bots are now a meaningful traffic source; explicit policy is more honest than silence. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: robots.ts output asserts `Sitemap: ...` line, explicit GPTBot/Google-Extended/anthropic-ai entries, all set to Allow
- [ ] Inline comment explains the open-source policy decision
- [ ] No new restrictions added (we are public)
- [ ] robots.ts file <60 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.88 — OG variants for Twitter, LinkedIn, Facebook + DNS prefetch | Cx: 8 | P1

**Description:**
Update layout.tsx metadata (coordinate with T1.38, T1.85): Twitter card type `summary_large_image` with locked slogan; LinkedIn uses `og:image:width=1200, og:image:height=627` (their preferred); Facebook respects standard og:image. Different platforms cache OG differently — verified via Twitter Card Validator + LinkedIn Post Inspector + Facebook Debugger (manual, document in PR). ALSO add `<link rel="dns-prefetch" href="//api.mapbox.com" />` and `<link rel="preconnect" href="https://fonts.googleapis.com">` to layout.tsx head. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: layout-metadata test asserts twitter.card === 'summary_large_image', og:image:width === 1200; head contains dns-prefetch for api.mapbox.com
- [ ] All assertions pass
- [ ] Manual validators (Twitter, LinkedIn, Facebook) all show correct preview — document screenshots in PR
- [ ] No regression on existing metadata
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.85

---

## Phase 20: PWA & Offline (Enrichment Pass)

The brief mentions PWA in passing (manifest theme color was T1.37) but never adds offline support, install prompt UX, or branded offline page. For a "real infrastructure" signal, the home page should install on a phone, work offline (read-only), and look branded when down. Phase 20 builds the minimum viable PWA layer.

### T1.89 — Service Worker scaffold (offline 404 + asset cache) | Cx: 14 | P1

**Description:**
Create `frontend/public/sw.js` (vanilla, no Workbox — keep bundle out of main). Cache strategy: cache-first for `/icon-*.png`, `/sounds/*.mp3`, `/og-image.svg`, `/_next/static/css/*`; network-first for HTML; offline-fallback for `/`. Registers via `frontend/src/lib/pwa/register-sw.ts` (env-guarded — only registers in production, NOT in dev to avoid hot-reload poisoning). **Honesty/C4:** if SW breaks Next 15 dev hot-reload, fallback is registration only behind `?sw=1` query for testing. **Confidence:** C3.

**AC:**
- [ ] Failing test written FIRST: register-sw.ts mocked navigator.serviceWorker.register called once in production env, not called in dev env; sw.js exists with cache strategy comments
- [ ] All cases pass
- [ ] Service Worker registers on / in production build; verified via Chrome DevTools Application panel (manual)
- [ ] sw.js <250 lines
- [ ] register-sw.ts <80 lines
- [ ] Dev hot-reload still works after registration logic added (verified by `npm run dev`)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.90 — Offline page (branded fallback) | Cx: 8 | P1

**Description:**
Create `frontend/src/app/offline/page.tsx`. Static, server-rendered branded fallback for when SW catches a network failure. Headline EN: "You're off the grid." ES: "Estás fuera de línea." Sub: "The Wall is back when you reconnect. Carlos's path is still drawn." CTA: "Try again" (window.location.reload). Branded with new tokens. Translation keys `edge.offline.*`. **Why beyond brief:** brief assumes online; demo-day venues frequently have flaky WiFi. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: page renders headline + retry CTA; reload CTA invokes window.location.reload
- [ ] EN + ES copy
- [ ] WCAG AAA contrast
- [ ] reduced-motion safe
- [ ] Page <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.22, T1.33

---

### T1.91 — InstallPrompt component (BeforeInstallPromptEvent) | Cx: 10 | P2

**Description:**
Create `frontend/src/components/wall/InstallPrompt.tsx`. Listens for `beforeinstallprompt` event, dismisses native banner, shows branded inline prompt instead. Trigger location: footer or dismissible toast — NOT modal (intrusive). Persist dismissal in localStorage `gowork.install.dismissed`. Translation keys `pwa.install.*`. **Why beyond brief:** native browser install banner is ugly; branded prompt continues editorial gravity. **Confidence:** C3 (BeforeInstallPromptEvent only Chrome/Edge — Safari iOS uses Add-to-Home-Screen which is OS-level).

**AC:**
- [ ] Failing test written FIRST: dispatch beforeinstallprompt event → component renders; click install CTA → calls saved event.prompt(); dismissal persists to localStorage
- [ ] Cases pass
- [ ] Safari iOS path: component is null (different UX path; brief comment in code)
- [ ] EN + ES copy
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.33

---

### T1.92 — Apple touch icons + splash screen variants | Cx: 6 | P2

**Description:**
Generate `apple-touch-icon-180x180.png` (already from T1.35) PLUS Apple-specific splash screens: `apple-splash-2048x2732.png` (iPad Pro 12.9), `apple-splash-1668x2388.png` (iPad Pro 11), `apple-splash-1290x2796.png` (iPhone Pro Max). Extend `frontend/scripts/generate-icons.mjs` (T1.35) to output these. Add `<link rel="apple-touch-startup-image">` tags in layout.tsx (coordinate with T1.38 budget). **Why beyond brief:** when judges install via Safari iOS, default white screen flash kills the editorial gravity. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: generate-icons script outputs all 3 splash screen PNGs at correct dimensions
- [ ] All splash screen files present in `frontend/public/`
- [ ] layout.tsx contains 3 apple-touch-startup-image link tags (within 130-line budget — coordinate with T1.38)
- [ ] Splash screen background = `--bg-base` (#0A0E1A); branded mark centered
- [ ] Reviewer agent approves

**Depends on:** T1.35, T1.38

---

## Phase 21: Security & Headers (Enrichment Pass)

Mapbox + Three.js + Satori + analytics each broaden the security surface. Without explicit CSP, an XSS vector via translations or user input could exfiltrate Mapbox tokens or session IDs. Phase 21 hardens the perimeter.

### T1.93 — Content Security Policy headers (Mapbox + Three.js + Satori safe) | Cx: 14 | P1

**Description:**
Add CSP via `frontend/next.config.ts` headers() function. Policy:
- `default-src 'self'`
- `script-src 'self' 'wasm-unsafe-eval'` (Three.js needs wasm; Satori needs eval-equivalent — `'wasm-unsafe-eval'` is the modern alternative to `unsafe-eval` for WASM-only)
- `style-src 'self' 'unsafe-inline'` (Tailwind/Lightning CSS injects inline styles)
- `img-src 'self' data: blob: https://*.tiles.mapbox.com https://api.mapbox.com`
- `connect-src 'self' https://api.mapbox.com https://events.mapbox.com`
- `font-src 'self' data:`
- `worker-src 'self' blob:` (Mapbox uses workers)
- `frame-ancestors 'none'`
- `form-action 'self'`
- `base-uri 'self'`
- `report-uri /api/csp-report`. **Honesty/C4:** if CSP breaks Mapbox tile loading, must broaden img-src — verified via `npm run dev` + page load. **Confidence:** C3.

**AC:**
- [ ] Failing test written FIRST: response from `/` includes Content-Security-Policy header with all 11 directives above
- [ ] Mapbox tiles still load with CSP active (manual + Playwright assert no `Refused to load` console error on `/`)
- [ ] Three.js loads (W3 will verify; W1 smoke: import three in a hidden component, verify no CSP block)
- [ ] No `unsafe-eval` outside `wasm-unsafe-eval`
- [ ] CSP report endpoint stub (W4 wires real ingestion)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.94 — Permissions-Policy + HSTS + X-Frame-Options + Referrer-Policy | Cx: 6 | P1

**Description:**
In `next.config.ts` headers(), add:
- `Permissions-Policy: camera=(), microphone=(), geolocation=(self), interest-cohort=()` (deny camera/mic; allow geolocation only first-party for future map "find my location"; deny FLoC/Topics)
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Frame-Options: DENY` (paired with frame-ancestors 'none')
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: response headers include all 5 directives with exact values above
- [ ] All assertions pass
- [ ] Mapbox geolocation API NOT broken when used (W2 will verify; W1 manually checks `navigator.permissions.query({name:'geolocation'})` returns 'granted' or 'prompt' in dev)
- [ ] Reviewer agent approves

**Depends on:** T1.93

---

### T1.95 — Subresource Integrity audit (no external scripts in main bundle) | Cx: 6 | P2

**Description:**
Create `frontend/scripts/audit-sri.mjs`. Greps the built `.next/server` output and `.next/static` for any `<script src="https://...">` referencing third-party origins. Reports findings; exits 1 if any external script lacks `integrity=`. **Goal:** keep main bundle 100% first-party JS — Mapbox is the ONLY exception (loaded via npm, not CDN). **Why beyond brief:** any unaudited third-party script is a supply-chain vector. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: script test fixture with external <script src="cdn.example.com"> (no integrity) → exits 1; clean fixture → exits 0
- [ ] Run against current build: exit 0 (we have no external scripts today)
- [ ] Script <120 lines
- [ ] Added to `npm run` scripts as `"audit:sri"` for periodic runs
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

## Phase 22: Accessibility Beyond AAA (Enrichment Pass)

The brief hits WCAG AAA contrast and reduced-motion, but accessibility has many more axes. Forced-Colors mode (Windows high-contrast users), prefers-contrast: more (low-vision users), Battery API (battery-conscious users), Vibration API (touch feedback for motor-impaired), explicit accessibility statement page. **The Spanish-only screen-reader user from Spotlight Multiple Selves drove this phase.**

### T1.96 — Forced Colors Mode CSS adaptations | Cx: 8 | P0

**Description:**
Add `frontend/src/app/styles/tokens/forced-colors.css` (new partial; @import-wired by T1.8 — coordinate). Block: `@media (forced-colors: active) { :root { --accent-cyan: LinkText; --bg-base: Canvas; --fg-primary: CanvasText; --accent-amber: Mark; --status-negative: Mark; ... } *:focus-visible { outline: 2px solid Highlight; } svg [stroke="currentColor"] { stroke: CanvasText; } }`. Maps brand tokens to system colors so Windows High Contrast Mode renders the Wall as functional, not just legible. **Why beyond brief:** ~3% of users have HCM enabled; they currently see broken token-derived colors. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: vitest+jsdom asserts forced-colors.css contains `@media (forced-colors: active)` block AND maps --accent-cyan to LinkText, --bg-base to Canvas
- [ ] @import added in globals.css (T1.8 list)
- [ ] Manual: Windows + Edge with HCM toggled — every text legible, brand mark visible (not invisible)
- [ ] Partial <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.7, T1.8, T1.10, T1.11

---

### T1.97 — prefers-contrast: more variant tokens | Cx: 6 | P1

**Description:**
Add to `frontend/src/app/styles/tokens/colors.css`: `@media (prefers-contrast: more) { :root { --fg-secondary: var(--fg-primary); --fg-muted: #B0B8C5; /* lifted from #64748B */ --accent-cyan: #5EEEFF; /* brighter */ } }`. Boosts contrast for users who explicitly request it (overlapping but not identical to forced-colors). **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: asserts `@media (prefers-contrast: more)` block exists in colors.css with the 3 token overrides
- [ ] WCAG verified: lifted muted tones still pass AAA contrast (delegate to T1.13 contrast script)
- [ ] No regression on default contrast (default --fg-muted unchanged)
- [ ] colors.css line count <250
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.13

---

### T1.98 — Battery API integration (animations off <20%) | Cx: 10 | P2

**Description:**
Create `frontend/src/hooks/useBatteryAware.ts`. Returns `{ level: number | null, charging: boolean | null, isLow: boolean }` via `navigator.getBattery()` (Chrome/Edge; gracefully nulls on Safari/Firefox). `isLow` true when level <0.2 AND not charging. W2/W3 use this to disable expensive animations (3D barrier graph, cursor flashlight) when user is on low battery. **Why beyond brief:** mobile demo viewer at 18% battery should not have their phone die mid-Wall. **Confidence:** C3 (Battery API is dropping in Firefox; gracefully degrade).

**AC:**
- [ ] Failing test written FIRST: mock getBattery returning {level:0.5, charging:false} → isLow=false; mock {level:0.15, charging:false} → isLow=true; mock {level:0.15, charging:true} → isLow=false; getBattery undefined (Firefox) → level=null, isLow=false
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Cleanup removes battery event listeners on unmount
- [ ] Hook <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.99 — Save-Data + Network-Information aware utility | Cx: 8 | P1

**Description:**
Create `frontend/src/lib/wall/network.ts`. Exports `getNetworkProfile(): { saveData: boolean, effectiveType: '2g' | '3g' | '4g' | 'unknown', downlinkMbps: number | null }`. Reads `navigator.connection` (mostly Chromium; gracefully degrades). Used by W2 to decide between Mapbox vector tiles (4g) vs. raster preview-only (2g/3g/saveData). **Why beyond brief:** brief's mobile fallback used innerWidth only — users on slow rural networks need data-aware fallback regardless of screen size. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: mock navigator.connection {saveData:true, effectiveType:'3g', downlink:1.5} → returns matching object; navigator.connection undefined → returns saveData:false, effectiveType:'unknown', downlinkMbps:null
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Module <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.100 — `/accessibility` statement page | Cx: 10 | P1

**Description:**
Create `frontend/src/app/accessibility/page.tsx`. Editorial accessibility statement: WCAG AAA conformance claim, list of supported assistive tech (NVDA, VoiceOver, JAWS), Forced Colors Mode support, prefers-reduced-motion respect, keyboard navigation summary, contact email `accessibility@gowork.example`, last-audited date (build timestamp). Footer link added in T1.55 list. Translation keys `a11y.statement.*`. **Why beyond brief:** Section 508 + EU EAA expect a published accessibility statement for civic-tech products. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: page renders all 7 sections (WCAG claim, AT list, forced-colors, reduced-motion, keyboard, contact, audit date)
- [ ] EN + ES copy
- [ ] WCAG AAA contrast verified
- [ ] Page <250 lines
- [ ] Link added to Footer (coordinate with T1.55)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.33, T1.55

---

### T1.101 — Vibration API touch-feedback utility | Cx: 6 | P2

**Description:**
Create `frontend/src/lib/wall/haptics.ts`. Exposes `pulse(durationMs: number = 10)`, `tap()`, `confirm()`. Wraps `navigator.vibrate()` (mostly Android; iOS does NOT support web Vibration API as of 2026). Respects user opt-in via localStorage `gowork.haptics` (default `false` — battery-friendly + iOS-honest). Used by W3 chapter transitions for users who opt in. **Why beyond brief:** for users with sensory needs, haptic confirmation of a CTA tap is meaningful; native apps do this — we should match. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: with opt-in true, pulse(20) calls navigator.vibrate(20) once; with opt-in false, no call; navigator.vibrate undefined → no-op without crash
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Module <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

## Phase 23: Typography & Editorial Polish (Enrichment Pass)

Inter Variable's wght axis is in T1.15 — but the optical-size axis goes further (italic, slant, opsz combinations create real editorial typography). Drop caps, pull quotes, chapter dividers as ART (not blank lines), branded scrollbar, hover-on-brand path animation — all the small polish that compounds into "Fortune 500" feel.

### T1.102 — Variable font axis tokens (slant, italic, optical) | Cx: 8 | P1

**Description:**
Append to `frontend/src/app/styles/tokens/typography.css` and `frontend/src/lib/wall/tokens.ts`:
CSS:
```
--font-axis-wght-display: 900;
--font-axis-wght-body: 400;
--font-axis-opsz-display: 32;
--font-axis-opsz-body: 14;
--font-axis-slnt-italic: -10;  /* Inter slant axis */
```
TS export `FONT_AXES = { wghtDisplay: 900, wghtBody: 400, opszDisplay: 32, opszBody: 14, slntItalic: -10 } as const`. Also create utility `.italic-axis` class using `font-style: oblique -10deg;` for Inter Variable's slant axis (NOT the static italic font). **Why beyond brief:** brief mentions opsz only; slant axis enables the "drop cap" + "pull quote" typography in T1.103/T1.104 to render with editorial polish. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: typography.css contains all 5 new tokens; tokens.ts exports FONT_AXES with matching values; .italic-axis class compiles to `font-style: oblique -10deg`
- [ ] All assertions pass
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.15, T1.16

---

### T1.103 — Drop cap CSS utility | Cx: 6 | P1

**Description:**
Add to `typography.css`: `.dropcap::first-letter { float: left; font-size: 5em; line-height: 0.85; padding: 0.05em 0.1em 0 0; font-variation-settings: "wght" 800, "opsz" 60; color: var(--accent-cyan); }`. Used by W2 chapter intros' first paragraph. Also adds `@media print { .dropcap::first-letter { color: black; } }` for print stylesheet (T1.45). **Why beyond brief:** drop caps are a 500-year-old editorial convention; signals "this is a magazine essay, not a webpage." **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: typography.css contains `.dropcap::first-letter` rule with float:left + cyan color + variable font weight
- [ ] Print override present
- [ ] Manual visual check: render a test paragraph with `.dropcap` → first letter is large, cyan, properly aligned (no overlap with second line)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.102

---

### T1.104 — Pull quote component + typography | Cx: 8 | P1

**Description:**
Create `frontend/src/components/wall/PullQuote.tsx`. Renders a `<blockquote>` with editorial typography: italic axis (T1.102), large display weight, cyan rule on left, attribution (`<cite>`) below. Used by W2 chapters for editorial emphasis. Translation keys `wall.pullQuotes.*` (W2 populates content). **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: renders blockquote element with italic-axis class + cyan border-left + cite element when attribution provided
- [ ] WCAG AAA contrast (italic cyan rule on bg-base ≥3:1)
- [ ] reduced-motion safe (no entrance animation by default)
- [ ] Component <80 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.102, T1.10, T1.11

---

### T1.105 — Chapter divider as ART (SVG ornament, not blank line) | Cx: 10 | P1

**Description:**
Create `frontend/public/dividers/chapter-divider.svg`. Hand-tuned ornament: a small horizontal cyan path-line with a center bullet that echoes the brand mark's path. Used between chapters as a visual rhythm marker — NOT a `<hr>`. ALSO create `frontend/src/components/wall/ChapterDivider.tsx` that renders the SVG with `aria-hidden` (decorative). Animates path-draw on intersection-observer (when scrolled into view). reduced-motion: static. **Why beyond brief:** brief says "one chapter ends, next begins" but never specifies the seam. Magazine essays use ornaments. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: SVG file exists with viewBox and path; component renders it with aria-hidden=true; with prefers-reduced-motion, NO animation prop applied
- [ ] All assertions pass
- [ ] svgo idempotent run preserves the file
- [ ] Component <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.5, T1.10, T1.30

---

### T1.106 — Branded custom scrollbar CSS | Cx: 6 | P1

**Description:**
Add to `frontend/src/app/styles/tokens/layout.css` (coordinate with T1.65):
```
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-surface); }
::-webkit-scrollbar-thumb { background: color-mix(in oklch, var(--accent-cyan), var(--bg-elevated) 60%); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
html { scrollbar-color: var(--accent-cyan) var(--bg-surface); scrollbar-width: thin; }  /* Firefox */
```
**Why beyond brief:** default OS scrollbar is the loudest "this is a webpage" signal. Custom scrollbar carries brand into the chrome. **Confidence:** C2 (Webkit + Firefox covered; older browsers fall back gracefully).

**AC:**
- [ ] Failing test written FIRST: layout.css contains all 4 webkit-scrollbar selectors AND `scrollbar-color` for Firefox
- [ ] reduced-motion: no transition on hover (instant color)
- [ ] WCAG: thumb-on-track contrast ≥3:1 (verified via T1.13)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.65

---

### T1.107 — Brand mark hover: animated path-draw | Cx: 8 | P1

**Description:**
Update `frontend/public/icon.svg` (created in T1.34) — wrap the cyan path-line in a `<g class="path-draw">` with `stroke-dasharray` + `stroke-dashoffset` set up for SMIL OR CSS animation on hover. ALSO create CSS in `frontend/src/app/styles/tokens/layout.css`: `.brand-mark:hover svg .path-draw { animation: draw-path 600ms cubic-bezier(0.32, 0.72, 0, 1) both; } @keyframes draw-path { from { stroke-dashoffset: 100; } to { stroke-dashoffset: 0; } }`. Reduced-motion: animation disabled. **Why beyond brief:** brief says "animated path-draw on hover" but provides no implementation; this is the spec. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: icon.svg contains class="path-draw" group with stroke-dasharray attr; layout.css contains .brand-mark:hover rule + @keyframes draw-path
- [ ] reduced-motion override present
- [ ] Manual hover test: hover triggers path-draw 600ms; reduced-motion → no animation
- [ ] svgo idempotent preserves the class attribute
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.34, T1.65

---

## Phase 24: Iconography (Enrichment Pass)

Lucide is the existing icon library; sufficient for utility icons. But the four barrier types (criminal record, transit, childcare, credit) deserve custom icons that signal "we built this for THIS problem" — not "we picked an icon library." Phase 24 builds the four barrier icons + branded button variant tokens.

### T1.108 — Custom barrier-type icons (criminal record, transit, childcare, credit) | Cx: 12 | P1

**Description:**
Create 4 SVGs in `frontend/public/icons/barriers/`:
(a) `criminal-record.svg` — line-art document with a strikethrough redaction line (cyan)
(b) `transit.svg` — abstract bus stop pole + 71-min arc
(c) `childcare.svg` — abstract small + adult silhouette pair
(d) `credit.svg` — abstract three-tier bar with gap (representing score gap)
All hand-tuned 24x24 viewBox, single cyan stroke on transparent, designed at 16px first per brief. ALSO create `frontend/src/components/wall/BarrierIcon.tsx` mapping `BarrierType` enum → icon path. **Why beyond brief:** brief says "Lucide defaults" — defaults are interchangeable; custom barrier icons signal authorship. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: BarrierIcon component renders correct SVG for each of 4 BarrierType values; each SVG file contains <title> matching the barrier name
- [ ] All 4 SVGs exist and pass svgo idempotent run
- [ ] Component <100 lines
- [ ] aria-label set for screen readers (e.g., "Criminal record barrier icon")
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.5, T1.10, T1.11

---

### T1.109 — Branded button variants (CTA primary, ghost, danger, link) | Cx: 10 | P1

**Description:**
Update `frontend/src/components/ui/button.tsx` (existing shadcn — verify path) OR create `frontend/src/components/wall/Button.tsx` if existing component is shadcn-locked. Variants:
- `cta-primary`: bg accent-cyan + fg bg-base, large radius, animated outline-offset on focus
- `ghost`: transparent bg, fg-primary, subtle hover bg-elevated
- `danger`: accent-rose bg, white fg
- `link`: underline only, accent-cyan
All variants respect reduced-motion (transition durations swap to 0). All keyboard reachable, focus visible. Sized via Tailwind classes. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: render each variant; assert distinct className per variant; focus-visible outline matches accent-cyan; reduced-motion disables transitions
- [ ] All 4 variants pass
- [ ] WCAG AAA contrast verified per variant (cta-primary fg on bg, danger fg on bg, etc.)
- [ ] Component <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.11, T1.22

---

## Phase 25: Performance Beyond Lighthouse (Enrichment Pass)

Lighthouse 90+ is the gate, but real performance is about font subsetting, DPR-aware assets, resource hints, brotli, cache headers. Phase 25 puts the infrastructure in place to PASS the gate by margin, not by squeak.

### T1.110 — Font subsetting (Latin EN; Spanish charset overlay) | Cx: 10 | P1

**Description:**
Configure `next/font/google` for Inter Variable in `layout.tsx` (T1.38 owns; coordinate) with `subsets: ['latin']` baseline. For ES locale, lazy-load `latin-ext` subset via dynamic font definition gated by `useLanguage()` (T1.33). Verifies that the EN-only first-paint downloads only the Latin subset (~14KB), and ES toggle adds latin-ext (~6KB) on demand. **Honesty/C4:** Next.js next/font does NOT support runtime subset switching; fallback path is to ship both subsets but use `unicode-range` CSS to load lazily — document the path tried in PR. **Confidence:** C4.

**AC:**
- [ ] Failing test written FIRST: layout-metadata test asserts subsets includes 'latin'; on ES toggle, additional font CSS link element present (or unicode-range rule fires)
- [ ] All assertions pass
- [ ] Network panel: EN-only page loads exactly 1 woff2 (Latin); after ES toggle, additional woff2 loaded
- [ ] No FOIT (flash of invisible text) — `adjustFontFallback: true` from T1.15 covers this
- [ ] Bundle delta: total font weight <25KB across both subsets
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.15, T1.33, T1.38

---

### T1.111 — DPR-aware asset utility (1x/2x/3x) | Cx: 8 | P1

**Description:**
Create `frontend/src/lib/wall/dpr.ts`. Exports `pickDprVariant(srcset: { 1: string; 2: string; 3: string })` and React component `<DprImage src={...} alt={...} />` that picks the right variant based on `window.devicePixelRatio`. Used by W2 for the per-chapter atmosphere images (sky textures, building extrusions). **Why beyond brief:** retina iPhone judges shouldn't see blurry 1x assets; 3GB Android shouldn't download 3x. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: pickDprVariant({1:'a.png',2:'b.png',3:'c.png'}) at devicePixelRatio=1 returns 'a.png'; at 2 returns 'b.png'; at 3 returns 'c.png'; SSR returns '1' fallback
- [ ] DprImage component renders <img src=...> matching variant
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Module <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.112 — Resource hints (preconnect, prefetch, dns-prefetch) | Cx: 6 | P1

**Description:**
Update `layout.tsx` head (coordinate budget with T1.38, T1.85, T1.88, T1.92 — file budget 130 lines): add `<link rel="preconnect" href="https://api.mapbox.com" crossorigin>`, `<link rel="preconnect" href="https://events.mapbox.com" crossorigin>`, `<link rel="dns-prefetch" href="//*.tiles.mapbox.com">`. Saves ~100-300ms on first Mapbox tile request by warming the connection during HTML parse. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: layout-metadata test asserts head contains preconnect for api.mapbox.com and events.mapbox.com, dns-prefetch for *.tiles.mapbox.com
- [ ] All assertions pass
- [ ] layout.tsx still <130 lines (coordinate)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.38

---

### T1.113 — HTTP cache headers per asset type (Vercel headers config) | Cx: 8 | P1

**Description:**
Update `frontend/next.config.ts` headers() to set per-asset-type Cache-Control:
- `/_next/static/*` → `public, max-age=31536000, immutable`
- `/icons/*`, `/sounds/*`, `/dividers/*` → `public, max-age=2592000, stale-while-revalidate=86400` (30d cache, 1d SWR)
- `/og-image.svg`, `/icon.svg` → `public, max-age=3600, stale-while-revalidate=86400` (1h cache, brand updates fast)
- HTML routes → `public, max-age=0, must-revalidate` (always fresh — chapter content may change)
**Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: response headers for `/_next/static/sample.js` include `max-age=31536000, immutable`; `/og-image.svg` includes `max-age=3600`; `/` includes `must-revalidate`
- [ ] All assertions pass via Playwright fetch + header inspection
- [ ] No regression on existing build output
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.114 — Bundle analyzer baseline + thresholds extension | Cx: 8 | P1

**Description:**
Update `frontend/baseline-bundle-sizes.json` _meta to include W1's expected First Load JS deltas: install of mapbox-gl + react-map-gl + three is heavyweight but lazy-loaded so should NOT increase `/` route's bundle. Add a CI-runnable check `frontend/scripts/check-bundle-budget.mjs` that reads route sizes from `.next/build-manifest.json` AND compares against thresholds (10% over baseline → fail). Document W1 baseline pre-Mapbox: `/` route = 161KB. After T1.1+T1.2+T1.3+T1.4 installs, baseline must be re-captured; if deltas >5KB on routes, investigate (likely missing lazy-load). **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: script test fixture with route at 200KB vs baseline 161KB → exits 1 (24% over); fixture at 165KB → exits 0 (within 10%)
- [ ] All cases pass
- [ ] `npm run check:bundle` script added to package.json
- [ ] Re-baseline post-W1: documented in PR; new baseline shows mapbox/three NOT in `/` route's First Load JS
- [ ] Script <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.1, T1.2, T1.3, T1.4

---

## Phase 26: Error Handling & Monitoring (Enrichment Pass)

Per-component error boundaries (richer than the global error.tsx of T1.41), Sentry-style scaffold (own-rolled, no SDK), 404 → relevant suggestions. Phase 26 makes failure dignified.

### T1.115 — Per-section ErrorBoundary component | Cx: 10 | P1

**Description:**
Create `frontend/src/components/wall/SectionErrorBoundary.tsx`. React class-based ErrorBoundary that catches errors in child subtree and renders T1.44's ErrorState component instead of crashing whole page. Logs error to T1.117's reporter. Props: `{ sectionName: string; children: React.ReactNode; fallback?: React.ReactNode }`. Used by W2 to wrap each chapter — one chapter crash should NOT take down the others. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: child throws → ErrorBoundary renders ErrorState with sectionName; reporter mock called once with error and section name; reset path works (clicking retry renders children again)
- [ ] All cases pass
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.44

---

### T1.116 — 404 → chapter suggestions | Cx: 8 | P2

**Description:**
Update `frontend/src/app/not-found.tsx` (T1.40 owns; coordinate). Add a "Maybe you meant…" section listing the 10 chapters as links to `/#chapter-NN`. Suggested in EN+ES via translations. Visual: small grid of chapter titles in tabular-nums + cyan hover. **Why beyond brief:** stock 404s dead-end; ours converts a misroute into a chapter discovery moment. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: not-found page contains 10 chapter suggestion links; each href matches `/#chapter-NN`; EN + ES copy verified
- [ ] All assertions pass
- [ ] WCAG AAA contrast on links
- [ ] Page <120 lines (T1.40 was <100 — extension within budget)
- [ ] Reviewer agent approves

**Depends on:** T1.40, T1.86

---

### T1.117 — Error reporter scaffold (PII-safe, console-only in W1) | Cx: 10 | P1

**Description:**
Create `frontend/src/lib/error-reporter.ts`. Module-level singleton with `report(error: Error, context?: Record<string, string | number>)`. In dev: console.error with full context. In production: posts to `/api/errors/ingest` (W4 endpoint — graceful 404 swallowing). PII filter: scrubs any context value matching email regex, replaces stack-trace path components matching `/Users/[username]` or `C:\\Users\\[username]` with `<USER>`. **Why beyond brief:** brief mentions error pages but never logs errors — without logs, post-demo debugging is blind. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: report(new Error('boom')) in dev calls console.error once; in production posts to /api/errors/ingest; email in context scrubbed to `<EMAIL>`; user-path stack trace scrubbed to `<USER>`; endpoint 404 swallowed
- [ ] All cases pass
- [ ] Module <200 lines
- [ ] SSR-safe
- [ ] Bundle delta <2KB
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6, T1.81

---

## Phase 27: Live / Time-of-Day Precursors (Enrichment Pass)

useTimeOfDay (T1.24) supports 4 phases. The brief's life-layer #1 says "golden 6am, deep navy 11pm" — that implies more granularity. Phase 27 extends to 8 phases + adds weather-awareness scaffold + reading-speed adapter.

### T1.118 — useTimeOfDay 8-phase extension | Cx: 8 | P1

**Description:**
Update `frontend/src/hooks/useTimeOfDay.ts` (T1.24 owns; coordinate as ENHANCE-IN-PLACE, not new file). Phase enum extended from 4 to 8: `'dawn' | 'morning' | 'midday' | 'afternoon' | 'golden' | 'dusk' | 'evening' | 'night'`. Boundaries: dawn 5–7, morning 7–10, midday 10–14, afternoon 14–17, golden 17–18.5, dusk 18.5–20, evening 20–22, night 22–5. Each phase maps to a distinct accentShift + Mapbox sky preset (W2 wires sky). **Backward-compat:** old TimePhase type union now wider; types.ts (T1.67) updated to match. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: at fake-time 6:30 → phase=dawn; 17:30 → phase=golden; 22:30 → phase=night; 11:00 → phase=midday
- [ ] All 8 cases pass
- [ ] Existing useTimeOfDay tests still green (4-phase test cases adapted to 8-phase outputs)
- [ ] Type export TimePhase has all 8 literals
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.24, T1.67

---

### T1.119 — Weather-awareness scaffold hook | Cx: 10 | P2

**Description:**
Create `frontend/src/hooks/useWeather.ts`. Returns `{ cloudCover: number /* 0..1 */, isPrecip: boolean, condition: 'clear' | 'cloudy' | 'rainy' | 'foggy' | 'unknown' }`. Polls `/api/weather` (W4 endpoint with NWS API proxy — for W1, hook returns `{ cloudCover: 0.3, isPrecip: false, condition: 'unknown' }` placeholder + 404 graceful). Used by W2 to dim Mapbox sky on cloudy + raise atmosphere fog. **Why beyond brief:** life-layer #1 is time-aware; weather-aware is the natural fusion (Spotlight). Real Fort Worth weather on the demo screen = "the city is real" signal. **Confidence:** C3 (NWS API integration is W4; W1 stub is safe).

**AC:**
- [ ] Failing test written FIRST: endpoint mock returns {cloudCover:0.8, isPrecip:true, condition:'rainy'} → hook returns matching object; 404 → returns placeholder values
- [ ] All cases pass
- [ ] SSR-safe
- [ ] Polling interval 5 minutes (configurable)
- [ ] Hook <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6

---

### T1.120 — Reading-speed adapter (auto-scroll passive viewing mode) | Cx: 12 | P2

**Description:**
Create `frontend/src/components/wall/AutoScrollMode.tsx`. Toggleable mode (button in header or footer) that auto-scrolls the page at a measured pace (default 60 words/min × per-chapter word count → chapter dwell time). Allows judges to watch the Wall passively without scrolling — useful for "TV-mounted-in-airplane-mode-judge" scenario from Spotlight Multiple Selves. Pause on hover; resume after 3s idle. Accessible: keyboard space-bar pauses/resumes; aria-live announces "Auto-scroll paused / resumed". reduced-motion: disabled (returns null). **Why beyond brief:** brief assumes scrolling; passive mode is the demo-day affordance for non-interactive judging contexts. **Confidence:** C3.

**AC:**
- [ ] Failing test written FIRST: enable auto-scroll → fake timer advance 1s → window.scrollBy called with positive y delta; hover → scrollBy NOT called; spacebar press → toggles paused state; reduced-motion → component renders null
- [ ] All cases pass
- [ ] Component <150 lines
- [ ] aria-live announces toggle state
- [ ] EN + ES copy
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.30, T1.33, T1.27

---

## Phase 28: Real-Data Verification (Enrichment Pass)

Carlos's path uses 5 real Fort Worth offices. Article 55 cites Texas Government Code. HHSC childcare program is named CCS. Trinity Metro GTFS is a real feed. Phase 28 verifies these with primary sources — because if a journalist or judge fact-checks and finds an error, the editorial credibility collapses.

### T1.121 — Carlos's 5-office address verification matrix | Cx: 10 | P1

**Description:**
Create `frontend/src/lib/wall/carlos-path.ts` AND `frontend/src/lib/wall/__tests__/carlos-path.test.ts`. Module exports the 5 office records (T1.67 ChapterId 7 references): Tarrant County District Clerk (100 N Calhoun St, Fort Worth, TX 76196), HHSC office (closest to 76119 — verify), Legal Aid of Northwest Texas (300 S Center St, Arlington TX OR Fort Worth office — verify), Workforce Solutions for Tarrant County on E. Belknap (verify exact address), Amazon FC DFW5 (verify coords). Each record: `{ id, name, address, lat, lng, sourceUrl }`. Test asserts each `sourceUrl` returns 200 (manual one-time verification documented in PR; tests assert structure). **Why beyond brief:** brief lists offices but never sources them. Sourcing makes the work auditable. **Confidence:** C3 (real addresses; geocoding accuracy depends on OSM/Mapbox lookup).

**AC:**
- [ ] Failing test written FIRST: module exports 5 records with id/name/address/lat/lng/sourceUrl; latitudes within Tarrant County bounding box (32.5–33.0 lat, -97.6 to -97.2 lng); each sourceUrl is a real .gov or .org URL
- [ ] All assertions pass
- [ ] PR includes screenshots of each sourceUrl proving address
- [ ] HHSC office geocoded ≤8 mi from 76119 centroid
- [ ] Module <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.67

---

### T1.122 — Article 55 Texas Government Code citation verification | Cx: 6 | P1

**Description:**
Create `frontend/src/lib/wall/legal-citations.ts`. Exports the citation: `{ id: 'tx-art-55', code: 'Texas Government Code, Chapter 55', topic: 'Expunction of Criminal Records', sourceUrl: 'https://statutes.capitol.texas.gov/Docs/GV/htm/GV.55.htm' (verify), summary: '...' }`. **Honesty:** the brief's "Article 55 expunction" is shorthand; verify the actual chapter and section. If the citation is wrong, FIX IT — don't ship a fictional code. **Confidence:** C3.

**AC:**
- [ ] Failing test written FIRST: module exports legal citation with id, code, topic, sourceUrl, summary
- [ ] sourceUrl matches Texas statutes.capitol.texas.gov path (manually verified, screenshot in PR)
- [ ] If brief's "Article 55" is incorrect, document the correction in PR with the actual code reference
- [ ] Module <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.67

---

### T1.123 — Trinity Metro GTFS feed freshness check + HHSC CCS naming | Cx: 8 | P1

**Description:**
Create `frontend/scripts/verify-gtfs-freshness.mjs`. Fetches Trinity Metro GTFS feed URL (https://ridetrinitymetro.org/developer-resources or transitland.org), checks `feed_info.txt` `feed_end_date` is within 60 days of today. ALSO update `frontend/src/lib/wall/carlos-path.ts` (T1.121) to include the HHSC childcare program with the CORRECT program name: **"Child Care Services" (CCS)** — verified via hhsc.texas.gov. The brief's "HHSC childcare subsidy" should be normalized to CCS. **Why beyond brief:** stale GTFS = stale routes = wrong commute estimates. Wrong program name = workers Google for help and find the wrong page. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: script test fixture with feed_end_date 90 days old → exits 1; 30 days old → exits 0
- [ ] Run against real GTFS URL: documented in PR (PASS or descope to manual check)
- [ ] carlos-path.ts records HHSC office with `program: 'Child Care Services (CCS)'`
- [ ] hhsc.texas.gov URL verified live and present in record
- [ ] Script <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.121

---

## Phase 29: Brand Sound + Chapter Navigation + Dev Tooling (Enrichment Pass)

Last polish layer: a single-note brand sound logo (opt-in only), full keyboard-accessible chapter quick-jump, reading-mode toggle, and a unified dev tools surface that compounds T1.76, T1.82, and a memory profiler hook into one developer experience.

### T1.124 — Brand sound logo (subtle audio signature on first interaction) | Cx: 8 | P2

**Description:**
Create `frontend/public/sounds/brand-sound-logo.mp3` (placeholder silent for W1 — replaced post-W1 with real audio asset by composer). Add SoundId `'brand-logo'` to T1.56 sound module. Plays ONCE per session on first user gesture if sound is unmuted. Single soft chime (~400ms, two tones), respectful, NOT a jingle. Persisted via sessionStorage `gowork.brandSoundPlayed`. **Why beyond brief:** brief lists sound as descope candidate (Phase N priority 1), but a single 400ms brand sound on opt-in first interaction = mnemonic without disruption. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: play('brand-logo') called on first user gesture when unmuted; sessionStorage flag set; subsequent gesture does NOT replay
- [ ] All cases pass
- [ ] Placeholder silent file <50KB (within budget)
- [ ] PR includes "REPLACE BEFORE LAUNCH" note for asset swap
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.56, T1.59

---

### T1.125 — Chapter quick-jump menu (1-0 keyboard shortcuts) | Cx: 10 | P1

**Description:**
Create `frontend/src/components/wall/ChapterQuickJump.tsx`. Listens for keyboard `1`–`9` and `0` (chapter 10) keys. On press, `window.scrollTo()` to `#chapter-NN` with `behavior: 'smooth'` (or instant if reduced-motion). Visible affordance: small `?` keyboard-help button in header that opens a modal listing shortcuts. Aria: live region announces "Jumping to Chapter N". **Why beyond brief:** keyboard-only users + power-judges should not need to scroll through 5 minutes of chapters to revisit chapter 8. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: keydown event with key='3' → window.scrollTo called targeting #chapter-03; reduced-motion → behavior: 'auto' instead of 'smooth'; ariaLive announces "Jumping to Chapter 3" (or ES equivalent)
- [ ] All cases pass
- [ ] Modal opens on `?` press; closes on Esc; focus-trapped
- [ ] EN + ES copy
- [ ] Component <150 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.27, T1.30, T1.33, T1.64

---

### T1.126 — Reading mode toggle (text-only, no map) | Cx: 10 | P2

**Description:**
Create `frontend/src/components/wall/ReadingModeToggle.tsx`. Toggle button (header or footer) that swaps the page from full Wall (Mapbox + chapters + 3D) to TEXT-ONLY editorial mode (chapters render as long-form essay, no map, no animations). Persisted in localStorage `gowork.readingMode`. Uses CSS class `.reading-mode` on `<body>` that suppresses Mapbox container, 3D layer, cursor flashlight, sound, etc. **Why beyond brief:** Spotlight Multiple Selves — the slow-3G mobile user in West Texas can't load 5MB of Mapbox tiles; reading mode is the rescue. Also useful for jurors who want to read without scrolling-to-control. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: toggle on → body has `.reading-mode` class; localStorage updated; toggle off → class removed
- [ ] CSS rules in layout.css `.reading-mode .mapbox-container { display: none; }` + similar suppressions
- [ ] aria-live announces "Reading mode: on/off"
- [ ] EN + ES copy
- [ ] Component <120 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.33, T1.64, T1.65

---

### T1.127 — aria-current="step" on chapter "you are here" | Cx: 6 | P1

**Description:**
Update `frontend/src/components/wall/ChapterCounter.tsx` (T1.52 owns; ENHANCE-IN-PLACE) to use `aria-current="step"` on the active chapter indicator. Adds visible "you are here" affordance for screen readers and visual users. ALSO update Header (T1.51) to make `ChapterCounter` itself a live region (`aria-live="polite"`) so chapter changes are announced. **Why beyond brief:** scrolling through 10 chapters with no announcement = screen-reader silence; aria-current is the convention. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: ChapterCounter renders with aria-current="step" on active span; aria-live="polite" wrapper present
- [ ] All assertions pass
- [ ] T1.52's existing tests still green (additive change)
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.52, T1.64

---

### T1.128 — Memory profiler hook (dev-only) | Cx: 8 | P2

**Description:**
Create `frontend/src/hooks/useMemoryProfiler.ts` (dev-only — env-guarded; bundle excluded in production). Wraps `performance.memory` (Chrome only) into a hook returning `{ jsHeapUsedMb, jsHeapLimitMb, percentUsed }`. Updates every 2 seconds. Used by FpsOverlay (T1.82) to display memory alongside FPS. **Why beyond brief:** brief's W4 Lighthouse gate doesn't measure memory; W3's 3D barrier graph could leak across re-renders. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: in dev env, hook returns numeric jsHeapUsedMb when performance.memory available; in production env, hook returns null/0 and is never registered
- [ ] All cases pass
- [ ] Cleanup clears interval on unmount
- [ ] Hook <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.6, T1.73

---

### T1.129 — Unified dev tools surface (`/dev` route hub) | Cx: 8 | P2

**Description:**
Create `frontend/src/app/(dev)/dev/page.tsx`. Dev-only route hub linking to `/tokens` (T1.76), inline FPS overlay (T1.82) toggle, memory profiler stat (T1.128), CSP report viewer (T1.93), bundle size report. Single panel with route links — judges/users never see this in production. **Why beyond brief:** dev tools are scattered (T1.76, T1.82, T1.128, etc.); a single hub is easier to remember. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: in dev env, /dev route renders with links to /tokens + FPS toggle + memory stat; in production, /dev returns 404 (or redirects)
- [ ] All cases pass
- [ ] Route group `(dev)` confirmed working OR env-check fallback documented
- [ ] Page <150 lines
- [ ] No production bundle bloat
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.76, T1.82, T1.128

---

### T1.130 — Cookie/privacy disclosure banner (cookieless analytics — minimal) | Cx: 8 | P1

**Description:**
Create `frontend/src/components/wall/PrivacyDisclosureBanner.tsx`. Tiny inline disclosure (NOT a GDPR-style modal — we use cookieless analytics so consent is not required). Text EN: "GoWork uses cookie-less analytics to understand which chapters readers reach. No personal data leaves your device. Read our privacy notice." with link to /privacy. Dismissible; persists dismissal in sessionStorage. Translation keys `privacy.disclosure.*`. **Why beyond brief:** even cookieless analytics deserves transparency; one-time inline banner respects users without intruding. **Confidence:** C1.

**AC:**
- [ ] Failing test written FIRST: renders banner once; dismissal persists to sessionStorage; second mount → banner null
- [ ] EN + ES copy
- [ ] WCAG AAA contrast
- [ ] Keyboard reachable dismiss
- [ ] reduced-motion safe
- [ ] Component <100 lines
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.10, T1.33

---

## Phase 30: Print Polish + OS-Language Detect (Enrichment Pass)

Last enrichment phase. Print stylesheet from T1.45 covers magazine layout — but drop-cap rendering in print + per-chapter page breaks + Playwright print-preview test were never spec'd. Plus OS-language auto-detect on first visit (delegated from T1.33's "browser default" but never tested as primary intent).

### T1.131 — Print drop-cap + chapter page breaks + Playwright print snapshot | Cx: 12 | P2

**Description:**
Update `frontend/src/app/styles/print.css` (T1.45 owns; ENHANCE-IN-PLACE):
- `.dropcap::first-letter { color: #000 !important; font-size: 4em; }` for print
- `.wall-chapter { page-break-before: always; page-break-inside: avoid; orphans: 3; widows: 3; }`
- `.wall-pull-quote { page-break-inside: avoid; }`
ALSO add `frontend/tests/e2e/visual/print-magazine.spec.ts` Playwright spec that emulates print media on `/`, takes a screenshot, verifies it does not contain the Mapbox container, the header is hidden, the body uses serif. Snapshot diff against a baseline saved in repo. **Why beyond brief:** brief mentions "9-page magazine essay" but never tests it. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: print.css contains all 3 new rules; Playwright spec asserts header hidden + body serif + no .mapbox-container element
- [ ] Both tests pass
- [ ] T1.45's existing tests still green
- [ ] PR includes a print-preview screenshot from real Chrome print dialog as evidence
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.45, T1.103, T1.104

---

### T1.132 — OS-language auto-detect on first visit + lang attribute sync | Cx: 6 | P1

**Description:**
Update `frontend/src/hooks/useLanguage.ts` (T1.33 owns; ENHANCE-IN-PLACE — no new file). Strengthen the navigator.language detection: if `navigator.languages` array is available, prefer first es-* match if any (more accurate than just primary). ALSO ensure on locale change, `<html lang="...">` attribute updates dynamically (currently set once in layout.tsx). Use a useEffect that calls `document.documentElement.lang = locale === 'es' ? 'es-MX' : 'en-US'`. Critical for screen readers — wrong html lang attribute = wrong pronunciation. **Confidence:** C2.

**AC:**
- [ ] Failing test written FIRST: navigator.languages = ['es-MX', 'en-US'] → useLanguage returns 'es' on first mount; setLocale('en') → document.documentElement.lang === 'en-US'; setLocale('es') → 'es-MX'
- [ ] All cases pass
- [ ] T1.33's existing tests still green
- [ ] SSR-safe
- [ ] No regression on localStorage persistence
- [ ] `bpsai-pair arch check` passes
- [ ] Reviewer agent approves

**Depends on:** T1.33

---

## Spotlight Inventions Summary

### Invention 1 — `usePerformanceBudget` hook (T1.73)
**Why:** Brief sets W4's Lighthouse 90+ gate but provides no in-build telemetry. This hook is the early-warning canary across W2/W3 so we don't discover regression at the gate.
**Tasks:** T1.73
**Confidence:** C2

### Invention 2 — Mapbox-token-missing branded fallback (T1.74)
**Why:** Brief says "fall back to static" but doesn't design the fallback. First-impression rescue when judges clone without env setup.
**Tasks:** T1.74
**Confidence:** C2

### Invention 3 — `useDeviceCapability` hook (T1.75)
**Why:** Brief's mobile fallback uses only window.innerWidth — misses low-end Android RAM/CPU constraints that would crash Three.js. This hook tiers devices for W3 graceful degradation.
**Tasks:** T1.75
**Confidence:** C2

### Invention 4 — Token gallery dev route (T1.76)
**Why:** Brief defers Storybook as P2. A dev-only `/tokens` page is 10x cheaper and serves the same review purpose for Shawn + Ren before W2 builds on tokens.
**Tasks:** T1.76
**Confidence:** C2

### Invention 5 — Legacy M-shape retirement audit (T1.77)
**Why:** Brief mentions explicitly retiring the M-shape but provides no audit. Silent retirements become forgotten ghosts. This script + state.md note is the receipt.
**Tasks:** T1.77
**Confidence:** C1

---

## Honest Uncertainty (located ignorance)

- **C4 — `next/font` Inter Variable optical-size axis (T1.15):** Next.js 15 + `next/font/google` may not yet expose the `axes` parameter in stable form. If `axes: ['opsz']` causes a build failure, the fallback is the variable weight axis only, deferring optical-size to a self-hosted Inter Variable from `fontsource`. Confidence raised by: trying it in T1.15, and if it fails, splitting into a sub-task to switch to `@fontsource-variable/inter`.
- **C4 — Lightning CSS @import ordering (T1.8):** Next 15 uses Lightning CSS by default; `@import` inside non-CSS-Module entry sometimes hoists or warns. If T1.8 fails build, fallback is to inline the partials at build time via PostCSS `postcss-import` (must add devDep). Raised by: testing locally before committing.
- **C4 — `color-mix()` browser support (T1.11, T1.12, T1.65):** Safari 16.4+, Chrome 111+, Firefox 113+. We target evergreen. If a judge uses a 2-year-old Safari, the `@supports not (color: color-mix(...))` fallback hex must be present. Raised by: T1.11's `@supports not` block being mandatory AC.
- **C4 — `@vercel/og` runtime in Next 15 App Router (T1.3):** The package is install-only in W1; the actual route handler is W4. Pinning version compatible with Next 15 App Router (Edge runtime) requires verification at install time. Raised by: T1.3's `npm run build` AC.
- **C5 — Token gallery route (T1.76) bundle isolation:** Marking a route "dev-only" in Next.js App Router is non-trivial. Cleanest path is a `(dev)` route group + middleware NextResponse.rewrite to /404 in production. If middleware approach fails, fallback is environment variable check inside the page component (less clean but works). Raised by: trying middleware first, falling back to env-check.
- **C3 — Mapbox token + Mapbox style URL (T1.1, T1.6):** The brief assumes Shawn registers a Mapbox account and creates a custom dark style. T1.6 only validates the token format; W2 will fail loudly at runtime if the style URL is unset. Raised by: documenting the required env vars in `.env.local.example` (T1.1) and adding a separate W2 task for style URL validation.
- **C2 — Spanish translation tone (T1.48 and beyond):** AI-translated Spanish ("El Muro" for "The Wall") may read clinically. Brief says "no Google translate". For W1's edge-state and title sequence keys, AI-translation is acceptable as placeholder — W4's Spanish parity sweep will engage a fluent reviewer. Flagged in T1.48 PR as "AI-translated, awaiting W4 review".
- **C3 — Howler.js on Safari iOS audio context unlock (T1.58):** iOS Safari requires user gesture to start AudioContext, sometimes also requires touchstart specifically (not just pointerdown). T1.58 listens for both pointerdown and keydown — adds touchstart as third listener if iOS Safari is detected via `useDeviceCapability` (T1.75). Raised by: testing on iOS device in W2.

---

## Wave Schedule (engage will compute from `Depends on:` graph)

**Wave 1 (no deps):** T1.1, T1.7
**Wave 2 (depends on Wave 1):** T1.2 → T1.3 → T1.4 → T1.5 (sequential infra installs); T1.8 → T1.9 (CSS architecture imports + smoke); T1.6 (depends on T1.1)
**Wave 3 (tokens + hooks, depends on T1.7/T1.8/T1.6):** T1.10–T1.13 (color), T1.15–T1.17 (typography), T1.19–T1.23 (motion), T1.24–T1.33 (10 hooks), T1.67 (types)
**Wave 4 (depends on tokens+hooks):** T1.34 (brand mark), T1.35–T1.38 (assets+layout), T1.40–T1.44 (edge states), T1.45 (print + smoke), T1.47–T1.48 (title sequence), T1.50–T1.55 (header+footer subcomponents+rewrites), T1.56–T1.57 (audio), T1.60–T1.61 (cursor), T1.63–T1.65 (a11y), T1.68 (hub+barrel), T1.73–T1.77 (Spotlight)
**Wave 5 (final verification):** T1.70 (arch sweep), T1.72 (vitest green)

Engage `--max-parallel` recommendation: 4 (4 driver agents working in parallel within waves; serialize across waves).

---

## KANSEI dispatch directive for W1

Every task in W1 dispatched with full KANSEI 8-section dispatch:
- IDENTITY: "Driver agent — frontend foundation specialist"
- INTENT + WHY: "Build the foundation tokens/hooks/edge-states for The Wall. Without coherent foundations, every later sprint paints over inconsistent work and judges see the seams. The Wall is the home page; the foundation IS the product."
- SCOPE: file paths from this backlog with line counts where files exist
- AC: lifted from each task's AC checkboxes (every box specific, no template fillers)
- CONSTRAINTS: 13 permanent constraints (top of file)
- NEGATIVE: "DO NOT skip the globals.css split. DO NOT add hex colors outside `--accent-*` token definitions. DO NOT bypass prefers-reduced-motion. DO NOT introduce new motion library (use existing framer-motion). DO NOT silently retire the legacy M-shape — use T1.77's audit script. DO NOT translate Spanish via raw machine output without flagging in PR for W4 review."
- TEST PATTERNS: existing vitest patterns in `frontend/src/__tests__/` and component-test directories; existing Playwright in `frontend/tests/e2e/`
- DEPENDENCY GRAPH: each task's `Depends on:` line; engage computes waves

---

慣性の契約. The dispatch is a contract. Both sides deliver. Sprint W1 is the ground floor — every weight above it pivots on whether this floor is level.
