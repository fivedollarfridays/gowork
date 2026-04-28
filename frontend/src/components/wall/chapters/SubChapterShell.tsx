"use client";

/**
 * W2 Driver C — shared sub-chapter shell for Ch4 (4a–4d).
 *
 * Each Ch4 sub-chapter is identical in shape: a stat band on the left,
 * an editorial detail on the right, an optional pull-quote underneath,
 * and a polite ARIA narration string. Extracting the shell keeps each
 * sub-chapter file <50 lines and lets the editorial copy own the whole
 * file.
 *
 * Spotlight invention #2 — `data-emphasis-tint`: the shell accepts a
 * `tint` token ("amber" | "rose" | "cyan") and forwards it as a data
 * attribute. The W3 cliff layer can read this to know which barrier the
 * user is currently hearing about. Sibling W3 chapters get a free
 * "remember 4c" hook without polluting our import surface.
 */
import type { ReactElement, ReactNode } from "react";
import { t } from "@/lib/i18n";

export type SubChapterTint = "amber" | "rose" | "cyan";

export interface SubChapterShellProps {
  /** Sub-chapter id, e.g. "4a", "4b". Drives data-subchapter + a11y id. */
  subChapterId: string;
  /** i18n key prefix, e.g. "wall.chapter04a". */
  i18nPrefix: string;
  /** Local progress 0..1 inside this sub-chapter (forwarded for tests). */
  progress: number;
  /** Visual tint for the stat band + pull-quote border. Defaults to amber. */
  tint?: SubChapterTint;
  /** Optional extra slot rendered under the editorial — usually a quote. */
  extras?: ReactNode;
}

export function SubChapterShell({
  subChapterId,
  i18nPrefix,
  progress,
  tint = "amber",
  extras,
}: SubChapterShellProps): ReactElement {
  const title = t(`${i18nPrefix}.title`);
  const detail = t(`${i18nPrefix}.detail`);
  const statValue = t(`${i18nPrefix}.statValue`);
  const statLabel = t(`${i18nPrefix}.statLabel`);
  const ariaText = t(`${i18nPrefix}.aria`);
  const pullquote = t(`${i18nPrefix}.pullquote`);

  // Map tint → CSS variable. Amber is the chapter-4 default; rose comes
  // online when 4d hands off to Ch5 (forms-counter) per Spotlight wiring.
  const tintVar =
    tint === "rose"
      ? "var(--accent-rose)"
      : tint === "cyan"
        ? "var(--accent-cyan)"
        : "var(--accent-amber)";

  return (
    <section
      data-testid="ch4-subchapter"
      data-subchapter={subChapterId}
      data-emphasis-tint={tint}
      data-progress={progress.toFixed(2)}
      aria-labelledby={`ch4-${subChapterId}-title`}
      className="ch4-subchapter relative flex max-w-3xl flex-col gap-6 px-6 py-8"
    >
      <h2
        id={`ch4-${subChapterId}-title`}
        className="ch4-subchapter__title text-3xl font-semibold tracking-tight"
        style={{ color: tintVar }}
      >
        {title}
      </h2>

      <div className="ch4-subchapter__row flex flex-col gap-6 md:flex-row md:items-baseline">
        <div
          className="ch4-stat-band flex flex-col items-start"
          data-testid="ch4-stat-band"
        >
          <span
            data-testid="ch4-stat-value"
            className="ch4-stat-band__value text-5xl font-semibold tabular-nums"
            style={{ color: tintVar }}
          >
            {statValue}
          </span>
          <span className="ch4-stat-band__label text-sm uppercase tracking-wide text-[var(--fg-secondary)]">
            {statLabel}
          </span>
        </div>

        <p
          data-testid="ch4-detail"
          className="ch4-subchapter__detail text-lg leading-relaxed text-[var(--fg-primary)] md:text-xl"
        >
          {detail}
        </p>
      </div>

      {pullquote && pullquote !== `${i18nPrefix}.pullquote` ? (
        <blockquote
          data-testid="ch4-pullquote"
          className="editorial-pullquote"
          style={{ borderLeftColor: tintVar }}
        >
          {pullquote}
        </blockquote>
      ) : null}

      {extras}

      <span className="sr-only" data-testid="ch4-aria-narration">
        {ariaText}
      </span>
    </section>
  );
}
