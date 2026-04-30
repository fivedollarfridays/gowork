"use client";

/**
 * useScrollTiedSlide — premium-Webflow scroll-tied slide-from-side.
 *
 * Returns a ref. The element starts off-screen (xPercent ±100, opacity
 * 0) and slides into place as the element scrolls through the viewport.
 * scrub:true means the animation is BOUND to scroll progress — reversing
 * scroll reverses the slide-in. This is the Lithosquare / Linear /
 * Mercury signature: every text block has a directional entrance and
 * the user can scroll back up to "rewind" the page.
 *
 * Usage:
 *   const ref = useScrollTiedSlide<HTMLDivElement>({ from: "left" });
 *   return <div ref={ref}>...</div>;
 *
 * For staggered children (e.g. paragraph block where each <p> slides in
 * on its own), wrap each child with its own `useScrollTiedSlide`,
 * alternating `from: "left" | "right"` for the cinematic feel.
 *
 * Reduced-motion: paints final state immediately, no scroll trigger.
 */

import { useEffect, useRef } from "react";

export type SlideDirection = "left" | "right" | "up" | "down";

export interface UseScrollTiedSlideOptions {
  from?: SlideDirection;
  /** Distance offset (px or %, default 100% via xPercent / yPercent). */
  distance?: number;
  /** ScrollTrigger start. Default "top 90%" (start when element is 10% on-screen). */
  start?: string;
  /** ScrollTrigger end. Default "top 50%" (end when element midpoint reaches viewport mid). */
  end?: string;
  /** Disable the effect (useful for conditional reduced-motion). */
  disabled?: boolean;
}

export function useScrollTiedSlide<T extends HTMLElement = HTMLElement>(
  opts: UseScrollTiedSlideOptions = {},
): React.RefObject<T> {
  const {
    from = "left",
    distance = 100,
    start = "top 90%",
    end = "top 50%",
    disabled = false,
  } = opts;
  const ref = useRef<T>(null);

  useEffect(() => {
    if (disabled) return undefined;
    if (typeof window === "undefined") return undefined;
    const el = ref.current;
    if (!el) return undefined;
    if (typeof window.matchMedia === "function") {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        el.style.transform = "translate3d(0, 0, 0)";
        el.style.opacity = "1";
        return undefined;
      }
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

        const initial: gsap.TweenVars = { opacity: 0 };
        if (from === "left") initial.xPercent = -distance;
        else if (from === "right") initial.xPercent = distance;
        else if (from === "up") initial.yPercent = -distance;
        else if (from === "down") initial.yPercent = distance;
        gsap.set(el, initial);

        const target: gsap.TweenVars = { opacity: 1, xPercent: 0, yPercent: 0, ease: "none" };
        const tween = gsap.to(el, {
          ...target,
          scrollTrigger: {
            trigger: el,
            start,
            end,
            scrub: 0.6,
          },
        });
        stInst = tween.scrollTrigger ?? null;
      } catch {
        // GSAP unavailable — paint final state.
        el.style.transform = "translate3d(0, 0, 0)";
        el.style.opacity = "1";
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
  }, [from, distance, start, end, disabled]);

  return ref;
}
