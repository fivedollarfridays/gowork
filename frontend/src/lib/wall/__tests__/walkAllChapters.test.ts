/**
 * walkAllChapters — programmatic spine walk (W3 Driver D Spotlight #5).
 *
 * # Why this exists
 *
 * Existing tests assert each chapter independently:
 *   - cameraChoreography.test.ts pins each chapter's camera
 *   - cameraTransitionsAudit-w3.test.ts pins adjacent pairs
 *   - spineProgression.test.ts pins midpoint resolution
 *
 * What none of them catch: a chapter that's "skipped" by the timeline.
 * If a future bounds tweak accidentally makes Ch7's range zero-width
 * (or overlaps Ch8 entirely), the per-chapter tests still pass because
 * they hit the chapter at its midpoint via `localToGlobal(0.5, 7)` —
 * which DOESN'T iterate the timeline; it just queries the bounds map.
 *
 * walkAllChapters is the e2e-style guard: walk totalProgress 0 → 1 in
 * 200 steps and verify EVERY chapter (1..10) becomes the active chapter
 * at SOME step. If a chapter is silently skipped by the timeline, this
 * test fails loudly.
 *
 * # Spotlight Lens — Wisdom
 *
 * Per-chapter tests miss continuity. The spine is a sequence; the
 * sequence has to actually be walked to be trusted.
 */
import { describe, it, expect } from "vitest";
import { frameAt } from "../wallTimeline";
import { TOTAL_CHAPTERS } from "../wallProgress";

const STEPS = 200;

describe("walkAllChapters — every chapter is reachable along the timeline", () => {
  it("walking 0..1 in 200 steps visits every chapter at least once", () => {
    const visited = new Set<number>();
    for (let i = 0; i <= STEPS; i += 1) {
      const t = i / STEPS;
      visited.add(frameAt(t).currentChapter);
    }
    for (let n = 1; n <= TOTAL_CHAPTERS; n += 1) {
      expect(
        visited.has(n),
        `Chapter ${n} was never the current chapter during the walk`,
      ).toBe(true);
    }
    expect(visited.size).toBe(TOTAL_CHAPTERS);
  });

  it("the visited chapter sequence is monotonically non-decreasing", () => {
    let prev = 0;
    for (let i = 0; i <= STEPS; i += 1) {
      const t = i / STEPS;
      const cur = frameAt(t).currentChapter;
      expect(cur).toBeGreaterThanOrEqual(prev);
      prev = cur;
    }
  });

  it("totalProgress=0 starts at Ch1; totalProgress=1 ends at Ch10", () => {
    expect(frameAt(0).currentChapter).toBe(1);
    expect(frameAt(1).currentChapter).toBe(10);
  });
});

describe("walkAllChapters — chapter spans are non-empty", () => {
  it("every chapter has a span > 1/200 (>=0.5%)", () => {
    const counts: Record<number, number> = {};
    for (let i = 0; i <= STEPS; i += 1) {
      const t = i / STEPS;
      const ch = frameAt(t).currentChapter;
      counts[ch] = (counts[ch] ?? 0) + 1;
    }
    for (let n = 1; n <= TOTAL_CHAPTERS; n += 1) {
      expect(
        (counts[n] ?? 0) > 1,
        `Chapter ${n} has fewer than 2 sample points across 200 steps — bounds are too narrow`,
      ).toBe(true);
    }
  });
});

describe("walkAllChapters — phase progression within each chapter", () => {
  it("each chapter walks through entering -> dwelling -> exiting at fine granularity", () => {
    // Sample 100 sub-steps WITHIN each chapter's bounds and verify all
    // three phases are visited at least once. Catches a bounds collapse
    // that would make a chapter only briefly enter "dwelling."
    const FINE_STEPS = 100;
    for (let chapter = 1; chapter <= TOTAL_CHAPTERS; chapter += 1) {
      const phases = new Set<string>();
      const start = (chapter - 1) / TOTAL_CHAPTERS;
      const end = chapter / TOTAL_CHAPTERS;
      const span = end - start;
      // Sample within [start, end), excluding the boundary (which would
      // belong to the next chapter for non-final chapters).
      for (let i = 0; i < FINE_STEPS; i += 1) {
        const t = start + (i / FINE_STEPS) * span * 0.999;
        phases.add(frameAt(t).transitionPhase);
      }
      expect(
        phases.has("entering"),
        `Ch${chapter} never entered 'entering' phase`,
      ).toBe(true);
      expect(
        phases.has("dwelling"),
        `Ch${chapter} never entered 'dwelling' phase`,
      ).toBe(true);
      expect(
        phases.has("exiting"),
        `Ch${chapter} never entered 'exiting' phase`,
      ).toBe(true);
    }
  });
});
