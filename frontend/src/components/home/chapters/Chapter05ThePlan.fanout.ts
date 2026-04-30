"use client";

/**
 * Driver C — Ch05 fan-out scroll trigger.
 *
 * Reads scroll progress 0..1 across the section and feeds it to the
 * chapter's onProgress callback. Reduced-motion: jumps straight to 1
 * (cards rendered fanned, no scrub).
 */

import { useEffect, type RefObject } from "react";

export interface CardTransform {
  /** Translate-X in px. */
  x: number;
  /** Translate-Y in px. */
  y: number;
  /** Rotation in degrees. */
  angle: number;
  /** Opacity 0..1. */
  opacity: number;
  /** z-index integer. */
  zIndex: number;
  /** Scale 0..1. */
  scale: number;
}

export interface UseCh05FanOutOptions {
  sectionRef: RefObject<HTMLElement | null>;
  onProgress: (p: number) => void;
  reduced: boolean;
}

export function useCh05FanOut({
  sectionRef,
  onProgress,
  reduced,
}: UseCh05FanOutOptions): void {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = sectionRef.current;
    if (!el) return;

    if (reduced) {
      onProgress(1);
      return;
    }

    let stInst: { kill: () => void } | null = null;
    let cancelled = false;

    (async () => {
      try {
        const stMod = await import("gsap/ScrollTrigger");
        const gsapMod = await import("gsap");
        if (cancelled) return;
        gsapMod.gsap.registerPlugin(stMod.ScrollTrigger);

        stInst = stMod.ScrollTrigger.create({
          trigger: el,
          start: "top 80%",
          end: "bottom 20%",
          scrub: 0.6,
          onUpdate: (self: { progress: number }) => {
            onProgress(self.progress);
          },
        });
      } catch {
        // GSAP unavailable — render fanned out (final state).
        onProgress(1);
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
  }, [sectionRef, onProgress, reduced]);
}
