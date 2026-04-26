import { describe, it, expect } from "vitest";
import {
  isFlaky,
  latestVerdict,
  scenarioVerdicts,
  suiteVerdict,
} from "../flakes";
import type { QcRun } from "../types";

function mkRun(suiteId: string, isoTs: string, verdicts: string[]): QcRun {
  return {
    suite_id: suiteId,
    suite_name: suiteId,
    environment: "dev",
    timestamp: isoTs,
    scenarios: verdicts.map((v, i) => ({
      name: `scenario-${i}`,
      verdict: v as QcRun["scenarios"][number]["verdict"],
      failure_reason: "",
      steps: [],
    })),
  };
}

describe("suiteVerdict", () => {
  it("returns 'passed' when all scenarios passed", () => {
    const run = mkRun("a", "2026-04-25T10:00:00Z", ["passed", "passed"]);
    expect(suiteVerdict(run)).toBe("passed");
  });

  it("returns 'failed' if any scenario failed", () => {
    const run = mkRun("a", "2026-04-25T10:00:00Z", ["passed", "failed"]);
    expect(suiteVerdict(run)).toBe("failed");
  });

  it("returns 'error' if any scenario errored (and no failures)", () => {
    const run = mkRun("a", "2026-04-25T10:00:00Z", ["passed", "error"]);
    expect(suiteVerdict(run)).toBe("error");
  });

  it("returns 'skipped' when only skipped/passed and at least one skip", () => {
    const run = mkRun("a", "2026-04-25T10:00:00Z", ["skipped", "skipped"]);
    expect(suiteVerdict(run)).toBe("skipped");
  });
});

describe("latestVerdict", () => {
  it("picks the run with the most recent timestamp", () => {
    const older = mkRun("a", "2026-04-20T10:00:00Z", ["passed"]);
    const newer = mkRun("a", "2026-04-25T10:00:00Z", ["failed"]);
    expect(latestVerdict([older, newer])).toBe("failed");
  });

  it("returns 'unknown' for empty input", () => {
    expect(latestVerdict([])).toBe("unknown");
  });
});

describe("scenarioVerdicts", () => {
  it("flattens scenario verdicts across last N runs", () => {
    const runs = [
      mkRun("a", "2026-04-21T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-22T10:00:00Z", ["failed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["passed"]),
    ];
    expect(scenarioVerdicts(runs, 5)).toEqual(["passed", "failed", "passed"]);
  });

  it("limits to last N runs (most recent)", () => {
    const runs = Array.from({ length: 10 }, (_, i) =>
      mkRun("a", `2026-04-${String(10 + i).padStart(2, "0")}T10:00:00Z`, [
        i % 2 === 0 ? "passed" : "failed",
      ]),
    );
    // Last 5 by date: i=5..9 → fail, pass, fail, pass, fail
    expect(scenarioVerdicts(runs, 5)).toEqual([
      "failed",
      "passed",
      "failed",
      "passed",
      "failed",
    ]);
  });
});

describe("isFlaky", () => {
  it("identical-pass-streak is NOT flaky", () => {
    const runs = [
      mkRun("a", "2026-04-21T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-22T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["passed"]),
    ];
    expect(isFlaky(runs)).toBe(false);
  });

  it("alternating pass/fail in last 5 IS flaky", () => {
    const runs = [
      mkRun("a", "2026-04-21T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-22T10:00:00Z", ["failed"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["passed"]),
    ];
    expect(isFlaky(runs)).toBe(true);
  });

  it("all-fails is NOT flaky (just failing)", () => {
    const runs = [
      mkRun("a", "2026-04-21T10:00:00Z", ["failed"]),
      mkRun("a", "2026-04-22T10:00:00Z", ["failed"]),
    ];
    expect(isFlaky(runs)).toBe(false);
  });

  it("ignores skipped runs when deciding flakiness", () => {
    const runs = [
      mkRun("a", "2026-04-21T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-22T10:00:00Z", ["skipped"]),
      mkRun("a", "2026-04-23T10:00:00Z", ["passed"]),
    ];
    expect(isFlaky(runs)).toBe(false);
  });

  it("only considers the last 5 runs", () => {
    // Old failures shouldn't count once they fall out of the window
    const runs: QcRun[] = [
      mkRun("a", "2026-04-10T10:00:00Z", ["failed"]),
      mkRun("a", "2026-04-11T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-12T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-13T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-14T10:00:00Z", ["passed"]),
      mkRun("a", "2026-04-15T10:00:00Z", ["passed"]),
    ];
    expect(isFlaky(runs)).toBe(false);
  });
});
