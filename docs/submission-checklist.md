# GoWork — HackFW 2026 Submission Checklist

> **Authored:** W5 Driver C, 2026-04-28
> **Audience:** Shawn, at T-1 hour before submit.
> **Deadline:** **May 2, 2026, 2:00 PM CDT** (14:00 CDT). Hard cutoff.
> **Target submit:** **9:00 AM CDT, May 2, 2026** (5-hour buffer per W5
> backlog decision lock #1). Buffer is non-negotiable.
>
> Print this. Tick boxes with a pen. Do NOT improvise. The buffer eats
> minor surprises (Devpost upload retry, captions don't burn-in, Mapbox
> token rotated). Without the buffer one bug eats the whole afternoon.

---

## Pre-flight (T-24 hours, do this Sunday May 1)

- [ ] All gates green on `main` (run `npm run pre-deploy` from frontend/)
- [ ] Production Vercel deploy is GREEN — see `docs/vercel-deploy-runbook.md`
- [ ] `NEXT_PUBLIC_LAST_CALIBRATED` updated to `2026-05-01T<h>:<m>:00Z`
- [ ] Devpost account confirmed working (login, profile, team)
- [ ] Press kit final on `docs/press-kit.md` and shipped images present
- [ ] Submission video < 4:00 final (target 3:55 per
      `docs/submission-video-script.md` master timeline; W5-D
      compressed from 4:30 to satisfy
      `docs/visual-rebirth-briefs.md` "Final video < 4 min" rule),
      captions present (.srt or burned-in)
- [ ] 60-second teaser final
- [ ] Get a full night of sleep — past-Shawn's gift to future-Shawn

---

## T-2 hours (10:00 AM Vercel-clock; ~12:00 PM CDT)

### Production smoke (30 min budget)

- [ ] Final smoke test on production URL (`https://gowork.vercel.app` or custom)
- [ ] All 4 Lighthouse scores ≥ 0.90 on production (Chrome DevTools panel,
      Network: Fast 3G if you want a worst case; Desktop preset matches CI)
- [ ] If any Lighthouse score < 0.90 — re-run on production directly,
      confirm a single-run miss vs. real regression. Check `lhci` from
      local against staging if needed
- [ ] All 3,428+ frontend tests green: `cd frontend && npx vitest run`
- [ ] All backend tests green (per backend ops)
- [ ] Mapbox token live: open `/` on production, verify the Wall map
      tiles render (not the static fallback)
- [ ] OG card #1 (Ch1) — open `https://gowork.vercel.app/api/og/1` in
      browser, verify a 1200×630 PNG renders with chapter title
- [ ] OG default — open `/api/og/default`, verify GoWork fallback PNG
- [ ] Mobile fallback — open `/` on a real iPhone (Safari) or Chrome
      mobile emulation, confirm MobileWallFallback shows 10 chapter cards

### Spanish + a11y smoke (15 min budget)

- [ ] Spanish toggle works on production: switch ES, verify Ch6 wage
      slider labels swap to Spanish + Ch10 CTA reads in Spanish
- [ ] Reduced-motion: enable system pref (macOS System Settings →
      Accessibility → Display → Reduce motion = ON), reload `/`, verify
      View Transitions are skipped + motion-blur is off + idle drift is off
- [ ] Skip-to-content link visible on `<Tab>` from blank page
      (incognito → hit Tab once → "Skip to main content" link should
      appear at top-left, not be hidden under the header)

### Asset pre-check (15 min budget)

- [ ] Wall screenshot in README renders correctly on GitHub
      (https://github.com/fivedollarfridays/montgowork/blob/main/README.md)
- [ ] Press kit images load
- [ ] Submission video file is < 50 MB
- [ ] Submission video runtime is **< 4:00** (target 3:55 per master
      timeline; W5-D verified against visual-rebirth-briefs.md
      "Final video < 4 min" requirement). If Devpost rules tighten to
      3:00, fall back to the emergency cut documented in Section G of
      `docs/submission-video-script.md`
- [ ] Captions verified — open the video, confirm text matches audio

---

## T-1 hour (~13:00 PM CDT — but target wraps at 9:00 AM CDT per buffer)

### Devpost form fill (45 min budget — includes upload time)

- [ ] Open Devpost submission form for HackFW 2026
- [ ] Project name: `GoWork` (NOT MontGoWork)
- [ ] Project tagline / one-liner pasted from `docs/copy-thesis.md`
- [ ] Project description pasted from `docs/devpost-submission.md`
- [ ] Built with tags pasted (Next.js, FastAPI, Mapbox, Tailwind, etc.)
- [ ] Categories selected: **Reindustrialization, Workforce, AI/ML,
      Civic Tech, Open Source**
- [ ] Team members added (with linked Devpost profiles)
- [ ] **Production URL** pasted in "Try it out" field (the live
      Vercel URL, NOT staging)
- [ ] **GitHub repo URL** pasted in "Code repository" field — point
      at the tag: `https://github.com/fivedollarfridays/montgowork/tree/v0.1.0-hackfw-submission`
- [ ] Video uploaded to Devpost — wait for "processing complete"
      confirmation (NOT just "upload complete")
- [ ] Verify video has captions in the Devpost preview player
- [ ] Cover image uploaded (Wall screenshot from press kit)

---

## T-30 minutes

### Final review pass (no edits unless something is wrong)

- [ ] Open Devpost preview, read description top-to-bottom
- [ ] Click every link in description — none broken (README, press kit,
      video on Vercel/YouTube, GitHub tag, demo URL)
- [ ] Verify "Open source" / "MIT licensed" mentioned in description
- [ ] Press kit linked / referenced
- [ ] Hero question + subhead + tagline ALL match `docs/copy-thesis.md`
      verbatim across README + press kit + Devpost form (consistency sweep)
- [ ] No "MontGoWork" in any submission asset (brand discipline lock)
- [ ] Test count "5,189 total (4,080 backend + 1,109 frontend)"
      consistent across surfaces (no stale "1,808")

---

## T-15 minutes (target 8:45 AM CDT per buffer)

- [ ] Click **SUBMIT** on Devpost
- [ ] Save the confirmation email to a permanent folder
- [ ] Take a screenshot of the confirmation page
- [ ] Take a screenshot of the Devpost project URL (your project's
      public-facing page)

---

## T-0 (DEADLINE — 2:00 PM CDT, NEVER let it get this close)

- [ ] Submitted before 2:00 PM CDT
- [ ] You should be 5 hours past this point already (per buffer rule)

---

## T+15 minutes (post-submit hygiene)

- [ ] Tag the git commit using the canonical script (W5 Driver D):
      ```
      node scripts/tag-submission.mjs
      ```
      The script verifies a clean working tree, the branch
      (`sprint/visual-rebirth` / `sprint/w5-submission` / `main`),
      the absence of an existing `v0.1.0-hackfw-submission` tag,
      writes the structured tag message (sprint summary, test counts,
      Lighthouse scores, deployment URL), creates the annotated tag,
      and pushes it to origin. Pass `--dry-run` first to preview the
      message; pass `--force` to re-tag (audited). Override defaults
      with `--tests-frontend=N --bundle-kb=N --lighthouse-perf=X
      --deploy-url=URL` flags or matching env vars at tag time.
- [ ] Verify the tag appears on GitHub at
      `https://github.com/fivedollarfridays/montgowork/releases/tag/v0.1.0-hackfw-submission`
- [ ] Update Devpost "Code repository" field to the tag URL if not done
      pre-submit
- [ ] Reddit / X / LinkedIn post drafts published (drafts in
      `docs/post-submission/` — `reddit-r-civic-tech.md`,
      `twitter-thread.md`, `linkedin-announcement.md`)
- [ ] Slack the team with the Devpost project URL + git tag
- [ ] Eat. Drink water. Stop touching the keyboard.

---

## Emergency procedures

### Production breaks at T-1 hour

1. Immediately open `docs/vercel-deploy-runbook.md` §8 Rollback.
2. Rollback to previous Vercel build (1-click in dashboard, < 60s).
3. Re-run smoke test §T-2 hours.
4. If still broken, swap Devpost "Try it out" field to staging URL
   (Fly.io — see `docs/submission-demo.md`).
5. **Do not panic-edit code.** Forward fixes after submit.

### Devpost upload fails

1. Refresh the form. Devpost auto-saves drafts.
2. Try a different browser (Chrome → Firefox).
3. If video upload fails: re-encode at lower bitrate (target 30 MB),
   retry. Devpost cap is 50 MB.
4. Last resort: upload video to YouTube unlisted, embed YouTube link in
   Devpost description, leave the upload field blank.

### Mapbox token rotates / quota exceeded

1. Generate a new public token at
   https://account.mapbox.com/access-tokens/.
2. Update `NEXT_PUBLIC_MAPBOX_TOKEN` in Vercel.
3. Redeploy. Wait 3 min.
4. Re-run smoke test step #6 (Mapbox token live).

### Lighthouse drops below 0.90 unexpectedly

1. Re-measure on production directly (Chrome DevTools panel) — local
   `lhci` and production scores can differ by 5-10 points.
2. If still red — apply W4 brief descope (audio off → temperature
   multiplier off → 3D barrier graph already lazy → View Transitions
   feature-detected). Each is a 1-line edit.
3. Re-deploy. Re-measure.
4. Document final score in `docs/lighthouse-final-scores.md`.

---

## Sign-off

- Operator: ________________________________
- Date / time of submit: ________________________________
- Devpost project URL: ________________________________
- Git tag SHA: ________________________________

---

## See also

- `docs/vercel-deploy-runbook.md` — production deploy procedure
- `docs/cross-browser-test-plan.md` — manual QA per-browser
- `docs/mobile-slow-3g-test-plan.md` — mobile + slow-3G validation
- `docs/lighthouse-final-scores.md` — measured Lighthouse scores
- `docs/devpost-submission.md` — Devpost form copy (Driver A's lane)
- `docs/copy-thesis.md` — single source of truth for slogans + numbers
