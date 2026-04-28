# Cross-Browser Manual QA Plan — GoWork Wall

> **Authored:** W5 Driver C, 2026-04-28
> **Audience:** Shawn (or any human QA pass before submit).
> **Type:** **manual** QA plan. Not automated. Run on real hardware
> against the production Vercel URL the morning of submission.
> **Estimated total time:** 90 minutes for a thorough sweep across all
> 4 browsers (~22 min/browser).

This plan covers the four mainstream desktop browsers GoWork must render
on. Mobile (iOS Safari, Android Chrome) and slow-3G are covered in
`docs/mobile-slow-3g-test-plan.md`.

---

## Why this is manual

The Wall combines View Transitions (Chrome/Edge only at full quality),
Mapbox GL JS (WebGL), CSS `color-mix()`, container queries, and a
3D barrier graph (react-three-fiber). No automated test rig replicates
all five surfaces — a real human eyeball is the gate.

---

## Browser support matrix

| Browser | Min version | View Transitions | color-mix() | WebGL2 | Notes |
|---------|-------------|-------------------|-------------|--------|-------|
| Chrome 135+ | 135 | Full (cinematic) | Yes | Yes | Reference platform |
| Edge 135+ | 135 | Full (cinematic) | Yes | Yes | Chromium — identical to Chrome |
| Safari 17+ | 17.2 | Partial — Safari < 16.4 falls back to standard nav | Yes (16.4+) | Yes | Test on real macOS Safari, NOT Chrome's Safari mode |
| Firefox 130+ | 130 | NOT supported (graceful fallback to standard nav) | Yes (113+) | Yes | View Transitions feature-detected per W4 brief |

---

## Pre-test setup (do once before browser sweep)

- [ ] Production URL is live: `https://gowork.vercel.app` (or custom domain)
- [ ] Open the URL in each browser and bookmark
- [ ] Open DevTools console in each — look for ZERO red errors at first paint
- [ ] System OS reduced-motion is OFF for the first pass; you'll flip ON for one a11y check
- [ ] Tab key on physical keyboard works (for skip-link and tab-order tests)

---

## Per-browser walkthrough

The same set of checks runs in each browser. Use the matrix below — each
row is one assertion the human QA must verify by eyeball or interaction.

### Chrome 135+

#### Pages to walk

- [ ] Home `/` loads, Wall renders Ch1 hero
- [ ] `/assess` loads (assessment wizard step 1)
- [ ] `/plan` loads (after a test assessment OR a seeded plan ID — leave
      this if the demo path doesn't require a /plan visit)
- [ ] `/api/og/1` returns a 1200×630 PNG (visual smoke — open in tab,
      not via curl)
- [ ] `/api/og/10` returns a 1200×630 PNG
- [ ] `/api/og/default` returns a 1200×630 PNG fallback
- [ ] `/bogus-url-xyz` returns 404 with wall-metaphor copy

#### Functional

- [ ] Scroll Ch1 → Ch10 smoothly, no jank, no console errors
- [ ] Ch6 wage slider — drag, watch net-income chart update
- [ ] Ch9 fly-to-Montgomery — click, verify Mapbox camera moves to
      Montgomery coordinates
- [ ] Ch10 CTA — click "Build my plan", View Transition fires
      cinematically, navigates to `/assess`
- [ ] Click browser back from `/assess` — reverse View Transition fires,
      returns to Wall scroll position

#### a11y (keyboard + screen reader)

- [ ] Tab from blank page → "Skip to main content" link appears
- [ ] Tab through Ch1 → Ch10 — each chapter's interactive elements receive
      focus rings
- [ ] Open Chrome's accessibility tree (DevTools → Lighthouse panel →
      Accessibility audit) — score ≥ 0.90
- [ ] (Optional) Run a NVDA / VoiceOver pass on Ch1 hero — verify the
      hero question reads as h1, subhead reads as paragraph

#### Visual regressions

- [ ] Take a screenshot of Ch1 hero, diff against the press-kit
      `wall-chapter-1-hero.png` baseline (manual eyeball OK)
- [ ] Take a screenshot of Ch7 path, diff against
      `wall-chapter-7-path.png`

---

### Edge 135+

(Identical to Chrome — Chromium engine. Run the SAME checklist as Chrome
above. Skip if time-pressed and Chrome was clean — Edge surprises are
rare. But verify at least the home page and Ch10 CTA.)

