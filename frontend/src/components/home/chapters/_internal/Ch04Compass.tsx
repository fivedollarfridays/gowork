"use client";

/**
 * Driver Ch04-enrich — top-right compass / coordinates HUD.
 *
 * Subscribes to `window._gw_map_overlay` for live center/zoom/bearing
 * readouts. SSR-safe (renders default values until the bridge is up).
 *
 * Per v1: 4 rows in a 2-col grid (label + value), pulsing cyan dot.
 */

import { useEffect, useState, type ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

interface CompassValues {
  lat: string;
  lon: string;
  bearing: string;
  zoom: string;
}

const INITIAL: CompassValues = {
  lat: "32.7555 N",
  lon: "97.3308 W",
  bearing: "-15°",
  zoom: "12.5",
};

function formatLat(lat: number): string {
  return `${Math.abs(lat).toFixed(4)} ${lat >= 0 ? "N" : "S"}`;
}
function formatLon(lng: number): string {
  return `${Math.abs(lng).toFixed(4)} ${lng <= 0 ? "W" : "E"}`;
}
function formatBearing(b: number): string {
  return `${b.toFixed(0)}°`;
}

export function Ch04Compass(): ReactElement {
  const { t } = useTranslation();
  const [vals, setVals] = useState<CompassValues>(INITIAL);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const bridge = window._gw_map_overlay;
    if (!bridge) return;
    const repaint = () => {
      const c = bridge.getCenter();
      const z = bridge.getZoom();
      const b = bridge.getBearing();
      setVals({
        lat: c ? formatLat(c.lat) : INITIAL.lat,
        lon: c ? formatLon(c.lng) : INITIAL.lon,
        bearing: b !== null ? formatBearing(b) : INITIAL.bearing,
        zoom: z !== null ? z.toFixed(2) : INITIAL.zoom,
      });
    };
    const unsub = bridge.subscribe(repaint);
    return unsub;
  }, []);
  return (
    <div
      data-ch04-compass=""
      aria-hidden="true"
      className="ch04-compass"
    >
      <span className="ch04-compass__lab">{t("home.ch4.compass.city")}</span>
      <span className="ch04-compass__val">
        <span className="ch04-compass__dot" data-ch04-compass-dot="" />
        Fort Worth, TX
      </span>
      <span className="ch04-compass__lab">{t("home.ch4.compass.lat")}</span>
      <span className="ch04-compass__val ch04-compass__val--cyan" data-ch04-compass-row="lat">{vals.lat}</span>
      <span className="ch04-compass__lab">{t("home.ch4.compass.lon")}</span>
      <span className="ch04-compass__val ch04-compass__val--cyan" data-ch04-compass-row="lon">{vals.lon}</span>
      <span className="ch04-compass__lab">{t("home.ch4.compass.bearing")}</span>
      <span className="ch04-compass__val" data-ch04-compass-row="bearing">{vals.bearing}</span>
      <span className="ch04-compass__lab">{t("home.ch4.compass.zoom")}</span>
      <span className="ch04-compass__val" data-ch04-compass-row="zoom">{vals.zoom}</span>
    </div>
  );
}

export default Ch04Compass;
