/**
 * Driver Ch04-enrich — pure layer-registration helpers for the v1 stack.
 *
 * Extracted from `Chapter04TheMap.mount.ts` so mount.ts stays under the
 * 400-line architecture limit AND so each addLayer() call is unit-
 * testable without booting Mapbox-GL. Each helper takes a minimal
 * `GwMap`-shaped object and registers a single source + layer family
 * (idempotent — guards against double-add via `getSource` probe).
 */

import { MAPBOX_COLORS } from "@/lib/wall/colors";
import {
  buildAmberRouteSource,
  buildCyanRouteSource,
  buildGhostRouteSource,
  buildTractFeatures,
  buildCatchmentFeature,
  buildTransitFeatures,
} from "./Chapter04TheMap.geo";
import type { GwMap } from "./Chapter04TheMap.layers";

/** Hex constants — Mapbox paint props can't use oklch literals. */
const ROSE = "#FB7185";
const AMBER = "#F59E0B";
const CYAN = "#22D3EE";
const TRACT_FILLS: Readonly<Record<string, [string, number]>> = {
  "t-1": ["#22D3EE", 0.04],
  "t-2": ["#22D3EE", 0.09],
  "t-3": ["#22D3EE", 0.16],
  "t-4": [AMBER, 0.1],
  "t-5": [ROSE, 0.1],
};

function safeAdd(map: GwMap, sourceId: string, source: Record<string, unknown>): boolean {
  try {
    if (map.getSource?.(sourceId)) return false;
    map.addSource?.(sourceId, source);
    return true;
  } catch {
    return false;
  }
}

/** Choropleth tracts — paint 5 quintile fills + outline. */
export function addTractLayers(map: GwMap): void {
  const tracts = buildTractFeatures();
  if (
    !safeAdd(map, "ch04-tracts", {
      type: "geojson",
      data: { type: "FeatureCollection", features: tracts },
    })
  ) {
    return;
  }
  try {
    map.addLayer?.({
      id: "ch04-tracts-fill",
      type: "fill",
      source: "ch04-tracts",
      paint: {
        "fill-color": [
          "match",
          ["get", "tier"],
          "t-1",
          TRACT_FILLS["t-1"][0],
          "t-2",
          TRACT_FILLS["t-2"][0],
          "t-3",
          TRACT_FILLS["t-3"][0],
          "t-4",
          TRACT_FILLS["t-4"][0],
          "t-5",
          TRACT_FILLS["t-5"][0],
          MAPBOX_COLORS.cyan,
        ],
        "fill-opacity": [
          "match",
          ["get", "tier"],
          "t-1",
          TRACT_FILLS["t-1"][1],
          "t-2",
          TRACT_FILLS["t-2"][1],
          "t-3",
          TRACT_FILLS["t-3"][1],
          "t-4",
          TRACT_FILLS["t-4"][1],
          "t-5",
          TRACT_FILLS["t-5"][1],
          0.06,
        ],
      },
    });
    map.addLayer?.({
      id: "ch04-tracts-outline",
      type: "line",
      source: "ch04-tracts",
      paint: {
        "line-color": "#A4B3C7",
        "line-opacity": 0.18,
        "line-width": 0.6,
      },
    });
  } catch {
    /* ignore — tract paint is decorative */
  }
}

/** Como Elementary dotted catchment polygon. */
export function addCatchmentLayer(map: GwMap): void {
  if (
    !safeAdd(map, "ch04-catchment", {
      type: "geojson",
      data: buildCatchmentFeature(),
    })
  ) {
    return;
  }
  try {
    map.addLayer?.({
      id: "ch04-catchment-fill",
      type: "fill",
      source: "ch04-catchment",
      paint: { "fill-color": AMBER, "fill-opacity": 0.05 },
    });
    map.addLayer?.({
      id: "ch04-catchment-line",
      type: "line",
      source: "ch04-catchment",
      paint: {
        "line-color": AMBER,
        "line-width": 1.4,
        "line-opacity": 0.55,
        "line-dasharray": [3, 5],
      },
    });
  } catch {
    /* ignore */
  }
}

/** Bus 4 / Bus 6 dashed transit lines. */
export function addTransitLayers(map: GwMap): void {
  const feats = buildTransitFeatures();
  if (
    !safeAdd(map, "ch04-transit", {
      type: "geojson",
      data: { type: "FeatureCollection", features: feats },
    })
  ) {
    return;
  }
  try {
    map.addLayer?.({
      id: "ch04-transit-line",
      type: "line",
      source: "ch04-transit",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": CYAN,
        "line-width": 2,
        "line-opacity": 0.6,
        "line-dasharray": [4, 4],
      },
    });
  } catch {
    /* ignore */
  }
}

/** Amber morning route (home → DPS → Workforce → Como) with glow. */
export function addAmberRouteLayer(map: GwMap): void {
  if (!safeAdd(map, "ch04-route-amber", buildAmberRouteSource())) return;
  try {
    map.addLayer?.({
      id: "ch04-route-amber-glow",
      type: "line",
      source: "ch04-route-amber",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": AMBER,
        "line-width": 14,
        "line-opacity": 0.18,
        "line-blur": 6,
      },
    });
    map.addLayer?.({
      id: "ch04-route-amber-line",
      type: "line",
      source: "ch04-route-amber",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": AMBER, "line-width": 3.5, "line-opacity": 0.95 },
    });
  } catch {
    /* ignore */
  }
}

/** Cyan afternoon route (Como → Courthouse → Job) with glow. */
export function addCyanRouteLayer(map: GwMap): void {
  if (!safeAdd(map, "ch04-route-cyan", buildCyanRouteSource())) return;
  try {
    map.addLayer?.({
      id: "ch04-route-cyan-glow",
      type: "line",
      source: "ch04-route-cyan",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": CYAN,
        "line-width": 14,
        "line-opacity": 0.18,
        "line-blur": 6,
      },
    });
    map.addLayer?.({
      id: "ch04-route-cyan-line",
      type: "line",
      source: "ch04-route-cyan",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": CYAN, "line-width": 3.5, "line-opacity": 0.95 },
    });
  } catch {
    /* ignore */
  }
}

/** Ghost route (rose dashed broken path the no-car worker must take). */
export function addGhostRouteLayer(map: GwMap): void {
  if (!safeAdd(map, "ch04-route-ghost", buildGhostRouteSource())) return;
  try {
    map.addLayer?.({
      id: "ch04-route-ghost-line",
      type: "line",
      source: "ch04-route-ghost",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ROSE,
        "line-width": 2,
        "line-opacity": 0.45,
        "line-dasharray": [6, 6],
      },
    });
  } catch {
    /* ignore */
  }
}

/** Single registration entry-point — calls every helper in the right
 *  draw order (tracts at the bottom, ghost above tracts, day routes on top).
 */
export function registerEnrichedLayers(map: GwMap): void {
  addTractLayers(map);
  addCatchmentLayer(map);
  addTransitLayers(map);
  addGhostRouteLayer(map);
  addAmberRouteLayer(map);
  addCyanRouteLayer(map);
}
