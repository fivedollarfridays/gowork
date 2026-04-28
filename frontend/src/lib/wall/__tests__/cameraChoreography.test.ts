import { describe, it, expect } from "vitest";
import {
  CHAPTER_CAMERAS,
  INITIAL_CAMERA,
  TRANSITION_SPEEDS,
  type ChapterCameraState,
  type ChapterId,
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
    const state = CHAPTER_CAMERAS[chapter]!;
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
    expect(CHAPTER_CAMERAS[1]!.zoom).toBeLessThanOrEqual(4);
  });

  it("Chapter 2 dollies into Fort Worth (zoom 11, pitch 60)", () => {
    expect(CHAPTER_CAMERAS[2]!.zoom).toBe(11);
    expect(CHAPTER_CAMERAS[2]!.pitch).toBe(60);
  });

  it("Chapter 3 is neighborhood scale (zoom 14, bearing tilted east)", () => {
    expect(CHAPTER_CAMERAS[3]!.zoom).toBe(14);
    expect(CHAPTER_CAMERAS[3]!.pitch).toBe(60);
    expect(CHAPTER_CAMERAS[3]!.bearing).toBe(25);
  });

  it("Chapter 4 (parent) is mid-altitude FW (zoom 13, pitch 50)", () => {
    expect(CHAPTER_CAMERAS[4]!.zoom).toBe(13);
    expect(CHAPTER_CAMERAS[4]!.pitch).toBe(50);
  });

  it("Chapter 5 is mid-altitude bird's-eye for the labyrinth (zoom 11, pitch 30)", () => {
    expect(CHAPTER_CAMERAS[5]!.zoom).toBe(11);
    expect(CHAPTER_CAMERAS[5]!.pitch).toBe(30);
  });
});

describe("T2.7 — coordinates land within plausible bounds", () => {
  it.each(W2_CHAPTERS)("chapter %i lng/lat are sensible (US continental for Ch1; Tarrant for Ch2-5)", (chapter) => {
    const state = CHAPTER_CAMERAS[chapter]!;
    expect(state).toBeDefined();
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
    const easing = CHAPTER_CAMERAS[chapter]!.flyToOptions.easing;
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

describe("W3 Driver B — Ch7 Path camera state", () => {
  it("Chapter 7 is registered with neighborhood-altitude framing", () => {
    expect(CHAPTER_CAMERAS[7]).toBeDefined();
    const ch7 = CHAPTER_CAMERAS[7]!;
    // Pulls to neighborhood altitude per brief: zoom 13, pitch 60, bearing 25
    expect(ch7.zoom).toBe(13);
    expect(ch7.pitch).toBe(60);
    expect(ch7.bearing).toBe(25);
  });

  it("Chapter 7 lng/lat lands within Tarrant County bounds", () => {
    const ch7 = CHAPTER_CAMERAS[7]!;
    expect(ch7.longitude).toBeGreaterThan(-97.6);
    expect(ch7.longitude).toBeLessThan(-97.0);
    expect(ch7.latitude).toBeGreaterThan(32.5);
    expect(ch7.latitude).toBeLessThan(33.0);
  });
});

describe("W3 Driver B — Ch8 Graph (3D constellation) camera state", () => {
  it("Chapter 8 tilts UP to reveal constellation above the city", () => {
    expect(CHAPTER_CAMERAS[8]).toBeDefined();
    const ch8 = CHAPTER_CAMERAS[8]!;
    // Pitch 60 is the dramatic tilt that keeps the Ch8->Ch9 audit
    // constraint intact (60° max delta from Ch9's pitch 0). Driver D
    // retuned from 70 → 60 during W3 maximization; the constellation
    // still reads as floating above downtown at this pitch.
    expect(ch8.pitch).toBe(60);
    expect(ch8.bearing).toBe(0);
    expect(ch8.zoom).toBe(12);
  });

  it("Chapter 8 lng/lat centers Fort Worth (constellation hovers above downtown)", () => {
    const ch8 = CHAPTER_CAMERAS[8]!;
    expect(ch8.longitude).toBeCloseTo(-97.3308, 2);
    expect(ch8.latitude).toBeCloseTo(32.7555, 2);
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

/* -------------------------------------------------------------------------
 * W3 Driver A — Ch6 + Ch9 camera states.
 * Driver B will land Ch7 + Ch8; Driver C will land Ch10. The Partial<Record>
 * type lets each driver add their slot without coordinating on a single edit
 * to the union literal type.
 * ----------------------------------------------------------------------- */

describe("W3 Driver A — Chapter 6 (The Math) lands at Amazon FC DFW5", () => {
  const ch6 = (CHAPTER_CAMERAS as Partial<Record<ChapterId, ChapterCameraState>>)[6];

  it("Ch6 camera state is defined", () => {
    expect(ch6).toBeDefined();
  });

  it("Ch6 lands within Tarrant / north FW (DFW5 ~ 32.99°N, -97.34°W)", () => {
    expect(ch6).toBeDefined();
    expect(ch6!.longitude).toBeGreaterThan(-97.6);
    expect(ch6!.longitude).toBeLessThan(-97.0);
    expect(ch6!.latitude).toBeGreaterThan(32.5);
    expect(ch6!.latitude).toBeLessThan(33.2); // DFW5 sits on north Tarrant edge
  });

  it("Ch6 zoom 14 + pitch 50 — building-altitude tilt over the FC", () => {
    expect(ch6).toBeDefined();
    expect(ch6!.zoom).toBe(14);
    expect(ch6!.pitch).toBe(50);
    expect(ch6!.bearing).toBe(0);
  });

  it("Ch6 reuses W1 EASE_LINEAR_SIG cubic-bezier easing", () => {
    expect(ch6).toBeDefined();
    expect(ch6!.flyToOptions.easing).toEqual([0.32, 0.72, 0, 1]);
  });
});

describe("W3 Driver A — Chapter 9 (Any City) is continental", () => {
  const ch9 = (CHAPTER_CAMERAS as Partial<Record<ChapterId, ChapterCameraState>>)[9];

  it("Ch9 camera state is defined", () => {
    expect(ch9).toBeDefined();
  });

  it("Ch9 is continental US (zoom <= 5; centered roughly Kansas)", () => {
    expect(ch9).toBeDefined();
    expect(ch9!.zoom).toBeLessThanOrEqual(5);
    // Continental view — longitude in continental US.
    expect(ch9!.longitude).toBeGreaterThan(-130);
    expect(ch9!.longitude).toBeLessThan(-65);
    expect(ch9!.latitude).toBeGreaterThan(25);
    expect(ch9!.latitude).toBeLessThan(50);
  });

  it("Ch9 has no tilt or bearing — top-down map for the city dots", () => {
    expect(ch9).toBeDefined();
    expect(ch9!.pitch).toBe(0);
    expect(ch9!.bearing).toBe(0);
  });

  it("Ch9 reuses W1 EASE_LINEAR_SIG cubic-bezier easing", () => {
    expect(ch9).toBeDefined();
    expect(ch9!.flyToOptions.easing).toEqual([0.32, 0.72, 0, 1]);
  });
});
