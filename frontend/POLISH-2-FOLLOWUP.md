---
title: polish-2 follow-ups (Drivers D + E output)
status: open
owner: integrator
created: 2026-04-29
---

# polish-2 — Driver D follow-ups

These items require touching surfaces that Driver D's lane explicitly
does not own (chrome / Driver A files, chapter components). They are
documented here so the integrator (or Driver A in a follow-up commit)
can apply them post-merge.

---

## T46 — Lazy-load `BrandMark` inside `SiteFooter`

### Finding

`frontend/src/components/home/SiteFooter.tsx` currently imports the
brand component statically:

```ts
import { BrandMark } from "@/components/wall/BrandMark";
```

The footer is rendered only after the user scrolls below all 8
chapters. The brand-mark is an inline SVG (~88 lines, including hover
animation hooks); shipping it eagerly costs initial-page bytes for a
component that paints near the end of the viewport stack.

### Recommendation

Replace the static import with a `next/dynamic` import keyed off the
footer's intersection observer (or the `IdleStateProvider` already
mounted in the wall). Suggested edit:

```ts
import dynamic from "next/dynamic";
const BrandMark = dynamic(
  () => import("@/components/wall/BrandMark").then((m) => m.BrandMark),
  { ssr: false, loading: () => null },
);
```

If the chunk only loads on intersection, wrap the footer's brand column
in an `<IntersectionObserver>` boundary (or reuse Driver A's existing
deferred-mount helper).

### Verification

After the change:

1. `npm run analyze` confirms the footer chunk bundle no longer
   includes `wall/BrandMark`.
2. Lighthouse FCP improves by the BrandMark byte cost (typically
   1-2 KB gzipped).

### Why Driver D did NOT make this change

`SiteFooter.tsx` is owned by Driver A. Cross-driver edits at this
sprint phase introduce merge conflicts the integrator cannot mediate
in time for the apex push.

---

## T47 — Responsive `<picture>` set on chapter thumbs

### Finding

