# GoWork — Submission Video Take Plan

> **Purpose:** numbered shot list for the HackFW 2026 submission
> video, with multiple-take requirements on the variance-prone shots.
> Authored W5 Driver B.
>
> **Read order:** voiceover script (`docs/submission-video-script.md`)
> first, then walkthrough overlay (`docs/submission-demo.md`), then
> this take plan. Each shot below maps to a chapter window in the
> overlay.

---

## Recording specs (apply to every take)

| Spec | Value |
|------|-------|
| Resolution | **1920×1080** |
| Framerate | **60fps** |
| Capture tool | **OBS** (preferred) · **Loom** · **QuickTime** (macOS fallback) |
| Audio | USB mic (Blue Yeti, Shure MV7, or equivalent) — voiceover read at human pace, no compression artifacts |
| Final encoding | **H.264**, **MP4** container |
| File size cap | **50 MB max** (Devpost limit) — re-encode at lower bitrate if larger |
| Capture monitor | Color-calibrated; brightness ≥ 200 nits so the dark-mode Wall reads on Devpost embeds |
| Background app suppression | Disable notifications, mute system sounds, kill Slack/Discord/Outlook before recording |
| Browser | Chrome 135+ (View Transitions API requirement for shot #11) |

> If using Loom: export at "Highest quality (1080p)" and re-mux
> through HandBrake to confirm 60fps and the 50 MB ceiling. Loom's
> default web-share encode targets 30fps and is too soft for the
> Ch8 reveal.

---

## Numbered shot list

> Format per shot: **#. Window · Chapter · Description · Take count
> · Notes.**

1. **Cold open static frame · Ch1 hero · 5 seconds.** SINGLE TAKE.
   Hold the Ch1 hero ("What's standing between you and a job?") with
   no motion, no scroll, no cursor. The frame is the title card. If
   the cursor drifts into frame, re-shoot.

2. **Ch1 → Ch2 camera dive · Continental → Fort Worth.** MULTIPLE
   TAKES (3) — pick the smoothest. The dive is scroll-driven; an
   uneven scroll makes the dolly stutter. Use a smooth-scroll
   extension (or trackpad inertial scroll) to drive a constant
   downward delta. **Test scroll speed before recording.**

3. **Ch2 dolly to neighborhood · Fort Worth → ZIP 76119.** SINGLE
   TAKE. Continuation of shot #2. The transit-route cyan reveal must
   be visible at full opacity before the camera moves on.

4. **Ch3 → Ch4 wall reveal + 47-form counter ticking up.** SINGLE TAKE
   — **the 47-form counter must hit 47 on screen.** If the
   counter undershoots (lands at 43, 45, etc.), the scroll was too
   fast. Re-shoot at a slower scroll. The counter animation is the
   load-bearing visual for Ch5 — it cannot be cut around.

5. **Ch5 labyrinth animation.** SINGLE TAKE. The labyrinth animation
   is procedural — every take produces an identical result, so one
   clean pass is enough.

6. **Ch6 cliff slider drag.** SINGLE TAKE. Drag the wage slider
   from $7.25 to $25 in **one smooth motion**, ~3 seconds total. The
   cliff color shifts across the page as you drag — that color shift
   is the wow moment, don't oscillate. If the drag jitters, re-shoot.

7. **Ch7 Carlos avatar walking 5-waypoint path.** MULTIPLE TAKES (2)
   — sync footstep audio. The avatar walks at a fixed pace tied to
   scroll progress. If footstep SFX (if present) drifts out of sync
   with avatar position, re-shoot. Pick the take where the avatar
   reaches Week 12 (Hired) cleanly.

8. **Ch8 3D barrier graph reveal (camera tilts up).** MULTIPLE TAKES (3)
   — **this is the wow moment, it must land.** The reveal is
   GPU-dependent; on a warm machine with the constellation already
   loaded the camera tilt is buttery, on a cold machine it can
   stutter. Reload the page between takes so each take starts cold,
   pick the warmest-feeling result. The constellation must rotate at
   least 90 degrees on screen during the reveal.

9. **Ch9 fly-to-Montgomery cross-country dolly.** **MULTIPLE TAKES (5)**
   — this is the longest cinematic in the demo and the most
   variance-prone. Mapbox flyTo can pop-in tiles mid-flight on a
   slow connection, and the camera bezier varies slightly between
   runs. **Pick the smoothest take with no Mapbox tile pop-in
   artifacts.** Take notes between attempts: which run had the
   cleanest tile load, which had the smoothest bezier. Don't settle
   for "good enough" on this shot.

10. **Ch9 return-to-Fort-Worth.** SINGLE TAKE. The return flight is
    the second cinematic beat. Click "Return to Fort Worth" *after*
    the camera has fully landed in Montgomery (don't interrupt the
    flyTo). Hold for the full landing.

11. **Ch10 CTA → View Transitions morph into /assess.** MULTIPLE TAKES (3)
    on **Chrome 135+**. The morph is the closing wow beat;
    it requires View Transitions API support and a warm DOM.
    Re-shoot if the morph degrades to a hard cut (browser stepped
    out of the API mid-flight) or if the destination /assess page
    isn't fully painted when the morph completes. **Chrome only —
    Firefox and Safari fall back to a normal navigation.**

---

## Take-count summary

| Shot | Chapter | Takes | Why |
|-----:|---------|------:|-----|
| 1 | Ch1 hero | 1 | Static frame |
| 2 | Ch1 → Ch2 dive | 3 | Scroll smoothness varies |
| 3 | Ch2 dolly | 1 | Continuation |
| 4 | Ch4 wall reveal + counter | 1 | Counter must hit 47 |
| 5 | Ch5 labyrinth | 1 | Procedural, deterministic |
| 6 | Ch6 cliff drag | 1 | One smooth drag |
| 7 | Ch7 avatar path | 2 | Footstep sync |
| 8 | Ch8 3D graph reveal | 3 | Wow-moment variance |
| 9 | Ch9 fly-to-Montgomery | **5** | Cross-country tile pop-in |
| 10 | Ch9 return | 1 | Second cinematic |
| 11 | Ch10 View Transitions morph | 3 | Chrome morph variance |
| **Totals** | — | **22 takes** | — |

> Plan recording bandwidth assuming **22 takes × 1.5 minutes per
> take** (record + review) = **~33 minutes** of Shawn's time, plus
> setup. Multi-take shots (#2, #7, #8, #9, #11) account for 16 of
> the 22 takes.

---

## Recording day prep

1. **T-30: pre-demo checklist.** Run every check in
   `docs/submission-demo.md` Section 3. The take plan assumes a green
   pre-demo checklist — don't record before that's clean.
2. **T-25: script read-through.** Read
   `docs/submission-video-script.md` Section A–C aloud, with a timer.
   Aim for 4:00–4:15 so the master timeline holds.
3. **T-20: monitor color check.** Pull up the Ch1 hero on the
   recording monitor and verify the dark-mode background isn't
   crushing to pure black. Adjust monitor brightness if so.
4. **T-15: dry-run shots 1–11 without recording.** Walk every shot
   verbally so the demo-runner has muscle memory for slider drag,
   button clicks, and pacing.
5. **T-10: record voiceover first** (audio-only), against the master
   timeline. The screen capture syncs to the voiceover, not the
   other way around.
6. **T-5: record screen captures** in shot order. Multi-take shots
   get re-shot in immediate succession so the demo-runner stays in
   the rhythm.
7. **T-0: review every take.** Mark the chosen take per shot. The
   editor cuts only the marked takes.

---

## Editor handoff

The editor receives:
- 22 raw screen-capture clips (named `shot-NN-takeM.mp4`).
- The voiceover audio track (single WAV / MP3, 4:30 length).
- This take plan (chosen-take markings).
- The captions file (`docs/submission-video.srt`).

Editor's deliverable: `submission-video.mp4` at 1920×1080 60fps,
under 50 MB, with burned-in captions OFF (the SRT ships separately
to Devpost so judges can toggle).

---

## References

- `docs/submission-demo.md` — chapter-locked walkthrough overlay
- `docs/submission-video-script.md` — voiceover script + master
  timeline
- `docs/submission-video.srt` — captions file
- `frontend/public/og/` — static OG fallbacks (1200×630 stills, the
  rescue gallery if a take is unrecoverable)

---

> **Authored:** W5 Driver B. **Branch:** `sprint/w5-submission` →
> `w5-driver-b/demo-video-script`. **Total takes:** 22 across 11
> shots. **Recording bandwidth:** ~33 minutes screen capture + ~10
> minutes voiceover + setup.
