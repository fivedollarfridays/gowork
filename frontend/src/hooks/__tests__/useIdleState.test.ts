import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIdleState } from "../useIdleState";

describe("useIdleState (T1.31)", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("starts as not-idle (false)", () => {
    const { result } = renderHook(() => useIdleState());
    expect(result.current).toBe(false);
  });

  it("flips to true after default 30s of no input", () => {
    const { result } = renderHook(() => useIdleState());
    act(() => {
      vi.advanceTimersByTime(30_000);
    });
    expect(result.current).toBe(true);
  });

  it("respects a custom idle duration", () => {
    const { result } = renderHook(() => useIdleState(1000));
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(true);
  });

  it("resets when pointermove fires", () => {
    const { result } = renderHook(() => useIdleState(500));
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe(true);

    act(() => {
      window.dispatchEvent(new PointerEvent("pointermove"));
    });
    expect(result.current).toBe(false);
  });

  it("resets when keydown fires", () => {
    const { result } = renderHook(() => useIdleState(500));
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(result.current).toBe(true);
    act(() => {
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
    });
    expect(result.current).toBe(false);
  });

  it("removes all 4 listeners on unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const { unmount } = renderHook(() => useIdleState());
    unmount();
    const types = new Set(removeSpy.mock.calls.map((c) => c[0]));
    expect(types.has("pointermove")).toBe(true);
    expect(types.has("keydown")).toBe(true);
    expect(types.has("wheel")).toBe(true);
    expect(types.has("touchstart")).toBe(true);
  });
});
