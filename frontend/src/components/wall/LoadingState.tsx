"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.43 — Branded skeleton loading state.
 *
 * Per the dispatch, "skeleton screens, NOT spinners. Subtle pulse with
 * --temperature-multiplier respected." The skeleton lines use the
 * `animate-pulse` Tailwind utility (Driver A's globals.css can extend
 * this with a custom keyframe respecting prefers-reduced-motion).
 *
 * Each line carries `data-skeleton-line` so consumers / tests can count
 * them deterministically. The label is read from i18n (edge.loading.label).
 */
export interface LoadingStateProps {
  /** Number of skeleton rows to render. Default: 3. */
  lines?: number;
}

export function LoadingState({ lines = 3 }: LoadingStateProps): JSX.Element {
  const { t } = useTranslation();
  const widths = ["w-11/12", "w-9/12", "w-10/12", "w-8/12", "w-11/12"];
  const rows = Array.from({ length: lines }, (_, i) => widths[i % widths.length]);
  return (
    <div
      role="status"
      aria-busy="true"
      aria-live="polite"
      data-edge-state="loading"
      className="mx-auto flex max-w-xl flex-col gap-3 px-6 py-8"
    >
      <p className="mb-1 text-xs uppercase tracking-widest text-cyan-400">
        {t("edge.loading.label")}
      </p>
      {rows.map((width, idx) => (
        <div
          key={idx}
          data-skeleton-line
          className={`h-3 animate-pulse rounded-full bg-foreground/10 ${width}`}
        />
      ))}
    </div>
  );
}
