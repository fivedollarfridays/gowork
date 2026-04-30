/**
 * Vitals reporter (T1.79).
 *
 * Single sink for web-vitals metrics. Behaviour by environment:
 *   - dev: `console.log("[vitals]", metric)`
 *   - prod, no NEXT_PUBLIC_VITALS_ENDPOINT: no-op (silent until W4 lands
 *     the backend)
 *   - prod, endpoint configured: POST JSON, swallow failures
 *
 * The reporter is intentionally fire-and-forget; we never block the
 * page on telemetry. Errors are logged at warn level in dev only.
 */

export interface VitalMetric {
  /** Metric key (LCP|CLS|INP|FCP|TTFB) */
  name: string;
  /** Current measured value (ms or ratio). */
  value: number;
  /** Unique id for the metric instance (web-vitals provides). */
  id: string;
  /** Optional rating bucket (good|needs-improvement|poor). */
  rating?: string;
}

function getEndpoint(): string | null {
  const e = process.env.NEXT_PUBLIC_VITALS_ENDPOINT;
  if (typeof e === "string" && e.length > 0) return e;
  return null;
}

/** Send a metric to the configured sink. Fire-and-forget. */
export function reportVitals(metric: VitalMetric): void {
  if (process.env.NODE_ENV === "development") {
    // eslint-disable-next-line no-console
    console.log("[vitals]", metric);
    return;
  }

  if (process.env.NODE_ENV !== "production") return;

  const endpoint = getEndpoint();
  if (!endpoint) return;

  try {
    const result = fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(metric),
      keepalive: true,
    });
    // Swallow failures — telemetry should never throw.
    if (result && typeof (result as Promise<unknown>).then === "function") {
      (result as Promise<unknown>).catch(() => {
        /* ignore */
      });
    }
  } catch {
    /* ignore */
  }
}
