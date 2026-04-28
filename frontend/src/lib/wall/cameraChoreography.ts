/**
 * T2.4 + T2.7 — Mapbox camera choreography for The Wall.
 *
 * Single source of truth for every chapter's Mapbox camera state.
 * Chapters 1–5 ship in W2; chapters 6–10 (W3) extend `CHAPTER_CAMERAS`.
 * Sub-chapters (Ch4a–Ch4d) are addressed via `TRANSITION_SPEEDS` keys —
 * the parent state is shared, only bearing tilts differ.
 *
 * Why one module instead of per-chapter literals: chapter components AND
 * the flyTo orchestrator both read camera state. If five chapter files
 * re-define their own camera, drift is inevitable. One config, one type,
 * one snapshot test.
 *
 * Spotlight (Wisdom Lens — Driver A): the brief asked for "per-chapter"
 * states; the structural answer is "one shared module, indexed by
 * chapter id." That's the contract Drivers B/C consume read-only.
 */

import { EASE_LINEAR_SIG } from "./tokens";
import type { ChapterId } from "./types";

/** W2 ships chapters 1–5; W3 extends with 6–10. Sub-chapters 4a/4b/4c/4d
 *  share Chapter 4's camera state (bearing tilts handled at runtime). */
export type W2ChapterId = Extract<ChapterId, 1 | 2 | 3 | 4 | 5>;
/** Chapters added by W3 dispatch (Drivers A: 6,9; B: 7,8; C: 10). */
export type W3ChapterId = Extract<ChapterId, 6 | 7 | 8 | 9 | 10>;
export type { ChapterId };

/** Mapbox camera + flyTo options. Mirrors mapbox-gl `CameraOptions`. */
export interface ChapterCameraState {
  /** Longitude in WGS84 (Fort Worth ~ -97.33). */
  longitude: number;
  /** Latitude in WGS84 (Fort Worth ~ 32.76). */
  latitude: number;
  /** Mapbox zoom level (0 = world, 22 = building). */
  zoom: number;
  /** Pitch in degrees (0 = top-down, 60 = max tilt). */
  pitch: number;
  /** Bearing in degrees (0 = north, clockwise). */
  bearing: number;
  /** Mapbox flyTo options — curve/speed/easing. */
  flyToOptions: {
    /** Mapbox flyTo curve — 1.2 is balanced cinematic; 1.42 is "swoop." */
    curve: number;
    /** Mapbox flyTo speed multiplier — 1.0 is default. Tuned per pair. */
    speed: number;
    /** Easing as cubic-bezier control points (W1 EASE_LINEAR_SIG). */
    easing: readonly [number, number, number, number];
  };
}

/** Fort Worth city centroid — the booted-into-default state. */
export const INITIAL_CAMERA: ChapterCameraState = {
  longitude: -97.3308,
  latitude: 32.7555,
  zoom: 11,
  pitch: 0,
  bearing: 0,
  flyToOptions: {
    curve: 1.2,
    speed: 1.0,
    easing: EASE_LINEAR_SIG,
  },
};

/**
 * Per-chapter camera states for W2 (1–5). W3 extends this object with
 * 6–10 across multiple drivers (A: 6, 9; B: 7, 8; C: 10). Type is a
 * Partial-Record so each driver can extend its own indices without
 * coupling to the others' lanes; runtime asserts presence per use-site.
 *
 * Coordinates verified within Tarrant County bounding box (lng -97.6 to
 * -97.0, lat 32.5 to 33.0) for chapters 2–5; chapter 1 is continental
 * (centered ~ -98, 39 — north-central US). Chapter 10 returns to the
 * Fort Worth overhead frame to mirror the opening "we've returned home"
 * narrative beat.
 */
