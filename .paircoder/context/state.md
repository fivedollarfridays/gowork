# Current State

> Last updated: 2026-04-25 (S13 doc cleanup — verbose detail moved to `.paircoder/archive/state-s13.md`)

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

### 2026-04-28 — Sprint W1 Driver A (Style + Tokens lane) complete

Worktree `worktree-agent-a5261163c6500bfcd` branched off `sprint/w1-foundation`. Driver A delivered the W1 visual foundation lane:

- **Wave 1 — Installs (T1.1-T1.5)**: package.json declarative deps for mapbox-gl + react-map-gl + @react-three/fiber + @react-three/drei + three + satori + @vercel/og + howler + svgo. svgo.config.mjs created with conservative settings (preserves viewBox/title/desc/id). NEXT_PUBLIC_MAPBOX_TOKEN documented in .env.local.example. Lockfile regen deferred to merge-time (worktree's node_modules junctions to parent).
- **Wave 2 — CSS architecture (T1.7-T1.9)**: globals.css split into 5 partials (colors/typography/motion/space/layout) + globals.css now a 14-line shell of @tailwind + @import. T1.9 regression test locks @import order.
- **Wave 3 — Color tokens (T1.10-T1.13)**: OKLCH base palette (7 tokens) + 7 accents/status + 15 color-mix shade variants + --temperature-multiplier formula for --accent-current. WCAG AAA contrast script + library + npm run contrast (15 fg/bg pairs all clear AAA). Token snapshot lock guards 59 token names.
- **Wave 4 — Typography (T1.15-T1.17)**: --font-inter-var + --font-inter-stack with metric-tuned fallback. Fluid clamp() type scale. .tabular-nums + .font-mono-data utilities. Driver C handoff documented for layout.tsx Inter Variable wiring.
- **Wave 5 — Motion (T1.19-T1.23)**: SPRING_SOFT/SNAPPY/ELASTIC + EASE_LINEAR_SIG + EASE_OUT + DURATION_BASELINE_MS + STAGGER_CHILD_OFFSET_S exports in frontend/src/lib/wall/tokens.ts (W1's TS token surface). CSS mirrors in motion.css. --motion-disabled token + universal !important reduced-motion override. @keyframes idle-pulse + .animate-idle-pulse utility.
- **Wave 6 — Print + focus + selection (T1.45, T1.65)**: frontend/src/app/styles/print.css magazine layout (serif body, .wall-chapter page-breaks, dropcap print, Mapbox→caption fallback). *:focus-visible cyan ring with animated outline-offset transition. ::selection + ::-moz-selection cyan glass.
- **Wave 7 — Enrichment (T1.96, T1.97, T1.102, T1.103, T1.106)**: forced-colors.css partial (Windows HCM brand-token-to-system-color mapping). prefers-contrast: more @media block. Variable font axis tokens (slant + opsz + wght). .dropcap::first-letter editorial drop cap. Branded scrollbar (Webkit + Firefox).
- **T1.6 — Mapbox token boot validator** at frontend/src/lib/wall/env.ts. SSR-safe; rejects sk.* private tokens.

**Test delta**: 11 new test files, 100+ new vitest assertions. Full suite: 1290/1291 passing (1 pre-existing PlanExport flake under parallel load — passes in isolation; not introduced by W1).

**Architecture compliance**: arch check clean on every modified file. Largest file: colors.css at 194 lines (under 200 warning).

**Spotlight inventions** (≥3 per dispatch):
1. Lifted --fg-secondary #94A3B8 → #A4B3C7 and --fg-muted #64748B → #8696A8 to clear AAA on all surfaces (plan-file values were 6.11 / 4.05 — under AAA-normal / AAA-large).
2. Pre-emptive forced-colors.css partial (T1.96 enrichment) wired into globals.css cascade order so HCM users see the Wall as functional civic infrastructure.
3. T1.97 prefers-contrast: more block built on top of T1.10-T1.11 instead of waiting for the enrichment phase — locked in early so Driver B/C can rely on consistent high-contrast tokens.
4. Token snapshot lock test (T1.13) covers 59 tokens, prevents silent renames.
5. Verify-contrast script extracted into a pure ESM lib (scripts/lib/contrast.mjs) so CI + vitest both consume the same code path.

**Honest uncertainty (C4 / C5 surfaced inline)**:
- next/font axes:['opsz'] in Next 15 (T1.15) — Driver C's territory; documented fallback to @fontsource-variable/inter.
- color-mix() browser support (T1.11, T1.12, T1.65) — @supports-not hex fallback block ships defensively.
- npm install lockfile regen deferred to merge-time (worktree node_modules junctions to parent).
- T1.21 Spotlight Resilience: motion.tsx left untouched; new tokens adopted by W2/W3/W4 components, not retrofit (existing 0.25 stagger preserved for legacy shadcn pages).

**Cross-driver concerns surfaced**:
- T1.15 layout.tsx wiring deferred to Driver C (file ownership). Tokens shipped + documented.
- T1.45 layout.tsx `<link rel="stylesheet" media="print">` deferred to Driver C.

Branch: `worktree-agent-a5261163c6500bfcd` ready for Ren to merge into sprint/w1-foundation.

### 2026-04-25 — Sprint S13 ready for PR

8 waves shipped (Wave 0 foundation → Wave 7B perf+analysis). Test deltas: backend 3267→4080 (+813), frontend 946→1109 (+163). 15 production fixes (catalog above in S13 summary).

Outstanding pre-PR: /reviewing-and-fixing pipeline running. Browser-driven remainder lives in a follow-up branch (S13b).

## What's Next

1. Ren coordinator merges 3 W1 driver worktrees into `sprint/w1-foundation`.
2. Run `npm install` once post-merge; verify package-lock regen + bundle analyzer (mapbox + three NOT in `/` route's First Load JS).
3. Run vitest full suite + Playwright; flake check.
4. Run souji-sweep on `sprint/w1-foundation`; merge to `sprint/visual-rebirth`.
5. W2 begins (10-chapter Mapbox Wall) on top of these foundations.

(S13 PR pipeline still pending — see archive history.)

## Blockers

None. /reviewing-and-fixing pipeline is the gate to PR.
