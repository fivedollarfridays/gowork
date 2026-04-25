# Divona QC Baselines

This tree holds reference PNGs for the divona-side `screenshot:` step type
documented in `.paircoder/qc/suites/_template.qc.yaml`. See
`docs/adr/qc-visual-regression.md` for the full architecture decision.

## Layout

```
.paircoder/qc/baselines/
├── README.md                              # this file
└── <suite-id>/                            # one per .qc.yaml suite
    └── <name>.png                         # one per `screenshot:` step
```

`<suite-id>` matches `suite_id` in the `.qc.yaml` (and the filename minus
`.qc.yaml`). `<name>` matches the `name:` field on the `screenshot:` step
(kebab-case, no extension).

## Generation

On first encounter divona writes the baseline; subsequent runs diff
against it via `backend/scripts/qc_diff.py`. Default threshold:
`max_diff_ratio: 0.001` (<0.1 % differing pixels). Override per-step.

## Why is this separate from `frontend/e2e/.../*-snapshots/`?

Playwright captures run in headless chromium on CI Linux; divona captures
run in the operator's interactive desktop browser. Font hinting, GPU
compositing, and OS-level rendering differ enough that a baseline from
one runner is useless to the other. The two trees are intentionally
distinct — neither runner reads the other's tree.

## Sample

`worker-onboarding/home.png` is a sample baseline (a copy of the
Playwright home capture, used as a reference for the divona convention).
It will be regenerated against the divona browser when divona's runtime
support for the `screenshot:` step type lands.