export const CHAPTER_CAMERAS: Readonly<Partial<Record<ChapterId, ChapterCameraState>>> & Record<W2ChapterId | 10, ChapterCameraState> = {
  // Ch1 — Continental top-down America. Centered roughly Kansas; W1 city
  // lights layer (T2.20) makes FW + Montgomery glow brighter than other
  // metros so the eye is led down to Fort Worth in Ch2.
  1: {
    longitude: -98.0,
    latitude: 39.0,
    zoom: 3,
    pitch: 0,
    bearing: 0,
    flyToOptions: { curve: 1.42, speed: 1.4, easing: EASE_LINEAR_SIG },
  },
  // Ch2 — City Arrival. Fort Worth at altitude with 3D tilt. The 3D
  // buildings extrusion (T2.24) becomes visible at zoom > 13, so Ch2's
  // zoom 11 stays edge-of-buildings — Ch3 zooms further.
  2: {
    longitude: -97.3308,
    latitude: 32.7555,
    zoom: 11,
    pitch: 60,
    bearing: 0,
    flyToOptions: { curve: 1.2, speed: 1.0, easing: EASE_LINEAR_SIG },
  },
  // Ch3 — Neighborhood. ZIP 76119 (Carlos's representative block).
  // Bearing tilted east toward downtown so the camera is "looking out"
  // from the neighborhood, not away from it.
  3: {
    longitude: -97.2700,
    latitude: 32.7100,
    zoom: 14,
    pitch: 60,
    bearing: 25,
    flyToOptions: { curve: 1.2, speed: 0.9, easing: EASE_LINEAR_SIG },
  },
  // Ch4 — The Wall (parent). Mid-altitude over Fort Worth so all four
  // sub-chapters can pivot bearing without re-flying. Sub-chapters
  // (Ch4a–Ch4d) share this camera and only adjust bearing.
  4: {
    longitude: -97.3308,
    latitude: 32.7555,
    zoom: 13,
    pitch: 50,
    bearing: 0,
    flyToOptions: { curve: 1.2, speed: 1.0, easing: EASE_LINEAR_SIG },
  },
  // Ch5 — The Labyrinth. Bird's-eye over Tarrant County's office grid.
  // Pitch 30 (less than Ch4's 50) so the chaotic SVG path overlay reads
  // as a 2D maze rather than a tilted 3D bowl.
  5: {
    longitude: -97.3308,
    latitude: 32.7555,
    zoom: 11,
    pitch: 30,
    bearing: 0,
    flyToOptions: { curve: 1.2, speed: 1.0, easing: EASE_LINEAR_SIG },
  },
  // Ch10 — Find Your Path. Camera returns to Fort Worth at zoom 11,
  // pitch 0 (top-down), bearing 0 (north-up). The "we've returned home"
  // framing — same lng/lat as INITIAL_CAMERA so the cinematic dolly
  // ends where it started, ready for the View Transitions handoff into
  // /assess. Slightly slower flyTo (speed 0.85) so the final beat feels
  // like a cinematic settle, not a race.
  10: {
    longitude: -97.3308,
    latitude: 32.7555,
    zoom: 11,
    pitch: 0,
    bearing: 0,
    flyToOptions: { curve: 1.2, speed: 0.85, easing: EASE_LINEAR_SIG },
  },
};

/**
 * Per-pair flyTo speed table. Mapbox `flyTo({ speed })` defaults to 1.2;
 * we tune longer transitions UP (cinematic dolly) and shorter pivots
 * DOWN (snappy reframe). Keys are `"<from>-><to>"` where each side is
 * either a chapter number or a sub-chapter id.
 *
 * Spotlight (Permission — Driver A creative authority): Mapbox's default
 * speed makes Ch1→Ch2 (continental → city) feel slow. Bumping to 1.4
 * gives the camera a sense of intent without sacrificing legibility.
 */
export const TRANSITION_SPEEDS: Readonly<Record<string, number>> = {
  "1->2": 1.4,   // Continental → City: long dolly, slightly faster
  "2->3": 1.0,   // City → Neighborhood: standard cinematic
  "3->4": 1.0,   // Neighborhood → Mid-altitude: standard
  "4->5": 0.9,   // Mid → Labyrinth: subtle reframe
  "4a->4b": 0.6, // Sub-chapter bearing pivots are short and snappy.
  "4b->4c": 0.6,
  "4c->4d": 0.6,
  // W3: Driver C owns 9->10 (final beat — settle into FW overhead).
  // Drivers A+B own 5->6, 6->7, 7->8, 8->9 in their respective lanes.
  "9->10": 0.85,
};
