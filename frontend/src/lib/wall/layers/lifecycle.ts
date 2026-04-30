/**
 * Shared register/remove helpers for Wall data layers (DRY).
 *
 * Every `WallDataLayer` shares the same lifecycle:
 *   register(map) → addSource (if not present) → addLayer for each cfg
 *   remove(map)   → removeLayer (reverse order, if present) → removeSource
 *
 * Idempotency is mandatory: composer (T2.17) may register/remove on map
 * style changes; the layer must never throw if the source is already
 * registered or already gone.
 */

import type { MapboxLikeMap, MapboxLayerSpec, GeoJSONSourceConfig } from "./types";

export function registerLayer(
  map: MapboxLikeMap,
  sourceId: string,
  sourceConfig: GeoJSONSourceConfig,
  layers: readonly MapboxLayerSpec[],
): void {
  if (!map.getSource(sourceId)) {
    map.addSource(sourceId, sourceConfig);
  }
  for (const layer of layers) {
    if (!map.getLayer(layer.id)) {
      map.addLayer(layer);
    }
  }
}

export function removeLayer(
  map: MapboxLikeMap,
  sourceId: string,
  layerIds: readonly string[],
): void {
  // Reverse order so a layer that depends on another below it is torn
  // down first (Mapbox doesn't strictly require this but it matches the
  // composer's documented z-order contract).
  for (let i = layerIds.length - 1; i >= 0; i--) {
    const id = layerIds[i];
    if (map.getLayer(id)) {
      map.removeLayer(id);
    }
  }
  if (map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
}
