"use client";

import { useEffect, useRef, useState } from "react";

export interface ScrollVelocityState {
  /** Magnitude of recent scroll, in pixels per millisecond. */
  velocity: number;
  /** `true` when velocity exceeds the configured threshold. */
  isFast: boolean;
}

const DEFAULT_THRESHOLD_PX_PER_MS = 3;

/**
 * Tracks scroll velocity, sampled via `requestAnimationFrame`.
 *
 * Returns `{ velocity, isFast }` where `velocity` is the magnitude of
 * `Δ scrollY / Δ ms`. `isFast` flips on when velocity exceeds the
 * threshold (default 3 px/ms). Used by W4's motion-blur-on-fast-scroll
 * life-layer.
 *
 * SSR-safe: returns `{ velocity: 0, isFast: false }` on the server,
 * cancels rAF on unmount.
 *
 * @param threshold px-per-ms threshold for `isFast`. Default 3.
 */
export function useScrollVelocity(threshold: number = DEFAULT_THRESHOLD_PX_PER_MS): ScrollVelocityState {
  const [state, setState] = useState<ScrollVelocityState>({ velocity: 0, isFast: false });
  const lastRef = useRef<{ y: number; t: number } | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sample = () => {
      const t = performance.now();
      const y = window.scrollY ?? 0;
      const last = lastRef.current;
      if (last) {
        const dt = Math.max(1, t - last.t);
        const velocity = Math.abs(y - last.y) / dt;
        setState((prev) => {
          const next: ScrollVelocityState = { velocity, isFast: velocity > threshold };
          if (prev.velocity === next.velocity && prev.isFast === next.isFast) return prev;
          return next;
        });
      }
      lastRef.current = { y, t };
      rafRef.current = window.requestAnimationFrame(sample);
    };

    rafRef.current = window.requestAnimationFrame(sample);
    return () => {
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [threshold]);

  return state;
}
