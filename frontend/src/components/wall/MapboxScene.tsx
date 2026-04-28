"use client";

/**
 * T2.3 + T2.4 + T2.5 + Wave 4 (Driver D) — MapboxScene.
 *
 * The Mapbox React wrapper. Mounts the live `react-map-gl` Map with:
 *   - the resolved style URL (T2.18 — env var or stock dark fallback)
 *   - the public token from `NEXT_PUBLIC_MAPBOX_TOKEN` (T2.1 / T1.6)
 *   - `INITIAL_CAMERA` (T2.4 — Fort Worth centroid, zoom 11)
 *   - explicit `map.remove()` on unmount (T2.5 — WebGL leak guard)
 *   - **Wave 4**: Driver B's data layers via `registerAllLayers(map)` on
 *     `map.on('load')`; `registerMarkerSymbols(map)` runs FIRST so the
 *     offices symbol layer's `icon-image` lookups resolve. `removeAllLayers`
 *     fires on unmount before the map is destroyed.
 *
 * Interactive controls are suppressed (chapter scroll drives the camera)
 * but `dragPan` + `touchZoomRotate` remain on for keyboard/touch a11y —
 * users must never feel trapped.
 *
 * The `<AttributionControl>` is mandatory (Mapbox ToS, T2.78). Even if
 * we customise styling later, the attribution element MUST render.
 *
 * Spotlight (Multiple Selves Lens — Driver A): the demo-day judge looking
 * at the page in airplane mode sees the static fallback (T2.1), not a
 * crashed map. The W4 mobile reviewer sees the same Mapbox or the
 * fallback — never a half-rendered stall.
 */

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import Map, { AttributionControl, type MapRef } from "react-map-gl";
import { getMapboxToken } from "@/lib/wall/env";
import { resolveMapboxStyleUrl } from "@/lib/wall/mapboxStyle";
import { INITIAL_CAMERA } from "@/lib/wall/cameraChoreography";
import { registerAllLayers, removeAllLayers } from "@/lib/wall/layers";
import { registerMarkerSymbols } from "@/lib/wall/markerSymbols";
import { useMapboxSkyForTimeOfDay, type MapLike } from "@/hooks/useMapboxSkyForTimeOfDay";
import { useResponsiveTier } from "@/hooks/useResponsiveTier";
import { MapCursorFlashlight } from "./MapCursorFlashlight";

/**
 * W4 T4.D.2 — Tablet zoom delta. Tablet (768-1023) drops one zoom step
 * below desktop's INITIAL_CAMERA.zoom for more visible context per frame
 * on iPad-class devices held in landscape.
 */
const TABLET_ZOOM_DELTA = -1;

/** Public props — kept narrow because chapters consume the map via context
 *  (T2.2 WallContainer), not via prop drilling. */
export interface MapboxSceneProps {
  /** Optional inline style passthrough — react-map-gl v7 accepts `style`
   *  but not `className` on the Map element directly. */
  style?: CSSProperties;
}

const DEFAULT_STYLE: CSSProperties = { width: "100%", height: "100%" };

/**
 * MapboxLikeMap is the minimal shape Driver B's layer modules consume.
 * `react-map-gl`'s MapRef.getMap() returns a real mapbox-gl Map; tests
 * stub a smaller object. We type the local cast as `unknown` then narrow.
 */
type MapboxGlInstance = {
  remove?: () => void;
  addSource?: (...args: unknown[]) => void;
  addLayer?: (...args: unknown[]) => void;
};

