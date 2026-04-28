/**
 * Trinity Metro routes layer (T2.11).
 *
 * Renders Trinity Metro bus routes as cyan polylines. **Bus 4** and
 * **Bus 6** are Carlos's commute spine (referenced verbatim in Ch4a +
 * Ch4b editorial: "4.8 miles. Bus 4 + Bus 6 = 71 minutes.").
 *
 * **Data provenance.** The committed GeoJSON is built offline via
 * `frontend/scripts/build-trinity-metro-geojson.mjs` (T2.11) which reads
 * the published Trinity Metro GTFS feed (https://ride.trinitymetro.org/).
 * Refresh cadence: pre-submission only. T2.73 enforces a freshness gate
 * via metadata sidecar.
 *
 * **Trinity Metro brand colors.** T2.123 enrichment switches the
 * highlighted Bus-4 paint to Trinity Metro's published primary blue for
 * editorial accuracy. W2 Wave 2 ships the cyan default + amber highlight
 * via feature-state; the brand-blue swap is a follow-up that touches
 * only the paint expression.
 */

import { registerLayer, removeLayer } from "./lifecycle";
import type {
  GeoJSONSourceConfig,
  MapboxLayerSpec,
  MapboxLikeMap,
  WallDataLayer,
} from "./types";

export const TRINITY_METRO_SOURCE_ID = "trinity-metro-source";
export const TRINITY_METRO_LINE_ID = "trinity-metro-line";

/** Routes singled out for editorial highlight (Carlos's commute). */
export const TRINITY_METRO_HIGHLIGHTED_ROUTE_IDS: readonly string[] = ["4", "6"] as const;

const CYAN = "oklch(0.78 0.13 215)";
const AMBER = "oklch(0.78 0.16 75)";

const sourceConfig: GeoJSONSourceConfig = {
  type: "geojson",
  data: "/data/wall/trinity-metro.geojson",
  generateId: true,
};

/**
 * Paint expression: highlighted feature-state → amber, otherwise cyan.
 * Driver A's flyTo orchestrator sets feature-state on chapter enter.
 */
const lineLayer: MapboxLayerSpec = {
  id: TRINITY_METRO_LINE_ID,
  type: "line",
  source: TRINITY_METRO_SOURCE_ID,
  paint: {
    "line-color": [
      "case",
      ["boolean", ["feature-state", "highlighted"], false],
      AMBER,
      CYAN,
    ],
    "line-width": [
      "case",
      ["boolean", ["feature-state", "highlighted"], false],
      3,
      1.5,
    ],
    "line-opacity": [
      "case",
      ["boolean", ["feature-state", "highlighted"], false],
      0.9,
      0.3,
    ],
  },
  layout: {
    "line-cap": "round",
    "line-join": "round",
  },
  minzoom: 9,
};

const layerConfigs: readonly MapboxLayerSpec[] = [lineLayer] as const;
const layerIds: readonly string[] = [TRINITY_METRO_LINE_ID] as const;

export const trinityMetroLayer: WallDataLayer = {
  sourceId: TRINITY_METRO_SOURCE_ID,
  layerIds,
  sourceConfig,
  layerConfigs,
  register(map: MapboxLikeMap) {
    registerLayer(map, TRINITY_METRO_SOURCE_ID, sourceConfig, layerConfigs);
  },
  remove(map: MapboxLikeMap) {
    removeLayer(map, TRINITY_METRO_SOURCE_ID, layerIds);
  },
};
