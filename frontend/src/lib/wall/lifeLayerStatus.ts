/**
 * Spotlight invention #2 (W4 Driver D) — lifeLayerStatus.
 *
 * Pure derivation: given the four life-layer signals (time-of-day phase,
 * global scroll progress, cursor-in-map flag, idle flag), return an
 * editorial-friendly status:
 *   `{ active: 'time' | 'cursor' | 'live' | 'idle', mood: '...' }`
 *
 * Single source of truth for which layer is "speaking loudest" at any
 * moment. Consumed by:
 *
 *   - The OG card composer (Spotlight #1) — to pick a hero copy line
 *     that matches the active layer (e.g. "still scrolling at 11pm" =
 *     night/idle).
 *   - The dev-overlay /dev/life-layers diagnostic.
 *   - Future telemetry (record which layer dominated a session).
 *
 * # Priority order
 *
 * `idle` wins (the abandoned reader is the most editorial signal),
 * then `cursor-in-map` (active engagement with the map), then `live`
 * (mid-scroll), then `time` (the static phase-of-day fallback).
 *
 * # Why a pure function
 *
 * Same logic, three runtimes: Edge route (OG card), browser dev overlay,
 * and Node test. Pure ⇒ composable.
 */

import type { W4Phase } from "./timeOfDayPalette";

/** Which life-layer is the dominant signal right now. */
export type LifeLayerKey = "time" | "cursor" | "live" | "idle";

export interface LifeLayerStatusInput {
  phase: W4Phase;
  /** 0..1 GLOBAL scroll progress across the whole Wall. */
  globalProgress: number;
  /** True when the cursor is over the Mapbox canvas. */
  cursorInsideMap: boolean;
  /** True after the idle threshold (default 30s) of no input. */
  idle: boolean;
}

export interface LifeLayerStatus {
  active: LifeLayerKey;
  /** A short editorial description of the current mood. */
  mood: string;
}

/** Phase → editorial mood line. Single source for press kit + OG card +
 *  dev overlay. Kept short (≤ 80 chars each) so they fit OG card layouts. */
export const PHASE_TO_MOOD: Record<W4Phase, string> = {
  dawn: "Amber morning light. The first scrollers of the day arrive.",
  morning: "Trinity Metro is running. Carlos is on Bus 4.",
  noon: "Sun overhead. The wall is in full daylight.",
  afternoon: "The cliff math is sharp this hour.",
  dusk: "Rose-gold over Fort Worth. The graph is breathing.",
  night: "The wall stays open after the offices close.",
};

/** Derive the dominant life-layer + an editorial mood line. */
export function deriveLifeLayerStatus(
  input: LifeLayerStatusInput,
): LifeLayerStatus {
  const { phase, globalProgress, cursorInsideMap, idle } = input;
  const mood = PHASE_TO_MOOD[phase];
  if (idle) return { active: "idle", mood };
  if (cursorInsideMap) return { active: "cursor", mood };
  if (globalProgress > 0) return { active: "live", mood };
  return { active: "time", mood };
}
