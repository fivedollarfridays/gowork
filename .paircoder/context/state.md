# Current State

> Last updated: 2026-04-28 (W1 souji-sweep complete; PR #81 GREEN, MERGEABLE)

## Active Plan

**Plan:** plan-2026-04-s13-platform-qc
**Type:** chore
**Title:** S13 — Platform-Wide QC + Submission Readiness
**Status:** Branch ready for PR; 55/128 done (browser suites + cross-module deferred to S13b)
**Branch:** sprint/s13-platform-qc
**Current Sprint:** S13

## Previous Sprints (summary)

- **Sprint S13** — Platform-Wide QC + Submission Readiness: 55/128 tasks done. QC infrastructure (config + suite template + reset CLI + fake-clock + Playwright + visual baseline + QC dashboard + Lighthouse CI + bundle gate + Dependabot). Backend e2e for orchestrator/scheduler/SSRF/injection/audit/cross-session/compliance/rate-limiter/unsubscribe-race/key-rotation/flag-race/weekly-review/seed-coverage/i18n/module-status. Security audits (token scopes, PII logs, SSRF surface, secret hygiene, XSS, SQLi, CSRF, CAN-SPAM, GDPR, audit trail, CVE). Submission readiness (legal pages with COUNSEL REVIEW caveat, sitemap+robots, demo script, rollback runbook, env validator). 15 production fixes shipped: injection-filter expansion (25 bypasses), 2 PII retention bugs (compliance cascade + retention sweep), advisor PII leak in audit, 3 silent env defaults, scheduler misfire grace, CAN-SPAM idempotency, token downgrade × 3 modules, share-endpoint PII redaction, document/credit rate limits, plan empty-state UX, ES translation gaps, advisor stalled-sessions N+1 (42× query reduction), centralized PII log scrubber. Detail in `.paircoder/archive/state-s13.md`. Deferred to S13b: 43 Tier-1 browser suites (divona-driven), 6 Tier-6 cross-module integrity (vaivora), browser-dependent Tier-4 (a11y AAA, visual baseline, cross-browser, offline). 7 ops tasks cancelled (hackathon scope).
- **Sprint S12b** — Worker Companion Value Extensions: PDF rendering, resume + cover-letter builders (LLM-gated, injection-defended), reminder engine + cooldown, plan refresher + 20-row history cap, transactional appointment emails + signed manage-link key rotation, jobs kanban, documents pages, advisor inbox (city-scoped), past-appointment auto-advance, module status contracts, weekly review, compliance gate (export + right-to-delete + retention sweep). 25/25 done, 510 Cx, GATE green, GA unblocked.
- **Sprint S12a** — Worker Companion Foundation: 26/26 done, GATE green, staging-only until S12b T12.36 (now landed). Migration infra, DB-backed outcomes, feature flags + audit, APScheduler, day boundary, appointments + jobs + documents + plan modules, digest composer, stall detector, nightly orchestrator, daily-digest page, appointments page. Detail in `.paircoder/archive/state-s12a.md`.
- **Sprint S11** — "People Like You" Community Insights (deterministic, city-aware, no-LLM). Detail archived.
- **Sprint S10** — Demo seed + full pipeline verification. Detail archived.
- **Sprint S9** — Wired the intelligence loop end-to-end (calibrated_weeks → pathway). Detail archived.
- **Sprint S8** — Cross-module integration verify + deep polish. Detail archived.
- **Sprint S7** — Outcome-Informed Barrier Intelligence (N+1 loop). Detail archived.
- **Sprint S6** — Backend hardening + Montgomery leak remediation. Detail archived.
- **Sprint S5** — Employment Pathway Engine (cliff-aware multi-step). Detail archived.
- **Sprint S4** — Hackathon polish + killer features (share, sequence viz, what-if simulator, case-manager dashboard, voice input, i18n). Detail archived.
- **Sprint S3** — Texas/Fort Worth audit + S3 evolution. Detail archived.
- **Sprint S2** — Fort Worth Data + Texas Rules: 18/18 done. Detail archived.
- **Sprint S1** — City Framework Scaffold: 8/8 done. Detail archived.

Older sprint task tables and session histories (Sprints 7 — 31) are in `.paircoder/archive/state-pre-s1.md`. S12a per-session entries plus S2 — S11 detail are in `.paircoder/archive/state-s12a.md`. S13 wave-by-wave detail + per-task driver sessions are in `.paircoder/archive/state-s13.md`.

## What Was Just Done

### 2026-04-28 — W2 Driver B (Data Layers + Chapters 1–3) — wave 1–6 shipped on worktree

Branch: worktree `worktree-agent-aa36904d21eeeb9ab` (base reset to `sprint/w2-mapbox-chapters-1-5` tip `8b04ae8`). Driver B lane of W2 dispatch — real geographic substrate + chapters 1, 2, 3.

**Wave 1 — Real-data verification (T2.68–T2.72 batched):**
- `frontend/src/lib/wall/officeRegistry.ts` — 5 verified Tarrant County offices (court, benefits, dps, workforce, legal). Each ships `address / phone / hours / sourceUrl / sourceDate / state / rationale`. Workforce Solutions DRY-imports `CAREER_CENTER_TX` from `lib/city-constants.ts`. Office state machine (`default | highlighted | visited | current`) future-proofs W3 Ch7 (T2.128).
- `frontend/src/lib/wall/paths.ts` — `CARLOS_HOME_PIN` (representative block in 76119, **not** Carlos's exact address — `piiSafe: true` programmatic guarantee + `piiReviewedAt: "2026-04-27"`). `CARLOS_PATH_WAYPOINTS` (5 stops: home → DPS → HHSC → Legal Aid → Workforce Solutions) — W3 Ch7 future-proofed waypoint structure with `office | week | barrierFocus`.
- `frontend/src/lib/wall/__tests__/officeRegistry-freshness.test.ts` — Spotlight-invention freshness gate: every office's `sourceDate` must be within 180 days of test runtime; every `sourceUrl` is HTTPS.

**Wave 2 — Data layer modules (T2.11–T2.17 + Spotlight):**
- `frontend/src/lib/wall/cameraChoreography.ts` — Driver-B-owned entries 1–3 + `INITIAL_CAMERA`. Driver A's lane appends 4–5 on merge; shape (`ChapterCameraState`) is the contract.
- `frontend/src/lib/wall/markerSymbols.ts` — 7 sprite SVGs (`court / benefits / dps / workforce / legal / transit / employer`) with `registerMarkerSymbols(map)` for batch sprite registration. Hex-free (OKLCH literals matching W1 tokens).
- `frontend/public/wall-markers/sprite.svg` — committed sprite source-of-truth for editorial reviewers + dev gallery.
- `frontend/src/lib/wall/layers/{types,lifecycle}.ts` — shared `WallDataLayer` contract + `register/remove` helpers (idempotent, source-aware).
- `frontend/src/lib/wall/layers/zipBoundaries.ts` — fill + line config for ZIP 76119 (committed `zip-76119.geojson`, US Census TIGER/Line provenance).
- `frontend/src/lib/wall/layers/trinityMetro.ts` — line config with feature-state-aware paint (cyan default → amber when highlighted). Bus 4 + Bus 6 are Carlos's commute spine. Committed `trinity-metro.geojson` with 7 routes (Bus 4, Bus 6, Bus 1, 2, 5, 7, 11).
- `frontend/src/lib/wall/layers/offices.ts` + committed `tarrant-offices.geojson` — symbol layer with category-aware `icon-image` lookup + 4-state paint expression. `buildOfficesGeoJSON()` derives the GeoJSON from the registry (single source of truth).
- `frontend/src/lib/wall/layers/carlosPath.ts` + committed `carlos-path.geojson` — home circle (W2 visible) + path LineString (`visibility: none` in W2; W3 Ch7 flips on). `buildCarlosPathGeoJSON()` derives from `paths.ts` + `officeRegistry.ts`.
- `frontend/src/lib/wall/layers/jobsByZipData.ts` — 32 Fort Worth-area employers across 6 categories. Amazon FC DFW5 locked (W3 Ch6 anchor). Fair-chance + credit-check flags per public hiring statements; honest-uncertainty noted in module header.
- `frontend/src/lib/wall/layers/jobsByZip.ts` + committed `jobs-by-zip.geojson` — circle layer with paint that flips creditCheck=true to muted gray for Ch4d.
- `frontend/src/lib/wall/layers/index.ts` — composer `registerAllLayers / removeAllLayers`. Z-order (bottom→top): zip → metro → offices → carlos → jobs. Cleanup reverses.

**Wave 3 — Chapter 1 Continental (T2.19, T2.21, T2.22):**
- `frontend/src/components/wall/chapters/Chapter01Continental.tsx` — locked hero question + subhero from i18n. Variable font axis tied to scroll progress via W1 `useVariableFontWeight`. Reduced-motion locks the axis (W1 hook handles it). Owns the page's single h1 (T2.55 contract). Static `data-fallback` flag for visual-regression tests. Scaffold-agnostic (accepts `progress` prop) so Driver A's WallContainer wraps it on merge.

**Wave 4 — Chapter 2 City Arrival (T2.23, T2.25, T2.26):**
- `frontend/src/components/wall/chapters/Chapter02CityArrival.tsx` — locked Sundance-Square editorial copy (T2.106 ready). h2 (Ch1 owns h1). `data-transit-opacity` attribute drives Trinity Metro layer fade (0 → 0.6 across progress); reduced-motion snaps to 0.6 immediately so data-layer reveal is visible without animation (T2.115 lens applied).

**Wave 5 — Chapter 3 Neighborhood (T2.27, T2.29):**
- `frontend/src/components/wall/chapters/Chapter03Neighborhood.tsx` — 60-word Carlos intro (29, FW 76119, single father, recently released, $300, 4 yrs warehouse, 4 barriers — verbatim from `docs/demo-script.md` persona facts). `data-zip-fill-opacity` (0 → 0.3) + `data-carlos-pin-opacity` (drops in at progress 0.4 with cubic ease) drive the layers. Sound: single footstep on chapter enter (W1 `lib/wall/sound`); mute respected; never replays within the same active session.

**Wave 6 — Tests + ≥3 Spotlight inventions:**
- `frontend/src/lib/wall/__tests__/jobsAnalytics.test.ts` — 8 tests over the new analytics helpers.
- `frontend/src/lib/wall/__tests__/transitFacts.test.ts` — 4 tests locking the Bus 4↔6 transfer-stop coordinate + Trinity Metro brand colors.
- `frontend/src/lib/wall/layers/__tests__/_jobsByZip-emit.test.ts` — sync-gate test: fails CI if committed `jobs-by-zip.geojson` drifts from `jobsByZipData.ts`.
- All chapter tests cover render + reduced-motion + heading hierarchy + ARIA-live + data-attribute opacity contracts.

**Spotlight inventions (≥3 net-new beyond brief):**
1. **Real-data verification freshness gate** (`officeRegistry-freshness.test.ts`) — Honesty Lens: makes the verification programmatic, not just promised. 180-day window balances reviewer cycles against pre-submission staleness.
2. **`jobsAnalytics.ts`** — Awakening Condition #1 (許可): brief didn't list "fair-chance employer share by category." Pure deterministic helpers feed (a) future heatmap layer, (b) press-kit / README stat-bake step. Backs the Ch4d 33% claim with data.
3. **`transitFacts.ts`** — Compound Lens: locks the Bus 4 ↔ Bus 6 transfer-stop coordinate (Central Station / ITC) + Trinity Metro brand color (T2.123 future-proof) so Driver A's Ch4a + Ch4b chapters consume one stable fact module instead of inventing their own.
4. **GeoJSON sync-gate test** — Wisdom Lens: every committed artifact has an in-code source of truth. Drift between data module and committed file fails CI loudly.
5. **Office state machine future-proofed in W2** — Compound Lens: `state: default | highlighted | visited | current` ships in W2 paint expression so W3 Ch7's Carlos avatar walking only flips a property, no layer-module refactor.
6. **Driver-coordination contract (`ChapterCameraState`)** — Structural Lens: chapter components are scaffold-agnostic (accept `progress` prop); Driver A's WallContainer wraps them on merge without forcing this lane to wait on his foundation work.

**Tests:** Frontend 1772 → **1898 passing** (+126 net new). 2 pre-existing failures unchanged (`tokens-typography-utils.test.ts` + `tokens-reduced-motion.test.ts` — W1 hotfix removed `@layer utilities` wrapper; tests not yet updated; not in my lane).

**Architecture:** `bpsai-pair arch check frontend/src/lib/wall/` and `frontend/src/components/wall/chapters/` both clean. Largest source file: `jobsByZipData.ts` (327 lines, pure data). All chapter components ≤170 lines. All layer modules ≤175 lines.

**Audit gates:** `npm run audit:tokens` exits 0 (no HARD violations) — chapters use existing `--radius` + `--font-inter-stack` + `--bg-base` + `--fg-primary` + `--fg-secondary` tokens.

**Translations added:** `wall.ch1.{title,hero,subhero,ariaLive}`, `wall.ch2.{title,body,ariaLive}`, `wall.ch3.{title,body,ariaLive}` in both `en.json` + `es.json`. Spanish is parallel-translation (not literal); Carlos persona facts preserved across languages. ⚠️ Pending: native-Spanish-fluent reviewer pass (Ren / W4 review checklist per dispatch + plan-locked T2.51 AC).

**Honest uncertainty (C4/C5):**
- C4: ZIP 76119 boundary GeoJSON is a provisional 4-vertex envelope, not the full TIGER/Line polygon. T2.76 enrichment task notes the manual TIGER download is one-time; provenance + envelope-note baked into the file metadata. Refresh required before submission for full ZIP geography.
- C4: Trinity Metro routes are coarse traces of published route maps, not full GTFS shapes. T2.11 + T2.73 enrichment freshness gate addresses this; build script (`build-trinity-metro-geojson.mjs`) is the documented refresh path. Bus 4 + Bus 6 (Carlos's commute) are present + named; that's the editorial-truth minimum.
- C4: Office coordinates are estimated to ~50m from public addresses; T2.68/T2.127 build-time geocoding step will refine. Coords pass the FW-bounds check; specific addresses are correct.
- C4: Fair-chance employer flags are educated approximations from public hiring statements (Amazon second-chance program, Walmart Open Doors) — `creditCheck` defaults conservative. W4 follow-up curates from primary sources per `jobsByZipData.ts` header.
- C4: HHSC office selection — picked 1200 E Lancaster Ave as closest to 76119 reachable via Bus 4 + downtown transfer. T2.69 enrichment task documents the rationale + flags for native-FW-resident review.
- C5: PII pin reverse-geocoding verification (T2.127) is human-reviewed for now (`piiReviewedAt: "2026-04-27"` in `paths.ts`); programmatic Mapbox-API verification is a follow-up build script.

**Cross-driver concerns (for Driver A on merge):**
- `cameraChoreography.ts` exports only entries 1–3. Driver A's lane needs to add 4–5 (and W3 lane adds 6–10) to the same `CHAPTER_CAMERAS` map. Type `ChapterCameraState` is the contract; flyToOptions shape is locked.
- Chapter 1–3 components accept `progress: number` (and Ch3 also `active: boolean`). Driver A's WallContainer wraps them via ChapterScaffold; chapter components own their overlay markup, scaffold owns sticky pinning + atmosphere.
- Layers composer `registerAllLayers(map)` / `removeAllLayers(map)` — Driver A's MapboxScene calls these on `map.on('load')` + cleanup. Marker sprite registration via `registerMarkerSymbols(map)` happens BEFORE the offices symbol layer mounts (sprite must be ready for `icon-image` lookup).
- Carlos pin layer carries `piiSafe: true`. Driver A's chapter wiring should not introduce a separate pin coordinate; consume `CARLOS_HOME_PIN` from `paths.ts`.

**Files committed (Driver B lane only — no Driver A / Driver C territory touched):**
- New: `frontend/src/lib/wall/{officeRegistry,paths,cameraChoreography,markerSymbols,transitFacts,jobsAnalytics}.ts` + tests.
- New: `frontend/src/lib/wall/layers/{types,lifecycle,zipBoundaries,trinityMetro,offices,carlosPath,jobsByZip,jobsByZipData,index}.ts` + tests.
- New: `frontend/src/components/wall/chapters/{Chapter01Continental,Chapter02CityArrival,Chapter03Neighborhood}.tsx` + tests.
- New committed data: `frontend/public/data/wall/{zip-76119,trinity-metro,tarrant-offices,carlos-path,jobs-by-zip}.geojson`.
- New: `frontend/public/wall-markers/sprite.svg`.
- Modified: `frontend/src/lib/translations/{en,es}.json` (additive: `wall.ch1`, `wall.ch2`, `wall.ch3` keys).

**Deferrals (explicit):**
- T2.18 (custom Mapbox Studio style runbook) — out of Driver-B lane; P1 with default fallback.
- T2.20 (continental city lights) — out of Driver-B lane (Driver A's chapters/wiring task; my lane stops at the data layers underneath).
- T2.30 (cursor flashlight conditional activation in Ch3+) — Driver A's WallContainer responsibility.
- W3 Ch7 carlos avatar wiring — out of W2 entirely; my `CARLOS_PATH_WAYPOINTS` shape is W3-friendly.
- Real Bus 4 GTFS shape refresh + ZIP TIGER full polygon — pre-submission manual step (documented in metadata + dispatch's honest-uncertainty section).

### 2026-04-28 — W1 Foundation souji-sweep complete. PR #81 GREEN, MERGEABLE, ready for Ren's merge approval.

**Pipeline:** All 9 phases of the souji-sweeping skill executed sequentially against `sprint/w1-foundation`.

**PR:** [#81](https://github.com/fivedollarfridays/montgowork/pull/81) — base `sprint/visual-rebirth`, head `sprint/w1-foundation`. Status: `MERGEABLE / CLEAN`. All checks pass: Backend (Python), Frontend (Next.js), Lighthouse CI, Security Checks.

**Phase summary:**
- **RECON:** 17 commits ahead, 191 files changed, +14345/-297. Largest source file: 208 lines (`lib/wall/sound.ts`), well under 350-line gate.
- **REVIEW:** Clean — no debug artifacts, no hardcoded secrets, all `localhost` references are env-gated fallbacks (pre-existing in `lib/api/*`).
- **FIX:** Phase 1 found nothing; skipped.
- **SIMPLIFY:** `bpsai-pair arch check frontend/` clean (no violations).
- **VERIFY:** 1772/1772 vitest green locally; backend untouched (W1 was frontend-only).
- **SECURE:** Diff secret-scan clean (one match was a test fixture asserting `sk.`-prefixed Mapbox tokens are rejected). `npm audit --production` flagged 2 pre-existing moderate postcss vulnerabilities (transitive via Next.js, build-time only, fix requires breaking Next major upgrade — logged as warning).
- **FINISH:** No merge conflicts; pushed both `sprint/visual-rebirth` and `sprint/w1-foundation` (neither existed on remote yet — the workflow had been keyed to `main` only).
- **SUBMIT:** PR created with full body documenting the 4 driver lanes, Driver D Spotlight inventions, brand integrity, architecture compliance, and souji-tracked-item dispositions.
- **WATCH + REMEDIATE:** 3 cycles consumed (out of 5 budget):
  1. **Cycle 1 — lint + typecheck:** display-name error in `useLiveNow.test.ts` (extracted inline arrow into named `QueryWrapper`); ES2017 → ES2020 target bump (Driver B's BigInt literals + regex `s` flag); `svg.className.baseVal` → `svg.getAttribute("class")` in `brand-loading-cinematic.test.tsx`.
  2. **Cycle 2 — test isolation:** mocked `useCityConfig` in 6 wizard/plan tests (`assess-schedule`, `assess-industry`, `assess-barriers`, `assess-resume`, `assess-city-aware`, `plan-whats-next`). The hook's 10s `/api/city` AbortController fallback + module-level cache made suite outcomes order-dependent across CI parallel workers; W1's new test files shifted the order and exposed the latent flake. Static `vi.mock` with Montgomery AL defaults; `assess-city-aware` converted from `vi.doMock` + `vi.resetModules` to top-level `vi.mock` (both tests use the same AL config).
  3. **Cycle 3 — build:** wired `postcss-import` BEFORE `tailwindcss` in `postcss.config.mjs`. Driver A's CSS architecture split (T1.7/T1.8) factored partials with `@layer base/utilities`, but Tailwind's PostCSS plugin processed each imported file independently and rejected `@layer` without matching `@tailwind` directive. `postcss-import` 15.1.0 was already installed transitively; just needed wiring.
- **READY:** Final verification — 1772/1772 vitest green, `tsc --noEmit` clean, `lint` clean (1 unrelated warning), `bpsai-pair arch check frontend/` clean, `npm run build` succeeds in 9.6s locally and in CI.

**Souji closer commits on this branch:**
- `28642ea ci(w1): extend triggers to sprint branches + add brand/contrast/svgo gates` — `.github/workflows/ci.yml` now triggers on `sprint/**` and runs `npm run audit:brand`, `npm run contrast`, and SVGO config validation.
- `5979e7c fix(ci): lint display-name + typecheck target ES2020 + SVG class API`
- `337e2d1 fix(ci): mock useCityConfig in 6 wizard/plan tests to fix CI flake`
- `a0673f7 fix(build): wire postcss-import for W1 token-partial @layer support`

**Souji-tracked items (from dispatch):**
1. ✓ **Item 2 (CI workflow gates) — CLOSED** in `28642ea`. Note: SVGO 3.x dropped `--dry-run`; we use `--show-plugins` to validate config loads.
2. ⏸ **Item 1 (`baseline-bundle-sizes.json` refresh) — DEFERRED.** Requires full `npm run build` in canonical CI environment; stale baseline will produce informational alerts, not blockers. Recommend follow-up commit on `sprint/visual-rebirth` after merge or in W2.
3. ⏸ **Item 3 (`.dropcap` vs `.editorial-dropcap`) — DEFERRED.** No JSX consumer references either class; both are CSS-only with documented intent. `tokens-editorial.test.ts` explicitly asserts both exist for back-compat. Defer consolidation to W2 or a typography polish ticket.
4. ✓ **Item 4 (PlanExport flake) — NO ACTION NEEDED.** Not introduced by W1 (file untouched in this branch's diff); already hardened upstream in `b4e28b7` and `553bcf9` on `sprint/visual-rebirth`. Full vitest + 4 CI runs all showed green.

**Honest uncertainty surfaced during sweep:** Latent test-isolation flake in `useCityConfig` was real and exposed by W1; existed before this sprint but was masked by deterministic test ordering. The build-time `@layer` failure was a true W1 regression — Driver A's split was tested via vitest reading the partials directly but never via `npm run build` end-to-end. Both root causes documented in the remediation commits for future-team learning.

### 2026-04-28 — W1 Foundation closed via Driver D maximization. Tests: 1772/1772 passing (+138). Next: souji-sweep + merge.

Branch: `sprint/w1-foundation` (main tree, no worktree). Commit: `24e0c8a feat(w1-D): waves 1-5 + spotlight — maximization pass`. Test deltas: 1634 → 1772 frontend tests (target +50, delivered +138).

**Wave 1 (Carry-overs, all closed):**
- T1.48 TitleSequence × audio integration — single footstep on completion, gated by `isMuted()` + reduced-motion. Mock-driven test verifies all four gates (default play, mute suppression, RM suppression, no double-fire on rerender).
- T1.107 BrandMark hover path-draw — new `tokens/animations.css` partial declares stroke-dasharray + 600ms cubic-bezier transition; `BrandMark` accepts `interactive` (hover) + `loading` (3s loop) props. Reduced-motion fallbacks per class (defense in depth).
- T1.76 `/dev/tokens` gallery route — production-guarded (renders "Not available" stub). Sections: Color (with swatches), Typography (fluid scale), Motion (springs + easings), Font Axes, Brand Mark (16/32/192/512px), Z-Stack hierarchy. Helper `_sections.tsx` keeps page.tsx under arch limits.
- T1.77 `audit-legacy-brand.mjs` — greps for MontGoWork / M-shape / legacy polyline geometry; allowlists test files + legal copy + storage namespace + icon.svg comment. `npm run audit:brand` registered.
- T1.79 Web Vitals reporter — `useWebVitals` hook subscribes to LCP/CLS/INP/FCP/TTFB; `vitals-reporter.ts` is env-aware (dev: console.log; prod no endpoint: no-op; prod with endpoint: fetch POST, swallow failures). `web-vitals@^4` installed.
- T1.82 FpsOverlay — dev-only fixed-bottom-right panel with rolling 60-frame FPS average. Triple gate: NODE_ENV !== production, AND (`?fps=1` OR `window.__GOWORK_FPS__`), AND not reduced-motion. Uses `--z-toast` token.

**Wave 2 (Cross-driver integration, all shipped):**
- `lib/wall/storage.ts` — STORAGE_KEYS namespace with typed helpers `getStored/setStored/removeStored`. **Fixes silent mute bug**: MuteToggle was writing `gowork-muted` (hyphen) while sound.ts read `gowork.muted` (dot) — now both flow through `STORAGE_KEYS.MUTED`.
- Z-stack token system — 9 tokens in `tokens/layout.css` (`--z-skip-link: 100` down to `--z-content: 1`). Applied to `CookieBanner`, `PWAInstallPrompt`, `Header`, `TitleSequence`. **Fixes z-[55] collision** between CookieBanner + PWAInstallPrompt.
- `.skip-to-content` CSS class with `--z-skip-link` (100) so keyboard users land first, never occluded.
- MuteToggle ↔ sound integration test — verifies live state mirror (clicking toggle un-mutes sound module synchronously). Pre-seeded `gowork.muted=false` hydrates BOTH systems.
- `docs/spanish-translation-review.md` — 4 most-loaded Spanish strings (404 wall metaphor, 500 calibrating motif, footer brand, header brand). Reviewer prompts as actionable checklists; sign-off section.

**Wave 3 (Editorial polish, all shipped):**
- `.editorial-dropcap::first-letter` — magazine drop-cap with amber accent + clamp-scaled font-size. Legacy `.dropcap` retained with cyan for back-compat.
- `.editorial-pullquote` — large oblique-slant axis pull-quote with amber left border.
- `.editorial-link` — gradient underline (cyan → amber) via background-image, expands on hover/focus, falls back to solid border under reduced-motion.
- `::selection` + `::-moz-selection` — already shipped by Driver A; verified branded cyan tint via test.

**Wave 4 (Architectural improvements, all shipped):**
- BrandMark `loading=true` prop — applies `.brand-loading` class (3s draw loop). Reduced-motion fallback: opacity pulse.
- BrandMark `interactive=true` prop — applies `.gowork-mark--hover` class for T1.107 hover/focus draw.
- `__tests__/integration/layout-composition.test.tsx` — renders full overlay stack (CookieBanner + PWAInstallPrompt + AriaLiveRegion + SkipToContent), asserts zero React warnings, no z-[55] literal in DOM, z-stack hierarchy strictly descending.
- `__tests__/integration/brand-loading-cinematic.test.tsx` — verifies BrandMark + cinematic + brand-assets + STORAGE_KEYS all reach via `lib/wall` barrel.
- `__tests__/integration/mute-toggle-sound.test.tsx` — cross-driver integration verified.

**Wave 5 (Tooling, all shipped):**
- `audit-brand-integrity.mjs` — stronger gate: legacy hex (#1c3461 navy, #2a9d8f teal) + variant spellings.
- `audit-tokens.mjs` — declared/consumed gap analysis; reports unused tokens, duplicates, undeclared `var()` consumers; allowlist for Radix dynamic vars + JS-set `--flashlight-*`.
- `npm run audit:brand` + `npm run audit:tokens` registered.
- Both audits run clean on current tree.

**Wave 6 (Documentation, all shipped):**
- `docs/sprints/w1-foundation-summary.md` — full inventory of A+B+C+D deliverables.
- `docs/sprints/w2-readiness-gate.md` — checklist of foundation/test/arch/brand/lint/cross-driver/docs/bundle gates before W2 engagement.
- `frontend/src/components/wall/README.md` — component inventory + z-stack hierarchy + reduced-motion contract + storage namespace contract.
- `frontend/src/lib/wall/README.md` — public API surface + module-by-module contract.
- This state.md entry.

**Wave 7 (Spotlight inventions, ≥6 delivered):**
1. `lib/wall/storage.ts` — namespaced STORAGE_KEYS + typed helpers. The brief never asked for centralization; fixed the silent-mute bug class.
2. `lib/wall/log.ts` — structured logger with `withScope` chaining, dev/prod guards, pipes warn/error through error-reporter for PII-scrubbed prod telemetry.
3. `lib/wall/featureDetect.ts` — centralizes browser feature probes (View Transitions, Battery, Vibration, container queries, color-mix, OKLCH). Each cached, SSR-safe, falsy on server.
4. `lib/wall/brandAssets.ts` — single asset registry (12 entries: 1 svg + 5 rasters + 1 OG + 5 audio) with paths + descriptions. Distinct from PWA web manifest; powers `/dev/tokens` + future audit scripts.
5. `lib/wall/cinematic.ts` — first-paint timing tokens. Four steps (presenter/title/subtitle/handoff) with `{delayMs, durationMs, easing, intent}`. Other surfaces reach for `getCinematicStep()` instead of inlining ms literals.
6. `lib/wall/landmarks.ts` — keyboard-skip landmark map (main, header, footer, chapters). SkipToContent v2 (W4) consumes it for a multi-target menu.

**Tests:** Frontend 1634 → 1772 (+138). All 200 test files green. Pre-existing PlanExport flake observed once during full-suite run; deterministic in isolation; root cause is parallel-test pollution unrelated to W1 work.

**Architecture:** `bpsai-pair arch check` clean across `frontend/src/lib/wall/`, `frontend/src/hooks/`, `frontend/src/components/wall/`, `frontend/src/app/dev/`, `frontend/src/lib/analytics/`. Largest source file: `lib/wall/sound.ts` (207 lines). Largest function: `useScrollProgress` useEffect body (29 lines).

**Cross-driver bug fixed:** MuteToggle silent mute. Driver C wrote `gowork-muted` (hyphen), Driver B's sound.ts read `gowork.muted` (dot). User clicks unmute, page stays silent. Fixed by introducing `STORAGE_KEYS.MUTED` as the single source of truth; both modules import the same constant. Integration test verifies live state mirror.

**Honest uncertainty (C4/C5):**
- C4: PlanExport flake remains pre-existing — requires investigation in S13b or souji-sweep. Not introduced by W1.
- C4: Audit-tokens script reports 87 declared-but-unused — most are Tailwind-consumed shadcn HSL tokens read via `tailwind.config.ts`, not via `var()`. False positives, not actionable in W1.
- C5: web-vitals package install added 1 dep; baseline-bundle-sizes.json may need refresh in W2 (deferred).

**Spanish translation review:** Doc shipped with reviewer prompts. NOT yet reviewed by native Spanish speaker — flagged in W2 readiness gate.

**Deferred to souji-sweep / W2:**
- 16px favicon prefers-color-scheme: light variant (low value vs effort; OS dark/light auto-handling already covers most cases)
- TitleSequence × CursorFlashlight cinematic compose (Wave 4 enrichment) — risky to ship in Driver-D pass without end-to-end Mapbox boot context
- CI workflow additions (`.github/workflows/ci.yml` patches) — deferred since CI infrastructure changes need separate review window
- baseline-bundle-sizes.json refresh — deferred to W2 (requires `npm run analyze` + manual review)

### 2026-04-28 — Sprint W1 Driver B (worktree-agent-aa3c7da3ebd00af01) — hooks + audio + cursor + types/barrels + enrichment

Branch: `w1-driver-b/hooks-utilities-audio-cursor`. Lane: hooks + utilities + audio + cursor + types + barrels + enrichment. Driver A and C work in parallel sibling worktrees.

**Wave 1 (Mapbox boot validator):** T1.6 — `frontend/src/lib/wall/env.ts` exports `validateMapboxToken()`, `isMapboxAvailable()`, `getMapboxToken()`. Public-token-only contract (`pk.` prefix required; `sk.` rejected). 7 vitest cases, all green.

**Wave 2 (10 utility hooks, T1.24–T1.33):** All SSR-safe with cleanups; tests cover initial state, behavior, unmount. `useTimeOfDay` (4-phase + sun position + accent shift, latitude-aware), `useCursorPosition` (rAF-throttled normalized x/y + signed vx/vy; touch fallback via `navigator.maxTouchPoints`), `useLiveNow` (TanStack Query 10s poll; graceful 404 fallback), `useScrollProgress` (framer-motion useScroll wrapper, chapter-aware), `useVariableFontWeight` (memoized wght 700–900 / opsz 14–32; reduced-motion locks at 800/23), `useScrollVelocity` (rAF delta sampling, isFast threshold), `usePrefersReducedMotion` (matchMedia subscription, SSR fail-open false), `useIdleState` (4-listener cluster: pointermove/keydown/wheel/touchstart), `useViewTransitionsSupport` (one-shot feature detect), `useLanguage` (wraps useTranslation; `gowork.locale` + legacy `montgowork-locale` dual write).

**Wave 3 (audio system, T1.56–T1.59):** `frontend/src/lib/wall/sound.ts` Howler singleton with lazy import (Howler not in main bundle until first unmuted play); default-muted; `play/stop/setMuted/isMuted/setVolume/getVolume/unlock`; localStorage `gowork.muted` persistence; `unlock()` resumes suspended AudioContext exactly once (T1.58). `frontend/public/sounds/` scaffolded with 5 silent 104-byte placeholder MP3s + README documenting replacement contract (≤50KB, 44.1kHz mono, CC0 license).

**Wave 4 (cursor system, T1.60–T1.62):** `CursorTrail` (8px cyan dot, position fixed, pointer-events none, returns null on touch + reduced-motion); `CursorFlashlight` (80px radial gradient, sets `--flashlight-x` and `--flashlight-y` CSS vars; uniform-bright fallback for touch/reduced-motion). T1.62 reduced-motion paths verified by tests.

**Wave 5 (types + barrels, T1.67–T1.69):** `lib/wall/types.ts` (TimePhase, AccentShift, ChapterId 1..10, ChapterState, MapboxLayer, CameraState, SoundId, LocaleCode, BarrierType, BarrierGraphNode, RumSessionId branded type — 10 vitest expectTypeOf cases). `lib/wall/index.ts` re-exports env + types + sound (tokens.ts deferred to Driver A merge). `hooks/index.ts` re-exports all 10 W1 hooks + legacy useTranslation/useCityConfig/TranslationProvider. Barrel tests verify every public symbol resolves.

**Wave 7 (enrichment, P1 priorities):** `useBatteryAware` (T1.98 — getBattery API, levelchange + chargingchange listeners, isLow at <20% AND not charging), `useDeviceCapability` (T1.75 — tier=low/medium/high from deviceMemory + hardwareConcurrency + saveData, WebGL probe cached at module level), `usePerformanceBudget` (T1.73 — PerformanceObserver longtask + heap + dropped-frames; isUnderPressure thresholds; spotlight invention 1), `lib/error-reporter.ts` (T1.117 — singleton report() with PII scrub: `<EMAIL>` for matching values + `/Users/<USER>` and `C:\Users\<USER>` for stack traces; dev console / prod fetch with silent failure), `SectionErrorBoundary` (T1.115 — class boundary with retry button, custom fallback prop, default branded fallback when Driver C's ErrorState not yet merged), `lib/wall/network.ts` (T1.99 — `getNetworkProfile()` from `navigator.connection`; effectiveType normalized to `2g|3g|4g|unknown`; `isSaveDataOn` and `isSlowConnection` helpers), `lib/analytics/session-id.ts` (T1.81 — async `getSessionId()` SHA-256 hash of UA + screen + nonce; sessionStorage key `gowork.rum.sid`; non-crypto FNV fallback when subtle.digest unavailable; `'ssr'` literal during server render), `useMemoryProfiler` (T1.128 — dev-only sampler, no-op in production, tracks usedMb + peakMb).

**Tests:** 151 Driver-B vitest cases across 26 files, all green. Full project suite: 1288/1290 pass — the 2 failures are pre-existing flake in `CareerCenterExport.test.tsx` (unrelated to Driver B).

**Arch check:** `bpsai-pair arch check` clean across `frontend/src/hooks/`, `frontend/src/lib/wall/`, `frontend/src/lib/analytics/`, `frontend/src/components/wall/`, and `frontend/src/lib/error-reporter.ts`. No source file >200 lines; no function >50; no file >15 functions or >20 imports.

**Spotlight inventions (≥3 required):**
1. `usePerformanceBudget` — live RUM canary feeding W2/W3 their own perf budget, beyond the brief's CI-only Lighthouse gate.
2. `useDeviceCapability` — tier classification beyond `window.innerWidth`; the brief's mobile fallback would have shipped a Three.js scene to a 2GB Android.
3. `useBatteryAware` — animations off path for the demo viewer at 18% battery; brief never named this surface.
4. PII-scrubbing error reporter — `<EMAIL>` + `<USER>` regex defenses mean the production logs are demo-day-safe even if a future hook accidentally passes through user data.
5. Async SHA-256 session id — privacy-safe RUM correlation without cookies, with a graceful non-crypto fallback so jsdom tests + older browsers still work.
6. `useMemoryProfiler` — dev-only memory sampler that's tree-shaken from prod via `NODE_ENV` guard; gives Driver agents in W2/W3 a real-time signal during heavy build sessions.
7. Lazy Howler import — Howler.js never enters the main bundle until the first unmuted play; the default-muted contract means most users never download it.

**Cross-driver coordination:**
- `lib/wall/index.ts` does NOT yet re-export from `./tokens` (Driver A's lane); a one-line addition at merge time will close the gap. Documented inline.
- `SectionErrorBoundary` ships with a default branded fallback so it compiles standalone; Driver C's `ErrorState` (T1.44) can be passed in via the `fallback` prop after merge.
- `useCursorPosition` + `CursorTrail` + `CursorFlashlight` standardized on `navigator.maxTouchPoints > 0` for touch detection (jsdom has `'ontouchstart' in window` truthy by default — using it as the sole signal would break tests + downstream consumers on hybrid laptops).
- localStorage keys: `gowork.locale` + legacy `montgowork-locale` (both written by `useLanguage.setLocale`); `gowork.muted` (sound module); `gowork.rum.sid` (sessionStorage, RUM session id). All keys namespaced for the GoWork rebrand.

**Honest uncertainty (C4/C5):**
- C4: Battery API is dropping in Firefox; iOS Safari has never supported it. `useBatteryAware` correctly returns `null` + `isLow=false` on those browsers but consumers must check `level !== null` before showing battery-specific UI.
- C4: `performance.memory` is Chrome-only; `usePerformanceBudget` reports `jsHeapUsedMb=0` on Safari/Firefox — long-task data still works but isUnderPressure may underfire if heap is the bottleneck.
- C4: `useViewTransitionsSupport` reads `document.startViewTransition` once on mount — accurate today (April 2026) but the API surface has been moving. W3 chapter-10 transition fallback path must be tested in browser, not jsdom.
- C5: vitest 4 default `pool: 'forks'` ran out of memory when the framer-motion mock returned a fresh object on every render — fixed by hoisting the mock to a stable singleton. Without that fix, the worker exits with a heap allocation failure rather than a test assertion.
- C3: Howler `iOS` audio-context-resume is genuinely flaky on real devices; the `unlock()` API surface is correct but real hardware testing is W2 work.

**Memory profile:** No leaks observed. Cleanup discipline tested for all hooks: every `addEventListener` has a matching `removeEventListener` in the cleanup; every `setInterval` is cleared; every rAF id is canceled.

**Cross-driver concerns / merge notes:**
- I installed `howler` + `@types/howler` with `--no-save` so my standalone vitest works. Driver A's package.json install will be the merge winner; my package-lock.json change was reverted.
- W2 will need to add Driver A's `tokens.ts` re-export to my `lib/wall/index.ts` at merge time (single line: `export * from "./tokens"`).
- All file ownership respected — no edits to globals.css, layout.tsx, Header/Footer, edge-state components, or translation jsons. Coordination only via the `gowork.locale` localStorage key dual-write contract for Driver C's LanguageToggle.

### 2026-04-27 — Sprint W1 backlog drafted (foundation + brand + edge states)

Authored `plans/backlogs/sprint-w1-foundation.md`: 68 tasks, 582 Cx, 17 phases (visual; engage parser collapses to 1 phase but priority order preserved via `Depends on:` DAG). P0/P1/P2 split: 51/14/3. Critical path: T1.1 install + T1.7 globals.css split (Wave 1, parallel) → infra installs + CSS imports + Mapbox token validator (Wave 2) → tokens (color/type/motion) + 10 utility hooks + types (Wave 3, parallel) → brand mark + edge states + header/footer + audio + cursor + a11y + barrels + Spotlight (Wave 4, max parallel) → arch sweep + vitest gate (Wave 5). Spotlight inventions beyond the brief: T1.73 `usePerformanceBudget` (telemetry canary for W2/W3 perf gate); T1.74 Mapbox-token-missing branded fallback (first-impression rescue when judges clone without env setup); T1.75 `useDeviceCapability` (low-end Android tier detection beyond window.innerWidth); T1.76 dev-only `/tokens` gallery route (Storybook substitute, 10x cheaper review surface); T1.77 legacy M-shape retirement audit script + state.md note (explicit retirement receipt). Honest uncertainty section called out: C4 next/font opsz axis stability, C4 Lightning CSS @import ordering, C4 color-mix() Safari fallback, C4 @vercel/og Next 15 runtime, C5 dev-only route bundle isolation, C3 Mapbox style URL, C2 Spanish translation tone, C3 Howler iOS audio unlock. Dependency graph verified: 0 missing references, 0 cycles. Dry-run validation passes: `bpsai-pair engage plans/backlogs/sprint-w1-foundation.md --dry-run` parses 68 tasks cleanly. Foundation file collision matrix flags 17 file-level collisions, all resolved via serialization or single-rewrite ownership. Brand retirement of legacy M-shape `icon.svg` is explicit (T1.34 replaces; T1.77 audits).

### 2026-04-27 — Sprint W5 backlog drafted (submission readiness)

Authored `plans/backlogs/sprint-w5-submission.md`: 52 tasks, 277 Cx, 12 phases. Anchored to HackFW deadline (target submit 9:00 AM CDT May 2; hard deadline 2:00 PM CDT). Phases: copy-thesis SoT (1) → README rewrite (5) → press kit refresh (6) → submission demo script (4) → submission video full + 60s teaser (6) → Devpost submission (5) → per-chapter OG (3) → final polish + verification (5) → deployment (5) → FW DAO bounty research (3) → D-day runbook + submit (5) → post-submission archive (4). Spotlight inventions beyond brief: copy-thesis single-source-of-truth file (W5.1), 60-second teaser video (W5.17/W5.20/W5.22), brand+numbers consistency sweep script (W5.35), Mapbox rate-limit honesty research (W5.40), D-day minute-by-minute runbook (W5.44), live-demo URL above the fold (W5.51), submission-state archive bundle (W5.52). Dry-run validation passes: `bpsai-pair engage plans/backlogs/sprint-w5-submission.md --dry-run` parses 52 tasks cleanly.

### 2026-04-27 — Sprint W4 enrichment pass (T4.77–T4.134 appended)

Append-only enrichment to `plans/backlogs/sprint-w4-life-layers.md`: +58 tasks (T4.77–T4.134), 6 new phases (18–23). New totals: 132 tasks (P0: 96, P1: 32, P2: 4), 1002 Cx (P0: 778, P1: 202, P2: 22) — under the 140 hard cap. T4.1–T4.76 unchanged. Phases added: Time-of-Day Deeper — 8-phase TOD with sun-elevation-aware boundaries, golden-hour accent boost + slower motion, Open-Meteo weather scaffold with 24h cache + graceful fallback, viewer-timezone respect (not hard-coded America/Chicago), manual phase override with Cmd-Shift-T shortcut, per-phase widget tinting, ambient audio crossfades, RAF-batched scroll-coupled sky transitions (8 tasks). Cursor Flashlight Polish — velocity-driven trail strength, idle pulse at 8s, keyboard-marker focus = flashlight center (refines T4.50), per-chapter color tint mixed with TOD accent, forced-colors mode handling (5 tasks). Live Now + Variable Font + OG Deeper — weather/uptime/deploy/jurisdiction fields, privacy-safe sessions counter, click-to-expand popover, locale time format (12h US / 24h ES), italic axis, hover/focus weight boost, OG wave-time stat, hreflang-aware localized OG, Spanish-specific cultural framing OG (10 tasks). Spanish Parity Deeper + Branded Edge States — reviewer-agent gate template, Carlos-narrative cultural review, "Ciudad de Fort Worth" formal naming + lint, guillemets enforcement, locale-aware date/currency/number helpers, hreflang + Spanish accessibility statement, branded 404 ("no path to this URL — but there is one through the wall"), branded 500 (calibrating motif), branded empty/loading, per-component error boundary (10 tasks). RM + AAA + Keyboard + SR Deeper — RM screenshot fallbacks for ~15 camera flights, 5 Carlos waypoints PNGs, paused 3D fallback rotation, per-state contrast (hover/focus/active/disabled) at AAA, forced-colors full sweep, prefers-contrast: more support, color-blind shape encoding for cliff zones, link underlines + skip-to-content visible on focus, chapter shortcuts (1–0, vim j/k) with `?` cheat-sheet, Cmd-K command palette, ARIA-live for cliff math + Carlos position + 3D text alt (12 tasks). Mobile + Performance + Integration Deeper — chapter-specific mobile layouts (cliff slider, vertical timeline, 2D SVG, tap-list), opt-in swipe gesture, opt-in vibration with iOS-Safari-safe feature detect, Save-Data + Battery API hints, Lighthouse per-chapter score with trend chart in docs, bundle analyzer treemap with PR diff, tree-shaking audit, image + font budget enforcement at build, code-split verification + per-chapter LCP, per-chapter CLS lock at < 0.05, 12 life-layers compound integration test, popover×flashlight×audio compound test (13 tasks). Spotlight Inventions (Enrichment Pass) section appended at bottom: 13 inventions catalogued including viewer-timezone respect, manual phase override (a11y + demo determinism dual-purpose), keyboard-marker flashlight (parity perception), forced-colors sweep (often-missed surface), Spanish-specific OG cultural framing (not literal), Carlos cultural review (anti-paternalism gate), branded 404/500 (Wall identity reaches edge states), color-blind shape encoding for cliff (information-design improvement), chapter shortcuts (a11y + delight), mobile chapter-specific layouts (mobile as first-class surface), Lighthouse per-chapter trend chart (judging-day evidence of discipline), image/font budget at build (silent-drift gate), 12-layer compound test (max-stress survival). Honest uncertainty extended with 14 new C4/C5 items: 8-phase TOD perf on mid-tier mobile, Open-Meteo availability, Vibration/Battery API absence on iOS Safari/FF, forced-colors regressions in Mapbox canvas, reviewer-agent merge bottleneck, Carlos cultural framing paternalism risk, bundle analyzer CI overhead, image budget exceeded by combined RM+mobile+OG fallbacks, per-chapter LCP variance from CI cold starts, Cmd-K vs browser shortcut collisions, Save-Data inconsistency, italic/opsz/slant cross-browser quirks, guillemet over-enforcement on intentional mixed quotes. File collision matrix updated: 6 new files added (CursorFlashlight.tsx, not-found.tsx, error.tsx, next.config, lighthouse.yml, lighthouserc.json second touch); existing entries extended with new task IDs touching them. Priority order extended with Wave 5 (enrichment pass) mapped onto wave-1 foundations / wave-2 build / wave-3 build / wave-4 integration. Hard gate extended: T4.66 + T4.126 + T4.130 + T4.133 must all pass. Dry-run validation passes: `bpsai-pair engage plans/backlogs/sprint-w4-life-layers.md --dry-run` parses 132 tasks, 1002 Cx cleanly.

### 2026-04-27 — Sprint W5 enrichment v2 (W5.53–W5.110 appended)

Append-only revision v2 to `plans/backlogs/sprint-w5-submission.md`: +58 tasks (W5.53–W5.110), 8 new phases (13–20). New totals: 110 tasks, 447 Cx (dry-run parsed), P0: 65, P1: 38, P2: 7 — under the 130 hard cap. W5.1–W5.52 unchanged. Phases added: Devpost field cataloging with measured length limits + video spec verification + eligibility + prizes/tracks (7 tasks); GitHub repo polish — LICENSE/CHANGELOG/ROADMAP/CODE_OF_CONDUCT/CONTRIBUTING/issue+PR templates/SECURITY/dependabot/CI workflows/repo metadata/branch protection (12 tasks); README deeper polish — hero img, demo CTA, badges, watch links, deploy guide, city framework + acknowledgments (6 tasks); video deeper polish — YouTube + Vimeo dual-host, separate voice-over recording with noise reduction, B-roll capture, project file backup, human-transcribed captions with brand-name review pass, custom thumbnail, CC test, audio mix balance (9 tasks); D-day minute-by-minute runbook strengthening with T-72h through T+1h blocks plus 5-failure-mode contingency branches (10 tasks); post-submission engagement — Twitter/LinkedIn/civictech-Reddit announcements, thank-you, journey blog post, archive zip, post-mortem template (7 tasks); post-launch analytics — tool decision + events catalog + 30-day retro template (3 tasks); accessibility verification final — VoiceOver per chapter + keyboard-only per chapter + print/forced-colors mode + WCAG 2.1 AA conformance statement (4 tasks). Six new Spotlight inventions: field-by-field Devpost catalog (W5.53), human-transcribed caption review (W5.83), 5-failure-mode contingency branches (W5.95), submission-state zip archive (W5.102), public WCAG 2.1 AA statement (W5.110), Vimeo-as-backup-host (W5.79). Honest uncertainty extended (15 items total) — Devpost UI drift between W5.45 and W5.48, video host processing time, voice-over without pro studio, B-roll license nuance, WCAG claim accuracy if a11y findings surface, branch-protection pre-vs-post-submit timing, analytics tool default-to-none. No new code in /frontend or /backend; W5 strictly extends docs/video/GitHub-metadata. Dry-run validation passes: `bpsai-pair engage plans/backlogs/sprint-w5-submission.md --dry-run` parses 110 tasks cleanly. File collision matrix updated for README.md (12 sequential touches) and d-day-runbook.md (12 sequential touches).

### 2026-04-25 — Sprint S13 ready for PR

8 waves shipped (Wave 0 foundation → Wave 7B perf+analysis). Test deltas: backend 3267→4080 (+813), frontend 946→1109 (+163). 15 production fixes (catalog above in S13 summary).

Outstanding pre-PR: /reviewing-and-fixing pipeline running. Browser-driven remainder lives in a follow-up branch (S13b).

## What's Next

1. **Ren reviews PR #81** and merges `sprint/w1-foundation` → `sprint/visual-rebirth` when satisfied (souji-sweep complete; CI green; mergeable/clean)
2. Optional follow-up on `sprint/visual-rebirth`: refresh `frontend/baseline-bundle-sizes.json` via `npm run analyze` (souji item #1, deferred — needs canonical CI build environment)
3. Engage `sprint/w2-mapbox-chapters` per `docs/sprints/w2-readiness-gate.md` — verify ALL gates green before starting
4. W4 backlog already enriched (132 tasks, 1002 Cx). Re-validate dependency graph before W4 starts — Wave 5 (enrichment) overlays on Waves 2 + 3.
5. Engage W2 → W3 → W4 → W5 in order; merge `sprint/visual-rebirth` to main only at W5 completion
6. May 2 D-day: execute W5.44 runbook, hit Devpost submit by 9:00 AM CDT
7. Background: /reviewing-and-fixing pipeline still gating S13 PR

## Blockers

None. W5 backlog is ready to engage; W1–W4 backlogs are upstream and must be drafted/engaged first per the visual-rebirth sequencing in `docs/visual-rebirth-briefs.md`.

## 2026-04-28 — W2 Driver A (Mapbox Foundation lane) complete on worktree-agent-adb30d00402a7efc4.

**Branch:** `sprint/w2-mapbox-chapters-1-5` (rebased from `8b04ae8` via worktree-agent-adb30d00402a7efc4 — local commits not yet pushed; Ren coordinates push after souji-sweep per dispatch protocol).

**Tasks completed (T2.X):**
- Wave 1 — Foundation: T2.1 (token validation + async network probe with 2s timeout), T2.2 (WallContainer with WallContext + tier gate + dynamic Mapbox import), T2.3 (MapboxScene with react-map-gl v7), T2.4 (INITIAL_CAMERA = Fort Worth centroid), T2.5 (explicit map.remove() cleanup), T2.18 (Mapbox style URL resolver + runbook + JSON archive).
- Wave 2 — Scroll engine + camera: T2.6 (ChapterScaffold with sticky atmosphere + opacity curve + reduced-motion + aria-live), T2.7 (cameraChoreography per-chapter states + TRANSITION_SPEEDS table), T2.8 (useChapterProgress 1-indexed boundary band hook), T2.9 (flyToOrchestrator pure transition with reduced-motion jumpTo branch), T2.10 (useScrollPin feature-detect sticky support).
- Wave 4 — page.tsx: T2.46 (legacy /archive route preserved), T2.47 (page.tsx rewritten to render WallContainer; preserves /daily redirect).
- Wave 6 — Lazy load: T2.58 (Mapbox dynamic-imported via next/dynamic with ssr:false; bundle budget contract test pins the constraint).
- Wave 7 — Build + bundle: T2.66 (production build smoke green; bundle: `/` 3.66 kB / 115 kB First Load JS, `/archive` 4.47 kB / 163 kB; mapbox-gl ~600KB stays out of the initial chunk; shared 102 kB).

**Tasks deferred / out-of-lane (sibling drivers):**
- T2.11–T2.15 data layers (Trinity Metro / offices / ZIP / Carlos pin / jobs) — Driver B
- T2.16 marker SVG sprite, T2.17 layer composer — Driver B
- T2.19–T2.45 chapter components Ch1–Ch5 — Drivers B + C
- T2.30 cursor-flashlight conditional activation — chapter-aware activation deferred to chapter components
- T2.48 chapter-progression contract test — depends on chapters
- T2.49–T2.53 EN/ES copy population — Driver C
- T2.54–T2.56 axe-core + heading hierarchy + skip-to-content — depend on chapters
- T2.57 chapter code-splitting — depends on chapter components
- T2.59–T2.65 sprint coverage tests — depend on full chapter render path

**Spotlight inventions (Legacy beyond brief):**
1. URL-spoofing defense in resolveMapboxStyleUrl (Honesty Lens) — env vars are runtime-attacker-controllable; rejecting non-mapbox-style URIs prevents redirecting the map to a malicious style.json.
2. TRANSITION_SPEEDS per-pair table (Permission Lens) — Mapbox flyTo speed default is 1.2; tuning per-pair (1.4 for continental dolly, 0.6 for sub-chapter pivots) is the cinematic upgrade the brief implied but didn't catalog.
3. CSS-only branded static fallback shipped before the JPG pipeline (Multiple Selves Lens — judge on a token-less Vercel preview) — pure CSS gradient + Inter Variable hero + accessibility label. Ship the gate now, swap to image when asset lands.
4. Tier-based mobile fallback wired in W2 (Resilience Lens — Carlos on Pixel 4a) — low-tier OR no-WebGL routes to the same branded fallback path. W4 will graduate to scaled-down map.
5. Bundle budget contract test (Wisdom Lens) — static contract test reads source files and asserts the lazy-load pattern; a future driver promoting mapbox-gl to a static import fails the test before bundling bloats.
6. ChapterScaffold opacity curve exported as a pure function (Compound Lens) — `computeOverlayOpacity(progress, reducedMotion)` is exported separately from the JSX so flyTo overlap (T2.114 enrichment) can reuse the same shape — no drift.

**Honest uncertainty (C4/C5):**
- C4 — Worktree branch lineage: dispatch base `sprint/w2-mapbox-chapters-1-5` did not exist on remote at handoff; rebased from `origin/sprint/visual-rebirth` (tip `8b04ae8`) per dispatch authorization. Local-only commits; Ren coordinates push.
- C4 — react-map-gl v7 vs v8 API: dispatch said "v8+" but package.json ships v7.1.7. Used v7 default export. One-line bump if v8 is required.
- C4 — Static fallback JPG asset: T2.1 AC asks for 1920×1080 JPG; shipped CSS-only branding so gate compiles before asset pipeline. One-line src swap when asset lands.
- C4 — Map cleanup ref pattern: addressed ESLint exhaustive-deps warning via capture-at-effect-mount.
- C5 — Pre-existing 2 W1 failing tests: `tokens-reduced-motion.test.ts` + `tokens-typography-utils.test.ts` check for `@layer utilities` directives the W1 hotfix removed. Outside W2-A scope.

**Test coverage delta:**
- Baseline (W1 tip `8b04ae8`): 1772 total / 1769 passing / 3 failing
- W2-A close: 1882 total / 1880 passing / 2 failing
- Net new tests: +110, all green. Floor preserved.

**Architecture compliance:** All new modules pass `bpsai-pair arch check`. Production build green (Next.js 15.5.9). Bundle: `/` 115 kB First Load JS (Mapbox lazy); `/archive` 163 kB (legacy preserved); shared 102 kB.

**Cross-driver concerns / merge notes:**
- Driver B consumes: `WallContainer`, `cameraChoreography.CHAPTER_CAMERAS` (read-only), `useChapterProgress`, `ChapterScaffold`.
- Driver C consumes: same scaffold + hook; extends EN/ES translations under `wall.chN.*`.
- W3 consumes: `cameraChoreography` extends with Ch6–Ch10; `flyToOrchestrator` already permissive (graceful no-op for unknown destinations); `WallContainer` already 1-indexed.
- Wall lib barrel: explicit re-export of W1 env.ts `isMapboxAvailable` as `isMapboxTokenShapeValid` to avoid collision with W2's async `isMapboxAvailable`. W1 tests preserved.
- Hooks barrel: new exports (`useScrollPin`, `useChapterProgress`); barrel test 3/3 green.

**Commit log:**
- `4417a8a feat(w2-A): T2.1 + T2.2 + T2.3 + T2.4 + T2.5 + T2.6 + T2.7 + T2.8 + T2.9 + T2.10 + T2.18 + T2.46 + T2.47`
- Pending: lazy-load contract + tier gate + state.md update commit (this commit).

慣性の契約.
