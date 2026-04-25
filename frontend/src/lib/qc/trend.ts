/**
 * Trend / pass-rate helpers for the QC dashboard (T13.8).
 *
 * "Last 7 days" is a wall-clock window relative to a reference time
 * (defaults to now). Skipped runs are ignored in the denominator —
 * they reflect unmet preconditions, not a stability signal.
 */

import { isFlaky, latestVerdict, suiteVerdict } from "./flakes";
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

function newestRun(runs: QcRun[]): QcRun | null {
  if (runs.length === 0) return null;
  return [...runs].sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0];
}

/** Roll up all runs for a single suite into one SuiteSummary row. */
export function summarizeSuite(
  suiteId: string,
  runs: QcRun[],
  now: Date = new Date(),
): SuiteSummary {
  const newest = newestRun(runs);
  const window7d = runsInLastDays(runs, 7, now);
  return {
    suite_id: suiteId,
    suite_name: newest?.suite_name ?? suiteId,
    latest_verdict: latestVerdict(runs),
    latest_run_at: newest?.timestamp ?? null,
    is_flaky: isFlaky(runs),
    pass_rate_7d: passRateLast7Days(runs, now),
    run_count_7d: window7d.length,
    total_runs: runs.length,
  };
}
