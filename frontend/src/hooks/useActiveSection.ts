"use client";

/**
 * useActiveSection — scroll-position-based active-chapter tracker.
 *
 * polish-3 round-3 — was IntersectionObserver-based, but GSAP `pin:
 * true` on Ch08 (which uses `position: fixed` + a pin-spacer wrapper)
 * confused IO: the spacer occupies the natural document flow while the
 * pinned element sits at top of viewport, so IO would see Ch07 (still
 * in normal flow above the pin-spacer) as the highest intersection
 * ratio while the user was actually viewing Ch08.
 *
 * The rewrite: on every scroll (rAF-throttled), compute the section
 * whose midpoint is CLOSEST to the viewport's vertical center via
 * `getBoundingClientRect()`. This survives GSAP pins because a pinned
 * element's bounding rect IS at top:0 of the viewport, so its center
 * is naturally near viewport center.
 *
 * Contract:
 *   - Pass a list of section ids (already on the DOM, e.g. "chapter-01"
 *     ... "chapter-08").
 *   - Returns the 1-indexed active section (1..N).
 *   - SSR-safe: returns 1 before mount.
 *
 * Lazy-loaded sections: re-resolves element refs every scroll tick
 * (cheap getElementById lookup), so a chapter that mounts via
 * next/dynamic AFTER the hook's first effect run is picked up
 * automatically once it lands in the DOM.
 */

import { useEffect, useState } from "react";

export interface UseActiveSectionOptions {
  /** Section ids in narrative order, 1-indexed in the result. */
  sectionIds: ReadonlyArray<string>;
}

export function useActiveSection(
  opts: UseActiveSectionOptions,
): number {
  const { sectionIds } = opts;
  const [active, setActive] = useState<number>(1);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    let rafId: number | null = null;
    let scheduled = false;
    let lastIdx = -1;

    const sample = () => {
      scheduled = false;
      const vh = window.innerHeight || 1;
      const center = vh / 2;
      let bestIdx = 1;
      let bestDist = Number.POSITIVE_INFINITY;
      for (let i = 0; i < sectionIds.length; i += 1) {
        const el = document.getElementById(sectionIds[i]);
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        // Skip sections fully off-screen.
        if (rect.bottom < 0 || rect.top > vh) continue;
        const sectionCenter = rect.top + rect.height / 2;
        const dist = Math.abs(sectionCenter - center);
        if (dist < bestDist) {
          bestDist = dist;
          bestIdx = i + 1;
        }
      }
      if (bestIdx !== lastIdx) {
        lastIdx = bestIdx;
        setActive(bestIdx);
      }
    };

    const onScroll = () => {
      if (scheduled) return;
      scheduled = true;
      rafId = window.requestAnimationFrame(sample);
    };

    sample();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (rafId !== null) window.cancelAnimationFrame(rafId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionIds.length]);

  return active;
}
