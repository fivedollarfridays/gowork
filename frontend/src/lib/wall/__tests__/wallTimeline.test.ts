/**
 * wallTimeline — pure timeline derivation (W3 Driver D Spotlight #2).
 *
 * Asserts the contract that future surfaces depend on:
 *   - frameAt(totalProgress) returns currentChapter, chapterProgress,
 *     nextChapter, transitionPhase, currentBounds — for ANY input.
 *   - phase boundaries are stable (entering < 0.15, dwelling, exiting >= 0.85).
 *   - Ch10 has nextChapter null (terminal).
 *   - midpointFrames returns 10 frames in chapter order.
 */
import { describe, it, expect } from "vitest";
import { frameAt, midpointFrames } from "../wallTimeline";
import { localToGlobal } from "../wallProgress";

describe("frameAt — basic shape", () => {
  it("returns the full frame contract for total=0", () => {
    const f = frameAt(0);
    expect(f.currentChapter).toBe(1);
    expect(f.chapterProgress).toBeCloseTo(0, 6);
    expect(f.nextChapter).toBe(2);
    expect(f.transitionPhase).toBe("entering");
    expect(f.currentBounds.chapter).toBe(1);
  });

  it("returns the terminal frame for total=1", () => {
    const f = frameAt(1);
    expect(f.currentChapter).toBe(10);
    expect(f.chapterProgress).toBeCloseTo(1, 6);
    expect(f.nextChapter).toBeNull();
    expect(f.transitionPhase).toBe("exiting");
  });

  it("clamps NaN to 0", () => {
    const f = frameAt(Number.NaN);
    expect(f.totalProgress).toBe(0);
    expect(f.currentChapter).toBe(1);
  });

  it("clamps negative to 0", () => {
    const f = frameAt(-0.5);
    expect(f.totalProgress).toBe(0);
  });

  it("clamps > 1 to 1", () => {
    const f = frameAt(1.5);
    expect(f.totalProgress).toBe(1);
  });
});

describe("frameAt — chapter membership across the spine", () => {
  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "midpoint of Ch%i resolves to currentChapter=%i",
    (n) => {
      const mid = localToGlobal(0.5, n);
      const f = frameAt(mid);
      expect(f.currentChapter).toBe(n);
      expect(f.chapterProgress).toBeCloseTo(0.5, 6);
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9] as const)(
    "Ch%i has nextChapter as Ch%i+1",
    (n) => {
      const mid = localToGlobal(0.5, n);
      const f = frameAt(mid);
      expect(f.nextChapter).toBe(n + 1);
    },
  );

  it("Ch10 has nextChapter=null", () => {
    const mid = localToGlobal(0.5, 10);
    const f = frameAt(mid);
    expect(f.nextChapter).toBeNull();
  });
});

describe("frameAt — transitionPhase windowing", () => {
  it("entering phase when chapterProgress < 0.15", () => {
    const at = localToGlobal(0.05, 5);
    expect(frameAt(at).transitionPhase).toBe("entering");
  });

  it("dwelling phase between 0.15 and 0.85", () => {
    const at = localToGlobal(0.5, 5);
    expect(frameAt(at).transitionPhase).toBe("dwelling");
  });

  it("exiting phase when chapterProgress >= 0.85", () => {
    const at = localToGlobal(0.9, 5);
    expect(frameAt(at).transitionPhase).toBe("exiting");
  });
});

describe("midpointFrames", () => {
  it("returns 10 frames in chapter order", () => {
    const frames = midpointFrames();
    expect(frames).toHaveLength(10);
    for (let i = 0; i < frames.length; i += 1) {
      expect(frames[i].currentChapter).toBe(i + 1);
      expect(frames[i].chapterProgress).toBeCloseTo(0.5, 6);
    }
  });

  it("totalProgress values strictly increase across the frames", () => {
    const frames = midpointFrames();
    let prev = -1;
    for (const f of frames) {
      expect(f.totalProgress).toBeGreaterThan(prev);
      prev = f.totalProgress;
    }
  });
});
