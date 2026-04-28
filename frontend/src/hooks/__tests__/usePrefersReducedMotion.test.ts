import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePrefersReducedMotion } from "../usePrefersReducedMotion";

type Listener = (event: MediaQueryListEvent) => void;

interface MockMediaQueryList {
  matches: boolean;
  media: string;
  addEventListener: (type: string, listener: Listener) => void;
  removeEventListener: (type: string, listener: Listener) => void;
  dispatchEvent: (event: MediaQueryListEvent) => void;
  onchange: null;
  addListener: (listener: Listener) => void; // legacy
  removeListener: (listener: Listener) => void; // legacy
}

function makeMockMediaQueryList(initialMatches: boolean): MockMediaQueryList {
  const listeners = new Set<Listener>();
  return {
    matches: initialMatches,
    media: "(prefers-reduced-motion: reduce)",
    onchange: null,
    addEventListener: (_type, listener) => listeners.add(listener),
    removeEventListener: (_type, listener) => listeners.delete(listener),
    dispatchEvent: (event) => {
      listeners.forEach((l) => l(event));
      return true;
    },
    addListener: (listener) => listeners.add(listener),
    removeListener: (listener) => listeners.delete(listener),
  };
}

describe("usePrefersReducedMotion (T1.30)", () => {
  let mql: MockMediaQueryList;

  beforeEach(() => {
    mql = makeMockMediaQueryList(false);
    window.matchMedia = vi.fn().mockImplementation((query: string) => {
      mql.media = query;
      return mql;
    }) as typeof window.matchMedia;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns false when matchMedia reports no preference", () => {
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);
  });

  it("returns true when matchMedia reports reduce", () => {
    mql.matches = true;
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(true);
  });

  it("re-renders when the user toggles preference", () => {
    const { result } = renderHook(() => usePrefersReducedMotion());
    expect(result.current).toBe(false);
    act(() => {
      mql.matches = true;
      mql.dispatchEvent({ matches: true } as MediaQueryListEvent);
    });
    expect(result.current).toBe(true);
  });

  it("removes its listener on unmount (no leak)", () => {
    const removeSpy = vi.spyOn(mql, "removeEventListener");
    const { unmount } = renderHook(() => usePrefersReducedMotion());
    unmount();
    expect(removeSpy).toHaveBeenCalledWith("change", expect.any(Function));
  });

  it("uses the (prefers-reduced-motion: reduce) media query", () => {
    renderHook(() => usePrefersReducedMotion());
    expect(window.matchMedia).toHaveBeenCalledWith("(prefers-reduced-motion: reduce)");
  });
});
