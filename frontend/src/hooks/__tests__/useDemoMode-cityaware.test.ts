import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("useDemoMode city-aware", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("location", { ...window.location, search: "" });
  });

  // T25.8 (Sprint 25 — Dallas Expansion): parametrize over both DFW cities so
  // the canonical demo ZIP for each metro is asserted by the same shape.
  // Adding new cities = add a row here; the demo plumbing must already resolve.
  const cityCases: Array<{ city: string; expectedZip: string; label: string }> = [
    { city: "fort-worth", expectedZip: "76102", label: "Fort Worth" },
    { city: "dallas", expectedZip: "75201", label: "Dallas" },
  ];

  for (const { city, expectedZip, label } of cityCases) {
    it(`uses ${label} ZIP (${expectedZip}) when city param is ${city}`, async () => {
      vi.stubGlobal("location", {
        ...window.location,
        search: `?demo=true&city=${city}`,
      });
      const { useDemoMode } = await import("../useDemoMode");
      const { result } = renderHook(() => useDemoMode());

      await waitFor(() => {
        expect(result.current).not.toBeNull();
      });
      expect(result.current!.zipCode).toBe(expectedZip);
    });
  }

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
