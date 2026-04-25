/**
 * Flake / verdict heuristics for the QC dashboard (T13.8).
 *
 * A suite is "flaky" when the same suite shows BOTH passed and failed
 * outcomes within its last 5 runs. Skipped runs are ignored — a skip
 * indicates an unmet precondition, not a real signal about stability.
 *
 * "Currently failing" (latest verdict = failed) is reported separately;
 * an all-failing streak is failing, not flaky.
 */

import type { QcRun, ScenarioVerdict, SuiteVerdict } from "./types";

const FLAKE_WINDOW = 5;

/** Sort runs newest-first by timestamp. */
function sortNewestFirst(runs: QcRun[]): QcRun[] {
  return [...runs].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

/**
 * Roll up a single run's scenario verdicts into a suite verdict.
 *
 * Precedence (worst wins): failed > error > skipped-only > passed.
 * A run with zero scenarios collapses to "skipped" (nothing ran).
 */
export function suiteVerdict(run: QcRun): SuiteVerdict {
  const verdicts = run.scenarios.map((s) => s.verdict);
  if (verdicts.length === 0) return "skipped";
  if (verdicts.includes("failed")) return "failed";
  if (verdicts.includes("error")) return "error";
  if (verdicts.every((v) => v === "skipped")) return "skipped";
  return "passed";
}

/** Latest verdict across the runs given (any suite). */
export function latestVerdict(runs: QcRun[]): SuiteVerdict {
  if (runs.length === 0) return "unknown";
  const newest = sortNewestFirst(runs)[0];
  return suiteVerdict(newest);
}

/**
 * Per-run suite verdicts for the last `windowSize` runs (newest-first).
 * Returned in chronological order (oldest first) for trend display.
 */
export function scenarioVerdicts(
  runs: QcRun[],
  windowSize: number,
): SuiteVerdict[] {
  const window = sortNewestFirst(runs).slice(0, windowSize);
  return window.reverse().map(suiteVerdict);
}

/**
 * Flake detection: in the last 5 runs (skips ignored), did the same
 * suite show both passed AND failed verdicts?
 */
export function isFlaky(runs: QcRun[]): boolean {
  const verdicts = scenarioVerdicts(runs, FLAKE_WINDOW).filter(
    (v) => v !== "skipped" && v !== "unknown",
  );
  const sawPass = verdicts.some((v) => v === "passed");
  const sawFail = verdicts.some((v) => v === "failed" || v === "error");
  return sawPass && sawFail;
}

/** Re-export so callers can avoid importing types separately. */
export type { ScenarioVerdict, SuiteVerdict };
