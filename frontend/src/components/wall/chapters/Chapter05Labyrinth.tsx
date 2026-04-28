"use client";

/**
 * W2 Driver C — Chapter 05 The Labyrinth (T2.41 + T2.42 + T2.45).
 *
 * 5 offices. 47 forms. Each one says go to the next one.
 *
 * Visual:
 *   - chaotic SVG path overlay (looping, dead-ending) drawn between
 *     5 fixed office nodes
 *   - 47-form counter ticks 0 → 47 with progress
 *   - editorial pull-quote ("Every office gave me one form...") below
 *
 * Reduced-motion: path is rendered fully drawn, counter snaps to 47.
 * Sound: paper-rustle on chapter entry (mute-respected via W1 sound API).
 */
import { useEffect, useRef } from "react";
import type { ReactElement } from "react";
import { t } from "@/lib/i18n";
import { useAriaAnnounce } from "@/components/wall/AriaLiveRegion";
import { play as playSound } from "@/lib/wall/sound";
import {
  LABYRINTH_NODES,
  LABYRINTH_PATH_D,
  LABYRINTH_PATH_LENGTH,
  progressDashoffset,
  isNodeLit,
} from "@/lib/wall/chapters/labyrinthPath";
import { FormsCounter } from "./FormsCounter";

export interface Chapter05LabyrinthProps {
  /** Local Ch5 progress 0..1. Driver A's useChapterProgress feeds this. */
  progress: number;
  /** Reduced-motion override; defaults to false (motion allowed). */
  reducedMotion?: boolean;
}

export function Chapter05Labyrinth({
  progress,
  reducedMotion = false,
}: Chapter05LabyrinthProps): ReactElement {
  const announce = useAriaAnnounce();
  const enteredRef = useRef(false);

  useEffect(() => {
    if (enteredRef.current) return;
    enteredRef.current = true;
    playSound("paper-rustle");
    const aria = t("wall.chapter05.aria");
    if (aria) announce(aria);
  }, [announce]);

  const dashoffset = reducedMotion ? 0 : progressDashoffset(progress);

  return (
    <section
      data-testid="chapter05-labyrinth"
      data-chapter="05"
      data-chapter-id="labyrinth"
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-labelledby="chapter05-title"
      className="chapter05-labyrinth relative flex min-h-screen flex-col items-center justify-center gap-8 px-6 py-12"
    >
      <h2
        id="chapter05-title"
        className="chapter05-labyrinth__title text-3xl font-semibold tracking-tight md:text-4xl"
      >
        {t("wall.chapter05.title")}
      </h2>

      <p
        data-testid="ch5-editorial"
        className="chapter05-labyrinth__editorial max-w-2xl text-center text-xl leading-relaxed text-[var(--fg-primary)] md:text-2xl"
      >
        {t("wall.chapter05.editorial")}
      </p>

      <FormsCounter progress={progress} reducedMotion={reducedMotion} />

      <span className="chapter05-labyrinth__counterLabel text-sm uppercase tracking-wide text-[var(--fg-secondary)]">
        {t("wall.chapter05.formsCounterLabel")}
      </span>

      <svg
        data-testid="ch5-labyrinth-svg"
        className="chapter05-labyrinth__svg h-72 w-full max-w-3xl"
        viewBox="0 0 1000 800"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
        focusable="false"
      >
        <path
          data-testid="ch5-labyrinth-path"
          d={LABYRINTH_PATH_D}
          fill="none"
          stroke="var(--accent-amber)"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={LABYRINTH_PATH_LENGTH}
          strokeDashoffset={dashoffset}
          opacity={0.85}
        />
        {LABYRINTH_NODES.map((node, idx) => {
          const lit = isNodeLit(idx, progress);
          return (
            <circle
              key={node.id}
              data-testid={`ch5-office-${node.id}`}
              data-lit={lit ? "true" : "false"}
              cx={node.x}
              cy={node.y}
              r={lit ? 14 : 8}
              fill={lit ? "var(--accent-amber)" : "var(--fg-muted)"}
              opacity={lit ? 1 : 0.4}
            />
          );
        })}
      </svg>

      <blockquote
        data-testid="ch5-pullquote"
        className="editorial-pullquote max-w-2xl"
      >
        {t("wall.chapter05.pullquote")}
      </blockquote>
    </section>
  );
}
