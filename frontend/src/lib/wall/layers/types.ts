/**
 * Shared types for Wall data-layer modules.
 *
 * Each `WallDataLayer` is a pure config + lifecycle pair consumed by
 * `MapboxScene` (Driver A) via the layers `index.ts` composer (T2.17).
 * Modules never reach into Mapbox state directly outside `register` /
 * `remove`; they own only the config + lifecycle, never the map.
 */

/** Minimal Mapbox map surface this lane needs — keeps tests light. */
export interface MapboxLikeMap {
  addSource: (id: string, source: unknown) => void;
  removeSource: (id: string) => void;
  addLayer: (layer: unknown) => void;
  removeLayer: (id: string) => void;
  getSource: (id: string) => unknown;
  getLayer: (id: string) => unknown;
  setPaintProperty?: (layerId: string, prop: string, value: unknown) => void;
  setLayoutProperty?: (layerId: string, prop: string, value: unknown) => void;
}

/** Mapbox GeoJSON source config with offline-committed data. */
export interface GeoJSONSourceConfig {
  type: "geojson";
  /** Public-relative URL — committed under /data/wall/. */
  data: string;
  /** Optional Mapbox `generateId` for feature-state hover. */
  generateId?: boolean;
  /** Optional Mapbox `lineMetrics` (enables line-progress for line-gradient). */
  lineMetrics?: boolean;
}

/** Mapbox layer descriptor (paint expressions allowed). */
export interface MapboxLayerSpec {
  id: string;
  type: string;
  source: string;
  paint?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  filter?: unknown[];
  minzoom?: number;
  maxzoom?: number;
}

/**
 * Public API of every Wall data-layer module.
 *
 * Modules expose this object so the composer can register/remove without
 * caring about implementation specifics.
 */
export interface WallDataLayer {
  /** Stable source id — used by the composer for ordering + cleanup. */
  readonly sourceId: string;
  /** Stable layer ids — order is z-order (last = on top). */
  readonly layerIds: readonly string[];
  /** GeoJSON source config (committed offline data). */
  readonly sourceConfig: GeoJSONSourceConfig;
  /** Mapbox layer configs (rendered in array order = z-order). */
  readonly layerConfigs: readonly MapboxLayerSpec[];
  /** Adds source + layers; idempotent. */
  register(map: MapboxLikeMap): void;
  /** Removes layers (reverse order) then source; idempotent. */
  remove(map: MapboxLikeMap): void;
}
