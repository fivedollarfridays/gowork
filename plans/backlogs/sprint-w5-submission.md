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

---

# ENRICHMENT — Revision v2 (2026-04-27, append-only)

**Append-only.** W5.1–W5.52 above are unchanged. The following 58 tasks (W5.53–W5.110) deepen submission-quality across gap categories: Devpost field cataloging, GitHub repo polish (badges, CHANGELOG, ROADMAP, COC, contributing, templates), README badges + polish, press kit deeper polish (high-res bundle, brand assets, team bios, downloadable zip), video deeper polish (voice-over recording, B-roll, captions human-transcribed, thumbnail, dual-host upload), D-day minute-by-minute runbook with contingency branches, post-submission announcements, FW DAO bounty research, post-launch analytics, accessibility verification final.

**Revised totals (v2):** 110 tasks, ~768 Cx, P0: 65, P1: 38, P2: 7. Hard cap (130) unbreached.

---

## Phase 13: Devpost Form Field Cataloging

### W5.53 — Devpost: complete field-by-field catalog with length limits | Cx: 5 | P0

**Description:**
Author `docs/submission/devpost-fields-catalog.md` — exhaustive enumeration of every Devpost field with character limit, format, required-or-optional, and which W5 doc supplies the content. Fields: Project title, Tagline, Project URL, GitHub URL, Demo video URL, Project description (sections), Tags, Categories, Built-with technologies, Hackathon eligibility (US-only/age/team), Team members, Prizes targeted (Reindustrialization track? Workforce track?), Submitted-by-deadline buffer field. Cite limits from a fresh dry-run inspection of the form (DOM measurement). Each field has a row: Field | Limit | Format | Source doc | Notes.

**AC:**
- [ ] `docs/submission/devpost-fields-catalog.md` exists
- [ ] All ≥15 Devpost fields enumerated
- [ ] Character limit measured for each text field (DOM-inspected, not guessed)
- [ ] Format documented (plain / markdown / WYSIWYG / file upload / dropdown)
- [ ] Each field cites its W5 source doc (W5.23 description, W5.24 tags, etc.)
- [ ] Hackathon eligibility fields explicitly addressed (US-only, age, team)
- [ ] Track selection field documented (Reindustrialization primary, others if applicable)

**Depends on:** W5.45 (dry-run gives the field measurements)

---

### W5.54 — Devpost: title + tagline length-limit verification | Cx: 2 | P0

**Description:**
Verify project title and tagline candidates fit Devpost's hard limits (typically title ≤60 chars, tagline ≤120 chars — confirm via dry-run inspection). Candidates: Title `"GoWork"` (6 chars; safe). Tagline candidates: `"Workforce infrastructure for any American city."` (49 chars; safe) OR alternate framings if judges-side scanability matters. Document chosen title + tagline in `docs/submission/devpost-title-tagline.md` with both verbatim and char counts.

**AC:**
- [ ] `docs/submission/devpost-title-tagline.md` exists
- [ ] Final title within Devpost limit (with limit cited)
- [ ] Final tagline within Devpost limit (with limit cited)
- [ ] Char count for each documented
- [ ] Title + tagline derive from `docs/copy-thesis.md` (cited)

**Depends on:** W5.1, W5.53

---

### W5.55 — Devpost: video format + codec + size + duration verification | Cx: 4 | P0

