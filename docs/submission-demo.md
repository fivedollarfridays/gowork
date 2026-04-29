# GoWork — Wall Walkthrough Overlay (HackFW 2026 Submission Demo)

> **Audience:** judges & graders watching The Wall live (or via the
> submission video). **Mode:** chapter-locked scrollytelling demo. The
> Wall does the storytelling — this overlay tells the demo-runner *when
> to breathe, when to talk, and what to point at*.
>
> Authored W5 Driver B (sprint/w5-submission). The S13-era staging walk
> (assess → plan → daily) is preserved at `docs/demo-script.md` as the
> Carlos persona reference; this overlay supersedes it for the
> submission demo because the Wall *is* the product surface that
> judges see first.

---

## 0. Setup (one time, before judging starts)

| Item | Value |
|------|-------|
| Demo URL | `https://gowork.fly.dev` (or local: `http://localhost:3000`) |
| Required browser | Chrome 135+ (View Transitions API on by default) |
| GPU | Hardware-accelerated (Three.js Ch8 graph + Mapbox WebGL) |
| Mapbox token | Set as `NEXT_PUBLIC_MAPBOX_TOKEN`; verify before share-screen |
| Audio | Optional — Wall has no required audio; voiceover lives in the video |
| Recording (if recording) | OBS / Loom / QuickTime, 1920×1080 @ 60fps |

> **Total runtime:** 5:40 (340s). Budget for ≤6 minutes including
> on-camera intro / outro. Stop scrolling at Ch10 CTA — do not navigate
> away during the take.

---

## 1. Chapter-locked walkthrough overlay

Each chapter beat lists: **timing window** · **what the Wall is doing
visually** · **what the demo-runner says** · **interaction trigger**
(if any). Scroll progress drives chapter changes — let the Wall
animate; do **not** scroll faster than the timing windows below.

> Pacing rule: when in doubt, *let it breathe*. The Wall is a film,
> not a slide deck.

### Ch1 — Continental (0–30s) · *Hover and breathe*

- **Visual:** America from above, single pin lit on Fort Worth. Hero
  question: "What's standing between you and a job?"
- **Narration:** "What's standing between you and a job? That's the
  question every workforce site dodges. The Wall doesn't."
- **Interaction:** none. **Hold the scroll for the full 30 seconds.**
  Most demo-runners cut this short — that's a mistake. The hero
  question must land before any motion happens.
- **Visual anchor:** the single Fort Worth pin in the dark.

### Ch2 — City Arrival (30–50s) · *Dolly into Fort Worth*

- **Visual:** Camera dives from continental to city altitude. Trinity
  Metro routes thread the map in cyan.
- **Narration:** "Carlos lives here. ZIP 76119. East of downtown.
  Trinity Metro routes thread the city — half of them don't reach the
  warehouses."
- **Interaction:** scroll continuously. Camera tween is scroll-driven.
- **Visual anchor:** cyan transit lines lighting up.

### Ch3 — The Neighborhood (50–70s) · *Meet Carlos*

- **Visual:** Camera dolly continues to a neighborhood block in
  76119. Carlos's portrait beat surfaces.
- **Narration:** "Carlos is 29. Single father of one. Three years
  past a misdemeanor charge — sentence complete. Four years of
  warehouse work behind him. He has $300, no car, and four barriers."
- **Interaction:** scroll. **Pause at the bottom of Ch3 for one
  beat** — let the four-barriers framing land before the wall reveal.
- **Visual anchor:** Carlos's neighborhood label "ZIP 76119 — East
  Fort Worth".

### Ch4 — The Wall (70–110s) · *Four barriers, named one at a time*

- **Visual:** **The wall reveals.** Five offices appear as pins.
  Paths animate between Carlos's home and each office. The 47-form
  counter ticks up alongside the office count.
- **Narration:** "Most workforce sites pretend barriers don't matter.
  We do the math to prove they do. Criminal record. No transit. No
  childcare. Bad credit. Each one is a number — 71-minute commute,
  $1,200/month childcare, 33% of jobs unreachable, 540 credit score."
- **Interaction:** scroll-driven barrier reveal (Ch4a–4d). Don't
  rush — each barrier card lands on its own scroll tick. The 47-form
  counter must finish ticking up before you scroll past Ch5.
- **Visual anchor:** the **47-form counter** ticking up; barrier
  pull-quotes ("I came home with $300 and a daughter…").

### Ch5 — The Labyrinth (110–140s) · *Counter lands at 47*

- **Visual:** Labyrinth animation — five offices wired into a chaotic
  graph of forms, transfers, dead-ends. The "47" counter is now
  static and bright.
- **Narration:** "Five offices. Forty-seven forms. Each one says go
  to the next one. Without GoWork, this is the path. We named it so
  we could replace it."
- **Interaction:** scroll. The labyrinth animation runs scroll-tied.
- **Visual anchor:** "47 forms to fill out" stat label.

