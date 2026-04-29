"use client";

/**
 * W3 Driver B — Chapter 07 The Path (T3.10).
 *
 * Narrative Reset (sprint/narrative-reset): Same-day case file.
 *
 * The original chapter narrative — "Five stops. Twelve weeks." walking
 * Carlos through DPS → HHSC → Legal Aid → Workforce Solutions over twelve
 * weeks — was the OLD GoWork story. It's depressing and inaccurate. The
 * actual GoWork promise is a SAME-DAY case file: we hand you the PDF
 * today, you take it to a case worker tomorrow, you apply Day 3, you're
 * working this week.
 *
 * The avatar still walks the polyline, but the editorial framing
 * compresses the timeline from 5 weeks to 4 day-stages:
 *   Today — Case file
 *   Tomorrow — Case worker
 *   Day 3 — Apply
 *   This week — Working
 *
 * Visual:
 *   - dark gradient overlay with locked editorial copy + 4 day-stage marks
 *   - Mapbox path-draw layer (extends W2's hidden trace) draws progressively
 *   - Carlos avatar walks along the polyline (rendered as a sibling marker)
 *   - per-leg Trinity Metro highlight (CARLOS_PATH_LEG_ROUTES)
 *
 * Reduced-motion: a static SVG fallback shows the finished path so the
 * editorial moment lands without animation. Audio respects mute.
 */
import { useMemo } from "react";
import type { ReactElement } from "react";
import { t } from "@/lib/i18n";
import { CARLOS_PATH_WAYPOINTS } from "@/lib/wall/paths";
import { buildAvatarPolyline } from "@/lib/wall/avatarPath";
import type { ChapterProps } from "@/lib/wall/chapterContract";

/**
 * Day-stage label keys. Narrative Reset compressed the old 5-week timeline
 * (Week 1/4/8/10/12) to 4 same-day stages: Today, Tomorrow, Day 3, This week.
 */
const DAY_LABEL_KEYS = [
  "wall.chapter07.weekLabel1",
  "wall.chapter07.weekLabel2",
  "wall.chapter07.weekLabel3",
  "wall.chapter07.weekLabel4",
] as const;

/** Day-stage identifiers used as data-day attributes on each timeline mark. */
const TIMELINE_DAYS = ["today", "tomorrow", "day-3", "this-week"] as const;

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/** Renders the 4 day-stage marks (Today, Tomorrow, Day 3, This week). */
function TimelineMarks(): ReactElement {
  return (
    <ol
      data-testid="ch7-timeline"
      className="ch7-timeline"
      aria-label={t("wall.chapter07.aria")}
      style={{
        display: "flex",
        gap: "1.5rem",
        listStyle: "none",
        padding: 0,
        margin: "1.5rem 0 0 0",
        flexWrap: "wrap",
        justifyContent: "center",
      }}
    >
      {TIMELINE_DAYS.map((day, idx) => (
        <li
          key={day}
          data-testid={`ch7-timeline-day-${day}`}
          data-day={day}
          style={{
            fontSize: "0.85rem",
            color: "var(--fg-secondary)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            borderLeft: "2px solid var(--accent-amber)",
            paddingLeft: "0.5rem",
          }}
        >
          {t(DAY_LABEL_KEYS[idx])}
        </li>
      ))}
    </ol>
  );
}

/** Static path SVG used when prefers-reduced-motion is active. */
function StaticPathFallback({ progress }: { progress: number }): ReactElement {
  // Render the polyline pre-drawn (no animation).
  const poly = buildAvatarPolyline();
  const coords = poly.coordinates;
  const lngs = coords.map((c) => c[0]);
  const lats = coords.map((c) => c[1]);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const W = 320;
  const H = 200;
  const padX = 16;
  const padY = 16;
  const sx = (lng: number) =>
    padX + ((lng - minLng) / Math.max(1e-9, maxLng - minLng)) * (W - padX * 2);
  const sy = (lat: number) =>
    H - padY - ((lat - minLat) / Math.max(1e-9, maxLat - minLat)) * (H - padY * 2);
  const d = coords
    .map((c, i) => `${i === 0 ? "M" : "L"}${sx(c[0]).toFixed(1)} ${sy(c[1]).toFixed(1)}`)
    .join(" ");
  return (
    <svg
      data-testid="ch7-static-path-svg"
      data-progress={progress.toFixed(3)}
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="160"
      role="img"
      aria-label={t("wall.chapter07.body")}
      focusable="false"
      style={{ marginTop: "1rem" }}
    >
      <path
        d={d}
        fill="none"
        stroke="var(--accent-amber)"
        strokeWidth={3}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {coords.map((c, i) => (
        <circle
          key={`stop-${i}`}
          cx={sx(c[0])}
          cy={sy(c[1])}
          r={5}
          fill="var(--accent-amber)"
        />
      ))}
    </svg>
  );
}

export function Chapter07ThePath(props: ChapterProps): ReactElement {
  const { progress, reducedMotion = false } = props;
  const clamped = useMemo(() => clamp01(progress), [progress]);
  const waypointCount = CARLOS_PATH_WAYPOINTS.length;

  return (
    <section
      data-testid="chapter07-the-path"
      data-chapter="07"
      data-chapter-id="path"
      data-progress={clamped.toFixed(3)}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      data-waypoint-count={String(waypointCount)}
      aria-labelledby="chapter07-title"
      className="chapter07-the-path relative flex min-h-screen flex-col items-center justify-center px-6 py-12"
      style={{
        position: "relative",
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 88%, transparent) 0%, color-mix(in oklch, var(--bg-base) 70%, transparent) 100%)",
      }}
    >
      <div
        style={{
          maxWidth: "44rem",
          padding: "1.5rem 2rem",
          color: "var(--fg-primary)",
          background: "color-mix(in oklch, var(--bg-base) 80%, transparent)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(8px)",
        }}
      >
        <h2
          id="chapter07-title"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(1.5rem, 3vw, 2.25rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.15,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter07.title")}
        </h2>
        <p
          data-testid="ch7-hero"
          style={{
            marginTop: "1rem",
            fontSize: "1.0625rem",
            lineHeight: 1.65,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter07.hero")}
        </p>
        <p
          data-testid="ch7-body"
          style={{
            marginTop: "0.75rem",
            fontSize: "0.95rem",
            lineHeight: 1.6,
            color: "var(--fg-secondary)",
          }}
        >
          {t("wall.chapter07.body")}
        </p>
        <TimelineMarks />
        {reducedMotion ? <StaticPathFallback progress={clamped} /> : null}
      </div>
    </section>
  );
}

export default Chapter07ThePath;
