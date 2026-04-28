/**
 * W3 Driver C — T3.20 / T3.25a — Camera choreography extension.
 *
 * Tests Driver C's lane (Ch10) AND the W3 contract that Drivers A+B
 * extend later: every chapter 1..10 must have an entry in
 * CHAPTER_CAMERAS, and every adjacent pair must have a TRANSITION_SPEEDS
 * entry. We assert chapter 10 directly here; chapters 6/7/8/9 are
 * asserted with `it.skip` so souji-sweep can un-skip after merge.
 */
import { describe, expect, it } from "vitest";
import {
  CHAPTER_CAMERAS,
  TRANSITION_SPEEDS,
} from "../cameraChoreography";

describe("W3 Ch10 camera choreography (T3.20)", () => {
  it("CHAPTER_CAMERAS[10] is defined", () => {
    expect(CHAPTER_CAMERAS[10]).toBeDefined();
  });

  it("Ch10 frames Fort Worth at overhead zoom (the 'home' framing)", () => {
    const ch10 = CHAPTER_CAMERAS[10];
    expect(ch10).toBeDefined();
    if (!ch10) return;
    // Centered on Fort Worth city centroid (matches INITIAL_CAMERA + Ch2)
    expect(ch10.longitude).toBeCloseTo(-97.3308, 3);
    expect(ch10.latitude).toBeCloseTo(32.7555, 3);
    // Zoom ≤ 11 — overhead, not buildings-altitude
    expect(ch10.zoom).toBeLessThanOrEqual(11);
    expect(ch10.zoom).toBeGreaterThanOrEqual(9);
    // Pitch 0 — back to top-down "we've returned home"
    expect(ch10.pitch).toBe(0);
    // Bearing 0 — north-up
    expect(ch10.bearing).toBe(0);
  });

  it("Ch10 flyToOptions are sane (curve > 1, speed > 0, easing length 4)", () => {
    const ch10 = CHAPTER_CAMERAS[10];
    expect(ch10).toBeDefined();
    if (!ch10) return;
    const opts = ch10.flyToOptions;
    expect(opts.curve).toBeGreaterThan(1);
    expect(opts.speed).toBeGreaterThan(0);
    expect(opts.easing).toHaveLength(4);
  });

  it("TRANSITION_SPEEDS has 9->10 entry (Driver C's lane)", () => {
    expect(TRANSITION_SPEEDS["9->10"]).toBeDefined();
    expect(typeof TRANSITION_SPEEDS["9->10"]).toBe("number");
    expect(TRANSITION_SPEEDS["9->10"]).toBeGreaterThan(0);
  });

  // Drivers A+B's W3 chapters extend the table; Driver D un-skipped these
  // after the W3 merge consolidated all 10 entries.
  it("CHAPTER_CAMERAS[6] is defined (Driver A Ch6 — un-skipped by Driver D)", () => {
    const cameras = CHAPTER_CAMERAS as unknown as Record<number, unknown>;
    expect(cameras[6]).toBeDefined();
  });

  it("CHAPTER_CAMERAS[7] is defined (Driver B Ch7 — un-skipped by Driver D)", () => {
    const cameras = CHAPTER_CAMERAS as unknown as Record<number, unknown>;
    expect(cameras[7]).toBeDefined();
  });

  it("CHAPTER_CAMERAS[8] is defined (Driver B Ch8 — un-skipped by Driver D)", () => {
    const cameras = CHAPTER_CAMERAS as unknown as Record<number, unknown>;
    expect(cameras[8]).toBeDefined();
  });

  it("CHAPTER_CAMERAS[9] is defined (Driver A Ch9 — un-skipped by Driver D)", () => {
    const cameras = CHAPTER_CAMERAS as unknown as Record<number, unknown>;
    expect(cameras[9]).toBeDefined();
  });
});
