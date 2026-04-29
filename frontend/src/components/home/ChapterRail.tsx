"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * ChapterRail — sprint/gowork-facelift Driver A.
 *
 * Fixed-left vertical chapter list with 8 ticks + a 60px progress bar
 * that fills cyan→amber as the page scrolls. Hidden below 1100px viewport
 * via the `chapter-rail--hidden` media query in tokens/layout.css.
 *
 * Stateless — receives `activeChapter` (1..8) and `progress` (0..1) as
 * props so the parent can drive both with `useChapterProgress` +
 * `useScrollProgress` without forcing this component to re-subscribe.
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

const CHAPTERS: ReadonlyArray<{ id: number; labelKey: string; anchor: string }> = [
  { id: 1, labelKey: "chapterRail.ch1", anchor: "#chapter-1" },
  { id: 2, labelKey: "chapterRail.ch2", anchor: "#chapter-2" },
  { id: 3, labelKey: "chapterRail.ch3", anchor: "#chapter-3" },
  { id: 4, labelKey: "chapterRail.ch4", anchor: "#chapter-4" },
  { id: 5, labelKey: "chapterRail.ch5", anchor: "#chapter-5" },
  { id: 6, labelKey: "chapterRail.ch6", anchor: "#chapter-6" },
  { id: 7, labelKey: "chapterRail.ch7", anchor: "#chapter-7" },
  { id: 8, labelKey: "chapterRail.ch8", anchor: "#chapter-8" },
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

  return (
    <nav
      aria-label={t("chapterRail.label")}
      data-chapter-rail
      className="chapter-rail fixed left-8 top-1/2 -translate-y-1/2 z-[95] hidden xl:flex flex-col gap-4 items-start"
      style={{ pointerEvents: "auto" }}
    >
      <ol className="flex flex-col gap-3 list-none p-0 m-0">
        {CHAPTERS.map((c) => {
          const isActive = c.id === activeChapter;
          return (
            <li key={c.id} data-chapter-id={c.id}>
              <a
                href={c.anchor}
                aria-current={isActive ? "true" : undefined}
                className="chapter-rail__tick group flex items-center gap-3 transition-transform"
                style={{
                  color: isActive ? "var(--accent-cyan)" : "var(--fg-muted)",
                  transform: isActive ? "scale(1.08)" : "scale(1)",
                  transformOrigin: "left center",
                }}
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
                  className="font-mono text-[11px] tracking-wider"
                >
                  {pad2(c.id)}
                </span>
                <span className="text-xs font-medium whitespace-nowrap">
                  {t(c.labelKey)}
                </span>
              </a>
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
