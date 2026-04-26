import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, writeFileSync, rmSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadRunsFromDir } from "../runs_dir";

let dir: string;

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "qc-runs-"));
});

afterEach(() => {
  rmSync(dir, { recursive: true, force: true });
});

describe("loadRunsFromDir", () => {
  it("returns empty array when the directory is missing", () => {
    expect(loadRunsFromDir(join(dir, "does-not-exist"))).toEqual([]);
  });

  it("returns empty array for an empty directory", () => {
    expect(loadRunsFromDir(dir)).toEqual([]);
  });

  it("loads and parses every matching JSON file", () => {
    writeFileSync(
      join(dir, "worker-onboarding-2026-04-25T12-00-00.json"),
      JSON.stringify({
        suite_name: "Worker Onboarding",
        environment: "dev",
        scenarios: [
          { name: "happy", verdict: "passed", failure_reason: "", steps: [] },
        ],
      }),
    );
    writeFileSync(
      join(dir, "advisor-send-note-2026-04-24T09-00-00.json"),
      JSON.stringify({
        suite_name: "Advisor Send Note",
        environment: "dev",
        scenarios: [
          { name: "ok", verdict: "failed", failure_reason: "x", steps: [] },
        ],
      }),
    );
    // Decoy file that should be ignored
    writeFileSync(join(dir, "README.md"), "ignore me");

    const runs = loadRunsFromDir(dir);
    expect(runs).toHaveLength(2);
    const ids = runs.map((r) => r.suite_id).sort();
    expect(ids).toEqual(["advisor-send-note", "worker-onboarding"]);
  });

  it("skips malformed JSON without crashing", () => {
    writeFileSync(
      join(dir, "broken-2026-04-25T12-00-00.json"),
      "{ not json",
    );
    writeFileSync(
      join(dir, "good-2026-04-25T12-00-00.json"),
      JSON.stringify({ suite_name: "Good", environment: "dev", scenarios: [] }),
    );
    const runs = loadRunsFromDir(dir);
    expect(runs).toHaveLength(1);
    expect(runs[0].suite_id).toBe("good");
  });

  it("does NOT recurse into subdirectories", () => {
    mkdirSync(join(dir, "nested"));
    writeFileSync(
      join(dir, "nested", "x-2026-04-25T12-00-00.json"),
      JSON.stringify({ suite_name: "X", environment: "dev", scenarios: [] }),
    );
    expect(loadRunsFromDir(dir)).toHaveLength(0);
  });
});
