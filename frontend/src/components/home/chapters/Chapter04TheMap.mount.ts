"use client";

/**
 * Driver C — Ch04 Mapbox mount + tinting + GeoJSON layers + markers.
 *
 * Lifted out of `Chapter04TheMap.tsx` so the chapter component stays
 * narrative + lean. This module owns the imperative Mapbox-GL plumbing:
 *
 *   - dynamic `mapbox-gl` import (so jsdom + airplane-mode judge survive)
 *   - dark-v11 / light-v11 style swap based on `<html data-theme>`
 *   - tint of background/water/parks/buildings/roads/symbols
 *   - 3D buildings extrusion layer
 *   - 3 path arcs (home→alcon, home→bnsf, home→dunn) with curve helper
 *   - 4 markers (home + 3 employers)
 *   - `setFog` for the dark atmospheric look
 *   - publishes `window._gw_map` so SiteHeader can swap style on theme.
 *
 * Falls back gracefully on every error path — chapter renders the
 * editorial fallback layer behind the (failed) map div.
 */

import { useEffect, type RefObject } from "react";
import { MAPBOX_COLORS } from "@/lib/wall/colors";
import { HOME_EMPLOYERS } from "@/lib/home/employers";
import {
  buildPathArcs,
  buildBuildingsLayer,
  HOME_LNG_LAT,
  CH04_INITIAL_VIEW,
  type GwMap,
} from "./Chapter04TheMap.layers";

declare global {
  interface Window {
    _gw_map?: { setStyle: (style: string) => void };
  }
}

/**
 * Read the Mapbox public token from env. NO inline fallback — committing a
 * publishable token (`pk.*`) inflates the demo owner's free tier across any
 * domain that can ship the bundle, and GitHub secret scanning will (rightly)
 * block any push that hardcodes one. The Ch4 component renders a branded
 * fallback gradient when this returns "" so jsdom + airplane-mode + token-
 * less previews still render the editorial copy without crashing.
 */
function readToken(): string {
  return process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";
}

function readStyleUrl(): string {
  if (typeof document === "undefined") return "mapbox://styles/mapbox/dark-v11";
  const theme = document.documentElement.dataset.theme;
  return theme === "light"
    ? "mapbox://styles/mapbox/light-v11"
    : "mapbox://styles/mapbox/dark-v11";
}

/** Apply Mapbox-safe (hex) tinting to the loaded style. Wrapped in try
 *  blocks per layer because dark-v11 / light-v11 ship slightly different
 *  layer ids — missing ones must not throw. */
function tintStyle(map: GwMap): void {
  const tints: ReadonlyArray<[string, string, string]> = [
    ["background", "background-color", "#0A0E1A"],
    ["water", "fill-color", "#0d2438"],
    ["land", "background-color", "#0A0E1A"],
    ["landuse", "fill-color", "#15241f"],
    ["road-motorway", "line-color", "#3d5278"],
    ["road-trunk", "line-color", "#3d5278"],
    ["road-primary", "line-color", "#2f4467"],
    ["road-secondary", "line-color", "#2f4467"],
    ["road-residential", "line-color", "#22314c"],
  ];
  for (const [layerId, prop, val] of tints) {
    try {
      if (map.getLayer?.(layerId)) {
        map.setPaintProperty?.(layerId, prop, val);
      }
    } catch {
      /* ignore — layer absent in this style version */
    }
  }
  // Fog — dark atmospheric depth.
  try {
    map.setFog?.({
      range: [-1, 8],
      color: "#0A0E1A",
      "horizon-blend": 0.18,
      "high-color": "#1a2547",
      "space-color": "#060912",
    });
  } catch {
    /* setFog absent on some style versions */
  }
}

/** Add path arcs (home→3 destinations) as a single source + 2 layers. */
function addPathArcs(map: GwMap): void {
  try {
    const features = buildPathArcs();
    if (map.getSource?.("ch04-paths")) return;
    map.addSource?.("ch04-paths", {
      type: "geojson",
      data: { type: "FeatureCollection", features },
    });
    map.addLayer?.({
      id: "ch04-paths-glow",
      type: "line",
      source: "ch04-paths",
      paint: {
        "line-color": MAPBOX_COLORS.cyan,
        "line-width": 6,
        "line-blur": 4,
        "line-opacity": 0.18,
      },
    });
    map.addLayer?.({
      id: "ch04-paths-line",
      type: "line",
      source: "ch04-paths",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": MAPBOX_COLORS.cyan,
        "line-width": 1.6,
        "line-opacity": 0.85,
      },
    });
  } catch {
    /* graceful — path arcs are decoration */
  }
}

