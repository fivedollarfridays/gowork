"use client";

import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";
import { BrandMark } from "@/components/wall/BrandMark";

/**
 * T1.55 — Footer rewrite.
 *
 * The site-wide footer is now the GoWork brand surface :
 *   - Brand mark (G + cyan path) and brand label.
 *   - Privacy + Terms (legacy legal contract preserved).
 *   - GitHub link (target=_blank, rel=noopener noreferrer).
 *   - MIT-licensed declaration.
 *   - Last-calibration timestamp when supplied (Driver B's useLiveNow
 *     in W2 will feed this — the prop is the contract).
 *
 * The legacy `footer.entity` / `footer.tagline` strings remain in the
 * i18n catalog (the legal-counsel placeholder still applies to the
 * privacy/terms page chrome). This component, however, leads with the
 * NEW `footer.brand.label` to surface the GoWork wordmark.
 */
const REPO_URL = "https://github.com/fivedollarfridays/montgowork";

export interface FooterProps {
  /** Last-calibrated timestamp from Driver B's useLiveNow hook (W2). */
  lastCalibration?: Date;
}

export function Footer({ lastCalibration }: FooterProps = {}) {
  const { t, locale } = useTranslation();
  const year = new Date().getFullYear();
  const calibrationText = lastCalibration
    ? lastCalibration.toLocaleString(locale === "es" ? "es-ES" : "en-US", {
        hour: "numeric",
        minute: "2-digit",
        day: "numeric",
        month: "short",
      })
    : null;
  return (
    <footer
      className="mt-auto border-t border-foreground/10 bg-foreground/5 px-4 py-6 text-sm text-muted-foreground"
      role="contentinfo"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 sm:flex-row">
        <div className="flex items-center gap-3 text-center sm:text-left">
          <BrandMark size={20} className="text-foreground/80" />
          <span className="font-medium text-foreground">
            {t("footer.brand.label")}
          </span>
          <span className="ml-1 text-xs">&copy; {year}</span>
        </div>
        <nav
          aria-label={t("footer.navLabel")}
          className="flex flex-wrap items-center justify-center gap-3 text-xs"
        >
          <Link href="/privacy" className="hover:text-foreground hover:underline">
            {t("footer.privacy")}
          </Link>
          <Sep />
          <Link href="/terms" className="hover:text-foreground hover:underline">
            {t("footer.terms")}
          </Link>
          <Sep />
          <Link
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-foreground hover:underline"
          >
            {t("footer.github")}
          </Link>
          <Sep />
          <span>{t("footer.license")}</span>
          {calibrationText ? (
            <>
              <Sep />
              <span data-testid="footer-last-calibration">
                {t("footer.lastCalibration")} {calibrationText}
              </span>
            </>
          ) : null}
        </nav>
      </div>
      <div className="mx-auto mt-2 max-w-6xl text-center sm:text-left">
        <span className="text-[11px] text-muted-foreground/70">
          {t("footer.entity")} · {t("footer.tagline")}
        </span>
      </div>
    </footer>
  );
}

function Sep() {
  return (
    <span aria-hidden="true" className="text-foreground/30">
      &middot;
    </span>
  );
}
