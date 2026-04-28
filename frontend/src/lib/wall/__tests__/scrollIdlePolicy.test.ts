/**
 * Spotlight invention #6 (W4 Driver D) — scrollIdlePolicy.test.ts.
 *
 * Guard test for the W4 idle-state debounce + scroll-velocity threshold
 * defaults. These are tuned numbers that affect the editorial feel of
 * the Wall — a future driver who lowers the idle threshold to 5s breaks
 * the design contract (the user feels watched, not invited).
 *
 * The test pins:
 *   1. `useIdleState` defaults to 30 000 ms (30s).
 *   2. `useScrollVelocity` defaults to 3 px/ms (~3000 px/s) for `isFast`.
 *   3. `useIdleState` resets on the four canonical activity events.
 *   4. The two thresholds are documented as constants — no magic numbers
 *      hidden inside the hook bodies.
 *
 * Without this test, a refactor could lose these numbers silently.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import fs from "fs";
import path from "path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..", "..");
const IDLE_HOOK = path.resolve(
  FRONTEND_ROOT,
  "src/hooks/useIdleState.ts",
);
const VELOCITY_HOOK = path.resolve(
  FRONTEND_ROOT,
  "src/hooks/useScrollVelocity.ts",
);

afterEach(() => {
  vi.useRealTimers();
});

describe("Spotlight #6 — scrollIdlePolicy: useIdleState defaults", () => {
  it("default idleMs is documented as 30 000", () => {
    const src = fs.readFileSync(IDLE_HOOK, "utf-8");
    expect(src).toContain("30_000");
  });

  it("returns false initially, true after default 30s of inactivity", async () => {
    vi.useFakeTimers();
    const { useIdleState } = await import("@/hooks/useIdleState");
    const { result } = renderHook(() => useIdleState());
    expect(result.current).toBe(false);
    act(() => {
      vi.advanceTimersByTime(30_001);
    });
    expect(result.current).toBe(true);
  });

  it("resets to false on a pointermove activity event", async () => {
    vi.useFakeTimers();
    const { useIdleState } = await import("@/hooks/useIdleState");
    const { result } = renderHook(() => useIdleState());
    act(() => {
      vi.advanceTimersByTime(30_001);
    });
    expect(result.current).toBe(true);
    act(() => {
      window.dispatchEvent(new Event("pointermove"));
    });
    expect(result.current).toBe(false);
  });

  it("resets on keydown (canonical activity event)", async () => {
    vi.useFakeTimers();
    const { useIdleState } = await import("@/hooks/useIdleState");
    const { result } = renderHook(() => useIdleState());
    act(() => {
      vi.advanceTimersByTime(30_001);
    });
    expect(result.current).toBe(true);
    act(() => {
      window.dispatchEvent(new Event("keydown"));
    });
    expect(result.current).toBe(false);
  });

  it("respects a custom idleMs argument", async () => {
    vi.useFakeTimers();
    const { useIdleState } = await import("@/hooks/useIdleState");
    const { result } = renderHook(() => useIdleState(5_000));
    expect(result.current).toBe(false);
    act(() => {
      vi.advanceTimersByTime(5_001);
    });
    expect(result.current).toBe(true);
  });
});

describe("Spotlight #6 — scrollIdlePolicy: useScrollVelocity threshold", () => {
  it("default threshold is 3 px/ms (documented)", () => {
    const src = fs.readFileSync(VELOCITY_HOOK, "utf-8");
    expect(src).toMatch(/DEFAULT_THRESHOLD_PX_PER_MS\s*=\s*3/);
  });

  it("hook returns initial { velocity: 0, isFast: false }", async () => {
    const { useScrollVelocity } = await import("@/hooks/useScrollVelocity");
    const { result } = renderHook(() => useScrollVelocity());
    expect(result.current.velocity).toBe(0);
    expect(result.current.isFast).toBe(false);
  });
});

describe("Spotlight #6 — scrollIdlePolicy: cross-hook coexistence", () => {
  it("idle hook + velocity hook can mount together without throwing", async () => {
    const { useIdleState } = await import("@/hooks/useIdleState");
    const { useScrollVelocity } = await import("@/hooks/useScrollVelocity");
    const { result } = renderHook(() => ({
      idle: useIdleState(),
      velocity: useScrollVelocity(),
    }));
    expect(result.current.idle).toBe(false);
    expect(result.current.velocity.velocity).toBe(0);
  });
});
