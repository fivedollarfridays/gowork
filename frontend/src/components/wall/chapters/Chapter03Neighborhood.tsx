"use client";

/**
 * Chapter 03 — The Neighborhood (T2.27, T2.29).
 *
 * Camera at zoom 14, pitch 60, bearing 25 (toward east). ZIP 76119
 * boundary fades in (paint expression driven by `data-zip-fill-opacity`
 * attribute Driver A's MapboxScene observes). Carlos's representative-
 * block pin drops in around progress 0.5 with spring easing.
 *
 * # Sound trigger (T2.27 AC + W1 sound module)
 *
 * Single footstep plays once when this chapter enters viewport (state
 * transitions from inactive → active). Mute toggle respected. The
 * "already-played" flag is per-mount, so a scroll-back (chapter
 * inactive → active again) replays once — appropriate for editorial
 * pacing without becoming spammy. T2.130 enrichment can extend to a
 * cross-session memo if needed.
 *
 * # Reduced-motion contract (T2.27 + T2.115)
 *
 * - Pin opacity = 1 at progress 0 (instant reveal).
 * - ZIP fill opacity = 0.3 at progress 0 (data visible immediately).
 * - Sound STILL fires (audio is opt-in independent of motion preference;
 *   reduced-motion only affects animation, not audio cues).
 *
 * # PII safety
 *
 * The pin renders only via the layer module (`carlosPath.ts`) which
 * carries the `piiSafe: true` programmatic guarantee. This chapter
 * never declares its own pin coordinates.
 */

import { useEffect, useRef } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useTranslation } from "@/hooks/useTranslation";
import { play, isMuted } from "@/lib/wall/sound";

const ZIP_FILL_OPACITY_TARGET = 0.3;
const CARLOS_PIN_DROP_PROGRESS = 0.4;

export interface Chapter03NeighborhoodProps {
  /** 0..1 within-chapter progress. */
  progress: number;
  /** true when this chapter is the current chapter (Driver A wires). */
  active: boolean;
  /** Optional override for the chapter id used in data attributes. */
  chapterId?: string;
}

function computeZipOpacity(progress: number, reduced: boolean): number {
  if (reduced) return ZIP_FILL_OPACITY_TARGET;
  const clamped = Math.max(0, Math.min(1, progress));
  return clamped * ZIP_FILL_OPACITY_TARGET;
}

function computeCarlosPinOpacity(progress: number, reduced: boolean): number {
  if (reduced) return 1;
  if (progress <= CARLOS_PIN_DROP_PROGRESS) return 0;
  const remaining = 1 - CARLOS_PIN_DROP_PROGRESS;
  const local = (progress - CARLOS_PIN_DROP_PROGRESS) / remaining;
  // Spring-like ease: snappy initial rise, soft cap.
  return Math.min(1, 1 - Math.pow(1 - local, 3));
}

export function Chapter03Neighborhood({
  progress,
  active,
  chapterId = "neighborhood",
}: Chapter03NeighborhoodProps) {
  const reduced = usePrefersReducedMotion();
  const { t } = useTranslation();
  const playedRef = useRef<boolean>(false);

  // Sound trigger on chapter enter — once per active transition.
  useEffect(() => {
    if (!active) {
      playedRef.current = false;
      return;
    }
    if (playedRef.current) return;
    if (isMuted()) return;
    play("footstep");
    playedRef.current = true;
  }, [active]);

  const zipFillOpacity = computeZipOpacity(progress, reduced);
  const carlosPinOpacity = computeCarlosPinOpacity(progress, reduced);
  const fallback = reduced ? "static" : "scroll";

  return (
    <section
      data-testid="ch3-section"
      data-chapter-id={chapterId}
      aria-labelledby="ch3-heading"
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "4rem 0",
      }}
    >
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: "absolute",
          width: 1,
          height: 1,
          margin: -1,
          padding: 0,
          overflow: "hidden",
          clip: "rect(0 0 0 0)",
          whiteSpace: "nowrap",
          border: 0,
        }}
      >
        {t("wall.chapter03.aria")}
      </div>

      <div
        data-testid="ch3-overlay"
        data-fallback={fallback}
        data-zip-fill-opacity={zipFillOpacity.toFixed(3)}
        data-carlos-pin-opacity={carlosPinOpacity.toFixed(3)}
        style={{
          // Heroic scale (T-Render.1).
          maxWidth: "min(72vw, 56rem)",
          width: "min(92vw, 56rem)",
          padding: "clamp(2rem, 4vw, 4rem) clamp(1.5rem, 4vw, 3rem)",
          color: "var(--fg-primary)",
          background:
            "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 88%, transparent) 0%, color-mix(in oklch, var(--bg-base) 92%, transparent) 100%)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(12px) saturate(140%)",
          WebkitBackdropFilter: "blur(12px) saturate(140%)",
          boxShadow:
            "0 24px 80px color-mix(in oklch, var(--bg-base) 60%, transparent)",
          opacity: reduced ? 1 : Math.max(0.85, progress),
          transition: reduced ? "none" : "opacity 200ms ease-out",
        }}
      >
        <h2
          id="ch3-heading"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(2rem, 4vw, 3.5rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter03.title")}
        </h2>
        <p
          style={{
            marginTop: "1.25rem",
            fontSize: "clamp(1.0625rem, 1.5vw, 1.375rem)",
            lineHeight: 1.65,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter03.body")}
        </p>
      </div>
    </section>
  );
}
