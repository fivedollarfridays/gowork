/**
 * Driver C — Ch04 Mapbox source/layer/path payload helpers.
 *
 * Pure-data module (no Mapbox import) so it runs cleanly in jsdom and
 * stays test-friendly. Imported by `Chapter04TheMap.mount.ts` and the
 * SVG overlay component.
 *
 * # Architecture (Ch04-enrich)
 *
 * The original module shipped only home-employer arcs. The v1 reference
 * (the-path-mapbox-v1.html) layers SIX waypoints, two color-coded day
 * routes (amber morning + cyan afternoon), a ghost route, choropleth
 * tracts, a school catchment polygon, transit lines, and editorial
 * callout annotations. Those data factories live in the sibling
 * `Chapter04TheMap.geo.ts` module and are re-exported here so consumers
 * have a single import surface.
 */

import { HOME_EMPLOYERS } from "@/lib/home/employers";

export {
  WAYPOINTS,
  DAY_ROUTE_AMBER,
  DAY_ROUTE_CYAN,
  GHOST_ROUTE,
  buildAmberRouteSource,
  buildCyanRouteSource,
  buildGhostRouteSource,
  buildTractFeatures,
  buildCatchmentFeature,
  buildTransitFeatures,
  buildAnnotations,
} from "./Chapter04TheMap.geo";
export type {
  Waypoint,
  TractFeature,
  TransitFeature,
  Annotation,
} from "./Chapter04TheMap.geo";

/** Carlos's home centroid in ZIP 76104. */
export const HOME_LNG_LAT: [number, number] = [-97.338, 32.734];

/** Initial map view — Tuesday 6:42a frame.
 *  polish-2 fix — zoom 11.6 → 12.5, center tightened toward Carlos's
 *  76104 ↔ downtown corridor. The wider DFW-metro framing was burying
 *  the path arcs and markers in negative space. */
export const CH04_INITIAL_VIEW = {
  center: [-97.330, 32.755] as [number, number],
  zoom: 12.5,
  pitch: 45,
  bearing: -15,
};

/** Minimal Mapbox-Map shape this module + the mount helper consume. We
 *  type narrowly so the chapter renders fine even when mapbox-gl typings
 *  are not loaded (tests, server-side analyze). */
export interface GwMap {
  on?: (event: string, fn: (...args: unknown[]) => void) => void;
  off?: (event: string, fn: (...args: unknown[]) => void) => void;
  once?: (event: string, fn: () => void) => void;
  remove?: () => void;
  setStyle?: (style: string) => void;
  setPaintProperty?: (layer: string, prop: string, value: unknown) => void;
  setFog?: (fog: Record<string, unknown>) => void;
  addSource?: (id: string, source: Record<string, unknown>) => void;
  addLayer?: (
    layer: Record<string, unknown>,
    beforeId?: string,
  ) => void;
  getLayer?: (id: string) => unknown;
  getSource?: (id: string) => unknown;
  flyTo?: (opts: Record<string, unknown>) => void;
  jumpTo?: (opts: Record<string, unknown>) => void;
  project?: (lngLat: [number, number]) => { x: number; y: number };
  getCenter?: () => { lng: number; lat: number };
  getZoom?: () => number;
  getBearing?: () => number;
  getPitch?: () => number;
  getCanvas?: () => HTMLCanvasElement | null;
}

/** Curve helper — given two points, return a 3-point arc (start → mid
 *  with perpendicular bias → end). Used to render the home → employer
 *  path lines as a gentle visual arc rather than straight rays. */
function arc(
  a: [number, number],
  b: [number, number],
): [number, number][] {
  const mx = (a[0] + b[0]) / 2;
  const my = (a[1] + b[1]) / 2;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy) || 1;
  const px = -dy / len;
  const py = dx / len;
  const bias = len * 0.22;
  const cx = mx + px * bias;
  const cy = my + py * bias;
  return [a, [cx, cy], b];
}

/** Build the 3 path-arc LineString features for the legacy paths source.
 *  Kept for backward compat — the new v1 stack uses the day-route sources. */
export function buildPathArcs(): Array<{
  type: "Feature";
  properties: { id: string };
  geometry: { type: "LineString"; coordinates: [number, number][] };
}> {
  return HOME_EMPLOYERS.map((emp) => ({
    type: "Feature" as const,
    properties: { id: emp.id },
    geometry: {
      type: "LineString" as const,
      coordinates: arc(HOME_LNG_LAT, [emp.longitude, emp.latitude]),
    },
  }));
}

/** 3D buildings extrusion layer config — composite source-layer with
 *  zoom-interpolated height. Inserted before `road-label` so labels
 *  remain readable above the buildings. */
export function buildBuildingsLayer(): Record<string, unknown> {
  return {
    id: "ch04-3d-buildings",
    source: "composite",
    "source-layer": "building",
    filter: ["==", "extrude", "true"],
    type: "fill-extrusion",
    minzoom: 13,
    paint: {
      "fill-extrusion-color": "#1a2236",
      "fill-extrusion-height": [
        "interpolate",
        ["linear"],
        ["zoom"],
        13,
        0,
        13.5,
        ["get", "height"],
      ],
      "fill-extrusion-opacity": 0.85,
    },
  };
}
