"use client";

import { useEffect, useState } from "react";
import { useCursorPosition } from "@/hooks/useCursorPosition";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

const DOT_DIAMETER_PX = 8;

function detectTouch(): boolean {
  if (typeof window === "undefined") return false;
  // Require BOTH signals — `ontouchstart in window` alone is true on
  // jsdom + some hybrid laptops without an actual touchscreen.
  if (typeof navigator !== "undefined" && (navigator.maxTouchPoints ?? 0) > 0) {
    return true;
  }
  return false;
}

/**
 * CursorTrail (T1.60)
 *
 * A soft cyan dot that follows the cursor with a slight spring lag.
 * Uses normalized position from `useCursorPosition` mapped to viewport
 * pixels at render time (no layout shift — the dot is `position: fixed`
 * with `pointer-events: none`).
 *
 * Disabled when:
 * - Touch device (no pointer events to track)
 * - `prefers-reduced-motion: reduce` (per dispatch T1.62)
 */
export function CursorTrail(): JSX.Element | null {
  const reducedMotion = usePrefersReducedMotion();
  const [isTouch, setIsTouch] = useState<boolean>(false);
  const { x, y } = useCursorPosition();

  useEffect(() => {
    setIsTouch(detectTouch());
  }, []);

  if (reducedMotion || isTouch) return null;

  const left =
    typeof window === "undefined" ? 0 : x * window.innerWidth - DOT_DIAMETER_PX / 2;
  const top =
    typeof window === "undefined" ? 0 : y * window.innerHeight - DOT_DIAMETER_PX / 2;

  return (
    <div
      data-testid="cursor-trail-dot"
      aria-hidden="true"
      style={{
        position: "fixed",
        pointerEvents: "none",
        width: `${DOT_DIAMETER_PX}px`,
        height: `${DOT_DIAMETER_PX}px`,
        borderRadius: "50%",
        background: "var(--accent-cyan, #22D3EE)",
        opacity: 0.6,
        mixBlendMode: "screen",
        transform: "translate3d(0, 0, 0)",
        left: `${left}px`,
        top: `${top}px`,
        transition: "left 80ms ease-out, top 80ms ease-out",
        zIndex: 9999,
      }}
    />
  );
}
