/**
 * W3 Driver C Spotlight #3 — chapterCounter module.
 *
 * Pure derivation from globalProgress -> "N / 10". Used today by
 * WallContainer's path-line header to surface a counter; reused in
 * W4 by the persistent chapter-aware tinting layer to know which
 * chapter is "primary" without re-running the wallProgress slicer.
 */
import { describe, expect, it } from "vitest";
import {
  currentChapterFor,
  formatCounter,
  TOTAL_CHAPTERS_LABEL,
} from "../chapterCounter";

describe("chapterCounter — currentChapterFor (T3.26 Spotlight #3)", () => {
  it("global progress 0 returns Ch1", () => {
    expect(currentChapterFor(0)).toBe(1);
  });

  it("global progress 0.05 (mid-Ch1) returns Ch1", () => {
    expect(currentChapterFor(0.05)).toBe(1);
  });

  it("global progress 0.15 (mid-Ch2) returns Ch2", () => {
    expect(currentChapterFor(0.15)).toBe(2);
  });

  it("global progress 0.95 (mid-Ch10) returns Ch10", () => {
    expect(currentChapterFor(0.95)).toBe(10);
  });

  it("global progress 1.0 (terminal) returns Ch10", () => {
    expect(currentChapterFor(1.0)).toBe(10);
  });

  it("clamps below zero to Ch1", () => {
    expect(currentChapterFor(-0.5)).toBe(1);
  });

  it("clamps above one to Ch10", () => {
    expect(currentChapterFor(1.5)).toBe(10);
  });

  it("rejects NaN -> Ch1", () => {
    expect(currentChapterFor(Number.NaN)).toBe(1);
  });

  it("boundary 0.1 belongs to Ch2 (matches wallProgress.isChapterActive)", () => {
    expect(currentChapterFor(0.1)).toBe(2);
  });
});

describe("chapterCounter — formatCounter", () => {
  it("formats Ch1 as '01 / 10'", () => {
    expect(formatCounter(1)).toBe("01 / 10");
  });

  it("formats Ch10 as '10 / 10'", () => {
    expect(formatCounter(10)).toBe("10 / 10");
  });

  it("zero-pads single digits", () => {
    expect(formatCounter(7)).toBe("07 / 10");
  });

  it("clamps out-of-range chapter (0) to '01 / 10'", () => {
    expect(formatCounter(0)).toBe("01 / 10");
  });

  it("clamps out-of-range chapter (11) to '10 / 10'", () => {
    expect(formatCounter(11)).toBe("10 / 10");
  });
});

describe("chapterCounter — TOTAL_CHAPTERS_LABEL", () => {
  it("constant is '10' (no drift from wallProgress.TOTAL_CHAPTERS)", () => {
    expect(TOTAL_CHAPTERS_LABEL).toBe("10");
  });
});
