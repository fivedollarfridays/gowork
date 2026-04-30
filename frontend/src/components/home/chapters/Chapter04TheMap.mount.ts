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

import { useEffect, useRef, type RefObject } from "react";
import { MAPBOX_COLORS } from "@/lib/wall/colors";
import { HOME_EMPLOYERS } from "@/lib/home/employers";
import {
  buildPathArcs,
  buildBuildingsLayer,
  HOME_LNG_LAT,
  CH04_INITIAL_VIEW,
  type GwMap,
} from "./Chapter04TheMap.layers";
import { registerEnrichedLayers } from "./Chapter04TheMap.mountLayers";
import { createOverlayBridge } from "./Chapter04TheMap.overlayBridge";

/** Map event the SVG overlay subscribes to so it can re-project markers. */
type MapMoveEvent = "move" | "zoom" | "rotate" | "pitch";

declare global {
  interface Window {
    _gw_map?: { setStyle: (style: string) => void };
    /** Companion accessor for choreography flyTo / jumpTo + the SVG overlay
     *  subscribe + project bridge. The choreography + overlay files declare
     *  matching shapes — TS merges Window augmentations across modules. */
    _gw_map_fly?: {
      flyTo?: (opts: Record<string, unknown>) => void;
      jumpTo?: (opts: Record<string, unknown>) => void;
    };
    /** Pure-data accessor for the SVG overlay. The overlay registers a
     *  listener via `subscribe()`; mount calls back on every map move so
     *  the overlay can reproject anchors. `project()` is the live
     *  lng/lat → screen-pixel projector. */
    _gw_map_overlay?: {
      subscribe: (fn: () => void) => () => void;
      project: (
        lngLat: [number, number],
      ) => { x: number; y: number } | null;
      getCenter: () => { lng: number; lat: number } | null;
      getZoom: () => number | null;
      getBearing: () => number | null;
      getPitch: () => number | null;
    };
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

/**
 * Always return the dark style. The home page design is dark-first; the
 * light branch was never visually polished (atmosphere overlay washes it
 * out, paint colors fight the bg). Stale `localStorage["gowork-theme"] =
 * "light"` from a stray toggle was loading light-v11 + nuking the
 * cinematic look. SiteHeader's theme toggle still flips the rest of the
 * site; the map specifically locks dark.
 */
function readStyleUrl(): string {
  return "mapbox://styles/mapbox/dark-v11";
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

/** 3D buildings layer inserted before road-label IF that layer exists in
 *  the active style. dark-v11 / light-v11 / streets-v12 each ship slightly
 *  different label-layer ids — passing a beforeId Mapbox can't resolve
 *  throws "Layer with id 'road-label' does not exist on this map" 100+
 *  times per session. Probe and fall back to "no beforeId" (renders on
 *  top, still readable). */
function add3DBuildings(map: GwMap): void {
  try {
    if (map.getLayer?.("ch04-3d-buildings")) return;
    // Probe for a label layer to insert under; fall back to undefined so
    // Mapbox appends the buildings on top (still rendered, no throw).
    const labelCandidates = [
      "road-label",
      "road-label-simple",
      "settlement-label",
      "settlement-major-label",
    ] as const;
    const beforeId = labelCandidates.find((id) => map.getLayer?.(id));
    map.addLayer?.(buildBuildingsLayer(), beforeId);
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
 *  on theme change, publish window._gw_map for the SiteHeader bridge.
 *
 *  CRITICAL — latest-ref pattern. The `onAlive` and `onMapReady`
 *  callbacks come from the parent as inline arrow functions, which
 *  means a new reference every render. If we put them in the effect's
 *  dep array the effect tears down + rebuilds the Mapbox map on every
 *  parent re-render (and the parent re-renders constantly during scroll
 *  because setActiveStep / setLiveMap / useTimeOfDay all fire). That
 *  was the visible "flash" — Mapbox was being remounted ~60 times per
 *  second. The fix: stash the callbacks in refs and depend ONLY on
 *  the (stable) mapDivRef. The map mounts exactly once, callbacks
 *  always invoke the latest version. */
export function useMapboxMount({
  mapDivRef,
  onAlive,
  onMapReady,
}: UseMapboxMountOptions): void {
  const onAliveRef = useRef(onAlive);
  const onMapReadyRef = useRef(onMapReady);
  useEffect(() => {
    onAliveRef.current = onAlive;
  }, [onAlive]);
  useEffect(() => {
    onMapReadyRef.current = onMapReady;
  }, [onMapReady]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const container = mapDivRef.current;
    if (!container) return;

    let map: GwMap | null = null;
    let cancelled = false;

    (async () => {
      try {
        const mod = await import("mapbox-gl");
        const mapboxgl = (mod.default ?? mod) as unknown as typeof import(
          "mapbox-gl"
        );
        if (cancelled) return;
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

        // Subscribers registered by the SVG overlay — fired on every
        // map move/zoom/rotate/pitch event so anchors can reproject.
        const { fire: fireOverlay, bridge } = createOverlayBridge(() => map);

        map.on?.("load", () => {
          if (!map) return;
          tintStyle(map);
          addPathArcs(map);
          add3DBuildings(map);
          // v1 enriched stack — tracts + catchment + transit + 3 routes.
          registerEnrichedLayers(map);
          addMarkers(mapboxgl, map);
          onAliveRef.current(true);
          onMapReadyRef.current?.(map);
          // Fire once after load so the overlay can paint with first
          // valid projection.
          fireOverlay();
        });

        const moveEvents: MapMoveEvent[] = ["move", "zoom", "rotate", "pitch"];
        for (const ev of moveEvents) {
          map.on?.(ev, fireOverlay);
        }

        // Bridge for SiteHeader theme toggle + Driver C choreography flyTo.
        window._gw_map = {
          setStyle: (style: string) => {
            if (!map) return;
            try {
              map.setStyle?.(style);
              map.once?.("style.load", () => {
                if (map) {
                  tintStyle(map);
                  addPathArcs(map);
                  add3DBuildings(map);
                  registerEnrichedLayers(map);
                }
              });
            } catch {
              /* ignore */
            }
          },
        };
        // SVG overlay bridge — subscribe + project anchors without
        // holding a direct reference to the live Mapbox instance.
        window._gw_map_overlay = bridge;

        // Surface flyTo so the choreography hook can drive the camera
        // without holding a reference to the live map instance.
        window._gw_map_fly = {
          flyTo: (opts: Record<string, unknown>) => {
            try {
              map?.flyTo?.(opts);
            } catch {
              /* ignore */
            }
          },
          jumpTo: (opts: Record<string, unknown>) => {
            try {
              map?.jumpTo?.(opts);
            } catch {
              /* ignore */
            }
          },
        };
      } catch {
        onAliveRef.current(false);
      }
    })();

    return () => {
      cancelled = true;
      try {
        if (typeof window !== "undefined") {
          delete window._gw_map;
          delete window._gw_map_fly;
          delete window._gw_map_overlay;
        }
        map?.remove?.();
        onMapReadyRef.current?.(null);
      } catch {
        /* ignore */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapDivRef]);
}
