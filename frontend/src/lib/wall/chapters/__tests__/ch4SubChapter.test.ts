/**
 * W2 Driver C — Ch4 sub-chapter state machine.
 *
 * Chapter 4 has 4 sub-chapters and global progress 30–40% drives them:
 *   30.0–32.5% → 4a (criminal record)
 *   32.5–35.0% → 4b (no transit)
 *   35.0–37.5% → 4c (no childcare)
 *   37.5–40.0% → 4d (bad credit)
 *
 * `ch4SubChapter` accepts the LOCAL chapter progress 0..1 (Driver A's
 * useChapterProgress already normalizes the global window for us).
 */
import { describe, it, expect } from "vitest";
import { ch4SubChapter, CH4_SUBCHAPTERS } from "../ch4SubChapter";

describe("ch4SubChapter — local-progress mapping", () => {
  it("returns 4a at the start of the chapter", () => {
    expect(ch4SubChapter(0)).toBe("4a");
  });

  it("stays on 4a through the first quarter", () => {
    expect(ch4SubChapter(0.24)).toBe("4a");
  });

  it("transitions to 4b at 0.25", () => {
    expect(ch4SubChapter(0.25)).toBe("4b");
  });

  it("returns 4c around the midpoint", () => {
    expect(ch4SubChapter(0.6)).toBe("4c");
  });

  it("returns 4d in the last quarter", () => {
    expect(ch4SubChapter(0.8)).toBe("4d");
  });

  it("clamps progress > 1 to 4d", () => {
    expect(ch4SubChapter(1.5)).toBe("4d");
  });

  it("clamps progress < 0 to 4a", () => {
    expect(ch4SubChapter(-0.2)).toBe("4a");
  });
});

describe("CH4_SUBCHAPTERS — ordering + content", () => {
  it("declares 4 sub-chapters in narrative order", () => {
    expect(CH4_SUBCHAPTERS.map((s) => s.id)).toEqual([
      "4a",
      "4b",
      "4c",
      "4d",
    ]);
  });

  it("each sub-chapter has a barrier name", () => {
    for (const sub of CH4_SUBCHAPTERS) {
      expect(sub.barrier).toBeTruthy();
    }
  });

  it("each sub-chapter declares a stat band value (for the overlay)", () => {
    for (const sub of CH4_SUBCHAPTERS) {
      expect(sub.statValue).toBeTruthy();
    }
  });
});