export default function MapboxScene({ style }: MapboxSceneProps) {
  const mapRef = useRef<MapRef | null>(null);
  const layersRegisteredRef = useRef<boolean>(false);
  // W4 — exposed once `onLoad` fires so the time-of-day sky setter can
  // call setPaintProperty / setLight against a real map instance. We do
  // not pull the ref directly inside the hook because the ref's
  // mutation does not retrigger the hook's effect — the state setter
  // does. Spotlight (Multiple Selves Lens — Driver A): the airplane-mode
  // judge with no Mapbox load event sees the static sky default fall
  // through. The page never crashes for the missing sky.
  const [mapInstance, setMapInstance] = useState<MapLike | null>(null);
  const token = getMapboxToken() ?? "";
  const styleUrl = resolveMapboxStyleUrl();

  // W4 T4.D.2 — Tablet drops zoom by 1 step. Driver A's deferred constraint:
  // "threading a tablet-specific zoom into MapboxScene is one prop away."
  const { isTablet } = useResponsiveTier();
  const initialZoom = INITIAL_CAMERA.zoom + (isTablet ? TABLET_ZOOM_DELTA : 0);

  // W4 T4.A.1 — sync time-of-day to the map's sky + light.
  useMapboxSkyForTimeOfDay(mapInstance);

  /** Wave 4 — onLoad handler runs sprite registration FIRST (offices symbol
   *  layer's `icon-image` needs the sprite available before its source +
   *  layer config touches the map), then composes the Driver-B layers in
   *  z-order. Idempotent: a second `load` event (Mapbox style swap) is
   *  safe because Driver B's `register()` calls are individually
   *  idempotent. */
  const handleMapLoad = useCallback(() => {
    const raw = mapRef.current?.getMap?.() as unknown;
    if (!raw) return;
    const map = raw as MapboxGlInstance;
    // W4 T4.A.1 — publish the live map instance so the sky-setter hook
    // can target it. Done AFTER onLoad so the style is ready for paint
    // property writes.
    setMapInstance(raw as MapLike);
    try {
      registerMarkerSymbols(map as Parameters<typeof registerMarkerSymbols>[0]);
      registerAllLayers(map as Parameters<typeof registerAllLayers>[0]);
      layersRegisteredRef.current = true;
    } catch (err) {
      // Swallow — judges should never see a crashed map. The error is
      // logged by Driver B's modules; here we just keep the page alive.
      if (process.env.NODE_ENV !== "production") {
        // eslint-disable-next-line no-console
        console.warn("[MapboxScene] layer registration failed:", err);
      }
    }
  }, []);

  // T2.5 — explicit cleanup. Mapbox does NOT free its WebGL context when
  // the React wrapper unmounts; without this, a second mount stalls.
  // Wave 4 — also remove Driver B's layers BEFORE the map itself is
  // destroyed so Mapbox never holds a layer referencing a removed source.
  useEffect(() => {
    const refSnapshot = mapRef;
    const layersFlag = layersRegisteredRef;
    return () => {
      const raw = refSnapshot.current?.getMap?.() as unknown;
      const map = raw as MapboxGlInstance;
      if (map) {
        if (layersFlag.current) {
          try {
            removeAllLayers(map as Parameters<typeof removeAllLayers>[0]);
          } catch {
            // Cleanup is best-effort. A failed layer remove must not
            // block the WebGL context release that follows.
          }
        }
        if (typeof map.remove === "function") map.remove();
      }
    };
  }, []);

  return (
    <div style={{ position: "relative", ...DEFAULT_STYLE, ...style }}>
      <Map
        ref={mapRef}
        mapboxAccessToken={token}
        mapStyle={styleUrl}
        onLoad={handleMapLoad}
        initialViewState={{
          longitude: INITIAL_CAMERA.longitude,
          latitude: INITIAL_CAMERA.latitude,
          zoom: initialZoom,
          pitch: INITIAL_CAMERA.pitch,
          bearing: INITIAL_CAMERA.bearing,
        }}
        // Chapter scroll drives the camera — these controls are off.
        dragRotate={false}
        scrollZoom={false}
        // Touch + keyboard remain reachable (a11y).
        dragPan={true}
        touchZoomRotate={true}
        // T2.78 — attribution is rendered explicitly so styling can wrap it
        // without losing the legal-required link.
        attributionControl={false}
        style={DEFAULT_STYLE}
      >
        <AttributionControl
          position="bottom-left"
          customAttribution={["© GoWork · The Wall"]}
        />
      </Map>
      {/* W4 T4.A.3 — cursor flashlight overlay over the map. */}
      <MapCursorFlashlight />
    </div>
  );
}
