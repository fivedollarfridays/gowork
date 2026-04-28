/**
 * cameraTransitionsAudit — sanity gate for adjacent chapter camera moves.
 *
 * Driver D Spotlight invention #3.
 *
 * Every adjacent chapter pair (1→2, 2→3, ..., 4→5) needs a sane camera
 * transition. "Sane" means:
 *   - The Mapbox flyTo distance must be within a plausible range (not 0,
 *     not crossing the planet — judges should never see a 90-degree pitch
 *     flip without warning).
 *   - Pitch deltas don't exceed 60° (Mapbox max pitch).
 *   - Bearing deltas don't exceed 180° (a half-rotation; anything more is
 *     a sign someone wrote 360° instead of 0°).
 *   - Zoom deltas don't exceed 11 (continental→neighborhood is the biggest
 *     legitimate jump in the W2 sequence; anything wider means a typo).
 *   - The TRANSITION_SPEEDS table has an entry for every adjacent pair.
 *
 * If a future driver adds a chapter that flies the camera to Antarctica,
 * this test fails before the demo recording does.
 */
import { describe, expect, it } from "vitest";
import {
  CHAPTER_CAMERAS,
  TRANSITION_SPEEDS,
  type W2ChapterId,
} from "../cameraChoreography";

const W2_PAIRS: ReadonlyArray<[W2ChapterId, W2ChapterId]> = [
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 5],
];

const MAX_PITCH_DELTA = 60;
const MAX_BEARING_DELTA = 180;
const MAX_ZOOM_DELTA = 11;
const MAX_LNG_DELTA_DEG = 30; // continental shift is the legit ceiling
const MAX_LAT_DELTA_DEG = 15;

describe("cameraTransitionsAudit — every adjacent W2 pair has a sane transition", () => {
  it.each(W2_PAIRS)(
    "Ch%i → Ch%i — pitch delta within bounds",
    (from, to) => {
      const a = CHAPTER_CAMERAS[from];
      const b = CHAPTER_CAMERAS[to];
      expect(Math.abs(a.pitch - b.pitch)).toBeLessThanOrEqual(MAX_PITCH_DELTA);
    },
  );

  it.each(W2_PAIRS)(
    "Ch%i → Ch%i — bearing delta within bounds",
    (from, to) => {
      const a = CHAPTER_CAMERAS[from];
      const b = CHAPTER_CAMERAS[to];
      expect(Math.abs(a.bearing - b.bearing)).toBeLessThanOrEqual(
        MAX_BEARING_DELTA,
      );
    },
  );

  it.each(W2_PAIRS)(
    "Ch%i → Ch%i — zoom delta within bounds",
    (from, to) => {
      const a = CHAPTER_CAMERAS[from];
      const b = CHAPTER_CAMERAS[to];
      expect(Math.abs(a.zoom - b.zoom)).toBeLessThanOrEqual(MAX_ZOOM_DELTA);
    },
  );

  it.each(W2_PAIRS)(
    "Ch%i → Ch%i — lng/lat delta within continental scale",
    (from, to) => {
      const a = CHAPTER_CAMERAS[from];
      const b = CHAPTER_CAMERAS[to];
      expect(Math.abs(a.longitude - b.longitude)).toBeLessThanOrEqual(
        MAX_LNG_DELTA_DEG,
      );
      expect(Math.abs(a.latitude - b.latitude)).toBeLessThanOrEqual(
        MAX_LAT_DELTA_DEG,
      );
    },
  );

  it.each(W2_PAIRS)(
    "Ch%i → Ch%i — TRANSITION_SPEEDS table has an entry",
    (from, to) => {
      const key = `${from}->${to}`;
      expect(TRANSITION_SPEEDS[key]).toBeDefined();
      expect(typeof TRANSITION_SPEEDS[key]).toBe("number");
    },
  );

  it("no two adjacent chapters share identical camera state (every pair is a real move)", () => {
    for (const [from, to] of W2_PAIRS) {
      const a = CHAPTER_CAMERAS[from];
      const b = CHAPTER_CAMERAS[to];
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
