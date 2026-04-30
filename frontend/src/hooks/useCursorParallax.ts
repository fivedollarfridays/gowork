"use client";

/**
 * useCursorParallax — subtle hero-element drift toward cursor.
 *
 * Premium-Webflow hero pattern: the H1 / hero composition tracks the
 * cursor with a soft 8-12px max translate, scaled by distance from the
 * viewport center. Reads as cinematic depth without being a literal
 * 3D scene. Disabled on coarse pointer + reduced motion.
 *
 * Returns a ref. Apply to the element you want parallaxed:
 *   const ref = useCursorParallax<HTMLDivElement>({ maxX: 12, maxY: 8 });
 *   return <div ref={ref}>...</div>;
 *
 * Implementation uses requestAnimationFrame easing (lerp 0.08) so the
 * element doesn't snap 1:1 with the cursor — the lag is what feels
 * cinematic. Cleans up on unmount.
 */

import { useEffect, useRef } from "react";

export interface UseCursorParallaxOptions {
  /** Max horizontal translation in px. Default 10. */
  maxX?: number;
  /** Max vertical translation in px. Default 6. */
  maxY?: number;
  /** Lerp amount per rAF tick (0..1). Lower = smoother+slower. Default 0.08. */
  lerp?: number;
  /** Disable the effect. */
  disabled?: boolean;
}

export function useCursorParallax<T extends HTMLElement = HTMLElement>(
  opts: UseCursorParallaxOptions = {},
): React.RefObject<T> {
  const { maxX = 10, maxY = 6, lerp = 0.08, disabled = false } = opts;
  const ref = useRef<T>(null);

  useEffect(() => {
    if (disabled) return undefined;
    if (typeof window === "undefined") return undefined;
    if (typeof window.matchMedia === "function") {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return undefined;
      if (window.matchMedia("(pointer: coarse)").matches) return undefined;
    }

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let rafId: number | null = null;
    let scheduled = false;

    const apply = () => {
      const el = ref.current;
      if (!el) {
        scheduled = false;
        return;
      }
      currentX += (targetX - currentX) * lerp;
      currentY += (targetY - currentY) * lerp;
      el.style.transform = `translate3d(${currentX.toFixed(2)}px, ${currentY.toFixed(2)}px, 0)`;
      const dx = targetX - currentX;
      const dy = targetY - currentY;
      if (Math.abs(dx) < 0.05 && Math.abs(dy) < 0.05 && targetX === 0 && targetY === 0) {
        currentX = 0;
        currentY = 0;
        el.style.transform = `translate3d(0, 0, 0)`;
        scheduled = false;
        rafId = null;
        return;
      }
      rafId = window.requestAnimationFrame(apply);
    };

    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      rafId = window.requestAnimationFrame(apply);
    };

    const onMove = (e: MouseEvent) => {
      const cx = window.innerWidth / 2 || 1;
      const cy = window.innerHeight / 2 || 1;
      const nx = (e.clientX - cx) / cx; // -1 .. 1
      const ny = (e.clientY - cy) / cy;
      targetX = Math.max(-maxX, Math.min(maxX, nx * maxX));
      targetY = Math.max(-maxY, Math.min(maxY, ny * maxY));
      schedule();
    };

    const onLeave = () => {
      targetX = 0;
      targetY = 0;
      schedule();
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mouseleave", onLeave);

    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseleave", onLeave);
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      if (ref.current) ref.current.style.transform = "";
    };
  }, [maxX, maxY, lerp, disabled]);

  return ref;
}
