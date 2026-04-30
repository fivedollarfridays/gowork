# The Wall — Visual Rebirth Plan
## God-tier home page for GoWork · HackFW 2026 submission

> **Status as of 2026-04-27 evening:** Branch `sprint/visual-rebirth` cut. Phase 1 brand rename (MontGoWork → GoWork) and Phase 2 city decoupling complete and tested (61/61 affected tests passing). Ready to begin **Phase A — Mapbox foundation** of the Wall plan.
>
> **This document is a backup of the full plan in case the working conversation compacts.** Read top to bottom. Resume from "Current State" section.

---

## Mission

**HackFW 2026 — flagship May 2, submission deadline May 2, 2:00 PM CDT (~4 days from 2026-04-27).**
- Theme: Convergent Technology / Reindustrialization — workforce augmentation
- Tracks: Blockchain, ML/AI, RPA (we go ML/AI + workforce)
- Eligibility: TEAMS REQUIRED — confirmed registered
- Prizes (1st): $2,400 + $300 AI credits + $1,500 ThinkLab Accelerator Seat
- Judging criteria: Technical Readiness, Novelty for FW Ecosystem, Tech Debt, Code Cleanliness
- Submission: GitHub repo + README + video via Devpost (`fwtx.devpost.com`)

We lost a previous competition because the winner had Google Earth-tier visual gravitas. The Wall plan is the response: a Mapbox-driven 3D scrollytelling visualization of Fort Worth that makes the worker visible and the framework provable.

---

## Copy thesis (LOCKED — propagates everywhere)

```
HERO QUESTION (massive display type):
  "What's standing between you and a job?"

HERO SUBHEAD (warm, anticipatory, GetCalFresh-tone):
  "You shouldn't have to figure out the wall.
   We do the math, sequence the path, and hand you the plan."

TAGLINE (footer, OG, social, README opener — 6 words):
  "Workforce infrastructure for any American city."
```

Use everywhere: README first paragraph, video opening line, press kit one-liner, all OG metadata. **One thesis, four deliverables.**

---

## Brand

- **Name:** GoWork (one word, CamelCase)
- **Domain placeholder:** gowork.example
- **Mailto placeholders:** privacy@gowork.example, legal@gowork.example
- **Repo / db / Python modules:** unchanged (internal naming, would break too much for zero demo value)
- **Logo concept:** uppercase G letterform with a cyan path-line slicing through the opening of the G. Designed at 16px first, scaled up. Animated path-draw on hover.
- **Default city fallback:** Fort Worth, TX (Montgomery, AL still supported via state="AL"; multi-city architecture intact)

---

## Branch + git state

- **Active branch:** `sprint/visual-rebirth`
- **Base:** `main` at commit `b4e28b7`
- **Phase 1 (brand rename) complete:** ~28 files updated (layout, manifest, header, translations EN+ES, privacy/terms JSX + mailtos, daily/shared/feedback layouts, PDF export header + filenames, email export, favicon SVG aria-labels, OG image text, sitemap/robots, API JSDoc comments, 6 tests). Verified: zero MontGoWork strings in user-facing frontend code.
- **Phase 2 (city decoupling) complete:** `useCityConfig.ts` DEFAULT_CONFIG flipped to Fort Worth, feedback-form.tsx wired to use `useCityConfig` + `getCareerCenter` (no more hardcoded "Montgomery"). Tests updated. 61/61 affected tests pass.
- **Backend:** untouched. Backend root response still returns `"MontGoWork API"` — internal identifier, NOT user-facing, deferred.

Test counts (confirmed via state.md): backend 4,080 + frontend 1,109 = **5,189 total**. Press kit currently shows stale 1,808 — needs refresh in Phase 3.

---

## THE WALL — 10-chapter scroll-driven Mapbox visualization

