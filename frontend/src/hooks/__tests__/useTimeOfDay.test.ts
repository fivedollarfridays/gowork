import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTimeOfDay } from "../useTimeOfDay";

function setNow(year: number, month: number, day: number, hour: number, minute = 0): void {
  vi.setSystemTime(new Date(year, month, day, hour, minute, 0, 0));
}

describe("useTimeOfDay (T1.24)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("returns phase=morning at 06:00 local time", () => {
    setNow(2026, 4, 27, 6);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.phase).toBe("morning");
  });

  it("returns phase=day at 14:00 local time", () => {
    setNow(2026, 4, 27, 14);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.phase).toBe("day");
    expect(result.current.sunPosition).toBeGreaterThan(0);
    expect(result.current.sunPosition).toBeLessThanOrEqual(1);
    expect(result.current.accentShift).toBe("cyan");
  });

  it("returns phase=evening at 18:30 local time", () => {
    setNow(2026, 4, 27, 18, 30);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.phase).toBe("evening");
    expect(result.current.accentShift).toBe("amber");
  });

  it("returns phase=night at 21:00 local time", () => {
    setNow(2026, 4, 27, 21);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.phase).toBe("night");
    expect(result.current.accentShift).toBe("navy");
  });

  it("re-renders to new phase when minute interval fires", () => {
    setNow(2026, 4, 27, 16, 59);
    const { result } = renderHook(() => useTimeOfDay());
    expect(result.current.phase).toBe("day");
    act(() => {
      setNow(2026, 4, 27, 17, 0);
      vi.advanceTimersByTime(60_000);
    });
    expect(result.current.phase).toBe("evening");
  });

  it("clears the interval on unmount (no leak)", () => {
    const clearSpy = vi.spyOn(global, "clearInterval");
    setNow(2026, 4, 27, 12);
    const { unmount } = renderHook(() => useTimeOfDay());
    unmount();
    expect(clearSpy).toHaveBeenCalled();
  });

  it("accepts a latitude parameter for sun-position calculation", () => {
    setNow(2026, 4, 27, 12);
    const fortWorth = renderHook(() => useTimeOfDay(32.7555));
    const montgomery = renderHook(() => useTimeOfDay(32.3792));
    expect(fortWorth.result.current.sunPosition).toBeCloseTo(
      montgomery.result.current.sunPosition,
      1,
    );
  });

  it("returns sunPosition=0 at midnight and sunPosition≈1 at solar noon", () => {
    setNow(2026, 4, 27, 0);
    const midnight = renderHook(() => useTimeOfDay());
    expect(midnight.result.current.sunPosition).toBeLessThan(0.05);

    setNow(2026, 4, 27, 12);
    const noon = renderHook(() => useTimeOfDay());
    expect(noon.result.current.sunPosition).toBeGreaterThan(0.9);
  });
});
