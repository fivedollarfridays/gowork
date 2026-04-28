import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useBatteryAware } from "../useBatteryAware";

interface MockBattery {
  level: number;
  charging: boolean;
  addEventListener: (type: string, fn: () => void) => void;
  removeEventListener: (type: string, fn: () => void) => void;
  dispatchEvent: (type: string) => void;
}

function makeBatteryMock(level: number, charging: boolean): MockBattery {
  const listeners = new Map<string, Set<() => void>>();
  return {
    level,
    charging,
    addEventListener: (type, fn) => {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type)!.add(fn);
    },
    removeEventListener: (type, fn) => {
      listeners.get(type)?.delete(fn);
    },
    dispatchEvent: (type: string) => {
      listeners.get(type)?.forEach((fn) => fn());
    },
  };
}

afterEach(() => {
  delete (navigator as unknown as { getBattery?: unknown }).getBattery;
  vi.restoreAllMocks();
});

describe("useBatteryAware (T1.98)", () => {
  it("returns null + false when getBattery is unavailable (Firefox)", async () => {
    delete (navigator as unknown as { getBattery?: unknown }).getBattery;
    const { result } = renderHook(() => useBatteryAware());
    await waitFor(() => expect(result.current.level).toBeNull());
    expect(result.current.charging).toBeNull();
    expect(result.current.isLow).toBe(false);
  });

  it("populates level + charging when getBattery resolves", async () => {
    const battery = makeBatteryMock(0.5, false);
    (navigator as unknown as { getBattery: () => Promise<MockBattery> }).getBattery = () =>
      Promise.resolve(battery);
    const { result } = renderHook(() => useBatteryAware());
    await waitFor(() => expect(result.current.level).toBe(0.5));
    expect(result.current.charging).toBe(false);
    expect(result.current.isLow).toBe(false);
  });

  it("flags isLow=true when level < 0.2 AND not charging", async () => {
    const battery = makeBatteryMock(0.15, false);
    (navigator as unknown as { getBattery: () => Promise<MockBattery> }).getBattery = () =>
      Promise.resolve(battery);
    const { result } = renderHook(() => useBatteryAware());
    await waitFor(() => expect(result.current.isLow).toBe(true));
  });

  it("flags isLow=false when low but charging", async () => {
    const battery = makeBatteryMock(0.15, true);
    (navigator as unknown as { getBattery: () => Promise<MockBattery> }).getBattery = () =>
      Promise.resolve(battery);
    const { result } = renderHook(() => useBatteryAware());
    await waitFor(() => expect(result.current.charging).toBe(true));
    expect(result.current.isLow).toBe(false);
  });

  it("removes listeners on unmount", async () => {
    const battery = makeBatteryMock(0.5, false);
    const removeSpy = vi.spyOn(battery, "removeEventListener");
    (navigator as unknown as { getBattery: () => Promise<MockBattery> }).getBattery = () =>
      Promise.resolve(battery);
    const { unmount, result } = renderHook(() => useBatteryAware());
    await waitFor(() => expect(result.current.level).toBe(0.5));
    unmount();
    const types = removeSpy.mock.calls.map((c) => c[0]);
    expect(types).toContain("levelchange");
    expect(types).toContain("chargingchange");
  });
});
