"use client";

/**
 * useScrollDirection — polish-2 T2.
 *
 * Detect scroll direction so the SiteHeader can hide on scroll-down and
 * restore on scroll-up (Linear / Vercel / Mercury signature pattern).
 *
 * Contract:
 *   const direction = useScrollDirection({ threshold: 80 });
 *   // direction: "up" | "down" | "idle"
 *
 * Behavior:
 *   - Returns "idle" until the user has scrolled past `threshold` px.
 *   - Returns "down" when scrollY is increasing past the last sample.
 *   - Returns "up" when scrollY is decreasing past the last sample.
 *   - Coalesces sub-frame updates via rAF (no thrash on inertial scroll).
 *   - SSR-safe: returns "idle" when `window` is undefined.
 */

import { useEffect, useRef, useState } from "react";

export type ScrollDirection = "up" | "down" | "idle";

export interface UseScrollDirectionOptions {
  /** Threshold below which direction stays "idle" (default 80px). */
  threshold?: number;
  /** Minimum delta in px between samples that registers as a direction change. */
  minDelta?: number;
}

const DEFAULT_THRESHOLD = 80;
const DEFAULT_MIN_DELTA = 4;

export function useScrollDirection(
  opts: UseScrollDirectionOptions = {},
): ScrollDirection {
  const { threshold = DEFAULT_THRESHOLD, minDelta = DEFAULT_MIN_DELTA } = opts;
  const [direction, setDirection] = useState<ScrollDirection>("idle");
  const lastYRef = useRef<number>(0);
  const tickingRef = useRef<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const sample = () => {
      tickingRef.current = false;
      const y = window.scrollY ?? 0;
      const last = lastYRef.current;
      if (y < threshold) {
        setDirection((prev) => (prev === "idle" ? prev : "idle"));
        lastYRef.current = y;
        return;
      }
      const delta = y - last;
      if (Math.abs(delta) < minDelta) {
        return;
      }
      const next: ScrollDirection = delta > 0 ? "down" : "up";
      setDirection((prev) => (prev === next ? prev : next));
      lastYRef.current = y;
    };

    const onScroll = () => {
      if (tickingRef.current) return;
      tickingRef.current = true;
      window.requestAnimationFrame(sample);
    };

    lastYRef.current = window.scrollY ?? 0;
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
    };
  }, [threshold, minDelta]);

  return direction;
}
