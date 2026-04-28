/**
 * avatarPath — Spotlight invention #1 (W3 Driver B).
 *
 * Central avatar-position interpolation along Carlos's 5-waypoint path.
 *
 * # Why a separate module
 *
 * Ch7's `CarlosAvatar` needs (lng, lat) at any normalized t in [0..1] so
 * the avatar walks along the real path. W4's life-layers (cursor flashlight
 * ↔ avatar sync) consumes the SAME interpolation. If two surfaces inline
 * the math, drift is inevitable. One module, one test, three+ surfaces
 * (Compound Lens — feeds Ch7 now, W4 later).
 *
 * # Contract
 *
 *   - Source of truth: `paths.ts` `CARLOS_PATH_WAYPOINTS` + `officeRegistry`
 *   - Polyline of N waypoints → N-1 segments → cumulative length
 *   - `positionAt(0)` = home; `positionAt(1)` = final office
 *   - 0 < t < 1 → linear interpolation by cumulative length
 *   - `segmentIndexAt(t)` exposes the active leg for per-leg highlight
 *   - `isLingeringAt(t)` flags pause windows around each interior waypoint
 *
 * # Linger semantics
 *
 * The avatar PAUSES at each office for `AVATAR_LINGER_FRACTION` of a
 * waypoint-radius (in normalized t-space). This keeps the choreography
 * humane: no judge sees the avatar fly past offices like a marathon
 * cyclist. A 10% radius around each interior waypoint reads as a
 * "stop, sit on a bench, breathe" beat.
 */

import { CARLOS_HOME_PIN, CARLOS_PATH_WAYPOINTS } from "./paths";
import { TARRANT_OFFICES } from "./officeRegistry";

/** Lng/lat point in WGS84. */
export interface AvatarPoint {
  longitude: number;
  latitude: number;
}

/** Polyline geometry — coordinates + cumulative segment lengths. */
export interface AvatarPolyline {
  /** N coordinates (one per waypoint). */
  readonly coordinates: ReadonlyArray<readonly [number, number]>;
  /** N-1 segment lengths (great-circle planar approximation). */
  readonly segmentLengths: readonly number[];
  /** Sum of segmentLengths. */
  readonly totalLength: number;
}

/** Normalized linger radius around each interior waypoint (in t-units). */
export const AVATAR_LINGER_FRACTION = 0.1 as const;

function clamp01(t: number): number {
  if (!Number.isFinite(t)) return 0;
  if (t < 0) return 0;
  if (t > 1) return 1;
  return t;
}

function resolveCoord(officeId: string): [number, number] {
  if (officeId === "home") {
    return [CARLOS_HOME_PIN.longitude, CARLOS_HOME_PIN.latitude];
  }
  const office = TARRANT_OFFICES.find((o) => o.id === officeId);
  if (!office) {
    // Honest uncertainty: a missing office id is a data bug, not a runtime
    // hazard. We fall back to home so the avatar never disappears.
    return [CARLOS_HOME_PIN.longitude, CARLOS_HOME_PIN.latitude];
  }
  return [office.longitude, office.latitude];
}

/** Planar distance between two lng/lat points (sufficient for ~10km city scale). */
function planarDistance(a: readonly [number, number], b: readonly [number, number]): number {
  const dLng = b[0] - a[0];
  const dLat = b[1] - a[1];
  return Math.sqrt(dLng * dLng + dLat * dLat);
}

let _cached: AvatarPolyline | null = null;

/** Build the polyline. Memoized — paths are immutable at runtime. */
export function buildAvatarPolyline(): AvatarPolyline {
  if (_cached) return _cached;
  const coordinates: Array<readonly [number, number]> = [];
  for (const wp of CARLOS_PATH_WAYPOINTS) {
    coordinates.push(resolveCoord(wp.office));
  }
  const segmentLengths: number[] = [];
  for (let i = 1; i < coordinates.length; i++) {
    segmentLengths.push(planarDistance(coordinates[i - 1], coordinates[i]));
  }
  const totalLength = segmentLengths.reduce((a, b) => a + b, 0);
  _cached = { coordinates, segmentLengths, totalLength };
  return _cached;
}

/** Compute avatar position at normalized t in [0..1]. */
export function positionAt(t: number): AvatarPoint {
  const poly = buildAvatarPolyline();
  const c = clamp01(t);
  if (c <= 0) {
    const [lng, lat] = poly.coordinates[0];
    return { longitude: lng, latitude: lat };
  }
  if (c >= 1) {
    const last = poly.coordinates[poly.coordinates.length - 1];
    return { longitude: last[0], latitude: last[1] };
  }
  if (poly.totalLength <= 0) {
    const [lng, lat] = poly.coordinates[0];
    return { longitude: lng, latitude: lat };
  }
  const targetDist = c * poly.totalLength;
  let acc = 0;
  for (let i = 0; i < poly.segmentLengths.length; i++) {
    const segLen = poly.segmentLengths[i];
    if (acc + segLen >= targetDist) {
      const localT = segLen <= 0 ? 0 : (targetDist - acc) / segLen;
      const a = poly.coordinates[i];
      const b = poly.coordinates[i + 1];
      return {
        longitude: a[0] + (b[0] - a[0]) * localT,
        latitude: a[1] + (b[1] - a[1]) * localT,
      };
    }
    acc += segLen;
  }
  const last = poly.coordinates[poly.coordinates.length - 1];
  return { longitude: last[0], latitude: last[1] };
}

/** Active segment index (0..N-2) at normalized t. */
export function segmentIndexAt(t: number): number {
  const poly = buildAvatarPolyline();
  const N = poly.coordinates.length;
  if (N < 2) return 0;
  const c = clamp01(t);
  if (c >= 1) return N - 2;
  if (c <= 0) return 0;
  if (poly.totalLength <= 0) return 0;
  const targetDist = c * poly.totalLength;
  let acc = 0;
  for (let i = 0; i < poly.segmentLengths.length; i++) {
    const segLen = poly.segmentLengths[i];
    if (acc + segLen >= targetDist) return i;
    acc += segLen;
  }
  return N - 2;
}

/** True when t lands inside the linger window around an interior waypoint. */
export function isLingeringAt(t: number): boolean {
  const poly = buildAvatarPolyline();
  const N = poly.coordinates.length;
  if (N < 3) return false;
  const c = clamp01(t);
  // Each interior waypoint k (k=1..N-2) sits at t = k/(N-1).
  for (let k = 1; k <= N - 2; k++) {
    const tk = k / (N - 1);
    if (Math.abs(c - tk) <= AVATAR_LINGER_FRACTION / 2) return true;
  }
  return false;
}

/** Test-only reset. */
export function _resetAvatarPathCacheForTests(): void {
  _cached = null;
}
