/**
 * wallProgress — global-to-local scroll-progress slicer.
 *
 * Driver D Spotlight invention #1.
 *
 * The Wall's scroll engine produces ONE global progress value (0..1 across
 * all 10 chapters). Every chapter component asks the same question:
 * "Given the global progress, what's MY local 0..1?". Driver D's job is
 * to make sure 10 chapter components don't each invent their own
 * arithmetic. Drift here means a Ch4 sub-chapter that says "we're at 30%
 * of Ch4" while the camera is at zoom 5 over Ch3 — invisible until demo
 * day.
 *
 * Contract:
 *   - Chapters are 1-indexed (1..10).
 *   - Each chapter spans an equal slice of global progress (1/10 = 0.1).
 *   - Local progress is clamped to [0, 1].
 *
 * # Why one module instead of inline math
 *
 * Compound Lens (W2 → W3 → W4 → W5): the same slicer ships in W3 (Ch6-10)
 * and is consumed by life-layers (W4) for chapter-aware tinting. Three
 * future surfaces; one source of truth.
 */

/** Total chapters in The Wall. Drives the slice width. */
export const TOTAL_CHAPTERS = 10 as const;

/** Inclusive 1-indexed chapter id (1..10). */
export type ChapterIndex =
  | 1
  | 2
  | 3
  | 4
  | 5
  | 6
  | 7
  | 8
  | 9
  | 10;

export interface ChapterBounds {
  /** 1-indexed chapter id. */
  chapter: ChapterIndex;
  /** Global progress (0..1) at which this chapter starts (inclusive). */
  start: number;
  /** Global progress (0..1) at which this chapter ends (exclusive for
   *  non-final chapters; inclusive for chapter 10). */
  end: number;
}

const SLICE = 1 / TOTAL_CHAPTERS;

/** Pre-computed chapter bounds — public so other surfaces (audit tests,
 *  dev tools) can iterate without duplicating the slice math. */
export const CHAPTER_BOUNDS: readonly ChapterBounds[] = Array.from(
  { length: TOTAL_CHAPTERS },
  (_, i) => ({
    chapter: (i + 1) as ChapterIndex,
    start: i * SLICE,
    end: (i + 1) * SLICE,
  }),
);

function clampChapterId(chapter: number): ChapterIndex {
  const c = Math.max(1, Math.min(TOTAL_CHAPTERS, Math.floor(chapter)));
  return c as ChapterIndex;
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

/** Get the bounds for a chapter (1-indexed; clamped to the valid range). */
export function chapterBoundsFor(chapter: number): ChapterBounds {
  const id = clampChapterId(chapter);
  return CHAPTER_BOUNDS[id - 1];
}

/**
 * Slice a global progress value (0..1) into LOCAL progress (0..1) within
 * the requested chapter. Out-of-range values clamp to the boundary.
 */
export function globalToLocal(globalProgress: number, chapter: number): number {
  const bounds = chapterBoundsFor(chapter);
  const span = bounds.end - bounds.start;
  if (span <= 0) return 0;
  const local = (globalProgress - bounds.start) / span;
  return clamp01(local);
}

/**
 * Inverse: convert a LOCAL progress value (0..1) inside a chapter to the
 * global progress value (0..1) across all chapters.
 */
export function localToGlobal(localProgress: number, chapter: number): number {
  const bounds = chapterBoundsFor(chapter);
  const local = clamp01(localProgress);
  const span = bounds.end - bounds.start;
  return bounds.start + local * span;
}

/**
 * True when global progress falls inside the requested chapter's range.
 *
 * Boundary policy: the start boundary is inclusive; the end boundary is
 * exclusive for chapters 1..9 (so progress=0.1 belongs to Ch2, not Ch1).
 * The final chapter's end (1.0) is inclusive so progress=1.0 keeps Ch10
 * active.
 */
export function isChapterActive(
  globalProgress: number,
  chapter: number,
): boolean {
  const bounds = chapterBoundsFor(chapter);
  if (bounds.chapter === TOTAL_CHAPTERS) {
    return globalProgress >= bounds.start && globalProgress <= bounds.end;
  }
  return globalProgress >= bounds.start && globalProgress < bounds.end;
}
