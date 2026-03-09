import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("useDemoMode", () => {
  beforeEach(() => {
    vi.resetModules();
    // Reset location to no search params
    vi.stubGlobal("location", { ...window.location, search: "" });
  });

  it("returns pre-filled BarrierFormData when URL has ?demo=true", async () => {
    vi.stubGlobal("location", { ...window.location, search: "?demo=true" });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.zipCode).toBe("36104");
    expect(result.current!.employment).toBe("unemployed");
    expect(result.current!.hasVehicle).toBe(false);
  });

  it("returns null when URL has no demo param", async () => {
    vi.stubGlobal("location", { ...window.location, search: "" });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());
    expect(result.current).toBeNull();
  });

  it("pre-filled data has at least one barrier selected (credit=true)", async () => {
    vi.stubGlobal("location", { ...window.location, search: "?demo=true" });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.barriers.credit).toBe(true);
  });

  it("pre-filled data has work history text", async () => {
    vi.stubGlobal("location", { ...window.location, search: "?demo=true" });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.workHistory.length).toBeGreaterThan(0);
  });
});
