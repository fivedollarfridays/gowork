"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.42 — Reusable empty-state with branded line-art.
 *
 * Per the dispatch, NO stock illustrations : the line-art is inline SVG
 * drawn in code. The mark echoes the brand mark — a partial G arc with
 * a horizontal cyan path-line — but tonally muted (lower opacity) so it
 * reads as "waiting to be filled" rather than as a promotional logo.
 *
 * Defaults pull from i18n keys edge.empty.title / edge.empty.body.
 * Consumers can override either with the `title` / `body` props.
 */
export interface EmptyStateProps {
  title?: string;
  body?: string;
}

export function EmptyState({ title, body }: EmptyStateProps): JSX.Element {
  const { t } = useTranslation();
  const headline = title ?? t("edge.empty.title");
  const detail = body ?? t("edge.empty.body");
  return (
    <div
      role="region"
      aria-label={headline}
      data-edge-state="empty"
      className="mx-auto flex max-w-md flex-col items-center justify-center gap-4 px-6 py-12 text-center"
    >
      <svg
        viewBox="0 0 64 64"
        role="img"
        aria-hidden="true"
        className="h-16 w-16"
      >
        <g
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.4"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M 56 32 A 24 24 0 1 0 32 56" />
        </g>
        <line
          x1="32"
          y1="32"
          x2="60"
          y2="32"
          stroke="#22D3EE"
          strokeOpacity="0.55"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
      <h2 className="text-xl font-semibold tracking-tight">{headline}</h2>
      <p className="text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}
