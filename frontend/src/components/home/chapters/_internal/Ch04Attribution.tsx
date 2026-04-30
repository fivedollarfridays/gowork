"use client";

/**
 * Driver Ch04-enrich — branded Mapbox attribution chip (top-left).
 *
 * The map div hides the default Mapbox attribution (per polish-2).
 * Mapbox ToS still requires "© Mapbox · © OpenStreetMap" be visible
 * when the map is — this chip honors that AND adds editorial polish:
 *   - pulsing cyan live-dot
 *   - "live · 12:30p" timestamp (static, editorial)
 */

import type { ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

export function Ch04Attribution(): ReactElement {
  const { t } = useTranslation();
  return (
    <div
      data-ch04-attrib=""
      aria-label={t("home.ch4.attrib.aria")}
      className="ch04-attrib"
    >
      <span className="ch04-attrib__live" aria-hidden="true" />
      <span>{t("home.ch4.attrib.liveLabel")}</span>
      <span className="ch04-attrib__sep" aria-hidden="true">
        ·
      </span>
      <a
        className="ch04-attrib__link"
        href="https://www.mapbox.com/about/maps/"
        target="_blank"
        rel="noopener noreferrer"
      >
        © Mapbox
      </a>
      <a
        className="ch04-attrib__link"
        href="https://www.openstreetmap.org/copyright"
        target="_blank"
        rel="noopener noreferrer"
      >
        © OpenStreetMap
      </a>
      <span className="ch04-attrib__sep" aria-hidden="true">
        ·
      </span>
      <span>{t("home.ch4.attrib.timestamp")}</span>
    </div>
  );
}

export default Ch04Attribution;
