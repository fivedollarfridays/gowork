import { describe, it, expect } from "vitest";
import { parseRunFile, groupBySuite, suiteIdFromFilename } from "../loader";

describe("suiteIdFromFilename", () => {
  it("extracts suite id from `<suite>-<ISO timestamp>.json`", () => {
    expect(
      suiteIdFromFilename("worker-onboarding-2026-04-25T12-00-00.json"),
    ).toEqual({
      suite_id: "worker-onboarding",
      timestamp: "2026-04-25T12:00:00Z",
    });
  });

  it("handles single-token suite ids", () => {
    expect(
      suiteIdFromFilename("smoke-2026-04-25T12-00-00.json"),
    ).toEqual({
      suite_id: "smoke",
      timestamp: "2026-04-25T12:00:00Z",
    });
  });

  it("returns null for files that don't match the pattern", () => {
    expect(suiteIdFromFilename("not-a-run.txt")).toBeNull();
    expect(suiteIdFromFilename("README.md")).toBeNull();
  });
});

describe("parseRunFile", () => {
  it("populates suite_id + timestamp from filename when JSON omits them", () => {
    const json = JSON.stringify({
      suite_name: "Worker Onboarding",
      environment: "dev",
      scenarios: [
        { name: "happy", verdict: "passed", failure_reason: "", steps: [] },
      ],
    });
    const run = parseRunFile(
      "worker-onboarding-2026-04-25T12-00-00.json",
      json,
    );
    expect(run).not.toBeNull();
    expect(run!.suite_id).toBe("worker-onboarding");
    expect(run!.suite_name).toBe("Worker Onboarding");
    expect(run!.timestamp).toBe("2026-04-25T12:00:00Z");
    expect(run!.scenarios).toHaveLength(1);
  });

  it("returns null for malformed JSON (does not crash)", () => {
    const run = parseRunFile(
      "worker-onboarding-2026-04-25T12-00-00.json",
      "{not json",
    );
    expect(run).toBeNull();
  });

  it("returns null for files whose name doesn't match the pattern", () => {
    const json = JSON.stringify({ suite_name: "x", environment: "dev", scenarios: [] });
    expect(parseRunFile("README.md", json)).toBeNull();
  });
});

describe("groupBySuite", () => {
  it("groups runs by suite_id", () => {
    const runs = [
      {
        suite_id: "a",
        suite_name: "A",
        environment: "dev",
        timestamp: "2026-04-25T10:00:00Z",
        scenarios: [],
      },
      {
        suite_id: "b",
        suite_name: "B",
        environment: "dev",
        timestamp: "2026-04-25T10:00:00Z",
        scenarios: [],
      },
      {
        suite_id: "a",
        suite_name: "A",
        environment: "dev",
        timestamp: "2026-04-24T10:00:00Z",
        scenarios: [],
      },
    ];
    const grouped = groupBySuite(runs);
    expect(grouped.get("a")).toHaveLength(2);
    expect(grouped.get("b")).toHaveLength(1);
  });
});