### Ch6 — The Math (140–180s) · *Cliff slider drag*

- **Visual:** Camera lands on Amazon FC DFW5. Wage slider appears.
  Cliff chart renders.
- **Narration:** "When more pay means less money. Carlos stocks
  shelves at DFW5 — 71 minutes from home on Bus 4. A $2-an-hour raise
  sounds like a win. The benefits cliff says otherwise."
- **Interaction:** **Drag the wage slider from $7.25 to $25**, slowly,
  in one smooth motion. The cliff color shifts across the entire
  page as you drag — that color shift is the wow moment for Ch6,
  don't rush it.
- **Visual anchor:** cliff chart line dropping at $14/hr (childcare
  subsidy) and $17/hr (SNAP).

### Ch7 — The Path (180–230s) · *Carlos's avatar walks 5 waypoints*

- **Visual:** Carlos's avatar appears on the map. The 12-week path
  draws itself: Home → DPS → HHSC → Legal Aid → Workforce → Hired.
  Trinity Metro Bus 4 + Bus 6 highlight as active legs.
- **Narration:** "Five stops. Twelve weeks. One plan. GoWork
  sequences the same offices Carlos was bouncing between — but in
  the right order, with the right form, at the right week."
- **Interaction:** scroll continuously. The avatar walks at a fixed
  pace tied to scroll. Stay on the chapter long enough for the
  avatar to reach Week 12 / Hired.
- **Visual anchor:** the active leg highlighting cyan as Carlos
  reaches each waypoint.

### Ch8 — The Graph (230–280s) · *THE WALL'S SECRET WEAPON*

- **Visual:** **The 3D barrier graph rises** above downtown Fort
  Worth. Camera tilts up. 33 nodes. 7 categories. Edges glow with
  dependency relationships. The constellation breathes.
- **Narration:** "The wall isn't a list. It's a graph. Every barrier
  connects to two more. Resolve one, and three others move within
  reach. Thirty-three nodes. Seven categories. We mapped the wall so
  we could route around it."
- **Interaction:** scroll, then **stop**. Let the graph rotate on its
  own for 5 seconds. This is the chapter that wins the demo. Don't
  step on it.
- **Visual anchor:** the constellation hovering — the camera tilt-up
  reveal.

### Ch9 — Any City (280–310s) · *Cross-country flight to Montgomery*

- **Visual:** Camera retreats to continental. Two cities lit (Fort
  Worth + Montgomery). Six dotted in (Dallas, Houston, Atlanta,
  Memphis, Charlotte, Birmingham). **"Fly to Montgomery" button.**
- **Narration:** "It works in Fort Worth. It will work in Montgomery.
  It will work where you are. GoWork ships as a city template — Fort
  Worth is the reference deployment. Montgomery is the second."
- **Interaction:** **Click "Fly to Montgomery."** The camera flies
  cross-country (Mapbox flyTo, ~3 seconds). Wait for it to land. Then
  click "Return to Fort Worth" — the return is the second cinematic
  beat. **This is the longest cinematic in the demo and the most
  variance-prone.** If recording: take 5+ tries, pick the smoothest.
- **Visual anchor:** dotted future-city pins; "5,189 tests · 13
  sprints · 2 cities · MIT" stat.

### Ch10 — Find Your Path (310–340s) · *CTA + View Transitions morph*

- **Visual:** Hero CTA "Start your assessment." Footer brand "GoWork
  · Fort Worth, TX." GitHub link.
- **Narration:** "You've seen the wall. You've seen the labyrinth.
  Now skip both. Start your assessment, and we'll hand you a plan
  that's already done the offices, forms, and math."
- **Interaction:** **Click "Start your assessment."** Chrome 135+
  triggers the View Transitions API morph from /the-wall to /assess.
  This is the closing wow beat.
- **Visual anchor:** the morph itself.

---

## 2. Backup paths (if a beat breaks live)

| If this breaks | Do this |
|----------------|---------|
| **Mapbox fails to load** (network blip / token rotation) | The Wall renders a static fallback image for the map layers. Narrate over it: "Fort Worth is rendered live with Mapbox in production; for this demo we're using the cached map tile." Do NOT skip Ch9 — describe the cross-country fly verbally and point at the dotted future cities. |
| **View Transitions don't fire** (Firefox or Safari in audience) | Ch10's morph degrades to a normal navigation. Call it out: "On Chrome 135+ this morphs as a continuous transform — your browser's stepping us through it as a regular nav. Same destination." |
| **Three.js Ch8 graph stutters** (low-end GPU) | The reduced-motion fallback is a static image of the constellation. Narrate over it: "The 3D constellation is interactive on a real machine — what you're seeing is the static rendering of the same 33-node graph." |
| **Wage slider lags on Ch6** | Drag once smoothly $7.25 → $25, don't oscillate. If it still stutters, point at the chart and read the cliffs aloud: "$14/hr childcare subsidy gone. $17/hr SNAP gone." |
| **"Fly to Montgomery" hangs (Mapbox flyTo no-op)** | Reload the page, scroll back to Ch9, and re-click. If it hangs again, narrate: "Production has the second city deployed at gowork-mgm.fly.dev — same engine, same playbook, local data." |
| **Audio missing or out of sync** (recording) | Captions file at `docs/submission-video.srt` is the canonical script. Re-record voiceover only; the screen capture stays. |
| **All else fails** | Switch to the static OG fallback gallery: `/og/1.png` through `/og/10.png` are 1200×630 stills of every chapter. They are the fallback story. |

