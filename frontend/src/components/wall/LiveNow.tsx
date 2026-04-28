"use client";

import { useState, type CSSProperties, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useLiveNowFormatted } from "@/hooks/useLiveNowFormatted";

/**
 * T4.A.5 — LiveNow.
 *
 * Header widget showing live "as of right now" telemetry:
 *   - the current clock time (locale-formatted)
 *   - a small session count badge (server count or deterministic stub)
 *   - the relative time since last navigator-data calibration
 *
 * Visible on chapters 2-10. Hidden on Ch1 hero so the question can
 * breathe. Visibility is controlled by the parent (Header) via the
 * `hidden` prop — this component does not subscribe to chapter state
 * itself (single-source-of-truth: WallContainer is the chapter authority).
 *
 * a11y: the root is an aria-live=polite region so screen readers
 * announce updates without interrupting the user.
 */

interface LiveNowProps {
  /** Hide the widget (Ch1 hero). Renders null when true. */
  hidden?: boolean;
  /** BCP 47 locale forwarded to `useLiveNowFormatted`. */
  locale?: string;
}

const ROOT_STYLE: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.5rem",
  fontSize: "0.75rem",
  color: "var(--fg-secondary, var(--fg-primary))",
  fontVariantNumeric: "tabular-nums",
};

const SESSION_STYLE: CSSProperties = {
  fontVariantNumeric: "tabular-nums",
  fontWeight: 600,
  color: "var(--accent-current, var(--fg-primary))",
};

const SEPARATOR_STYLE: CSSProperties = {
  opacity: 0.4,
};

function LiveNowInner({ locale }: { locale: string }) {
  const { nowLabel, sessionCount, lastCalibratedRelative } = useLiveNowFormatted(locale);
  return (
    <div
      data-testid="live-now"
      aria-live="polite"
      aria-atomic="true"
      className="font-mono-data tabular-nums"
      style={ROOT_STYLE}
    >
      <span data-testid="live-now-time">{nowLabel}</span>
      <span style={SEPARATOR_STYLE}>·</span>
      <span data-testid="live-now-sessions" style={SESSION_STYLE}>
        {sessionCount} live
      </span>
      <span style={SEPARATOR_STYLE}>·</span>
      <span data-testid="live-now-calibration">
        cal. {lastCalibratedRelative}
      </span>
    </div>
  );
}

/** Wraps LiveNowInner with its own QueryClient when none is provided
 *  by the app shell. Always mounts a local client at the LiveNow
 *  boundary; if the app already provides a QueryClient higher in the
 *  tree, this inner provider becomes the nearest scope for LiveNow's
 *  /api/now polling, which is exactly what we want — Live Now's poll
 *  cadence stays isolated from the parent app's queries.
 */
function LiveNowBoundary({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: false, staleTime: 0 } },
      }),
  );
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

export function LiveNow({ hidden = false, locale = "en-US" }: LiveNowProps = {}) {
  if (hidden) return null;
  return (
    <LiveNowBoundary>
      <LiveNowInner locale={locale} />
    </LiveNowBoundary>
  );
}

