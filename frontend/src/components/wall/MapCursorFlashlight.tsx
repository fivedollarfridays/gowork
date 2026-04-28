"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useThrottledRAF } from "@/hooks/useThrottledRAF";

/**
 * T4.A.3 — MapCursorFlashlight.
 *
 * Spotlight overlay that brightens a 200 px radius around the cursor on
 * the Mapbox canvas, dimming the rest by ~10% via a radial-gradient
 * mask image. The W1 `CursorFlashlight` is a different effect (a glow
 * disc); this is a viewport-coverage mask wired specifically to the
 * map element.
 *
 * Implementation:
 *   - Listens to `window.pointermove` (the overlay itself uses
 *     `pointer-events:none` so the map underneath stays interactive).
 *   - Updates `--cursor-x` and `--cursor-y` CSS custom properties
 *     in viewport-pixel units, throttled via `useThrottledRAF` so we
 *     never schedule more than one paint per frame.
 *   - The mask is `radial-gradient(circle <radius>px at var(--cursor-x)
 *     var(--cursor-y), white, transparent)` — Safari < 15.4 falls back
 *     to no-mask (vendor support gracefully degrades).
 *
 * Reduced-motion / touch fallback: the overlay still mounts but renders
 * fully transparent with `data-fallback="disabled"` so visual-regression
 * tests can assert the fallback path. The map below shows at full
 * opacity (no dim, no mask).
 */

interface MapCursorFlashlightProps {
  /** Mask radius in pixels. Default 200 per W4 spec. */
  radiusPx?: number;
  /** Dim amount applied to the unmasked area (0..1). Default 0.10. */
  dim?: number;
}

const DEFAULT_RADIUS = 200;
const DEFAULT_DIM = 0.10;

function detectTouch(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof navigator !== "undefined" && (navigator.maxTouchPoints ?? 0) > 0) {
    return true;
  }
  return false;
}

export function MapCursorFlashlight({
  radiusPx = DEFAULT_RADIUS,
  dim = DEFAULT_DIM,
}: MapCursorFlashlightProps = {}): JSX.Element {
  const reducedMotion = usePrefersReducedMotion();
  const [isTouch, setIsTouch] = useState<boolean>(false);
  const overlayRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setIsTouch(detectTouch());
  }, []);

  const useFallback = reducedMotion || isTouch;

  // Latest cursor pos, applied to the overlay imperatively to avoid
  // a React rerender per frame.
  const apply = useThrottledRAF((coords: { x: number; y: number }) => {
    const el = overlayRef.current;
    if (!el) return;
    el.style.setProperty("--cursor-x", `${coords.x}px`);
    el.style.setProperty("--cursor-y", `${coords.y}px`);
  });

  useEffect(() => {
    if (useFallback) return;
    const handler = (event: PointerEvent) => {
      apply({ x: event.clientX, y: event.clientY });
    };
    window.addEventListener("pointermove", handler, { passive: true });
    return () => window.removeEventListener("pointermove", handler);
  }, [useFallback, apply]);

  const baseStyle: CSSProperties = {
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
  };

  // Reduced-motion / touch — full transparency, no mask.
  const style: CSSProperties = useFallback
    ? { ...baseStyle, background: "transparent" }
    : {
        ...baseStyle,
        background: `oklch(0 0 0 / ${dim})`,
        maskImage: `radial-gradient(circle ${radiusPx}px at var(--cursor-x) var(--cursor-y), transparent 0%, black 100%)`,
        WebkitMaskImage: `radial-gradient(circle ${radiusPx}px at var(--cursor-x) var(--cursor-y), transparent 0%, black 100%)`,
      };

  return (
    <div
      ref={overlayRef}
      data-testid="map-cursor-flashlight"
      data-fallback={useFallback ? "disabled" : "live"}
      aria-hidden="true"
      style={style}
    />
  );
}
