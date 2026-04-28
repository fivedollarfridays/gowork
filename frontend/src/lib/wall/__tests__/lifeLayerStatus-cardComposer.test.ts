/**
 * Cross-spotlight integration: lifeLayerStatus → cardComposer mood line.
 *
 * Verifies that PHASE_TO_MOOD covers the full W4Phase set the OG card
 * composer might want to consume. If a future driver renames a phase
 * key in `timeOfDayPalette`, this test catches it because both modules
 * import from the same type.
 */

import { describe, it, expect } from "vitest";
import {
  PHASE_TO_MOOD,
  deriveLifeLayerStatus,
} from "../lifeLayerStatus";
import { phaseFromHour } from "../timeOfDayPalette";

describe("lifeLayerStatus × timeOfDayPalette: phase coverage", () => {
  it("phaseFromHour returns a key that PHASE_TO_MOOD has a mood for (full hour sweep)", () => {
    for (let h = 0; h < 24; h += 1) {
      const phase = phaseFromHour(h);
      expect(PHASE_TO_MOOD[phase]).toBeDefined();
      expect(typeof PHASE_TO_MOOD[phase]).toBe("string");
      expect(PHASE_TO_MOOD[phase].length).toBeGreaterThan(0);
    }
  });

  it("each hour-of-day yields a non-empty mood when run through deriveLifeLayerStatus", () => {
    for (let h = 0; h < 24; h += 1) {
      const phase = phaseFromHour(h);
      const status = deriveLifeLayerStatus({
        phase,
        globalProgress: 0,
        cursorInsideMap: false,
        idle: false,
      });
      expect(status.mood.length).toBeGreaterThan(0);
    }
  });

  it("idle dominates over cursor-in-map", () => {
    const status = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0.5,
      cursorInsideMap: true,
      idle: true,
    });
    expect(status.active).toBe("idle");
  });

  it("cursor-in-map dominates over live (mid-scroll)", () => {
    const status = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0.5,
      cursorInsideMap: true,
      idle: false,
    });
    expect(status.active).toBe("cursor");
  });

  it("live dominates over time (top of wall)", () => {
    const statusTop = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0,
      cursorInsideMap: false,
      idle: false,
    });
    expect(statusTop.active).toBe("time");

    const statusMid = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0.01,
      cursorInsideMap: false,
      idle: false,
    });
    expect(statusMid.active).toBe("live");
  });
});