/** 3D buildings layer inserted before road-label. */
function add3DBuildings(map: GwMap): void {
  try {
    if (map.getLayer?.("ch04-3d-buildings")) return;
    map.addLayer?.(buildBuildingsLayer(), "road-label");
  } catch {
    /* not all styles include the composite source */
  }
}

/** Build the 4 marker DOM elements (home + 3 employers) and attach. */
function addMarkers(mapboxgl: typeof import("mapbox-gl"), map: GwMap): void {
  try {
    const Marker = mapboxgl.Marker;
    if (!Marker) return;
    // Home (amber).
    const homeEl = makeMarkerEl("#F59E0B");
    new Marker(homeEl).setLngLat(HOME_LNG_LAT).addTo(
      map as unknown as mapboxgl.Map,
    );
    // Three employers (cyan).
    for (const emp of HOME_EMPLOYERS) {
      const el = makeMarkerEl("#22D3EE");
      new Marker(el)
        .setLngLat([emp.longitude, emp.latitude])
        .addTo(map as unknown as mapboxgl.Map);
    }
  } catch {
    /* if Marker API unavailable, the path arcs alone still tell the story */
  }
}

function makeMarkerEl(color: string): HTMLDivElement {
  const el = document.createElement("div");
  el.style.width = "18px";
  el.style.height = "18px";
  el.style.borderRadius = "50%";
  el.style.background = color;
  el.style.border = "2px solid #0A0E1A";
  el.style.boxShadow = `0 0 0 4px ${color}33, 0 0 16px ${color}aa`;
  return el;
}

export interface UseMapboxMountOptions {
  mapDivRef: RefObject<HTMLDivElement | null>;
  onAlive: (alive: boolean) => void;
  /** Optional — invoked once with the live map instance (or null on
   *  unmount/failure) so callers can wire reactive hooks like
   *  `useMapboxSkyForTimeOfDay`. */
  onMapReady?: (map: GwMap | null) => void;
}

/** Mount the Mapbox map imperatively, wire layers + markers, swap style
 *  on theme change, publish window._gw_map for the SiteHeader bridge. */
export function useMapboxMount({
  mapDivRef,
  onAlive,
  onMapReady,
}: UseMapboxMountOptions): void {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const container = mapDivRef.current;
    if (!container) return;

    let map: GwMap | null = null;
    let cancelled = false;

    (async () => {
      try {
        const mod = await import("mapbox-gl");
        // mapbox-gl v3 exports types via a default export; we need both
        // the constructor and Marker. Cast through `unknown` because the
        // ambient `typeof import('mapbox-gl')` differs from the runtime
        // shape under v3's module re-export.
        const mapboxgl = (mod.default ?? mod) as unknown as typeof import(
          "mapbox-gl"
        );
        if (cancelled) return;
        // Token assignment is required on mapbox-gl v3.
        (mapboxgl as unknown as { accessToken: string }).accessToken =
          readToken();

        map = new mapboxgl.Map({
          container,
          style: readStyleUrl(),
          center: CH04_INITIAL_VIEW.center,
          zoom: CH04_INITIAL_VIEW.zoom,
          pitch: CH04_INITIAL_VIEW.pitch,
          bearing: CH04_INITIAL_VIEW.bearing,
          antialias: true,
          attributionControl: false,
          interactive: false,
          dragRotate: false,
        }) as unknown as GwMap;

        map.on?.("load", () => {
          if (!map) return;
          tintStyle(map);
          addPathArcs(map);
          add3DBuildings(map);
          addMarkers(mapboxgl, map);
          onAlive(true);
          // T23 — surface the live map to the chapter so the
          // useMapboxSkyForTimeOfDay hook can paint the sky once style is in.
          onMapReady?.(map);
        });

        // Bridge for SiteHeader theme toggle.
        window._gw_map = {
          setStyle: (style: string) => {
            if (!map) return;
            try {
              map.setStyle?.(style);
              // Re-tint after the style swap completes.
              map.once?.("style.load", () => {
                if (map) {
                  tintStyle(map);
                  addPathArcs(map);
                  add3DBuildings(map);
                }
              });
            } catch {
              /* ignore */
            }
          },
        };
      } catch {
        // Mapbox unavailable — fallback layer carries the page.
        onAlive(false);
      }
    })();

    return () => {
      cancelled = true;
      try {
        if (typeof window !== "undefined") {
          delete window._gw_map;
        }
        map?.remove?.();
        onMapReady?.(null);
      } catch {
        /* ignore */
      }
    };
  }, [mapDivRef, onAlive, onMapReady]);
}
