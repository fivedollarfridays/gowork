# ADR: Visual Regression Approach for QC

- **Status:** Accepted (T13.6, sprint S13)
- **Deciders:** S13 platform-QC working group
- **Date:** 2026-04-24

## Context

S13 needs visual-regression coverage on top of the structural QC suites.
Two runners share the `.qc.yaml` flow library:

- **Playwright headless** (T13.129) — CI gate, top-five `@critical` paths,
  runs in chromium on CI Linux.
- **Divona** (`.claude/agents/divona.md`) — interactive author-time runner,
  uses the operator's actual desktop browser, broad coverage.

Both produce browser screenshots at points in their flows. We need a
verdict mechanism — pass/fail under a configurable pixel threshold — and a
durable baseline-storage convention that survives across PRs and CI runs.

## Decision

Adopt a **two-track** strategy that mirrors the two-runner split:

1. **Playwright track:** use the built-in `expect(page).toHaveScreenshot()`
   matcher. Baselines live next to specs at
   `frontend/e2e/__screenshots__/<spec>/<name>.png` (Playwright's default
   path template). Threshold: `maxDiffPixelRatio: 0.001` (<0.1%).
2. **Divona track:** add a `screenshot:` step to the `.qc.yaml` schema.
   On first encounter divona writes the baseline to
   `.paircoder/qc/baselines/<suite-id>/<name>.png`; on subsequent runs it
   diffs against the baseline using the new helper at
   `backend/scripts/qc_diff.py` (Pillow). Threshold: same default of 0.001,
   tunable per step via `max_diff_ratio`.

The two baseline trees are **deliberately separate.** Mixing them would
conflate fundamentally different captures: Playwright runs headless
chromium on CI Linux, divona runs an interactive desktop browser
(typically macOS Chrome). Font hinting, sub-pixel rendering, and OS-level
GPU compositing differ enough that a baseline from one runner is useless
to the other.

### Threshold

`maxDiffPixelRatio: 0.001` (one pixel in a thousand) is the default for
both tracks. Tunable per assertion when a flow legitimately exceeds it
(animated content, OS-level rendering quirks).

### Diff helper location

`backend/scripts/qc_diff.py`, runnable in the backend venv (Pillow is
already a transitive dep of WeasyPrint there). Original spec proposed
`.paircoder/qc/_diff.py` but `.paircoder/` has no Python invocation
context and no venv — keeping the helper inside `backend/scripts/`
matches the location of `nightly_digest.py`, `nightly_accounting.py`, and
the rest of the operational toolkit.

## Alternatives Considered

### `pixelmatch` standalone (Node, npm)

Would work, but reinvents what Playwright already wraps. Adds another
dependency to the frontend without buying capability we don't already
get from `toHaveScreenshot()`. Rejected.

### Percy / Chromatic / Loki (cloud SaaS)

Mature commercial tools with hosted review UIs. Cost: $X / month per
project plus per-snapshot fees. Out of scope for a hackathon delivery and
adds a third-party data dependency to a privacy-sensitive workforce
application. Rejected.

### BackstopJS

Yet another runner. We just landed Playwright (T13.129) and don't need a
parallel headless harness with its own baseline format. Rejected as
redundant.

### `pixelmatch` invoked from Python via `subprocess`

Would consolidate to one diff library across both tracks but introduces
Node from the backend, which the backend venv has no contract with.
Rejected — Pillow is local, fast, and already in the dep tree.

## Consequences

- **Baselines are committed to the repo.** Both trees: `frontend/e2e/__screenshots__/`
  and `.paircoder/qc/baselines/`. Reviewers must inspect screenshot
  changes the same way they review code changes.
- **Cross-platform rendering will differ.** Playwright handles this with
  per-platform `<name>-<platform>.png` baselines (the snapshot path
  template includes `{platform}` automatically when set up). CI uses the
  Linux baselines as authoritative; macOS / Windows local runs may need
  `--update-snapshots` once per environment. The divona track sidesteps
  the issue by being single-operator (the author who ran it).
- **First run is special.** On a fresh checkout the Playwright snapshot
  test will FAIL until the baseline is generated with
  `npm run test:e2e -- --update-snapshots`. This is documented in the
  spec and in `.paircoder/qc/suites/README.md`.
- **The divona `screenshot:` step is a future spec as of T13.6.** The
  schema is documented in `.paircoder/qc/suites/_template.qc.yaml` and
  the helper exists, but divona's runtime does not yet emit `screenshot:`
  steps. T13.6 ships the infrastructure ahead of usage.
- **Threshold tunability.** Both tracks expose `max_diff_ratio` /
  `maxDiffPixelRatio`. The default of 0.001 is conservative; flows with
  legitimate dynamic content (timestamps, randomized testimonials) should
  override per-step rather than relax globally.
