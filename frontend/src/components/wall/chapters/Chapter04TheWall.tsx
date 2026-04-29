"use client";

/**
 * W2 Driver C — Chapter 04 The Wall — parent orchestrator (T2.31).
 *
 * Carlos's four walls, named one at a time. The orchestrator is small on
 * purpose: pick the active sub-chapter from local progress, route to the
 * right component, fire ONE sound + ONE ARIA narration on the transition.
 *
 * Spotlight invention #3 — a SINGLE narration sink: every sub-chapter
 * transition publishes through `gowork:aria-announce` (W1 AriaLiveRegion).
 * This means a single screen-reader read covers all four barriers without
 * the four sub-chapters knowing about each other. Removing or reordering
 * sub-chapters is a one-line change.
 */
import { useEffect, useRef } from "react";
import type { ReactElement } from "react";
import {
  ch4SubChapter,
  type Ch4SubChapterId,
  CH4_SUBCHAPTERS,
} from "@/lib/wall/chapters/ch4SubChapter";
import { useAriaAnnounce } from "@/components/wall/AriaLiveRegion";
import { play as playSound, type SoundId } from "@/lib/wall/sound";
import { t } from "@/lib/i18n";
import { Chapter04aCriminalRecord } from "./Chapter04aCriminalRecord";
import { Chapter04bNoTransit } from "./Chapter04bNoTransit";
import { Chapter04cNoChildcare } from "./Chapter04cNoChildcare";
import { Chapter04dBadCredit } from "./Chapter04dBadCredit";

export interface Chapter04TheWallProps {
  /** Local chapter progress 0..1 from Driver A's useChapterProgress. */
  progress: number;
  /** Reduced-motion override (forwarded to sub-chapters). */
  reducedMotion?: boolean;
}

/** Map sub-chapter id to a SoundId on the canonical W1 sound catalog. */
function soundFor(id: Ch4SubChapterId): SoundId {
  const sub = CH4_SUBCHAPTERS.find((s) => s.id === id);
  return (sub?.soundId ?? "paper-rustle") as SoundId;
}

/** Sub-chapter renderer — kept inside the orchestrator file as a 1-liner. */
function renderSubChapter(
  id: Ch4SubChapterId,
  progress: number,
): ReactElement {
  if (id === "4a") return <Chapter04aCriminalRecord progress={progress} />;
  if (id === "4b") return <Chapter04bNoTransit progress={progress} />;
  if (id === "4c") return <Chapter04cNoChildcare progress={progress} />;
  return <Chapter04dBadCredit progress={progress} />;
}

export function Chapter04TheWall({
  progress,
  reducedMotion = false,
}: Chapter04TheWallProps): ReactElement {
  const activeSub = ch4SubChapter(progress);
  const announce = useAriaAnnounce();
  const lastSubRef = useRef<Ch4SubChapterId | null>(null);

  useEffect(() => {
    if (lastSubRef.current === activeSub) return;
    lastSubRef.current = activeSub;
    // Fire sound + ARIA narration exactly once per sub-chapter entry.
    playSound(soundFor(activeSub));
    const ariaText = t(`wall.chapter04${activeSub.slice(1)}.aria`);
    if (ariaText) announce(ariaText);
  }, [activeSub, announce]);

  return (
    <section
      data-testid="chapter04-wall"
      data-chapter="04"
      data-chapter-id="the-wall"
      data-subactive={activeSub}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-labelledby="chapter04-title"
      className="chapter04-wall relative flex min-h-screen flex-col items-center justify-center px-6 py-16"
    >
      <h2 id="chapter04-title" className="sr-only">
        {t("wall.chapter04.title")}
      </h2>
      {renderSubChapter(activeSub, progress)}
    </section>
  );
}
