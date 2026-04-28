# Lighthouse CI Runbook

## Running locally

```bash
cd frontend
npm ci
npm run build
npm run lhci
```

The `lhci autorun` command builds nothing on its own — you must `npm run build`
first so that `npm run start` (used as `startServerCommand`) has artifacts to
serve. A real Chrome install is required; on macOS the `chrome` binary that
ships with `puppeteer` (pulled in transitively by `@lhci/cli`) is used by
default.

## Tuning thresholds

Edit `frontend/lighthouserc.json` under `ci.assert.assertions`:

| Category        | Floor (minScore) | AC source              |
|-----------------|------------------|------------------------|
| performance     | 0.80             | T13.7 AC: Perf >=80    |
| accessibility   | 0.90             | T13.7 AC: A11y >=90    |
| best-practices  | 0.90             | T13.7 AC: BP >=90      |
| seo             | 0.90             | T13.7 AC: SEO >=90     |

Lower a floor temporarily by changing `minScore` (e.g. `0.75`) and committing.
Prefer fixing the regression over loosening the floor.

## Why `numberOfRuns: 3`

Lighthouse scores are noisy; the canonical recommendation is `numberOfRuns: 3`
(median wins). W2 introduced a Mapbox-heavy `/` route which pushed single-run
variance high enough to flake the perf gate (observed 0.72 once vs the 0.80
floor on PR #82, while the parallel run on the same commit scored ≥0.80).
Per W2 souji we bumped to 3 runs and take the median — the canonical
mitigation. Cost: six routes x ~30s/run x 3 runs ≈ 9 min in CI.

If `/` perf still flakes after this, fix the underlying regression rather
than lowering the floor.

## Route list rationale

We audit only public, unauthenticated routes that render meaningful content
without a logged-in session:

- `/` — landing
- `/daily` — daily plan view
- `/appointments` — appointments list
- `/documents/resume` — resume builder (bare `/documents` 404s; NavBar links
  here directly)
- `/jobs` — job board
- `/case-manager` — advisor / case-manager view (the AC referred to this as
  `/advisor`; the actual route in this codebase is `/case-manager`)

Excluded:

- `/api/*` — JSON, no Lighthouse value
- `/feedback/[token]` — token-gated, no fixed URL
- `/admin/*` — auth-gated, would render a redirect under Lighthouse

## CI integration

The `lighthouse` job in `.github/workflows/ci.yml` runs after the `frontend`
job succeeds. It rebuilds the app (Lighthouse needs the build artifact and the
existing `frontend` job does not upload one). The optional
`LHCI_GITHUB_APP_TOKEN` secret enables PR status comments; without it, runs
upload to `temporary-public-storage` (anonymous, public) and the link is
printed in the job logs.
