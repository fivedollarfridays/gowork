import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useHeroFontWeight, useChapterHeadingFontWeight } from "../useHeroFontWeight";

vi.mock("../usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: vi.fn(() => false),
}));

import { usePrefersReducedMotion } from "../usePrefersReducedMotion";

afterEach(() => {
  vi.mocked(usePrefersReducedMotion).mockReturnValue(false);
});

describe("useHeroFontWeight (T4.A.6)", () => {
  it("returns weight 700 at scroll progress 0", () => {
    const { result } = renderHook(() => useHeroFontWeight(0));
    expect(result.current).toContain('"wght" 700');
  });

  it("returns weight 700 while scroll progress < 0.05 (mostly held flat)", () => {
    const { result } = renderHook(() => useHeroFontWeight(0.025));
    // At halfway through the trigger range (0.025 of 0.05), weight is
    // already 800.
    expect(result.current).toMatch(/"wght" 8\d\d/);
  });

  it("returns weight 900 at scroll progress >= 0.05", () => {
    const { result } = renderHook(() => useHeroFontWeight(0.05));
    expect(result.current).toContain('"wght" 900');
  });

  it("clamps at weight 900 above scroll progress 0.05", () => {
    const { result } = renderHook(() => useHeroFontWeight(0.5));
    expect(result.current).toContain('"wght" 900');
  });

  it("locks to weight 700 under reduced-motion (no interpolation)", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { result } = renderHook(() => useHeroFontWeight(0.025));
    expect(result.current).toContain('"wght" 700');
  });

  it("returns the same value across rerenders with the same input", () => {
    const { result, rerender } = renderHook(
      ({ p }: { p: number }) => useHeroFontWeight(p),
      { initialProps: { p: 0.03 } },
    );
    const first = result.current;
    rerender({ p: 0.03 });
    expect(result.current).toBe(first);
  });
});

describe("useChapterHeadingFontWeight (T4.A.6)", () => {
  it("returns weight 600 at chapter-local progress 0", () => {
    const { result } = renderHook(() => useChapterHeadingFontWeight(0));
    expect(result.current).toContain('"wght" 600');
  });

  it("returns weight 800 at chapter-local progress 1", () => {
    const { result } = renderHook(() => useChapterHeadingFontWeight(1));
    expect(result.current).toContain('"wght" 800');
  });

  it("interpolates roughly mid-range at progress 0.5", () => {
    const { result } = renderHook(() => useChapterHeadingFontWeight(0.5));
    // 600 + 200 * 0.5 = 700
    expect(result.current).toContain('"wght" 700');
  });

  it("locks to weight 600 under reduced-motion", () => {
    vi.mocked(usePrefersReducedMotion).mockReturnValue(true);
    const { result } = renderHook(() => useChapterHeadingFontWeight(0.5));
    expect(result.current).toContain('"wght" 600');
  });
});
