"use client";

import { useEffect, useRef, useState } from "react";

const DEFAULT_INTERVAL_MS = 1000;
const DEV_ENABLED = process.env.NODE_ENV !== "production";

export interface MemoryProfile {
  /** Current `performance.memory.usedJSHeapSize` in MB. */
  usedMb: number;
  /** Highest used heap observed since hook mounted. */
  peakMb: number;
}

interface MemoryLike {
  usedJSHeapSize?: number;
}

function readUsedMb(): number {
  if (typeof performance === "undefined") return 0;
  const mem = (performance as unknown as { memory?: MemoryLike }).memory;
  if (!mem || typeof mem.usedJSHeapSize !== "number") return 0;
  return mem.usedJSHeapSize / (1024 * 1024);
}

/**
 * useMemoryProfiler (T1.128) — dev-only memory sampler.
 *
 * Samples `performance.memory.usedJSHeapSize` on mount + every
 * `intervalMs` (default 1s). Tracks current + session peak. Returns
 * zero-state when:
 *   - performance.memory is unavailable (Safari, Firefox)
 *   - NODE_ENV === 'production' (the hook is dev-only by intent)
 *
 * Optional `_stampForTests` parameter forces a re-sample synchronously
 * — the production code path uses the timer interval and ignores it.
 */
export function useMemoryProfiler(
  intervalMs: number = DEFAULT_INTERVAL_MS,
  _stampForTests?: number,
): MemoryProfile {
  const [profile, setProfile] = useState<MemoryProfile>({ usedMb: 0, peakMb: 0 });
  const peakRef = useRef<number>(0);

  useEffect(() => {
    if (!DEV_ENABLED) return;
    if (typeof window === "undefined") return;

    const sample = () => {
      const used = readUsedMb();
      if (used > peakRef.current) peakRef.current = used;
      setProfile({ usedMb: used, peakMb: peakRef.current });
    };

    sample();
    if (intervalMs <= 0) return;
    const id = setInterval(sample, intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, _stampForTests]);

  return profile;
}