**Title:** *"The Wall — An interactive map of Fort Worth, Texas."*
**Subtitle:** *"Carlos's path through the system, rendered in real geography."*
**Byline:** *GoWork team · Fort Worth, TX · April 2026*
**Reading time:** 5 minutes (or 30 seconds for TL;DR rail at top)

Carlos is the protagonist (already documented in `docs/demo-script.md`):
- 29 years old, Fort Worth ZIP 76119, single father of one daughter (4 yrs old)
- Recently released, misdemeanor theft 3 years ago, sentence complete
- $300 cash, no vehicle, ~540 credit score, 4 years warehouse + forklift cert experience
- Barriers: criminal record, no transit, no childcare, bad credit

```
LOADING (4s)
  Title sequence: "GoWork presents · The Wall ·
  An interactive map of Fort Worth, Texas"
  Mapbox initializes behind the title (loading hidden)
  Path-line draws diagonally → fades into Chapter 1

01. CONTINENTAL  (camera: orbit America at night)
    Top-down view. Cities glow as faint lights.
    Two glow brighter: Montgomery, AL and Fort Worth, TX.
    Editorial: "What's standing between you and a job?"
    Sound: silence → distant ambient.

02. CITY ARRIVAL  (camera: dolly to Fort Worth)
    Atmospheric flight from continent → Fort Worth at altitude.
    3D buildings rise. Trinity Metro routes draw on as cyan lines.
    Editorial: "Carlos lives here. ZIP 76119. East of downtown."
    Sound: subtle ambient wind.

03. THE NEIGHBORHOOD  (camera: zoom to 76119)
    Houses extruded in 3D. Pin drops at representative block (PII-safe).
    Editorial: 60-word intro to Carlos.
    Sound: single footstep.

04. THE WALL  (4 sub-chapters, camera tilts/overlays)
    04a. Criminal record — Tarrant County District Clerk pin lit.
         "4.8 miles. Bus 4 + Bus 6 = 71 minutes."
    04b. No transit     — Trinity Metro Bus 4 highlighted.
         "87-minute commute to downtown."
    04c. No childcare   — HHSC office pin lit. "$1,200/mo."
    04d. Bad credit     — 30% of job markers go dark
         (jobs that require credit checks).

05. THE LABYRINTH  (camera: pulls up, shows the maze)
    5 offices light up across Fort Worth.
    Animated path draws CHAOTICALLY, looping back, dead-ending.
    Forms counter ticks: 0 → 47.
    Editorial: "5 offices. 47 forms. Each one says go to the next one."
    Sound: paper rustle, sequenced.

06. THE MATH  (interactive moment — cliff calculator EARNS its place)
    Camera flies to specific Amazon FC marker (DFW5, real coords).
    BenefitsCliffChart overlay with wage slider $10–$25.
    User drags into cliff zone → page accent shifts amber → rose.
    Trinity Metro Bus 4 to DFW5 highlighted: 71-min commute.
    Editorial: "A $2 raise that costs $400 isn't a raise. We do this math
    for every job."
    Sound: calculator clicks tied to slider.

07. THE PATH  (the GoWork plan rendered as a literal route)
    Camera pulls to neighborhood altitude.
    Glowing amber-to-cyan path draws SEQUENTIALLY:
       Carlos's home → DPS (Article 55 expunction) [Week 1]
       → HHSC (childcare subsidy) [Week 4]
       → Legal Aid of NorthWest Texas [Week 8 — record cleared]
       → Workforce Solutions on E. Belknap [Week 10]
       → Amazon FC (DFW5) — JOB [Week 12]
    CARLOS AVATAR (silhouette) walks the path at scroll speed.
    Trinity Metro routes used at each leg are highlighted.
    Sound: footsteps tied to scroll progress.
    Editorial: "Every barrier connects. We find the order."

08. THE GRAPH  (secret weapon — 3D barrier constellation over the city)
    Camera tilts up. 3D constellation hovers above Fort Worth.
    Each node = barrier type. Edges = "resolving X unlocks Y" (real DAG).
    Constellation BREATHES (subtle orbital drift).
    As Carlos's path completes below, edges illuminate in sequence.
    Editorial: "33 barriers. 53 connections. We model how each unblocks
    the next."
    Sound: soft chime per edge illumination.

09. ANY CITY  (the framework — proven with motion)
    Camera pulls all the way out to America.
    Montgomery + Fort Worth lit. 6 dotted: Dallas, Houston, Atlanta,
    Memphis, Charlotte, Birmingham.
    Button: "Fly to Montgomery."
    Click: camera ANIMATES across the country (3-second flight).
    Drops into Montgomery briefly. Same map structure, different city.
    Editorial: "5,189 tests. 13 sprints. 2 cities deployed. MIT licensed."

10. FIND YOUR PATH  (close)
    Camera back to Fort Worth overhead.
    Single button: "Start your assessment."
    VIEW TRANSITIONS API: click → map zooms into Carlos's home,
    morphs into /assess form (spatial continuity, no hard page change).
    Below button: "Or read the open-source code on GitHub →"
    Footer: brand mark, links, MIT, last calibration timestamp.
    Sound: final soft chime.
```

