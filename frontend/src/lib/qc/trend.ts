/**
 * Trend / pass-rate helpers for the QC dashboard (T13.8).
 *
 * "Last 7 days" is a wall-clock window relative to a reference time
 * (defaults to now). Skipped runs are ignored in the denominator —
 * they reflect unmet preconditions, not a stability signal.
 */

import { sortNewestFirst } from "./dashboard";
import {
  isFlakyFromSorted,
  latestVerdictFromSorted,
  suiteVerdict,
} from "./flakes";
import type { QcRun, SuiteSummary } from "./types";

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** Filter runs whose timestamp is within `days` of the reference time. */
export function runsInLastDays(
  runs: QcRun[],
  days: number,
  now: Date = new Date(),
): QcRun[] {
  const cutoff = now.getTime() - days * MS_PER_DAY;
  return runs.filter((r) => Date.parse(r.timestamp) >= cutoff);
}

/**
 * Pass rate over the last 7 days (skipped runs excluded from
 * denominator). Returns `null` if no runs ran in the window.
 */
export function passRateLast7Days(
  runs: QcRun[],
  now: Date = new Date(),
): number | null {
  const window = runsInLastDays(runs, 7, now);
  const verdicts = window
    .map(suiteVerdict)
    .filter((v) => v !== "skipped" && v !== "unknown");
  if (verdicts.length === 0) return null;
  const passes = verdicts.filter((v) => v === "passed").length;
  return passes / verdicts.length;
}

/**
 * Roll up all runs for a single suite into one SuiteSummary row.
 *
 * Optimisation: callers previously triggered three independent sorts
 * (one each in `latestVerdict`, `isFlaky`, and the local `newestRun`).
 * We sort once and feed the sorted array into the `*FromSorted`
 * variants — see their docstrings for the contract.
 */
export function summarizeSuite(
  suiteId: string,
  runs: QcRun[],
  now: Date = new Date(),
): SuiteSummary {
  const sorted = sortNewestFirst(runs);
  const newest = sorted[0] ?? null;
  const window7d = runsInLastDays(runs, 7, now);
  return {
    suite_id: suiteId,
    suite_name: newest?.suite_name ?? suiteId,
    latest_verdict: latestVerdictFromSorted(sorted),
    latest_run_at: newest?.timestamp ?? null,
    is_flaky: isFlakyFromSorted(sorted),
    pass_rate_7d: passRateLast7Days(runs, now),
    run_count_7d: window7d.length,
    total_runs: runs.length,
  };
}
