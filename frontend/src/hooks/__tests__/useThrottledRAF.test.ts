import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useThrottledRAF } from "../useThrottledRAF";

describe("useThrottledRAF (Spotlight #2)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns a callback function", () => {
    const fn = vi.fn();
    const { result } = renderHook(() => useThrottledRAF(fn));
    expect(typeof result.current).toBe("function");
  });

  it("invokes the underlying callback on the next animation frame", () => {
    const fn = vi.fn();
    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation((cb) => {
        cb(0);
        return 1;
      });
    const { result } = renderHook(() => useThrottledRAF(fn));
    act(() => {
      result.current(42);
    });
    expect(fn).toHaveBeenCalledWith(42);
    rafSpy.mockRestore();
  });

  it("coalesces multiple sync invocations into a single rAF callback", () => {
    const fn = vi.fn();
    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation(() => 1);
    const { result } = renderHook(() => useThrottledRAF(fn));
    act(() => {
      result.current(1);
      result.current(2);
      result.current(3);
    });
    // Only one rAF scheduled — three sync calls collapsed into one.
    expect(rafSpy).toHaveBeenCalledTimes(1);
    rafSpy.mockRestore();
  });

  it("invokes the callback with the LATEST argument value when multiple calls collapse", () => {
    const fn = vi.fn();
    let storedCb: ((t: number) => void) | null = null;
    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation((cb) => {
        storedCb = cb;
        return 1;
      });
    const { result } = renderHook(() => useThrottledRAF(fn));
    act(() => {
      result.current("a");
      result.current("b");
      result.current("c");
    });
    act(() => {
      storedCb?.(0);
    });
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn).toHaveBeenCalledWith("c");
    rafSpy.mockRestore();
  });

  it("cancels the pending rAF on unmount", () => {
    const fn = vi.fn();
    const cancelSpy = vi.spyOn(window, "cancelAnimationFrame");
    const rafSpy = vi
      .spyOn(window, "requestAnimationFrame")
      .mockImplementation(() => 99);
    const { result, unmount } = renderHook(() => useThrottledRAF(fn));
    act(() => {
      result.current("x");
    });
    unmount();
    expect(cancelSpy).toHaveBeenCalledWith(99);
    rafSpy.mockRestore();
    cancelSpy.mockRestore();
  });
});
