"use client";

/**
 * W2 Driver C — Ch4b (T2.33) No transit sub-chapter.
 *
 * Locked editorial (en.json): "He lives in 76119. Bus 4 to downtown is
 * 45 minutes. Plus a transfer. Plus a wait." Stat: "87 min" downtown
 * commute.
 */
import type { ReactElement } from "react";
import { SubChapterShell } from "./SubChapterShell";

export interface Chapter04bProps {
  progress: number;
}

export function Chapter04bNoTransit({
  progress,
}: Chapter04bProps): ReactElement {
  return (
    <SubChapterShell
      subChapterId="4b"
      i18nPrefix="wall.chapter04b"
      progress={progress}
      tint="amber"
    />
  );
}
