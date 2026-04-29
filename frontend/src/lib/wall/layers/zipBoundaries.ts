/**
 * ZIP 76119 boundary layer (T2.13).
 *
 * Renders the Carlos-ZIP polygon as a fill (low opacity) + a line
 * (higher contrast outline). Source GeoJSON is committed offline at
 * `frontend/public/data/wall/zip-76119.geojson` (US Census TIGER/Line
 * ZCTA dataset, public domain — see T2.76 LICENSES note).
 *
 * Paint uses W1 design tokens via Mapbox `text-color`/`fill-color`
 * indirection through CSS custom properties — Mapbox does NOT read CSS
 * vars at runtime, so we resolve them to literal OKLCH at the style level
 * (the custom Mapbox style, T2.18, holds the resolved values). For W2's
 * default `mapbox://styles/mapbox/dark-v11` fallback, we use OKLCH
 * literals matching W1 `--accent-amber` and `--accent-amber-strong`.
 */

import { registerLayer, removeLayer } from "./lifecycle";
import type {
  GeoJSONSourceConfig,
  MapboxLayerSpec,
  MapboxLikeMap,
  WallDataLayer,
} from "./types";

export const ZIP_BOUNDARIES_SOURCE_ID = "zip-76119-source";
export const ZIP_BOUNDARIES_FILL_ID = "zip-76119-fill";
export const ZIP_BOUNDARIES_LINE_ID = "zip-76119-line";

/** Mapbox doesn't parse oklch() — we precompute the sRGB hex equivalent
 *  of the W1 --accent-amber tokens via lib/wall/colors.ts. */
import { MAPBOX_COLORS } from "../colors";
const AMBER = MAPBOX_COLORS.amber;
const AMBER_STRONG = MAPBOX_COLORS.amberStrong;

const sourceConfig: GeoJSONSourceConfig = {
  type: "geojson",
  data: "/data/wall/zip-76119.geojson",
  generateId: true,
};

const fillLayer: MapboxLayerSpec = {
  id: ZIP_BOUNDARIES_FILL_ID,
  type: "fill",
  source: ZIP_BOUNDARIES_SOURCE_ID,
  paint: {
    "fill-color": AMBER,
    "fill-opacity": 0.15,
  },
  // Visible from zoom 8 up; pointless at continental zoom.
  minzoom: 8,
};

const lineLayer: MapboxLayerSpec = {
  id: ZIP_BOUNDARIES_LINE_ID,
  type: "line",
  source: ZIP_BOUNDARIES_SOURCE_ID,
  paint: {
    "line-color": AMBER_STRONG,
    "line-width": 1.5,
    "line-opacity": 0.6,
  },
  minzoom: 8,
};

const layerConfigs: readonly MapboxLayerSpec[] = [fillLayer, lineLayer] as const;
const layerIds: readonly string[] = [ZIP_BOUNDARIES_FILL_ID, ZIP_BOUNDARIES_LINE_ID] as const;

export const zipBoundariesLayer: WallDataLayer = {
  sourceId: ZIP_BOUNDARIES_SOURCE_ID,
  layerIds,
  sourceConfig,
  layerConfigs,
  register(map: MapboxLikeMap) {
    registerLayer(map, ZIP_BOUNDARIES_SOURCE_ID, sourceConfig, layerConfigs);
  },
  remove(map: MapboxLikeMap) {
    removeLayer(map, ZIP_BOUNDARIES_SOURCE_ID, layerIds);
  },
};
