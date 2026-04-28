import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

/**
 * T2.8 — useChapterProgress.
 *
 * Derives chapter-aware scroll state from W1's `useScrollProgress`. Returns
 * `{currentChapter, chapterProgress, nextChapter, isTransitioning}`.
 *
 * Boundaries are equal page divisions for W2 (10 chapters → each 10% of
 * page). `isTransitioning` is true within ±5% of a boundary.
 *
 * The hook is the contract Drivers B/C consume to drive overlay opacity
 * and trigger flyTo. Get the math right ONCE so 10 chapter components
 * don't each re-implement boundary detection.
 */

// Mock the upstream hook so each test can drive scroll deterministically.
const scrollMock = vi.fn();
vi.mock("../useScrollProgress", () => ({
  useScrollProgress: () => scrollMock(),
}));

beforeEach(() => {
  scrollMock.mockReset();
});

afterEach(() => {
  scrollMock.mockReset();
});

async function importHook() {
  const mod = await import("../useChapterProgress");
  return mod.useChapterProgress;
}

describe("T2.8 — useChapterProgress maps total scroll to chapter id (1-indexed)", () => {
  it("totalProgress=0 → currentChapter=1, chapterProgress=0", async () => {
    scrollMock.mockReturnValue({ chapter: 0, progressInChapter: 0, totalProgress: 0 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.currentChapter).toBe(1);
    expect(result.current.chapterProgress).toBeCloseTo(0, 3);
    expect(result.current.nextChapter).toBe(2);
  });

  it("totalProgress=0.05 → currentChapter=1, chapterProgress=0.5 (mid Ch1)", async () => {
    scrollMock.mockReturnValue({ chapter: 0, progressInChapter: 0.5, totalProgress: 0.05 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.currentChapter).toBe(1);
    expect(result.current.chapterProgress).toBeCloseTo(0.5, 3);
  });

  it("totalProgress=0.55 → currentChapter=6, chapterProgress=0.5 (mid Ch6)", async () => {
    scrollMock.mockReturnValue({ chapter: 5, progressInChapter: 0.5, totalProgress: 0.55 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.currentChapter).toBe(6);
    expect(result.current.chapterProgress).toBeCloseTo(0.5, 3);
    expect(result.current.nextChapter).toBe(7);
  });

  it("totalProgress=1 → currentChapter=10 (last), nextChapter=10 (clamped)", async () => {
    scrollMock.mockReturnValue({ chapter: 9, progressInChapter: 1, totalProgress: 1 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.currentChapter).toBe(10);
    expect(result.current.nextChapter).toBe(10); // No chapter 11 — clamped.
  });
});

describe("T2.8 — isTransitioning fires within ±5% of a chapter boundary", () => {
  // 10 chapters → each is 10% of page → 5% of one chapter = 0.005 page-progress
  // units away from a boundary.

  it("totalProgress=0.97 inside Ch10 → isTransitioning=false (no Ch11 above)", async () => {
    scrollMock.mockReturnValue({ chapter: 9, progressInChapter: 0.7, totalProgress: 0.97 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.isTransitioning).toBe(false);
  });

  it("totalProgress=0.498 (within 0.005 of Ch5/Ch6 boundary) → isTransitioning=true", async () => {
    scrollMock.mockReturnValue({ chapter: 4, progressInChapter: 0.98, totalProgress: 0.498 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.isTransitioning).toBe(true);
  });

  it("totalProgress=0.502 (within 0.005 of Ch5/Ch6 boundary, post) → isTransitioning=true", async () => {
    scrollMock.mockReturnValue({ chapter: 5, progressInChapter: 0.02, totalProgress: 0.502 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.isTransitioning).toBe(true);
  });

  it("totalProgress=0.55 (mid Ch6, well clear of boundary) → isTransitioning=false", async () => {
    scrollMock.mockReturnValue({ chapter: 5, progressInChapter: 0.5, totalProgress: 0.55 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.isTransitioning).toBe(false);
  });

  it("totalProgress=0.49 (within 1pp = 10% of Ch5; OUTSIDE 5% band) → isTransitioning=false", async () => {
    scrollMock.mockReturnValue({ chapter: 4, progressInChapter: 0.9, totalProgress: 0.49 });
    const useChapterProgress = await importHook();
    const { result } = renderHook(() => useChapterProgress());
    expect(result.current.isTransitioning).toBe(false);
  });
});
