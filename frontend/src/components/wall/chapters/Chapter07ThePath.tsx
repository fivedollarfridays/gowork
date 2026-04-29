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
import { CarlosAvatar } from "../CarlosAvatar";

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

/**
 * Avatar overlay (T-Render.4) — a 2D projection of the 5-waypoint polyline
 * with Carlos walking along it as progress increases. This is rendered as
 * an absolute-positioned SVG overlay inside the chapter card so the avatar
 * is visible whether or not Mapbox is mounted (independence). The polyline
 * itself uses stroke-dasharray for a progressive draw; the avatar's left/top
 * position interpolates linearly from waypoint[0] → waypoint[N-1].
 */
function Ch7AvatarOverlay({
  progress,
  reducedMotion,
}: {
  progress: number;
  reducedMotion: boolean;
}): ReactElement {
  const poly = buildAvatarPolyline();
  const coords = poly.coordinates;
  const lngs = coords.map((c) => c[0]);
  const lats = coords.map((c) => c[1]);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const W = 800;
  const H = 320;
  const padX = 48;
  const padY = 32;
  const sx = (lng: number) =>
    padX + ((lng - minLng) / Math.max(1e-9, maxLng - minLng)) * (W - padX * 2);
  const sy = (lat: number) =>
    H - padY - ((lat - minLat) / Math.max(1e-9, maxLat - minLat)) * (H - padY * 2);
  const points = coords.map((c) => ({ x: sx(c[0]), y: sy(c[1]) }));
  const d = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");
  // Position avatar along the projected polyline by progress.
  const N = points.length;
  const tt = Math.max(0, Math.min(1, progress));
  const segIdxFloat = tt * (N - 1);
  const segIdx = Math.min(N - 2, Math.floor(segIdxFloat));
  const localT = segIdxFloat - segIdx;
  const a = points[segIdx];
  const b = points[Math.min(N - 1, segIdx + 1)];
  const avatarX = a.x + (b.x - a.x) * localT;
  const avatarY = a.y + (b.y - a.y) * localT;
  // Stroke-dasharray draw — visible polyline length scales with progress.
  // Approximate length = sum of segment distances.
  const totalLen = points.reduce((acc, p, i) => {
    if (i === 0) return 0;
    const prev = points[i - 1];
    return acc + Math.hypot(p.x - prev.x, p.y - prev.y);
  }, 0);
  const drawn = reducedMotion ? totalLen : totalLen * tt;
  const offset = reducedMotion ? 0 : Math.max(0, totalLen - drawn);

  return (
    <div
      data-testid="ch7-avatar-overlay"
      data-progress={tt.toFixed(3)}
      style={{
        position: "relative",
        marginTop: "1.5rem",
        width: "100%",
        minHeight: 320,
      }}
    >
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height="320"
        aria-hidden="true"
        focusable="false"
        style={{ display: "block" }}
      >
        {/* Background polyline (faint) */}
        <path
          d={d}
          fill="none"
          stroke="var(--accent-amber)"
          strokeWidth={2}
          strokeOpacity={0.25}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Drawn polyline (progressive) */}
        <path
          data-testid="ch7-avatar-path"
          d={d}
          fill="none"
          stroke="var(--accent-cyan)"
          strokeWidth={3.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={totalLen}
          strokeDashoffset={offset}
        />
        {/* Stop dots */}
        {points.map((p, i) => (
          <circle
            key={`stop-${i}`}
            cx={p.x}
            cy={p.y}
            r={8}
            fill="var(--accent-amber)"
            stroke="var(--bg-base)"
            strokeWidth={2}
          />
        ))}
      </svg>
      <div
        data-testid="ch7-avatar-position"
        style={{
          position: "absolute",
          left: `calc(${(avatarX / W) * 100}% - 16px)`,
          top: `calc(${(avatarY / H) * 100}% - 40px)`,
          width: 32,
          height: 48,
          pointerEvents: "none",
          transition: reducedMotion ? "none" : "left 200ms linear, top 200ms linear",
        }}
      >
        <CarlosAvatar progress={tt} reducedMotion={reducedMotion} />
      </div>
    </div>
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
      className="chapter07-the-path relative flex min-h-screen flex-col items-center justify-center px-6 py-16"
      style={{
        position: "relative",
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 70%, transparent) 0%, color-mix(in oklch, var(--bg-base) 60%, transparent) 100%)",
      }}
    >
      <div
        style={{
          // Heroic scale (T-Render.1).
          maxWidth: "min(78vw, 60rem)",
          width: "min(92vw, 60rem)",
          padding: "clamp(2rem, 4vw, 4rem) clamp(1.5rem, 4vw, 3rem)",
          color: "var(--fg-primary)",
          background:
            "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 88%, transparent) 0%, color-mix(in oklch, var(--bg-base) 92%, transparent) 100%)",
          borderRadius: "var(--radius)",
          backdropFilter: "blur(12px) saturate(140%)",
          WebkitBackdropFilter: "blur(12px) saturate(140%)",
          boxShadow:
            "0 24px 80px color-mix(in oklch, var(--bg-base) 60%, transparent)",
        }}
      >
        <h2
          id="chapter07-title"
          style={{
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(2rem, 4vw, 3.5rem)",
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            margin: 0,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter07.title")}
        </h2>
        <p
          data-testid="ch7-hero"
          style={{
            marginTop: "1.25rem",
            fontSize: "clamp(1.0625rem, 1.5vw, 1.375rem)",
            lineHeight: 1.65,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter07.hero")}
        </p>
        <p
          data-testid="ch7-body"
          style={{
            marginTop: "1rem",
            fontSize: "clamp(1rem, 1.3vw, 1.1875rem)",
            lineHeight: 1.6,
            color: "var(--fg-secondary)",
          }}
        >
          {t("wall.chapter07.body")}
        </p>
        <TimelineMarks />
        {/* Mount the avatar overlay (T-Render.4) — visible whether motion is
         *  reduced or not. The avatar walks along the polyline as progress
         *  increases. */}
        <Ch7AvatarOverlay progress={clamped} reducedMotion={reducedMotion} />
        {reducedMotion ? <StaticPathFallback progress={clamped} /> : null}
      </div>
    </section>
  );
}

export default Chapter07ThePath;
