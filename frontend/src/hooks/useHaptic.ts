"use client";

import { useReducedMotion } from "framer-motion";
import { useCallback } from "react";

export function useHaptic() {
  const prefersReduced = useReducedMotion();

  const vibrate = useCallback(
    (pattern: number | number[]) => {
      if (prefersReduced) return;
      try {
        navigator?.vibrate?.(pattern);
      } catch {
        // vibrate not supported
      }
    },
    [prefersReduced],
  );

  return {
    tap: useCallback(() => vibrate(10), [vibrate]),
    success: useCallback(() => vibrate([10, 50, 10]), [vibrate]),
    error: useCallback(() => vibrate(30), [vibrate]),
  };
}
