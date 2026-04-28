"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.47 / T1.49 — Page-load title sequence.
 *
 * The 4-second opening for the wall :
 *   - "GoWork presents"  — fade in (1s)
 *   - "The Wall"          — typewriter in (2s)
 *   - "An interactive map of Fort Worth, Texas · April 2026"
 *                          — fade in (1s)
 *
 * Mapbox initializes behind this sequence; the path-line draws
 * diagonally as a separate concern (PathLineHeader). When complete,
 * onComplete fires so the consumer can hand off to the first chapter.
 *
 * Reduced-motion : everything renders instantly, onComplete fires on
 * the next tick. The page is still readable, just without choreography.
 *
 * Per the dispatch (Wave 2 / T1.48), the audio-cue trigger on first
 * scroll is wired in Driver B's audio scaffold via `useEffect` of a
 * scroll listener. This component does NOT play audio itself.
 */
export interface TitleSequenceProps {
  /** Total duration in ms. Default: 4000. Tests pass a small value. */
  durationMs?: number;
  /** When true, skips animation; renders all three texts immediately. */
  reducedMotion?: boolean;
  /** Called when the sequence finishes (or immediately under RM). */
  onComplete?: () => void;
}

export function TitleSequence({
  durationMs = 4000,
  reducedMotion = false,
  onComplete,
}: TitleSequenceProps): JSX.Element {
  const { t } = useTranslation();
  const [stage, setStage] = useState<0 | 1 | 2 | 3>(reducedMotion ? 3 : 0);

  useEffect(() => {
    if (reducedMotion) {
      onComplete?.();
      return;
    }
    const t1 = setTimeout(() => setStage(1), durationMs * 0.25);
    const t2 = setTimeout(() => setStage(2), durationMs * 0.75);
    const t3 = setTimeout(() => {
      setStage(3);
      onComplete?.();
    }, durationMs);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [durationMs, reducedMotion, onComplete]);

  return (
    <div
      data-title-sequence
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="pointer-events-none fixed inset-0 z-40 flex flex-col items-center justify-center text-center"
    >
      <p
        className={`text-xs uppercase tracking-[0.4em] text-cyan-400 transition-opacity duration-700 ${
          stage >= 0 ? "opacity-100" : "opacity-0"
        }`}
      >
        {t("wall.titleSequence.presenter")}
      </p>
      <h1
        className={`mt-3 text-6xl font-extrabold tracking-tight text-foreground transition-opacity duration-1000 sm:text-7xl ${
          stage >= 1 ? "opacity-100" : "opacity-0"
        }`}
      >
        {t("wall.titleSequence.title")}
      </h1>
      <p
        className={`mt-4 max-w-2xl text-base text-muted-foreground transition-opacity duration-700 ${
          stage >= 2 ? "opacity-100" : "opacity-0"
        }`}
      >
        {t("wall.titleSequence.subtitle")}
      </p>
    </div>
  );
}
