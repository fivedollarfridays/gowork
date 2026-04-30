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
import { WAYPOINTS } from "./Chapter04TheMap.geo";

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

/** Add waypoint markers as a NATIVE Mapbox symbol layer (circle +
 *  text-field). Renders directly on the WebGL canvas — no DOM
 *  marker wrapper to mis-position, no overflow gotchas, no z-index
 *  conflicts with the SVG overlay above. Text labels are first-
 *  class GIS data with proper halo + anti-collision built in.
 *
 *  Reads from WAYPOINTS in Chapter04TheMap.geo (single source of
 *  truth — same data the route lines are built from), so each
 *  labeled stop is exactly where the routes connect. */
function addWaypointMarkers(map: GwMap): void {
  try {
    if (map.getSource?.("ch04-waypoints")) return;
    const features = Object.values(WAYPOINTS).map((w) => ({
      type: "Feature" as const,
      geometry: {
        type: "Point" as const,
        coordinates: [w.lng, w.lat] as [number, number],
      },
      properties: {
        label: w.label,
        sub: w.sub,
        color: w.color,
      },
    }));
    map.addSource?.("ch04-waypoints", {
      type: "geojson",
      data: { type: "FeatureCollection", features },
    });
    // Outer halo circle — soft glow ring so each stop reads even
    // against the dense tract overlay below it.
    map.addLayer?.({
      id: "ch04-waypoints-halo",
      type: "circle",
      source: "ch04-waypoints",
      paint: {
        "circle-radius": 18,
        "circle-color": [
          "match",
          ["get", "color"],
          "amber", "#F59E0B",
          "cyan", "#22D3EE",
          "rose", "#FB7185",
          "#F5F3EE",
        ],
        "circle-opacity": 0.18,
        "circle-blur": 0.8,
      },
    });
    // Filled dot — solid colour ring with dark inner border for
    // readability against any tract / road colour combination.
    map.addLayer?.({
      id: "ch04-waypoints-dot",
      type: "circle",
      source: "ch04-waypoints",
      paint: {
        "circle-radius": 8,
        "circle-color": [
          "match",
          ["get", "color"],
          "amber", "#F59E0B",
          "cyan", "#22D3EE",
          "rose", "#FB7185",
          "#F5F3EE",
        ],
        "circle-stroke-color": "#0A0E1A",
        "circle-stroke-width": 2.5,
      },
    });
    // Text labels — Mapbox native text-field. Renders the
    // `label` property of each waypoint with a dark halo so
    // letterforms read on any backdrop. Anchored top with offset
    // so the label sits BELOW the dot, never covering it.
    map.addLayer?.({
      id: "ch04-waypoints-label",
      type: "symbol",
      source: "ch04-waypoints",
      layout: {
        "text-field": ["get", "label"],
        "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
        "text-size": 12,
        "text-letter-spacing": 0.08,
        "text-offset": [0, 1.6],
        "text-anchor": "top",
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: {
        "text-color": "#F5F3EE",
        "text-halo-color": "#0A0E1A",
        "text-halo-width": 2,
        "text-halo-blur": 1,
      },
    });
    // Sub-label (time + activity) — slightly smaller and dimmer,
    // sits BELOW the main label.
    map.addLayer?.({
      id: "ch04-waypoints-sublabel",
      type: "symbol",
      source: "ch04-waypoints",
      layout: {
        "text-field": ["get", "sub"],
        "text-font": ["Open Sans Regular", "Arial Unicode MS Regular"],
        "text-size": 9.5,
        "text-letter-spacing": 0.04,
        "text-offset": [0, 3.0],
        "text-anchor": "top",
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: {
        "text-color": "#A4B3C7",
        "text-halo-color": "#0A0E1A",
        "text-halo-width": 1.6,
        "text-halo-blur": 0.5,
      },
    });
  } catch {
    /* fail silent — markers are decoration, the routes still tell the story */
  }
  // BARRIER ANNOTATIONS — second symbol layer with editorial labels
  // that name each invisible barrier at its real Fort Worth location.
  // Gives the map narrative weight: the user sees not just stops but
  // OBSTACLES — court, childcare, bus headway, background check, etc.
  addBarrierLabels(map);
}

/** Editorial "invisible barrier" annotations — places the seven
 *  invisible barriers from Ch01 marquee at their real Fort Worth
 *  locations as map labels. Gives the map narrative weight: the
 *  user can see WHERE each obstacle lives in the city. */
function addBarrierLabels(map: GwMap): void {
  try {
    if (map.getSource?.("ch04-barriers")) return;
    const barriers = [
      // Suspended license — at DPS area
      { lng: -97.305, lat: 32.733, label: "SUSPENDED LICENSE", sub: "·  90 min at DPS unblocks 4 jobs", color: "amber" },
      // Open court date — at the courthouse
      { lng: -97.337, lat: 32.762, label: "OPEN COURT DATE", sub: "·  status hearing 4:00p Tue", color: "rose" },
      // Childcare pickup gap — at Como Elementary area
      { lng: -97.398, lat: 32.760, label: "CHILDCARE PICKUP GAP", sub: "·  Lily off bus 2:00p", color: "amber" },
      // 47-min bus headway — Bus 4 stop area
      { lng: -97.350, lat: 32.720, label: "47-MIN BUS HEADWAY", sub: "·  miss one, miss the shift", color: "cyan" },
      // Background-check stigma — at Workforce Solutions area
      { lng: -97.315, lat: 32.745, label: "BACKGROUND CHECK", sub: "·  1 in 3 records non-disqualifying", color: "cyan" },
      // Wage-cliff math — at the employer Alcon area
      { lng: -97.348, lat: 32.840, label: "WAGE-CLIFF MATH", sub: "·  $2 raise = -$400 lost benefits", color: "rose" },
      // No human to call — between districts
      { lng: -97.330, lat: 32.700, label: "NO HUMAN TO CALL", sub: "·  GoWork = navigator + plan", color: "amber" },
    ] as const;
    const features = barriers.map((b) => ({
      type: "Feature" as const,
      geometry: {
        type: "Point" as const,
        coordinates: [b.lng, b.lat] as [number, number],
      },
      properties: {
        label: b.label,
        sub: b.sub,
        color: b.color,
      },
    }));
    map.addSource?.("ch04-barriers", {
      type: "geojson",
      data: { type: "FeatureCollection", features },
    });
    // Small marker dot for each barrier — colour-coded.
    map.addLayer?.({
      id: "ch04-barriers-dot",
      type: "circle",
      source: "ch04-barriers",
      paint: {
        "circle-radius": 4,
        "circle-color": [
          "match",
          ["get", "color"],
          "amber", "#F59E0B",
          "cyan", "#22D3EE",
          "rose", "#FB7185",
          "#F5F3EE",
        ],
        "circle-opacity": 0.85,
        "circle-stroke-color": "#0A0E1A",
        "circle-stroke-width": 1.5,
      },
    });
    // Barrier title — uppercase mono, smaller than waypoints so
    // the visual hierarchy reads waypoints > barriers > city
    // labels.
    map.addLayer?.({
      id: "ch04-barriers-label",
      type: "symbol",
      source: "ch04-barriers",
      layout: {
        "text-field": ["get", "label"],
        "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
        "text-size": 10,
        "text-letter-spacing": 0.12,
        "text-offset": [0, 1.0],
        "text-anchor": "top",
        "text-allow-overlap": false,
        "text-ignore-placement": false,
      },
      paint: {
        "text-color": [
          "match",
          ["get", "color"],
          "amber", "#FCDFB1",
          "cyan", "#C5F0F7",
          "rose", "#FED1D8",
          "#F5F3EE",
        ],
        "text-halo-color": "#0A0E1A",
        "text-halo-width": 1.8,
        "text-halo-blur": 0.6,
      },
    });
    // Sub-text barrier explanation.
    map.addLayer?.({
      id: "ch04-barriers-sub",
      type: "symbol",
      source: "ch04-barriers",
      layout: {
        "text-field": ["get", "sub"],
        "text-font": ["Open Sans Italic", "Arial Unicode MS Regular"],
        "text-size": 8.5,
        "text-letter-spacing": 0.02,
        "text-offset": [0, 2.0],
        "text-anchor": "top",
        "text-allow-overlap": false,
      },
      paint: {
        "text-color": "#A4B3C7",
        "text-halo-color": "#0A0E1A",
        "text-halo-width": 1.4,
      },
    });
  } catch {
    /* ignore — narrative layer, optional */
  }
}

interface MarkerOpts {
  color: string;
  label: string;
  iconType: "home" | "employer";
}

function makeMarkerEl({ color, label, iconType }: MarkerOpts): HTMLDivElement {
  const wrap = document.createElement("div");
  wrap.className = "ch04-map-marker";
  wrap.style.position = "relative";
  wrap.style.display = "flex";
  wrap.style.flexDirection = "column";
  wrap.style.alignItems = "center";
  wrap.style.cursor = "pointer";
  wrap.style.pointerEvents = "auto";

  // Coloured dot with embedded icon.
  const dot = document.createElement("div");
  dot.style.width = "32px";
  dot.style.height = "32px";
  dot.style.borderRadius = "50%";
  dot.style.background = color;
  dot.style.border = "2.4px solid #0A0E1A";
  dot.style.boxShadow = `0 0 0 4px ${color}33, 0 0 18px ${color}cc, 0 4px 8px rgba(10, 14, 26, 0.5)`;
  dot.style.display = "flex";
  dot.style.alignItems = "center";
  dot.style.justifyContent = "center";
  dot.style.transition =
    "transform 280ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 280ms cubic-bezier(0.16, 1, 0.3, 1)";
  dot.innerHTML =
    iconType === "home"
      ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A0E1A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12L12 4L21 12V20C21 20.5523 20.5523 21 20 21H15V14H9V21H4C3.44772 21 3 20.5523 3 20V12Z"/></svg>`
      : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0A0E1A" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="9" width="12" height="12" rx="1"/><path d="M9 9V5h6v4"/><path d="M6 14h12"/></svg>`;

  // Floating pill label below.
  const labelEl = document.createElement("div");
  labelEl.style.position = "absolute";
  labelEl.style.top = "calc(100% + 8px)";
  labelEl.style.left = "50%";
  labelEl.style.transform = "translateX(-50%)";
  labelEl.style.padding = "4px 10px";
  labelEl.style.background = "rgba(10, 14, 26, 0.92)";
  labelEl.style.border = `1px solid color-mix(in oklch, ${color}, transparent 55%)`;
  labelEl.style.borderRadius = "999px";
  labelEl.style.fontFamily = "var(--font-mono-data, monospace)";
  labelEl.style.fontSize = "10px";
  labelEl.style.fontWeight = "600";
  labelEl.style.letterSpacing = "0.08em";
  labelEl.style.textTransform = "uppercase";
  labelEl.style.color = "#F5F3EE";
  labelEl.style.whiteSpace = "nowrap";
  labelEl.style.pointerEvents = "none";
  labelEl.style.opacity = "0.88";
  labelEl.style.transition = "opacity 240ms cubic-bezier(0.16, 1, 0.3, 1)";
  labelEl.textContent = label;

  wrap.appendChild(dot);
  wrap.appendChild(labelEl);

  // Hover affordance — dot scales up, label brightens.
  wrap.addEventListener("pointerenter", () => {
    dot.style.transform = "scale(1.2)";
    dot.style.boxShadow = `0 0 0 6px ${color}44, 0 0 32px ${color}ee, 0 6px 14px rgba(10, 14, 26, 0.6)`;
    labelEl.style.opacity = "1";
  });
  wrap.addEventListener("pointerleave", () => {
    dot.style.transform = "scale(1)";
    dot.style.boxShadow = `0 0 0 4px ${color}33, 0 0 18px ${color}cc, 0 4px 8px rgba(10, 14, 26, 0.5)`;
    labelEl.style.opacity = "0.88";
  });

  return wrap;
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
          // User can drag to pan, drag-rotate, double-click zoom, and
          // pinch on touch — but NOT scroll-zoom (would steal the
          // page scroll that drives the chapter pin choreography).
          // The choreography flyTo on step change still overrides
          // user pan when the user crosses a step boundary.
          interactive: true,
          scrollZoom: false,
          boxZoom: false,
          dragPan: true,
          dragRotate: true,
          doubleClickZoom: true,
          touchZoomRotate: true,
          touchPitch: true,
        }) as unknown as GwMap;

        // Subscribers registered by the SVG overlay — fired on every
        // map move/zoom/rotate/pitch event so anchors can reproject.
        const { fire: fireOverlay, bridge } = createOverlayBridge(() => map);

        map.on?.("load", () => {
          if (!map) return;
          tintStyle(map);
          // polish-3 fix — `addPathArcs` paints the legacy 3 cyan home→
          // employer arcs. The v1 enrichment (`registerEnrichedLayers`)
          // owns routes now (amber morning + cyan afternoon + ghost),
          // and rendering both made the canvas read as 5 overlapping
          // lines stretched across half the city. Disabled.
          // addPathArcs(map);
          add3DBuildings(map);
          // v1 enriched stack — tracts + catchment + transit + 3 routes.
          registerEnrichedLayers(map);
          addWaypointMarkers(map);
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
                  add3DBuildings(map);
                  registerEnrichedLayers(map);
                  // Re-add waypoint markers — setStyle clears all
                  // sources, so the labelled stops would vanish on
                  // a theme toggle without this.
                  addWaypointMarkers(map);
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
