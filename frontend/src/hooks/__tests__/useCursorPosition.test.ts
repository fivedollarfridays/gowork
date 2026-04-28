import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCursorPosition } from "../useCursorPosition";

function dispatchPointer(clientX: number, clientY: number): void {
  const event = new PointerEvent("pointermove", {
    clientX,
    clientY,
    bubbles: true,
  });
  window.dispatchEvent(event);
}

describe("useCursorPosition (T1.25)", () => {
  beforeEach(() => {
    Object.defineProperty(window, "innerWidth", { value: 1000, configurable: true });
    Object.defineProperty(window, "innerHeight", { value: 800, configurable: true });
    // Ensure non-touch path
    Object.defineProperty(navigator, "maxTouchPoints", { value: 0, configurable: true });
    vi.useFakeTimers({ shouldAdvanceTime: false });
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => setTimeout(() => cb(performance.now()), 16) as unknown as number),
    );
    vi.stubGlobal("cancelAnimationFrame", ((id: number) => clearTimeout(id)) as unknown as typeof cancelAnimationFrame);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("returns the center on initial render", () => {
    const { result } = renderHook(() => useCursorPosition());
    expect(result.current.x).toBe(0.5);
    expect(result.current.y).toBe(0.5);
    expect(result.current.vx).toBe(0);
    expect(result.current.vy).toBe(0);
  });

  it("updates normalized x/y after a pointermove and rAF tick", () => {
    const { result } = renderHook(() => useCursorPosition());
    act(() => {
      dispatchPointer(500, 400);
      vi.advanceTimersByTime(20);
    });
    expect(result.current.x).toBeCloseTo(0.5, 2);
    expect(result.current.y).toBeCloseTo(0.5, 2);
  });

  it("clamps x/y to 0..1 range when cursor goes outside the viewport", () => {
    const { result } = renderHook(() => useCursorPosition());
    act(() => {
      dispatchPointer(2000, -500);
      vi.advanceTimersByTime(20);
    });
    expect(result.current.x).toBeLessThanOrEqual(1);
    expect(result.current.x).toBeGreaterThanOrEqual(0);
    expect(result.current.y).toBeGreaterThanOrEqual(0);
  });

  it("removes pointermove listener on unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const { unmount } = renderHook(() => useCursorPosition());
    unmount();
    const removed = removeSpy.mock.calls.some((call) => call[0] === "pointermove");
    expect(removed).toBe(true);
  });

  it("returns center static on touch devices and skips listener", () => {
    Object.defineProperty(navigator, "maxTouchPoints", { value: 5, configurable: true });
    const addSpy = vi.spyOn(window, "addEventListener");
    const { result } = renderHook(() => useCursorPosition());
    expect(result.current.x).toBe(0.5);
    expect(result.current.y).toBe(0.5);
    const moveCalls = addSpy.mock.calls.filter((c) => c[0] === "pointermove");
    expect(moveCalls.length).toBe(0);
    Object.defineProperty(navigator, "maxTouchPoints", { value: 0, configurable: true });
  });

  it("computes positive vx when cursor moves right between frames", () => {
    const { result } = renderHook(() => useCursorPosition());
    act(() => {
      dispatchPointer(100, 400);
      vi.advanceTimersByTime(20);
    });
    act(() => {
      dispatchPointer(900, 400);
      vi.advanceTimersByTime(20);
    });
    expect(result.current.vx).toBeGreaterThan(0);
  });
});
