/**
 * wallTimeline — pure derivation of "where in the spine am I" data.
 *
 * W3 Driver D Spotlight invention #2.
 *
 * # Why this exists
 *
 * The question "given totalProgress, what chapter am I in and how far
 * through it?" is asked from at least eight surfaces today:
 *
 *   - useChapterProgress hook (React)
 *   - chapterCounter.currentChapterFor (pure)
 *   - WallContainer (React, derives currentChapter + chapterProgress)
 *   - ChaptersSequence (React, computes local for each chapter)
 *   - path-line header (consumes total → counter)
 *   - cameraChoreography flyToOrchestrator (camera key derivation)
 *   - dev/wall inspector (Spotlight #4; needs current + bounds)
 *   - axe + sound audit harnesses (test helpers)
 *
 * Eight derivation paths, each with its own arithmetic. wallTimeline
 * provides ONE pure function that returns ALL the answers, so the eight
 * surfaces consume it instead of re-deriving.
 *
 * # Spotlight Lens — Structural
 *
 * The "what chapter am I in" question shouldn't have eight different
 * answers. wallTimeline is the answer.
 *
 * # Compound Lens
 *
 * W4 will need transition-phase awareness ("am I in the dwell, the
 * crossfade, or the settle?") for life-layer fades. Shipping
 * `transitionPhase` now means W4 reads the same lens, not a new one.
 */

import {
  TOTAL_CHAPTERS,
  CHAPTER_BOUNDS,
  globalToLocal,
  type ChapterIndex,
  type ChapterBounds,
} from "./wallProgress";
import { currentChapterFor } from "./chapterCounter";

/** Phase of the chapter spine — what kind of beat are we on right now? */
export type TransitionPhase =
  /** First 15% of the chapter — entrance / settle. */
  | "entering"
  /** Middle 70% — the chapter's content time. */
  | "dwelling"
  /** Last 15% — preparing the camera handoff to the next chapter. */
  | "exiting";

export interface TimelineFrame {
  /** Global progress (0..1), clamped to range. */
  totalProgress: number;
  /** 1-indexed current chapter (1..10). */
  currentChapter: ChapterIndex;
  /** 0..1 progress within the current chapter. */
  chapterProgress: number;
  /** 1-indexed next chapter id, or null if currentChapter === 10. */
  nextChapter: ChapterIndex | null;
  /** Phase of the current chapter (entering/dwelling/exiting). */
  transitionPhase: TransitionPhase;
  /** Bounds of the current chapter (for hand-off math). */
  currentBounds: ChapterBounds;
}

const ENTRY_THRESHOLD = 0.15;
const EXIT_THRESHOLD = 0.85;

function clamp01(v: number): number {
  if (Number.isNaN(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

function phaseFor(local: number): TransitionPhase {
  if (local < ENTRY_THRESHOLD) return "entering";
  if (local >= EXIT_THRESHOLD) return "exiting";
  return "dwelling";
}

/**
 * Pure derivation: given a global progress value (0..1), return the full
 * timeline frame — which chapter, how far through, what comes next, and
 * what phase the cinematic engine should be on.
 */
export function frameAt(totalProgress: number): TimelineFrame {
  const t = clamp01(totalProgress);
  const currentChapter = currentChapterFor(t);
  const currentBounds = CHAPTER_BOUNDS[currentChapter - 1];
  const chapterProgress = globalToLocal(t, currentChapter);
  const isFinal = currentChapter === (TOTAL_CHAPTERS as ChapterIndex);
  const nextChapter = isFinal ? null : ((currentChapter + 1) as ChapterIndex);
  const transitionPhase = phaseFor(chapterProgress);
  return {
    totalProgress: t,
    currentChapter,
    chapterProgress,
    nextChapter,
    transitionPhase,
    currentBounds,
  };
}

/**
 * Pre-computed sample frames at chapter midpoints. Useful for tests, dev
 * inspectors, and any UI that wants to enumerate "where the timeline puts
 * the camera at each chapter's midpoint."
 */
export function midpointFrames(): readonly TimelineFrame[] {
  return CHAPTER_BOUNDS.map((b) => {
    const mid = (b.start + b.end) / 2;
    return frameAt(mid);
  });
}
