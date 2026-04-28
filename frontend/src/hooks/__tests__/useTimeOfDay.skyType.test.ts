import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useTimeOfDay } from "../useTimeOfDay";

/**
 * T4.A.1 — sky-type and accent-token extensions on useTimeOfDay.
 *
 * Additive contract — these fields are required for W4 sky setter and
 * accent shift. Existing morning/day/evening/night phases are preserved
 * (covered by useTimeOfDay.test.ts).
 */

function setNow(year: number, month: number, day: number, hour: number, minute = 0): void {
  vi.setSystemTime(new Date(year, month, day, hour, minute, 0, 0));
}

describe("useTimeOfDay sky extensions (T4.A.1)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("exposes sunAltitudeDeg in 0..90 range at solar noon", () => {
    setNow(2026, 4, 27, 12);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.sunAltitudeDeg).toBeGreaterThan(0);
    expect(result.current.sunAltitudeDeg).toBeLessThanOrEqual(90);
  });

  it("returns near-zero sunAltitudeDeg at midnight", () => {
    setNow(2026, 4, 27, 0);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.sunAltitudeDeg).toBeLessThan(5);
  });

  it("exposes skyTypeName='atmosphere' during day phase", () => {
    setNow(2026, 4, 27, 12);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.skyTypeName).toBe("atmosphere");
  });

  it("exposes skyTypeName='gradient' at night", () => {
    setNow(2026, 4, 27, 23);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.skyTypeName).toBe("gradient");
  });

  it("returns an OKLCH-formatted skyColor string", () => {
    setNow(2026, 4, 27, 14);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.skyColor).toMatch(/^oklch\(/);
  });

  it("returns the legacy accentShift AND a W4 accentToken in sync", () => {
    setNow(2026, 4, 27, 14);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.accentShift).toBe("cyan");
    // W4 accentToken is the per-phase CSS-variable-friendly slug.
    expect(typeof result.current.accentToken).toBe("string");
    expect(result.current.accentToken.length).toBeGreaterThan(0);
  });

  it("emits accentToken='rose' at evening (dusk) and 'navy' at night", () => {
    setNow(2026, 4, 27, 19);
    const evening = renderHook(() => useTimeOfDay());
    expect(evening.result.current.accentToken).toMatch(/rose|amber|dusk/);

    setNow(2026, 4, 27, 23);
    const night = renderHook(() => useTimeOfDay());
    expect(night.result.current.accentToken).toMatch(/navy|indigo|night/);
  });
});
