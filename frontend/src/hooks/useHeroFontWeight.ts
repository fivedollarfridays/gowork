"use client";

import { useMemo } from "react";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

/**
 * T4.A.6 — useHeroFontWeight + useChapterHeadingFontWeight.
 *
 * Two narrow wrappers around the variable-font axis system:
 *
 * 1. **useHeroFontWeight(scrollProgress)** — Ch1 hero contract.
 *    The headline holds at weight 700 while the user is on the question
 *    (scroll progress < 0.05) and lifts to 900 as they pass it.
 *    Reduced-motion locks to 700 (the default rest weight).
 *
 * 2. **useChapterHeadingFontWeight(localProgress)** — Ch2-10 h2.
 *    Chapter headings interpolate 600→800 across their own 0..1 local
 *    scroll. Reduced-motion locks to 600.
 *
 * Both honour `font-optical-sizing: auto` at the call site (CSS rule)
 * so the optical-size axis tracks the rendered display size automatically.
 */

const HERO_TRIGGER = 0.05;
const HERO_WEIGHT_REST = 700;
const HERO_WEIGHT_PEAK = 900;
const CHAPTER_WEIGHT_REST = 600;
const CHAPTER_WEIGHT_PEAK = 800;

function clamp01(value: number): number {
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function variation(weight: number): string {
  return `"wght" ${weight}`;
}

/** Hero headline weight — 700 across scroll 0..0.05, climbing to 900. */
export function useHeroFontWeight(scrollProgress: number): string {
  const reduced = usePrefersReducedMotion();
  return useMemo(() => {
    if (reduced) return variation(HERO_WEIGHT_REST);
    const remapped = clamp01(scrollProgress / HERO_TRIGGER);
    const weight = Math.round(
      HERO_WEIGHT_REST + (HERO_WEIGHT_PEAK - HERO_WEIGHT_REST) * remapped,
    );
    return variation(weight);
  }, [scrollProgress, reduced]);
}

/** Chapter heading weight — 600→800 across chapter-local 0..1 progress. */
export function useChapterHeadingFontWeight(localProgress: number): string {
  const reduced = usePrefersReducedMotion();
  return useMemo(() => {
    if (reduced) return variation(CHAPTER_WEIGHT_REST);
    const p = clamp01(localProgress);
    const weight = Math.round(
      CHAPTER_WEIGHT_REST + (CHAPTER_WEIGHT_PEAK - CHAPTER_WEIGHT_REST) * p,
    );
    return variation(weight);
  }, [localProgress, reduced]);
}
