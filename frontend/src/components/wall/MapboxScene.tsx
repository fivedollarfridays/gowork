"use client";

/**
 * T2.3 + T2.4 + T2.5 — MapboxScene.
 *
 * The Mapbox React wrapper. Mounts the live `react-map-gl` Map with:
 *   - the resolved style URL (T2.18 — env var or stock dark fallback)
 *   - the public token from `NEXT_PUBLIC_MAPBOX_TOKEN` (T2.1 / T1.6)
 *   - `INITIAL_CAMERA` (T2.4 — Fort Worth centroid, zoom 11)
 *   - explicit `map.remove()` on unmount (T2.5 — WebGL leak guard)
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

import { useEffect, useRef } from "react";
import Map, { AttributionControl, type MapRef } from "react-map-gl";
import { getMapboxToken } from "@/lib/wall/env";
import { resolveMapboxStyleUrl } from "@/lib/wall/mapboxStyle";
import { INITIAL_CAMERA } from "@/lib/wall/cameraChoreography";

/** Public props — kept narrow because chapters consume the map via context
 *  (T2.2 WallContainer), not via prop drilling. */
export interface MapboxSceneProps {
  /** Optional className passthrough so WallContainer can size the map. */
  className?: string;
}

export default function MapboxScene({ className }: MapboxSceneProps) {
  const mapRef = useRef<MapRef | null>(null);
  const token = getMapboxToken() ?? "";
  const styleUrl = resolveMapboxStyleUrl();

  // T2.5 — explicit cleanup. Mapbox does NOT free its WebGL context when
  // the React wrapper unmounts; without this, a second mount stalls.
  useEffect(() => {
    return () => {
      const map = mapRef.current?.getMap?.();
      if (map && typeof (map as { remove?: () => void }).remove === "function") {
        (map as { remove: () => void }).remove();
      }
    };
  }, []);

  return (
    <Map
      ref={mapRef}
      mapboxAccessToken={token}
      mapStyle={styleUrl}
      initialViewState={INITIAL_CAMERA}
      // Chapter scroll drives the camera — these controls are off.
      dragRotate={false}
      scrollZoom={false}
      // Touch + keyboard remain reachable (a11y).
      dragPan={true}
      touchZoomRotate={true}
      // T2.78 — attribution is rendered explicitly so styling can wrap it
      // without losing the legal-required link.
      attributionControl={false}
      className={className}
      style={{ width: "100%", height: "100%" }}
    >
      <AttributionControl
        position="bottom-left"
        customAttribution={["© GoWork · The Wall"]}
      />
    </Map>
  );
}
