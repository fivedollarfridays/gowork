"use client";

import { useTranslation } from "@/hooks/useTranslation";
import { useLiveNowFormatted } from "@/hooks/useLiveNowFormatted";

/**
 * PageMeta — sprint/gowork-facelift Driver A.
 *
 * Bottom-right HUD chip showing four mono rows: CITY / CHAPTER / SCROLL /
 * LIGHT. Hidden below 720px viewport via CSS in tokens/layout.css.
 *
 * Stateless — receives `city`, `chapter`, `totalChapters`, `progress`
 * (0..1), and `hour` (0..23) as props so the parent can drive these
 * with `useChapterProgress` + `useScrollProgress` + `useTimeOfDay`
 * without forcing this component to re-subscribe.
 *
 * `pointer-events: none` so the HUD never intercepts a click on the
 * chapter content beneath it.
 */

export interface PageMetaProps {
  /** Display string, e.g. "Fort Worth, TX". */
  city: string;
  /** 1-indexed chapter. */
  chapter: number;
  /** Total chapters (default 8). */
  totalChapters?: number;
  /** 0..1 page scroll progress. */
  progress: number;
  /** 0..23 current hour for the LIGHT label. */
  hour: number;
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

/**
 * Map an hour (0..23) to a light-label translation key.
 *
 * dawn:        5–6
 * morning:     7–10
 * midday:      11–13
 * afternoon:   14–16
 * golden:      17–18
 * dusk:        19–20
 * night:       21–4
 */
export function lightLabelKey(hour: number): string {
  const h = ((hour % 24) + 24) % 24;
  if (h >= 5 && h < 7) return "pageMeta.lightDawn";
  if (h >= 7 && h < 11) return "pageMeta.lightMorning";
  if (h >= 11 && h < 14) return "pageMeta.lightMidday";
  if (h >= 14 && h < 17) return "pageMeta.lightAfternoon";
  if (h >= 17 && h < 19) return "pageMeta.lightGolden";
  if (h >= 19 && h < 21) return "pageMeta.lightDusk";
  return "pageMeta.lightNight";
}

/** Replace `{count}` / `{when}` placeholders in a translation string. */
function fillPlaceholders(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(/\{(\w+)\}/g, (_, key) =>
    values[key] !== undefined ? String(values[key]) : `{${key}}`,
  );
}

export function PageMeta({
  city,
  chapter,
  totalChapters = 8,
  progress,
  hour,
}: PageMetaProps): JSX.Element {
  const { t, locale } = useTranslation();
  const scrollPct = Math.round(clamp01(progress) * 100);
  const lightLabel = t(lightLabelKey(hour));
  const live = useLiveNowFormatted(locale === "es" ? "es-MX" : "en-US");
  const liveSessions = fillPlaceholders(t("pageMeta.liveSessions"), {
    count: live.sessionCount,
  });
  const liveCalibrated = fillPlaceholders(t("pageMeta.liveCalibrated"), {
    when: live.lastCalibratedRelative,
  });

  return (
    <aside
      role="complementary"
      aria-label="Page meta"
      data-page-meta
      className="page-meta hidden md:block fixed right-8 bottom-7 z-[95]"
      style={{
        pointerEvents: "none",
        color: "var(--fg-muted)",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      }}
    >
      <dl className="flex flex-col gap-1 text-[11px] tracking-wider items-end m-0">
        <div className="flex gap-2">
          <dt className="opacity-70">{t("pageMeta.city")}:</dt>
          <dd className="m-0" style={{ color: "var(--fg-secondary)" }}>
            {city}
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="opacity-70">{t("pageMeta.chapter")}:</dt>
          <dd className="m-0" style={{ color: "var(--fg-secondary)" }}>
            {pad2(chapter)} / {pad2(totalChapters)}
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="opacity-70">{t("pageMeta.scroll")}:</dt>
          <dd className="m-0" style={{ color: "var(--fg-secondary)" }}>
            {scrollPct}%
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="opacity-70">{t("pageMeta.light")}:</dt>
          <dd className="m-0" style={{ color: "var(--accent-amber)" }}>
            {lightLabel}
          </dd>
        </div>
        <div className="flex gap-2" data-page-meta-live>
          <dt className="opacity-70">{t("pageMeta.live")}</dt>
          <dd
            className="m-0"
            style={{ color: "var(--status-positive, var(--accent-cyan))" }}
          >
            {liveSessions} · {liveCalibrated}
          </dd>
        </div>
      </dl>
    </aside>
  );
}
