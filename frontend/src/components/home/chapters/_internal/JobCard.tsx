"use client";

/**
 * Driver C — Ch06 JobCard sub-component.
 *
 * Renders a single fair-chance hero job card. Reads the employer record
 * from `lib/home/employers.ts` (via id) and pulls EN/ES copy from i18n.
 */

import type { ReactElement } from "react";
import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { getHomeEmployerById } from "@/lib/home/employers";

export interface JobCardProps {
  /** Employer id (alcon | bnsf | dunn). */
  id: "alcon" | "bnsf" | "dunn";
}

/** i18n key prefix per employer — keeps the TSX dense without losing
 *  the translation lookup. */
const KEY_BY_ID: Record<JobCardProps["id"], {
  name: string;
  addr: string;
  wage: string;
  commute: string;
  shift: string;
  blurb: string;
}> = {
  alcon: {
    name: "home.ch6.cards.alconName",
    addr: "home.ch6.cards.alconAddr",
    wage: "home.ch6.cards.alconWage",
    commute: "home.ch6.cards.alconCommute",
    shift: "home.ch6.cards.alconShift",
    blurb: "home.ch6.cards.alconBlurb",
  },
  bnsf: {
    name: "home.ch6.cards.bnsfName",
    addr: "home.ch6.cards.bnsfAddr",
    wage: "home.ch6.cards.bnsfWage",
    commute: "home.ch6.cards.bnsfCommute",
    shift: "home.ch6.cards.bnsfShift",
    blurb: "home.ch6.cards.bnsfBlurb",
  },
  dunn: {
    name: "home.ch6.cards.dunnName",
    addr: "home.ch6.cards.dunnAddr",
    wage: "home.ch6.cards.dunnWage",
    commute: "home.ch6.cards.dunnCommute",
    shift: "home.ch6.cards.dunnShift",
    blurb: "home.ch6.cards.dunnBlurb",
  },
};

export function JobCard({ id }: JobCardProps): ReactElement | null {
  const { t } = useTranslation();
  const emp = getHomeEmployerById(id);
  if (!emp) return null;
  const k = KEY_BY_ID[id];
  return (
    <article
      className="ch06-card"
      data-testid={`ch06-card-${id}`}
      data-employer={id}
    >
      <div className="ch06-card__head">
        <span
          className="ch06-logo"
          data-color={emp.logoColor}
          aria-hidden="true"
        >
          {emp.logo}
        </span>
        <h3 className="ch06-card__name">{t(k.name)}</h3>
      </div>
      <div className="ch06-card__meta">
        <span className="wage">{t(k.wage)}</span>
        <span>{t(k.commute)}</span>
        <span>{t(k.shift)}</span>
        <span style={{ gridColumn: "span 2" }}>{t(k.addr)}</span>
      </div>
      <p className="ch06-card__blurb">{t(k.blurb)}</p>
      <Link
        className="jc-cta"
        href={`/assess?employer=${id}`}
        aria-label={`${t(k.name)} — ${t("home.ch6.cards.applyCta")}`}
      >
        {t("home.ch6.cards.applyCta")}
      </Link>
    </article>
  );
}

export default JobCard;
