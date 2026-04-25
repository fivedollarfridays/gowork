import { describe, it, expect } from "vitest";
import { passRateLast7Days, runsInLastDays, summarizeSuite } from "../trend";
import type { QcRun } from "../types";

const NOW = new Date("2026-04-25T12:00:00Z");

function mkRun(suiteId: string, isoTs: string, verdicts: string[]): QcRun {
  return {
    suite_id: suiteId,
    suite_name: suiteId,
    environment: "dev",
    timestamp: isoTs,
    scenarios: verdicts.map((v, i) => ({
      name: `s-${i}`,
      verdict: v as QcRun["scenarios"][number]["verdict"],
      failure_reason: "",
      steps: [],
    })),
  };
}

describe("runsInLastDays", () => {
  it("includes runs strictly within the window", () => {
    const runs = [
      mkRun("a", "2026-04-19T11:00:00Z", ["passed"]), // 6d 1h ago — IN
      mkRun("a", "2026-04-18T11:00:00Z", ["passed"]), // 7d 1h ago — OUT
      mkRun("a", "2026-04-25T11:00:00Z", ["passed"]), // 1h ago — IN
    ];
    const filtered = runsInLastDays(runs, 7, NOW);
    expect(filtered).toHaveLength(2);
  });

  it("returns empty when no runs are in window", () => {
    const runs = [mkRun("a", "2026-01-01T00:00:00Z", ["passed"])];
    expect(runsInLastDays(runs, 7, NOW)).toEqual([]);
  });
});

describe("passRateLast7Days", () => {
  it("returns null when there are no runs in the window", () => {
    expect(passRateLast7Days([], NOW)).toBeNull();
  });

  it("returns 1.0 for all passing", () => {
    const runs = [
      mkRun("a", "2026-04-24T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["passed"]),
    ];
    expect(passRateLast7Days(runs, NOW)).toBe(1);
  });

  it("returns 0.5 for half pass / half fail", () => {
    const runs = [
      mkRun("a", "2026-04-24T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["failed"]),
    ];
    expect(passRateLast7Days(runs, NOW)).toBe(0.5);
  });

  it("ignores skipped runs in the denominator", () => {
    const runs = [
      mkRun("a", "2026-04-24T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["skipped"]),
    ];
    expect(passRateLast7Days(runs, NOW)).toBe(1);
  });
});

describe("summarizeSuite", () => {
  it("rolls a suite's runs into a SuiteSummary", () => {
    const runs = [
      mkRun("worker-onboarding", "2026-04-25T10:00:00Z", ["passed"]),
      mkRun("worker-onboarding", "2026-04-24T10:00:00Z", ["failed"]),
    ];
    const summary = summarizeSuite("worker-onboarding", runs, NOW);
    expect(summary.suite_id).toBe("worker-onboarding");
    expect(summary.latest_verdict).toBe("passed");
    expect(summary.is_flaky).toBe(true);
    expect(summary.pass_rate_7d).toBe(0.5);
    expect(summary.run_count_7d).toBe(2);
    expect(summary.total_runs).toBe(2);
    expect(summary.latest_run_at).toBe("2026-04-25T10:00:00Z");
  });

  it("returns null pass_rate when no runs are in the 7d window", () => {
    const runs = [
      mkRun("worker-onboarding", "2026-01-01T00:00:00Z", ["passed"]),
    ];
    const summary = summarizeSuite("worker-onboarding", runs, NOW);
    expect(summary.pass_rate_7d).toBeNull();
    expect(summary.run_count_7d).toBe(0);
    expect(summary.total_runs).toBe(1);
  });

  it("uses the most recent run's suite_name as the summary's display name", () => {
    const runs = [
      { ...mkRun("a", "2026-04-25T10:00:00Z", ["passed"]), suite_name: "Latest Name" },
      { ...mkRun("a", "2026-04-20T10:00:00Z", ["passed"]), suite_name: "Old Name" },
    ];
    const summary = summarizeSuite("a", runs, NOW);
    expect(summary.suite_name).toBe("Latest Name");
  });
});
