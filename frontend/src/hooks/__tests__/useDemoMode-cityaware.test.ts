import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("useDemoMode city-aware", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("location", { ...window.location, search: "" });
  });

  it("uses Fort Worth ZIP (76102) when city param is fort-worth", async () => {
    vi.stubGlobal("location", {
      ...window.location,
      search: "?demo=true&city=fort-worth",
    });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.zipCode).toBe("76102");
  });

  it("uses Montgomery ZIP (36104) by default", async () => {
    vi.stubGlobal("location", {
      ...window.location,
      search: "?demo=true",
    });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.zipCode).toBe("36104");
  });

  it("uses Montgomery ZIP when city=montgomery", async () => {
    vi.stubGlobal("location", {
      ...window.location,
      search: "?demo=true&city=montgomery",
    });
    const { useDemoMode } = await import("../useDemoMode");
    const { result } = renderHook(() => useDemoMode());

    await waitFor(() => {
      expect(result.current).not.toBeNull();
    });
    expect(result.current!.zipCode).toBe("36104");
  });
});