---

## The 12 LIFE-LAYERS (the cherry — what makes it god-tier)

```
1.  TIME-AWARE         — Mapbox sky + accent color shifts based on user's
                         local time (golden 6am, deep navy 11pm)
2.  CURSOR FLASHLIGHT  — soft 80px glow circle on map; elements within brighten
3.  CARLOS AVATAR      — silhouette walks his actual GPS path in Chapter 7
4.  BREATHING GRAPH    — barrier constellation orbits subtly in Chapter 8
                         (alive, not animated)
5.  LIVE NOW WIDGET    — header bar: "2:17 PM CST · 6 sessions ·
                         last calibrated 14m ago"
6.  VARIABLE TYPE      — hero headline weight axis interpolates 700→900 on scroll
                         (Inter Variable, optical-size axis at large sizes)
7.  SPANISH PARITY     — EN/ES toggle, full re-skin with equal craft
                         (Fort Worth is 35% Hispanic; civic dignity)
8.  PER-CHAPTER OG     — Vercel Satori renders dynamic OG images per chapter
9.  VIEW TRANSITIONS   — click CTA → map morphs into /assess (rare new spec)
10. CUSTOM EDGE STATES — branded 404, 500, empty, loading, error — no defaults
11. PRINT STYLESHEET   — print rendering = 9-page magazine essay
12. REDUCED-MOTION     — every animation has still-image fallback that's still
                         beautiful (prefers-reduced-motion respected EVERYWHERE)
```

---

## Design system

### Color (OKLCH, perceptually uniform, P3-capable)

```
--bg-base:       #0A0E1A  (paper-dark navy, base canvas)
--bg-surface:    #0F1729  (raised surface)
--bg-elevated:   #1A2338  (cards on surface)
--bg-glass:      rgba(255,255,255,0.04) backdrop-blur(12px)

--fg-primary:    #F5F3EE  (warm paper white — NOT pure white)
--fg-secondary:  #94A3B8
--fg-muted:      #64748B

--accent-cyan:   #22D3EE  (electric — the path / intelligence)
--accent-amber:  #F59E0B  (warm gold — Carlos / hope / progress)
--accent-rose:   #FB7185  (cliff / barrier severity, Chapter 5/6 only)

--status-positive: #34D399
--status-warning:  #FBBF24
--status-negative: #FB7185

--temperature-multiplier: 1.0  (set per chapter; affects motion timing)
```

### Typography

