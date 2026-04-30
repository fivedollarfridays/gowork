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
import { getEmployerById, EMPLOYER_DFW5_ID } from "../employerRegistry";

export const TRINITY_METRO_SOURCE_ID = "trinity-metro-source";
export const TRINITY_METRO_LINE_ID = "trinity-metro-line";

/** Routes singled out for editorial highlight (Carlos's commute). */
export const TRINITY_METRO_HIGHLIGHTED_ROUTE_IDS: readonly string[] = ["4", "6"] as const;

/**
 * W3 Driver A — Bus 4 → DFW5 corridor accent (T3.3).
 *
 * Identifies the derived GeoJSON line that connects Bus 4's served
 * downtown corridor to Amazon FC DFW5. The corridor is a programmatic
 * accent (NOT in the Trinity Metro GTFS feed) — it shows the route the
 * REAL Bus 4 + transfer takes to reach DFW5. Ch6 toggles its visibility
 * via feature-state when the chapter is active.
 */
export const BUS4_TO_DFW5_CORRIDOR = {
  id: "trinity-metro-bus4-dfw5-corridor",
  routeId: "4",
} as const;

import { MAPBOX_COLORS } from "../colors";
const CYAN = MAPBOX_COLORS.cyan;
const AMBER = MAPBOX_COLORS.amber;

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

/** GeoJSON LineString for the Bus 4 → DFW5 corridor accent. */
export interface CorridorFeature {
  type: "Feature";
  properties: { route: string; corridor: string };
  geometry: { type: "LineString"; coordinates: [number, number][] };
}

/**
 * Build the Bus 4 → DFW5 corridor feature programmatically.
 *
 * Three control points: Carlos's neighborhood (76119) → downtown FW
 * (Bus 4 spine) → DFW5 (Heritage Pkwy / Haslet). The middle leg is the
 * actual Bus-4 corridor; the final leg is a derived "transfer + walk"
 * vector to DFW5 — not a Trinity Metro route by itself.
 */
export function buildBus4Dfw5CorridorFeature(): CorridorFeature {
  const dfw5 = getEmployerById(EMPLOYER_DFW5_ID);
  // 76119 representative block (Carlos's home, NOT exact address — PII safe).
  const carlosBlock: [number, number] = [-97.27, 32.71];
  // Downtown FW Trinity Metro hub (T&P/Intermodal Transportation Center).
  const downtownHub: [number, number] = [-97.3289, 32.7549];
  // DFW5 (fallback to coords if registry hasn't been initialized in tests).
  const dest: [number, number] = dfw5
    ? [dfw5.longitude, dfw5.latitude]
    : [-97.3399, 32.9942];
  return {
    type: "Feature",
    properties: { route: BUS4_TO_DFW5_CORRIDOR.routeId, corridor: "dfw5" },
    geometry: {
      type: "LineString",
      coordinates: [carlosBlock, downtownHub, dest],
    },
  };
}