`ChapterRailTooltip` (Driver A's component) ships full-size JPGs from
`frontend/public/home/chapter-thumbs/0[1-8]-*.jpg`. There is no
`srcset`, no `sizes`, no `loading="lazy"`, and no WebP/AVIF fallback.
On a Pixel 5 the rail tooltip currently transfers ~2.1 MB of JPEGs even
though the rendered preview tops out at 200 px wide.

### Recommendation

Apply the following pattern to `ChapterRailTooltip.tsx`:

```tsx
<picture>
  <source
    type="image/avif"
    srcSet={`${base}-200.avif 200w, ${base}-400.avif 400w, ${base}-800.avif 800w`}
    sizes="(min-width: 1024px) 200px, 50vw"
  />
  <source
    type="image/webp"
    srcSet={`${base}-200.webp 200w, ${base}-400.webp 400w, ${base}-800.webp 800w`}
    sizes="(min-width: 1024px) 200px, 50vw"
  />
  <img
    src={`${base}-400.jpg`}
    srcSet={`${base}-200.jpg 200w, ${base}-400.jpg 400w, ${base}-800.jpg 800w`}
    sizes="(min-width: 1024px) 200px, 50vw"
    loading="lazy"
    decoding="async"
    alt={alt}
    width={400}
    height={225}
  />
</picture>
```

### Build pipeline

Driver D shipped `frontend/scripts/build-chapter-thumbs.mjs` which
emits the 200/400/800 WebP + AVIF variants from the existing JPGs.
Run it post-install (or wire it into the `prebuild` hook) before the
`<picture>` markup will resolve. The script logs each emitted file and
falls back to a no-op (with a console message) when `sharp` is not
installed.

### Why Driver D did NOT make this change

`ChapterRailTooltip.tsx` is owned by Driver A. The script + audit are
Driver D's contribution; the actual `<picture>` markup change must be
applied by the lane owner.

---

## Sign-off

When applied, please remove this file and add a line to
`.paircoder/context/state.md` under "What Was Just Done":

> "polish-2 follow-up T46/T47: lazy-loaded BrandMark + responsive
> picture set applied per Driver D's POLISH-2-FOLLOWUP.md."

---

# polish-2 — Driver E follow-ups

The following items belong to surfaces Driver E does not own
(SiteHeader / SiteFooter / ChapterRailTooltip / chapter content).
The infrastructure (helpers, hooks, listeners) is in place; only the
single-prop wiring remains.

---

## T50 — MuteToggle in SiteHeader (Driver A) + chapter sound triggers (Drivers B/C)

### What Driver E shipped

A cross-driver sound-trigger module:
`frontend/src/lib/home/soundTriggers.ts`. Three named events with their
sound mappings:

| Event name                      | Sound id          | Fired by    |
|---------------------------------|-------------------|-------------|
| `gowork:ch4-step`               | `footstep`        | Ch4 (B/C)   |
| `gowork:ch5-fan-complete`       | `chime`           | Ch5 (B/C)   |
| `gowork:ch7-cliff-cross`        | `calculator-click`| Ch7 (B/C)   |

`installSoundTriggers()` is mounted at `HomePage` and wires every event
through `lib/wall/sound.play(soundId)`. First user gesture
(`pointerdown`/`keydown`) triggers `unlock()` exactly once.

### What Driver A needs to do

`MuteToggle` already exists (`components/wall/MuteToggle.tsx`). The
toggle persists `localStorage["gowork.muted"]` and the sound module
honors it. Mount the component inside `SiteHeader` next to the
language toggle. No prop wiring needed.

### What Drivers B/C need to do

In their chapter components, fire the matching DOM event when the
relevant interaction happens. Use the helpers exported from
`@/lib/home/soundTriggers`:

```ts
import {
  fireChapter4Step,
  fireChapter5FanComplete,
  fireChapter7CliffCross,
} from "@/lib/home/soundTriggers";

// Ch4 — when entering each map step
useEffect(() => fireChapter4Step(), [activeStep]);

// Ch5 — when the slot fan-out animation completes
onFanComplete={() => fireChapter5FanComplete()}

// Ch7 — when the slider crosses the cliff X
if (crossedCliff) fireChapter7CliffCross();
```

### Verification

1. Click MuteToggle once — `localStorage["gowork.muted"] === "false"`.
2. Step into Ch4 → footstep audible (one tap).
3. Watch Ch5 fan-out complete → chime plays.
4. Drag Ch7 slider across the cliff → calculator-click plays.

---

## T57 — PageMeta `batterySaver` chip (Driver A)

### What Driver E shipped

`ScrollVelocityBridge` writes `body[data-battery-low]` when battery
drops below 20% AND not charging (already wired through
`useBatteryAware`). The CSS rule in `home-velocity.css` disables the
cursor flashlight, cursor trail, marquees, and particle effects.

The i18n key `pageMeta.batterySaver` already exists in en/es.

### What Driver A needs to do

In `PageMeta.tsx`, add a small chip that renders when
`useBatteryAware().isLow === true`:

```tsx
import { useBatteryAware } from "@/hooks/useBatteryAware";
import { useTranslation } from "@/hooks/useTranslation";
// ...
const { isLow } = useBatteryAware();
const { t } = useTranslation();
// inside render
{isLow && (
  <span className="page-meta-chip" data-chip="battery-saver">
    {t("pageMeta.batterySaver")}
  </span>
)}
```

### Verification

1. Mock `getBattery()` → `{ level: 0.15, charging: false }`.
2. PageMeta renders the chip.
3. Body picks up `data-battery-low` attr.
4. Marquee / cursor flashlight visually disabled.

---

## T58 — Network-aware video poster in `ChapterRailTooltip` (Driver A)

### What Driver E shipped

A new helper hook: `frontend/src/hooks/useEffectiveConnection.ts`.
Returns `"slow" | "fast" | "unknown"` from
`navigator.connection.effectiveType` with proper SSR guards and live
`change` event subscription.

### What Driver A needs to do

In `ChapterRailTooltip.tsx`, gate the WebP / AVIF preview behind a
`fast`-or-`unknown` check:

```tsx
import { useEffectiveConnection } from "@/hooks/useEffectiveConnection";
// ...
const conn = useEffectiveConnection();
if (conn === "slow") {
  // Render text-only preview — no <picture>, no images.
  return <span className="tooltip-text-fallback">{t(...)}</span>;
}
// Otherwise render the full <picture> set per Driver D's T47 follow-up.
```

### Verification

1. `useEffectiveConnection` test under jsdom (already shipping in
   `src/hooks/__tests__/useEffectiveConnection.test.tsx`).
2. Mock `navigator.connection.effectiveType = "2g"` → tooltip shows
   text-only.
3. Mock `"4g"` → full picture set renders.

---

## T60 — FW DAO bounty link in `SiteFooter` (Driver A)

### Decision

The FW DAO bounty CTA goes in `SiteFooter`'s "For cities" column —
NOT in Ch8. Ch8's single-CTA discipline ("Find your path") must stay
preserved; the DAO bounty audience (city operators / forkers) is
distinct from the worker audience and naturally lands in the
operator-facing "For cities" footer column.

### Spec for Driver A

Add to `SiteFooter.tsx`'s "For cities" column, immediately after
`citiesOpenSource`:

```tsx
<li>
  <a
    href="https://dao.fwtx.city/bounties"
    target="_blank"
    rel="noopener"
    data-analytics="dao-bounty"
  >
    {t("siteFooter.citiesDaoBounties")}
  </a>
</li>
```

### i18n keys

Driver A owns `siteFooter.*`; please add:

```json
// en.json
"citiesDaoBounties": "FW DAO bounties"
// es.json
"citiesDaoBounties": "Recompensas FW DAO"
```

### Verification

1. Click "FW DAO bounties" → opens `https://dao.fwtx.city/bounties`
   in a new tab.
2. Analytics `dao-bounty` event fires (when wired).
3. Ch8 still has exactly ONE CTA ("Find your path / Get your plan").

---

## T55 — Eyebrow numeric variable-font axis (Drivers B/C)

### What Driver E shipped

`EyebrowActiveBridge` writes `data-eyebrow-active="true"` on the
chapter `<section>` that occupies ≥40% of the viewport. The CSS rule
in `home-velocity.css` reads `.eyebrow .num` (or `[data-eyebrow-num]`)
inside `[data-eyebrow-active]` and lifts `font-variation-settings:
"wght" 700`.

### What Drivers B/C need to do (verify only)

For each chapter, the eyebrow chip MUST contain an element with class
`.num` (or `data-eyebrow-num`) wrapping the `01..08` numeric. Check
each `Chapter0NEyebrow.tsx` (or in-chapter eyebrow markup):

```tsx
<div className="eyebrow">
  <span className="num">{`0${chapterNumber}`}</span>
  <span>{label}</span>
</div>
```

If the markup currently renders the number inline as plain text,
extract it to a `<span className="num">` so the CSS rule can target
it. This is a one-prop edit per chapter.

### Verification

1. Scroll Ch4 into ≥40% viewport.
2. The Ch4 eyebrow's `04` text-weight visibly thickens.
3. Scroll to Ch5 — Ch4's `04` returns to weight 400, Ch5's `05`
   thickens.