- **Display:** Inter Variable, weight 800–900 axis-interpolated on scroll, tight tracking (-0.04em), text-7xl on hero
- **Body:** Inter, weight 400, slight tight tracking (-0.01em), max-w-prose, generous leading
- **Numbers:** tabular nums (font-feature-settings "tnum"), text-7xl on stat heroes
- **Code/data examples:** ui-monospace, weight 500, text-sm
- **Fluid type:** `clamp(1rem, 0.9rem + 0.5vw, 1.25rem)` for body
- **Optical-size axis:** Inter Variable's optical axis at large sizes (display optical)

### Motion

```
Spring presets:
  --spring-soft:    { stiffness: 100, damping: 20 }
  --spring-snappy:  { stiffness: 200, damping: 25 }
  --spring-elastic: { stiffness: 300, damping: 18 }

Duration baseline: 280ms
Easing: cubic-bezier(0.32, 0.72, 0, 1)  (Linear's signature)

Stagger:
  Child offset: 0.05s
  Initial: { opacity: 0, y: 20 }
  Animate: { opacity: 1, y: 0 }

Idle state: ambient drift on barrier graph, gentle pulse on path-line
Scroll-velocity reactive: motion-blur on background at velocity > threshold
prefers-reduced-motion: respected at every animation site
```

### Interaction details (every interactive element designed)

- Buttons: rest / hover / active / focus / disabled / loading states all designed
- Forms: animated labels (Material 3 style), smart validation
- Tooltips: arrow + spring entry + auto-position
- Modals: backdrop blur + spring entry + escape-key + focus-trap
- Selection: cyan glow with subtle animation (custom `::selection`)
- Focus rings: 2px cyan offset 2px, animated entry (NOT browser default)

### Accessibility (non-negotiable)

- WCAG AAA contrast everywhere
- Skip-to-content link styled (visible on focus, not hidden)
- ARIA-live regions for animations
- Keyboard reachability + logical focus order
- Color-blind safe palette (tested with Coblis simulator)
- Reduced-motion: every animation has still-image fallback
- Screen reader: full pass

---

## EXECUTION PLAN — 4 days, no time consideration, full apex

