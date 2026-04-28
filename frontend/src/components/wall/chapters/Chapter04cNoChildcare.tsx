"use client";

/**
 * W2 Driver C — Ch4c (T2.34) No childcare sub-chapter.
 *
 * Locked editorial (en.json): "His daughter is 4. Childcare is $1,200 a
 * month he doesn't have." Stat: "$1,200/mo".
 */
import type { ReactElement } from "react";
import { SubChapterShell } from "./SubChapterShell";

export interface Chapter04cProps {
  progress: number;
}

export function Chapter04cNoChildcare({
  progress,
}: Chapter04cProps): ReactElement {
  return (
    <SubChapterShell
      subChapterId="4c"
      i18nPrefix="wall.chapter04c"
      progress={progress}
      tint="amber"
    />
  );
}
