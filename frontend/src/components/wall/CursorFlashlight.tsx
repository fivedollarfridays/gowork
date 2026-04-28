"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { useCursorPosition } from "@/hooks/useCursorPosition";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

const FLASHLIGHT_RADIUS_PX = 80;

function detectTouch(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof navigator !== "undefined" && (navigator.maxTouchPoints ?? 0) > 0) {
    return true;
  }
  return false;
}

interface CursorFlashlightProps {
  /** Optional override of the flashlight radius (default 80px). */
  radiusPx?: number;
}

/**
 * CursorFlashlight (T1.61)
 *
 * The 80px glow circle that brightens map elements within. Wired to
 * `useCursorPosition`; sets `--flashlight-x` and `--flashlight-y`
 * percentage CSS variables that consuming styles (W2 map paint
 * expressions) can read.
 *
 * Reduced-motion / touch fallback: the overlay still mounts but uses
 * a uniform-bright background instead of the localized radial gradient,
 * so map readability is preserved without the cursor effect.
 *
 * Built independent of Mapbox so it can be unit-tested + used in W2's
 * sandbox routes before the Mapbox dep is wired up.
 */
export function CursorFlashlight({ radiusPx = FLASHLIGHT_RADIUS_PX }: CursorFlashlightProps = {}): JSX.Element {
  const reducedMotion = usePrefersReducedMotion();
  const { x, y } = useCursorPosition();
  const [isTouch, setIsTouch] = useState<boolean>(false);

  useEffect(() => {
    setIsTouch(detectTouch());
  }, []);

  const useFallback = reducedMotion || isTouch;
  const xPct = (x * 100).toFixed(2);
  const yPct = (y * 100).toFixed(2);

  const baseStyle: CSSProperties = {
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
  };

  const flashlightStyle: CSSProperties = useFallback
    ? {
        ...baseStyle,
        background:
          "radial-gradient(circle at 50% 50%, rgba(255,255,255,0.18), rgba(255,255,255,0.18))",
      }
    : {
        ...baseStyle,
        background: `radial-gradient(circle ${radiusPx}px at var(--flashlight-x) var(--flashlight-y), rgba(255,255,255,0.0) 0%, rgba(0,0,0,0.5) 100%)`,
        ["--flashlight-x" as keyof CSSProperties]: `${xPct}%`,
        ["--flashlight-y" as keyof CSSProperties]: `${yPct}%`,
      } as CSSProperties;

  return (
    <div
      data-testid="cursor-flashlight"
      data-fallback={useFallback ? "uniform" : "live"}
      aria-hidden="true"
      style={flashlightStyle}
    />
  );
}
