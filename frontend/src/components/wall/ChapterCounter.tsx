"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.52 — Chapter counter (01/10 format, tabular nums).
 *
 * Presentational : the host (Driver B's chapter-state hook in W2) owns
 * the source of truth and passes `current` + `total` as props. The
 * component pads to a two-digit string ("01", "07", "10") and renders
 * with `tabular-nums` so the slash-and-digits sequence does not jitter
 * as the chapter advances.
 *
 * The aria-label is sourced from the i18n catalog (header.chapterCounter
 * .aria) so screen-reader callers hear "Current chapter, of ten" in
 * their locale.
 */
export interface ChapterCounterProps {
  current: number;
  total: number;
}

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

export function ChapterCounter({
  current,
  total,
}: ChapterCounterProps): JSX.Element {
  const { t } = useTranslation();
  return (
    <div
      role="status"
      aria-label={t("header.chapterCounter.aria")}
      aria-current="step"
      data-counter
      className="flex items-center gap-1 font-mono text-sm tabular-nums tracking-wider text-foreground/80"
    >
      <span className="text-foreground">{pad(current)}</span>
      <span aria-hidden="true" className="text-foreground/40">
        /
      </span>
      <span className="text-foreground/60">{pad(total)}</span>
    </div>
  );
}