---

## 3. Pre-demo checklist (T-30 minutes before judging)

- [ ] **T-30: verify Mapbox token loaded.** Hit
      `https://gowork.fly.dev/api/wall/health` (or your deploy's
      health endpoint). Response should include
      `{"mapbox":"ok","tilesetReachable":true}`. If 503, rotate the
      token and redeploy.
- [ ] **T-30: confirm Chrome 135+** is the demo browser. Open
      `chrome://version` in the demo window — anything <135 means
      View Transitions Ch10 morph won't fire. **Do not use Firefox
      or Safari for the live demo.**
- [ ] **T-25: verify hardware-accelerated GPU.** Open
      `chrome://gpu` — "WebGL: Hardware accelerated" must show
      green. If software-rendered, Ch8 will lag.
- [ ] **T-20: slow-network test.** Throttle to "Fast 4G" in DevTools
      and reload `/the-wall`. The Wall must render Ch1 within 3
      seconds. If it doesn't, the production deploy isn't using the
      Edge bundle — investigate before judging starts.
- [ ] **T-15: Spanish toggle test.** Append `?locale=es` to the URL,
      reload. Every chapter heading should swap to ES. If any
      English copy persists, that's a parity bug — flag it but
      proceed in EN for the live demo.
- [ ] **T-10: reduced-motion test.** Toggle system "Reduce motion"
      preference (macOS: System Settings → Accessibility → Display;
      Windows: Settings → Accessibility → Visual effects). Reload.
      Wall should fall back to fades + static graph. Restore the
      preference before the live demo.
- [ ] **T-5: open one tab pre-loaded at `/the-wall`.** Scroll to
      Ch1 and re-load so the page starts at the top. Have a second
      tab ready at `/assess` so the Ch10 morph has somewhere to
      land if View Transitions fail.
- [ ] **T-2: re-warm.** Hit `/the-wall` once more so the SSR cache
      is hot.
- [ ] **T-0: deep breath, smile, hit "Share Screen."**

> If any T-30..T-10 check fails, **fix it before going live.** Backup
> paths exist for live failures, but the pre-demo checklist exists so
> we don't need them.

---

## 4. Timing budget summary

| Chapter | Window | Cumulative | Critical interaction |
|---------|--------|-----------:|----------------------|
| Ch1 Continental | 0–30s | 0:30 | Hold for full 30s |
| Ch2 City Arrival | 30–50s | 0:50 | Scroll-driven dolly |
| Ch3 Neighborhood | 50–70s | 1:10 | Pause at end |
| Ch4 The Wall | 70–110s | 1:50 | 47-form counter ticks up |
| Ch5 Labyrinth | 110–140s | 2:20 | Counter lands at 47 |
| Ch6 The Math | 140–180s | 3:00 | Drag slider $7.25 → $25 |
| Ch7 The Path | 180–230s | 3:50 | Avatar walks to Hired |
| Ch8 The Graph (**secret weapon**) | 230–280s | 4:40 | Stop, let it rotate 5s |
| Ch9 Any City | 280–310s | 5:10 | **Cross-country flight** |
| Ch10 Find Your Path | 310–340s | 5:40 | View Transitions morph |
| **Total** | **5:40** | — | — |

---

## 5. References

- `frontend/src/lib/translations/en.json` — chapter copy (Ch1..Ch10)
- `docs/visual-rebirth-plan.md` — narrative architecture
- `docs/visual-rebirth-briefs.md` — per-sprint briefs
- `docs/demo-script.md` — Carlos persona (assess → plan flow,
  preserved as reference for the post-Wall product walk)
- `docs/submission-video-script.md` — voiceover for the submission
  video (lifts the chapter copy directly)
- `docs/submission-video-take-plan.md` — numbered shot list with
  multiple-take requirements
- `docs/submission-video.srt` — captions file
- `frontend/public/og/[chapter].png` — static OG fallback (1200×630)

---

> **Authored:** W5 Driver B. **Branch:** `sprint/w5-submission` →
> `w5-driver-b/demo-video-script`. **Total runtime:** 5:40 + slack
> within the ≤6:30 submission budget. Every chapter measured.
