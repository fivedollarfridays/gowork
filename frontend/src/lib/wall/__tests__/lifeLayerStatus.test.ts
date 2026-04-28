/**
 * Spotlight invention #2 (W4 Driver D) — lifeLayerStatus.test.ts.
 *
 * `deriveLifeLayerStatus(input)` is a pure derivation: given the four
 * life-layer signals (time-of-day phase, scroll progress, cursor inside
 * map, idle-state flag), it returns an editorial-friendly status:
 *   { active: 'time' | 'cursor' | 'live' | 'idle', mood: '...' }
 *
 * Used by:
 *   - The press-kit OG card composer (Spotlight #1) — picks a hero copy
 *     line that matches the active layer.
 *   - The dev-overlay /dev/life-layers diagnostic page.
 *   - Future telemetry (record which layer was the dominant signal in
 *     a given session).
 *
 * Pure: no fetch, no DOM, no time. Just (input) → status.
 */

import { describe, it, expect } from "vitest";
import {
  deriveLifeLayerStatus,
  PHASE_TO_MOOD,
} from "../lifeLayerStatus";

describe("Spotlight #2 — deriveLifeLayerStatus pure derivation", () => {
  it("idle=true overrides everything → active='idle'", () => {
    const r = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0.5,
      cursorInsideMap: true,
      idle: true,
    });
    expect(r.active).toBe("idle");
  });

  it("cursor in map AND not idle AND scrolling → active='cursor'", () => {
    const r = deriveLifeLayerStatus({
      phase: "noon",
      globalProgress: 0.5,
      cursorInsideMap: true,
      idle: false,
    });
    expect(r.active).toBe("cursor");
  });

  it("not idle, not cursor-in-map, mid-scroll → active='live'", () => {
    const r = deriveLifeLayerStatus({
      phase: "afternoon",
      globalProgress: 0.5,
      cursorInsideMap: false,
      idle: false,
    });
    expect(r.active).toBe("live");
  });

  it("not idle, not cursor-in-map, at the top (progress=0) → active='time'", () => {
    const r = deriveLifeLayerStatus({
      phase: "dusk",
      globalProgress: 0,
      cursorInsideMap: false,
      idle: false,
    });
    expect(r.active).toBe("time");
  });

  it("returns a non-empty mood string for every phase", () => {
    const phases = ["dawn", "morning", "noon", "afternoon", "dusk", "night"] as const;
    for (const phase of phases) {
      const r = deriveLifeLayerStatus({
        phase,
        globalProgress: 0,
        cursorInsideMap: false,
        idle: false,
      });
      expect(typeof r.mood).toBe("string");
      expect(r.mood.length).toBeGreaterThan(0);
    }
  });

  it("PHASE_TO_MOOD covers all six W4 phases", () => {
    const keys = Object.keys(PHASE_TO_MOOD).sort();
    expect(keys).toEqual([
      "afternoon",
      "dawn",
      "dusk",
      "morning",
      "night",
      "noon",
    ]);
  });

  it("dawn mood mentions 'morning' or 'sun' or 'awake' — editorial check", () => {
    expect(PHASE_TO_MOOD.dawn.toLowerCase()).toMatch(
      /morning|sun|awake|dawn|amber|warm/,
    );
  });

  it("night mood mentions 'late' or 'still' or 'after' — editorial check", () => {
    expect(PHASE_TO_MOOD.night.toLowerCase()).toMatch(
      /night|late|still|after|deep/,
    );
  });

  it("globalProgress >= 1 (end of wall) returns active='live' if not idle/cursor", () => {
    const r = deriveLifeLayerStatus({
      phase: "dusk",
      globalProgress: 1,
      cursorInsideMap: false,
      idle: false,
    });
    expect(r.active).toBe("live");
  });
});
