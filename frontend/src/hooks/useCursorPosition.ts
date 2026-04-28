"use client";

import { useEffect, useRef, useState } from "react";

export interface CursorPosition {
  /** Normalized 0..1 along the viewport width. */
  x: number;
  /** Normalized 0..1 along the viewport height. */
  y: number;
  /** Velocity along x axis, signed, in normalized units per millisecond. */
  vx: number;
  /** Velocity along y axis, signed, in normalized units per millisecond. */
  vy: number;
}

const CENTER: CursorPosition = { x: 0.5, y: 0.5, vx: 0, vy: 0 };

function isTouchDevice(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof navigator !== "undefined" && (navigator.maxTouchPoints ?? 0) > 0) {
    return true;
  }
  return false;
}

function clamp01(value: number): number {
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

/**
 * Tracks the cursor's normalized position + signed velocity across the
 * viewport.
 *
 * Returns `{ x, y, vx, vy }` where x/y are 0..1 (clamped) and vx/vy
 * are normalized units per millisecond, updated from rAF-throttled
 * `pointermove` deltas.
 *
 * SSR-safe: returns the center placeholder when `window` is undefined.
 * Touch devices: returns the center static (no `pointermove`) — used
 * by `CursorTrail` (T1.60) and `CursorFlashlight` (T1.61) to render
 * the no-op variant.
 *
 * Cleanup discipline: removes the `pointermove` listener AND cancels
 * the pending rAF frame on unmount. Verified by the cleanup test.
 */
export function useCursorPosition(): CursorPosition {
  const [pos, setPos] = useState<CursorPosition>(CENTER);
  const rafIdRef = useRef<number | null>(null);
  const pendingRef = useRef<{ x: number; y: number; t: number } | null>(null);
  const lastRef = useRef<{ x: number; y: number; t: number } | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || isTouchDevice()) return;

    const flush = () => {
      rafIdRef.current = null;
      const next = pendingRef.current;
      if (!next) return;
      const last = lastRef.current;
      const dt = last ? Math.max(1, next.t - last.t) : 1;
      const vx = last ? (next.x - last.x) / dt : 0;
      const vy = last ? (next.y - last.y) / dt : 0;
      lastRef.current = next;
      setPos({ x: next.x, y: next.y, vx, vy });
    };

    const handler = (event: PointerEvent) => {
      const w = window.innerWidth || 1;
      const h = window.innerHeight || 1;
      pendingRef.current = {
        x: clamp01(event.clientX / w),
        y: clamp01(event.clientY / h),
        t: performance.now(),
      };
      if (rafIdRef.current === null) {
        rafIdRef.current = window.requestAnimationFrame(flush);
      }
    };

    window.addEventListener("pointermove", handler, { passive: true });
    return () => {
      window.removeEventListener("pointermove", handler);
      if (rafIdRef.current !== null) {
        window.cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, []);

  return pos;
}
