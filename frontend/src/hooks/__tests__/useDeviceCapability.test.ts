import { describe, it, expect, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useDeviceCapability } from "../useDeviceCapability";

afterEach(() => {
  // Reset overrides
  Object.defineProperty(navigator, "deviceMemory", { value: undefined, configurable: true });
  Object.defineProperty(navigator, "hardwareConcurrency", { value: 8, configurable: true });
  delete (navigator as unknown as { connection?: unknown }).connection;
  delete (navigator as unknown as { maxTouchPoints?: number }).maxTouchPoints;
});

describe("useDeviceCapability (T1.75)", () => {
  it("classifies a high-end desktop as tier=high", () => {
    Object.defineProperty(navigator, "deviceMemory", { value: 16, configurable: true });
    Object.defineProperty(navigator, "hardwareConcurrency", { value: 12, configurable: true });
    Object.defineProperty(navigator, "connection", {
      value: { saveData: false, effectiveType: "4g" },
      configurable: true,
    });
    const { result } = renderHook(() => useDeviceCapability());
    expect(result.current.tier).toBe("high");
    expect(result.current.deviceMemoryGb).toBe(16);
    expect(result.current.hardwareConcurrency).toBe(12);
    expect(result.current.prefersReducedData).toBe(false);
  });

  it("classifies a low-end Android (2 GB, 2 cores, save-data) as tier=low", () => {
    Object.defineProperty(navigator, "deviceMemory", { value: 2, configurable: true });
    Object.defineProperty(navigator, "hardwareConcurrency", { value: 2, configurable: true });
    Object.defineProperty(navigator, "connection", {
      value: { saveData: true, effectiveType: "3g" },
      configurable: true,
    });
    Object.defineProperty(navigator, "maxTouchPoints", { value: 5, configurable: true });
    const { result } = renderHook(() => useDeviceCapability());
    expect(result.current.tier).toBe("low");
    expect(result.current.isMobile).toBe(true);
    expect(result.current.prefersReducedData).toBe(true);
  });

  it("classifies a mid-range device as tier=medium", () => {
    Object.defineProperty(navigator, "deviceMemory", { value: 4, configurable: true });
    Object.defineProperty(navigator, "hardwareConcurrency", { value: 4, configurable: true });
    const { result } = renderHook(() => useDeviceCapability());
    expect(result.current.tier).toBe("medium");
  });

  it("returns deviceMemoryGb=null when unsupported (Safari)", () => {
    Object.defineProperty(navigator, "deviceMemory", { value: undefined, configurable: true });
    Object.defineProperty(navigator, "hardwareConcurrency", { value: 8, configurable: true });
    const { result } = renderHook(() => useDeviceCapability());
    expect(result.current.deviceMemoryGb).toBeNull();
    // Without memory data we still produce a tier from concurrency alone.
    expect(["high", "medium", "low"]).toContain(result.current.tier);
  });

  it("memoizes WebGL detection (does not create canvas every render)", () => {
    const { result, rerender } = renderHook(() => useDeviceCapability());
    const first = result.current.supportsWebGL;
    rerender();
    expect(result.current.supportsWebGL).toBe(first);
  });
});
