import { describe, it, expect, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMemoryProfiler } from "../useMemoryProfiler";

afterEach(() => {
  delete (performance as unknown as { memory?: unknown }).memory;
});

describe("useMemoryProfiler (T1.128)", () => {
  it("returns 0/0 when performance.memory is unavailable", () => {
    delete (performance as unknown as { memory?: unknown }).memory;
    const { result } = renderHook(() => useMemoryProfiler(0));
    expect(result.current.usedMb).toBe(0);
    expect(result.current.peakMb).toBe(0);
  });

  it("returns the live used heap when present (single sample)", () => {
    Object.defineProperty(performance, "memory", {
      value: { usedJSHeapSize: 30 * 1024 * 1024 },
      configurable: true,
    });
    const { result } = renderHook(() => useMemoryProfiler(0));
    expect(result.current.usedMb).toBeGreaterThanOrEqual(30);
  });

  it("tracks peak across samples", () => {
    Object.defineProperty(performance, "memory", {
      value: { usedJSHeapSize: 20 * 1024 * 1024 },
      configurable: true,
    });
    const { result, rerender } = renderHook(
      ({ stamp }: { stamp: number }) => useMemoryProfiler(0, stamp),
      { initialProps: { stamp: 0 } },
    );
    expect(result.current.peakMb).toBeGreaterThanOrEqual(20);

    Object.defineProperty(performance, "memory", {
      value: { usedJSHeapSize: 50 * 1024 * 1024 },
      configurable: true,
    });
    act(() => {
      rerender({ stamp: 1 });
    });
    expect(result.current.peakMb).toBeGreaterThanOrEqual(50);

    Object.defineProperty(performance, "memory", {
      value: { usedJSHeapSize: 10 * 1024 * 1024 },
      configurable: true,
    });
    act(() => {
      rerender({ stamp: 2 });
    });
    expect(result.current.peakMb).toBeGreaterThanOrEqual(50); // peak retained
  });
});