- [ ] Home `/` loads, Wall renders Ch1 hero (Edge)
- [ ] Scroll Ch1 → Ch10, no jank (Edge)
- [ ] Ch10 CTA fires View Transition (Edge)
- [ ] `/api/og/1` returns PNG (Edge)
- [ ] No console errors (Edge)

---

### Safari 17+

#### Pages to walk

- [ ] Home `/` loads, Wall renders Ch1 hero
- [ ] `/assess` loads
- [ ] `/api/og/1` returns PNG
- [ ] `/api/og/default` returns PNG

#### Functional (Safari-specific)

- [ ] Scroll Ch1 → Ch10 smoothly
- [ ] Ch6 wage slider works
- [ ] Ch9 fly-to-Montgomery works
- [ ] Ch10 CTA — **VERIFY graceful fallback** if Safari < 16.4. View
      Transitions are partial-support; navigation should be a standard
      page change with NO crash, NO blank screen, NO console error.
      Document Safari version used.
- [ ] Mapbox sky layer renders (W2) — should NOT crash; if WebGL2
      unavailable, fall back to flat dark style
- [ ] color-mix() syntax — verify accent colors match design tokens (vs.
      black fallback indicating color-mix isn't parsed)

#### a11y (Safari + VoiceOver)

- [ ] VoiceOver ON (Cmd+F5) — Tab through Wall, verify each chapter's
      heading is announced
- [ ] Skip-to-content link visible on Tab
- [ ] Reduced motion: System Settings → Accessibility → Display →
      Reduce motion ON → reload `/` → verify View Transitions skipped,
      motion-blur off, idle ambient drift off

#### Visual

- [ ] Take screenshot of Ch1, eyeball against Chrome screenshot — no
      catastrophic divergence (slight font-rendering differences are OK)

---

### Firefox 130+

#### Pages to walk

- [ ] Home `/` loads, Wall renders Ch1 hero
- [ ] `/assess` loads
- [ ] `/api/og/1` returns PNG
- [ ] `/api/og/default` returns PNG

#### Functional (Firefox-specific)

- [ ] Scroll Ch1 → Ch10 smoothly
- [ ] Ch6 wage slider works
- [ ] Ch9 fly-to-Montgomery works
- [ ] Ch10 CTA — **VERIFY graceful fallback**. Firefox 130 has no View
      Transitions API. Click should produce a standard navigation to
      `/assess` with NO crash, NO blank screen, NO console error.
      `viewTransitionsPolish.test.ts` already pins this contract.
- [ ] Mapbox WebGL works
- [ ] color-mix() works (Firefox 113+)

#### a11y

- [ ] Tab through Wall — focus rings visible
- [ ] Skip-to-content link visible on Tab
- [ ] Run Firefox's built-in accessibility inspector (DevTools →
      Accessibility tab) — verify roles + labels intact

#### Visual

- [ ] Take screenshot of Ch1, eyeball against Chrome — minor font
      differences OK, layout MUST match

---

## Cross-browser sign-off

After all four browsers pass:

- [ ] Total console errors across browsers: 0
- [ ] Total layout regressions: 0 catastrophic, ≤ 2 cosmetic (font hinting OK)
- [ ] All 4 OG endpoints (`/api/og/1`, `/api/og/10`, `/api/og/default`,
      `/api/og/<bad>` 404) return correct responses in Chrome
- [ ] `/bogus-url` 404 wall-metaphor renders in EN+ES across all 4
      browsers

---

## What to do if a browser fails

| Failure | Severity | Action |
|---------|----------|--------|
| Chrome / Edge regression | P0 | Stop. Fix before submit. This is the reference platform. |
| Safari < 16.4 — View Transitions fail | P3 | Acceptable. Brief documents this. Verify graceful fallback. |
| Firefox — View Transitions fail | P3 | Acceptable. Brief documents this. Verify graceful fallback. |
| Firefox — Mapbox WebGL fail | P1 | Investigate. WebGL2 should work in Firefox 130+. |
| Any browser — console error | P1 | Investigate. Console must be clean for credibility. |
| Any browser — 404 page broken | P0 | Fix. The 404 is the most-likely page a judge hits. |

---

## See also

- `docs/mobile-slow-3g-test-plan.md` — Mobile (iPhone, Android) + slow-3G
- `docs/submission-checklist.md` — T-1 hour checklist
- `docs/vercel-deploy-runbook.md` — production deploy procedure
