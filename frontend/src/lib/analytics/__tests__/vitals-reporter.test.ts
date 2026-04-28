/**
 * vitals-reporter — environment-aware sink for web-vitals metrics (T1.79).
 *
 * Dev: console.log. Prod (no endpoint set): silent no-op. Prod (endpoint
 * configured via VITALS_ENDPOINT env): POST JSON via fetch.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("vitals-reporter — env-driven dispatch", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("development: logs to console with a [vitals] prefix", async () => {
    vi.stubEnv("NODE_ENV", "development");
    const logSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    const { reportVitals } = await import("../vitals-reporter");
    reportVitals({ name: "LCP", value: 1500, id: "v-lcp" });
    expect(logSpy).toHaveBeenCalledWith(
      expect.stringContaining("[vitals]"),
      expect.objectContaining({ name: "LCP", value: 1500 }),
    );
    logSpy.mockRestore();
  });

  it("production with no endpoint: no-op (silent, no fetch)", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 200 }),
    );
    const { reportVitals } = await import("../vitals-reporter");
    reportVitals({ name: "LCP", value: 1500, id: "v-lcp" });
    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("production with endpoint: POST JSON to /api/vitals/ingest", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_VITALS_ENDPOINT", "/api/vitals/ingest");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 200 }),
    );
    const { reportVitals } = await import("../vitals-reporter");
    reportVitals({ name: "CLS", value: 0.05, id: "v-cls" });
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/vitals/ingest",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "content-type": "application/json",
        }),
      }),
    );
    fetchSpy.mockRestore();
  });

  it("production: a fetch failure does not throw (silent for now)", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_VITALS_ENDPOINT", "/api/vitals/ingest");
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new Error("network down"),
    );
    const { reportVitals } = await import("../vitals-reporter");
    expect(() =>
      reportVitals({ name: "INP", value: 80, id: "v-inp" }),
    ).not.toThrow();
    fetchSpy.mockRestore();
  });
});
