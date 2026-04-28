/**
 * Core type definitions for The Wall (W1–W4).
 *
 * Pure types — no runtime code, no imports. Re-exported via the
 * `frontend/src/lib/wall/index.ts` hub for ergonomic consumption.
 */

/** Time-of-day phase. Drives accent shift + Mapbox sky styling. */
export type TimePhase = "morning" | "day" | "evening" | "night";

/** Accent color shifted by phase (and W4 weather/temperature overrides). */
export type AccentShift = "cyan" | "amber" | "rose" | "navy";

/** 1-indexed chapter id (the Wall has 10 chapters). */
export type ChapterId = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

/** Mapbox view-state (camera) snapshot. */
export interface CameraState {
  lng: number;
  lat: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

/** Mapbox layer descriptor (paint omitted; per-chapter style files own it). */
export interface MapboxLayer {
  id: string;
  type: string;
  source: string;
  paint?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  filter?: unknown[];
}

/** Audio cue ids exposed by lib/wall/sound. */
export type SoundId =
  | "footstep"
  | "paper-rustle"
  | "calculator-click"
  | "chime"
  | "wind-ambient";

/** ISO-639 locale codes the app currently supports. */
export type LocaleCode = "en" | "es";

/** Barrier categories visualized in W3 chapters 6–10. */
export type BarrierType = "criminal-record" | "transit" | "childcare" | "credit";

/** A node in the barrier graph (W3 — interactive 3D barrier visualization). */
export interface BarrierGraphNode {
  id: string;
  type: BarrierType;
  /** 0..1, drives node radius + edge intensity. */
  severity: number;
  /** Optional grouping for cluster layouts. */
  cluster?: string;
}

/** Per-chapter narrative + camera state. */
export interface ChapterState {
  id: ChapterId;
  /** Slug used in URLs (e.g. "the-wall"). */
  slug: string;
  /** Camera target for this chapter. */
  camera: CameraState;
  /** Color accent override for this chapter (W4). */
  accentShift: AccentShift;
  /** Optional barrier focus when chapter highlights a single barrier. */
  barrierFocus?: BarrierType;
}

/** RUM session id — opaque hashed string per privacy policy. */
export type RumSessionId = string & { readonly __brand: "RumSessionId" };
