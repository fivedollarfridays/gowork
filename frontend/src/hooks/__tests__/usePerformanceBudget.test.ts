import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePerformanceBudget } from "../usePerformanceBudget";

interface FakeObserver {
  observe: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  fire: (entries: PerformanceEntryList) => void;
}

let observerInstances: FakeObserver[] = [];

class FakeOb {
  observe = vi.fn();
  disconnect = vi.fn();
  cb: PerformanceObserverCallback;
  constructor(cb: PerformanceObserverCallback) {
    this.cb = cb;
    observerInstances.push(this);
  }
  fire(entries: PerformanceEntryList): void {
    this.cb({ getEntries: () => entries } as PerformanceObserverEntryList, this as unknown as PerformanceObserver);
  }
  takeRecords(): PerformanceEntryList {
    return [];
  }
}

describe("usePerformanceBudget (T1.73)", () => {
  const origPerfObserver = globalThis.PerformanceObserver;

  beforeEach(() => {
    observerInstances = [];
    (globalThis as unknown as { PerformanceObserver: unknown }).PerformanceObserver = FakeOb;
  });

  afterEach(() => {
    (globalThis as unknown as { PerformanceObserver: unknown }).PerformanceObserver = origPerfObserver;
    vi.restoreAllMocks();
  });

  it("starts with all zeros and isUnderPressure=false", () => {
    const { result } = renderHook(() => usePerformanceBudget());
    expect(result.current.longTasksMs).toBe(0);
    expect(result.current.droppedFrames).toBe(0);
    expect(result.current.isUnderPressure).toBe(false);
  });

  it("accumulates longTasksMs from PerformanceObserver entries", () => {
    const { result } = renderHook(() => usePerformanceBudget());
    act(() => {
      observerInstances[0]?.fire([
        { duration: 80 } as PerformanceEntry,
        { duration: 60 } as PerformanceEntry,
      ]);
    });
    expect(result.current.longTasksMs).toBeGreaterThanOrEqual(140);
  });

  it("flips isUnderPressure when a long-task entry exceeds threshold", () => {
    const { result } = renderHook(() => usePerformanceBudget({ longTaskMsThreshold: 100 }));
    act(() => {
      observerInstances[0]?.fire([{ duration: 200 } as PerformanceEntry]);
    });
    expect(result.current.isUnderPressure).toBe(true);
  });

  it("populates jsHeapUsedMb when performance.memory exists", () => {
    Object.defineProperty(performance, "memory", {
      value: { usedJSHeapSize: 50 * 1024 * 1024 },
      configurable: true,
    });
    const { result } = renderHook(() => usePerformanceBudget());
    expect(result.current.jsHeapUsedMb).toBeGreaterThanOrEqual(50);
    delete (performance as unknown as { memory?: unknown }).memory;
  });

  it("disconnects PerformanceObserver on unmount (no leak)", () => {
    const { unmount } = renderHook(() => usePerformanceBudget());
    const ob = observerInstances[0];
    unmount();
    expect(ob?.disconnect).toHaveBeenCalled();
  });

  it("degrades gracefully when PerformanceObserver is undefined", () => {
    (globalThis as unknown as { PerformanceObserver: unknown }).PerformanceObserver = undefined;
    const { result } = renderHook(() => usePerformanceBudget());
    expect(result.current.longTasksMs).toBe(0);
    expect(result.current.isUnderPressure).toBe(false);
  });
});
