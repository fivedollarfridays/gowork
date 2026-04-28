/**
 * Tests for the unified ChapterProps contract.
 *
 * Driver D Spotlight invention #2. Five chapter components built by three
 * drivers in three worktrees inevitably ship five slightly-different prop
 * shapes (Driver B's Ch3 has `active`, Driver C's Ch5 has `reducedMotion`,
 * Driver A's scaffold has neither). This module pins the canonical shape
 * so W3 chapters 6-10 inherit the same contract instead of inventing a
 * sixth variant.
 */
import { describe, expect, it } from "vitest";
import {
  CHAPTER_PROP_KEYS,
  isChapterProps,
  isValidChapterId,
} from "../chapterContract";
import type { ChapterProps } from "../chapterContract";

describe("CHAPTER_PROP_KEYS", () => {
  it("declares the canonical prop keys every chapter accepts", () => {
    expect(CHAPTER_PROP_KEYS).toContain("progress");
    expect(CHAPTER_PROP_KEYS).toContain("active");
    expect(CHAPTER_PROP_KEYS).toContain("chapterId");
    expect(CHAPTER_PROP_KEYS).toContain("reducedMotion");
  });
});

describe("isChapterProps", () => {
  it("accepts an object with progress + active", () => {
    const props: ChapterProps = { progress: 0.5, active: true };
    expect(isChapterProps(props)).toBe(true);
  });

  it("accepts the optional reducedMotion / chapterId / chapterNumber fields", () => {
    const props: ChapterProps = {
      progress: 0,
      active: false,
      reducedMotion: true,
      chapterId: "neighborhood",
      chapterNumber: 3,
    };
    expect(isChapterProps(props)).toBe(true);
  });

  it("rejects when progress is not a number", () => {
    expect(isChapterProps({ progress: "0.5", active: true })).toBe(false);
  });

  it("rejects when active is missing", () => {
    expect(isChapterProps({ progress: 0.5 })).toBe(false);
  });

  it("rejects null / undefined / non-objects", () => {
    expect(isChapterProps(null)).toBe(false);
    expect(isChapterProps(undefined)).toBe(false);
    expect(isChapterProps(42)).toBe(false);
  });
});

describe("isValidChapterId", () => {
  it("accepts integers 1..10", () => {
    for (let i = 1; i <= 10; i++) expect(isValidChapterId(i)).toBe(true);
  });

  it("rejects 0, 11, negative, fractional", () => {
    expect(isValidChapterId(0)).toBe(false);
    expect(isValidChapterId(11)).toBe(false);
    expect(isValidChapterId(-1)).toBe(false);
    expect(isValidChapterId(1.5)).toBe(false);
  });

  it("rejects non-numbers", () => {
    expect(isValidChapterId("3" as unknown as number)).toBe(false);
    expect(isValidChapterId(NaN)).toBe(false);
  });
});
