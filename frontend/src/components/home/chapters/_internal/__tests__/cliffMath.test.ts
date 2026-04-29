/**
 * Driver C — polish-2 T32 — cliffMath unit tests.
 *
 * Locks the household-size adjustment: the cliff zone shifts up the wage
 * axis as household size grows because the income limits for SNAP /
 * childcare / Medicaid scale with household size.
 *
 * Cliff-edge wage by household size:
 *   1 → $19, 2 → $21, 3 → $24, 4 → $27.
 *
 * Backwards compat: `computeCliff(wage)` keeps the household-1 result.
 */
import { describe, it, expect } from "vitest";
import { computeCliff, cliffEdgeForHousehold } from "../cliffMath";

describe("cliffMath — household-size adjustment (T32)", () => {
  it("computeCliff(20, 1) flags lapses (cliff edge $19)", () => {
    const out = computeCliff(20, 1);
    expect(out.medicaid).toBe("lapses");
  });

  it("computeCliff(20, 4) is safe — household of 4 has cliff edge $27", () => {
    const out = computeCliff(20, 4);
    expect(out.medicaid).toBe("safe");
  });

  it("cliffEdgeForHousehold returns 19/21/24/27", () => {
    expect(cliffEdgeForHousehold(1)).toBe(19);
    expect(cliffEdgeForHousehold(2)).toBe(21);
    expect(cliffEdgeForHousehold(3)).toBe(24);
    expect(cliffEdgeForHousehold(4)).toBe(27);
  });

  it("computeCliff(wage) without household defaults to household-1", () => {
    const a = computeCliff(20);
    const b = computeCliff(20, 1);
    expect(a.medicaid).toBe(b.medicaid);
    expect(a.snapDelta).toBe(b.snapDelta);
    expect(a.ccDelta).toBe(b.ccDelta);
  });

  it("household=4 keeps SNAP delta = 0 at $20 (under that household's cliff)", () => {
    const out = computeCliff(20, 4);
    expect(out.snapDelta).toBe(0);
  });

  it("household=2 puts $20 under the cliff (at-risk zone)", () => {
    const out = computeCliff(20, 2);
    expect(out.medicaid).toBe("at risk");
  });

  it("markerX is unchanged by household size — chart x-axis is wage", () => {
    const a = computeCliff(20, 1);
    const b = computeCliff(20, 4);
    expect(a.markerX).toBe(b.markerX);
  });
});
