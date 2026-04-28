import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useVariableFontWeight } from "../useVariableFontWeight";

vi.mock("../usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "../usePrefersReducedMotion";

describe("useVariableFontWeight (T1.28)", () => {
  it("returns weight 700 + opsz 14 at progress=0", () => {
    const { result } = renderHook(() => useVariableFontWeight(0));
    expect(result.current).toBe('"wght" 700, "opsz" 14');
  });

  it("returns weight 900 + opsz 32 at progress=1", () => {
    const { result } = renderHook(() => useVariableFontWeight(1));
    expect(result.current).toBe('"wght" 900, "opsz" 32');
  });

  it("interpolates linearly at progress=0.5", () => {
    const { result } = renderHook(() => useVariableFontWeight(0.5));
    expect(result.current).toBe('"wght" 800, "opsz" 23');
  });

  it("clamps progress below 0", () => {
    const { result } = renderHook(() => useVariableFontWeight(-0.5));
    expect(result.current).toBe('"wght" 700, "opsz" 14');
  });

  it("clamps progress above 1", () => {
    const { result } = renderHook(() => useVariableFontWeight(2));
    expect(result.current).toBe('"wght" 900, "opsz" 32');
  });

  it("locks weight at 800 under reduced-motion regardless of progress", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { result } = renderHook(() => useVariableFontWeight(0.2));
    expect(result.current).toContain('"wght" 800');
    vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
  });

  it("returns a stable string ref between rerenders with same progress", () => {
    const { result, rerender } = renderHook(
      ({ p }: { p: number }) => useVariableFontWeight(p),
      { initialProps: { p: 0.3 } },
    );
    const first = result.current;
    rerender({ p: 0.3 });
    expect(result.current).toBe(first);
  });
});
