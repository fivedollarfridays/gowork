import { describe, it, expect } from "vitest";
import {
  CHAPTER_CAMERAS,
  INITIAL_CAMERA,
  TRANSITION_SPEEDS,
  type ChapterCameraState,
  type W2ChapterId,
} from "../cameraChoreography";

/**
 * T2.4 + T2.7 — Camera choreography: per-chapter Mapbox camera states.
 *
 * Single source of truth for chapters 1–5 (W2 scope). W3 extends this file
 * with chapters 6–10. Without a shared module, ten chapters race to invent
 * their own camera state and the choreography drifts.
 *
 * Tests lock:
 *   - INITIAL_CAMERA = Fort Worth centroid (zoom 11, pitch 0, bearing 0)
 *   - Each W2 chapter has a complete state shape (no undefined fields)
 *   - Coordinates resolve to plausible Fort Worth / Tarrant County / FW ZIP
 *   - flyToOptions reference W1 motion tokens (cubic-bezier)
 *   - Snapshot guard against accidental coordinate edits
 *
 * Spotlight (Wisdom Lens — Driver A): one shared module is cleaner than
 * five chapter-local definitions. The brief said "per-chapter" — the
 * structural answer is "one config, indexed by chapter."
 */

const W2_CHAPTERS: W2ChapterId[] = [1, 2, 3, 4, 5];

describe("T2.4 — INITIAL_CAMERA boots into Fort Worth overview", () => {
  it("centers Fort Worth (lng -97.3308, lat 32.7555)", () => {
    expect(INITIAL_CAMERA.longitude).toBeCloseTo(-97.3308, 3);
    expect(INITIAL_CAMERA.latitude).toBeCloseTo(32.7555, 3);
  });

  it("zoom 11, pitch 0, bearing 0 (no jarring snap on first paint)", () => {
    expect(INITIAL_CAMERA.zoom).toBe(11);
    expect(INITIAL_CAMERA.pitch).toBe(0);
    expect(INITIAL_CAMERA.bearing).toBe(0);
  });
});

describe("T2.7 — every W2 chapter has a complete camera state", () => {
  it.each(W2_CHAPTERS)("chapter %i defines lng/lat/zoom/pitch/bearing/flyToOptions", (chapter) => {
    const state = CHAPTER_CAMERAS[chapter];
    expect(state).toBeDefined();
    expect(typeof state.longitude).toBe("number");
    expect(typeof state.latitude).toBe("number");
    expect(typeof state.zoom).toBe("number");
    expect(typeof state.pitch).toBe("number");
    expect(typeof state.bearing).toBe("number");
    expect(state.flyToOptions).toBeDefined();
    expect(state.flyToOptions.curve).toBeTypeOf("number");
    expect(state.flyToOptions.speed).toBeTypeOf("number");
    expect(Array.isArray(state.flyToOptions.easing)).toBe(true);
  });
});

describe("T2.7 — chapter zoom progression (continental → neighborhood → mid)", () => {
  it("Chapter 1 is continental (zoom ≤ 4 — top-down America)", () => {
    expect(CHAPTER_CAMERAS[1].zoom).toBeLessThanOrEqual(4);
  });

  it("Chapter 2 dollies into Fort Worth (zoom 11, pitch 60)", () => {
    expect(CHAPTER_CAMERAS[2].zoom).toBe(11);
    expect(CHAPTER_CAMERAS[2].pitch).toBe(60);
  });

  it("Chapter 3 is neighborhood scale (zoom 14, bearing tilted east)", () => {
    expect(CHAPTER_CAMERAS[3].zoom).toBe(14);
    expect(CHAPTER_CAMERAS[3].pitch).toBe(60);
    expect(CHAPTER_CAMERAS[3].bearing).toBe(25);
  });

  it("Chapter 4 (parent) is mid-altitude FW (zoom 13, pitch 50)", () => {
    expect(CHAPTER_CAMERAS[4].zoom).toBe(13);
    expect(CHAPTER_CAMERAS[4].pitch).toBe(50);
  });

  it("Chapter 5 is mid-altitude bird's-eye for the labyrinth (zoom 11, pitch 30)", () => {
    expect(CHAPTER_CAMERAS[5].zoom).toBe(11);
    expect(CHAPTER_CAMERAS[5].pitch).toBe(30);
  });
});

describe("T2.7 — coordinates land within plausible bounds", () => {
  it.each(W2_CHAPTERS)("chapter %i lng/lat are sensible (US continental for Ch1; Tarrant for Ch2-5)", (chapter) => {
    const state = CHAPTER_CAMERAS[chapter];
    if (chapter === 1) {
      // Continental view — somewhere in the contiguous US
      expect(state.longitude).toBeGreaterThan(-130);
      expect(state.longitude).toBeLessThan(-65);
      expect(state.latitude).toBeGreaterThan(25);
      expect(state.latitude).toBeLessThan(50);
    } else {
      // Tarrant County / Fort Worth — TIGER bounding box
      expect(state.longitude).toBeGreaterThan(-97.6);
      expect(state.longitude).toBeLessThan(-97.0);
      expect(state.latitude).toBeGreaterThan(32.5);
      expect(state.latitude).toBeLessThan(33.0);
    }
  });
});

describe("T2.7 — flyToOptions use W1 motion tokens (cubic-bezier from EASE_LINEAR_SIG)", () => {
  it.each(W2_CHAPTERS)("chapter %i easing equals [0.32, 0.72, 0, 1]", (chapter) => {
    const easing = CHAPTER_CAMERAS[chapter].flyToOptions.easing;
    expect(easing).toEqual([0.32, 0.72, 0, 1]);
  });
});

describe("T2.7 — TRANSITION_SPEEDS table varies per chapter pair", () => {
  it("Ch1→Ch2 is the longest cinematic transition (speed >= 1.2)", () => {
    expect(TRANSITION_SPEEDS["1->2"]).toBeGreaterThanOrEqual(1.2);
  });

  it("Ch4 internal sub-chapter transitions are short (speed <= 0.8)", () => {
    // Sub-chapter pivots within Chapter 4 are bearing-only — short.
    // Filter for SUB-chapter pairs only (e.g., "4a->4b") — chapter pairs
    // like "4->5" are full re-flies and stay at standard speed.
    const subValues = Object.entries(TRANSITION_SPEEDS).filter(([key]) =>
      /^4[a-d]->4[a-d]$/.test(key),
    );
    expect(subValues.length).toBeGreaterThanOrEqual(1);
    for (const [, speed] of subValues) {
      expect(speed).toBeLessThanOrEqual(0.8);
    }
  });
});

describe("T2.4 + T2.7 — regression-guard snapshot of camera coords", () => {
  it("coordinates are stable (snapshot guard against accidental edits)", () => {
    expect({
      initial: INITIAL_CAMERA,
      chapters: CHAPTER_CAMERAS,
    }).toMatchSnapshot();
  });
});

describe("T2.7 — type ChapterCameraState exposes the public shape", () => {
  it("compiles with required fields (TypeScript-only assertion)", () => {
    const _check: ChapterCameraState = {
      longitude: 0,
      latitude: 0,
      zoom: 0,
      pitch: 0,
      bearing: 0,
      flyToOptions: { curve: 1.2, speed: 1.0, easing: [0.32, 0.72, 0, 1] },
    };
    expect(_check).toBeDefined();
  });
});
