# W2 Readiness Gate

> Final checklist before engaging `sprint/w2-mapbox-chapters`.  
> Authored: 2026-04-28 by W1 Driver D.

## Purpose

W2 lands Mapbox + Chapters 1–5 — the first interactive surface the judges will see. W1 is the foundation. If W1 is not green by every metric below, W2 will inherit fragility that compounds through W3 and W4.

This gate is NOT a green-light vote — every item below must be verified by an independent agent (souji-sweep + reviewer pass) before W2 starts.

## Foundation gates

- [ ] All W1 backlog tasks marked done in `plans/backlogs/sprint-w1-foundation.md` OR explicitly deferred with reason
- [ ] `git log --oneline sprint/w1-foundation` shows merge commits for Drivers A, B, C, D
- [ ] No dirty working tree (`git status` clean)
- [ ] No `.env` or `credentials.json` committed (run `git log -- '*.env' '*credentials*' --since=1.month` — must be empty)

## Test gates

- [ ] `cd frontend && npx vitest run` exits 0 with >= 1700 tests
- [ ] No flaky tests in 3 consecutive runs (PlanExport.test.tsx + CareerCenterExport.test.tsx flagged but pre-existing)
- [ ] No skipped tests with `it.skip` or `describe.skip` outside intentional WIP guards
- [ ] Coverage gate at >= 95% statements for all new W1 modules

## Architecture gates

- [ ] `bpsai-pair arch check frontend/src/lib/wall/` passes
- [ ] `bpsai-pair arch check frontend/src/hooks/` passes
- [ ] `bpsai-pair arch check frontend/src/components/wall/` passes
- [ ] `bpsai-pair arch check frontend/src/app/dev/` passes
- [ ] `bpsai-pair arch check frontend/src/lib/analytics/` passes
- [ ] No file > 400 lines, no function > 50 lines, no file > 15 functions, no file > 20 imports

## Brand integrity gates

- [ ] `cd frontend && npm run audit:brand` exits 0 (legacy MontGoWork retired)
- [ ] `cd frontend && npm run audit:tokens` exits 0 (no orphan var() consumers)
- [ ] `cd frontend && npm run contrast` exits 0 (WCAG AAA)
- [ ] `cd frontend && npm run svgo -- --dry-run` clean
- [ ] `public/icon.svg`, `public/og-image.svg`, raster favicons present at filesystem level

## Lint + type gates

- [ ] `cd frontend && npm run lint` clean
- [ ] `cd frontend && npx tsc --noEmit` clean (or accepted skiplist)
- [ ] No new `// @ts-ignore` or `eslint-disable` lines without an accompanying issue ref

## Cross-driver integration gates

- [ ] MuteToggle ↔ sound module key alignment (`STORAGE_KEYS.MUTED`)
- [ ] LanguageToggle ↔ useLanguage dual-write to `gowork.locale` + legacy `montgowork-locale`
- [ ] CursorFlashlight + CursorTrail + reduced-motion fallback chain
- [ ] TitleSequence audio handoff plays footstep on completion (when not muted, not RM)
- [ ] Z-stack tokens applied to overlay components (CookieBanner, PWAInstallPrompt, Header, TitleSequence)

## Documentation gates

- [ ] `docs/sprints/w1-foundation-summary.md` exists
- [ ] `docs/spanish-translation-review.md` exists with reviewer prompts
- [ ] `frontend/src/components/wall/README.md` exists (W6 task)
- [ ] `frontend/src/lib/wall/README.md` exists (W6 task)
- [ ] State.md final W1 entry appended

## Bundle + perf gates

- [ ] `cd frontend && npm run size:check` exits 0 (bundle baseline updated post-web-vitals install)
- [ ] `cd frontend && npm run build` succeeds without warnings
- [ ] `frontend/baseline-bundle-sizes.json` committed and reflects new package additions

## Reviewer agent verdict

- [ ] Souji-sweep agent: pass
- [ ] Reviewer agent (style + token + brand sweep): pass
- [ ] Reviewer agent (a11y + reduced-motion sweep): pass

## Final go / no-go

- [ ] All gates above check ✅
- [ ] Branch merged to `sprint/visual-rebirth`
- [ ] `sprint/w2-mapbox-chapters` engaged with `bpsai-pair engage plans/backlogs/sprint-w2-mapbox.md`

If any gate is amber/red, stop and surface — do not start W2 with a broken foundation.

---

## Sign-off

| Gate group | Reviewer | Date | Status |
|------------|----------|------|--------|
| Foundation | _______ | _____ | [ ] |
| Tests | _______ | _____ | [ ] |
| Architecture | _______ | _____ | [ ] |
| Brand integrity | _______ | _____ | [ ] |
| Lint + types | _______ | _____ | [ ] |
| Cross-driver | _______ | _____ | [ ] |
| Documentation | _______ | _____ | [ ] |
| Bundle + perf | _______ | _____ | [ ] |
