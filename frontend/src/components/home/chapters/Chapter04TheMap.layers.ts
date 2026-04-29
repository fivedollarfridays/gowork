/**
 * Driver C — Ch04 Mapbox source/layer/path payload helpers.
 *
 * Pure-data module (no Mapbox import) so it runs cleanly in jsdom and
 * stays test-friendly. Imported by `Chapter04TheMap.mount.ts`.
 */

import { HOME_EMPLOYERS } from "@/lib/home/employers";

/** Carlos's home centroid in ZIP 76104. */
export const HOME_LNG_LAT: [number, number] = [-97.338, 32.734];

/** Initial map view — Tuesday 6:42a frame. */
export const CH04_INITIAL_VIEW = {
  center: [-97.345, 32.772] as [number, number],
  zoom: 11.6,
  pitch: 48,
  bearing: -16,
};

/** Minimal Mapbox-Map shape this module + the mount helper consume. We
 *  type narrowly so the chapter renders fine even when mapbox-gl typings
 *  are not loaded (tests, server-side analyze). */
export interface GwMap {
  on?: (event: string, fn: () => void) => void;
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
  // Perpendicular vector, normalized then scaled by ~0.18 of segment length.
  const len = Math.hypot(dx, dy) || 1;
  const px = -dy / len;
  const py = dx / len;
  const bias = len * 0.22;
  const cx = mx + px * bias;
  const cy = my + py * bias;
  return [a, [cx, cy], b];
}

/** Build the 3 path-arc LineString features for the paths source. */
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
