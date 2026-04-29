"use client";

import Link from "next/link";
import { BrandMark } from "@/components/wall/BrandMark";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * SiteFooter — sprint/gowork-facelift Driver A.
 *
 * Three-column footer + brand column. Mirrors the design-handoff
 * gowork-homepage.html `.site-footer` block.
 *
 * - Brand column: BrandMark + "GoWork" wordmark + locked tagline
 *   (`siteFooter.brandTagline`).
 * - For workers: Plan, Find a navigator, Daily check-in, Documents.
 * - For navigators: Caseload view, Outcomes dashboard, Training (#).
 * - For cities: Deploy GoWork (GitHub), Press kit (/about), Open source · MIT.
 *
 * Below the rule: HackFW credit + shipped line + version pin (read from
 * NEXT_PUBLIC_APP_VERSION at the call site OR pass `version` prop).
 *
 * All internal routes use `next/link`. External links use a plain anchor
 * with `target="_blank" rel="noopener"` for safety.
 */

interface SiteFooterProps {
  /** Optional version pin override; defaults to env or v0.4.2. */
  version?: string;
}

const REPO_URL = "https://github.com/fivedollarfridays/montgowork";
const PRESS_KIT_URL = `${REPO_URL}/blob/main/docs/press-kit.md`;

export function SiteFooter({ version }: SiteFooterProps = {}): JSX.Element {
  const { t } = useTranslation();
  const resolvedVersion =
    version ?? process.env.NEXT_PUBLIC_APP_VERSION ?? "v0.4.2";

  return (
    <footer
      role="contentinfo"
      data-site-footer
      className="site-footer w-full mt-24 border-t pt-16 pb-10 px-6"
      style={{
        background: "var(--bg-base)",
        borderTopColor: "color-mix(in oklch, var(--fg-primary), transparent 90%)",
        color: "var(--fg-secondary)",
      }}
    >
      <div className="mx-auto max-w-screen-2xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12">
        {/* Brand column */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2" style={{ color: "var(--fg-primary)" }}>
            <BrandMark size={22} />
            <span className="font-bold tracking-tight text-base">
              {t("siteFooter.brandHeading")}
            </span>
          </div>
          <p className="text-sm leading-relaxed max-w-xs" style={{ color: "var(--fg-muted)" }}>
            {t("siteFooter.brandTagline")}
          </p>
        </div>

        {/* For workers */}
        <div className="flex flex-col gap-3">
          <h3
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: "var(--fg-primary)" }}
          >
            {t("siteFooter.workersHeading")}
          </h3>
          <ul className="flex flex-col gap-2 text-sm list-none p-0 m-0">
            <li>
              <Link href="/assess" className="footer-link">
                {t("siteFooter.workersPlan")}
              </Link>
            </li>
            <li>
              <Link href="/case-manager" className="footer-link">
                {t("siteFooter.workersNavigator")}
              </Link>
            </li>
            <li>
              <Link href="/daily" className="footer-link">
                {t("siteFooter.workersDaily")}
              </Link>
            </li>
            <li>
              <Link href="/documents/resume" className="footer-link">
                {t("siteFooter.workersDocuments")}
              </Link>
            </li>
          </ul>
        </div>

        {/* For navigators */}
        <div className="flex flex-col gap-3">
          <h3
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: "var(--fg-primary)" }}
          >
            {t("siteFooter.navigatorsHeading")}
          </h3>
          <ul className="flex flex-col gap-2 text-sm list-none p-0 m-0">
            <li>
              <Link href="/case-manager" className="footer-link">
                {t("siteFooter.navigatorsCaseload")}
              </Link>
            </li>
            <li>
              <Link href="/case-manager?view=outcomes" className="footer-link">
                {t("siteFooter.navigatorsOutcomes")}
              </Link>
            </li>
            <li>
              <a
                href={`${REPO_URL}/blob/main/docs/case-manager-training.md`}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                {t("siteFooter.navigatorsTraining")}
              </a>
            </li>
          </ul>
        </div>

        {/* For cities */}
        <div className="flex flex-col gap-3">
          <h3
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: "var(--fg-primary)" }}
          >
            {t("siteFooter.citiesHeading")}
          </h3>
          <ul className="flex flex-col gap-2 text-sm list-none p-0 m-0">
            <li>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                {t("siteFooter.citiesDeploy")}
              </a>
            </li>
            <li>
              <a
                href={PRESS_KIT_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                {t("siteFooter.citiesPress")}
              </a>
            </li>
            <li>
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="footer-link"
              >
                {t("siteFooter.citiesOpenSource")}
              </a>
            </li>
          </ul>
        </div>
      </div>

      {/* Legal row — Privacy / Terms / Accessibility / Feedback (carried over
          from the canonical app Footer so users still reach legal+a11y from
          the home page, even though the canonical chrome is suppressed on `/`
          via ChromeFrame). */}
      <nav
        aria-label={t("siteFooter.legalNavLabel")}
        className="mx-auto max-w-screen-2xl mt-10 pt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs"
        style={{
          borderTop: "1px solid color-mix(in oklch, var(--fg-primary), transparent 92%)",
          color: "var(--fg-muted)",
        }}
      >
        <Link href="/privacy" className="footer-link">
          {t("footer.privacy")}
        </Link>
        <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
        <Link href="/terms" className="footer-link">
          {t("footer.terms")}
        </Link>
        <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
        <Link href="/accessibility" className="footer-link">
          {t("siteFooter.legalAccessibility")}
        </Link>
        <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="footer-link"
        >
          {t("footer.github")}
        </a>
      </nav>

      {/* Credit row */}
      <div
        className="mx-auto max-w-screen-2xl mt-3 flex flex-col md:flex-row gap-3 md:items-center md:justify-between text-xs"
        style={{ color: "var(--fg-muted)" }}
      >
        <span>{t("siteFooter.creditLine")}</span>
        <span>{t("siteFooter.shippedLine")}</span>
        <span data-site-footer-version className="font-mono opacity-80">
          {resolvedVersion}
        </span>
      </div>
    </footer>
  );
}
