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
import {
  computeCliff,
  cliffEdgeForHousehold,
  wageGlowColor,
  wageGlowIntensity,
} from "../cliffMath";

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

describe("wageGlowColor — continuous wage-state glow (Ch07)", () => {
  // The glow color is the same in both cliff cards — controls panel
  // (left) and chart card (right) — so the two read as a paired state.
  // Pure cyan when comfortably below the cliff, blends through amber at
  // the edge, settles to pure rose past the cliff. Bands are relative to
  // the household-aware cliff edge.

  it("returns pure cyan when wage is comfortably below the cliff (delta <= -4)", () => {
    // HH=1, edge=$19 → wage=$14 means delta=-5 (clamped to -4).
    expect(wageGlowColor(14, 1)).toBe("var(--accent-cyan)");
    // HH=2, edge=$21 → wage=$16 means delta=-5.
    expect(wageGlowColor(16, 2)).toBe("var(--accent-cyan)");
    // HH=4, edge=$27 → wage=$22 means delta=-5.
    expect(wageGlowColor(22, 4)).toBe("var(--accent-cyan)");
  });

  it("returns a cyan→amber color-mix when delta is in (-4, 0)", () => {
    // HH=1, edge=$19 → wage=$17 means delta=-2 → 50% amber blend.
    const mid = wageGlowColor(17, 1);
    expect(mid).toMatch(/color-mix\(in oklch, var\(--accent-cyan\), var\(--accent-amber\) \d+%\)/);
    // wage=$15.5, delta=-3.5 → 13% amber blend (low).
    // (4 + -3.5) / 4 = 0.125 → Math.round(12.5) = 13.
    expect(wageGlowColor(15.5, 1)).toMatch(/var\(--accent-amber\) 13%/);
    // wage=$18, delta=-1 → 75% amber blend (high).
    expect(wageGlowColor(18, 1)).toMatch(/var\(--accent-amber\) 75%/);
  });

  it("returns pure amber at the cliff edge (delta = 0)", () => {
    // delta=0 → "amber → rose 0%" which is functionally pure amber.
    expect(wageGlowColor(19, 1)).toMatch(/var\(--accent-rose\) 0%/);
    expect(wageGlowColor(21, 2)).toMatch(/var\(--accent-rose\) 0%/);
    expect(wageGlowColor(27, 4)).toMatch(/var\(--accent-rose\) 0%/);
  });

  it("returns an amber→rose color-mix when delta is in (0, 2)", () => {
    // wage=$20, edge=$19 → delta=+1 → 50% rose blend.
    expect(wageGlowColor(20, 1)).toMatch(/var\(--accent-rose\) 50%/);
    // wage=$19.5, delta=+0.5 → 25% rose blend.
    expect(wageGlowColor(19.5, 1)).toMatch(/var\(--accent-rose\) 25%/);
  });

  it("returns pure rose when wage is past the cliff by 2+ (delta >= +2)", () => {
    expect(wageGlowColor(21, 1)).toBe("var(--accent-rose)");
    expect(wageGlowColor(24, 1)).toBe("var(--accent-rose)");
    expect(wageGlowColor(29, 4)).toBe("var(--accent-rose)");
  });

  it("defaults to household=1 when household omitted (back-compat with computeCliff)", () => {
    expect(wageGlowColor(14)).toBe(wageGlowColor(14, 1));
    expect(wageGlowColor(20)).toBe(wageGlowColor(20, 1));
  });
});

describe("wageGlowIntensity — alpha curve peaks at the cliff edge", () => {
  // Range [0.32, 0.62]. Peaks at delta=0 (edge), drops to floor at
  // |delta|>=5. So the user gets the strongest visual warning right
  // when the slider crosses the edge — math urgency = visual urgency.

  it("peaks at delta=0 (cliff edge)", () => {
    expect(wageGlowIntensity(19, 1)).toBeCloseTo(0.62, 2);
    expect(wageGlowIntensity(21, 2)).toBeCloseTo(0.62, 2);
    expect(wageGlowIntensity(27, 4)).toBeCloseTo(0.62, 2);
  });

  it("hits floor 0.32 when wage is far from the edge (|delta| >= 5)", () => {
    expect(wageGlowIntensity(14, 1)).toBeCloseTo(0.32, 2); // -5
    expect(wageGlowIntensity(24, 1)).toBeCloseTo(0.32, 2); // +5
  });

  it("never goes below the floor or above the peak", () => {
    for (let w = 14; w <= 32; w += 0.5) {
      const i1 = wageGlowIntensity(w, 1);
      const i4 = wageGlowIntensity(w, 4);
      expect(i1).toBeGreaterThanOrEqual(0.32);
      expect(i1).toBeLessThanOrEqual(0.62);
      expect(i4).toBeGreaterThanOrEqual(0.32);
      expect(i4).toBeLessThanOrEqual(0.62);
    }
  });

  it("defaults to household=1 when household omitted", () => {
    expect(wageGlowIntensity(19)).toBe(wageGlowIntensity(19, 1));
  });
});
