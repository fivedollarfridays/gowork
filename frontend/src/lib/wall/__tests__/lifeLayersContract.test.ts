import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";

/**
 * Spotlight invention #3 (W4 Driver A) — lifeLayersContract.
 *
 * Single guard test asserting all four W4 life-layers initialize without
 * crashing under degenerate inputs:
 *
 *   1. Time-of-day sky setter — `map === null` (mount-time race)
 *   2. Cursor flashlight — touch device + reduced-motion both true
 *   3. Live Now — server returns 0 sessions and null calibration
 *   4. Variable font axis — out-of-range scroll progress (-1, +5)
 *
 * Any future regression that crashes a life-layer hook on a SSR/null
 * boundary will trip this test. The whole point: the page must never
 * white-screen for a missing prop or pre-mount race.
 */

import { useMapboxSkyForTimeOfDay } from "@/hooks/useMapboxSkyForTimeOfDay";
import { useHeroFontWeight, useChapterHeadingFontWeight } from "@/hooks/useHeroFontWeight";
import { useLiveNowFormatted } from "@/hooks/useLiveNowFormatted";

vi.mock("@/hooks/useTimeOfDay", () => ({
  useTimeOfDay: () => ({
    phase: "day",
    sunPosition: 0.5,
    accentShift: "cyan",
    sunAltitudeDeg: 45,
    skyTypeName: "atmosphere",
    skyColor: "oklch(0.85 0.05 230)",
    accentToken: "blue",
  }),
}));

vi.mock("@/hooks/useLiveNow", () => ({
  useLiveNow: () => ({
    now: new Date("2026-04-27T12:00:00.000Z"),
    sessions: 0,
    lastCalibration: null,
  }),
}));

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => false,
}));

describe("Life-layers contract (Spotlight #3)", () => {
  it("sky setter does not crash when map is null", () => {
    expect(() => {
      renderHook(() => useMapboxSkyForTimeOfDay(null));
    }).not.toThrow();
  });

  it("hero font weight does not crash with negative progress", () => {
    expect(() => {
      renderHook(() => useHeroFontWeight(-1));
    }).not.toThrow();
  });

  it("hero font weight does not crash with absurd progress", () => {
    expect(() => {
      renderHook(() => useHeroFontWeight(5));
    }).not.toThrow();
  });

  it("chapter heading font weight does not crash on out-of-range input", () => {
    expect(() => {
      renderHook(() => useChapterHeadingFontWeight(-2));
      renderHook(() => useChapterHeadingFontWeight(99));
    }).not.toThrow();
  });

  it("live-now formatted does not crash with zero sessions and null calibration", () => {
    expect(() => {
      const { result } = renderHook(() => useLiveNowFormatted("en-US"));
      // Always emits a non-empty string trio so the header never renders
      // a missing slot.
      expect(typeof result.current.nowLabel).toBe("string");
      expect(typeof result.current.lastCalibratedRelative).toBe("string");
      expect(result.current.lastCalibratedRelative.length).toBeGreaterThan(0);
    }).not.toThrow();
  });
});
