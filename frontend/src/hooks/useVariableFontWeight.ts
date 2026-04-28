"use client";

import { useMemo } from "react";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

const WEIGHT_MIN = 700;
const WEIGHT_MAX = 900;
const OPSZ_MIN = 14;
const OPSZ_MAX = 32;
const REDUCED_MOTION_LOCK_WEIGHT = 800;
const REDUCED_MOTION_LOCK_OPSZ = 23;

function clamp01(progress: number): number {
  if (progress < 0) return 0;
  if (progress > 1) return 1;
  return progress;
}

/**
 * Interpolates Inter Variable's `wght` (700–900) and `opsz` (14–32) axes
 * along a 0..1 progress, returning a string suitable for CSS
 * `font-variation-settings`.
 *
 * Reduced-motion: locks at `wght 800, opsz 23` (the midpoint) so the
 * headline never animates its weight. Backlog T1.28 spec.
 *
 * @param progress 0..1; values outside the range are clamped.
 */
export function useVariableFontWeight(progress: number): string {
  const reduced = usePrefersReducedMotion();
  return useMemo(() => {
    if (reduced) {
      return `"wght" ${REDUCED_MOTION_LOCK_WEIGHT}, "opsz" ${REDUCED_MOTION_LOCK_OPSZ}`;
    }
    const p = clamp01(progress);
    const weight = Math.round(WEIGHT_MIN + (WEIGHT_MAX - WEIGHT_MIN) * p);
    const opsz = Math.round(OPSZ_MIN + (OPSZ_MAX - OPSZ_MIN) * p);
    return `"wght" ${weight}, "opsz" ${opsz}`;
  }, [progress, reduced]);
}
