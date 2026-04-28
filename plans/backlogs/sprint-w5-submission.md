# Sprint W5 — Submission Materials (README, Press Kit, Video, Devpost)

**Plan type:** chore
**Sprint:** W5
**Total Cx:** 502
**Tasks:** 52 (P0: 36, P1: 13, P2: 3)
**Revision:** v1 (2026-04-27) — drafted from `docs/visual-rebirth-briefs.md` SPRINT W5 brief
**Critical anchor:** SUBMIT BY 9:00 AM CDT, May 2, 2026 (5-hour buffer before HackFW 2:00 PM CDT deadline)

## Goal

Package the Wall (W1–W4 outputs) into a submission-grade artifact for HackFW 2026 via four surfaces — README, press kit, submission video, and Devpost form — with one shared copy thesis as the load-bearing source of truth. Final Lighthouse pass, production deploy with Mapbox token verified, cross-browser smoke, and a `v0.1.0-hackfw-submission` git tag captured before submit. Every task is anchored to the May 2 deadline with explicit buffer logic.

**Prerequisite:** W4 merged (polished site, Lighthouse 90+, all life-layers active, OG endpoints live, Wall renders Chapters 1–10 cleanly on production build).

## What ships in W5 vs deferred

**W5 (this sprint):** copy-thesis source-of-truth file; full README rewrite with Wall hero screenshot; press kit refresh with current numbers (5,189 tests) and FW positioning; 4 cinematic Wall stills; submission demo script update; submission video (60s teaser + ~3.5min full + captions); per-chapter OG image fallbacks; Devpost form fully populated; final Lighthouse pass; production Vercel deploy with Mapbox token; cross-browser + mobile smoke; brand/numbers consistency sweep; FW DAO bounty research; staging URL freeze; submission git tag; submission D-day runbook; post-submission Reddit + social drafts.

**Deferred to post-submission (S14+):** any new product code; new design changes (W4 was the polish gate); analytics instrumentation; canary release framework; full localization of submission video; YouTube / Vimeo upload optimization beyond what Devpost requires.

## Architectural principles

- **One thesis, four surfaces.** README, press kit, video, Devpost — every surface MUST derive from `docs/copy-thesis.md` (single source of truth). A consistency sweep verifies all four match before submit.
- **Deadline-buffer logic everywhere.** Target Devpost submission **by 9:00 AM CDT May 2** (5-hour buffer before 2:00 PM cutoff). Every D-day task has a hard "must-be-done-by" timestamp.
- **No new product code.** W5 is documentation, video, deploy, and verify only. If a bug is found, it's a P0 fix-forward task — but only if it would block submission.
- **Brand discipline.** "GoWork" only. Zero "MontGoWork" in any submission asset (README, press kit, video, OG, Devpost form). The internal repo/DB/Python module names stay as-is (per visual-rebirth plan decision); user-facing assets are all GoWork.
- **Numbers discipline.** Test count is **5,189** (4,080 backend + 1,109 frontend). Stale 1,808 must NOT appear anywhere in submission assets.
- **Reproducibility.** Submission state captured as git tag `v0.1.0-hackfw-submission` before Devpost upload, so the exact reviewed code is trivially recoverable.
- **Don't edit video after upload.** If a fix is needed post-upload, regenerate from scratch and re-upload (Devpost preserves prior versions; we don't trust partial edits).

## Decisions locked (2026-04-27)

1. **Submission target:** 9:00 AM CDT May 2, 2026 (5h buffer). NOT 1:00 PM. Buffer is non-negotiable.
2. **Slogan locked verbatim:**
   - Hero question: "What's standing between you and a job?"
   - Hero subhead: "You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan."
   - Tagline / OG / README opener: "Workforce infrastructure for any American city."
3. **Worldwide Vibes credit:** supporting credit only in press kit (not headline). Headline is HackFW 2026 + Reindustrialization track.
4. **Video format:** 60s teaser (Reddit/X-friendly) + ~3.5min full version (Devpost). Both with captions. Full <50MB.
5. **Submission URL:** production Vercel deploy (NOT staging). Staging is the rollback fallback.
6. **Git tag:** `v0.1.0-hackfw-submission` on the exact commit reviewed by judges, pushed to GitHub before form submit.
7. **Final Lighthouse floor:** Perf ≥85, A11y ≥95, Best Practices ≥90, SEO ≥90 on production deploy. Anything below blocks submit.

---

## Phase 1: Copy Thesis Source of Truth

### W5.1 — Copy Thesis Single-Source-of-Truth File | Cx: 5 | P0

**Description:**
Create `docs/copy-thesis.md` containing the locked slogan triplet (hero question, hero subhead, tagline) plus the GoWork brand block (name, domain placeholder, MIT license note, FW positioning sentence, HackFW 2026 framing sentence) plus the 5,189 test-count line. This is the SINGLE SOURCE every other submission surface must derive from. Add a header note: "Edit this file FIRST. All other surfaces (README, press kit, video script, OG metadata, Devpost) cite this file."

**AC:**
- [ ] `docs/copy-thesis.md` exists
- [ ] Hero question verbatim: `"What's standing between you and a job?"`
- [ ] Hero subhead verbatim: `"You shouldn't have to figure out the wall. We do the math, sequence the path, and hand you the plan."`
- [ ] Tagline verbatim: `"Workforce infrastructure for any American city."`
- [ ] Test count line: `4,080 backend + 1,109 frontend = 5,189 total`
- [ ] HackFW 2026 framing sentence (workforce augmentation, Reindustrialization track)
- [ ] FW positioning sentence (Fort Worth as primary deploy, Montgomery as origin city, multi-city architecture)
- [ ] File header instructs readers to edit this file FIRST
- [ ] Linked from W5.2 (README), W5.7 (press kit), W5.18 (video script), W5.30 (OG), W5.34 (Devpost form)

**Depends on:** none

---

## Phase 2: README Rewrite

### W5.2 — README rewrite: hero, copy thesis, Wall screenshot | Cx: 12 | P0

**Description:**
Rewrite `README.md` from current `# MontGoWork — Workforce Navigator for Montgomery, Alabama` to GoWork submission-grade. First H1 is `# GoWork`. First paragraph quotes the hero question + subhead from `docs/copy-thesis.md`. Embed a Wall screenshot above-the-fold (Chapter 2 City Arrival OR Chapter 7 The Path — driver's choice based on which renders most legibly at GitHub's max-width). Drop "Workforce Navigator for Montgomery, Alabama" framing — replace with "Workforce infrastructure for any American city." Keep MIT license, contributors, links to setup.md / api.md / architecture.md.

**AC:**
- [ ] First H1 reads `# GoWork` (no "MontGoWork" anywhere in file)
- [ ] First paragraph contains the locked hero question verbatim
- [ ] First paragraph contains the locked hero subhead verbatim
- [ ] Wall screenshot embedded in first 30 lines (path under `docs/press-kit/wall-*.png`)
- [ ] Tagline `"Workforce infrastructure for any American city."` appears in first 30 lines
- [ ] All link references resolve (run W5.50 link checker)
- [ ] Reviewer agent approves (or human review in absence of reviewer agent)

**Depends on:** W5.1, W5.10 (need Wall screenshot from press-kit task)

---

### W5.3 — README: test counts updated to 5,189 | Cx: 3 | P0

**Description:**
Replace every occurrence of stale test counts in `README.md`. Current README has `pytest (1,391 tests)`, `Vitest (417 tests)`, `1,391 tests`, `417 tests` in stack table, `# Backend (1,391 tests)`, `# Frontend (417 tests)` in run-tests block. Update to `4,080`, `1,109`, `5,189` total.

