/**
 * Wall data-layer composer (T2.17).
 *
 * Single composer module that registers all W2 data layers on the
 * Mapbox map in correct z-order. Driver A's `MapboxScene.tsx` calls
 * `registerAllLayers(map)` on `map.on('load')` and `removeAllLayers(map)`
 * on cleanup.
 *
 * # Z-order (bottom → top)
 *
 *   1. zip boundaries — fill + line under everything else
 *   2. trinity metro  — bus polylines on top of ZIP fill
 *   3. offices        — symbols above transit lines
 *   4. carlos path    — pin + (future) trace above offices
 *   5. jobs by zip    — employer dots above the path
 *
 * Cleanup reverses the order so Mapbox never holds a layer referencing
 * a removed source.
 *
 * Marker sprite registration (T2.16) is intentionally separate —
 * `MapboxScene` calls `registerMarkerSymbols(map)` BEFORE the offices
 * symbol layer mounts so `icon-image` lookups resolve.
 */

import { zipBoundariesLayer } from "./zipBoundaries";
import { trinityMetroLayer } from "./trinityMetro";
import { officesLayer } from "./offices";
import { carlosPathLayer } from "./carlosPath";
import { jobsByZipLayer } from "./jobsByZip";
import type { MapboxLikeMap, WallDataLayer } from "./types";

/** Documented z-order (bottom → top). */
export const WALL_LAYER_ORDER: readonly string[] = [
  "zipBoundaries",
  "trinityMetro",
  "offices",
  "carlosPath",
  "jobsByZip",
] as const;

const LAYERS_IN_ORDER: readonly WallDataLayer[] = [
  zipBoundariesLayer,
  trinityMetroLayer,
  officesLayer,
  carlosPathLayer,
  jobsByZipLayer,
] as const;

/**
 * Register all data layers on the Mapbox map. Idempotent — safe to call
 * after a Mapbox style change (sources persist across style swaps).
 */
export function registerAllLayers(map: MapboxLikeMap): void {
  for (const layer of LAYERS_IN_ORDER) {
    layer.register(map);
  }
}

/**
 * Remove all data layers (reverse z-order). Idempotent — safe before
 * any register.
 */
export function removeAllLayers(map: MapboxLikeMap): void {
  for (let i = LAYERS_IN_ORDER.length - 1; i >= 0; i--) {
    LAYERS_IN_ORDER[i].remove(map);
  }
}

/**
 * Re-export the per-layer modules so consumers (Driver A's MapboxScene,
 * Spotlight inventions like the dev debug panel T2.89) can target a
 * single layer without reaching into individual modules.
 */
export { zipBoundariesLayer } from "./zipBoundaries";
export { trinityMetroLayer } from "./trinityMetro";
export { officesLayer } from "./offices";
export { carlosPathLayer } from "./carlosPath";
export { jobsByZipLayer } from "./jobsByZip";
export type { WallDataLayer, MapboxLikeMap } from "./types";
