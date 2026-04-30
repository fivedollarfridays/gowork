"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { BrandMark } from "@/components/wall/BrandMark";
import { useTranslation } from "@/hooks/useTranslation";
import { useScrollVelocity } from "@/hooks/useScrollVelocity";

/**
 * SiteFooter — sprint/gowork-facelift Driver A. Polish-2 T5 + T8.
 *
 * Three-column footer + brand column. T5 promotes every in-prose anchor
 * to the global `.editorial-link` class for the gradient underline reveal.
 * T8 adds a reverse-scroll GOWORK wordmark below the legal/credit rows.
 */

interface SiteFooterProps {
  /** Optional version pin override; defaults to env or v0.4.2. */
  version?: string;
}

const REPO_URL = "https://github.com/fivedollarfridays/montgowork";
const PRESS_KIT_URL = `${REPO_URL}/blob/main/docs/press-kit.md`;
const TRAINING_URL = `${REPO_URL}/blob/main/docs/case-manager-training.md`;
const FOOTER_LINK_CLASS = "footer-link editorial-link";

interface InternalProps {
  href: string;
  label: string;
}

function InternalLink({ href, label }: InternalProps): JSX.Element {
  return (
    <Link href={href} className={FOOTER_LINK_CLASS}>
      {label}
    </Link>
  );
}

interface ExternalProps extends InternalProps {
  href: string;
}

function ExternalLink({ href, label }: ExternalProps): JSX.Element {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={FOOTER_LINK_CLASS}
    >
      {label}
    </a>
  );
}

interface FooterColumnProps {
  heading: string;
  children: React.ReactNode;
}

function FooterColumn({ heading, children }: FooterColumnProps): JSX.Element {
  return (
    <div className="flex flex-col gap-3">
      <h3
        className="text-xs font-semibold uppercase tracking-widest"
        style={{ color: "var(--fg-primary)" }}
      >
        {heading}
      </h3>
      <ul className="flex flex-col gap-2 text-sm list-none p-0 m-0">{children}</ul>
    </div>
  );
}

interface BrandColumnProps {
  brandHeading: string;
  brandTagline: string;
}

function BrandColumn({ brandHeading, brandTagline }: BrandColumnProps): JSX.Element {
  return (
    <div className="flex flex-col gap-3">
      <div
        className="flex items-center gap-2"
        style={{ color: "var(--fg-primary)" }}
      >
        <BrandMark size={22} />
        <span className="font-bold tracking-tight text-base">{brandHeading}</span>
      </div>
      <p
        className="text-sm leading-relaxed max-w-xs"
        style={{ color: "var(--fg-muted)" }}
      >
        {brandTagline}
      </p>
    </div>
  );
}

interface LegalNavProps {
  t: (key: string) => string;
}

function LegalNav({ t }: LegalNavProps): JSX.Element {
  return (
    <nav
      aria-label={t("siteFooter.legalNavLabel")}
      className="mx-auto max-w-screen-2xl mt-10 pt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs"
      style={{
        borderTop: "1px solid color-mix(in oklch, var(--fg-primary), transparent 92%)",
        color: "var(--fg-muted)",
      }}
    >
      <InternalLink href="/privacy" label={t("footer.privacy")} />
      <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
      <InternalLink href="/terms" label={t("footer.terms")} />
      <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
      <InternalLink href="/accessibility" label={t("siteFooter.legalAccessibility")} />
      <span aria-hidden="true" style={{ opacity: 0.4 }}>·</span>
      <ExternalLink href={REPO_URL} label={t("footer.github")} />
    </nav>
  );
}

interface CreditRowProps {
  t: (key: string) => string;
  resolvedVersion: string;
}

function CreditRow({ t, resolvedVersion }: CreditRowProps): JSX.Element {
  return (
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
  );
}

/**
 * polish-2 T8 — Reverse-scroll wordmark.
 *
 * Reads scroll velocity (px/ms) and accumulates a horizontal offset that
 * moves OPPOSITE to scroll direction. Magnitude scales with velocity so
 * the wordmark drifts gently rather than races.
 */
function ReverseWordmark(): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const offsetRef = useRef<number>(0);
  const { velocity } = useScrollVelocity(0.5);

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    let lastY = window.scrollY ?? 0;
    let rafId: number | null = null;
    const tick = () => {
      const y = window.scrollY ?? 0;
      const dy = y - lastY;
      lastY = y;
      const speed = Math.min(40, Math.abs(velocity) * 30 + Math.abs(dy) * 0.6);
      const sign = dy > 0 ? -1 : dy < 0 ? 1 : 0;
      offsetRef.current = (offsetRef.current + sign * speed) % 4000;
      if (ref.current) {
        ref.current.style.transform = `translateX(${offsetRef.current.toFixed(2)}px)`;
      }
      rafId = window.requestAnimationFrame(tick);
    };
    rafId = window.requestAnimationFrame(tick);
    return () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
    };
  }, [velocity]);

  return (
    <div
      data-site-footer-wordmark
      aria-hidden="true"
      className="site-footer__wordmark-row"
    >
      <div ref={ref} className="site-footer__wordmark">
        <span>GOWORK&nbsp;·&nbsp;GOWORK&nbsp;·&nbsp;GOWORK&nbsp;·&nbsp;GOWORK&nbsp;·&nbsp;GOWORK&nbsp;·&nbsp;GOWORK</span>
      </div>
    </div>
  );
}

interface ColumnsGridProps {
  t: (key: string) => string;
}

function ColumnsGrid({ t }: ColumnsGridProps): JSX.Element {
  return (
    <div className="mx-auto max-w-screen-2xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12">
      <BrandColumn
        brandHeading={t("siteFooter.brandHeading")}
        brandTagline={t("siteFooter.brandTagline")}
      />
      <FooterColumn heading={t("siteFooter.workersHeading")}>
        <li><InternalLink href="/assess" label={t("siteFooter.workersPlan")} /></li>
        <li><InternalLink href="/case-manager" label={t("siteFooter.workersNavigator")} /></li>
        <li><InternalLink href="/daily" label={t("siteFooter.workersDaily")} /></li>
        <li><InternalLink href="/documents/resume" label={t("siteFooter.workersDocuments")} /></li>
      </FooterColumn>
      <FooterColumn heading={t("siteFooter.navigatorsHeading")}>
        <li><InternalLink href="/case-manager" label={t("siteFooter.navigatorsCaseload")} /></li>
        <li><InternalLink href="/case-manager?view=outcomes" label={t("siteFooter.navigatorsOutcomes")} /></li>
        <li><ExternalLink href={TRAINING_URL} label={t("siteFooter.navigatorsTraining")} /></li>
      </FooterColumn>
      <FooterColumn heading={t("siteFooter.citiesHeading")}>
        <li><ExternalLink href={REPO_URL} label={t("siteFooter.citiesDeploy")} /></li>
        <li><ExternalLink href={PRESS_KIT_URL} label={t("siteFooter.citiesPress")} /></li>
        <li><ExternalLink href={REPO_URL} label={t("siteFooter.citiesOpenSource")} /></li>
      </FooterColumn>
    </div>
  );
}

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
      {/* polish-3 fix — kept the four-column footer (brand + workers +
       *  navigators + cities). The reverse-scroll GOWORK wordmark that
       *  used to sit BELOW the legal+credit row is removed: it duplicated
       *  the Ch08 closer + bloated the bottom of the page. The columns
       *  are the actual nav, they stay. */}
      <ColumnsGrid t={t} />
      <LegalNav t={t} />
      <CreditRow t={t} resolvedVersion={resolvedVersion} />
    </footer>
  );
}
