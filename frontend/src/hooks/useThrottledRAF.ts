"use client";

import { useCallback, useEffect, useRef } from "react";

/**
 * Spotlight invention #2 (W4 Driver A) — useThrottledRAF.
 *
 * Generic requestAnimationFrame-throttled wrapper for high-frequency
 * event callbacks (mousemove, scroll, pointermove, resize). Multiple
 * synchronous invocations within the same frame coalesce into one
 * rAF-scheduled callback that fires with the LATEST argument value.
 *
 * Re-used today by:
 *   - W4 cursor flashlight on the Mapbox canvas
 *   - W4 hero variable-font scroll (eventually — when the hook moves
 *     off the W1 scroll-progress source which already throttles)
 *
 * Future re-use:
 *   - any chapter that hooks pointermove for parallax
 *   - W5 press kit page scroll-position telemetry
 *
 * Cleans up the pending rAF on unmount so the callback never fires
 * against an unmounted component (silently no-ops if unmount happens
 * mid-frame, since `cancelAnimationFrame` aborts the pending tick).
 *
 * @template T Argument type passed through the throttled callback.
 */
export function useThrottledRAF<T>(callback: (value: T) => void): (value: T) => void {
  const rafIdRef = useRef<number | null>(null);
  const pendingRef = useRef<T | null>(null);
  const callbackRef = useRef<(value: T) => void>(callback);

  // Keep latest callback reference without re-scheduling rAFs.
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    return () => {
      if (rafIdRef.current !== null && typeof window !== "undefined") {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, []);

  return useCallback((value: T) => {
    pendingRef.current = value;
    if (rafIdRef.current !== null) return;
    if (typeof window === "undefined") {
      callbackRef.current(value);
      return;
    }
    rafIdRef.current = window.requestAnimationFrame(() => {
      rafIdRef.current = null;
      const v = pendingRef.current;
      pendingRef.current = null;
      if (v !== null) callbackRef.current(v as T);
    });
  }, []);
}
