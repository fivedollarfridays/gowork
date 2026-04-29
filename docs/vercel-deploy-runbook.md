# Vercel Deploy Runbook — GoWork production

> **Authored:** W5 Driver C, 2026-04-28
> **Audience:** Shawn (operator). Anyone with Vercel + GitHub access.
> **Frequency:** every push to `sprint/visual-rebirth` or `main` (preview);
> manual promotion to production for the HackFW submission.
> **Estimated time end-to-end:** 25 minutes for a clean staging deploy,
> 10 minutes to promote, 5 minutes for smoke tests. **Do not rush.**

This runbook is the contract between the work in W1–W4 and the live URL we
hand to the judges. If a step here is unclear, **stop and ask** — the
submission deadline (May 2, 2026, 2:00 PM CDT, target submit by 9:00 AM CDT
per W5 backlog buffer logic) gives no room for retries.

---

## 0. Vercel project name

The Vercel project is named **gowork** (NOT MontGoWork — see the visual
rebirth brand-discipline rule). Default Vercel domain: `gowork.vercel.app`
unless a custom domain is wired (see §10).

---

## 1. Pre-deploy gates (run locally — every gate must be green)

Before pushing the deploy branch, run the full gauntlet from a clean
checkout. The Spotlight script `scripts/pre-deploy-gate.mjs` automates
this in one command:

```bash
cd frontend
npm run pre-deploy
```

Manual equivalent (each must exit 0):

| # | Gate | Command | Why |
|---|------|---------|-----|
| 1 | TypeScript | `npx tsc --noEmit` | Catches type drift |
| 2 | Lint | `npx next lint` | Catches accessibility, react-hooks bugs |
| 3 | Vitest | `npx vitest run` | All 3,400+ tests must pass |
| 4 | Production build | `npm run build` | Vercel will run the same |
| 5 | Architecture | `bpsai-pair arch check frontend/` | File / function / import limits |
| 6 | Brand audit | `npm run audit:brand` | Zero "MontGoWork" leaks |
| 7 | Token audit | `npm run audit:tokens` | Zero hard-coded colors |
| 8 | Contrast | `npm run contrast` | AAA pairs intact |
| 9 | Lighthouse | `npm run build && npm run lhci` | All 4 categories ≥ 0.90 |

If any gate is red, **fix before deploying**. Do NOT bypass with `--force`.

---

## 2. Vercel project setup (one-time, may already be done)