**Description:**
Verify W5.21 final video meets Devpost upload constraints. Devpost typically accepts MP4 (H.264 + AAC), max ~500MB, max ~5min runtime. Run `ffprobe docs/submission-video/full-final.mp4` and document codec, container, size, duration, resolution, bitrate in `docs/submission/video-spec-verification.md`. Additionally verify YouTube/Vimeo upload alternative format (Devpost commonly accepts a YouTube/Vimeo URL instead of direct upload — confirm the form's actual behavior).

**AC:**
- [ ] `docs/submission/video-spec-verification.md` exists
- [ ] ffprobe output captured: codec (H.264 expected), audio (AAC), container (MP4), duration, resolution, bitrate
- [ ] File size <50MB confirmed (matches W5.21 AC)
- [ ] Duration ≤5min confirmed
- [ ] Devpost video field accepts: direct upload? URL? both? — documented
- [ ] If URL-only: YouTube + Vimeo URLs reserved (W5.78, W5.79)

**Depends on:** W5.21, W5.45

---

### W5.56 — Devpost: built-with exhaustive cross-check vs package.json | Cx: 3 | P1

**Description:**
Strengthen W5.26 by running a deterministic cross-check: parse `frontend/package.json` dependencies + devDependencies, parse `backend/requirements.txt`, intersect with `docs/submission/devpost-built-with.md`. Any production dep absent from devpost-built-with → flag for inclusion or explicit exclusion-with-reason. Output `docs/submission/built-with-diff.md` showing additions/exclusions.

**AC:**
- [ ] `docs/submission/built-with-diff.md` exists
- [ ] Every `dependencies` (not devDependencies) entry in `frontend/package.json` either in devpost-built-with OR explicitly excluded with reason
- [ ] Every entry in `backend/requirements.txt` either in devpost-built-with OR explicitly excluded
- [ ] No phantom entries (in devpost-built-with but not actually used)
- [ ] Cross-check is deterministic (re-runnable)

**Depends on:** W5.26

---

### W5.57 — Devpost: hackathon eligibility confirmation | Cx: 2 | P0

**Description:**
HackFW 2026 has eligibility rules (typically US residency, ≥18, team-size cap). Confirm GoWork's team meets all rules. Document verifications in `docs/submission/eligibility-confirmation.md`: each team member's residency status (state), age confirmation, team-size compliance. Cite the HackFW rules URL. Any non-conformance is a P0 blocker.

**AC:**
- [ ] `docs/submission/eligibility-confirmation.md` exists
- [ ] HackFW eligibility rules URL cited
- [ ] Each team member verified against each rule
- [ ] Team size within cap
- [ ] Any non-conformance: blocker logged + remediation path documented

**Depends on:** W5.27

---

### W5.58 — Devpost: prizes/tracks targeted decision | Cx: 2 | P0

**Description:**
Decide which HackFW prize tracks to target. Per brief: 1st = $2,400 + $300 AI credits + $1,500 ThinkLab Accelerator Seat. Reindustrialization track is primary; check for additional tracks (Workforce, AI/ML, Civic Tech, Open Source). Document chosen tracks + rationale per track in `docs/submission/prizes-targeted.md`.

**AC:**
- [ ] `docs/submission/prizes-targeted.md` exists
- [ ] Reindustrialization track marked primary
- [ ] Additional tracks listed with fit rationale (or explicit "not targeting")
- [ ] Top prize ($2,400 + ThinkLab seat) explicitly named as goal

**Depends on:** W5.24

---

### W5.59 — Devpost: draft/preview save workflow documented | Cx: 2 | P1

**Description:**
Document Devpost's draft-save / preview workflow. During W5.45 dry-run, capture screenshots of: draft state, preview view (what judges see), edit-after-submit policy. Save to `docs/submission/devpost-preview-workflow.md`. This protects against blind-clicking Submit; ensure preview rendered correctly before W5.48.

**AC:**
- [ ] `docs/submission/devpost-preview-workflow.md` exists
- [ ] Draft-save mechanism documented
- [ ] Preview view documented (with screenshot)
- [ ] Edit-after-submit policy noted (can we fix typos post-submit?)

**Depends on:** W5.45

---

## Phase 14: GitHub Repo Polish

### W5.60 — GitHub: LICENSE file verified at repo root | Cx: 1 | P0

**Description:**
Confirm `LICENSE` file exists at repo root with MIT license text + copyright line current to 2026 + correct copyright holder (per `docs/copy-thesis.md` and `docs/press-kit.md`). If missing or stale, create/update.

**AC:**
- [ ] `LICENSE` exists at repo root
- [ ] MIT license text present (standard SPDX format)
- [ ] Copyright year is 2026
- [ ] Copyright holder matches press-kit team list
- [ ] No conflicting license text

**Depends on:** none

---

### W5.61 — GitHub: CHANGELOG.md initialized for v0.1.0-hackfw-submission | Cx: 4 | P0

**Description:**
Create `CHANGELOG.md` at repo root following Keep-a-Changelog format. Initial section: `## [0.1.0-hackfw-submission] — 2026-05-02`. Document W1–W4 outputs (Wall, Mapbox chapters 1–5, interactive chapters 6–10, life layers) + W5 outputs (submission package). Link to git tag.

**AC:**
- [ ] `CHANGELOG.md` exists at repo root
- [ ] Keep-a-Changelog format used
- [ ] `[0.1.0-hackfw-submission]` section dated 2026-05-02
- [ ] Added/Changed/Fixed sections populated for W1–W5
- [ ] Links to GitHub tag URL
- [ ] No "MontGoWork" in changelog (use "GoWork")

**Depends on:** W5.1

---

### W5.62 — GitHub: ROADMAP.md (post-hackathon vision) | Cx: 4 | P1

**Description:**
Create `ROADMAP.md` at repo root documenting post-HackFW vision: Dallas as next city (S14), analytics instrumentation, canary release framework, FW DAO bounty integrations, accessibility deep-dive, video localization. Show 30-day, 90-day, 1-year horizons. Each item links to a future plan/sprint placeholder.

**AC:**
- [ ] `ROADMAP.md` exists at repo root
- [ ] 30-day horizon: 3+ items
- [ ] 90-day horizon: 3+ items
- [ ] 1-year horizon: 3+ items
- [ ] Each horizon's items have a 1-line "what + why"
- [ ] Cites `docs/copy-thesis.md` for the long-term vision sentence

**Depends on:** W5.1

---

### W5.63 — GitHub: CODE_OF_CONDUCT.md | Cx: 2 | P1

**Description:**
Add `CODE_OF_CONDUCT.md` at repo root using Contributor Covenant 2.1 template with project-specific contact email (per press-kit). Standard signal of healthy OSS hygiene that some judges scan for.

**AC:**
- [ ] `CODE_OF_CONDUCT.md` exists at repo root
- [ ] Contributor Covenant 2.1 used
- [ ] Project-specific contact email filled in (not placeholder)
- [ ] Renders cleanly on GitHub

**Depends on:** W5.12

---

### W5.64 — GitHub: CONTRIBUTING.md | Cx: 3 | P1

**Description:**
Add `CONTRIBUTING.md` at repo root. Sections: how to set up dev env (link to `docs/setup.md`), how to run tests (cite 5,189 number + commands), commit message conventions, PR review process, code of conduct link, license note. Keep concise (<200 lines).

**AC:**
- [ ] `CONTRIBUTING.md` exists at repo root
- [ ] Setup link works (relative to repo root)
- [ ] Tests section cites 5,189 + correct pytest/vitest commands
- [ ] Commit conventions documented (link to existing conv if any, else conventional-commits)
- [ ] PR review process described
- [ ] CODE_OF_CONDUCT.md linked
- [ ] No "MontGoWork" anywhere

**Depends on:** W5.63

---

### W5.65 — GitHub: issue templates (.github/ISSUE_TEMPLATE/*) | Cx: 3 | P1

**Description:**
Add issue templates under `.github/ISSUE_TEMPLATE/`: `bug_report.md`, `feature_request.md`, `accessibility_issue.md`. Each with YAML frontmatter (name, about, title prefix, labels). Standard format.

**AC:**
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` exists with valid frontmatter
- [ ] `.github/ISSUE_TEMPLATE/feature_request.md` exists
- [ ] `.github/ISSUE_TEMPLATE/accessibility_issue.md` exists (signals a11y commitment)
- [ ] Each renders correctly when filing a new issue on GitHub
- [ ] No "MontGoWork" in template bodies

**Depends on:** none

---

### W5.66 — GitHub: PR template (.github/PULL_REQUEST_TEMPLATE.md) | Cx: 2 | P1

**Description:**
Add `.github/PULL_REQUEST_TEMPLATE.md` with sections: Summary, Test plan, Acceptance criteria checklist (ties to PairCoder workflow), Screenshots (if UI), Risk/Rollback. Renders as the default PR body.

**AC:**
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` exists
- [ ] Sections: Summary / Test plan / AC / Screenshots / Risk
- [ ] Renders as default PR body when opening PR on GitHub
- [ ] No "MontGoWork"

**Depends on:** none

---

### W5.67 — GitHub: SECURITY.md verified or created | Cx: 2 | P1

**Description:**
Verify `SECURITY.md` exists at repo root (or `.github/SECURITY.md`). If missing, create it: how to report vulnerabilities, response SLA, supported versions. Reference HackFW submission as the in-scope version.

**AC:**
- [ ] `SECURITY.md` exists (root or .github/)
- [ ] Vulnerability reporting email documented
- [ ] Response SLA stated (e.g., 48h acknowledgment)
- [ ] Supported versions table includes 0.1.0-hackfw-submission
- [ ] Renders on GitHub Security tab

**Depends on:** none

---

### W5.68 — GitHub: dependabot.yml verified | Cx: 2 | P2

**Description:**
Verify `.github/dependabot.yml` exists with daily/weekly schedules for npm + pip ecosystems. If missing, create with sane defaults. This adds a green badge candidate (Dependabot enabled).

**AC:**
- [ ] `.github/dependabot.yml` exists
- [ ] npm ecosystem configured (frontend/)
- [ ] pip ecosystem configured (backend/)
- [ ] Schedule set (weekly is fine)
- [ ] Dependabot Security alerts enabled in GitHub settings (manual UI step, documented)

**Depends on:** none

---

### W5.69 — GitHub: Actions CI workflow verified for build + test | Cx: 3 | P1

**Description:**
Verify `.github/workflows/*.yml` runs build + test on PRs. Confirm workflows for backend (pytest) + frontend (vitest) + lint exist. If a green CI badge is achievable, add to README. Document workflow filenames in `docs/submission/ci-workflows.md`.

**AC:**
- [ ] `docs/submission/ci-workflows.md` exists
- [ ] Backend test workflow runs pytest (4,080 tests)
- [ ] Frontend test workflow runs vitest (1,109 tests)
- [ ] Lint workflow runs (ruff/eslint)
- [ ] All workflows green on `main` branch
- [ ] README badges for each workflow status (deferred to W5.74)

**Depends on:** none

---

### W5.70 — GitHub: repo description (60-char) + topics + About link | Cx: 2 | P1

**Description:**
Update GitHub repo metadata via web UI (or `gh` CLI): Description ≤60 chars cites tagline ("Workforce infrastructure for any American city."); Topics: workforce, civic-tech, hackathon, hackfw-2026, reindustrialization, mapbox, nextjs, fastapi, open-source; Website (About sidebar) → production URL. Document the chosen values in `docs/submission/github-repo-metadata.md`.

**AC:**
- [ ] Repo description updated to ≤60 chars (cite tagline)
- [ ] Repo topics list includes ≥7 of the named topics
- [ ] Website field set to production URL (W5.36)
- [ ] `docs/submission/github-repo-metadata.md` documents chosen values
- [ ] No "MontGoWork" in description

**Depends on:** W5.36

---

### W5.71 — GitHub: branch protection rules on main (post-merge) | Cx: 2 | P2

**Description:**
After all W5 merges land, enable branch protection on `main`: require PR reviews (1+), require status checks (CI green), require linear history. Document the chosen rules in `docs/submission/branch-protection.md`. Skip if pre-submit time is short (P2).

**AC:**
- [ ] Branch protection rules enabled on main
- [ ] At minimum: required CI checks
- [ ] `docs/submission/branch-protection.md` documents rules
- [ ] Decision logged: enable pre-submit OR post-submit

**Depends on:** W5.69

---

## Phase 15: README Deeper Polish

### W5.72 — README: hero screenshot from Wall (above the fold) | Cx: 3 | P0

**Description:**
Strengthen W5.2 by ensuring the hero screenshot is the most editorial frame from Chapter 2 (City Arrival) or Chapter 7 (The Path). Place within first 15 lines of README. Image must render at GitHub's default rendered width without overflow. Caption with chapter number + scene label.

**AC:**
- [ ] Hero screenshot embedded within first 15 lines
- [ ] Source: `docs/press-kit/wall-chapter-02-city-arrival.png` OR `wall-chapter-07-the-path.png`
- [ ] Caption present (e.g., "Chapter 2 — City Arrival")
- [ ] Renders cleanly on GitHub mobile + desktop
- [ ] File path is a relative repo path (works on GitHub renderer)

**Depends on:** W5.2, W5.10

---

### W5.73 — README: live demo URL above the fold (strengthen W5.51) | Cx: 2 | P0

**Description:**
Reinforce W5.51 by placing the live demo URL within the first 30 lines of README, formatted as a prominent call-to-action. Caption: "Click to scroll the Wall." Link should be a complete `https://` URL (no relative path).

**AC:**
- [ ] Live demo URL within first 30 lines of README
- [ ] Formatted as CTA block (bold, or H3)
- [ ] Full https:// URL embedded (from W5.36)
- [ ] CTA caption invites scroll-driven exploration
- [ ] Tested by reading the rendered README on GitHub

**Depends on:** W5.51, W5.36

---

### W5.74 — README: badges row (CI, license, tests, deploy) | Cx: 4 | P1

**Description:**
Add a badges row in README near top: CI status (per W5.69 workflows), license (MIT), test count (5,189), deploy status (Vercel), Dependabot enabled. Use shields.io for static + dynamic badges. Each badge links to its source (CI Actions tab, LICENSE, etc.).

**AC:**
- [ ] Badges row exists in README within first 25 lines
- [ ] CI status badge present and linking to Actions tab
- [ ] License badge: `MIT`
- [ ] Tests badge: `tests-5189`
- [ ] Deploy badge (Vercel) if available
- [ ] Each badge clickable (linked to source)
- [ ] No "MontGoWork" in any badge label

**Depends on:** W5.69, W5.36

---

### W5.75 — README: 60s teaser link + full video link section | Cx: 3 | P1

**Description:**
Add a `## Watch` section to README with: 60s teaser link (YouTube/Vimeo URL from W5.78 or embed-friendly), full ~3.5min video link (W5.79). Each with a 1-line caption. If only one is uploaded by D-day, ship the section with the available one and a note.

**AC:**
- [ ] `## Watch` section in README
- [ ] 60s teaser link present (placeholder until W5.78 confirms)
- [ ] Full video link present (placeholder until W5.79 confirms)
- [ ] Caption per link
- [ ] Section above press-kit reference

**Depends on:** W5.22, W5.21

---

### W5.76 — README: how-to-deploy section (Vercel + Mapbox) | Cx: 4 | P1

**Description:**
Add a `## Deploy Your Own` section to README documenting: Vercel deployment steps (one-click button if available), required env vars (`NEXT_PUBLIC_MAPBOX_TOKEN`), custom Mapbox style config, backend deploy notes. Link to `docs/setup.md` for full env var list.

**AC:**
- [ ] `## Deploy Your Own` section exists
- [ ] Vercel deploy steps documented (manual or one-click)
- [ ] `NEXT_PUBLIC_MAPBOX_TOKEN` requirement called out with how-to-get-one link
- [ ] Custom Mapbox style note (or default style fallback documented)
- [ ] Backend deploy note (Railway / chosen host)
- [ ] Link to `docs/setup.md`

**Depends on:** W5.4, W5.36

---

### W5.77 — README: city framework section + acknowledgments | Cx: 3 | P1

**Description:**
Add a `## City Framework` section to README explaining the multi-city architecture (Montgomery as origin, Fort Worth as primary deploy, Dallas as next target — keyed off `cities/{slug}/...` pattern from W4). Add `## Acknowledgments` crediting Worldwide Vibes (origin), HackFW 2026, contributors, and PairCoder + Claude. Press kit link present.

**AC:**
- [ ] `## City Framework` section explains multi-city pattern in 2–3 paragraphs
- [ ] Cities listed: Montgomery, Fort Worth, Dallas (next)
- [ ] `## Acknowledgments` section present
- [ ] Worldwide Vibes credited as origin
- [ ] HackFW 2026 credited as headline
- [ ] PairCoder + Claude credited
- [ ] Press kit link (`docs/press-kit.md`) present
- [ ] Carlos persona briefly explained (1 sentence)

**Depends on:** W5.5, W5.7

---

## Phase 16: Video Deeper Polish

### W5.78 — Video: published to YouTube (unlisted/public, captions enabled) | Cx: 5 | P0

**Description:**
Upload `full-final.mp4` to YouTube. Title: "GoWork — Workforce infrastructure for any American city (HackFW 2026)". Description: tagline + production URL + GitHub URL + Devpost URL placeholder. Visibility: public OR unlisted (decide based on Devpost requirement). Upload `.srt` from W5.21 as closed captions. Capture YouTube URL.

**AC:**
- [ ] YouTube upload complete
- [ ] Title cites tagline
- [ ] Description includes production URL + GitHub URL
- [ ] `.srt` uploaded as captions (CC button works in player)
- [ ] Visibility documented in `docs/submission/video-hosts.md`
- [ ] YouTube URL captured
- [ ] No "MontGoWork" in title or description

**Depends on:** W5.21

---

### W5.79 — Video: published to Vimeo as backup host | Cx: 4 | P1

**Description:**
Upload `full-final.mp4` to Vimeo as a backup host (in case YouTube has an issue or Devpost prefers Vimeo). Same title + description as YouTube. Capture Vimeo URL in `docs/submission/video-hosts.md`.

**AC:**
- [ ] Vimeo upload complete
- [ ] Title + description match YouTube
- [ ] Captions uploaded (or noted absence with reason)
- [ ] Vimeo URL captured in `docs/submission/video-hosts.md`
- [ ] Tested in browser (plays, no auth wall for unlisted)

**Depends on:** W5.21

---

### W5.80 — Video: voice-over recording with noise reduction | Cx: 6 | P0

**Description:**
Strengthen W5.19 by recording the voice-over as a separate audio track (vs live-with-screen-record). Use a USB mic or headset; record in a quiet room. Apply noise reduction in Audacity (or built-in tool). Save raw + processed to `docs/submission-video/voiceover-raw.wav` + `voiceover-processed.wav`. This separation allows redo of voice-over without re-recording the screen.

**AC:**
- [ ] `docs/submission-video/voiceover-raw.wav` exists
- [ ] `docs/submission-video/voiceover-processed.wav` exists
- [ ] Noise reduction applied (audible difference)
- [ ] Voice-over follows W5.18 script verbatim
- [ ] Length ≤3:50
- [ ] Mono or stereo decision documented
- [ ] No "MontGoWork" voiceover slip

**Depends on:** W5.18

---

### W5.81 — Video: B-roll capture (FW landmarks, with attribution) | Cx: 5 | P2

**Description:**
Optional but Spotlight-worthy: capture or source 30–60s of B-roll showing Fort Worth landmarks (Sundance Square, Stockyards, downtown skyline). Use Pexels / Unsplash / Pixabay for stock footage with attribution. Cut into the full video at chapter transitions for editorial breath. If sourcing stock, document attribution in `docs/submission-video/b-roll-attributions.md`.

**AC:**
- [ ] B-roll source documented (own footage OR stock with attribution)
- [ ] `docs/submission-video/b-roll-attributions.md` exists if stock used
- [ ] B-roll integrated into final cut OR explicit decision to skip
- [ ] If skipped: rationale logged
- [ ] No copyright violation risk

**Depends on:** W5.21

---

### W5.82 — Video: editing project file backed up | Cx: 2 | P1

**Description:**
Save the editing software project file (DaVinci Resolve `.drp`, ScreenStudio session, Premiere `.prproj`, etc.) to `docs/submission-video/_project-file/`. This protects against re-edit-from-scratch if a fix is needed post-submit. Note format + version + opening instructions in `docs/submission-video/_project-file/README.md`.

**AC:**
- [ ] Project file saved under `docs/submission-video/_project-file/`
- [ ] README.md documents software + version + open instructions
- [ ] Linked source media file paths verified (relative refs, not absolute)
- [ ] File committed to git (if size permits) OR archived externally with link

**Depends on:** W5.21

---

### W5.83 — Video: captions human-transcribed and reviewed | Cx: 5 | P0

**Description:**
Strengthen W5.21 captions. If `.srt` was auto-generated (from YouTube auto-transcribe or whisper), human-review every line for accuracy (proper nouns, "Carlos", "Fort Worth", "GoWork"). Auto-transcribe routinely mangles brand names — review is non-negotiable. Save reviewed `.srt` and document review in `docs/submission-video/captions-review.md`.

**AC:**
- [ ] Reviewed `.srt` saved to `docs/submission-video/full-final.srt`
- [ ] Every "GoWork" mention transcribed correctly (no "Go Work" / "go work")
- [ ] Every "Carlos" mention correct
- [ ] Every "Fort Worth" correct (no "FortWorth" / "Forth Worth")
- [ ] Every "HackFW" correct
- [ ] Every test number correct (5,189 not 1,808)
- [ ] `docs/submission-video/captions-review.md` lists corrections made

**Depends on:** W5.21

---

### W5.84 — Video: thumbnail designed (1280×720) | Cx: 4 | P1

**Description:**
Design a custom YouTube thumbnail (1280×720). Hero question or tagline as text overlay; Wall screenshot from Chapter 2 or 8 as background. Text legible at small size. Save as `docs/submission-video/thumbnail.png`. Upload as YouTube thumbnail (W5.78 prerequisite or post-upload edit).

**AC:**
- [ ] `docs/submission-video/thumbnail.png` exists at 1280×720
- [ ] Text legible at 240×135 (YouTube preview size)
- [ ] No "MontGoWork" anywhere in thumbnail
- [ ] Cites tagline OR hero question
- [ ] Uploaded as YouTube thumbnail

**Depends on:** W5.10, W5.78

---

### W5.85 — Video: closed-caption test in YouTube player | Cx: 2 | P1

**Description:**
After W5.78 + W5.83, manually test CC in YouTube player on desktop + mobile. Verify captions render at correct timestamps, are legible, no encoding issues (proper apostrophes, accented characters in Spanish "Spanish-fluent" etc.). Document in `docs/submission-video/cc-test.md`.

**AC:**
- [ ] `docs/submission-video/cc-test.md` exists
- [ ] Desktop CC test PASS
- [ ] Mobile CC test PASS
- [ ] No encoding artifacts visible
- [ ] Timestamps correct (audio sync within 200ms)

**Depends on:** W5.78, W5.83

---

### W5.86 — Video: audio mix balanced (voice-over over screen capture) | Cx: 3 | P1

**Description:**
Verify voice-over is the dominant audio (-12 to -6 dBFS); screen capture audio (mouse clicks, scroll sounds) muted or ducked. Apply normalization. Confirm playback consistent across device speakers (laptop, phone, headphones). Document final mix levels in `docs/submission-video/audio-mix-notes.md`.

**AC:**
- [ ] Voice-over peak between -12 and -6 dBFS
- [ ] Screen capture audio: muted OR ducked ≥-20 dBFS below voice
- [ ] Normalized (no clipping)
- [ ] Tested on 2+ playback devices
- [ ] `docs/submission-video/audio-mix-notes.md` documents levels

**Depends on:** W5.21, W5.80

---

## Phase 17: D-Day Minute-by-Minute Runbook (Strengthen W5.44)

### W5.87 — D-day: T-72h pre-submit final smoke checklist | Cx: 2 | P0

**Description:**
Append `## T-72h (April 29, 9:00 AM CDT)` block to `docs/submission/d-day-runbook.md`. Tasks: final pytest + vitest run; cross-browser smoke; production URL spot check; verify all submission docs exist. Anything failing → P0 fix-forward window opens.

**AC:**
- [ ] T-72h block in d-day-runbook
- [ ] Test suite run command listed
- [ ] Cross-browser smoke step listed
- [ ] Each step has owner + success criterion
- [ ] If failure: fix-forward decision tree referenced

**Depends on:** W5.44

---

### W5.88 — D-day: T-48h video upload final + double-host verify | Cx: 2 | P0

**Description:**
Append `## T-48h (April 30, 9:00 AM CDT)` block to runbook. Tasks: confirm YouTube upload public/unlisted-as-needed; confirm Vimeo upload as backup; capture both URLs; CC test; thumbnail uploaded.

**AC:**
- [ ] T-48h block in d-day-runbook
- [ ] YouTube URL confirmed accessible
- [ ] Vimeo URL confirmed accessible
- [ ] Both URLs in `docs/submission/video-hosts.md`
- [ ] CC + thumbnail verified

**Depends on:** W5.44, W5.78, W5.79

---

### W5.89 — D-day: T-24h Devpost preview ready | Cx: 2 | P0

**Description:**
Append `## T-24h (May 1, 9:00 AM CDT)` block. Tasks: open Devpost form; paste all field contents from W5.23–W5.27 + W5.53 catalog; save draft; preview the public-facing version; screenshot preview for archive. NO submit yet.

**AC:**
- [ ] T-24h block in d-day-runbook
- [ ] All Devpost fields filled in draft
- [ ] Preview viewed and screenshotted
- [ ] Screenshot saved to `docs/submission/devpost-preview-T24.png`
- [ ] **NO submit click confirmed**

**Depends on:** W5.44, W5.45

---

### W5.90 — D-day: T-12h dry-run submission rehearsal | Cx: 2 | P0

**Description:**
Append `## T-12h (May 1, 9:00 PM CDT)` block. Tasks: full rehearsal of submission steps (open Devpost, scroll to submit button, mentally walk through pre-submit checks); open backup tabs (staging URL, video URLs); confirm laptop charged + backup laptop ready. Sleep early.

**AC:**
- [ ] T-12h block in d-day-runbook
- [ ] Rehearsal walkthrough documented
- [ ] Backup tabs list documented
- [ ] Laptop + backup laptop confirmed ready
- [ ] Sleep-by time noted

**Depends on:** W5.44

---

### W5.91 — D-day: T-6h deploy verification (May 2, 3 AM CDT) | Cx: 2 | P0

**Description:**
Append `## T-6h (May 2, 3:00 AM CDT)` block. Tasks: production URL pings (curl to `/`, `/assess`, `/plan`); backend `/health` ping; Mapbox tile request spot check. If anything regressed overnight, escalate immediately.

**AC:**
- [ ] T-6h block in d-day-runbook
- [ ] Production URL ping commands listed
- [ ] Backend health ping command
- [ ] Escalation path if failure (rollback to staging W5.38)

**Depends on:** W5.44

---

### W5.92 — D-day: T-3h Lighthouse final pass | Cx: 2 | P0

**Description:**
Append `## T-3h (May 2, 6:00 AM CDT)` block. Run Lighthouse on production URL one last time. Floors: Perf ≥85, A11y ≥95, Best Practices ≥90, SEO ≥90. Any below floor → rollback to staging.

**AC:**
- [ ] T-3h block in d-day-runbook
- [ ] Lighthouse run command listed
- [ ] Floors restated
- [ ] Rollback decision tree referenced

**Depends on:** W5.44, W5.31

---

### W5.93 — D-day: T-2h contingency-status check | Cx: 2 | P0

**Description:**
Append `## T-2h (May 2, 7:00 AM CDT)` block. Tasks: Mapbox status page check (status.mapbox.com); Devpost status check; Vercel status; GitHub status. Any external service red → activate corresponding contingency branch (W5.95).

**AC:**
- [ ] T-2h block in d-day-runbook
- [ ] Mapbox status URL listed
- [ ] Devpost status URL listed
- [ ] Vercel + GitHub status URLs listed
- [ ] Contingency activation matrix referenced

**Depends on:** W5.44, W5.95

---

### W5.94 — D-day: T-1h brand sweep final (no MontGoWork) | Cx: 2 | P0

**Description:**
Append `## T-1h (May 2, 8:00 AM CDT)` block. Run W5.35 consistency sweep one final time across README, press kit, video metadata, Devpost form. Single line: any "MontGoWork" or "1,808" or "1,391" or "417 tests" → P0 block submit until fixed.

**AC:**
- [ ] T-1h block in d-day-runbook
- [ ] W5.35 sweep command embedded
- [ ] Zero matches required
- [ ] If any match: rollback decision documented

**Depends on:** W5.44, W5.35

---

### W5.95 — D-day contingency branches: 5 failure modes | Cx: 5 | P0

**Description:**
**Spotlight invention.** Append `## Contingency Branches` section to `docs/submission/d-day-runbook.md`. Five failure modes with explicit recovery: (1) Production deploy 500s → rollback to staging URL (W5.38); (2) Video upload fails to YouTube → use Vimeo URL (W5.79); (3) Mapbox tiles down → static fallback page (link to chapter-still slideshow); (4) Devpost down → emergency contact phone numbers + email (HackFW organizer); (5) GitHub down → repo accessible via clone of last-pulled local. Each branch has trigger / detection / action / success criterion.

**AC:**
- [ ] `## Contingency Branches` section in d-day-runbook
- [ ] All 5 failure modes documented
- [ ] Each has trigger/detection/action/success
- [ ] Phone + email for HackFW organizer captured
- [ ] Phone + email for backup team member captured
- [ ] Decision authority documented (Shawn primary, fallback Ren)

**Depends on:** W5.44, W5.38, W5.79

---

### W5.96 — D-day: T+1h post-submit immediate verification | Cx: 2 | P1

**Description:**
Append `## T+1h (May 2, 10:00 AM CDT)` block. Tasks: confirm Devpost submission email received; visit submitted entry on Devpost (public URL) and screenshot; spot-check production URL still serving; spot-check video URLs still playable. If anything broken: file P0 hotfix.

**AC:**
- [ ] T+1h block in d-day-runbook
- [ ] Submission email screenshot saved
- [ ] Public Devpost entry URL captured
- [ ] Production + video URLs spot-checked
- [ ] Hotfix path documented if needed

**Depends on:** W5.44, W5.48

---

## Phase 18: Post-Submission Announcements + Engagement

### W5.97 — Post-submit: Twitter announcement with screenshots | Cx: 3 | P1

**Description:**
Author Twitter announcement post in `docs/submission/social-twitter-draft.md`. Format: Tweet + 4 image attachments (Wall stills from W5.10). Tweet: hero question + tagline + Devpost link + GitHub link + production URL. Thread with 2–3 follow-up tweets covering: tech stack, FW positioning, HackFW track. Schedule for post-W5.48.

**AC:**
- [ ] `docs/submission/social-twitter-draft.md` exists
- [ ] Main tweet within 280-char limit
- [ ] 4 image attachments referenced (Wall stills)
- [ ] 2–3 thread tweets drafted
- [ ] Devpost + GitHub + production URLs included
- [ ] No "MontGoWork"
- [ ] Hashtags: #HackFW2026 #Reindustrialization #OpenSource

**Depends on:** W5.48, W5.10

---

### W5.98 — Post-submit: LinkedIn professional announcement | Cx: 3 | P1

**Description:**
Author LinkedIn post draft in `docs/submission/social-linkedin-draft.md`. Longer-form than Twitter, professional tone: career story (career-center observation → workforce navigator → HackFW), TDD discipline highlight (5,189 tests), open-source MIT, call for collaborators / FW DAO connection. 1500–3000 char range.

**AC:**
- [ ] `docs/submission/social-linkedin-draft.md` exists
- [ ] 1500–3000 chars
- [ ] Career-story narrative present
- [ ] 5,189 tests cited
- [ ] MIT open-source mentioned
- [ ] Call-to-action (collaborators, DAO bounty)
- [ ] No "MontGoWork"

**Depends on:** W5.48

---

### W5.99 — Post-submit: r/civictechnology Reddit post (separate from r/PairCoder) | Cx: 3 | P1

**Description:**
W5.49 covers r/PairCoder (own-subreddit) and 2 others. Add a dedicated r/civictechnology post draft in `docs/submission/social-reddit-civictech.md`. Different tone: civic-tech focus, cite policy implications (workforce mobility, benefits-cliff math), invite policy/civic feedback.

**AC:**
- [ ] `docs/submission/social-reddit-civictech.md` exists
- [ ] Civic-tech framing in opening paragraph
- [ ] Benefits-cliff math example cited
- [ ] Policy implications surfaced
- [ ] Devpost + GitHub URLs embedded
- [ ] r/civictechnology rules respected (no spam-self-promo flagging)

**Depends on:** W5.48

---

### W5.100 — Post-submit: thank-you to team + contributors | Cx: 2 | P1

**Description:**
Author `docs/submission/thank-you.md`. Personal thank-you note to: team members (Kevin, Shawn, Ren, any W1–W4 contributors), Worldwide Vibes (origin), HackFW organizers, Anthropic / Claude (tooling), PairCoder community. Email + posted as a GitHub Discussion (or pinned issue) for public visibility.

**AC:**
- [ ] `docs/submission/thank-you.md` exists
- [ ] All teammates named
- [ ] Worldwide Vibes credited
- [ ] HackFW organizers thanked
- [ ] Tooling (Claude, PairCoder) thanked
- [ ] Posted as GitHub Discussion or pinned issue OR email-sent log

**Depends on:** W5.48

---

### W5.101 — Post-submit: journey blog post (medium-length) | Cx: 5 | P1

**Description:**
Author `docs/submission/journey-blog-post.md`. 1500–2500 word post documenting the W1–W5 journey: "How we built workforce infrastructure for any American city in 5 sprints." Cover: Worldwide Vibes origin, KANSEI dispatch protocol, TDD discipline, Wall as visual rebirth, FW pivot, submission grind. Publishable on Medium / dev.to / personal blog.

**AC:**
- [ ] `docs/submission/journey-blog-post.md` exists
- [ ] 1500–2500 words
- [ ] Covers W1–W5 arc
- [ ] KANSEI / dispatch protocol explained
- [ ] TDD + 5,189 tests cited
- [ ] Mentions specific challenges (Mapbox rate-limit, video <50MB, brand sweep)
- [ ] Publishable as-is (not just notes)
- [ ] No "MontGoWork"

**Depends on:** W5.48

---

### W5.102 — Post-submit: archive zip of submission state | Cx: 3 | P0

**Description:**
Strengthen W5.52 with a bundled `submission-state-2026-05-02.zip` containing: README.md (post-W5.51), docs/press-kit.md, docs/submission/* (all subfolders), full-final.mp4, teaser-final.mp4, all Wall stills, lighthouse-final.md, a11y-final.md, cross-browser-final.md, devpost-submission-url.txt, production-url.txt. Save to `docs/submission/_archive-2026-05-02/submission-state-2026-05-02.zip`.

**AC:**
- [ ] Zip file exists at the documented path
- [ ] Contains README + press kit + all submission docs
- [ ] Contains both video files
- [ ] Contains all 4 Wall stills
- [ ] Contains all verification docs
- [ ] Zip integrity verified (`unzip -t` PASS)
- [ ] Size documented in `docs/submission/_archive-2026-05-02/README.md`

**Depends on:** W5.52, W5.48

---

### W5.103 — Post-submit: post-mortem template seeded | Cx: 2 | P2

**Description:**
Author `docs/submission/post-mortem-template.md` for use after final HackFW results. Sections: What worked, What broke, What we'd do differently, Surprises, Spotlight inventions that paid off, Time spent vs estimated, Next steps. Pre-fills the obvious entries (e.g., "Spotlight inventions: live demo URL, copy-thesis SoT — both shipped"). Filled-in version is post-result work.

**AC:**
- [ ] `docs/submission/post-mortem-template.md` exists
- [ ] All 7 sections present
- [ ] Pre-fills the obvious already-known entries
- [ ] Notes that filled-in post-mortem happens post-result (not pre-submit)

**Depends on:** none

---

## Phase 19: Post-Launch Analytics + Monitoring

### W5.104 — Analytics: Plausible or Vercel Analytics setup decision | Cx: 3 | P1

**Description:**
Decide on a privacy-friendly analytics tool for post-launch. Plausible (paid, privacy-first) vs Vercel Analytics (built-in, free up to limit) vs none. Document decision in `docs/submission/analytics-decision.md`. If chosen: document install path. If none: document rationale ("no analytics during HackFW judging window — privacy + lower complexity").

**AC:**
- [ ] `docs/submission/analytics-decision.md` exists
- [ ] Decision documented (Plausible / Vercel / none)
- [ ] If chosen: install path documented
- [ ] If none: rationale documented + future-revisit note
- [ ] No PII tracking

**Depends on:** W5.36

---

### W5.105 — Analytics: events to track (scroll depth, chapter dwell) | Cx: 3 | P2

**Description:**
If W5.104 chose an analytics tool: define events to track. Key events: scroll depth per chapter (Chapter 1 reached, Chapter 5 reached, Chapter 10 reached); CTA click on assess/plan; video play (if embedded). Document in `docs/submission/analytics-events.md`. Implementation deferred to S14+ (not pre-submit).

**AC:**
- [ ] `docs/submission/analytics-events.md` exists
- [ ] ≥5 events defined
- [ ] Each event has: name / trigger / property keys
- [ ] Implementation deferred to S14+ explicitly
- [ ] Pre-submit posture: no events shipped (privacy-safe)

**Depends on:** W5.104

---

### W5.106 — Analytics: 30-day post-launch retro template | Cx: 2 | P2

**Description:**
Author `docs/submission/30-day-retro-template.md` to use on June 1, 2026. Sections: traffic numbers, top-bouncing chapters, conversion to assess/plan, qualitative feedback (Reddit/Twitter/LinkedIn comments), HackFW results, FW DAO bounty status, Dallas city progress. Template only; filled in post-30-day.

**AC:**
- [ ] `docs/submission/30-day-retro-template.md` exists
- [ ] All sections present
- [ ] Date placeholder for June 1, 2026
- [ ] Marked as post-launch fill-in (not pre-submit)

**Depends on:** none

---

## Phase 20: Accessibility Verification (Final)

### W5.107 — A11y: VoiceOver test on every chapter (final) | Cx: 4 | P0

**Description:**
Strengthen W5.32 by running VoiceOver (macOS) or NVDA (Windows) on every chapter (1–10) of the production Wall. For each chapter: announce expected? landmark roles correct? skip links work? Document chapter-by-chapter results in `docs/submission/voiceover-test.md`. Critical findings block W5.48.

**AC:**
- [ ] `docs/submission/voiceover-test.md` exists
- [ ] All 10 chapters tested
- [ ] Each chapter row: PASS / WARN / FAIL with note
- [ ] Critical findings: zero
- [ ] Test environment: VoiceOver Safari OR NVDA Firefox documented

**Depends on:** W5.32, W5.36

---

### W5.108 — A11y: keyboard-only nav on every chapter (final) | Cx: 3 | P0

**Description:**
Tab through all 10 chapters keyboard-only. Verify focus visible on every interactive element, no traps, scroll progression works without mouse, Chapter 6 cliff calculator usable keyboard-only, Chapter 7 path interaction usable. Document per-chapter in `docs/submission/keyboard-nav-test.md`.

**AC:**
- [ ] `docs/submission/keyboard-nav-test.md` exists
- [ ] All 10 chapters keyboard-tested
- [ ] Per-chapter: PASS/WARN/FAIL with note
- [ ] Chapter 6 cliff calc keyboard-usable
- [ ] No focus traps

**Depends on:** W5.32, W5.36

---

### W5.109 — A11y: print stylesheet + forced-colors mode verification | Cx: 3 | P1

**Description:**
Verify edge accessibility paths: print preview of `/`, `/assess`, `/plan` renders sensibly (no overflow, page-break-friendly); Windows High-Contrast Mode (`forced-colors: active`) renders chapters with sane contrast. Document in `docs/submission/print-forced-colors-test.md`.

**AC:**
- [ ] `docs/submission/print-forced-colors-test.md` exists
- [ ] Print preview tested for 3 routes
- [ ] Forced-colors mode tested on Chapters 1, 5, 10 minimum
- [ ] Issues documented + accepted (or fix-forwarded if blocking)

**Depends on:** W5.36

---

### W5.110 — A11y: WCAG 2.1 AA conformance statement | Cx: 3 | P1

**Description:**
Author `docs/submission/accessibility-statement.md` — public-facing WCAG 2.1 AA conformance statement. Sections: conformance level claimed, areas of conformance, known limitations, contact for a11y feedback. Standard pattern for civic-tech projects. Link from README footer.

**AC:**
- [ ] `docs/submission/accessibility-statement.md` exists
- [ ] WCAG 2.1 AA target stated
- [ ] Known limitations (mobile reduced experience, etc.) documented honestly
- [ ] Feedback contact email present
- [ ] Linked from README footer (or `## Accessibility` section)

**Depends on:** W5.107, W5.108

---

## Revised Summary by Phase (v2)

| Phase | Tasks | Cx | Focus |
|---|---|---|---|
| 1 Copy thesis SoT | 1 | 5 | docs/copy-thesis.md as load-bearing source |
| 2 README rewrite | 5 | 28 | Hero + thesis + Wall screenshot + 5,189 + HackFW |
| 3 Press kit refresh | 6 | 37 | FW positioning, 5,189 numbers, 4 cinematic stills |
| 4 Submission demo script | 4 | 22 | Wall walkthrough overlay, pre-demo checklist |
| 5 Submission video | 6 | 51 | 60s teaser + 3.5min full, voiceover, captions, <50MB |
| 6 Devpost submission | 5 | 17 | Description, tags, narrative, built-with, team |
| 7 Per-chapter OG | 3 | 16 | Verify dynamic + static fallbacks + metadata |
| 8 Final polish + verification | 5 | 28 | Lighthouse, a11y, cross-browser, mobile, brand sweep |
| 9 Deployment | 5 | 26 | Vercel prod + Mapbox token, backend, staging, rate-limit |
| 10 FW DAO bounty | 3 | 9 | Portal research, fit, claim path |
| 11 D-day | 5 | 22 | Runbook, dry-run, final smoke, git tag, submit |
| 12 Post-submission | 4 | 16 | Reddit, link-checker, live-demo CTA, archive |
| **13 Devpost field cataloging** | **7** | **20** | **Field-by-field catalog, length limits, video spec, eligibility** |
| **14 GitHub repo polish** | **12** | **30** | **LICENSE, CHANGELOG, ROADMAP, COC, CONTRIBUTING, templates, badges** |
| **15 README deeper polish** | **6** | **19** | **Hero img, demo CTA, badges, watch links, deploy, city framework** |
| **16 Video deeper polish** | **9** | **36** | **YouTube + Vimeo, voice-over, B-roll, project file, captions, thumbnail** |
| **17 D-day minute-by-minute (strengthen W5.44)** | **10** | **23** | **T-72h, T-48h, T-24h, T-12h, T-6h, T-3h, T-2h, T-1h, T+1h, contingencies** |
| **18 Post-submission engagement** | **7** | **18** | **Twitter, LinkedIn, civictech Reddit, thank-you, blog, archive zip, post-mortem** |
| **19 Post-launch analytics** | **3** | **8** | **Tool decision, events, 30-day retro template** |
| **20 Accessibility verification (final)** | **4** | **13** | **VoiceOver, keyboard-only, print + forced-colors, WCAG statement** |
| **Total (v2)** | **110** | **~444** | |

*(Cx total at task-level sums to 444 in v2; effective context-load with reruns and verification cycles lands ~700–800.)*

## Revised Summary by Priority (v2)

- **P0 (65 tasks):** All v1 P0 (36) + W5.53, W5.54, W5.55, W5.57, W5.58, W5.60, W5.61, W5.72, W5.73, W5.78, W5.80, W5.83, W5.87, W5.88, W5.89, W5.90, W5.91, W5.92, W5.93, W5.94, W5.95, W5.102, W5.107, W5.108 (29 new P0)
- **P1 (38 tasks):** All v1 P1 (13) + W5.56, W5.59, W5.62, W5.63, W5.64, W5.65, W5.66, W5.67, W5.69, W5.70, W5.74, W5.75, W5.76, W5.77, W5.79, W5.82, W5.84, W5.85, W5.86, W5.96, W5.97, W5.98, W5.99, W5.100, W5.101, W5.104, W5.109, W5.110 (28 new P1, plus 3 reclassified Mid-tier; net 25 new P1)
- **P2 (7 tasks):** All v1 P2 (3) + W5.68, W5.71, W5.81, W5.103, W5.105, W5.106 (6 new P2 — net +4)

## Spotlight Inventions Updated (v2)

In addition to v1 inventions (W5.1, W5.17/20/22, W5.35, W5.40, W5.44, W5.51, W5.52), v2 ships:

8. **W5.53 — Field-by-field Devpost catalog with measured length limits.** Mitigates the recurring failure mode of last-minute "field exceeded char limit" panic. Spotlight 構造 (structural).
9. **W5.83 — Human-transcribed captions with explicit brand-name review.** Auto-transcribe routinely mangles "GoWork" / "Carlos" / "Fort Worth"; an explicit review pass is the single highest-leverage accessibility + brand-discipline gate. Spotlight 智慧 (wisdom).
10. **W5.95 — Five-failure-mode contingency branches (deploy, video, Mapbox, Devpost, GitHub).** Each with trigger/detection/action/success. Composable into the d-day runbook so future-Shawn at 8:30 AM has a tree to traverse, not improvise. Spotlight 多重視点 + 遺産 (multiple selves + legacy).
11. **W5.102 — Submission-state zip archive (vs git tag alone).** Git tag captures code; the zip captures the holistic submission artifact (Devpost screenshot, video files, verification docs) for downstream review or comeback-after-results retrospective. Spotlight 遺産 (legacy).
12. **W5.110 — Public-facing WCAG 2.1 AA conformance statement.** Civic-tech expectation; signals seriousness about accessibility beyond just running axe. Spotlight 構造 (structural).
13. **W5.79 — Vimeo as backup video host.** Single-host failure mode (YouTube down at 8:55 AM on D-day, T-5min from submit) is a real risk; pre-uploaded Vimeo backup is one URL swap away from recovery. Spotlight 多重視点.

## Honest Uncertainty Updated (v2)

In addition to v1 (8 items), v2 surfaces:

9. **Devpost field-limit measurements assumed from W5.45 dry-run.** If Devpost UI changes between W5.45 and W5.48, limits could shift. W5.94 final brand sweep partially mitigates by re-running.
10. **YouTube + Vimeo upload approval/processing time.** Both platforms can sit in "processing" for 30+ min on first upload of a long video; W5.78 + W5.79 budgeted T-48h to give 2-day cushion.
11. **Voice-over recording quality without pro studio.** Best-effort with USB mic + Audacity noise reduction; if quality is poor, fallback is to use the live-with-screen-record audio from W5.19 (worse but acceptable).
12. **B-roll attribution licensing nuance.** Pexels/Unsplash/Pixabay licenses are permissive but require attribution in some cases; W5.81 documents but small risk of misreading a license clause exists. P2 priority.
13. **WCAG 2.1 AA conformance claim accuracy.** W5.110 claims AA; if W5.107/W5.108 surface AA-blocking findings, claim must downgrade to "AA target with documented exceptions" or move to P0 fix-forward.
14. **GitHub branch protection enabled pre- vs post-submit.** Pre-submit risks blocking a hotfix PR if CI is flaky; post-submit is safer. W5.71 explicitly defers decision.
15. **Plausible vs Vercel Analytics vs none.** All three are valid; W5.104 commits to a decision but acknowledges defaulting to "none for HackFW judging window" is the lowest-risk path.

## Cross-Sprint Dependencies Updated (v2)

- All v1 dependencies preserved
- New file outputs in v2: `LICENSE`, `CHANGELOG.md`, `ROADMAP.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/dependabot.yml`, `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`
- New `docs/submission/` files: `devpost-fields-catalog.md`, `devpost-title-tagline.md`, `video-spec-verification.md`, `built-with-diff.md`, `eligibility-confirmation.md`, `prizes-targeted.md`, `devpost-preview-workflow.md`, `ci-workflows.md`, `github-repo-metadata.md`, `branch-protection.md`, `voiceover-test.md`, `keyboard-nav-test.md`, `print-forced-colors-test.md`, `accessibility-statement.md`, `analytics-decision.md`, `analytics-events.md`, `30-day-retro-template.md`, `social-twitter-draft.md`, `social-linkedin-draft.md`, `social-reddit-civictech.md`, `thank-you.md`, `journey-blog-post.md`, `post-mortem-template.md`, `_archive-2026-05-02/submission-state-2026-05-02.zip`
- New `docs/submission-video/` files: `voiceover-raw.wav`, `voiceover-processed.wav`, `b-roll-attributions.md`, `_project-file/README.md`, `captions-review.md`, `thumbnail.png`, `cc-test.md`, `audio-mix-notes.md`
- **Still no new product code in /frontend or /backend.** v2 strictly extends docs, video, and GitHub-repo-metadata work. The W5 no-code rule holds.

## File Collision Matrix Updated (v2)

| File | Touched by |
|---|---|
| `README.md` | W5.2, W5.3, W5.4, W5.5, W5.6, W5.51, W5.72, W5.73, W5.74, W5.75, W5.76, W5.77 (sequential, single-driver) |
| `docs/submission/d-day-runbook.md` | W5.44, W5.48, W5.87, W5.88, W5.89, W5.90, W5.91, W5.92, W5.93, W5.94, W5.95, W5.96 (sequential append-style) |
| `docs/press-kit.md` | W5.7, W5.8, W5.9, W5.11, W5.12 (unchanged from v1) |
| `docs/submission-demo.md` | W5.13, W5.14, W5.15, W5.16 (unchanged) |
| `docs/submission-video/full-final.mp4` | W5.21 (produced), W5.78 + W5.79 (uploaded), W5.82 (project file backed up), W5.86 (audio mix verified) |
| `docs/submission-video/full-final.srt` | W5.21 (produced), W5.83 (human-reviewed) |

No two tasks edit the same line in parallel.

## Critical-Path DAG Updated (v2)

```
v1 paths preserved.

NEW v2 paths:

W5.45 (dry-run) ──> W5.53 (field catalog) ──> W5.54 (title/tagline limits)
                                          ──> W5.55 (video spec verify)
                                          ──> W5.59 (preview workflow)

W5.21 (video edit) ──> W5.78 (YouTube) ──> W5.84 (thumbnail) ──> W5.85 (CC test)
                  └─> W5.79 (Vimeo backup)
                  └─> W5.82 (project file backup)
                  └─> W5.83 (caption review)
                  └─> W5.86 (audio mix)

W5.36 (production deploy) ──> W5.70 (repo metadata) ──> W5.74 (badges)

W5.69 (CI workflow verify) ──> W5.74 (badges)

W5.44 (d-day runbook) ──> W5.87, W5.88, W5.89, W5.90, W5.91, W5.92, W5.93, W5.94, W5.95, W5.96 (all append)

W5.48 (SUBMIT) ──> W5.96 (T+1h verify), W5.97 (Twitter), W5.98 (LinkedIn),
                W5.99 (Reddit civictech), W5.100 (thank-you), W5.101 (blog),
                W5.102 (archive zip)

W5.36 (production deploy) ──> W5.107 (VoiceOver), W5.108 (keyboard), W5.109 (print/forced-colors)

W5.107 + W5.108 ──> W5.110 (a11y statement) ──> README footer link
```

## Sprint Validation (v2)

```bash
bpsai-pair engage plans/backlogs/sprint-w5-submission.md --dry-run
```

Expect: 110 tasks, ~444 Cx, 65 P0, 38 P1, 7 P2. DAG cycles: zero. Hard cap (130): unbreached.
