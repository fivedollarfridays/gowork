"use client";

import { useEffect, useState } from "react";
import { useScroll } from "framer-motion";

export interface ScrollProgressState {
  /** 0-indexed chapter number (0..chapterCount-1). */
  chapter: number;
  /** 0..1 progress within the active chapter. */
  progressInChapter: number;
  /** 0..1 progress across the whole document. */
  totalProgress: number;
}

const DEFAULT_CHAPTER_COUNT = 10;

function deriveState(progress: number, chapterCount: number): ScrollProgressState {
  const safeCount = Math.max(1, chapterCount);
  const clamped = Math.max(0, Math.min(1, progress));
  const total = clamped * safeCount;
  const chapter = Math.min(safeCount - 1, Math.floor(total));
  const progressInChapter = total - chapter;
  return {
    chapter,
    progressInChapter: Math.max(0, Math.min(1, progressInChapter)),
    totalProgress: clamped,
  };
}

/**
 * Maps the document's scroll progress into a per-chapter offset.
 *
 * Wraps framer-motion's `useScroll` so consumers can ask "which chapter
 * is the reader in, and how deep?" without recomputing the math at every
 * call site. Default chapterCount is 10 (matches the W2/W3 chapter count).
 *
 * SSR-safe: framer-motion's `useScroll` no-ops on the server; we still
 * subscribe via `.on('change')` and tear down on unmount.
 *
 * @param chapterCount Total chapters across the document. Default 10.
 */
export function useScrollProgress(chapterCount: number = DEFAULT_CHAPTER_COUNT): ScrollProgressState {
  const { scrollYProgress } = useScroll();
  const [state, setState] = useState<ScrollProgressState>(() =>
    deriveState(scrollYProgress.get(), chapterCount),
  );

  useEffect(() => {
    setState(deriveState(scrollYProgress.get(), chapterCount));
    const unsubscribe = scrollYProgress.on("change", (value: number) => {
      setState(deriveState(value, chapterCount));
    });
    return unsubscribe;
  }, [scrollYProgress, chapterCount]);

  return state;
}
