/**
 * W3 Driver C — T3.25c + T3.25d — Spine progression contracts.
 *
 * Two assertions:
 *   T3.25c — path-line header progression: at chapter N's midpoint,
 *           wallProgress.localToGlobal(0.5, N) returns the expected
 *           global (within ±0.02 tolerance, matching the C5 honest
 *           uncertainty bound).
 *   T3.25d — chapter counter: at the midpoint of chapter N, the
 *           formatted counter reads "0N / 10".
 *
 * These run as pure-function tests so they don't depend on Drivers
 * A+B's chapter components landing — the spine math is W2 contract.
 */
import { describe, expect, it } from "vitest";
import { localToGlobal, TOTAL_CHAPTERS } from "../wallProgress";
import { currentChapterFor, formatCounter } from "../chapterCounter";

const PROGRESSION_TOLERANCE = 0.02;

describe("T3.25c — path-line header progresses 0..1 across all 10 chapters", () => {
  it("midpoint of Ch1 ≈ 0.05 (within ±0.02)", () => {
    expect(localToGlobal(0.5, 1)).toBeCloseTo(0.05, 2);
  });

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "midpoint of Ch%i is at the expected global progress",
    (n) => {
      const expected = (n - 0.5) / TOTAL_CHAPTERS;
      const actual = localToGlobal(0.5, n);
      expect(Math.abs(actual - expected)).toBeLessThanOrEqual(
        PROGRESSION_TOLERANCE,
      );
    },
  );

  it("midpoint values strictly increase across chapters 1..10", () => {
    let prev = -1;
    for (let n = 1; n <= TOTAL_CHAPTERS; n += 1) {
      const mid = localToGlobal(0.5, n);
      expect(mid).toBeGreaterThan(prev);
      prev = mid;
    }
  });
});

describe("T3.25d — chapter counter reads 'N / 10' at chapter N's midpoint", () => {
  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "globalProgress at Ch%i midpoint -> currentChapterFor returns %i",
    (n) => {
      const mid = localToGlobal(0.5, n);
      expect(currentChapterFor(mid)).toBe(n);
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "formatCounter reflects 'N / 10' at Ch%i midpoint",
    (n) => {
      const mid = localToGlobal(0.5, n);
      const ch = currentChapterFor(mid);
      const expected = `${n < 10 ? `0${n}` : String(n)} / 10`;
      expect(formatCounter(ch)).toBe(expected);
    },
  );
});
