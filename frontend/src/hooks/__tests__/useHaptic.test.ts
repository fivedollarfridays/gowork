import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockUseReducedMotion = vi.fn(() => false);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => mockUseReducedMotion() };
});

describe("useHaptic", () => {
  beforeEach(() => {
    navigator.vibrate = vi.fn();
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("returns object with tap, success, error functions", async () => {
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    expect(typeof result.current.tap).toBe("function");
    expect(typeof result.current.success).toBe("function");
    expect(typeof result.current.error).toBe("function");
  });

  it("tap() calls navigator.vibrate(10)", async () => {
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    result.current.tap();
    expect(navigator.vibrate).toHaveBeenCalledWith(10);
  });

  it("success() calls navigator.vibrate([10, 50, 10])", async () => {
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    result.current.success();
    expect(navigator.vibrate).toHaveBeenCalledWith([10, 50, 10]);
  });

  it("error() calls navigator.vibrate(30)", async () => {
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    result.current.error();
    expect(navigator.vibrate).toHaveBeenCalledWith(30);
  });

  it("does not throw when navigator.vibrate is undefined", async () => {
    Object.defineProperty(navigator, "vibrate", { value: undefined, writable: true, configurable: true });
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    expect(() => result.current.tap()).not.toThrow();
    expect(() => result.current.success()).not.toThrow();
    expect(() => result.current.error()).not.toThrow();
  });

  it("does not call vibrate when useReducedMotion returns true", async () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { useHaptic } = await import("../useHaptic");
    const { result } = renderHook(() => useHaptic());
    result.current.tap();
    result.current.success();
    result.current.error();
    expect(navigator.vibrate).not.toHaveBeenCalled();
  });
});
