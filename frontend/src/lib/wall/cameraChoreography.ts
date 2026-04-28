/**
 * Camera choreography — per-chapter view-state (T2.4, T2.7).
 *
 * **Driver-coordination note.** This module is the convergent dependency
 * for chapters 1-5 (W2) AND 6-10 (W3). Driver A owns the full
 * `CHAPTER_CAMERAS` map; **Driver B (this lane) ships only entries 1-3**
 * (the chapters Driver B implements). On merge with Driver A's WallContainer
 * lane, the union of both definitions becomes the authoritative
 * `CHAPTER_CAMERAS`. The TypeScript shape — `ChapterCameraState` — is the
 * contract.
 *
 * Cubic-bezier easing for `flyToOptions.easing` is sourced from W1 motion
 * tokens (see `frontend/src/app/styles/tokens/motion.css` — Linear-style
 * preset). Driver A wires the orchestrator (T2.9); this file owns the data.
 */

export interface ChapterCameraState {
  longitude: number;
  latitude: number;
  zoom: number;
  /** Mapbox pitch in degrees (0 = top-down, 60 = max tilt). */
  pitch: number;
  /** Mapbox bearing in degrees (0 = north up). */
  bearing: number;
  /** Mapbox flyTo options — speed/curve/duration override per chapter. */
  flyToOptions: {
    /** flyTo speed multiplier; lower = slower. */
    speed: number;
    /** Mapbox flyTo curve; higher = more zoom-out arc. */
    curve: number;
    /** Optional explicit duration override (ms). */
    duration?: number;
    /** Cubic-bezier easing array — Linear-style preset from W1 tokens. */
    easing: readonly [number, number, number, number];
  };
}

/** W1 motion-token "Linear-style" cubic-bezier preset. */
const LINEAR_EASING: readonly [number, number, number, number] = [
  0.32, 0.72, 0, 1,
];

/**
 * Initial camera state — Fort Worth overview (T2.4).
 *
 * Coordinates: Fort Worth centroid at (-97.3308, 32.7555). Zoom 11 + no
 * tilt is the "loading-completed default" the Mapbox map boots into.
 */
export const INITIAL_CAMERA = {
  longitude: -97.3308,
  latitude: 32.7555,
  zoom: 11,
  pitch: 0,
  bearing: 0,
} as const;

/**
 * Per-chapter camera states. Indexed by 1..10 chapter id.
 *
 * **Driver B owns 1-3 only.** Driver A appends 4-5 (and W3 appends 6-10)
 * to this same map on merge. Tests in `cameraChoreography.test.ts` only
 * assert 1-3 from this lane; Driver A's lane adds 4-5 assertions.
 */
export const CHAPTER_CAMERAS: Record<number, ChapterCameraState> = {
  1: {
    // Continental — top-down America centered approx Kansas (-98, 39).
    longitude: -98,
    latitude: 39,
    zoom: 3,
    pitch: 0,
    bearing: 0,
    flyToOptions: { speed: 0.6, curve: 1.42, duration: 2400, easing: LINEAR_EASING },
  },
  2: {
    // City arrival — Fort Worth at altitude with 3D tilt.
    longitude: INITIAL_CAMERA.longitude,
    latitude: INITIAL_CAMERA.latitude,
    zoom: 11,
    pitch: 60,
    bearing: 0,
    flyToOptions: { speed: 1.4, curve: 1.42, duration: 3000, easing: LINEAR_EASING },
  },
  3: {
    // Neighborhood — zoom to 76119 with slight tilt toward east.
    longitude: -97.293,
    latitude: 32.713,
    zoom: 14,
    pitch: 60,
    bearing: 25,
    flyToOptions: { speed: 1.0, curve: 1.42, duration: 2400, easing: LINEAR_EASING },
  },
};