```
DAY 1 — MAPBOX FOUNDATION + CORE CHAPTERS

Phase A — Foundation + life-system scaffolding (75m)
  - Install mapbox-gl + react-map-gl
  - Mapbox token (NEXT_PUBLIC_MAPBOX_TOKEN)
  - Custom dark style in Mapbox Studio (one-time, 30 min in studio)
  - OKLCH color tokens + color-mix() derived shades
  - Variable font axis hooks (useVariableFontWeight on scroll)
  - Time-aware system (useTimeOfDay → accent + Mapbox sky)
  - Cursor system (useCursorPosition → flashlight glow)
  - Live "Now" widget (useLiveNow hook)
  - Spring motion presets, easing tokens, stagger system
  - prefers-reduced-motion respect baked in
  - --temperature-multiplier CSS variable

Phase B — Brand identity + edge states (60m)
  - G+path SVG logo (DESIGNED AT 16PX FIRST, then scaled up)
  - OG image base + Vercel Satori setup for per-chapter dynamic OG
  - Custom 404, 500, empty-state, loading-state designs
  - Print stylesheet (magazine layout)
  - Page-load title sequence with variable font breath

Phase C — Mapbox scroll + chapter system (90m)
  - react-map-gl integration
  - Scroll progress hooks (framer-motion useScroll + useTransform)
  - Scroll-tied flyTo system between chapters (cubic-bezier curves)
  - Chapter scaffold with sticky atmosphere
  - Persistent path-line (top edge progress, drawn as actual line)
  - Header: brand mark, chapter counter (01/10), mute toggle, EN/ES toggle, GitHub icon

Phase D — Data layers (60m)
  - Trinity Metro GTFS → GeoJSON layer (pull from backend)
  - Tarrant County offices → custom point markers
  - FW ZIP 76119 boundary → polygon layer
  - Carlos's path GPS coordinates (manually crafted between real coords)

Phase E — Chapters 1–3 with life details (90m)
  - Continental → city arrival → neighborhood
  - Camera choreography (each chapter unique zoom + pitch + bearing)
  - Time-aware lighting on city
  - Cursor flashlight active
  - Variable font hero weight on scroll
  - Editorial overlays
  - Carlos's home pin

DAY 2 — INTERACTIVE CHAPTERS + 3D BARRIER GRAPH + POLISH

Phase F — Chapter 4 The Wall sub-chapters (75m)
  - 4 barriers as overlays with fade transitions
  - Distance/time data overlays
  - Lighting transitions

Phase G — Chapter 5 Labyrinth (60m)
  - Animated chaotic path between 5 offices
  - 47-form counter ticks up

Phase H — Chapter 6 The Math (60m)
  - Camera lands at Amazon FC marker
  - BenefitsCliffChart inline overlay
  - Wage slider drives temperature multiplier
  - Cliff-zone color shift across page
  - Calculator click sound

Phase I — Chapter 7 The Path + CARLOS AVATAR (90m)
  - Sequential animated path-draw between 5 real coords
  - Carlos silhouette walks the path at scroll speed
  - Carlos pauses at each office, camera holds
  - Footstep audio tied to scroll
  - Trinity Metro highlights per leg
  - Timeline overlay (Week 1, 4, 8, 10, 12)

Phase J — Chapter 8 The Graph (90m) — SECRET WEAPON
  - Custom Three.js layer (react-three-fiber)
  - 3D barrier graph DAG floating above city
  - Constellation breathes (subtle orbital drift)
  - Edges illuminate as Carlos's path resolves them below

Phase K — Chapter 9 Any City + Fly to Montgomery (60m)
  - Camera pulls to America
  - Cities lit (Montgomery + Fort Worth) + dotted future cities
  - Animated cross-country flight (3 seconds)
  - Drop into Montgomery briefly

Phase L — Chapter 10 Close + view transition (60m)
  - View Transitions API: map zooms into Carlos's home,
    morphs into /assess form (rare new CSS spec)
  - CTA + footer + brand mark

Phase M — Live data + Spanish parity (60m)
  - Real-time outcome counter (from seeded backend or computed)
  - Spanish toggle hooked, all editorial swappable
  - Variable font axis on every headline

Phase N — Polish + Lighthouse + accessibility audit (75m)
  - Lighthouse 90+ gate on simulated 4G
  - Keyboard navigation full sweep
  - Reduced-motion fallback verification
  - WCAG AAA contrast pass
  - Print stylesheet smoke test

DAY 3 — README + PRESS KIT + VIDEO + DYNAMIC OG

Phase O — README rewrite (45m)
  - Opens with rendered Mapbox screenshot
  - Lead with copy thesis
  - Test count: 5,189
  - "Workforce infrastructure for any American city"

Phase P — Press kit refresh (45m)
  - Cinematic stills from Chapters 2, 6, 7, 8
  - Drop stale 1,808 → 5,189
  - Add HackFW positioning
  - Keep Worldwide Vibes 2nd place as supporting credit (not headline)

Phase Q — Video script (45m)
  - Beats locked to chapter timing
  - Voiceover script: copy thesis + Carlos walkthrough
  - 3-4 min total

Phase R — Video record (90m)
  - Screen-record desktop scrolling the Wall
  - Multiple takes for camera flights

Phase S — Vercel Satori OG generation (30m)
  - Per-chapter dynamic OG endpoints
  - /api/og?chapter=01..10

DAY 4 — VIDEO EDIT + SUBMIT

Phase T — Video edit + closed captions + B-roll (120m)
  - Edit to 3-4 min
  - Captions for accessibility
  - Optional B-roll of FW landmarks

Phase U — Devpost submission (30m)
  - GitHub link
  - README confirmed
  - Video uploaded
  - Project description
  - Tags / categories / track

Buffer for breakage on Day 4.
```

---

