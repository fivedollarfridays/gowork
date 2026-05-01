"use client";

import { useState } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { ChapterRailTooltip } from "./ChapterRailTooltip";

/**
 * ChapterRail — sprint/gowork-facelift Driver A. Polish-2 T3 adds tooltip preview.
 *
 * Fixed-left vertical chapter list with 8 ticks + a 60px progress bar
 * that fills cyan→amber as the page scrolls. Hidden below 1100px viewport
 * via the `chapter-rail--hidden` media query in tokens/layout.css.
 *
 * Stateless wrt scroll — receives `activeChapter` (1..8) and `progress` (0..1)
 * as props. Owns local hover/focus state for the chapter preview tooltip
 * (T3): the tooltip slides out on mouseenter or focus and disappears on
 * mouseleave or blur.
 *
 * Active tick gets the cyan accent + 1.08x scale + a gradient marker bar
 * to the left. Click on any tick smooth-scrolls to the corresponding
 * chapter anchor (`#chapter-N`).
 */

export interface ChapterRailProps {
  /** 1-indexed active chapter (1..8). */
  activeChapter: number;
  /** 0..1 total page scroll progress. */
  progress: number;
}

interface ChapterRailEntry {
  id: number;
  labelKey: string;
  anchor: string;
  /** Filename (under /home/chapter-thumbs/) for the preview tooltip. */
  thumbnail: string;
}

// polish-3 fix — anchors use the actual section ids (`chapter-01`,
// not `chapter-1`). The leading-zero format matches the JSX in each
// chapter component; the prior single-digit format silently broke the
// click-to-scroll behavior.
const CHAPTERS: ReadonlyArray<ChapterRailEntry> = [
  { id: 1, labelKey: "chapterRail.ch1", anchor: "#chapter-01", thumbnail: "01-hero.jpg" },
  { id: 2, labelKey: "chapterRail.ch2", anchor: "#chapter-02", thumbnail: "02-the-numbers.jpg" },
  { id: 3, labelKey: "chapterRail.ch3", anchor: "#chapter-03", thumbnail: "03-meet-carlos.jpg" },
  { id: 4, labelKey: "chapterRail.ch4", anchor: "#chapter-04", thumbnail: "04-mapbox-detailed-v2.jpg" },
  { id: 5, labelKey: "chapterRail.ch5", anchor: "#chapter-05", thumbnail: "05-the-plan.jpg" },
  { id: 6, labelKey: "chapterRail.ch6", anchor: "#chapter-06", thumbnail: "06-open-jobs.jpg" },
  { id: 7, labelKey: "chapterRail.ch7", anchor: "#chapter-07", thumbnail: "07-wage-cliff.jpg" },
  { id: 8, labelKey: "chapterRail.ch8", anchor: "#chapter-08", thumbnail: "08-manifesto.jpg" },
];

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

export function ChapterRail({ activeChapter, progress }: ChapterRailProps): JSX.Element {
  const { t } = useTranslation();
  const fillPct = `${(clamp01(progress) * 100).toFixed(2)}%`;
  const [hoveredChapter, setHoveredChapter] = useState<number | null>(null);
  // Per Kevin's polish ask — the rail used to permanently stick out with
  // the full chapter labels. Now it defaults to a tucked-edge view (just
  // the tick markers + active-chapter hint) and expands the numbers +
  // labels on rail-hover. `railHovered` is independent of `hoveredChapter`
  // so the rail stays expanded while the user is moving between ticks.
  const [railHovered, setRailHovered] = useState<boolean>(false);

  return (
    <nav
      aria-label={t("chapterRail.label")}
      data-chapter-rail
      data-rail-expanded={railHovered}
      onMouseEnter={() => setRailHovered(true)}
      onMouseLeave={() => {
        setRailHovered(false);
        setHoveredChapter(null);
      }}
      className="chapter-rail fixed left-8 top-1/2 -translate-y-1/2 z-[95] hidden xl:flex flex-col gap-4 items-start"
      style={{ pointerEvents: "auto" }}
    >
      <ol className="flex flex-col gap-3 list-none p-0 m-0">
        {CHAPTERS.map((c) => {
          const isActive = c.id === activeChapter;
          const isHovered = hoveredChapter === c.id;
          return (
            <li
              key={c.id}
              data-chapter-id={c.id}
              className="relative"
              onMouseEnter={() => setHoveredChapter(c.id)}
              onMouseLeave={() => setHoveredChapter((id) => (id === c.id ? null : id))}
            >
              <a
                href={c.anchor}
                aria-current={isActive ? "true" : undefined}
                aria-describedby={isHovered ? `chapter-rail-tip-${c.id}` : undefined}
                className="chapter-rail__tick group flex items-center gap-3 transition-transform"
                style={{
                  color: isActive ? "var(--accent-cyan)" : "var(--fg-muted)",
                  transform: isActive ? "scale(1.08)" : "scale(1)",
                  transformOrigin: "left center",
                }}
                onFocus={() => setHoveredChapter(c.id)}
                onBlur={() =>
                  setHoveredChapter((id) => (id === c.id ? null : id))
                }
              >
                <span
                  aria-hidden="true"
                  data-chapter-marker
                  className="block w-6 h-[2px] rounded-full transition-all"
                  style={{
                    background: isActive
                      ? "linear-gradient(to right, var(--accent-cyan), var(--accent-amber))"
                      : "color-mix(in oklch, var(--fg-primary), transparent 80%)",
                    width: isActive ? "32px" : "16px",
                  }}
                />
                <span
                  data-chapter-number
                  className="font-mono text-[11px] tracking-wider transition-opacity duration-200"
                  style={{
                    opacity: railHovered || isActive ? 1 : 0,
                    pointerEvents: railHovered || isActive ? "auto" : "none",
                  }}
                >
                  {pad2(c.id)}
                </span>
                <span
                  className="text-xs font-medium whitespace-nowrap transition-opacity duration-200"
                  style={{
                    opacity: railHovered ? 1 : 0,
                    pointerEvents: railHovered ? "auto" : "none",
                  }}
                >
                  {t(c.labelKey)}
                </span>
              </a>
              {isHovered ? (
                <ChapterRailTooltip
                  chapterId={c.id}
                  eyebrow={t(c.labelKey)}
                  thumbnailSrc={`/home/chapter-thumbs/${c.thumbnail}`}
                  alt={`${t("chapterRail.tooltip.altPrefix")} ${t(c.labelKey)}`}
                />
              ) : null}
            </li>
          );
        })}
      </ol>

      <div
        className="chapter-rail__progress relative ml-4 mt-2 w-[2px] h-[60px] rounded-full overflow-hidden"
        role="progressbar"
        aria-label={t("chapterRail.progressLabel")}
        aria-valuenow={Math.round(clamp01(progress) * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        style={{
          background: "color-mix(in oklch, var(--fg-primary), transparent 90%)",
        }}
      >
        <span
          data-progress-fill
          aria-hidden="true"
          className="absolute left-0 top-0 w-full transition-[height]"
          style={{
            height: fillPct,
            background:
              "linear-gradient(to bottom, var(--accent-cyan), var(--accent-amber))",
          }}
        />
      </div>
    </nav>
  );
}
