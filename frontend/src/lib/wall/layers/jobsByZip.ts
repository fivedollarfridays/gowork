/**
 * Jobs-by-ZIP employer markers (T2.15).
 *
 * Renders employers as small circles, color-coded by fair-chance status.
 * Ch4d ("30% of jobs go dark") flips `creditCheck=true` markers from
 * amber to muted gray via paint expression. Amazon FC DFW5 is the W3
 * Ch6 anchor (real coordinates, locked).
 *
 * Data lives in `jobsByZipData.ts` (separate module to keep this file
 * under arch limits). The committed `/data/wall/jobs-by-zip.geojson` is
 * the rendered FeatureCollection — same source as the runtime layer.
 */

import { JOBS_BY_ZIP_EMPLOYERS, type EmployerPoint } from "./jobsByZipData";
import { registerLayer, removeLayer } from "./lifecycle";
import type {
  GeoJSONSourceConfig,
  MapboxLayerSpec,
  MapboxLikeMap,
  WallDataLayer,
} from "./types";

export const JOBS_BY_ZIP_SOURCE_ID = "jobs-by-zip-source";
export const JOBS_BY_ZIP_CIRCLE_ID = "jobs-by-zip-circle";

import { MAPBOX_COLORS } from "../colors";
const AMBER = MAPBOX_COLORS.amber;
const MUTED_GRAY = MAPBOX_COLORS.mutedGray;

export interface JobsByZipFeature {
  type: "Feature";
  properties: EmployerPoint;
  geometry: { type: "Point"; coordinates: [number, number] };
}

export interface JobsByZipFeatureCollection {
  type: "FeatureCollection";
  features: JobsByZipFeature[];
}

export function buildJobsByZipGeoJSON(): JobsByZipFeatureCollection {
  return {
    type: "FeatureCollection",
    features: JOBS_BY_ZIP_EMPLOYERS.map((e) => ({
      type: "Feature" as const,
      properties: e,
      geometry: {
        type: "Point" as const,
        coordinates: [e.longitude, e.latitude],
      },
    })),
  };
}

const sourceConfig: GeoJSONSourceConfig = {
  type: "geojson",
  data: "/data/wall/jobs-by-zip.geojson",
  generateId: false,
};

/**
 * Paint switches creditCheck=true to muted gray for Ch4d treatment.
 * Default state (W2 Ch1-3 + Ch4a/b/c): amber for everyone, dimmer for
 * non-fair-chance employers.
 */
const circleLayer: MapboxLayerSpec = {
  id: JOBS_BY_ZIP_CIRCLE_ID,
  type: "circle",
  source: JOBS_BY_ZIP_SOURCE_ID,
  paint: {
    "circle-radius": [
      "interpolate",
      ["linear"],
      ["zoom"],
      9,
      2,
      14,
      6,
    ],
    "circle-color": [
      "case",
      ["==", ["get", "creditCheck"], true],
      MUTED_GRAY,
      AMBER,
    ],
    "circle-stroke-color": AMBER,
    "circle-stroke-width": [
      "case",
      ["==", ["get", "fairChance"], true],
      1,
      0,
    ],
    "circle-opacity": [
      "case",
      ["==", ["get", "fairChance"], true],
      0.85,
      0.5,
    ],
  },
  minzoom: 9,
};

const layerConfigs: readonly MapboxLayerSpec[] = [circleLayer] as const;
const layerIds: readonly string[] = [JOBS_BY_ZIP_CIRCLE_ID] as const;

export const jobsByZipLayer: WallDataLayer = {
  sourceId: JOBS_BY_ZIP_SOURCE_ID,
  layerIds,
  sourceConfig,
  layerConfigs,
  register(map: MapboxLikeMap) {
    registerLayer(map, JOBS_BY_ZIP_SOURCE_ID, sourceConfig, layerConfigs);
  },
  remove(map: MapboxLikeMap) {
    removeLayer(map, JOBS_BY_ZIP_SOURCE_ID, layerIds);
  },
};