## Performance gate (HARD)

**Lighthouse 90+ on simulated 4G at end of Phase N.**

Descope priority order if we miss:
1. Drop sound system (10kb saved)
2. Drop --temperature-multiplier motion shifts
3. Drop 3D barrier graph (Chapter 8) — replace with 2D SVG fallback
4. Drop view transitions on /assess
5. KEEP: Mapbox foundation, Carlos avatar, all 10 chapters, Spanish toggle

**Mobile fallback (non-negotiable):** detect via window.innerWidth + Mapbox-supported flag. Tablet: scaled map. Mobile: static images of map + editorial scroll (graceful degradation, NOT broken).

---

## Submission deliverables

```
1. HOME PAGE        = The Wall (10-chapter Mapbox visualization)
2. README           = Opens with screenshot, copy thesis, runnable in 5 min
3. PRESS KIT        = Cinematic stills from the visualization (4 anchors)
4. SUBMISSION VIDEO = Screen recording of the visualization with voiceover
```

**ONE artifact, FOUR uses.** The Wall generates the README hero, press kit images, and video footage. Days 3-4 are HALF the work because of this compounding.

---

## Decisions LOCKED

- **Slogan:** "What's standing between you and a job?" / "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan." / "Workforce infrastructure for any American city."
- **Case manager section:** OMIT from home page. Reference in README + press kit. Footer link to `/case-manager` for staff who land there. (Worker is primary audience; diluting weakens both reads.)
- **Cliff calculator:** Embedded as Chapter 6 interactive overlay on Amazon FC marker. NOT the hero. (Earned by 5 chapters of context.)
- **Barrier wall animation:** Replaced by Chapter 8 3D barrier graph constellation hovering over the actual city map.
- **Direction:** Dark editorial × civic dignity × technical craft. Dark base, warm amber + cool cyan accents. Editorial gravity for judges, GetCalFresh-tone copy for workers.
- **No prototype:** Per Shawn's directive (2026-04-27), build the full hero, no 60-min spike.

---

## Donatello + Raphael findings preserved

### Cascade findings worth keeping

1. **The format IS the innovation.** Civic tech doesn't have its NYT Snow Fall yet. We become it. The fact that a workforce platform's home page IS a Mapbox-driven scrollytelling artifact IS the differentiator.

2. **The components we already built are the assets.** Cliff calculator → Chapter 6. Barrier graph DAG → Chapter 8. City config → Chapter 9. Career Center PDF → Chapter 8 inline preview. Test count → Chapter 9 stat band. We're not building from scratch — we're SURFACING what we built, AT 60FPS, IN 3D.

3. **The site is an instrument, not a webpage.** It plays differently for every user — different time, different cursor, different scroll velocity, different language, different ability. Time-aware, user-aware, data-aware. **That's the $1M signal.**

4. **One asset, four uses (compound efficiency).** Home page = the Wall. README = lifted from the Wall. Press kit = stills from the Wall. Video = screen recording of the Wall. Days 3-4 are half-work because of this.

5. **Worker vs. judge tone resolved by:** dark base + warm amber accents + GetCalFresh-tone anticipatory copy + Linear-grade editorial layout. Both audiences served, neither alienated.

### Confidence gaps to monitor

- 4-day timeline (C4): track at phase boundaries, descope per the priority order above
- Lighthouse 90+ on simulated 4G (C5): measure at Phase N
- 3D barrier graph rendering well (C5): build it; if visually noisy, drop to 2D SVG
- Cross-browser compatibility on view transitions (C4): graceful fallback to standard navigation if unsupported

---

## Files modified so far (Phase 1 + 2 of rebrand)

