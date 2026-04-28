import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useScrollVelocity } from "../useScrollVelocity";

describe("useScrollVelocity (T1.29)", () => {
  let now = 0;
  let rafCb: FrameRequestCallback | null = null;

  beforeEach(() => {
    now = 1000;
    rafCb = null;
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => {
        rafCb = cb;
        return 1 as unknown as number;
      }) as typeof requestAnimationFrame,
    );
    vi.stubGlobal("cancelAnimationFrame", (() => {}) as typeof cancelAnimationFrame);
    vi.spyOn(performance, "now").mockImplementation(() => now);
    Object.defineProperty(window, "scrollY", { value: 0, writable: true, configurable: true });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  function tick(deltaMs: number, scrollY: number): void {
    now += deltaMs;
    Object.defineProperty(window, "scrollY", { value: scrollY, writable: true, configurable: true });
    act(() => {
      if (rafCb) {
        const cb = rafCb;
        rafCb = null;
        cb(now);
      }
    });
  }

  it("returns velocity 0 and isFast=false when stationary", () => {
    const { result } = renderHook(() => useScrollVelocity());
    expect(result.current.velocity).toBe(0);
    expect(result.current.isFast).toBe(false);
  });

  it("computes velocity ≈2 px/ms over a 100px scroll across 50ms", () => {
    const { result } = renderHook(() => useScrollVelocity());
    // First tick establishes the baseline (last = {y: 0, t}).
    tick(0, 0);
    // Second tick produces the delta against the baseline.
    tick(50, 100);
    expect(result.current.velocity).toBeGreaterThan(1.5);
    expect(result.current.velocity).toBeLessThan(2.5);
  });

  it("flags isFast=true when velocity exceeds default threshold (3 px/ms)", () => {
    const { result } = renderHook(() => useScrollVelocity());
    tick(0, 0);
    tick(50, 200);
    expect(result.current.velocity).toBeGreaterThan(3);
    expect(result.current.isFast).toBe(true);
  });

  it("respects a custom threshold parameter", () => {
    const { result } = renderHook(() => useScrollVelocity(1));
    tick(0, 0);
    tick(50, 100);
    expect(result.current.isFast).toBe(true);
  });

  it("cancels rAF on unmount (no leak)", () => {
    const cancelSpy = vi.fn();
    vi.stubGlobal("cancelAnimationFrame", cancelSpy as typeof cancelAnimationFrame);
    const { unmount } = renderHook(() => useScrollVelocity());
    unmount();
    expect(cancelSpy).toHaveBeenCalled();
  });
});
