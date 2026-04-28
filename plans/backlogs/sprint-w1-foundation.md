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
| Total tasks | 68 |
| P0 / P1 / P2 | 51 / 14 / 3 |
| Total Cx | 582 |
| Wave count | 5 |
| Critical path | Infra install → CSS arch split → tokens (color/type/motion) → hooks/brand/edges/header parallel → wiring/types/tests |
| Spotlight inventions | 5 (added beyond the brief) |
| Architecture compliance | every code task includes `bpsai-pair arch check passes` AC |
| TDD compliance | every code task lists failing-test-first AC |
| Engage dry-run | passes (68 tasks parsed) |

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
