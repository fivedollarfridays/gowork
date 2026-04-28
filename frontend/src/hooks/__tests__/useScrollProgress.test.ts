import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

const mockScrollYProgress = { current: 0, _listeners: new Set<(v: number) => void>() };
const stableScrollYProgress = {
  get: () => mockScrollYProgress.current,
  on: (event: string, cb: (v: number) => void) => {
    if (event === "change") {
      mockScrollYProgress._listeners.add(cb);
    }
    return () => mockScrollYProgress._listeners.delete(cb);
  },
};
const stableUseScrollResult = { scrollYProgress: stableScrollYProgress };

vi.mock("framer-motion", () => ({
  useScroll: () => stableUseScrollResult,
}));

import { useScrollProgress } from "../useScrollProgress";

function setProgress(v: number): void {
  mockScrollYProgress.current = v;
  mockScrollYProgress._listeners.forEach((l) => l(v));
}

describe("useScrollProgress (T1.27)", () => {
  beforeEach(() => {
    mockScrollYProgress.current = 0;
    mockScrollYProgress._listeners.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns chapter=0 progress=0 at scrollY top", () => {
    const { result } = renderHook(() => useScrollProgress());
    expect(result.current.chapter).toBe(0);
    expect(result.current.progressInChapter).toBeCloseTo(0, 5);
    expect(result.current.totalProgress).toBeCloseTo(0, 5);
  });

  it("returns chapter≈4–5 at midpoint with 10 chapters", () => {
    const { result } = renderHook(() => useScrollProgress(10));
    act(() => setProgress(0.5));
    expect(result.current.chapter).toBeGreaterThanOrEqual(4);
    expect(result.current.chapter).toBeLessThanOrEqual(5);
    expect(result.current.totalProgress).toBeCloseTo(0.5, 2);
  });

  it("returns chapter=9 progress≈1 at scroll bottom (10 chapters)", () => {
    const { result } = renderHook(() => useScrollProgress(10));
    act(() => setProgress(1));
    expect(result.current.chapter).toBe(9);
    expect(result.current.progressInChapter).toBeCloseTo(1, 2);
    expect(result.current.totalProgress).toBeCloseTo(1, 5);
  });

  it("returns chapter=2 at exactly progress=0.25 with 10 chapters", () => {
    const { result } = renderHook(() => useScrollProgress(10));
    act(() => setProgress(0.25));
    expect(result.current.chapter).toBe(2);
    expect(result.current.progressInChapter).toBeCloseTo(0.5, 1);
  });

  it("supports custom chapterCount", () => {
    const { result } = renderHook(() => useScrollProgress(5));
    act(() => setProgress(0.4));
    expect(result.current.chapter).toBe(2);
  });

  it("unsubscribes from scroll listener on unmount", () => {
    const { unmount } = renderHook(() => useScrollProgress());
    expect(mockScrollYProgress._listeners.size).toBe(1);
    unmount();
    expect(mockScrollYProgress._listeners.size).toBe(0);
  });
});