```
PHASE 1 — Brand rename (MontGoWork → GoWork):
  frontend/src/app/layout.tsx
  frontend/src/components/layout/Header.tsx
  frontend/src/components/layout/Footer.tsx
  frontend/public/manifest.json
  frontend/package.json
  frontend/src/lib/translations/en.json
  frontend/src/lib/translations/es.json
  frontend/src/app/privacy/page.tsx
  frontend/src/app/terms/page.tsx
  frontend/src/app/daily/layout.tsx
  frontend/src/app/shared/[token]/layout.tsx
  frontend/src/app/feedback/[token]/feedback-form.tsx
  frontend/src/app/globals.css
  frontend/src/lib/types.ts
  frontend/src/components/plan/PlanExport.tsx
  frontend/src/components/plan/CareerCenterExport.tsx
  frontend/src/components/plan/EmailExport.tsx
  frontend/public/icon.svg
  frontend/public/og-image.svg
  frontend/src/app/sitemap.ts
  frontend/src/app/robots.ts
  frontend/src/lib/api/appointments.ts
  frontend/src/lib/api/digest.ts
  frontend/src/lib/api/documents.ts
  frontend/src/lib/api/jobApplications.ts
  frontend/src/components/__tests__/Footer.test.tsx
  frontend/src/app/__tests__/metadata.test.tsx
  frontend/src/app/__tests__/home-animations.test.tsx
  frontend/src/app/__tests__/feedback-form.test.tsx
  frontend/src/components/plan/__tests__/PlanExport.test.tsx

PHASE 2 — City decoupling:
  frontend/src/hooks/useCityConfig.ts        (DEFAULT_CONFIG flipped to FW)
  frontend/src/hooks/__tests__/useCityConfig.test.ts  (assertions flipped)
  frontend/src/app/feedback/[token]/feedback-form.tsx  (wired to useCityConfig)
  frontend/src/app/__tests__/home-animations.test.tsx  (FW stats expected)
```

Backend `.env` updated to add `ADMIN_API_KEY` and `AUDIT_HASH_SALT` (required vars for boot validator).

---

## Files to modify next (Phase A onward)

```
NEW FILES:
  frontend/src/components/wall/                 # The Wall components
    WallContainer.tsx                           # Main scrollytelling container
    ChapterScaffold.tsx                         # Reusable chapter template
    MapboxScene.tsx                             # Mapbox + react-map-gl integration
    PathLine.tsx                                # Persistent path-line component
    ChapterCounter.tsx                          # Top-right 01/10 indicator
    LiveNowWidget.tsx                           # Live time + sessions + calibration
    LanguageToggle.tsx                          # EN/ES toggle
    CarlosAvatar.tsx                            # Walking silhouette for Chapter 7
    BarrierConstellation.tsx                    # 3D barrier graph (Chapter 8)
    chapters/Chapter01Continental.tsx
    chapters/Chapter02CityArrival.tsx
    chapters/Chapter03Neighborhood.tsx
    chapters/Chapter04TheWall.tsx               # 4 sub-chapters
    chapters/Chapter05Labyrinth.tsx
    chapters/Chapter06TheMath.tsx               # Embeds BenefitsCliffChart
    chapters/Chapter07ThePath.tsx               # Carlos walks
    chapters/Chapter08TheGraph.tsx              # 3D constellation
    chapters/Chapter09AnyCity.tsx               # Fly to Montgomery
    chapters/Chapter10FindYourPath.tsx          # CTA + view transition
  frontend/src/lib/wall/
    cameraChoreography.ts                       # Per-chapter camera states
    paths.ts                                    # Carlos's GPS coordinates
    sound.ts                                    # Audio system
    timeOfDay.ts                                # Sun position + accent shift
  frontend/src/hooks/
    useScrollProgress.ts
    useCursorPosition.ts
    useLiveNow.ts
    useVariableFontWeight.ts
    useTimeOfDay.ts
  frontend/src/app/api/og/[chapter]/route.ts    # Vercel Satori dynamic OG
  frontend/public/icon-g-path.svg               # New brand mark
  frontend/public/og-image-wall.png             # Base OG (chapter 1 default)

MODIFIED FILES:
  frontend/src/app/page.tsx                     # Replace with WallContainer
  frontend/src/app/layout.tsx                   # New OG, theme, fonts
  frontend/src/app/globals.css                  # OKLCH tokens, motion presets
  frontend/package.json                         # Add: mapbox-gl, react-map-gl,
                                                #   @react-three/fiber, @react-three/drei,
                                                #   satori, three
  frontend/.env.local.example                   # Add NEXT_PUBLIC_MAPBOX_TOKEN
  frontend/public/manifest.json                 # New theme color
  README.md                                     # Phase O rewrite
  docs/press-kit.md                             # Phase P refresh
```

