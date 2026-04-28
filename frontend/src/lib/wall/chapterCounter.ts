/**
 * chapterCounter — derive "N / 10" counter strings from scroll progress.
 *
 * W3 Driver C Spotlight #3.
 *
 * # Why this exists
 *
 * `wallProgress.ts` answers "given global, what's local for chapter X"
 * (the slicer). It does NOT answer "given global, which chapter am I
 * in?" without callers iterating CHAPTER_BOUNDS themselves. The
 * existing W1 `ChapterCounter` component takes `current` + `total` as
 * props — the value derivation lives in the host.
 *
 * Today: `WallContainer` derives `currentChapter` from
 * `useChapterProgress()`. That works for the chapter component frame,
 * but the path-line header (T3.25c) needs the same number computed
 * from `totalProgress` directly (no React hook), and so does the
 * future W4 chapter-aware tinting layer. Three callers asking the same
 * question — one source of truth.
 *
 * # Compound Lens
 *
 * - W3 today: WallContainer counter, path-line header annotation.
 * - W4: chapter-aware tinting consults `currentChapterFor` for the
 *   "primary" chapter color. Same input, same answer, no drift.
 *
 * # Contract
 *
 * - Input: global progress (0..1). Out-of-range clamps; NaN -> Ch1.
 * - Output: 1-indexed chapter (1..10). Boundary policy mirrors
 *   `wallProgress.isChapterActive` (start inclusive, end exclusive
 *   except Ch10's terminal 1.0 which stays in Ch10).
 */
import { TOTAL_CHAPTERS, CHAPTER_BOUNDS, type ChapterIndex } from "./wallProgress";

/** String form of TOTAL_CHAPTERS — no drift if the constant ever changes. */
export const TOTAL_CHAPTERS_LABEL = String(TOTAL_CHAPTERS);

function clampChapter(n: number): ChapterIndex {
  if (n < 1) return 1;
  if (n > TOTAL_CHAPTERS) return TOTAL_CHAPTERS as ChapterIndex;
  return Math.floor(n) as ChapterIndex;
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

/**
 * Resolve the 1-indexed chapter for a given global progress value.
 * Mirrors `wallProgress.isChapterActive` boundary policy.
 */
export function currentChapterFor(globalProgress: number): ChapterIndex {
  if (Number.isNaN(globalProgress)) return 1;
  if (globalProgress <= 0) return 1;
  if (globalProgress >= 1) return TOTAL_CHAPTERS as ChapterIndex;
  for (const bounds of CHAPTER_BOUNDS) {
    if (bounds.chapter === TOTAL_CHAPTERS) {
      if (globalProgress >= bounds.start) return bounds.chapter;
    } else if (globalProgress >= bounds.start && globalProgress < bounds.end) {
      return bounds.chapter;
    }
  }
  return 1;
}

/**
 * Format a chapter number as "NN / 10" (zero-padded, slash-separated).
 * Out-of-range inputs clamp to [1, 10].
 */
export function formatCounter(chapter: number): string {
  const c = clampChapter(chapter);
  return `${pad2(c)} / ${TOTAL_CHAPTERS_LABEL}`;
}
