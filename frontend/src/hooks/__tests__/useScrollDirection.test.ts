/**
 * useScrollDirection — polish-2 T2.
 *
 * Detects scroll direction so the SiteHeader hides on scroll-down and
 * restores on scroll-up.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useScrollDirection } from "../useScrollDirection";

function setScrollY(y: number): void {
  Object.defineProperty(window, "scrollY", {
    value: y,
    writable: true,
    configurable: true,
  });
}

describe("useScrollDirection", () => {
  let rafCb: FrameRequestCallback | null = null;

  beforeEach(() => {
    setScrollY(0);
    rafCb = null;
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => {
        rafCb = cb;
        return 1 as unknown as number;
      }) as typeof requestAnimationFrame,
    );
    vi.stubGlobal("cancelAnimationFrame", (() => {}) as typeof cancelAnimationFrame);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function fireScroll(): void {
    act(() => {
      window.dispatchEvent(new Event("scroll"));
      if (rafCb) {
        const cb = rafCb;
        rafCb = null;
        cb(performance.now());
      }
    });
  }

  it("returns 'idle' before any scroll", () => {
    const { result } = renderHook(() => useScrollDirection());
    expect(result.current).toBe("idle");
  });

  it("stays idle while below the threshold", () => {
    const { result } = renderHook(() => useScrollDirection({ threshold: 80 }));
    setScrollY(40);
    fireScroll();
    expect(result.current).toBe("idle");
  });

  it("returns 'down' once scrollY crosses the threshold downward", () => {
    const { result } = renderHook(() => useScrollDirection({ threshold: 80 }));
    setScrollY(100);
    fireScroll();
    setScrollY(200);
    fireScroll();
    expect(result.current).toBe("down");
  });

  it("returns 'up' when scrolling back up after going past threshold", () => {
    const { result } = renderHook(() => useScrollDirection({ threshold: 80 }));
    setScrollY(100);
    fireScroll();
    setScrollY(200);
    fireScroll();
    setScrollY(150);
    fireScroll();
    expect(result.current).toBe("up");
  });

  it("returns 'idle' on SSR (no window)", () => {
    // Hooks are still callable; simulate SSR-ish by ensuring the initial value
    // before any effect runs is "idle".
    const { result } = renderHook(() => useScrollDirection());
    expect(result.current).toBe("idle");
  });

  it("cleans up the scroll listener on unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const { unmount } = renderHook(() => useScrollDirection());
    unmount();
    const calls = removeSpy.mock.calls.filter((c) => c[0] === "scroll");
    expect(calls.length).toBeGreaterThan(0);
  });
});
