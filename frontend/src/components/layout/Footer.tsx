"use client";

import Link from "next/link";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * T13.115 — Site-wide legal footer.
 *
 * Renders on every page via the root layout. Links to /privacy and /terms and
 * displays the legal entity name. Localized via the i18n catalog
 * (`footer.privacy`, `footer.terms`, `footer.entity`, `footer.tagline`).
 *
 * Note: the entity name is a hackathon-grade placeholder. Replace with the
 * registered entity name (e.g., "GoWork, Inc." or the operating LLC)
 * before any production rollout — see /privacy and /terms for the same
 * COUNSEL REVIEW REQUIRED caveat.
 */
export function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer
      className="mt-auto border-t bg-muted/30 px-4 py-6 text-sm text-muted-foreground"
      role="contentinfo"
    >
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 sm:flex-row">
        <div className="text-center sm:text-left">
          <span className="font-medium text-foreground">
            {t("footer.entity")}
          </span>
          <span className="ml-2 text-xs">
            {t("footer.tagline")} &copy; {year}
          </span>
        </div>
        <nav
          aria-label={t("footer.navLabel")}
          className="flex items-center gap-4"
        >
          <Link
            href="/privacy"
            className="hover:text-foreground hover:underline"
          >
            {t("footer.privacy")}
          </Link>
          <span aria-hidden="true">&middot;</span>
          <Link
            href="/terms"
            className="hover:text-foreground hover:underline"
          >
            {t("footer.terms")}
          </Link>
        </nav>
      </div>
    </footer>
  );
}
