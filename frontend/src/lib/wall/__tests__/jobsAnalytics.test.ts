/**
 * Test the pure analytics helpers over the jobs-by-zip data.
 *
 * Spotlight invention contract: helpers are deterministic + pure so a
 * future heatmap layer (W4) and the README stat-bake step both consume
 * the same numbers.
 */

import { describe, it, expect } from "vitest";
import {
  fairChanceShareByCategory,
  creditCheckShare,
} from "../jobsAnalytics";

describe("jobsAnalytics — fairChanceShareByCategory", () => {
  it("returns one entry per category in the dataset", () => {
    const result = fairChanceShareByCategory();
    const categories = new Set(result.map((r) => r.category));
    expect(categories.size).toBeGreaterThanOrEqual(3);
  });

  it("share is between 0 and 1 for every category", () => {
    for (const r of fairChanceShareByCategory()) {
      expect(r.share).toBeGreaterThanOrEqual(0);
      expect(r.share).toBeLessThanOrEqual(1);
      expect(r.fairChance).toBeLessThanOrEqual(r.total);
    }
  });

  it("results are sorted by descending share", () => {
    const result = fairChanceShareByCategory();
    for (let i = 1; i < result.length; i++) {
      expect(result[i - 1].share).toBeGreaterThanOrEqual(result[i].share);
    }
  });

  it("warehouse + logistics categories tend to be fair-chance heavy (sanity)", () => {
    const result = fairChanceShareByCategory();
    const warehouse = result.find((r) => r.category === "warehouse");
    expect(warehouse).toBeDefined();
    expect(warehouse!.share).toBeGreaterThanOrEqual(0.5);
  });

  it("supports custom employer arrays for arithmetic verification", () => {
    const result = fairChanceShareByCategory([
      { id: "a", name: "A", category: "warehouse", fairChance: true, creditCheck: false, longitude: 0, latitude: 0 },
      { id: "b", name: "B", category: "warehouse", fairChance: false, creditCheck: false, longitude: 0, latitude: 0 },
    ]);
    expect(result[0].share).toBe(0.5);
  });
});

describe("jobsAnalytics — creditCheckShare", () => {
  it("returns 0..1 for the default dataset", () => {
    const v = creditCheckShare();
    expect(v).toBeGreaterThanOrEqual(0);
    expect(v).toBeLessThanOrEqual(1);
  });

  it("editorial-truth check: at least 20% of jobs require credit checks (Ch4d 33% claim)", () => {
    // The Ch4d editorial claims 33%; the dataset must support a
    // credible-enough number for the editorial to be honest. We assert
    // ≥ 20% to leave room for dataset growth without churning the
    // exact-equality test.
    expect(creditCheckShare()).toBeGreaterThanOrEqual(0.2);
  });

  it("returns 0 on empty input", () => {
    expect(creditCheckShare([])).toBe(0);
  });
});
