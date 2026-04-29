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
 *
 * Driver A owns the canonical implementation.
 */

import { useEffect, useState } from "react";

export type ScrollDirection = "up" | "down" | "idle";

export interface UseScrollDirectionOptions {
  /** Threshold below which direction stays "idle" (default 80px). */
  threshold?: number;
}

export function useScrollDirection(
  _opts: UseScrollDirectionOptions = {},
): ScrollDirection {
  const [direction] = useState<ScrollDirection>("idle");

  useEffect(() => {
    // SCAFFOLD — Driver A fills.
    return undefined;
  }, []);

  return direction;
}
