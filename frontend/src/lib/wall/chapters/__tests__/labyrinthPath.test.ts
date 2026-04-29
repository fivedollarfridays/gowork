/**
 * W2 Driver C — labyrinthPath geometry contract.
 *
 * Narrative Reset (sprint/narrative-reset): each node now carries a
 * `barrierKey` mapping it to the barrier the user faces if they have to
 * visit that office alone. Convergence helpers (CONVERGENCE_THRESHOLD +
 * isConverged) gate the "47 forms / 5 offices" caption reveal.
 */
import { describe, it, expect } from "vitest";
import {
  LABYRINTH_NODES,
  LABYRINTH_PATH_D,
  LABYRINTH_PATH_LENGTH,
  progressDashoffset,
  isNodeLit,
  isConverged,
  CONVERGENCE_THRESHOLD,
} from "../labyrinthPath";

describe("LABYRINTH_NODES", () => {
  it("declares exactly 5 office nodes", () => {
    expect(LABYRINTH_NODES).toHaveLength(5);
  });

  it("each node has a unique id", () => {
    const ids = LABYRINTH_NODES.map((n) => n.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("nodes fit inside the 0..1000 viewBox", () => {
    for (const n of LABYRINTH_NODES) {
      expect(n.x).toBeGreaterThanOrEqual(0);
      expect(n.x).toBeLessThanOrEqual(1000);
      expect(n.y).toBeGreaterThanOrEqual(0);
      expect(n.y).toBeLessThanOrEqual(1000);
    }
  });
});

describe("LABYRINTH_PATH_D", () => {
  it("starts with a Move command", () => {
    expect(LABYRINTH_PATH_D.startsWith("M ")).toBe(true);
  });

  it("contains at least 6 line segments (dead-end branches + retraces)", () => {
    // The labyrinth is chaotic by design: every "L X Y" command is either
    // a dead-end branch or a retrace step. 6+ such segments is the visual
    // floor for "this looks like a maze" per docs/visual-rebirth-plan.md.
    const lMatches = LABYRINTH_PATH_D.match(/L \d+ \d+/g) ?? [];
    expect(lMatches.length).toBeGreaterThanOrEqual(6);
  });

  it("includes at least 2 cubic Bezier segments (loops feel curved)", () => {
    const matches = LABYRINTH_PATH_D.match(/\bC\b/g);
    expect((matches?.length ?? 0)).toBeGreaterThanOrEqual(2);
  });
});

describe("progressDashoffset", () => {
  it("returns the full length at progress=0 (path hidden)", () => {
    expect(progressDashoffset(0)).toBe(LABYRINTH_PATH_LENGTH);
  });

  it("returns 0 at progress=1 (path fully drawn)", () => {
    expect(progressDashoffset(1)).toBe(0);
  });

  it("interpolates linearly at the midpoint", () => {
    expect(progressDashoffset(0.5)).toBe(
      Math.round(LABYRINTH_PATH_LENGTH / 2),
    );
  });

  it("clamps progress < 0 to the full hidden length", () => {
    expect(progressDashoffset(-1)).toBe(LABYRINTH_PATH_LENGTH);
  });

  it("clamps progress > 1 to fully drawn", () => {
    expect(progressDashoffset(2)).toBe(0);
  });
});

describe("LABYRINTH_NODES — barrier mapping (Narrative Reset)", () => {
  it("each node carries a barrierKey", () => {
    for (const n of LABYRINTH_NODES) {
      expect(typeof n.barrierKey).toBe("string");
      expect(n.barrierKey.length).toBeGreaterThan(0);
    }
  });

  it("each node carries an officeKey matching its id", () => {
    for (const n of LABYRINTH_NODES) {
      expect(n.officeKey).toBe(n.id);
    }
  });

  it("declares the canonical 5-barrier set: criminalRecord, transit, childcare, credit, id", () => {
    const keys = LABYRINTH_NODES.map((n) => n.barrierKey).sort();
    expect(keys).toEqual(
      ["childcare", "credit", "criminalRecord", "id", "transit"].sort(),
    );
  });
});

describe("isConverged", () => {
  it("returns false before the convergence threshold", () => {
    expect(isConverged(0)).toBe(false);
    expect(isConverged(0.5)).toBe(false);
    expect(isConverged(CONVERGENCE_THRESHOLD - 0.01)).toBe(false);
  });

  it("returns true at and past the convergence threshold", () => {
    expect(isConverged(CONVERGENCE_THRESHOLD)).toBe(true);
    expect(isConverged(0.95)).toBe(true);
    expect(isConverged(1)).toBe(true);
  });

  it("clamps progress > 1 and < 0 safely", () => {
    expect(isConverged(2)).toBe(true);
    expect(isConverged(-1)).toBe(false);
  });
});

describe("isNodeLit", () => {
  it("lights node 0 early in the chapter", () => {
    expect(isNodeLit(0, 0.05)).toBe(true);
  });

  it("does NOT light node 4 until late", () => {
    expect(isNodeLit(4, 0.5)).toBe(false);
  });

  it("lights all nodes at progress=1", () => {
    for (let i = 0; i < LABYRINTH_NODES.length; i++) {
      expect(isNodeLit(i, 1)).toBe(true);
    }
  });
});