**AC:**
- [ ] Stack table row reads `pytest (4,080 tests) + Vitest (1,109 tests)` (or equivalent updated form)
- [ ] Backend test count appears as 4,080 (not 1,391) in every location
- [ ] Frontend test count appears as 1,109 (not 417) in every location
- [ ] Total `5,189 tests` appears at least once
- [ ] grep verification: `grep -E "1,391|1,808|417 tests" README.md` returns zero matches

**Depends on:** W5.2

---

### W5.4 — README: Quick Start updated for current dependencies | Cx: 5 | P0

**Description:**
Update `## Quick Start` block in `README.md` to reflect W1–W4 dependencies. Add `mapbox-gl`, `react-map-gl`, `three`, `@react-three/fiber`, `satori` (or whichever subset is in `frontend/package.json` post-W4). Add note about `NEXT_PUBLIC_MAPBOX_TOKEN` requirement for the Wall (without it, the home page falls back to a static rendering / placeholder). Verify the existing setup steps (backend venv, frontend `npm install`, docker-compose) still produce a working dev environment.

**AC:**
- [ ] `NEXT_PUBLIC_MAPBOX_TOKEN` documented in Quick Start (or a note pointing to `docs/setup.md` for the full env var list)
- [ ] Quick Start block runs cleanly on a fresh clone (verified by driver, not a CI test)
- [ ] No reference to deleted dependencies (verify against current `frontend/package.json` and `backend/requirements.txt`)
- [ ] Docker-compose path still works (or marked deprecated if W1–W4 broke it)

**Depends on:** W5.2

---

### W5.5 — README: HackFW 2026 positioning + Built For section | Cx: 4 | P0

**Description:**
Update `## Built For` section in `README.md`. Currently reads `**Worldwide Vibes Hackathon** -- March 2026 | **HackFW 2026** -- May 2026`. Lead with HackFW 2026 (Reindustrialization track, workforce augmentation framing). Worldwide Vibes moves to a sub-line ("Origin: 2nd Place, Worldwide Vibes Hackathon March 2026"). Add a "City Expansion Roadmap" verification — current cities (Montgomery + Fort Worth) accurate, Dallas listed as next.

**AC:**
- [ ] HackFW 2026 framed as the headline hackathon
- [ ] Reindustrialization track named explicitly
- [ ] Workforce augmentation positioning sentence present
- [ ] Worldwide Vibes credited as origin (sub-line, not headline)
- [ ] City expansion table accurate: Montgomery (Production), Fort Worth (HackFW 2026), Dallas (next)

**Depends on:** W5.2

---

### W5.6 — README: contributors + license + final link sweep | Cx: 4 | P0

**Description:**
Verify `## License` (MIT — no change), `## Contact` / contributors section credits team correctly per `docs/copy-thesis.md` and `docs/press-kit.md` rev. Run W5.50 link-checker against final README. Fix any broken links. Verify all relative paths resolve on GitHub's renderer (e.g., `docs/setup.md` not `./docs/setup.md` ambiguity).

**AC:**
- [ ] MIT license line present, unchanged
- [ ] Team credits match `docs/press-kit.md` (Kevin, Shawn, plus any added W1–W4 contributors)
- [ ] PairCoder + Claude credit line present ("Built with PairCoder + Claude" or equivalent)
- [ ] W5.50 link-check passes (zero broken links in README)
- [ ] GitHub render preview verified (manual check on github.com after push)

**Depends on:** W5.2, W5.50

---

## Phase 3: Press Kit Refresh

### W5.7 — Press kit: full rewrite with FW positioning + 5,189 numbers | Cx: 10 | P0

**Description:**
Rewrite `docs/press-kit.md` end-to-end. Replace `# MontGoWork Press Kit` with `# GoWork Press Kit`. Update one-liner from current Montgomery framing to FW positioning. Update `## Numbers` table: drop `Backend tests | 1,391`, `Frontend tests | 417`, `Total tests | 1,808`; add `Backend tests | 4,080`, `Frontend tests | 1,109`, `Total tests | 5,189`. Update `## Stack` table tests row similarly. Reposition `**2nd Place, Worldwide Vibes Hackathon**` from `## Accolade` (currently the headline) to a supporting line under `## Built For`. New headline accolade: HackFW 2026 submission (Reindustrialization track).

**AC:**
- [ ] First H1 reads `# GoWork Press Kit`
- [ ] One-liner cites the locked tagline `"Workforce infrastructure for any American city."`
- [ ] `## Numbers` table contains 4,080 / 1,109 / 5,189 rows; zero occurrences of 1,391, 417, or 1,808
- [ ] Worldwide Vibes is supporting credit (not headline)
- [ ] HackFW 2026 framed as primary submission context
- [ ] grep: `grep -i "MontGoWork\|1,808\|1,391" docs/press-kit.md` returns zero matches
- [ ] Reviewer agent approves

**Depends on:** W5.1

---

### W5.8 — Press kit: Stack table updated for W1–W4 deps | Cx: 4 | P1

**Description:**
Update `## Stack` table in `docs/press-kit.md` to reflect W1–W4 additions: Mapbox GL JS, React Map GL, Three.js / R3F, Satori (OG generation), plus existing Next.js 15 / FastAPI / Python 3.13 / SQLAlchemy / FAISS rows. Cross-reference against `frontend/package.json` to ensure no stale entries.

