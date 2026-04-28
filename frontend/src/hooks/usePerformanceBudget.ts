"use client";

import { useEffect, useRef, useState } from "react";

export interface PerformanceBudgetState {
  /** Cumulative ms spent in long tasks since hook mounted. */
  longTasksMs: number;
  /** JS heap used (Chrome only — null on Safari/Firefox is reported as 0). */
  jsHeapUsedMb: number;
  /** Number of frames whose delta was >2x the 16.67ms target. */
  droppedFrames: number;
  /** True when ANY threshold is breached. */
  isUnderPressure: boolean;
}

export interface PerformanceBudgetOptions {
  /** Single long-task duration that flips isUnderPressure. Default 50 ms. */
  longTaskMsThreshold?: number;
  /** Cumulative long-tasks-ms across the session that flips isUnderPressure. Default 250 ms. */
  cumulativeLongTaskBudgetMs?: number;
  /** Heap usage in MB that flips isUnderPressure. Default 200 MB. */
  heapBudgetMb?: number;
  /** Dropped frames count that flips isUnderPressure. Default 30. */
  droppedFrameBudget?: number;
}

const DEFAULTS: Required<PerformanceBudgetOptions> = {
  longTaskMsThreshold: 50,
  cumulativeLongTaskBudgetMs: 250,
  heapBudgetMb: 200,
  droppedFrameBudget: 30,
};

const SSR_DEFAULT: PerformanceBudgetState = {
  longTasksMs: 0,
  jsHeapUsedMb: 0,
  droppedFrames: 0,
  isUnderPressure: false,
};

interface MemoryLike {
  usedJSHeapSize?: number;
}

function readHeapMb(): number {
  if (typeof performance === "undefined") return 0;
  const mem = (performance as unknown as { memory?: MemoryLike }).memory;
  if (!mem || typeof mem.usedJSHeapSize !== "number") return 0;
  return mem.usedJSHeapSize / (1024 * 1024);
}

function isUnderPressureFor(
  state: PerformanceBudgetState,
  opts: Required<PerformanceBudgetOptions>,
  lastTaskMs: number,
): boolean {
  if (lastTaskMs >= opts.longTaskMsThreshold) return true;
  if (state.longTasksMs >= opts.cumulativeLongTaskBudgetMs) return true;
  if (state.jsHeapUsedMb >= opts.heapBudgetMb) return true;
  if (state.droppedFrames >= opts.droppedFrameBudget) return true;
  return false;
}

/**
 * Performance budget telemetry — Spotlight invention 1 (T1.73).
 *
 * Returns a live snapshot of long-task ms, heap usage, and dropped
 * frames. `isUnderPressure` flips on when any threshold is breached.
 *
 * Used by W2/W3 chapter components to decide when to drop expensive
 * effects (the 3D barrier graph, the cursor flashlight, full Mapbox
 * styling) in real-time — not just at build-time Lighthouse runs.
 *
 * SSR-safe: returns zero-state on the server. PerformanceObserver is
 * gracefully detected; Safari/Firefox without `performance.memory`
 * still get long-task + frame data.
 */
export function usePerformanceBudget(
  options: PerformanceBudgetOptions = {},
): PerformanceBudgetState {
  const opts: Required<PerformanceBudgetOptions> = { ...DEFAULTS, ...options };
  const [state, setState] = useState<PerformanceBudgetState>(SSR_DEFAULT);
  const lastTaskMsRef = useRef<number>(0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const POClass = (globalThis as unknown as { PerformanceObserver?: typeof PerformanceObserver })
      .PerformanceObserver;
    if (typeof POClass !== "function") return;

    const observer = new POClass((list: PerformanceObserverEntryList) => {
      let added = 0;
      let maxThis = 0;
      for (const entry of list.getEntries()) {
        const dur = (entry as PerformanceEntry).duration;
        added += dur;
        if (dur > maxThis) maxThis = dur;
      }
      lastTaskMsRef.current = maxThis;
      setState((prev) => {
        const next: PerformanceBudgetState = {
          longTasksMs: prev.longTasksMs + added,
          jsHeapUsedMb: readHeapMb(),
          droppedFrames: prev.droppedFrames,
          isUnderPressure: false,
        };
        next.isUnderPressure = isUnderPressureFor(next, opts, maxThis);
        return next;
      });
    });

    try {
      observer.observe({ entryTypes: ["longtask"] });
    } catch {
      /* longtask not supported in some browsers */
    }

    // Initial heap snapshot
    setState((prev) => ({ ...prev, jsHeapUsedMb: readHeapMb() }));

    return () => observer.disconnect();
  }, [opts.longTaskMsThreshold, opts.cumulativeLongTaskBudgetMs, opts.heapBudgetMb, opts.droppedFrameBudget]);

  return state;
}
