/**
 * Tests for `wallProgress` — global-to-local progress slicer.
 *
 * Driver D Spotlight invention #1. The brief asked us to slice global
 * scroll progress (0..1 across all 10 chapters) into per-chapter local
 * progress (0..1 within a chapter). The math is small but easy to drift
 * — chapter components inlining `(global - 0.2) / 0.1` is exactly the
 * kind of magic-literal smell we want to avoid as W3 lands chapters 6-10.
 *
 * One module. One test. Zero drift.
 */
import { describe, expect, it } from "vitest";
import {
  CHAPTER_BOUNDS,
  TOTAL_CHAPTERS,
  chapterBoundsFor,
  globalToLocal,
  isChapterActive,
  localToGlobal,
} from "../wallProgress";

describe("wallProgress.CHAPTER_BOUNDS", () => {
  it("declares 10 chapters, each spanning 1/10 of global progress", () => {
    expect(CHAPTER_BOUNDS).toHaveLength(TOTAL_CHAPTERS);
    expect(TOTAL_CHAPTERS).toBe(10);
  });

  it("has Ch1 starting at 0 and Ch10 ending at 1", () => {
    expect(CHAPTER_BOUNDS[0].start).toBe(0);
    expect(CHAPTER_BOUNDS[9].end).toBe(1);
  });

  it("has contiguous bounds — every chapter's end is the next one's start", () => {
    for (let i = 0; i < TOTAL_CHAPTERS - 1; i++) {
      expect(CHAPTER_BOUNDS[i].end).toBeCloseTo(CHAPTER_BOUNDS[i + 1].start, 9);
    }
  });

  it("uses 1-indexed chapter ids", () => {
    expect(CHAPTER_BOUNDS[0].chapter).toBe(1);
    expect(CHAPTER_BOUNDS[9].chapter).toBe(10);
  });
});

describe("chapterBoundsFor", () => {
  it("returns Ch1 bounds for chapter 1", () => {
    const b = chapterBoundsFor(1);
    expect(b.start).toBe(0);
    expect(b.end).toBeCloseTo(0.1, 9);
  });

  it("returns Ch5 bounds for chapter 5", () => {
    const b = chapterBoundsFor(5);
    expect(b.start).toBeCloseTo(0.4, 9);
    expect(b.end).toBeCloseTo(0.5, 9);
  });

  it("clamps chapter id below 1 to chapter 1", () => {
    expect(chapterBoundsFor(0).chapter).toBe(1);
    expect(chapterBoundsFor(-3).chapter).toBe(1);
  });

  it("clamps chapter id above 10 to chapter 10", () => {
    expect(chapterBoundsFor(11).chapter).toBe(10);
    expect(chapterBoundsFor(99).chapter).toBe(10);
  });
});

describe("globalToLocal", () => {
  it("returns 0 when global progress is at the chapter start", () => {
    expect(globalToLocal(0, 1)).toBe(0);
    expect(globalToLocal(0.1, 2)).toBe(0);
    expect(globalToLocal(0.4, 5)).toBeCloseTo(0, 9);
  });

  it("returns 1 when global progress is at the chapter end", () => {
    expect(globalToLocal(0.1, 1)).toBeCloseTo(1, 9);
    expect(globalToLocal(0.5, 5)).toBeCloseTo(1, 9);
  });

  it("returns 0.5 at chapter midpoint", () => {
    expect(globalToLocal(0.05, 1)).toBeCloseTo(0.5, 9);
    expect(globalToLocal(0.45, 5)).toBeCloseTo(0.5, 9);
  });

  it("clamps below 0 to 0 and above 1 to 1", () => {
    expect(globalToLocal(-0.5, 1)).toBe(0);
    expect(globalToLocal(0.5, 1)).toBe(1); // out-of-range high
  });
});

describe("localToGlobal — round-trip", () => {
  it("inverts globalToLocal exactly at midpoints", () => {
    for (let ch = 1; ch <= TOTAL_CHAPTERS; ch++) {
      const bounds = chapterBoundsFor(ch);
      const mid = (bounds.start + bounds.end) / 2;
      const local = globalToLocal(mid, ch);
      const global = localToGlobal(local, ch);
      expect(global).toBeCloseTo(mid, 9);
    }
  });
});

describe("isChapterActive", () => {
  it("returns true when global progress is inside the chapter range", () => {
    expect(isChapterActive(0.05, 1)).toBe(true);
    expect(isChapterActive(0.45, 5)).toBe(true);
  });

  it("returns false when global progress is outside the chapter range", () => {
    expect(isChapterActive(0.5, 1)).toBe(false);
    expect(isChapterActive(0.05, 5)).toBe(false);
  });

  it("treats the start boundary as inside (inclusive) and end boundary as outside (exclusive) for non-final chapters", () => {
    expect(isChapterActive(0.1, 1)).toBe(false); // 0.1 belongs to Ch2
    expect(isChapterActive(0.1, 2)).toBe(true);
  });

  it("includes the final chapter's end boundary (no successor)", () => {
    expect(isChapterActive(1, 10)).toBe(true);
  });
});

/* -------------------------------------------------------------------------
 * W3 Driver A — guard for Ch6 + Ch9 boundary slots.
 * Drivers B/C will lock 7/8/10 in their own commits.
 * ----------------------------------------------------------------------- */

describe("W3 Driver A — Ch6 (The Math) bounds", () => {
  it("Ch6 occupies global progress [0.5, 0.6]", () => {
    const b = chapterBoundsFor(6);
    expect(b.start).toBeCloseTo(0.5, 9);
    expect(b.end).toBeCloseTo(0.6, 9);
  });

  it("globalToLocal resolves Ch6 progress correctly at midpoint (0.55)", () => {
    expect(globalToLocal(0.55, 6)).toBeCloseTo(0.5, 6);
  });

  it("isChapterActive reports Ch6 active inside its bound (0.5, 0.55)", () => {
    expect(isChapterActive(0.5, 6)).toBe(true);
    expect(isChapterActive(0.55, 6)).toBe(true);
    // 0.4999 is below the start; treat as Ch5
    expect(isChapterActive(0.4999, 6)).toBe(false);
  });
});

describe("W3 Driver A — Ch9 (Any City) bounds", () => {
  it("Ch9 occupies global progress [0.8, 0.9]", () => {
    const b = chapterBoundsFor(9);
    expect(b.start).toBeCloseTo(0.8, 9);
    expect(b.end).toBeCloseTo(0.9, 9);
  });

  it("globalToLocal resolves Ch9 progress correctly at midpoint (0.85)", () => {
    expect(globalToLocal(0.85, 9)).toBeCloseTo(0.5, 6);
  });

  it("isChapterActive reports Ch9 active inside its bound (0.8, 0.85)", () => {
    expect(isChapterActive(0.8, 9)).toBe(true);
    expect(isChapterActive(0.85, 9)).toBe(true);
    // 0.7999 is below the start; treat as Ch8
    expect(isChapterActive(0.7999, 9)).toBe(false);
  });
});
