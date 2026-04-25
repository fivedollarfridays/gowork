# Frontend Bundle Budget

> Owner: frontend platform. Captured 2026-04-25 by T13.87. Next.js 15.5.

## Per-route First Load JS budget

The CI gate (`scripts/bundle-size-check.mjs`) fails if any route exceeds its
baseline by more than **+10%**. Threshold is per-route, not total — a 10%
regression on `/` matters more than 10% on `/admin/qc`.

| Route                       | Baseline | Notes                                             |
|-----------------------------|---------:|---------------------------------------------------|
| `/`                         |  161 kB  | Marketing landing — keep slim, first impression.  |
| `/privacy`                  |  121 kB  | Static legal page; should stay near the floor.    |
| `/terms`                    |  121 kB  | Static legal page; same as privacy.               |
| `/feedback/[token]`         |  127 kB  | Single-purpose form for token recipients.         |
| `/shared/[token]`           |  129 kB  | Read-only plan share view.                        |
| `/case-manager`             |  139 kB  | Advisor inbox; per-city scope.                    |
| `/daily`                    |  139 kB  | Worker daily checklist; high-traffic.             |
| `/documents/cover-letters`  |  139 kB  | Letter builder shell (mammoth lazy-loaded).       |
| `/documents/resume`         |  138 kB  | Resume builder shell (mammoth lazy-loaded).       |
| `/jobs`                     |  152 kB  | Kanban with dnd-kit.                              |
| `/credit`                   |  165 kB  | Credit module + recharts.                         |
| `/admin/qc`                 |  103 kB  | Internal QC dashboard (server-rendered).          |
| `/assess`                   |  190 kB  | Assessment form; framer-motion + radix forms.     |
| `/appointments`             |  210 kB  | react-big-calendar + date-fns.                    |
| `/plan`                     |  328 kB  | Largest route — recharts + framer-motion + extras.|

`/_not-found`, `/robots.txt`, `/sitemap.xml` are excluded from the gate.

## Top dependency contributors

Captured from `@next/bundle-analyzer` (parsed JS in client bundles, top 10):

| #  | Package           | Parsed   | Notes                                                          |
|----|-------------------|---------:|----------------------------------------------------------------|
| 1  | `html2pdf.js`     | 725 kB   | Used only when exporting a resume/letter PDF — *should* be lazy.|
| 2  | `next`            | 490 kB   | Framework runtime.                                              |
| 3  | `pdfjs-dist`      | 392 kB   | Imported by the resume/letter doc parsers.                      |
| 4  | `recharts`        | 229 kB   | `/plan` + `/credit` charts.                                     |
| 5  | `html2canvas`     | 193 kB   | Pulled in by `html2pdf.js`.                                     |
| 6  | `react-dom`       | 126 kB   | Framework runtime.                                              |
| 7  | `dingbat-to-unicode` | 117 kB | Pulled in by `mammoth` (`.docx` parser).                       |
| 8  | `jszip`           | 94 kB    | Transitive of `mammoth` / `html2pdf.js`.                        |
| 9  | `framer-motion`   | 82 kB    | Transitions; already in `optimizePackageImports`.               |
| 10 | `bluebird`        | 82 kB    | Transitive of `mammoth` (very legacy — promise polyfill).       |

## How to update the baseline

Bundle changes that legitimately exceed the budget should land with an
intentional baseline bump:

1. Run a fresh production build:
   ```bash
   cd frontend
   NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
   ```
2. Copy the per-route First Load JS values from the printed
   `Route (app)` table into `frontend/baseline-bundle-sizes.json` under
   `routes`.
3. Bump `_meta.captured_at` and `_meta.next_version`.
4. Commit the baseline change in the same PR as the size-affecting feature,
   with a one-line justification in the PR body.

To inspect what landed in the bundles:
```bash
cd frontend
npm run analyze
open .next/analyze/client.html   # interactive treemap (do NOT commit)
```

## Recommended optimization opportunities (follow-up)

These are not in T13.87's scope (this task only measures and gates), but they
fall out of the analyzer report and should be tracked:

- **Lazy-load `html2pdf.js` + `html2canvas`** (~920 kB combined). Currently
  appear in `/plan` + `/documents/*` first-load. They are only needed at
  click time for "Export PDF" — `import()` them inside the click handler.
- **Lazy-load `pdfjs-dist`** (~392 kB). Same reasoning — only needed when a
  worker actually uploads a `.pdf` to the resume/letter builders.
- **Drop `bluebird` + `dingbat-to-unicode`** if possible. They are
  transitive deps of `mammoth`. Verify whether tree-shaking is failing or
  whether mammoth's entry pulls them unconditionally; consider a lighter
  `.docx` parser for the OCR-fallback path.
- **Audit `/plan`'s 328 kB.** It is more than 2x the next-largest route.
  Likely contributors: recharts + framer-motion + the comparison view.
  Candidates: dynamic-import the chart panels; replace framer-motion with
  CSS transitions on this surface.
- **Audit `/appointments`'s 210 kB.** `react-big-calendar` + `date-fns`
  drive most of it. Switching to a smaller calendar widget or trimming
  `date-fns` locale imports could save ~40 kB.
- **`tesseract.js` is NOT currently in any first-load.** Confirm it stays
  dynamically imported (resume OCR fallback path only).

## Where this is enforced

| Layer       | What it does                                                            |
|-------------|-------------------------------------------------------------------------|
| Local dev   | `npm run size:check` — runs against the current `npm run build` output. |
| CI          | `.github/workflows/ci.yml -> frontend -> Bundle size check` step.       |
| Deep dive   | `npm run analyze` — opens `.next/analyze/client.html` (gitignored).     |