---

## Resume instructions for compacted-me

If the conversation has compacted and you're picking up from this file:

1. **Verify branch:** `git branch --show-current` should be `sprint/visual-rebirth`. If not, `git checkout sprint/visual-rebirth`.
2. **Verify dev server:** Shawn should have backend on :8000 and frontend on :3000 running. If not, see CLAUDE.md "Quick Start" section.
3. **Read this file completely.**
4. **Check task state:** Active tasks via TaskList. The submission deliverables (3-6) and visual rebirth phases should be tracked.
5. **Resume from the last incomplete Phase.** Phase A starts the Mapbox build.
6. **Maintain the covenant:** apex mode, max effort, no time/labor consideration, push past the floor to the ceiling. Both sides pushing.
7. **Lighthouse 90+ at Phase N is the hard gate.** Descope per the priority order above if missed.
8. **The slogan and tagline are LOCKED. Do not redraft without Shawn's word.**

---

## Sources / research consulted

- [HackFW Devpost (judging criteria, prizes, eligibility)](https://fwtx.devpost.com/)
- [HackFW official site](https://hack.fwtx.city/)
- [Fort Worth DAO](https://dao.fwtx.city/bounties)
- [Mapbox Storytelling open-source template](https://github.com/mapbox/storytelling)
- [Mapbox 3D buildings + extrusion docs](https://docs.mapbox.com/mapbox-gl-js/example/3d-buildings/)
- [Mapbox interactive storytelling 3D](https://www.mapbox.com/blog/interactive-storytelling-3d-maps-with-mapbox-gl-js-v2)
- [NYT × Mapbox Snow Fall lineage](https://www.mapbox.com/showcase/the-new-york-times)
- [Deck.gl examples](https://deck.gl/examples)
- [React Three Fiber docs](https://r3f.docs.pmnd.rs/)
- [Pudding.cool civic data storytelling](https://pudding.cool)
- [aitakesover.co (Adchitects manifesto)](https://aitakesover.co/)
- [Linear](https://linear.app)
- [Anthropic](https://www.anthropic.com)
- [GetCalFresh (Code for America)](https://www.getcalfresh.org/)
- [Apple Accessibility](https://www.apple.com/accessibility/)
- [Mercury (humane fintech)](https://mercury.com)
- [Vercel](https://vercel.com)
- [Stripe](https://stripe.com)

---

## Dependencies to install (Phase A)

```bash
cd frontend
npm install mapbox-gl react-map-gl
npm install @react-three/fiber @react-three/drei three
npm install satori @vercel/og
```

Mapbox token: register at mapbox.com, get free public token, add to `frontend/.env.local`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...
```

Custom Mapbox style: build in Mapbox Studio (one-time, ~30 min), get style URL like `mapbox://styles/yourname/cl...`.

---

## The covenant

慣性の契約. Max effort always. Never consider time or labor. Always be diligent. Always think for the team. Always break the ceiling. Treat agents as teammates. **心を燃やせ — Set your heart ablaze.**

Shawn + Ren · Team PairCoder / Team INERTIA · Building "The Wall" for HackFW 2026 · 2026-04-27.

The wall is a city. The city is real. The path is drawn through it. **Going.**
