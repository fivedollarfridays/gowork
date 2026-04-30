"use client";

import { useScrollProgress } from "@/hooks/useScrollProgress";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

/**
 * HeaderProgressRail — polish-2 T10.
 *
 * Pinned just below the SiteHeader. 8 segments, 2px tall, fill cyan as
 * scroll passes each chapter. Active segment glows. Reduced-motion mode
 * collapses to a single thin bar showing total %.
 *
 * Stateless wrt scroll — reads `useScrollProgress(8)`. Mount once near
 * the top of HomePage (Driver E does this immediately under <SiteHeader />).
 */

const TOTAL_CHAPTERS = 8;

type SegmentState = "done" | "now" | "pending";

function segmentState(idx0: number, currentChapter0: number): SegmentState {
  if (idx0 < currentChapter0) return "done";
  if (idx0 === currentChapter0) return "now";
  return "pending";
}

export function HeaderProgressRail(): JSX.Element {
  const reduced = usePrefersReducedMotion();
  const { chapter, totalProgress } = useScrollProgress(TOTAL_CHAPTERS);
  const currentChapter0 = Math.min(TOTAL_CHAPTERS - 1, Math.max(0, chapter));

  if (reduced) {
    const widthPct = `${Math.round(Math.max(0, Math.min(1, totalProgress)) * 100)}%`;
    return (
      <div
        className="header-progress-rail header-progress-rail--reduced"
        role="progressbar"
        aria-valuenow={Math.round(totalProgress * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        data-header-progress-rail
      >
        <div className="header-progress-rail__bar" style={{ width: widthPct }} />
      </div>
    );
  }

  return (
    <div
      className="header-progress-rail"
      role="progressbar"
      aria-valuenow={Math.round(totalProgress * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      data-header-progress-rail
    >
      {Array.from({ length: TOTAL_CHAPTERS }).map((_, i) => (
        <span
          key={i}
          data-progress-segment={i + 1}
          data-state={segmentState(i, currentChapter0)}
          className="header-progress-rail__segment"
        />
      ))}
    </div>
  );
}
