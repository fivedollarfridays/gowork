/**
 * W3 Driver C Spotlight #1 — axeChapterRunner contract tests.
 *
 * The runner wraps axe-core invocation + filtering + reporting so every
 * future chapter test reuses the SAME ruleset and severity threshold.
 * Without this, each driver invents their own AXE_OPTIONS and severity
 * threshold, which leaks contrast/landmark false positives across PRs.
 *
 * NOTE — these tests run the runner against synthetic DOM nodes (no
 * React render), so they're fast and don't depend on chapter components
 * existing. The actual chapter usage tests live in
 * `frontend/src/components/wall/__tests__/w3-a11y.test.tsx`.
 */
import { describe, expect, it } from "vitest";
import {
  axeChapterRules,
  filterModerateOrAbove,
  AXE_MIN_SEVERITY,
} from "../axeChapterRunner";
import type { Result as AxeResult } from "axe-core";

describe("axeChapterRunner — AXE_MIN_SEVERITY", () => {
  it("is set to 'moderate' (W3 dispatch contract)", () => {
    expect(AXE_MIN_SEVERITY).toBe("moderate");
  });
});

describe("axeChapterRunner — axeChapterRules", () => {
  it("disables color-contrast (jsdom can't compute pixel colors)", () => {
    expect(axeChapterRules.rules?.["color-contrast"]).toEqual({ enabled: false });
  });

  it("disables meta-viewport (lives in app/layout, not chapters)", () => {
    expect(axeChapterRules.rules?.["meta-viewport"]).toEqual({ enabled: false });
  });

  it("disables landmark-one-main (chapters render outside <main> in tests)", () => {
    expect(axeChapterRules.rules?.["landmark-one-main"]).toEqual({ enabled: false });
  });

  it("disables 'region' rule (test-time region wrappers)", () => {
    expect(axeChapterRules.rules?.region).toEqual({ enabled: false });
  });
});

function fakeViolation(impact: AxeResult["impact"]): AxeResult {
  return {
    id: "fake-rule",
    impact,
    description: "fake",
    help: "fake",
    helpUrl: "https://example.test/fake",
    tags: [],
    nodes: [],
  };
}

describe("axeChapterRunner — filterModerateOrAbove", () => {
  it("keeps moderate violations", () => {
    const out = filterModerateOrAbove([fakeViolation("moderate")]);
    expect(out).toHaveLength(1);
  });

  it("keeps serious violations", () => {
    const out = filterModerateOrAbove([fakeViolation("serious")]);
    expect(out).toHaveLength(1);
  });

  it("keeps critical violations", () => {
    const out = filterModerateOrAbove([fakeViolation("critical")]);
    expect(out).toHaveLength(1);
  });

  it("drops minor violations", () => {
    const out = filterModerateOrAbove([fakeViolation("minor")]);
    expect(out).toHaveLength(0);
  });

  it("drops null/undefined-impact violations (axe sometimes emits these)", () => {
    const out = filterModerateOrAbove([
      fakeViolation(null as unknown as AxeResult["impact"]),
    ]);
    expect(out).toHaveLength(0);
  });

  it("preserves array order for multi-violation input", () => {
    const v1 = fakeViolation("moderate");
    const v2 = fakeViolation("serious");
    const out = filterModerateOrAbove([v1, v2]);
    expect(out[0]).toBe(v1);
    expect(out[1]).toBe(v2);
  });
});
