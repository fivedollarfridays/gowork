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

/**
 * Camera keyframes — one per scene card. Coordinates pulled DIRECTLY
 * from the WAYPOINTS table in `Chapter04TheMap.geo.ts` so each step
 * centers on the exact waypoint the scene card describes:
 *
 *   step 0 → 06:42 AM · HOME · ZIP 76104           (Hemphill & Berry)
 *   step 1 → 10:00 AM · DPS · driver license       (south Fort Worth DPS)
 *   step 2 → 12:30 PM · WORKFORCE SOLUTIONS        (downtown navigator)
 *   step 3 → 03:27 PM · ALCON · shift start        (job destination)
 *
 * The previous coordinates were drifted ~2-5km away from each
 * waypoint, so the camera was flying to "empty" areas of the map
 * instead of following the labeled path the user could see drawn
 * across the canvas.
 *
 * Bearing per step is set so the NEXT route segment points roughly
 * "up" on screen — the user's eye reads the journey forward.
 * Pitch decreases as the camera zooms out at the destination so
 * the final overview has more horizon visible. */
const KEYFRAMES: ReadonlyArray<{
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
}> = [
  // Step 0 — HOME. Bearing +20° (next stop DPS is northeast). Tight
  // zoom + high pitch for the "morning departure" close-up.
  { center: [-97.3327, 32.705], zoom: 13.6, pitch: 52, bearing: 20 },
  // Step 1 — DPS. Bearing -25° (next stop Workforce is northwest).
  { center: [-97.311, 32.7395], zoom: 13.5, pitch: 48, bearing: -25 },
  // Step 2 — WORKFORCE SOLUTIONS. Bearing +5° (next is northbound
  // toward Alcon job). Slight zoom-out to show the route line.
  { center: [-97.3208, 32.7488], zoom: 13.0, pitch: 42, bearing: 5 },
  // Step 3 — ALCON · shift start (destination). Lower pitch + wider
  // zoom for the "arrival" overview shot.
  { center: [-97.3447, 32.835], zoom: 12.4, pitch: 36, bearing: -8 },
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
          // PIN: true — locks the section in place at the top of
          // the viewport while the user scrolls. The 4-step
          // choreography fires across +=56% of additional scroll
          // (≈14vh per step), THEN the section unpins and the
          // page below resumes normal scrolling. Without pin, the
          // map was sliding up and out of view while the camera
          // animations were still firing — by step 4 the user
          // could only see the bottom edge of the map.
          //
          // Pin adds 56vh to total page scroll (the user has to
          // scroll that distance through the pin region) but it's
          // the price of cinematic camera + steady viewport.
          start: "top top",
          end: "+=56%",
          pin: true,
          pinSpacing: true,
          anticipatePin: 1,
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
