"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.44 — Per-component error fallback.
 *
 * Designed for use inside per-chapter ErrorBoundary fallbacks (Wave 4 +
 * W2 chapter shells). Re-uses the `edge.500.*` copy bank so the wall's
 * "Something stalled / We're calibrating" motif extends from the global
 * error page down to component-local failures.
 *
 * If `onRetry` is omitted, the retry CTA is hidden (some failures cannot
 * be retried client-side).
 */
export interface ErrorStateProps {
  onRetry?: () => void;
  title?: string;
  body?: string;
}

export function ErrorState({
  onRetry,
  title,
  body,
}: ErrorStateProps): JSX.Element {
  const { t } = useTranslation();
  const headline = title ?? t("edge.500.title");
  const detail = body ?? t("edge.500.body");
  return (
    <div
      role="alert"
      data-edge-state="error"
      className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-lg border border-accent/30 bg-accent/5 px-6 py-6 text-center"
    >
      <h3 className="text-lg font-semibold tracking-tight">{headline}</h3>
      <p className="text-sm text-muted-foreground">{detail}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 inline-flex items-center justify-center rounded-full bg-cyan-400 px-5 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          {t("edge.500.cta")}
        </button>
      ) : null}
    </div>
  );
}
