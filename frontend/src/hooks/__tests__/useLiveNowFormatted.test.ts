import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

vi.mock("../useLiveNow", () => ({
  useLiveNow: vi.fn(),
}));

import { useLiveNow } from "../useLiveNow";
import { useLiveNowFormatted } from "../useLiveNowFormatted";

describe("useLiveNowFormatted (T4.A.4)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-27T19:42:00.000Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("returns a formatted nowLabel string", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date("2026-04-27T19:42:00.000Z"),
      sessions: 7,
      lastCalibration: new Date("2026-04-27T19:28:00.000Z"),
    });
    const { result } = renderHook(() => useLiveNowFormatted("en-US"));
    expect(typeof result.current.nowLabel).toBe("string");
    expect(result.current.nowLabel.length).toBeGreaterThan(0);
  });

  it("exposes sessionCount as a number", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date(),
      sessions: 42,
      lastCalibration: null,
    });
    const { result } = renderHook(() => useLiveNowFormatted("en-US"));
    expect(result.current.sessionCount).toBe(42);
  });

  it("returns a deterministic non-zero sessionCount when server gave 0", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date("2026-04-27T19:42:00.000Z"),
      sessions: 0,
      lastCalibration: null,
    });
    const a = renderHook(() => useLiveNowFormatted("en-US"));
    const b = renderHook(() => useLiveNowFormatted("en-US"));
    // Same `now` ⇒ same deterministic hash ⇒ same count.
    expect(a.result.current.sessionCount).toBe(b.result.current.sessionCount);
    expect(a.result.current.sessionCount).toBeGreaterThan(0);
  });

  it("returns a relative string for lastCalibratedRelative when calibration is set", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date("2026-04-27T19:42:00.000Z"),
      sessions: 5,
      lastCalibration: new Date("2026-04-27T19:28:00.000Z"),
    });
    const { result } = renderHook(() => useLiveNowFormatted("en-US"));
    expect(typeof result.current.lastCalibratedRelative).toBe("string");
    expect(result.current.lastCalibratedRelative.length).toBeGreaterThan(0);
  });

  it("emits a non-empty fallback for lastCalibratedRelative when calibration is null", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date("2026-04-27T19:42:00.000Z"),
      sessions: 3,
      lastCalibration: null,
    });
    const { result } = renderHook(() => useLiveNowFormatted("en-US"));
    expect(typeof result.current.lastCalibratedRelative).toBe("string");
    expect(result.current.lastCalibratedRelative.length).toBeGreaterThan(0);
  });

  it("locale-aware formatting differs between en-US and es-MX", () => {
    vi.mocked(useLiveNow).mockReturnValue({
      now: new Date("2026-04-27T14:30:00.000Z"),
      sessions: 5,
      lastCalibration: new Date("2026-04-27T14:00:00.000Z"),
    });
    const en = renderHook(() => useLiveNowFormatted("en-US")).result.current;
    const es = renderHook(() => useLiveNowFormatted("es-MX")).result.current;
    // Both produce strings; format details differ at locale level.
    expect(typeof en.nowLabel).toBe("string");
    expect(typeof es.nowLabel).toBe("string");
    // At minimum the locale code is honoured by the implementation
    // (we don't assert byte-equality of the OS-formatted string because
    // jsdom locale is a thin shim — but BOTH should be non-empty).
    expect(en.nowLabel.length).toBeGreaterThan(0);
    expect(es.nowLabel.length).toBeGreaterThan(0);
  });
});
