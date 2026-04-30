"use client";

/**
 * Driver Ch04-enrich — bottom-left legend chip (full v1 anatomy).
 *
 * Six rows + heading — three route-color rows (amber morning, cyan
 * afternoon, rose ghost dashed) and three waypoint-color rows
 * (amber home, cyan plan stop, rose courthouse). Each row is a
 * 3-column grid: swatch + label + numeric.
 *
 * The chapter mounts this only when the map column is visible.
 * Under fallback (jsdom, airplane mode) the CSS rule fades it out
 * (`[data-map-alive="false"] [data-ch04-legend]`).
 */

import type { ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

interface LegendRowDef {
  key: string;
  swatch:
    | "amber-line"
    | "cyan-line"
    | "rose-dash"
    | "amber-dot"
    | "cyan-dot"
    | "rose-dot";
  i18nLabel: string;
  i18nNum: string;
}

const ROWS: ReadonlyArray<LegendRowDef> = [
  {
    key: "morning",
    swatch: "amber-line",
    i18nLabel: "home.ch4.legend.morning",
    i18nNum: "home.ch4.legend.morningNum",
  },
  {
    key: "afternoon",
    swatch: "cyan-line",
    i18nLabel: "home.ch4.legend.afternoon",
    i18nNum: "home.ch4.legend.afternoonNum",
  },
  {
    key: "broken",
    swatch: "rose-dash",
    i18nLabel: "home.ch4.legend.broken",
    i18nNum: "home.ch4.legend.brokenNum",
  },
  {
    key: "home",
    swatch: "amber-dot",
    i18nLabel: "home.ch4.legend.home",
    i18nNum: "home.ch4.legend.homeNum",
  },
  {
    key: "plan",
    swatch: "cyan-dot",
    i18nLabel: "home.ch4.legend.plan",
    i18nNum: "home.ch4.legend.planNum",
  },
  {
    key: "court",
    swatch: "rose-dot",
    i18nLabel: "home.ch4.legend.court",
    i18nNum: "home.ch4.legend.courtNum",
  },
];

export function Ch04Legend(): ReactElement {
  const { t } = useTranslation();
  return (
    <aside
      data-ch04-legend=""
      aria-label={t("home.ch4.legendAria")}
      className="ch04-legend"
    >
      <h6 data-ch04-legend-heading="" className="ch04-legend__heading">
        {t("home.ch4.legend.heading")}
      </h6>
      {ROWS.map((row, i) => (
        <div
          key={row.key}
          data-legend-row={String(i + 1)}
          className="ch04-legend__row"
        >
          <span
            className={`swatch swatch--${row.swatch}`}
            data-legend-swatch={row.swatch}
            aria-hidden="true"
          />
          <span data-legend-label={row.key}>{t(row.i18nLabel)}</span>
          <span className="legend-time" data-legend-time={row.key}>
            {t(row.i18nNum)}
          </span>
        </div>
      ))}
    </aside>
  );
}

export default Ch04Legend;
