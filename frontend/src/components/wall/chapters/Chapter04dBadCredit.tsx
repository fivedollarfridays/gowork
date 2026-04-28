"use client";

/**
 * W2 Driver C — Ch4d (T2.35) Bad credit sub-chapter.
 *
 * Locked editorial (en.json): "540. Late payments. One collection
 * account. Half the apartments won't take him — and one in three jobs
 * runs a credit check." Stat: "33%" of jobs unreachable.
 *
 * 4d is the FOURTH wall — the rose tint comes online here, prefiguring
 * Ch5's Labyrinth and the W3 cliff. Spotlight: the page accent shifts
 * from amber to rose as the reader crosses the threshold of "every
 * direction has a barrier."
 */
import type { ReactElement } from "react";
import { SubChapterShell } from "./SubChapterShell";

export interface Chapter04dProps {
  progress: number;
}

export function Chapter04dBadCredit({
  progress,
}: Chapter04dProps): ReactElement {
  return (
    <SubChapterShell
      subChapterId="4d"
      i18nPrefix="wall.chapter04d"
      progress={progress}
      tint="rose"
    />
  );
}
