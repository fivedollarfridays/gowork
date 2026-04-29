"use client";

/**
 * Ch04 legend chip — bottom-left corner inside the pinned map frame.
 *
 * # T22 — Legend chip
 *
 * Three rows from the canonical mapbox reference:
 *   - amber path  · Carlos (home → DPS → Workforce Solutions → Alcon)
 *   - cyan path   · Public transit (47-min headway)
 *   - rose dot    · Cliff event (the wage-cliff trigger)
 *
 * A tabular distance/time column tracks total day-distance + drive-time.
 * The chapter mounts this only when `data-map-alive="true"` flips on the
 * section — under fallback (jsdom, airplane mode) the CSS rule hides it.
 */

import type { ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

export function Ch04Legend(): ReactElement {
  const { t } = useTranslation();
  return (
    <aside
      data-ch04-legend=""
      aria-label={t("home.ch4.legendAria")}
    >
      <span className="swatch swatch-amber" data-legend-swatch="amber" aria-hidden="true" />
      <span data-legend-row="1">{t("home.ch4.legendRow1")}</span>
      <span className="legend-time" data-legend-time="1">{t("home.ch4.legendRow1Time")}</span>

      <span className="swatch swatch-cyan" data-legend-swatch="cyan" aria-hidden="true" />
      <span data-legend-row="2">{t("home.ch4.legendRow2")}</span>
      <span className="legend-time" data-legend-time="2">{t("home.ch4.legendRow2Time")}</span>

      <span className="swatch swatch-rose" data-legend-swatch="rose" aria-hidden="true" />
      <span data-legend-row="3">{t("home.ch4.legendRow3")}</span>
      <span className="legend-time" data-legend-time="3">{t("home.ch4.legendRow3Time")}</span>
    </aside>
  );
}

export default Ch04Legend;
