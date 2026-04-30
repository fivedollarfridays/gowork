/**
 * Spotlight invention 1 — structured logger (lib/wall/log.ts).
 *
 * Pipes through error-reporter for warn/error so production telemetry
 * captures both diagnostic events and crashes through the same PII-scrubbed
 * sink. `info`/`debug` are dev-only and tree-shake out via NODE_ENV guard.
 *
 * Contract:
 *   - debug/info: console.* in dev, no-op in prod
 *   - warn: console.warn + reporter.report(level: warn)
 *   - error: console.error + reporter.report(level: error)
 *   - All log args are passed through PII scrub before reporting
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("lib/wall/log — structured logger", () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("dev: log.info goes to console.info", async () => {
    vi.stubEnv("NODE_ENV", "development");
    const spy = vi.spyOn(console, "info").mockImplementation(() => {});
    const { log } = await import("../log");
    log.info("hello", { x: 1 });
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("[gowork]"),
      "hello",
      { x: 1 },
    );
    spy.mockRestore();
  });

  it("prod: log.info is a no-op", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const spy = vi.spyOn(console, "info").mockImplementation(() => {});
    const { log } = await import("../log");
    log.info("hello");
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("warn fires console.warn in any env", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const spy = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { log } = await import("../log");
    log.warn("something off");
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it("error fires console.error and is the higher-severity sink", async () => {
    vi.stubEnv("NODE_ENV", "development");
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { log } = await import("../log");
    log.error("crash", new Error("boom"));
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it("withScope returns a logger that prefixes every message", async () => {
    vi.stubEnv("NODE_ENV", "development");
    const spy = vi.spyOn(console, "info").mockImplementation(() => {});
    const { log } = await import("../log");
    const scoped = log.withScope("audio");
    scoped.info("ready");
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("[gowork:audio]"),
      "ready",
    );
    spy.mockRestore();
  });
});
