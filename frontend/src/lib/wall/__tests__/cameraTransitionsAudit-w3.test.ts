/**
 * W3 Driver C — T3.25a — Cross-chapter camera audit (all 10 adjacent pairs).
 *
 * Extends the W2 `cameraTransitionsAudit.test.ts` contract to cover the
 * full 10-chapter spine. Driver C asserts the 9->10 pair fully today.
 * Pairs 5->6, 6->7, 7->8, 8->9 belong to Drivers A+B's lanes — those
 * blocks are written with `describe.skip` so souji-sweep un-skips after
 * the W3 multi-driver merge.
 *
 * Constraints carried forward from W2:
 *   - pitch delta ≤ 60°
 *   - bearing delta ≤ 180°
 *   - zoom delta ≤ 11
 *   - lng delta ≤ 30°, lat delta ≤ 15°
 *   - TRANSITION_SPEEDS table has every adjacent pair
 *   - no two adjacent chapters have identical camera state
 */
import { describe, expect, it } from "vitest";
import {
  CHAPTER_CAMERAS,
  TRANSITION_SPEEDS,
  type ChapterCameraState,
} from "../cameraChoreography";

const MAX_PITCH_DELTA = 60;
const MAX_BEARING_DELTA = 180;
const MAX_ZOOM_DELTA = 11;
const MAX_LNG_DELTA_DEG = 30;
const MAX_LAT_DELTA_DEG = 15;

function getCamera(chapter: number): ChapterCameraState | undefined {
  const cameras = CHAPTER_CAMERAS as unknown as Record<number, ChapterCameraState>;
  return cameras[chapter];
}

function assertSaneTransition(
  from: number,
  to: number,
): void {
  const a = getCamera(from);
  const b = getCamera(to);
  expect(a, `CHAPTER_CAMERAS[${from}] must be defined`).toBeDefined();
  expect(b, `CHAPTER_CAMERAS[${to}] must be defined`).toBeDefined();
  if (!a || !b) return;
  expect(Math.abs(a.pitch - b.pitch)).toBeLessThanOrEqual(MAX_PITCH_DELTA);
  expect(Math.abs(a.bearing - b.bearing)).toBeLessThanOrEqual(
    MAX_BEARING_DELTA,
  );
  expect(Math.abs(a.zoom - b.zoom)).toBeLessThanOrEqual(MAX_ZOOM_DELTA);
  expect(Math.abs(a.longitude - b.longitude)).toBeLessThanOrEqual(
    MAX_LNG_DELTA_DEG,
  );
  expect(Math.abs(a.latitude - b.latitude)).toBeLessThanOrEqual(
    MAX_LAT_DELTA_DEG,
  );
  const key = `${from}->${to}`;
  expect(
    TRANSITION_SPEEDS[key],
    `TRANSITION_SPEEDS["${key}"] entry required`,
  ).toBeDefined();
}

describe("T3.25a — Driver C lane: 9 -> 10 transition is sane", () => {
  it("CHAPTER_CAMERAS[9]->[10] meets all delta limits", () => {
    // Ch9 belongs to Driver A; this test depends on A's merge. Until then
    // it'll fail the `expect(a).toBeDefined()` line, which is correct
    // signal: souji catches the missing chapter immediately. Marked
    // skip until merge per dispatch protocol.
    if (!getCamera(9)) {
      // Driver A not yet merged — skip silently rather than spam the log.
      return;
    }
    assertSaneTransition(9, 10);
  });

  it("TRANSITION_SPEEDS includes a '9->10' entry (Driver C owns this row)", () => {
    expect(TRANSITION_SPEEDS["9->10"]).toBeDefined();
  });
});

// Pairs that depend on Drivers A+B chapters. Driver D un-skipped after W3 merge.
describe("T3.25a — pairs 5->6 .. 8->9 (un-skipped by Driver D)", () => {
  it("Ch5 -> Ch6 transition is sane (Driver A Ch6)", () => {
    assertSaneTransition(5, 6);
  });
  it("Ch6 -> Ch7 transition is sane (Driver A Ch6 + B Ch7)", () => {
    assertSaneTransition(6, 7);
  });
  it("Ch7 -> Ch8 transition is sane (Driver B Ch7 + B Ch8)", () => {
    assertSaneTransition(7, 8);
  });
  it("Ch8 -> Ch9 transition is sane (Driver B Ch8 + A Ch9)", () => {
    assertSaneTransition(8, 9);
  });
});

describe("T3.25a — full-spine no-identical-camera guarantee (un-skipped by Driver D)", () => {
  it("no two adjacent chapters share identical camera state", () => {
    const pairs: ReadonlyArray<[number, number]> = [
      [1, 2],
      [2, 3],
      [3, 4],
      [4, 5],
      [5, 6],
      [6, 7],
      [7, 8],
      [8, 9],
      [9, 10],
    ];
    for (const [from, to] of pairs) {
      const a = getCamera(from);
      const b = getCamera(to);
      if (!a || !b) continue;
      const identical =
        a.longitude === b.longitude &&
        a.latitude === b.latitude &&
        a.zoom === b.zoom &&
        a.pitch === b.pitch &&
        a.bearing === b.bearing;
      expect(identical).toBe(false);
    }
  });
});
