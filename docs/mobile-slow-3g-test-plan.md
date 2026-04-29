# Mobile + Slow-3G Manual QA Plan — GoWork Wall

> **Authored:** W5 Driver C, 2026-04-28
> **Audience:** Shawn (or human QA pass before submit).
> **Type:** **manual** plan, real-device + DevTools throttle hybrid.
> **Estimated time:** 30 minutes for the full sweep.

The Wall ships a dedicated mobile experience (`MobileWallFallback`,
W4 Driver B) for phones — Mapbox is too heavy for slow phones, so
mobile gets a card-based scroll instead of the full scrollytelling.
Tablets get a different responsive tier (zoom = 10 vs desktop 11,
W4 Driver D). Slow-3G is the worst-case judge experience.

---

## 1. iPhone (Safari Mobile, real device preferred)

### Setup

- [ ] Real iPhone (iOS 17+) on Wi-Fi (not throttled — separate test below)
- [ ] Open Safari, navigate to `https://gowork.vercel.app`
- [ ] Open Web Inspector (Mac Safari → Develop menu → connected iPhone)
      to watch console

### Verify

- [ ] **MobileWallFallback** renders (NOT the full Mapbox Wall)
- [ ] Exactly 10 chapter cards visible — scroll through all 10
- [ ] Each card has tappable hero / CTA — tap targets ≥ 44×44 pt
      (Apple HIG minimum)
- [ ] Smooth scroll, no jank, 60 fps where possible
- [ ] Layout integrity — no horizontal overflow, no clipped text
- [ ] Ch10 CTA tap → navigates to `/assess`
- [ ] OG card visual unchanged: `/api/og/1` opens, displays PNG
- [ ] No red console errors via Mac Safari Web Inspector

### Mobile Spanish toggle

- [ ] Toggle ES on the phone, verify Spanish labels surface
- [ ] Mobile fallback's chapter cards translate

---

## 2. Android (Chrome Mobile, real device preferred; emulator OK)

### Setup

- [ ] Android phone (Chrome 130+) OR Chrome DevTools mobile emulation
      (Pixel 7 preset)
- [ ] If emulating: `chrome://inspect` for the device console

### Verify

- [ ] On a phone-class viewport (< 768px width): MobileWallFallback
      renders (10 chapter cards) — same as iPhone path
- [ ] On a **tablet-class viewport** (e.g. 1024×1366 — iPad / Pixel
      Tablet): the FULL Mapbox Wall renders, BUT zoom is 10 instead of
      desktop's 11 (W4 Driver D `useResponsiveTier()` contract)
- [ ] Verify the responsive-tier zoom drop by visual inspection: tablet
      shows roughly 1 zoom level wider context per Mapbox frame than
      desktop. The chapter rhythm should still feel cinematic.
- [ ] Tap targets ≥ 48×48 dp (Material Design minimum)
- [ ] Smooth scroll, no jank
- [ ] Ch10 CTA tap → navigates to `/assess`
- [ ] No red console errors

---

## 3. Slow-3G (Chrome DevTools throttle)

### Setup

- [ ] Open Chrome DevTools → Network tab
- [ ] Throttle dropdown → "Slow 3G" (≈ 400 kb/s, 400 ms RTT)
- [ ] Disable cache: DevTools → Network → "Disable cache" checkbox ON
- [ ] Hard reload (Cmd+Shift+R or Ctrl+Shift+R) the production URL

### Verify performance budget

- [ ] **Hero text appears within 3 seconds** of navigation start
      (mark First Contentful Paint via DevTools Performance panel
      or Lighthouse Slow-3G run)
- [ ] **Mapbox lazy-loads after the user scrolls** — the initial
      payload should NOT include the Mapbox JS / tiles. Confirm by
      filtering Network tab for "mapbox" — entries should appear only
      AFTER first scroll, not on initial load.
- [ ] Video assets (if any) do NOT block the main thread; if a hero
      video exists, verify it has `preload="none"` or lazy attribute.
- [ ] Skeleton / placeholder visible until interactive (no white
      flash > 1s)
- [ ] Total Blocking Time < 600 ms (Lighthouse target)
- [ ] Largest Contentful Paint < 4 s on Slow-3G
- [ ] No console errors related to fetch timeouts

### Verify tap-target sizes (touch a11y on slow-3G context)

- [ ] On the throttled view, simulate touch (DevTools → Toggle device
      toolbar → Pixel 7) — the tap targets and scroll behavior should
      remain interactive even before Mapbox loads

---

## 4. Network failure / offline degradation

### Setup

- [ ] DevTools → Network → "Offline" toggle ON

### Verify

- [ ] Page should not crash — show a friendly offline message OR cached
      shell where service-worker is wired
- [ ] Reload while offline shouldn't hang the browser

---

## 5. Sign-off

- [ ] All 10 chapter cards confirmed on iPhone
- [ ] All 10 chapter cards confirmed on Android phone
- [ ] Tablet zoom-10 confirmed on a tablet-class viewport
- [ ] Slow-3G hero-text-budget < 3 s
- [ ] Mapbox lazy-load confirmed
- [ ] No red console errors on any of the above

---

## See also

- `docs/cross-browser-test-plan.md` — desktop browser sweep
- `docs/submission-checklist.md` — T-1 hour gate that consumes this
- `docs/vercel-deploy-runbook.md` — production deploy procedure
