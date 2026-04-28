"use client";

import { useScrollProgress } from "./useScrollProgress";

/**
 * T2.8 — useChapterProgress.
 *
 * Chapter-aware scroll state derived from W1 `useScrollProgress`. Returns
 * `{currentChapter, chapterProgress, nextChapter, isTransitioning}`.
 *
 * Chapter ids are 1-indexed (chapters 1–10). `useScrollProgress` returns
 * 0-indexed chapter offsets — this hook absorbs that boundary so chapter
 * components can speak 1-indexed: "Chapter 3 is currentChapter=3."
 *
 * `isTransitioning` is true when the user is within `BOUNDARY_BAND` of a
 * chapter boundary. flyTo orchestrators (T2.9) use this to debounce
 * camera flights and overlay fades use it to overlap (T2.114 enrichment).
 *
 * Spotlight (Compound Lens — Driver A): chapter components (Drivers B/C)
 * AND the flyTo orchestrator (Driver A) BOTH consume this hook. One
 * boundary-detection contract serves both — drift is impossible.
 */

const TOTAL_CHAPTERS = 10;
/** Distance from a chapter boundary inside which `isTransitioning` flips.
 *  0.005 of total page progress = 5 % of one chapter (with 10 chapters). */
const BOUNDARY_BAND = 0.005;

export interface ChapterProgressState {
  /** 1-indexed current chapter (1..10). */
  currentChapter: number;
  /** 0..1 progress within the current chapter. */
  chapterProgress: number;
  /** 1-indexed next chapter (clamped at the last chapter). */
  nextChapter: number;
  /** True when within `BOUNDARY_BAND` of an upstream/downstream boundary. */
  isTransitioning: boolean;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/** Hook that surfaces chapter index + progress + boundary band. */
export function useChapterProgress(): ChapterProgressState {
  const { chapter, progressInChapter, totalProgress } = useScrollProgress(TOTAL_CHAPTERS);

  const currentChapter = clamp(chapter + 1, 1, TOTAL_CHAPTERS);
  const nextChapter = clamp(currentChapter + 1, 1, TOTAL_CHAPTERS);

  // Boundary band — distance from nearest chapter boundary on the
  // 0..1 page-progress axis.
  const chapterWidth = 1 / TOTAL_CHAPTERS;
  const localOffset = totalProgress - chapter * chapterWidth;
  const distFromUpper = Math.abs(chapterWidth - localOffset);
  const distFromLower = Math.abs(localOffset);

  let isTransitioning = false;
  if (currentChapter < TOTAL_CHAPTERS && distFromUpper <= BOUNDARY_BAND) {
    isTransitioning = true;
  } else if (currentChapter > 1 && distFromLower <= BOUNDARY_BAND) {
    isTransitioning = true;
  }

  return {
    currentChapter,
    chapterProgress: clamp(progressInChapter, 0, 1),
    nextChapter,
    isTransitioning,
  };
}