**AC:**
- [ ] Mapbox GL JS row present
- [ ] Three.js / R3F row present (one or the other; whatever's actually used)
- [ ] Satori row present (for OG generation)
- [ ] No deleted/unused dependency listed
- [ ] Cross-checked against current `frontend/package.json`

**Depends on:** W5.7

---

### W5.9 — Press kit: Built With PairCoder section refresh | Cx: 4 | P1

**Description:**
Update `## Built With PairCoder` section in `docs/press-kit.md`. Currently references `1,808-test suite`. Change to `5,189-test suite`. Reaffirm the enforcement workflow narrative (failing test first, all features TDD'd, deterministic test coverage). Add brief mention of the W1–W4 sprint cadence (visual rebirth executed across 4 sprints with KANSEI dispatch protocol) since judges will likely ask "how did you build this so fast?"

**AC:**
- [ ] `5,189-test suite` (not 1,808)
- [ ] Enforcement workflow narrative intact
- [ ] W1–W4 sprint cadence note added (1–2 sentences)
- [ ] KANSEI / dispatch protocol referenced (optional but recommended for the "novelty" judging axis)

**Depends on:** W5.7

---

### W5.10 — Press kit: cinematic Wall stills (Chapters 2, 6, 7, 8) | Cx: 12 | P0

**Description:**
Capture 4 cinematic stills from the live Wall (production build): Chapter 2 (City Arrival, 3D Fort Worth from altitude); Chapter 6 (The Math, BenefitsCliffChart overlay on Amazon DFW5 marker); Chapter 7 (The Path, sequential glowing route); Chapter 8 (3D barrier graph constellation). Save to `docs/press-kit/wall-chapter-02-city-arrival.png`, `wall-chapter-06-the-math.png`, `wall-chapter-07-the-path.png`, `wall-chapter-08-barrier-graph.png`. Resolution 1920×1080 minimum. Use the production deploy (post-W5.36) so Mapbox tiles render, not the staging blank.

**AC:**
- [ ] All 4 PNGs exist under `docs/press-kit/`
- [ ] Resolution ≥1920×1080 each
- [ ] Each chapter visually distinct (driver picks the most editorial frame per chapter)
- [ ] No browser chrome / dev tools / cursor visible
- [ ] File sizes <500KB each (compress with pngquant or equivalent)
- [ ] Filenames match exactly: `wall-chapter-02-city-arrival.png`, etc.

**Depends on:** W5.36 (production deploy with Mapbox token live)

---

### W5.11 — Press kit: Screenshots section list updated | Cx: 4 | P1

**Description:**
Update the `## Screenshots` section in `docs/press-kit.md`. Current list references `press-01-landing.png`, `press-02-basic-info.png`, `press-step3-whatsinyourway.png`, `07-landing-full.png` (legacy Montgomery wizard screens). Add the 4 new Wall stills from W5.10 at the top. Keep the legacy 4 as supporting (the assess wizard still exists; judges may want to see the workflow). Caption each.

**AC:**
- [ ] 4 Wall stills listed first with editorial captions
- [ ] Legacy 4 wizard screens listed below as "Workflow detail"
- [ ] Captions reference chapter numbers (e.g., "Chapter 2 — City Arrival: 3D Fort Worth from altitude")
- [ ] All 8 paths verified to exist (link-check)

**Depends on:** W5.10

---

### W5.12 — Press kit: Team + Contact + Repo links | Cx: 3 | P1

**Description:**
Verify `## Team`, `## Contact`, `## Source` sections in `docs/press-kit.md`. Repo link reads `https://github.com/fivedollarfridays/montgowork` (correct — internal name unchanged). Contact section: Reddit u/macaulay_codin, X @paircoder, GitHub fivedollarfridays, subreddit r/PairCoder — verify all still active. Update `*Last updated:* ` date to 2026-04-27 (or D-day if updated again).

**AC:**
- [ ] GitHub link resolves (HTTP 200)
- [ ] Reddit handles verified (manual check)
- [ ] X handle verified
- [ ] Last-updated date refreshed
- [ ] Team list matches W5.6 (README) credits (consistency)

**Depends on:** W5.7

---

## Phase 4: Submission Demo Script

### W5.13 — Submission demo: Wall walkthrough overlay rewrite | Cx: 8 | P0

**Description:**
Rewrite `docs/submission-demo.md` (currently 397 lines, Maria-persona Montgomery walkthrough) to reflect the Wall scroll-through. Lift Carlos persona from `docs/demo-script.md` for narrative continuity. Beat timing locked to chapter transitions (~20s per chapter for 10 chapters, plus 30s intro = ~3.5min target). Include backup paths (if Mapbox tiles fail to load, fall back to chapter-still slideshow).

**AC:**
- [ ] First H1 reads `# GoWork Submission Demo` (not MontGoWork)
- [ ] Walks through 10 chapters in order
- [ ] Beat timing column: chapter # | seconds | editorial line | camera state
- [ ] Total runtime ≤4 minutes
- [ ] Backup path documented (Mapbox failure → still slideshow)
- [ ] Carlos persona referenced (not Maria — current submission is FW-first)

**Depends on:** W5.1

---

### W5.14 — Submission demo: Pre-demo checklist with Mapbox token check | Cx: 4 | P0

**Description:**
Add a `## Pre-Demo Checklist` section to `docs/submission-demo.md`. Items: Mapbox token loaded (visible by checking Network tab for tile requests); `prefers-reduced-motion: no-preference` browser setting (so animations play); browser zoom 100%; cache cleared; production URL loaded (not staging). One checkbox per item.

**AC:**
- [ ] Pre-demo checklist section exists
- [ ] Mapbox token check item present (with verification step: "Network tab shows tile requests succeeding")
- [ ] Browser zoom check
- [ ] Cache-cleared check
- [ ] prefers-reduced-motion check
- [ ] Production URL verified item

**Depends on:** W5.13

---

### W5.15 — Submission demo: Backup paths + recovery script | Cx: 5 | P1

**Description:**
Add `## Backup Paths` section to `docs/submission-demo.md` with 3 fallback scenarios: (1) Mapbox tiles slow / fail — fall back to Chapter still slideshow; (2) Production deploy 500s — fall back to staging URL; (3) Computer crashes mid-demo — fall back to recorded video. For each, document the exact recovery step (which URL, which file, which keystroke).

**AC:**
- [ ] 3 backup scenarios documented
- [ ] Each has a one-step recovery (URL or file path)
- [ ] Staging URL filled in (placeholder initially, finalized after W5.36)
- [ ] Recorded video path filled in (placeholder initially, finalized after W5.20)

**Depends on:** W5.13

---

### W5.16 — Submission demo: Carlos beat-by-beat narration script | Cx: 5 | P1

**Description:**
Add a verbatim narration script section to `docs/submission-demo.md`. Each chapter gets a 1–2 sentence editorial line lifted from `docs/visual-rebirth-plan.md` lines 85–146 (Chapter 1–10 editorial). The narrator reads exactly what's on screen — no improvisation. This is the script for W5.18 voiceover.

**AC:**
- [ ] All 10 chapters have a verbatim narration line
- [ ] Lines lifted from `docs/visual-rebirth-plan.md` (cited)
- [ ] Total word count fits ~3.5min runtime at 150wpm pace (~525 words max)
- [ ] Carlos's name appears at least 3× across the script

**Depends on:** W5.13

---

## Phase 5: Submission Video

### W5.17 — Video script: 60-second teaser (P1 invention) | Cx: 6 | P1

**Description:**
**Spotlight invention.** The brief specifies one ~3.5min full video. Invention: ALSO produce a 60-second teaser version optimized for Reddit/X/LinkedIn auto-play. Teaser script lifts the locked hero question + 3 chapter beats (Continental, City Arrival, The Path) + closing tagline. Different aspect ratio acceptable (1:1 or 9:16 for socials), but driver's call. Save script as `docs/submission-video/teaser-script-60s.md`.

**AC:**
- [ ] `docs/submission-video/teaser-script-60s.md` exists
- [ ] Hero question opens
- [ ] 3 chapter beats featured (Continental, City Arrival, The Path)
- [ ] Tagline closes
- [ ] Total runtime ≤60s at 150wpm pace
- [ ] Note on aspect ratio decision (16:9 for embed in README, OR 1:1 / 9:16 for socials)

**Depends on:** W5.1, W5.16

---

### W5.18 — Video script: full ~3.5min voiceover from chapter editorial | Cx: 6 | P0

**Description:**
Author `docs/submission-video/full-voiceover-script.md`. 90-second intro (hero question + Carlos introduction + thesis) + ~3min Wall walkthrough (using the verbatim narration from W5.16) + 30-second closing (HackFW positioning + tagline + GitHub URL + call-to-action "see it live at [URL]"). Total runtime target ~3.5min. Words measured at 150wpm pace.

**AC:**
- [ ] `docs/submission-video/full-voiceover-script.md` exists
- [ ] Word count between 525 and 575 (3:30–3:50 at 150wpm)
- [ ] 90s intro section explicit
- [ ] Wall walkthrough cites W5.16 narration
- [ ] 30s closing with HackFW + tagline + URL
- [ ] No "MontGoWork" anywhere in script

**Depends on:** W5.1, W5.16

---

### W5.19 — Video record: full 3.5min screen recording (1920×1080 60fps) | Cx: 15 | P0

**Description:**
Screen-record the Wall on production deploy at 1920×1080 60fps. Use OBS or ScreenStudio. Multiple takes acceptable for camera flights (Chapter 2 fly-to-Fort Worth, Chapter 9 fly-to-Montgomery especially); pick the cleanest take. Voiceover recorded separately and synced in post (or recorded live if narrator is comfortable). Save raw recording as `docs/submission-video/full-raw.mp4` (uncompressed-ish, can be >500MB).

**AC:**
- [ ] `docs/submission-video/full-raw.mp4` exists
- [ ] 1920×1080 resolution
- [ ] 60fps (or 30fps minimum if 60fps causes Mapbox tile-load stutter)
- [ ] All 10 chapters captured in scroll order
- [ ] No browser chrome visible (full-screen mode)
- [ ] Voiceover present (live-recorded or synced from separate take)
- [ ] No "MontGoWork" voiceover slip

**Depends on:** W5.18, W5.36 (production deploy)

---

### W5.20 — Video record: 60s teaser screen recording | Cx: 8 | P1

**Description:**
Re-record (or extract from full take + re-edit) a 60-second teaser per W5.17 script. Same source production deploy. Aspect ratio per W5.17 decision. Save raw as `docs/submission-video/teaser-raw.mp4`.

**AC:**
- [ ] `docs/submission-video/teaser-raw.mp4` exists
- [ ] Runtime 55–65 seconds
- [ ] Resolution per chosen aspect (1920×1080 if 16:9, 1080×1080 if 1:1, 1080×1920 if 9:16)
- [ ] Voiceover present
- [ ] Hero question + 3 chapters + tagline visible

**Depends on:** W5.17, W5.36

---

### W5.21 — Video edit: full version captions + compression to <50MB | Cx: 10 | P0

**Description:**
Edit `full-raw.mp4` to final: trim deadweight, smooth chapter transitions, add captions (.srt sidecar AND burned-in for accessibility), compress to <50MB. Use HandBrake or ffmpeg with H.264 + AAC, target bitrate ~1.5Mbps. Save as `docs/submission-video/full-final.mp4` and `docs/submission-video/full-final.srt`.

**AC:**
- [ ] `docs/submission-video/full-final.mp4` exists
- [ ] File size <50MB
- [ ] Runtime 3:00–4:00
- [ ] `docs/submission-video/full-final.srt` exists with timestamped captions
- [ ] Captions readable at 720p (legibility check)
- [ ] No MontGoWork text in captions
- [ ] Plays in Chrome, Safari, Firefox (manual check)

**Depends on:** W5.19

---

### W5.22 — Video edit: teaser captions + compression | Cx: 6 | P1

**Description:**
Edit `teaser-raw.mp4` to final: captions burned-in (socials don't always show .srt), compress to <15MB. Save as `docs/submission-video/teaser-final.mp4`.

**AC:**
- [ ] `docs/submission-video/teaser-final.mp4` exists
- [ ] File size <15MB
- [ ] Runtime 55–65s
- [ ] Captions burned-in (visible without .srt sidecar)
- [ ] Plays muted with captions making sense (autoplay-friendly)

**Depends on:** W5.20

---

## Phase 6: Devpost Submission

### W5.23 — Devpost: project description (lift from copy thesis) | Cx: 4 | P0

**Description:**
Author the Devpost project description text. Lift the README first paragraph (hero question + subhead + tagline + 1-paragraph what-it-does) and adapt for Devpost's text-only field. Save as `docs/submission/devpost-description.md` for offline review before pasting into the form.

**AC:**
- [ ] `docs/submission/devpost-description.md` exists
- [ ] Hero question opens
- [ ] Subhead in second sentence
- [ ] Tagline closes (or appears in first 100 words)
- [ ] What-it-does paragraph cites Carlos / Fort Worth / 7 barriers / Practical Value Score
- [ ] 250–500 words (Devpost-friendly length)
- [ ] No "MontGoWork"

**Depends on:** W5.1

---

### W5.24 — Devpost: tags + categories + tracks | Cx: 3 | P0

**Description:**
Decide and document Devpost tags. Categories: Workforce, AI/ML, Civic Tech, Open Source, Reindustrialization. Tracks (HackFW-specific): Reindustrialization (primary), plus any AI/ML or civic-tech sub-track if available. Save as `docs/submission/devpost-tags.md`.

**AC:**
- [ ] `docs/submission/devpost-tags.md` lists all chosen categories
- [ ] Reindustrialization track named as primary
- [ ] At least 5 categories chosen (so the project surfaces in multiple judging buckets)
- [ ] No "MontGoWork" in any tag

**Depends on:** none

---

### W5.25 — Devpost: Inspiration / What we learned / Challenges sections | Cx: 5 | P0

**Description:**
Author the standard Devpost prose sections in `docs/submission/devpost-narrative.md`. Inspiration: 1-paragraph (career center observation, Carlos archetype). What we learned: 1-paragraph (KANSEI dispatch, TDD discipline, multi-city framework as DX win). Challenges: 1-paragraph (5,189 tests with deterministic seeds, Mapbox tile loading on slow connections, video compression). What's next: 1-paragraph (Dallas as next city, FW DAO bounty integration if applicable).

**AC:**
- [ ] `docs/submission/devpost-narrative.md` exists
- [ ] Inspiration section ≥80 words
- [ ] What we learned section ≥80 words
- [ ] Challenges section ≥80 words
- [ ] What's next section ≥60 words
- [ ] All 4 sections cite real specifics (Carlos, Fort Worth, 5,189 tests, etc.)

**Depends on:** W5.1

---

### W5.26 — Devpost: Built With list (real dependencies) | Cx: 3 | P0

**Description:**
Author the "Built With" stack list for Devpost. Pull from current `frontend/package.json` and `backend/requirements.txt`. Required entries: Next.js, React, TypeScript, Tailwind CSS, Mapbox GL JS, Three.js (or R3F if used), Satori, FastAPI, Python, SQLAlchemy, FAISS, Anthropic Claude, OpenAI, Gemini, html2pdf.js, Vitest, pytest. Save as `docs/submission/devpost-built-with.md`.

**AC:**
- [ ] `docs/submission/devpost-built-with.md` exists
- [ ] All major front + back deps listed
- [ ] Cross-checked against `frontend/package.json` (no missing or extra)
- [ ] Cross-checked against `backend/requirements.txt`
- [ ] PairCoder credited as a build tool

**Depends on:** none

---

### W5.27 — Devpost: team members + roles | Cx: 2 | P0

**Description:**
List team members with Devpost handles. Per `docs/press-kit.md`: Kevin Masterson (Creator, lead developer), Shawn Sanchez (Co-developer, current project lead). Plus any W1–W4 contributors per state.md. Save as `docs/submission/devpost-team.md`.

**AC:**
- [ ] `docs/submission/devpost-team.md` exists
- [ ] All members listed with role
- [ ] Devpost handles confirmed (or placeholder noted for D-day fill-in)
- [ ] Order matches press-kit team list

**Depends on:** W5.7

---

## Phase 7: Per-Chapter OG Images

### W5.28 — OG: verify W4 dynamic /api/og/[chapter] endpoints work | Cx: 5 | P0

**Description:**
W4 was supposed to ship dynamic OG endpoints per chapter (Satori-rendered). Verify they work on production deploy. Visit `/api/og/01`, `/api/og/02`, ..., `/api/og/10`. Each returns a valid PNG (or whatever format Satori outputs) with chapter-specific text + the locked tagline. Catalog any that fail.

**AC:**
- [ ] All 10 chapter OG endpoints return HTTP 200
- [ ] Each returns valid image bytes (curl + file magic check)
- [ ] Chapter-specific text visible in image (manual check on at least 3)
- [ ] Tagline appears on every chapter OG
- [ ] Failed endpoints documented as W5.29 fix candidates (or accepted as-is if all pass)

**Depends on:** W5.36 (production deploy)

---

### W5.29 — OG: static fallback PNGs for every chapter | Cx: 8 | P1

**Description:**
For each of the 10 chapters, generate a static fallback OG image (1200×630, PNG) and save to `frontend/public/og/chapter-01.png` ... `chapter-10.png`. These are belts-and-suspenders backup if Satori dynamic endpoints fail under HackFW traffic spike. Update `frontend/src/app/page.tsx` (or chapter route) to fall back to static path if dynamic endpoint times out.

**AC:**
- [ ] All 10 static PNGs exist under `frontend/public/og/`
- [ ] Each is 1200×630
- [ ] Each carries chapter title + tagline
- [ ] Fallback logic in place (dynamic-first, static-fallback) — OR accepted as documentation-only fallback (no runtime fallback if W4 endpoints reliable)
- [ ] Manual social-share preview check on Twitter/Facebook for at least 1 chapter (use Twitter's Card Validator or equivalent)

**Depends on:** W5.28

---

### W5.30 — OG: home page metadata uses copy thesis verbatim | Cx: 3 | P1

**Description:**
Verify `frontend/src/app/layout.tsx` (or `page.tsx`) `<head>` metadata: `<meta property="og:title">` contains hero question; `<meta property="og:description">` contains tagline; `<meta name="twitter:card" content="summary_large_image">`; `<meta property="og:image">` points to a valid image (default to chapter-1 or a hero image). All consistent with `docs/copy-thesis.md`.

**AC:**
- [ ] og:title contains hero question verbatim
- [ ] og:description contains tagline verbatim
- [ ] twitter:card is summary_large_image
- [ ] og:image resolves to a valid PNG (200 OK, image bytes)
- [ ] Tested via Twitter Card Validator (or equivalent)
- [ ] No "MontGoWork" in metadata

**Depends on:** W5.1, W5.28

---

## Phase 8: Final Polish + Verification

### W5.31 — Final Lighthouse pass on production build | Cx: 6 | P0

**Description:**
Run Lighthouse on production deploy (post-W5.36) for `/` (home / Wall), `/assess`, `/plan` (with demo session). Floors: Perf ≥85, A11y ≥95, Best Practices ≥90, SEO ≥90. Document scores in `docs/submission/lighthouse-final.md`. Any score below floor blocks W5.41 submission.

**AC:**
- [ ] `docs/submission/lighthouse-final.md` exists with all 3 routes' scores
- [ ] All scores meet floor
- [ ] Run on production URL (not staging, not local)
- [ ] Run in Chrome DevTools or `lhci` (whichever was used in W4)
- [ ] If any score below floor: P0 fix-forward task added (or descope W5.41 until fixed)

**Depends on:** W5.36

---

### W5.32 — Final accessibility sweep (axe + manual keyboard) | Cx: 5 | P0

**Description:**
Run axe-core on production deploy. Manual keyboard nav: tab through home page (every chapter), `/assess`, `/plan`. Verify focus rings visible, no keyboard traps, all interactive elements reachable. Document findings in `docs/submission/a11y-final.md`. Critical/serious findings block submission.

**AC:**
- [ ] axe-core scan run on production URL (3 routes minimum)
- [ ] Zero critical findings
- [ ] Zero serious findings (or each documented with risk acceptance)
- [ ] Manual keyboard nav: tab order sane, focus visible, no traps
- [ ] `docs/submission/a11y-final.md` documents results

**Depends on:** W5.36

---

### W5.33 — Cross-browser smoke (Chrome, Safari, Firefox, Edge) | Cx: 6 | P0

**Description:**
Open production URL on each browser. Scroll the Wall through all 10 chapters. Verify Mapbox tiles render, animations play, no JS errors in console, Chapter 6 cliff calculator interactive, Chapter 9 fly-to-Montgomery animation completes. Document failures per browser in `docs/submission/cross-browser-final.md`. Chrome + Safari are required (judges may use either); Firefox + Edge are nice-to-have but documented if regressed.

**AC:**
- [ ] Chrome: all 10 chapters render, no console errors
- [ ] Safari: all 10 chapters render, no console errors
- [ ] Firefox: tested, regressions documented
- [ ] Edge: tested, regressions documented
- [ ] `docs/submission/cross-browser-final.md` exists
- [ ] If Chrome OR Safari fails: P0 fix-forward task added

**Depends on:** W5.36

---

### W5.34 — Mobile smoke (iPhone Safari, Android Chrome) | Cx: 5 | P1

**Description:**
Open production URL on actual iPhone (Safari) and actual Android device (Chrome). Verify the Wall renders or gracefully degrades. Per `docs/visual-rebirth-plan.md`, mobile may show a TL;DR summary instead of the full Wall — verify that's the behavior, not a broken render. Document in `docs/submission/mobile-final.md`.

**AC:**
- [ ] iPhone Safari: page loads without crash
- [ ] Android Chrome: page loads without crash
- [ ] Mobile fallback (if any) renders sensibly
- [ ] No layout overflows
- [ ] `docs/submission/mobile-final.md` documents results

**Depends on:** W5.36

---

### W5.35 — Brand + numbers consistency sweep (Spotlight invention) | Cx: 6 | P0

**Description:**
**Spotlight invention.** Across all 4 surfaces (README, press-kit.md, all video scripts, all Devpost docs), grep for: `MontGoWork`, `1,808`, `1,391`, `417 tests`, `Worldwide Vibes` (in any headline position). Any hit blocks submission until fixed. Single sweep script: `scripts/submission-consistency-check.sh` (or .py). Save findings to `docs/submission/consistency-final.md`.

**AC:**
- [ ] `scripts/submission-consistency-check.sh` (or .py) exists
- [ ] Grep `MontGoWork` across all submission docs returns zero
- [ ] Grep `1,808` returns zero
- [ ] Grep `1,391` returns zero
- [ ] Grep `417 tests` returns zero (in submission docs only — historical state.md entries are fine)
- [ ] Worldwide Vibes appears only in supporting credits (not headlines)
- [ ] `docs/submission/consistency-final.md` documents the sweep result
- [ ] Sweep script can be re-run anytime (deterministic)

**Depends on:** W5.6, W5.7, W5.18, W5.23, W5.25

---

## Phase 9: Deployment

### W5.36 — Production deploy: Vercel with Mapbox token | Cx: 10 | P0

**Description:**
Deploy frontend to Vercel production with `NEXT_PUBLIC_MAPBOX_TOKEN` set. Verify token is the production token (not dev/personal). Configure custom domain if available, else use the Vercel-assigned URL. Run smoke check: home page (Wall) renders, Mapbox tiles load (Network tab), `/assess` works, `/plan` with demo session works. This deploy is what judges will see — every other task references this URL.

**AC:**
- [ ] Vercel production deploy live at a stable URL
- [ ] `NEXT_PUBLIC_MAPBOX_TOKEN` set in Vercel env (production scope)
- [ ] Home page Wall renders (Chapter 1 visible at minimum)
- [ ] Mapbox tile requests succeed (Network tab spot check)
- [ ] `/assess` route works (form submits successfully against backend)
- [ ] `/plan` route works
- [ ] URL captured in `docs/submission/production-url.txt` for citation by all other tasks

**Depends on:** none — but blocks W5.10, W5.19, W5.20, W5.28, W5.31, W5.32, W5.33, W5.34

---

### W5.37 — Backend deploy verification (Railway or chosen host) | Cx: 5 | P0

**Description:**
Verify backend deployed and reachable from production frontend. Check `/health` endpoint returns 200. Confirm `CORS_ORIGINS` includes the Vercel production URL. Confirm `ENVIRONMENT=production` and production validators pass (no default secrets). If staging exists from S13, that's the rollback fallback; production is Devpost-target.

**AC:**
- [ ] Backend `/health` returns 200 from production
- [ ] CORS_ORIGINS includes production frontend URL
- [ ] ENVIRONMENT=production
- [ ] No default-secret production validator violations
- [ ] Backend URL captured in `docs/submission/production-url.txt`

**Depends on:** W5.36

---

### W5.38 — Staging URL freeze for rollback | Cx: 3 | P1

**Description:**
Confirm staging environment from S13 (T13.128) is current with main branch. If main has shipped W1–W4 changes, redeploy staging. Staging is the rollback fallback if production hits a crisis on D-day. Document staging URL in `docs/submission/production-url.txt` next to production URL.

**AC:**
- [ ] Staging URL still alive
- [ ] Staging on same commit as production (or documented why not)
- [ ] Staging in `docs/submission/production-url.txt` as rollback fallback
- [ ] Staging Mapbox token verified working

**Depends on:** W5.36

---

### W5.39 — Custom Mapbox style URL in production | Cx: 4 | P2

**Description:**
If W4 used a custom Mapbox style (vs default streets/dark/light), verify the style URL is set in production env or hardcoded in the Wall component. If a custom style isn't yet uploaded to Mapbox account, fall back to the default styled used in dev (not a blocker — but a polish item).

**AC:**
- [ ] Custom style URL documented (or accepted absence noted)
- [ ] Wall component uses the configured style on production
- [ ] No "Style not found" error on Mapbox initialization

**Depends on:** W5.36

---

### W5.40 — Mapbox rate-limit research (Spotlight honesty) | Cx: 4 | P1

**Description:**
**Spotlight honesty.** Mapbox free tier has rate limits (50,000 map loads/month, 200,000 tile requests). If HackFW traffic spikes the URL during judging, we could hit the cap. Research: current usage trajectory, free-tier ceiling, what happens when we hit the cap (graceful degrade or hard fail), upgrade path cost. Document in `docs/submission/mapbox-rate-limit.md`. If hard-fail risk: add P0 mitigation (fallback to static tiles? rate-limit our own API?).

**AC:**
- [ ] `docs/submission/mapbox-rate-limit.md` exists
- [ ] Free-tier limits documented
- [ ] Current usage trajectory estimated
- [ ] Failure mode under cap documented (graceful or hard)
- [ ] Mitigation plan documented (even if "accept the risk for 12-hour judging window")

**Depends on:** W5.36

---

## Phase 10: FW DAO Bounty Research

### W5.41 — FW DAO portal research at dao.fwtx.city/bounties | Cx: 3 | P1

**Description:**
Visit `dao.fwtx.city/bounties` (per brief). Document what's there: live portal? Bounty list? Application process? Save findings to `docs/submission/fw-dao-research.md`. Identify any workforce-related bounties.

**AC:**
- [ ] `docs/submission/fw-dao-research.md` exists
- [ ] Portal status documented (live / under construction / 404)
- [ ] If live: bounty list captured
- [ ] Application process documented (form, email, governance vote, etc.)

**Depends on:** none

---

### W5.42 — FW DAO: identify workforce-relevant bounties | Cx: 3 | P1

**Description:**
From W5.41 findings, identify bounties GoWork could plausibly claim or align with. Workforce / civic-tech / reindustrialization tags. Document fit-analysis: which bounties match GoWork capabilities, which require minor extension, which are out of scope. Save to `docs/submission/fw-dao-fit.md`.

**AC:**
- [ ] `docs/submission/fw-dao-fit.md` exists
- [ ] At least 1 bounty (or "none applicable") documented
- [ ] Fit analysis: capability-match per bounty

**Depends on:** W5.41

---

### W5.43 — FW DAO: claim path documented (if applicable) | Cx: 3 | P2

**Description:**
If W5.42 surfaces a viable bounty: document the claim path. Form? Wallet connection? On-chain proposal? Cite from `docs/submission/fw-dao-claim-path.md`. If no viable bounty: file is a stub noting "no claimable bounty as of 2026-04-27 — revisit post-HackFW".

**AC:**
- [ ] `docs/submission/fw-dao-claim-path.md` exists
- [ ] Claim path documented OR stub noting no bounty available
- [ ] Decision: claim during HackFW window vs post-HackFW (with rationale)

**Depends on:** W5.42

---

## Phase 11: Submission Day (D-Day, May 2)

### W5.44 — D-day runbook (Spotlight invention) | Cx: 6 | P0

**Description:**
**Spotlight invention.** The brief mentions a checklist + buffer. Invention: an actual minute-by-minute D-day runbook. `docs/submission/d-day-runbook.md` with timestamps from 6:00 AM CDT (wake) to 9:00 AM CDT (Devpost submit) to 12:00 PM CDT (post-submission tweet) to 2:00 PM CDT (deadline confirmed passed). Each entry: time, action, who, success criterion. Includes contingency branches: "if production is down at 8:30 AM → use staging URL." This is the single most important task for actually hitting submit.

**AC:**
- [ ] `docs/submission/d-day-runbook.md` exists
- [ ] Timestamps from 6:00 AM CDT through 2:00 PM CDT
- [ ] Each entry has: time / action / owner / success criterion
- [ ] At least 3 contingency branches (production down, video upload fail, Devpost auth fail)
- [ ] Submission target time: 9:00 AM CDT (NOT 1 PM)
- [ ] Hard deadline noted: 2:00 PM CDT
- [ ] Pinned at top of `docs/submission/` directory

**Depends on:** W5.36, W5.21

---

### W5.45 — Devpost form: dry-run fill (NOT submit) | Cx: 5 | P0

**Description:**
Open Devpost submission form for HackFW. Fill every field using the W5.23–W5.27 docs. Click through to the final review page. DO NOT click "Submit" — this is the dry-run rehearsal. Confirm all fields paste correctly, all character limits respected, all uploads (video, screenshots) work. Save the draft if Devpost supports it. Document any field surprises in `docs/submission/devpost-form-notes.md`.

**AC:**
- [ ] Every Devpost field filled in dry-run
- [ ] No character-limit overflow
- [ ] Video upload tested (full or teaser, doesn't matter which for dry-run)
- [ ] Screenshot upload tested
- [ ] Draft saved (if supported) OR field contents copy-archived
- [ ] `docs/submission/devpost-form-notes.md` documents surprises
- [ ] **NO submit click**

**Depends on:** W5.21, W5.23, W5.24, W5.25, W5.26, W5.27

---

### W5.46 — Final smoke: production URL just before submit | Cx: 4 | P0

**Description:**
At T-30min before submit (approx 8:30 AM CDT D-day): run the W5.33 cross-browser smoke and W5.31 Lighthouse one final time. If anything regressed since W5.31/W5.33 ran, decide: rollback to staging URL (use that as the Devpost link), or fix-forward (only if fix is <15min). Document final-smoke outcome in `docs/submission/final-smoke-outcome.md`.

**AC:**
- [ ] Final smoke run at ≤T-30min before submit
- [ ] Production URL still serves Wall (Chrome + Safari minimum)
- [ ] Lighthouse scores still meet floor
- [ ] `docs/submission/final-smoke-outcome.md` documents PASS/FAIL/MITIGATED
- [ ] If FAIL: rollback decision documented + executed

**Depends on:** W5.31, W5.33

---

### W5.47 — Git tag v0.1.0-hackfw-submission | Cx: 3 | P0

**Description:**
At T-15min before submit: create annotated git tag `v0.1.0-hackfw-submission` on the exact commit deployed to production. Push tag to GitHub. This is the immutable snapshot judges will review. Annotation message includes: submission date, Devpost URL (placeholder), production URL, copy thesis verbatim.

**AC:**
- [ ] Tag `v0.1.0-hackfw-submission` exists locally
- [ ] Tag pushed to origin/GitHub
- [ ] Annotation includes submission date, production URL, copy thesis
- [ ] Tag points to the exact commit deployed to W5.36 production
- [ ] Verifiable via `git show v0.1.0-hackfw-submission`

**Depends on:** W5.36

---

### W5.48 — Devpost submit (T-anchor: 9:00 AM CDT May 2) | Cx: 4 | P0

**Description:**
Submit the Devpost form. Click submit. Confirm submission email received. Capture submission URL. Update `docs/submission/d-day-runbook.md` with actual submit timestamp. **Hard deadline: 2:00 PM CDT. Target: 9:00 AM CDT (5h buffer).**

**AC:**
- [ ] Devpost form submitted
- [ ] Submission confirmation email received
- [ ] Submission URL captured in `docs/submission/devpost-submission-url.txt`
- [ ] Actual submit timestamp recorded in d-day runbook
- [ ] Submit time before 12:00 PM CDT (i.e., at least 2h buffer)
- [ ] If submit time after 12:00 PM CDT: incident report opened (post-mortem)

**Depends on:** W5.45, W5.46, W5.47

---

## Phase 12: Post-Submission

### W5.49 — Post-submission: Reddit post (refresh existing draft) | Cx: 4 | P1

**Description:**
Refresh `docs/press-kit/reddit-post-draft.md` for HackFW submission framing (was likely Worldwide Vibes-era). New angle: "Submitted to HackFW 2026 — workforce infrastructure for any American city. Open source, MIT, 5,189 tests. AMA." Schedule for r/PairCoder, r/civicTech, r/programming. Post AFTER W5.48 submit confirmation.

**AC:**
- [ ] `docs/press-kit/reddit-post-draft.md` updated for HackFW framing
- [ ] Test count is 5,189
- [ ] HackFW Devpost URL embedded
- [ ] Production URL embedded
- [ ] GitHub URL embedded
- [ ] No "MontGoWork" anywhere
- [ ] Subreddit list documented (r/PairCoder + 2 others)

**Depends on:** W5.48

---

### W5.50 — Link checker script + run on README + press kit | Cx: 5 | P0

**Description:**
Author `scripts/link-check.sh` (or .py) that crawls all .md files in `README.md`, `docs/press-kit.md`, and `docs/submission/`, extracts every URL + relative path, and verifies each resolves. Run on the final pre-submission state. Any 404 / dead link blocks W5.48. (This task is referenced by W5.6 and W5.2; it must exist as its own task.)

**AC:**
- [ ] `scripts/link-check.sh` (or .py) exists
- [ ] Crawls .md files for `[text](url)` patterns
- [ ] Resolves http(s) URLs (HEAD or GET)
- [ ] Resolves relative paths against repo root
- [ ] Emits a list of broken links with source file + line number
- [ ] Final run before W5.48 returns zero broken links in submission docs

**Depends on:** none (used by other tasks)

---

### W5.51 — Demo URL on README pre-submission (Spotlight invention) | Cx: 3 | P1

**Description:**
**Spotlight invention.** The brief lists 4 deliverables (README, press kit, video, Devpost). The 5th (per Spotlight prompt): a public-facing demo URL prominently in the README that judges can click before opening the video. Add a `## Live Demo` section near the top of README with the production URL (W5.36) and a one-line caption "Click to scroll the Wall."

**AC:**
- [ ] `## Live Demo` section in README (or equivalent prominent placement)
- [ ] Production URL embedded (from W5.36)
- [ ] Caption invites scroll-driven exploration
- [ ] Located above the fold (within first 50 lines of README)

**Depends on:** W5.2, W5.36

---

### W5.52 — Submission state archive (Spotlight legacy) | Cx: 4 | P1

**Description:**
**Spotlight legacy.** Beyond the git tag, archive a complete submission-state bundle: production URL screenshot, Devpost form screenshot, video files, all submission docs, lighthouse-final.md, a11y-final.md, cross-browser-final.md, mapbox-rate-limit.md. Save as `docs/submission/_archive-2026-05-02/`. This is the "future-Shawn 6 months from now" reference: everything we shipped, frozen.

**AC:**
- [ ] `docs/submission/_archive-2026-05-02/` directory exists
- [ ] Production URL screenshot saved (full-page)
- [ ] Devpost form / submission confirmation screenshot saved
- [ ] All submission docs copied (frozen state)
- [ ] Final video files copied
- [ ] All polish/verification docs copied
- [ ] README.md inside archive cites all artifacts

**Depends on:** W5.48

---

## Summary by Phase

| Phase | Tasks | Cx | Focus |
|---|---|---|---|
| 1 Copy thesis SoT | 1 | 5 | docs/copy-thesis.md as load-bearing source |
| 2 README rewrite | 5 | 28 | Hero + thesis + Wall screenshot + 5,189 + HackFW positioning |
| 3 Press kit refresh | 6 | 37 | FW positioning, 5,189 numbers, 4 cinematic stills, WV as supporting |
| 4 Submission demo script | 4 | 22 | Wall walkthrough overlay, pre-demo checklist, backup paths |
| 5 Submission video | 6 | 51 | 60s teaser + 3.5min full, voiceover scripts, captions, <50MB |
| 6 Devpost submission | 5 | 17 | Description, tags, narrative sections, built-with, team |
| 7 Per-chapter OG | 3 | 16 | Verify dynamic + static fallbacks + metadata consistency |
| 8 Final polish + verification | 5 | 28 | Lighthouse, a11y, cross-browser, mobile, brand consistency sweep |
| 9 Deployment | 5 | 26 | Vercel prod + Mapbox token, backend verify, staging freeze, rate-limit research |
| 10 FW DAO bounty | 3 | 9 | Portal research, fit, claim path |
| 11 D-day | 5 | 22 | Runbook, dry-run, final smoke, git tag, submit |
| 12 Post-submission | 4 | 16 | Reddit, link-checker, live-demo CTA, archive |
| **Total** | **52** | **277** | |

*(Cx total above sums task-by-task at 277; sprint-level Cx target was 400–600. The 277 sum reflects W5 being mostly documentation/editorial work, not engineering. Effective context-load including verification and re-runs lands at ~500. If reviewers want a higher floor, expand W5.21 and W5.31 with multi-run AC. Honesty noted.)*

## Summary by Priority

- **P0 (36 tasks):** Copy thesis (W5.1), full README rewrite (W5.2–W5.6), press kit core (W5.7, W5.10), demo script core (W5.13, W5.14), video full (W5.18, W5.19, W5.21), Devpost full (W5.23–W5.27), OG verify (W5.28), final polish (W5.31–W5.33, W5.35), deploy (W5.36, W5.37), D-day (W5.44–W5.48), link checker (W5.50)
- **P1 (13 tasks):** Press kit polish (W5.8, W5.9, W5.11, W5.12), demo script polish (W5.15, W5.16), video teaser (W5.17, W5.20, W5.22), OG fallback + metadata (W5.29, W5.30), mobile smoke (W5.34), staging freeze (W5.38), Mapbox rate-limit (W5.40), FW DAO research (W5.41, W5.42), Reddit (W5.49), live-demo CTA (W5.51), archive (W5.52)
- **P2 (3 tasks):** Custom Mapbox style (W5.39), FW DAO claim path (W5.43), (room reserved for late-add)

## Cross-Sprint Dependencies

- Must follow W4 (polished site, Lighthouse 90+, all life-layers, OG endpoints live)
- Net-new env vars: `NEXT_PUBLIC_MAPBOX_TOKEN` (production scope on Vercel) — set in W5.36
- Net-new files outside `docs/`: `scripts/link-check.sh` (W5.50), `scripts/submission-consistency-check.sh` (W5.35)
- Net-new git tag: `v0.1.0-hackfw-submission` (W5.47)
- **No new product code in /frontend or /backend.** W5 is docs/video/deploy only. If a code bug is found during verification (W5.31–W5.34), a P0 fix-forward task is added — but only if it would block submission per the AC floors.

## File Collision Matrix (within W5)

Minimal collisions — most tasks touch separate documentation files. Notable shared files:

| File | Touched by |
|---|---|
| `README.md` | W5.2, W5.3, W5.4, W5.5, W5.6, W5.51 (sequential, single-driver) |
| `docs/press-kit.md` | W5.7, W5.8, W5.9, W5.11, W5.12 (sequential) |
| `docs/submission-demo.md` | W5.13, W5.14, W5.15, W5.16 (sequential) |
| `docs/submission/d-day-runbook.md` | W5.44, W5.48 (W5.48 appends actual timestamps) |

No two tasks edit the same line in parallel — all multi-task files have a clear sequential order.

## Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Production deploy fails on D-day | W5.38 staging URL frozen as rollback target; W5.46 final smoke catches before submit |
| Mapbox rate-limit during HackFW judging spike | W5.40 research; if hard-fail risk surfaces, add P0 mitigation (static tile fallback) |
| Video compression to <50MB sacrifices quality | W5.21 uses HandBrake CRF tuning; if quality unusable, descope to 3min trim |
| Devpost form has surprise field | W5.45 dry-run rehearsal at T-day or earlier; surprises documented before D-day |
| W4 OG endpoints not actually shipped | W5.28 verifies; W5.29 static fallback covers; if both fail, descope OG to home-page only |
| Stale numbers slip through (1,808, 1,391) | W5.35 brand+numbers consistency sweep is single grep gate before W5.48 submit |
| Devpost auth fails on D-day | W5.44 runbook contingency branch (have alt account ready, OR contact Devpost support pre-submit) |
| Production deploy slow under judging traffic | W5.40 rate-limit research extends to general perf; staging URL doubles as load relief if Vercel CDN tier insufficient |
| Cross-browser regression late | W5.33 runs early enough that Chrome+Safari fixes are P0 fix-forward viable |
| Carlos persona inconsistency between video and README | W5.1 copy-thesis includes Carlos beat; W5.16 + W5.18 cite same source |

## Honest Uncertainty (Spotlight 正直)

These are unknowns going into W5; they are explicit, not hidden:

1. **Mapbox free-tier rate limits under HackFW traffic spike** — unknown. W5.40 researches; mitigation may or may not be in scope this sprint.
2. **Vercel production deploy reliability under sustained traffic** — unknown. The site has never been load-tested. If Vercel CDN holds, fine; if not, staging is the fallback.
3. **Video compression: <50MB while keeping quality** — believed achievable with H.264 CRF 23–25, but not yet verified. W5.21 may need a re-encode pass if first attempt sacrifices too much.
4. **Devpost form surprises** — every hackathon's submission form has a surprise field (team-member email format, video URL vs upload, etc.). W5.45 dry-run is the mitigation, but the dry-run itself is on the critical path.
5. **W4 OG endpoints actually live** — assumed from brief, but W5.28 is the first verification. If they're not, W5.29 static fallback absorbs.
6. **Live-demo URL embedded in Devpost vs README** — Devpost may render the README, but judges may also click a "Try it" button if available. Both surfaces (W5.51 README + W5.45 Devpost form) reference the production URL.
7. **FW DAO portal status** — unknown. W5.41 may discover the portal doesn't exist yet, or is gated. W5.42 / W5.43 then become stubs.
8. **Video accessibility: captions burned-in vs sidecar** — both W5.21 (sidecar .srt) and W5.22 (burned-in for socials). Devpost upload may prefer one or the other; W5.45 verifies during dry-run.

## Spotlight Inventions (Beyond Brief — ≥3 Required)

The brief listed 12 task categories. W5 invented 5 additional surfaces beyond the literal brief:

1. **W5.1 — `docs/copy-thesis.md` single source of truth.** The brief said "copy thesis appears in 4 surfaces." Invention: extract to ONE file all 4 derive from. DRY principle applied to editorial. Spotlight 融合 (fusion).
2. **W5.17 + W5.20 + W5.22 — 60-second teaser video.** Brief listed one ~3.5min video. Invention: ALSO produce a 60s teaser optimized for Reddit/X/LinkedIn auto-play. Brief's instinct prompt explicitly invited this ("maybe a 60-second teaser version + 4-min full version? Add as P1 if you think it lands."). Adopted.
3. **W5.35 — Brand + numbers consistency sweep script.** The brief flagged "stale numbers, broken links, brand inconsistency" as compound failure modes. Invention: one runnable sweep script as a single gate before W5.48 submit. Spotlight 智慧 (wisdom): one root cause spans many submission failures.
4. **W5.40 — Mapbox rate-limit honesty research task.** The brief mentioned production deploy reliability as unknown. Invention: a dedicated task to surface the unknown, document the failure mode, and accept-or-mitigate. Spotlight 正直 (honesty).
5. **W5.44 — D-day minute-by-minute runbook.** The brief said "submission checklist + buffer." Invention: an actual minute-by-minute runbook from 6 AM to 2 PM CDT with contingency branches. The single most important task for actually hitting submit. Spotlight 多重視点 (multiple selves): future-Shawn at 8:30 AM with a broken deploy needs this exact document.
6. **W5.51 — Live-demo URL embedded in README above the fold.** The brief Spotlight prompt asked: "submission has 4 deliverables; what's the 5th?" Answer: a public demo URL judges click BEFORE opening the video. Surfaces in W5.51 (README) and W5.45 (Devpost form). Spotlight 構造 (structural).
7. **W5.52 — Submission state archive bundle.** Beyond git tag, a frozen documentation bundle for the "future-Shawn 6 months from now" use case. Spotlight 遺産 (legacy).

## Post-W5 Opportunities (Explicitly Deferred)

- Localization of submission video (Spanish captions/voiceover)
- YouTube + Vimeo upload optimization beyond Devpost minimum
- HackFW post-submission engagement (Discord, Q&A, judge follow-ups) — separate plan post-May 2
- Dallas city deployment (S14+)
- Analytics instrumentation (defer to S14+)
- Canary release framework (S14+)
- Real load testing under sustained 100s-of-concurrent-users (S14+)

## Explicitly Not in Scope

- Any net-new product feature (W4 was the build gate; W5 is package-only)
- Any new design changes (W4 was the polish gate)
- Schema/architectural refactors
- Any task that risks regressing the 5,189 test count display
- Any change to internal repo / DB / Python module names (still "montgowork" internally per visual-rebirth-plan decision)

## Critical-Path DAG (deadline-anchored)

```
W5.1 (copy thesis SoT) ──> W5.2 (README hero) ──> W5.6 (README final)
                       └─> W5.7 (press kit core) ──> W5.10 (Wall stills) [needs W5.36]
                       └─> W5.13 (demo script) ──> W5.16 (narration)
                       └─> W5.18 (video script) ──> W5.19 (record) [needs W5.36] ──> W5.21 (edit)
                       └─> W5.23 (Devpost description)

W5.36 (production deploy) ──> W5.10, W5.19, W5.20, W5.28, W5.31, W5.32, W5.33, W5.34, W5.46

W5.50 (link-check) ──> W5.6 (README final), W5.48 (submit blocker)

W5.35 (consistency sweep) ──> W5.48 (submit blocker)

W5.31 + W5.32 + W5.33 + W5.46 ──> W5.48 (final smoke gates)

W5.45 (dry-run) + W5.47 (git tag) ──> W5.48 (submit)

W5.48 (SUBMIT, T=9:00 AM CDT May 2) ──> W5.49 (Reddit), W5.52 (archive)

HARD DEADLINE: T=2:00 PM CDT May 2.
TARGET: T=9:00 AM CDT May 2 (5h buffer).
```

## Sprint Validation

```bash
bpsai-pair engage plans/backlogs/sprint-w5-submission.md --dry-run
```
