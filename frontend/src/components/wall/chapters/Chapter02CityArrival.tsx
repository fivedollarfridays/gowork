"use client";

/**
 * Chapter 02 — City Arrival (T2.23, T2.24, T2.25, T2.26).
 *
 * Camera dolly from continental (zoom 3) into Fort Worth (zoom 11,
 * pitch 60). Editorial overlay carries the locked Sundance-Square line
 * (T2.106 enrichment). Trinity Metro layer fades in via the
 * `data-transit-opacity` attribute that Driver A's MapboxScene reads to
 * drive the layer paint expression — keeps render-path zero-LLM.
 *
 * # Reduced-motion contract
 *
 * Transit opacity snaps to its final value (0.6) so screen-reader /
 * reduced-motion users see the data immediately (T2.115 lens).
 */

import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useTranslation } from "@/hooks/useTranslation";

const TRANSIT_OPACITY_TARGET = 0.6;

export interface Chapter02CityArrivalProps {
  /** 0..1 within-chapter progress (Driver A wires from useChapterProgress). */
  progress: number;
  /** Optional override for the chapter id used in data attributes. */
  chapterId?: string;
}

function computeTransitOpacity(progress: number, reduced: boolean): number {
  if (reduced) return TRANSIT_OPACITY_TARGET;
  const clamped = Math.max(0, Math.min(1, progress));
  return clamped * TRANSIT_OPACITY_TARGET;
}

export function Chapter02CityArrival({
  progress,
  chapterId = "city-arrival",
}: Chapter02CityArrivalProps) {
  const reduced = usePrefersReducedMotion();
  const { t } = useTranslation();
  const transitOpacity = computeTransitOpacity(progress, reduced);
  const fallback = reduced ? "static" : "scroll";

  return (
    <section
      data-testid="ch2-section"
      data-chapter-id={chapterId}
      aria-labelledby="ch2-heading"
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "grid",
        placeItems: "end center",
        paddingBottom: "10vh",
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
        {t("wall.chapter02.aria")}
      </div>

      <div
        data-testid="ch2-overlay"
        data-fallback={fallback}
        data-transit-opacity={transitOpacity.toFixed(3)}
        style={{
          maxWidth: "44rem",
          padding: "1.5rem 2rem",
          textAlign: "left",
          color: "var(--fg-primary)",
          background: "color-mix(in oklch, var(--bg-base) 70%, transparent)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(8px)",
          opacity: reduced ? 1 : Math.max(0.85, progress),
          transition: reduced ? "none" : "opacity 200ms ease-out",
        }}
      >
        <h2
          id="ch2-heading"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(1.5rem, 3vw, 2.5rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter02.title")}
        </h2>
        <p
          style={{
            marginTop: "1rem",
            fontSize: "1.125rem",
            lineHeight: 1.55,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter02.body")}
        </p>
      </div>
    </section>
  );
}
