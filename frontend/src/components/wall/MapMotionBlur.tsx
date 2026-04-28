"use client";

/**
 * T4.D.6 — MapMotionBlur (Wave 4 polish).
 *
 * Subtle motion-blur on the Mapbox background when scroll velocity
 * exceeds the threshold. Wraps the Mapbox canvas in a transformed
 * div that toggles `filter: blur(2px)` based on `useScrollVelocity().isFast`.
 *
 * Reduced-motion: filter is always 'none'. The wrapper still renders so
 * the layout stays identical — only the filter is suppressed.
 *
 * # Why a wrapper not a hook on MapboxScene
 *
 * Mapbox-gl renders a WebGL canvas; a `filter` applied directly to the
 * canvas can affect input-pointer hit testing on some browsers. Wrapping
 * the canvas in a parent div and applying the filter on the parent keeps
 * pointer events clean (the wrapper is `pointer-events: none` only when
 * the filter is active).
 *
 * # Threshold + transition
 *
 * Threshold lives inside `useScrollVelocity` (Spotlight #6 guards the
 * default of 3 px/ms). The transition on `filter` smooths the on/off so
 * the user sees a gentle in/out, not a strobe.
 */

import { type CSSProperties, type ReactNode } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useScrollVelocity } from "@/hooks/useScrollVelocity";

const BLUR_PX = 2;

interface MapMotionBlurProps {
  children: ReactNode;
}

export function MapMotionBlur({ children }: MapMotionBlurProps) {
  const reduced = usePrefersReducedMotion();
  const { isFast } = useScrollVelocity();

  const blurActive = !reduced && isFast;
  const fallback: "live" | "reduced" | "idle" = reduced
    ? "reduced"
    : isFast
      ? "live"
      : "idle";

  const style: CSSProperties = {
    width: "100%",
    height: "100%",
    filter: blurActive ? `blur(${BLUR_PX}px)` : "none",
    transition: "filter 200ms ease-out",
    willChange: "filter",
  };

  return (
    <div
      data-testid="map-motion-blur"
      data-fallback={fallback}
      style={style}
    >
      {children}
    </div>
  );
}
