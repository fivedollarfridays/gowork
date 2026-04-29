"use client";

/**
 * Driver C — Ch04 scroll choreography hook.
 *
 * Slices the section's scroll progress into 4 keyframes and:
 *   - calls `map.flyTo` for each step (via `window._gw_map` published by
 *     the mount helper — extended with a `flyTo` accessor so SiteHeader's
 *     simple `setStyle` interface is preserved)
 *   - calls `onStepChange(step)` so the React tree can update HUD + cards
 *
 * Reduced-motion: jumps straight to the final keyframe (step 3), no scrub.
 */

import { useEffect, type RefObject } from "react";

const KEYFRAMES: ReadonlyArray<{
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
}> = [
  { center: [-97.338, 32.734], zoom: 13.4, pitch: 50, bearing: -10 },
  { center: [-97.33, 32.756], zoom: 12.6, pitch: 40, bearing: 8 },
  { center: [-97.325, 32.75], zoom: 12.2, pitch: 30, bearing: 0 },
  { center: [-97.295, 32.8], zoom: 11.9, pitch: 38, bearing: -16 },
];

interface MapWithFly {
  flyTo?: (opts: Record<string, unknown>) => void;
  jumpTo?: (opts: Record<string, unknown>) => void;
}

declare global {
  interface Window {
    _gw_map_fly?: MapWithFly;
  }
}

function flyToStep(step: number): void {
  if (typeof window === "undefined") return;
  const map = window._gw_map_fly;
  if (!map) return;
  const k = KEYFRAMES[step];
  try {
    map.flyTo?.({
      center: k.center,
      zoom: k.zoom,
      pitch: k.pitch,
      bearing: k.bearing,
      duration: 1400,
      essential: true,
    });
  } catch {
    /* ignore — flyTo failures degrade gracefully */
  }
}

function jumpToStep(step: number): void {
  if (typeof window === "undefined") return;
  const map = window._gw_map_fly;
  if (!map) return;
  const k = KEYFRAMES[step];
  try {
    map.jumpTo?.({
      center: k.center,
      zoom: k.zoom,
      pitch: k.pitch,
      bearing: k.bearing,
    });
  } catch {
    /* ignore */
  }
}

export interface UseCh04ChoreographyOptions {
  sectionRef: RefObject<HTMLElement | null>;
  onStepChange: (step: number) => void;
  reduced: boolean;
}

/**
 * Wire ScrollTrigger to fire onStepChange + flyTo at the 4 keyframes.
 * Lazy-imports gsap so jsdom + airplane-mode bundles never crash.
 */
export function useCh04Choreography({
  sectionRef,
  onStepChange,
  reduced,
}: UseCh04ChoreographyOptions): void {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = sectionRef.current;
    if (!el) return;

    if (reduced) {
      onStepChange(3);
      jumpToStep(3);
      return;
    }

    let stInst: { kill: () => void } | null = null;
    let cancelled = false;

    (async () => {
      try {
        const gsapMod = await import("gsap");
        const stMod = await import("gsap/ScrollTrigger");
        if (cancelled) return;
        const gsap = gsapMod.gsap;
        const ScrollTrigger = stMod.ScrollTrigger;
        gsap.registerPlugin(ScrollTrigger);

        let lastStep = -1;
        stInst = ScrollTrigger.create({
          trigger: el,
          start: "top 80%",
          end: "bottom top",
          scrub: 0.6,
          onUpdate: (self: { progress: number }) => {
            const p = self.progress;
            const step = Math.min(3, Math.max(0, Math.floor(p * 4)));
            if (step !== lastStep) {
              lastStep = step;
              onStepChange(step);
              flyToStep(step);
            }
          },
        });
      } catch {
        // gsap unavailable — fallback: snap straight to final keyframe.
        onStepChange(3);
        jumpToStep(3);
      }
    })();

    return () => {
      cancelled = true;
      try {
        stInst?.kill?.();
      } catch {
        /* ignore */
      }
    };
  }, [sectionRef, onStepChange, reduced]);
}
