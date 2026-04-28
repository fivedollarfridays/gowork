"use client";

/**
 * W2 Driver C — Ch4a (T2.32) Criminal record sub-chapter.
 *
 * Locked editorial (en.json):
 *   detail   — "4.8 miles. Bus 4 + Bus 6 = 71 minutes."
 *   statValue— "71 min" / "71 min"
 *   aria     — "Barrier one: criminal record. ..."
 *
 * Visual responsibility: Tarrant County District Clerk pin lights up
 * (Driver B's offices.ts owns the layer toggle; this component owns the
 * EDITORIAL OVERLAY only — the map surface is composed by WallContainer).
 */
import type { ReactElement } from "react";
import { SubChapterShell } from "./SubChapterShell";

export interface Chapter04aProps {
  /** Local progress 0..1 inside this sub-chapter. */
  progress: number;
}

export function Chapter04aCriminalRecord({
  progress,
}: Chapter04aProps): ReactElement {
  return (
    <SubChapterShell
      subChapterId="4a"
      i18nPrefix="wall.chapter04a"
      progress={progress}
      tint="amber"
    />
  );
}
