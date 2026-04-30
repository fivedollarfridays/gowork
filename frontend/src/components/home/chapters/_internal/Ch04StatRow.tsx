"use client";

/**
 * Driver Ch04-enrich — bottom-center stat row.
 *
 * 4 stats per the v1 reference, each with a color-tinted value (amber
 * for opportunity / cyan neutral / rose for severity). Tabular numerals.
 *
 *   - $22.50/hr (cyan) · wage at Alcon
 *   - 47 min   (amber) · bus headway
 *   - 4.8 mi   (cyan)  · home → Alcon commute
 *   - 1/3      (rose)  · records open
 *
 * Strings sourced via i18n so EN + ES match.
 */

import type { ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

interface StatDef {
  key: "wage" | "headway" | "commute" | "records";
  tone: "amber" | "cyan" | "rose";
  i18nVal: string;
  i18nUnit: string;
  i18nLabel: string;
}

const STATS: ReadonlyArray<StatDef> = [
  {
    key: "wage",
    tone: "cyan",
    i18nVal: "home.ch4.statRow.wageVal",
    i18nUnit: "home.ch4.statRow.wageUnit",
    i18nLabel: "home.ch4.statRow.wageLabel",
  },
  {
    key: "headway",
    tone: "amber",
    i18nVal: "home.ch4.statRow.headwayVal",
    i18nUnit: "home.ch4.statRow.headwayUnit",
    i18nLabel: "home.ch4.statRow.headwayLabel",
  },
  {
    key: "commute",
    tone: "cyan",
    i18nVal: "home.ch4.statRow.commuteVal",
    i18nUnit: "home.ch4.statRow.commuteUnit",
    i18nLabel: "home.ch4.statRow.commuteLabel",
  },
  {
    key: "records",
    tone: "rose",
    i18nVal: "home.ch4.statRow.recordsVal",
    i18nUnit: "home.ch4.statRow.recordsUnit",
    i18nLabel: "home.ch4.statRow.recordsLabel",
  },
];

export function Ch04StatRow(): ReactElement {
  const { t } = useTranslation();
  return (
    <div
      data-ch04-stat-row=""
      aria-hidden="true"
      className="ch04-stat-row"
    >
      {STATS.map((s) => (
        <div
          key={s.key}
          data-ch04-stat={s.key}
          className={`ch04-stat ch04-stat--${s.tone}`}
        >
          <span className="ch04-stat__v">
            {t(s.i18nVal)}
            <span className="ch04-stat__unit">{t(s.i18nUnit)}</span>
          </span>
          <span className="ch04-stat__l">{t(s.i18nLabel)}</span>
        </div>
      ))}
    </div>
  );
}

export default Ch04StatRow;
