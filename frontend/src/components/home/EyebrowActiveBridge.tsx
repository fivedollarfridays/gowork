"use client";

/**
 * EyebrowActiveBridge — polish-2 T55.
 *
 * Tracks the active chapter section via IntersectionObserver and
 * toggles `data-eyebrow-active="true"` on the section that occupies
 * ≥ 40% of the viewport. The CSS rule in `home-velocity.css` then
 * lifts the eyebrow's numeric font-weight from 400 → 700, giving the
 * "lit" feel for the chapter the reader is currently inside.
 *
 * Single-active-at-a-time invariant — when a new section becomes
 * active, the previously-active one has its attr removed.
 */
import { useEffect } from "react";

const SECTION_SELECTOR = "section.chapter";
const THRESHOLD = 0.4;
const ATTR = "data-eyebrow-active";

export function EyebrowActiveBridge(): null {
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (typeof IntersectionObserver === "undefined") return;

    const sections = Array.from(
      document.querySelectorAll<HTMLElement>(SECTION_SELECTOR),
    );
    if (sections.length === 0) return;

    let activeEl: HTMLElement | null = null;
    const setActive = (el: HTMLElement | null) => {
      if (activeEl === el) return;
      if (activeEl) activeEl.removeAttribute(ATTR);
      activeEl = el;
      if (activeEl) activeEl.setAttribute(ATTR, "true");
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const el = entry.target as HTMLElement;
          if (entry.intersectionRatio >= THRESHOLD && entry.isIntersecting) {
            setActive(el);
          } else if (el === activeEl && entry.intersectionRatio < THRESHOLD) {
            // Active section no longer satisfies the threshold.
            setActive(null);
          }
        }
      },
      { threshold: [THRESHOLD, 0.6, 0.9] },
    );

    for (const section of sections) observer.observe(section);

    return () => {
      observer.disconnect();
      if (activeEl) activeEl.removeAttribute(ATTR);
    };
  }, []);

  return null;
}
