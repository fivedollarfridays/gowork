"use client";

/**
 * W2 Driver C — FormsCounter (T2.41 + T2.45).
 *
 * Renders the Ch5 "47 forms" tally tied to chapter progress. The number is
 * the editorial heart of the Labyrinth chapter — it must be both visually
 * loud (text-7xl tabular amber) and accessible (aria-label names the total).
 *
 * Spotlight invention #1 — `data-cliff`: when the count crosses 30, the
 * counter sets `data-cliff="true"` and the page CSS swings from amber to
 * rose, foreshadowing the W3 Ch6 cliff. The COUNTER itself drives the
 * page's emotional accent. Exactly the same paint that announces "this
 * raise costs you $400" is being prefigured here.
 */
import type { ReactElement } from "react";
import { W2_LABYRINTH_FORM_COUNT } from "@/lib/wall/chapters/deps";

const CLIFF_THRESHOLD = 30;

export interface FormsCounterProps {
  /** Local Ch5 progress 0..1. Driver A's useChapterProgress feeds this. */
  progress: number;
  /** Skip transitions; render the final number instantly. */
  reducedMotion?: boolean;
  /** Optional CSS class for the wrapper (test overrides + page wiring). */
  className?: string;
}

export function FormsCounter({
  progress,
  reducedMotion = false,
  className,
}: FormsCounterProps): ReactElement {
  const clamped = Math.max(0, Math.min(1, progress));
  const value = Math.round(clamped * W2_LABYRINTH_FORM_COUNT);
  const cliff = value >= CLIFF_THRESHOLD;

  const wrapperClass = [
    "forms-counter",
    "flex flex-col items-center gap-2",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  const valueClass = [
    "forms-counter__value",
    "text-7xl",
    "tabular-nums",
    "font-semibold",
    cliff ? "text-[var(--accent-rose)]" : "text-[var(--accent-amber)]",
    reducedMotion ? "" : "transition-colors duration-500",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      data-testid="forms-counter"
      data-cliff={cliff ? "true" : "false"}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      className={wrapperClass}
      aria-label={`${value} of ${W2_LABYRINTH_FORM_COUNT} forms`}
      role="status"
    >
      <span data-testid="forms-counter-value" className={valueClass}>
        {value}
      </span>
    </div>
  );
}
