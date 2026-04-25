/**
 * Pure helpers for `QcDashboard` view (T13.8). Kept separate from the
 * React component so they're cheap to unit-test and reusable.
 */

import type { SuiteSummary, SuiteVerdict } from "./types";

export interface DashboardStats {
  total_suites: number;
  total_runs_7d: number;
  /** Weighted pass rate across all 7d runs (0..1), or null if no runs. */
  overall_pass_rate_7d: number | null;
}

/**
 * Sort order: failing first, flaky second, then everything else by
 * `latest_run_at` descending. Used by the dashboard table so eyeballs
 * land on broken things first.
 */
export function sortSummaries(summaries: SuiteSummary[]): SuiteSummary[] {
  return [...summaries].sort((a, b) => {
    const aRank = priority(a);
    const bRank = priority(b);
    if (aRank !== bRank) return aRank - bRank;
    return (b.latest_run_at ?? "").localeCompare(a.latest_run_at ?? "");
  });
}

function priority(s: SuiteSummary): number {
  if (s.latest_verdict === "failed" || s.latest_verdict === "error") return 0;
  if (s.is_flaky) return 1;
  return 2;
}

export function dashboardStats(summaries: SuiteSummary[]): DashboardStats {
  const total_suites = summaries.length;
  const total_runs_7d = summaries.reduce((sum, s) => sum + s.run_count_7d, 0);
  if (total_runs_7d === 0) {
    return { total_suites, total_runs_7d, overall_pass_rate_7d: null };
  }
  const weightedPasses = summaries.reduce((sum, s) => {
    if (s.pass_rate_7d == null) return sum;
    return sum + s.pass_rate_7d * s.run_count_7d;
  }, 0);
  return {
    total_suites,
    total_runs_7d,
    overall_pass_rate_7d: weightedPasses / total_runs_7d,
  };
}

export function verdictLabel(verdict: SuiteVerdict, isFlaky: boolean): string {
  if (verdict === "failed" || verdict === "error") return "Fail";
  if (isFlaky) return "Flake";
  if (verdict === "passed") return "Pass";
  if (verdict === "skipped") return "Skipped";
  return "Unknown";
}

export function verdictBadge(verdict: SuiteVerdict, isFlaky: boolean): string {
  if (verdict === "failed" || verdict === "error") return "✗";
  if (isFlaky) return "⚠";
  if (verdict === "passed") return "✓";
  if (verdict === "skipped") return "⏭";
  return "?";
}
