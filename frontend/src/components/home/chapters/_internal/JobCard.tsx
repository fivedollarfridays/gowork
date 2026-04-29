"use client";

/**
 * Driver C — Ch06 JobCard sub-component.
 *
 * Renders a single fair-chance hero job card. Reads the employer record
 * from `lib/home/employers.ts` (via id) and pulls EN/ES copy from i18n.
 *
 * polish-2 enhancements:
 *   - T27 — `loading` prop renders a 4-row shimmer skeleton in place of
 *     the card body.
 *   - T28 — Apply CTA gets `useMagneticHover` (proximity pull) plus a
 *     soft `useHaptic().tap()` on click. Both degrade gracefully when
 *     the underlying capability is unavailable (no vibrate API, reduced
 *     motion, coarse pointer).
 */

import { useCallback, type ReactElement } from "react";
import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { getHomeEmployerById } from "@/lib/home/employers";
import { useMagneticHover } from "@/hooks/useMagneticHover";
import { useHaptic } from "@/hooks/useHaptic";
import { JobCardSkeleton } from "./JobCardSkeleton";

export interface JobCardProps {
  /** Employer id (alcon | bnsf | dunn). */
  id: "alcon" | "bnsf" | "dunn";
  /** When true, render the shimmer skeleton instead of the real card body. */
  loading?: boolean;
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

export function JobCard({ id, loading = false }: JobCardProps): ReactElement | null {
  const { t } = useTranslation();
  const emp = getHomeEmployerById(id);
  const ctaRef = useMagneticHover<HTMLAnchorElement>({ disabled: loading });
  const haptic = useHaptic();

  const onCtaClick = useCallback(() => {
    haptic.tap();
    try {
      navigator?.vibrate?.(15);
    } catch {
      /* vibrate unsupported */
    }
  }, [haptic]);

  if (!emp) return null;
  const k = KEY_BY_ID[id];

  if (loading) {
    return (
      <article
        className="ch06-card"
        data-testid={`ch06-card-${id}`}
        data-employer={id}
        data-skeleton="true"
      >
        <JobCardSkeleton label={t("home.ch6.skeletonLabel")} />
      </article>
    );
  }

  return (
    <article
      className="ch06-card"
      data-testid={`ch06-card-${id}`}
      data-employer={id}
      data-skeleton="false"
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
        ref={ctaRef}
        className="jc-cta"
        href={`/assess?employer=${id}`}
        aria-label={`${t(k.name)} — ${t("home.ch6.cards.applyCta")}`}
        onClick={onCtaClick}
      >
        {t("home.ch6.cards.applyCta")}
      </Link>
    </article>
  );
}

export default JobCard;
