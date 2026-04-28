/**
 * T1.79 — useWebVitals + vitals-reporter (Wave 1 carry-over).
 *
 * Captures LCP/CLS/INP/FCP/TTFB and routes them through the configurable
 * reporter. Production: sends to /api/vitals/ingest (no-op until W4 lands
 * the backend). Development: console.log. SSR: no-op.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// Mock web-vitals so we can drive callbacks deterministically.
const onLCP = vi.fn();
const onCLS = vi.fn();
const onINP = vi.fn();
const onFCP = vi.fn();
const onTTFB = vi.fn();

vi.mock("web-vitals", () => ({
  onLCP: (cb: (m: unknown) => void) => onLCP(cb),
  onCLS: (cb: (m: unknown) => void) => onCLS(cb),
  onINP: (cb: (m: unknown) => void) => onINP(cb),
  onFCP: (cb: (m: unknown) => void) => onFCP(cb),
  onTTFB: (cb: (m: unknown) => void) => onTTFB(cb),
}));

import { useWebVitals } from "../useWebVitals";

describe("useWebVitals (T1.79)", () => {
  beforeEach(() => {
    onLCP.mockClear();
    onCLS.mockClear();
    onINP.mockClear();
    onFCP.mockClear();
    onTTFB.mockClear();
  });

  it("subscribes to all five core vitals on mount", () => {
    renderHook(() => useWebVitals());
    expect(onLCP).toHaveBeenCalledTimes(1);
    expect(onCLS).toHaveBeenCalledTimes(1);
    expect(onINP).toHaveBeenCalledTimes(1);
    expect(onFCP).toHaveBeenCalledTimes(1);
    expect(onTTFB).toHaveBeenCalledTimes(1);
  });

  it("invokes the supplied reporter once per metric", () => {
    const reporter = vi.fn();
    renderHook(() => useWebVitals({ reporter }));
    // Each onXxx mock receives a callback — call it with a sample metric.
    const lcpCb = onLCP.mock.calls[0]?.[0] as (m: unknown) => void;
    expect(typeof lcpCb).toBe("function");
    act(() => {
      lcpCb({ name: "LCP", value: 1234, id: "v1-lcp" });
    });
    expect(reporter).toHaveBeenCalledWith({
      name: "LCP",
      value: 1234,
      id: "v1-lcp",
    });
  });

  it("returns the latest captured metrics map", () => {
    const { result } = renderHook(() => useWebVitals());
    const lcpCb = onLCP.mock.calls[0]?.[0] as (m: unknown) => void;
    act(() => {
      lcpCb({ name: "LCP", value: 999, id: "lcp-1" });
    });
    expect(result.current.metrics.LCP).toEqual({
      name: "LCP",
      value: 999,
      id: "lcp-1",
    });
  });
});
