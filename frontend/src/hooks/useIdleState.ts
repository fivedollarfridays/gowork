"use client";

import { useEffect, useRef, useState } from "react";

const DEFAULT_IDLE_MS = 30_000;
const ACTIVITY_EVENTS = ["pointermove", "keydown", "wheel", "touchstart"] as const;

/**
 * Returns `true` after `idleMs` of no user input.
 *
 * Watched events: pointermove, keydown, wheel, touchstart.
 * Resets the timer on any of them. SSR-safe: returns `false` on the
 * server. Cleanup removes all 4 listeners + the timeout on unmount.
 *
 * Used by W4's idle-state visual cues (path-line gentle pulse) and
 * by the AmbientNarration system that nudges abandoned readers.
 *
 * @param idleMs Inactivity timeout. Default 30 000 ms.
 */
export function useIdleState(idleMs: number = DEFAULT_IDLE_MS): boolean {
  const [idle, setIdle] = useState<boolean>(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const reset = () => {
      setIdle(false);
      if (timerRef.current !== null) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => setIdle(true), idleMs);
    };

    reset();
    ACTIVITY_EVENTS.forEach((event) => {
      window.addEventListener(event, reset, { passive: true });
    });

    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        window.removeEventListener(event, reset);
      });
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [idleMs]);

  return idle;
}
