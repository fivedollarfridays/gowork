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

import { sortNewestFirst } from "./dashboard";
import type { QcRun, ScenarioVerdict, SuiteVerdict } from "./types";

const FLAKE_WINDOW = 5;

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
  return latestVerdictFromSorted(sortNewestFirst(runs));
}

/**
 * Same as :func:`latestVerdict` but trusts the caller to have already
 * sorted ``runs`` newest-first via :func:`sortNewestFirst`. Used by
 * :func:`summarizeSuite` to avoid re-sorting the same array three times.
 */
export function latestVerdictFromSorted(sortedRuns: QcRun[]): SuiteVerdict {
  if (sortedRuns.length === 0) return "unknown";
  return suiteVerdict(sortedRuns[0]);
}

/**
 * Per-run suite verdicts for the last `windowSize` runs (newest-first).
 * Returned in chronological order (oldest first) for trend display.
 */
export function scenarioVerdicts(
  runs: QcRun[],
  windowSize: number,
): SuiteVerdict[] {
  return scenarioVerdictsFromSorted(sortNewestFirst(runs), windowSize);
}

/**
 * Same as :func:`scenarioVerdicts` but trusts the caller-supplied
 * ``sortedRuns`` to already be newest-first.
 */
export function scenarioVerdictsFromSorted(
  sortedRuns: QcRun[],
  windowSize: number,
): SuiteVerdict[] {
  const window = sortedRuns.slice(0, windowSize);
  return window.reverse().map(suiteVerdict);
}

/**
 * Flake detection: in the last 5 runs (skips ignored), did the same
 * suite show both passed AND failed verdicts?
 */
export function isFlaky(runs: QcRun[]): boolean {
  return isFlakyFromSorted(sortNewestFirst(runs));
}

/**
 * Same as :func:`isFlaky` but trusts the caller to have already sorted
 * ``runs`` newest-first via :func:`sortNewestFirst`.
 */
export function isFlakyFromSorted(sortedRuns: QcRun[]): boolean {
  const verdicts = scenarioVerdictsFromSorted(sortedRuns, FLAKE_WINDOW).filter(
    (v) => v !== "skipped" && v !== "unknown",
  );
  const sawPass = verdicts.some((v) => v === "passed");
  const sawFail = verdicts.some((v) => v === "failed" || v === "error");
  return sawPass && sawFail;
}

/** Re-export so callers can avoid importing types separately. */
export type { ScenarioVerdict, SuiteVerdict };
