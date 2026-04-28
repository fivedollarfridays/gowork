"use client";

import { useEffect, useRef, useState } from "react";
import { onLCP, onCLS, onINP, onFCP, onTTFB } from "web-vitals";
import {
  reportVitals,
  type VitalMetric,
} from "@/lib/analytics/vitals-reporter";

/**
 * useWebVitals (T1.79).
 *
 * Subscribes to the five core Web Vitals (LCP, CLS, INP, FCP, TTFB) and
 * routes each emission through the configured reporter. The hook returns
 * the latest captured metrics map for components that want to surface
 * RUM data (dev panel, e2e debugging).
 *
 * Subscriptions install once on mount; web-vitals callbacks fire over the
 * page lifetime as the metrics stabilize.
 */
export interface UseWebVitalsOptions {
  /** Override the default reporter (defaults to vitals-reporter.reportVitals). */
  reporter?: (metric: VitalMetric) => void;
}

export interface UseWebVitalsResult {
  metrics: Partial<Record<string, VitalMetric>>;
}

export function useWebVitals(
  options: UseWebVitalsOptions = {},
): UseWebVitalsResult {
  const reporter = options.reporter ?? reportVitals;
  const reporterRef = useRef(reporter);
  reporterRef.current = reporter;
  const [metrics, setMetrics] = useState<Partial<Record<string, VitalMetric>>>(
    {},
  );

  useEffect(() => {
    const handle = (metric: VitalMetric) => {
      reporterRef.current(metric);
      setMetrics((prev) => ({ ...prev, [metric.name]: metric }));
    };
    onLCP(handle);
    onCLS(handle);
    onINP(handle);
    onFCP(handle);
    onTTFB(handle);
  }, []);

  return { metrics };
}
