/**
 * T2.9 — flyToOrchestrator.
 *
 * Pure-function camera transition. Given the current and next chapter
 * ids, calls `flyTo` on the Mapbox map with the configured camera state.
 * The reduced-motion path collapses to `jumpTo` (instant cut).
 *
 * The hook layer (T2.13) wires this to scroll-progress events and adds:
 *   - debouncing (avoid rapid-fire flyTos on fast scrolls)
 *   - user-gesture suppression window (T2.111 — drag → 2s freeze)
 *   - tab-blur pause (T2.112)
 *
 * Keeping the transition pure means each layer is independently testable.
 *
 * Spotlight (Resilience Lens — Driver A): the brief said "flyTo
 * orchestrator with reduced-motion fallback." The structural answer is
 * one pure function with two branches; complexity stacks at the hook
 * layer, not here.
 */

import {
  CHAPTER_CAMERAS,
  TRANSITION_SPEEDS,
  type ChapterCameraState,
  type ChapterId,
} from "./cameraChoreography";

/** Minimal Mapbox map surface this module relies on. Mapbox-gl's `Map`
 *  exposes both methods; we narrow so tests can pass plain spies. */
export interface FlyToCapableMap {
  flyTo: (options: {
    center?: [number, number];
    zoom?: number;
    pitch?: number;
    bearing?: number;
    curve?: number;
    speed?: number;
    easing?: (t: number) => number;
  }) => void;
  jumpTo: (options: {
    center?: [number, number];
    zoom?: number;
    pitch?: number;
    bearing?: number;
  }) => void;
}

export interface CameraTransitionParams {
  /** Mapbox map instance — null is graceful no-op. */
  map: FlyToCapableMap | null;
  /** Departing chapter id (used to look up TRANSITION_SPEEDS pair). */
  from: ChapterId;
  /** Destination chapter id (used to look up CHAPTER_CAMERAS state). */
  to: ChapterId;
  /** When true, use jumpTo (instant cut) — honors prefers-reduced-motion. */
  reducedMotion: boolean;
}

const DEFAULT_TRANSITION_SPEED = 1.0;

/** Convert a cubic-bezier control-point tuple into an easing fn for
 *  Mapbox's `flyTo`. Mapbox accepts (t: number) => number; we approximate
 *  the cubic-bezier curve via Mapbox's internal easing — for now we leave
 *  `easing` undefined so Mapbox uses its own cubic. T2.113 enrichment can
 *  upgrade to a true cubic-bezier if needed. */

/** The W2 contract: trigger a camera flight (or instant cut) between
 *  chapters. Pure: no side effects beyond the map call. */
export function triggerCameraTransition(params: CameraTransitionParams): void {
  const { map, from, to, reducedMotion } = params;
  if (!map) return;
  // Lookup is permissive: W3 chapter ids (6–10) are not in the W2 map yet,
  // so undefined is the graceful "no transition known" path.
  const dest = (CHAPTER_CAMERAS as Record<number, ChapterCameraState | undefined>)[to];
  if (!dest) return;

  const center: [number, number] = [dest.longitude, dest.latitude];

  if (reducedMotion) {
    map.jumpTo({
      center,
      zoom: dest.zoom,
      pitch: dest.pitch,
      bearing: dest.bearing,
    });
    return;
  }

  const pairKey = `${from}->${to}`;
  const speed = TRANSITION_SPEEDS[pairKey] ?? DEFAULT_TRANSITION_SPEED;

  map.flyTo({
    center,
    zoom: dest.zoom,
    pitch: dest.pitch,
    bearing: dest.bearing,
    curve: dest.flyToOptions.curve,
    speed,
  });
}