1. Sign in to [vercel.com](https://vercel.com) with the GitHub account that
   owns `fivedollarfridays/montgowork`.
2. **New Project → Import Git Repository → fivedollarfridays/montgowork**.
3. Configure:
   - **Project name:** `gowork`
   - **Framework preset:** Next.js (auto-detected)
   - **Root Directory:** `frontend/` ← critical, the repo is a monorepo
   - **Build Command:** `npm run build` (default)
   - **Install Command:** `npm ci` (default)
   - **Output Directory:** `.next` (default)
   - **Node version:** 20.x (Vercel default)
4. Click **Deploy**. The first deploy will fail until env vars are set in §3.

---

## 3. Environment variables (Vercel dashboard → Settings → Environment Variables)

### 3.1 Required for the Wall to render at all

| Variable | Scope | Value | Source |
|----------|-------|-------|--------|
| `NEXT_PUBLIC_API_URL` | Production + Preview | `https://montgowork-production.up.railway.app` | Railway backend URL — see `docs/DEPLOYMENT.md` for the Railway side |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Production + Preview | `pk.eyJ1Ijoi...` | [account.mapbox.com/access-tokens](https://account.mapbox.com/access-tokens/) — generate a public token (starts with `pk.`). Do NOT use a secret token (`sk.`) — it will leak in the browser bundle. |
| `NEXT_PUBLIC_SITE_URL` | Production | `https://gowork.vercel.app` (or custom domain) | Used by `lib/og/wallMetadata.ts` to absolutize OG image URLs for Slack / Twitter / LinkedIn unfurl. |

### 3.2 Required for visual polish (set these or the page is degraded)

| Variable | Scope | Value | Source |
|----------|-------|-------|--------|
| `NEXT_PUBLIC_MAPBOX_STYLE_URL` | Production + Preview | `mapbox://styles/<your-account>/wall-dark-editorial-v1` | Build the custom dark editorial style once in Mapbox Studio per `docs/runbooks/mapbox-style-setup.md`. The URI MUST start with `mapbox://styles/` — anything else is rejected as URL-spoofing defense in `lib/wall/mapboxStyle.ts`. |
| `NEXT_PUBLIC_LAST_CALIBRATED` | Production | ISO-8601 timestamp **at the moment you deploy** (e.g. `2026-05-02T09:30:00Z`) | The Live Now widget (W4 Driver A) shows "calibrated <relative-time> ago". **Update this value on every production promotion**, or the timestamp will look stale to judges. |

### 3.3 Optional (feature gates — page works without them)

| Variable | Scope | Value | Effect when missing |
|----------|-------|-------|---------------------|
| `NEXT_PUBLIC_EMAILJS_SERVICE_ID` | Production | EmailJS service ID | "Email My Plan" button hidden |
| `NEXT_PUBLIC_EMAILJS_TEMPLATE_ID` | Production | EmailJS template ID | "Email My Plan" button hidden |
| `NEXT_PUBLIC_EMAILJS_PUBLIC_KEY` | Production | EmailJS public key | "Email My Plan" button hidden |

After saving env vars: **redeploy** (Vercel Deployments → latest → "Redeploy") so the values are baked into the build.

---

## 4. Custom Mapbox style URL setup

The Wall uses a custom dark editorial Mapbox style for the cinematic look
(W2 T2.18). If you do NOT set `NEXT_PUBLIC_MAPBOX_STYLE_URL`, MapboxScene
falls back to `mapbox://styles/mapbox/dark-v11` (stock dark) — usable but
not the polished W2 visual.

To set it up:
1. Sign in to [Mapbox Studio](https://studio.mapbox.com).
2. Follow `docs/runbooks/mapbox-style-setup.md` to recreate the editorial
   palette.
3. Publish → copy the style URI (looks like
   `mapbox://styles/yourname/cm123abc456`).
4. Paste into Vercel env var `NEXT_PUBLIC_MAPBOX_STYLE_URL`.
5. Redeploy.

---

## 5. Staging deploy (preview)

Every push to a non-default branch creates a Vercel preview URL:

```bash
git push origin sprint/visual-rebirth
```

Vercel posts the preview URL in the GitHub PR check (or the Vercel
dashboard). Use it for the cross-browser test plan
(`docs/cross-browser-test-plan.md`) and the mobile / slow-3G plan
(`docs/mobile-slow-3g-test-plan.md`) before promoting.

---

## 6. Production promotion

**Do not promote to production until staging is fully validated.**

1. Merge `sprint/visual-rebirth` → `main` via GitHub PR (manual review).
2. Vercel auto-deploys `main` to the production domain on merge.
3. Watch the Vercel deployment log — should complete in ~3 min.
4. Hit the production URL in a fresh incognito window.
5. Run §7 smoke test.
6. **If anything is red, immediately roll back per §8 — do not pause to debug.**

---

## 7. Smoke test (post-deploy, must run on every promotion)

Automated via the Spotlight script (`scripts/post-deploy-smoke.mjs`):

```bash
SITE_URL=https://gowork.vercel.app node scripts/post-deploy-smoke.mjs
```

Manual checks (also in the script):

| # | URL | Expected | Why |
|---|-----|----------|-----|
| 1 | `/` | 200 OK, Wall renders Ch1 hero | Primary landing |
| 2 | Scroll Ch1 → Ch10 | All 10 chapters render, no console errors | Scrollytelling integrity |
| 3 | Click Ch10 CTA | Navigates to `/assess` | Wall→Funnel handoff |
| 4 | `/api/og/1` | 200 OK, 1200×630 PNG | OG card route (judges may share Ch1) |
| 5 | `/api/og/default` | 200 OK, 1200×630 PNG | OG fallback |
| 6 | `/bogus-url-xyz` | 404 with wall-metaphor copy in EN+ES | 404 page integrity |
| 7 | `/` mobile (iPhone Safari) | MobileWallFallback renders 10 chapter cards | W4 Driver B mobile fallback |
| 8 | `/` ES toggle | Ch6 wage slider + Ch10 CTA flip to Spanish | W4 Driver B Spanish parity |
| 9 | OS reduced-motion ON, reload `/` | View Transitions are skipped, motion-blur off | A11y reduced-motion |
| 10 | `<Tab>` from blank page | Skip-to-content link visible at top-left | A11y skip link |

If any check fails on production: **rollback first, debug after.**

---

## 8. Rollback path

Three options, in order of preference:

1. **Vercel instant redeploy** — Dashboard → Deployments → previous
   working build → "Promote to Production". Takes < 60s. Use this when
   the live build is broken but the previous build was green.
2. **Git revert + redeploy** — Use when the bug needs to be fixed forward
   in code:
   ```bash
   git checkout main
   git revert <bad-commit-sha> --no-edit
   git push origin main
   ```
   Vercel auto-deploys the revert commit (~3 min).
3. **Staging swap** — Last resort if Vercel is unreachable: point judges at
   the staging Fly.io URL (see `docs/submission-demo.md` — staging is the
   authoritative fallback). Update the Devpost form's "Try it out" field
   to the staging URL.

---

## 9. Per-deploy LAST_CALIBRATED update (mandatory)

Every deploy time, every production promotion MUST update
`NEXT_PUBLIC_LAST_CALIBRATED` to a fresh ISO timestamp (update at every
deploy — this is non-negotiable). The Live Now widget reads this at build time — a
stale value tells judges "nothing has shipped recently" and is a credibility
hit. Procedure:

1. Vercel dashboard → Settings → Environment Variables.
2. Edit `NEXT_PUBLIC_LAST_CALIBRATED` → set to `now()` ISO-8601, e.g.
   `2026-05-02T09:30:00Z`.
3. **Redeploy** (otherwise the new value isn't baked in).

---

## 10. Custom domain (optional, post-submission)

If a custom domain (`gowork.app` etc.) is wired:

1. Vercel dashboard → Domains → Add → enter the domain.
2. Update DNS at the registrar per Vercel's instructions (usually a CNAME
   to `cname.vercel-dns.com` or A records to `76.76.21.21`).
3. Wait for SSL (5-30 min — Vercel auto-issues via Let's Encrypt).
4. Update `NEXT_PUBLIC_SITE_URL` env var to the new origin.
5. Update `next.config.mjs` connect-src CSP whitelist if needed.
6. Redeploy.

**Honest uncertainty (W5-C C5):** the runbook assumes
`gowork.vercel.app`. Shawn may want `gowork.app`. Switching is a
one-line edit to `NEXT_PUBLIC_SITE_URL` plus the DNS dance above. The
submission video / Devpost form / README all cite `NEXT_PUBLIC_SITE_URL`
indirectly (via OG metadata / press kit), so the swap is loose-coupled.

---

## 11. Backend deployment (FYI — covered by `docs/DEPLOYMENT.md`)

The frontend on Vercel calls a FastAPI backend deployed separately on
Railway. The backend deploy is NOT in this runbook's scope — see
`docs/DEPLOYMENT.md` §"Deploy to Railway (Backend)" for the Railway side.
Key points relevant to Vercel:

- The Railway backend URL must be set as `NEXT_PUBLIC_API_URL` in Vercel.
- Railway's `CORS_ORIGINS` must include the Vercel frontend URL (e.g.
  `https://gowork.vercel.app`).
- Both services must be deployed before Vercel smoke tests will pass.

---

## 12. Tag the submission commit

After production smoke is green and BEFORE the Devpost form submit:

```bash
git tag v0.1.0-hackfw-submission
git push origin v0.1.0-hackfw-submission
```

This freezes the exact commit the judges review. Reference it in the
Devpost form's "Code repository" field as
`https://github.com/fivedollarfridays/montgowork/tree/v0.1.0-hackfw-submission`.

---

## 13. Honest uncertainty / known gaps

- **Vercel auto-deploys on push to `main`.** If `main` is wired to
  Vercel's "Production Branch", any PR merge to main triggers a
  production deploy. To avoid surprise, do NOT merge into `main` until
  you are ready to promote. Use `sprint/visual-rebirth` as the staging
  branch through submission.
- **EmailJS env vars are all optional.** If the demo touches "Email my
  plan", set them. If not, leave unset — the button hides gracefully.
- **The `lhci autorun` command runs against `localhost:3000`.** It does
  NOT measure Vercel-served performance. Use Chrome DevTools "Lighthouse"
  panel against the production URL for a true production measurement (the
  numbers will likely be 2-5 points higher than local because Vercel's
  CDN beats `next start`).
- **Custom domain DNS can take up to 24h to propagate** in pathological
  cases. If you decide to add a custom domain, do it the day before
  submission, not the morning of.

---

## See also

- `docs/submission-checklist.md` — the T-1 hour checklist that uses this
  runbook
- `docs/cross-browser-test-plan.md` — Manual QA on staging before promote
- `docs/mobile-slow-3g-test-plan.md` — Mobile + slow-3G validation
- `docs/lighthouse-final-scores.md` — measured Lighthouse scores at submit
- `docs/DEPLOYMENT.md` — Railway backend side (existing doc)
