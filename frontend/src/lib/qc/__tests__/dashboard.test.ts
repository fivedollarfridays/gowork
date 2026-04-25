import { describe, it, expect } from "vitest";
import {
  dashboardStats,
  sortSummaries,
  verdictBadge,
  verdictLabel,
} from "../dashboard";
import type { SuiteSummary } from "../types";

function summary(overrides: Partial<SuiteSummary>): SuiteSummary {
  return {
    suite_id: "x",
    suite_name: "X",
    latest_verdict: "passed",
    latest_run_at: "2026-04-25T10:00:00Z",
    is_flaky: false,
    pass_rate_7d: 1,
    run_count_7d: 1,
    total_runs: 1,
    ...overrides,
  };
}

describe("sortSummaries", () => {
  it("places failing suites before flaky before clean", () => {
    const a = summary({ suite_id: "passing" });
    const b = summary({ suite_id: "flaky", is_flaky: true });
    const c = summary({ suite_id: "failing", latest_verdict: "failed" });
    const sorted = sortSummaries([a, b, c]);
    expect(sorted.map((s) => s.suite_id)).toEqual([
      "failing",
      "flaky",
      "passing",
    ]);
  });

  it("treats 'error' verdict as failing for sort priority", () => {
    const a = summary({ suite_id: "ok" });
    const b = summary({ suite_id: "errored", latest_verdict: "error" });
    expect(sortSummaries([a, b]).map((s) => s.suite_id)).toEqual([
      "errored",
      "ok",
    ]);
  });

  it("breaks ties by latest_run_at descending", () => {
    const old = summary({
      suite_id: "old",
      latest_run_at: "2026-04-20T10:00:00Z",
    });
    const newr = summary({
      suite_id: "new",
      latest_run_at: "2026-04-25T10:00:00Z",
    });
    expect(sortSummaries([old, newr]).map((s) => s.suite_id)).toEqual([
      "new",
      "old",
    ]);
  });
});

describe("dashboardStats", () => {
  it("returns zero/null for empty input", () => {
    expect(dashboardStats([])).toEqual({
      total_suites: 0,
      total_runs_7d: 0,
      overall_pass_rate_7d: null,
    });
  });

  it("weights pass rate by run count across suites", () => {
    const a = summary({ run_count_7d: 4, pass_rate_7d: 1 });
    const b = summary({ run_count_7d: 1, pass_rate_7d: 0 });
    const stats = dashboardStats([a, b]);
    expect(stats.total_suites).toBe(2);
    expect(stats.total_runs_7d).toBe(5);
    expect(stats.overall_pass_rate_7d).toBeCloseTo(0.8, 5);
  });

  it("returns null overall pass rate when no runs in window", () => {
    const a = summary({ run_count_7d: 0, pass_rate_7d: null });
    expect(dashboardStats([a]).overall_pass_rate_7d).toBeNull();
  });
});

describe("verdictLabel + verdictBadge", () => {
  it("labels failing with 'Fail'", () => {
    expect(verdictLabel("failed", false)).toBe("Fail");
    expect(verdictBadge("failed", false)).toBe("✗");
  });

  it("labels flaky-but-passing with 'Flake'", () => {
    expect(verdictLabel("passed", true)).toBe("Flake");
    expect(verdictBadge("passed", true)).toBe("⚠");
  });

  it("labels clean passes with 'Pass'", () => {
    expect(verdictLabel("passed", false)).toBe("Pass");
    expect(verdictBadge("passed", false)).toBe("✓");
  });

  it("labels skipped runs", () => {
    expect(verdictLabel("skipped", false)).toBe("Skipped");
    expect(verdictBadge("skipped", false)).toBe("⏭");
  });

  it("flaky takes precedence over plain pass but NOT over fail", () => {
    expect(verdictLabel("failed", true)).toBe("Fail");
    expect(verdictBadge("failed", true)).toBe("✗");
  });
});
