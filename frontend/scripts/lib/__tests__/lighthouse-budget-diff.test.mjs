/**
 * W4 Driver C Spotlight #3 — lighthouse-budget-diff library tests.
 *
 * Pure-function unit tests. The CLI shim is a thin entry that imports
 * this lib (same shape as scripts/verify-contrast.mjs + lib/contrast.mjs).
 */
import { describe, it, expect } from "vitest";
import {
  extractCategoryScores,
  humanize,
  diffSummaries,
  formatDeltaLine,
  formatDiffReport,
  REGRESSION_THRESHOLD_PTS,
  AUDITED_CATEGORIES,
} from "../lighthouse-budget-diff.mjs";

describe("lighthouse-budget-diff — extractCategoryScores", () => {
  it("returns [] for null / undefined input", () => {
    expect(extractCategoryScores(null)).toEqual([]);
    expect(extractCategoryScores(undefined)).toEqual([]);
  });

  it("parses the manifest-row shape ({ summary: { performance: 0.9 } })", () => {
    const row = {
      summary: {
        performance: 0.92,
        accessibility: 0.95,
        "best-practices": 0.93,
        seo: 0.91,
      },
    };
    const scores = extractCategoryScores(row);
    expect(scores).toHaveLength(4);
    expect(scores.find((s) => s.category === "performance")?.score).toBe(0.92);
  });

  it("parses the raw lhci result shape ({ categories: { performance: { score: ... } } })", () => {
    const raw = {
      categories: {
        performance: { score: 0.88 },
        accessibility: { score: 0.97 },
        "best-practices": { score: 0.92 },
        seo: { score: 0.95 },
      },
    };
    const scores = extractCategoryScores(raw);
    expect(scores).toHaveLength(4);
    expect(scores.find((s) => s.category === "performance")?.score).toBe(0.88);
  });

  it("ignores unknown categories not in AUDITED_CATEGORIES", () => {
    const row = {
      summary: { performance: 0.9, "pwa-deprecated": 0.7 },
    };
    const scores = extractCategoryScores(row);
    expect(scores.map((s) => s.category)).toEqual(["performance"]);
  });
});

describe("lighthouse-budget-diff — humanize", () => {
  it("converts 0..1 to 0..100 rounded", () => {
    expect(humanize(0.92)).toBe(92);
    expect(humanize(0.875)).toBe(88);
    expect(humanize(0)).toBe(0);
    expect(humanize(1)).toBe(100);
  });

  it("returns 0 for invalid input", () => {
    expect(humanize(NaN)).toBe(0);
    expect(humanize(undefined)).toBe(0);
    expect(humanize(null)).toBe(0);
    expect(humanize("0.9")).toBe(0);
  });
});

describe("lighthouse-budget-diff — diffSummaries", () => {
  it("flat (no change) — no regressions", () => {
    const prev = [{ category: "performance", score: 0.92 }];
    const curr = [{ category: "performance", score: 0.92 }];
    const summary = diffSummaries(prev, curr);
    expect(summary.anyRegression).toBe(false);
    expect(summary.deltas[0]).toMatchObject({ delta: 0, regression: false });
  });

  it("a 6-pt drop on performance is a regression (threshold = 5)", () => {
    const prev = [{ category: "performance", score: 0.92 }];
    const curr = [{ category: "performance", score: 0.86 }];
    const summary = diffSummaries(prev, curr);
    expect(summary.anyRegression).toBe(true);
    expect(summary.worstRegression?.category).toBe("performance");
    expect(summary.worstRegression?.delta).toBe(-6);
  });

  it("a 5-pt drop is NOT a regression (threshold inclusive at 5)", () => {
    const prev = [{ category: "performance", score: 0.92 }];
    const curr = [{ category: "performance", score: 0.87 }];
    const summary = diffSummaries(prev, curr);
    expect(summary.anyRegression).toBe(false);
  });

  it("an improvement is positive delta, never a regression", () => {
    const prev = [{ category: "performance", score: 0.85 }];
    const curr = [{ category: "performance", score: 0.95 }];
    const summary = diffSummaries(prev, curr);
    expect(summary.anyRegression).toBe(false);
    expect(summary.deltas[0].delta).toBe(10);
  });

  it("worstRegression picks the largest drop across multiple categories", () => {
    const prev = [
      { category: "performance", score: 0.95 },
      { category: "accessibility", score: 0.95 },
    ];
    const curr = [
      { category: "performance", score: 0.85 }, // -10
      { category: "accessibility", score: 0.88 }, // -7
    ];
    const summary = diffSummaries(prev, curr);
    expect(summary.anyRegression).toBe(true);
    expect(summary.worstRegression?.category).toBe("performance");
    expect(summary.worstRegression?.delta).toBe(-10);
  });

  it("ignores categories present in only one side", () => {
    const prev = [
      { category: "performance", score: 0.95 },
      { category: "accessibility", score: 0.95 },
    ];
    const curr = [{ category: "performance", score: 0.95 }];
    const summary = diffSummaries(prev, curr);
    expect(summary.deltas).toHaveLength(1);
    expect(summary.deltas[0].category).toBe("performance");
  });
});

describe("lighthouse-budget-diff — formatDeltaLine", () => {
  it("formats a no-change line", () => {
    const line = formatDeltaLine({
      category: "performance",
      prev: 92,
      curr: 92,
      delta: 0,
      regression: false,
    });
    expect(line).toContain("performance");
    expect(line).toContain("92 → 92");
    expect(line).toContain("(+0)");
  });

  it("appends REGRESSION tag when delta is below threshold", () => {
    const line = formatDeltaLine({
      category: "performance",
      prev: 92,
      curr: 80,
      delta: -12,
      regression: true,
    });
    expect(line).toContain("REGRESSION");
  });
});

describe("lighthouse-budget-diff — formatDiffReport", () => {
  it("emits a header + per-category lines", () => {
    const summary = {
      deltas: [
        { category: "performance", prev: 92, curr: 92, delta: 0, regression: false },
        { category: "accessibility", prev: 95, curr: 96, delta: 1, regression: false },
      ],
      anyRegression: false,
      worstRegression: null,
    };
    const report = formatDiffReport(summary);
    expect(report).toContain("Lighthouse score diff");
    expect(report).toContain("performance");
    expect(report).toContain("accessibility");
  });

  it("includes WORST line when there is a regression", () => {
    const summary = {
      deltas: [
        { category: "performance", prev: 92, curr: 80, delta: -12, regression: true },
      ],
      anyRegression: true,
      worstRegression: { category: "performance", delta: -12 },
    };
    const report = formatDiffReport(summary);
    expect(report).toContain("WORST");
    expect(report).toContain("12 pts");
  });
});

describe("lighthouse-budget-diff — constants", () => {
  it("REGRESSION_THRESHOLD_PTS is 5 (typical Lighthouse-CI noise floor)", () => {
    expect(REGRESSION_THRESHOLD_PTS).toBe(5);
  });

  it("AUDITED_CATEGORIES covers the four W4 hard-gate categories", () => {
    expect(AUDITED_CATEGORIES).toEqual([
      "performance",
      "accessibility",
      "best-practices",
      "seo",
    ]);
  });
});
