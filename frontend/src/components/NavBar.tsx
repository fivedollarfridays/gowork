"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/hooks/useTranslation";

type NavLink = { href: string; labelKey: string };

// Keep list in a single source of truth so desktop + mobile render identically.
// "/case-manager" is the landing page for T12.31 (planned); link is still surfaced
// per T12.30 AC so advisors can reach the existing dashboard page today.
const NAV_LINKS: ReadonlyArray<NavLink> = [
  { href: "/appointments", labelKey: "nav.appointments" },
  { href: "/jobs", labelKey: "nav.jobs" },
  { href: "/documents/resume", labelKey: "nav.documents" },
  { href: "/daily", labelKey: "nav.daily" },
  { href: "/case-manager", labelKey: "nav.caseManager" },
];

export function NavBar() {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const primaryLabel = t("nav.primary");
  const toggleLabel = t("nav.toggle");

  return (
    <>
      {/* Single <nav> landmark. Desktop links are inline; mobile drawer reuses
          the same list via the `mobileOpen` expand. We avoid a second <nav>
          landmark to keep the accessibility tree clean. */}
      <nav aria-label={primaryLabel} className="flex items-center">
        <ul className="hidden sm:flex items-center gap-1 list-none p-0 m-0">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Button variant="ghost" size="sm" asChild>
                <Link href={link.href}>{t(link.labelKey)}</Link>
              </Button>
            </li>
          ))}
        </ul>

        <Button
          variant="ghost"
          size="icon"
          className="sm:hidden"
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={toggleLabel}
          aria-expanded={mobileOpen}
          aria-controls="nav-mobile-drawer"
        >
          {mobileOpen ? (
            <X className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Menu className="h-5 w-5" aria-hidden="true" />
          )}
        </Button>
      </nav>

      {/* Mobile drawer — full-width strip after the header row. Not a nav
          landmark (outer nav already covers this); uses a <ul> for semantics. */}
      <div
        id="nav-mobile-drawer"
        className={cn(
          "sm:hidden border-t overflow-hidden transition-all w-full",
          mobileOpen ? "max-h-96" : "max-h-0",
        )}
      >
        <ul className="flex flex-col px-4 py-2 list-none">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block py-2 text-sm font-medium text-foreground/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                {t(link.labelKey)}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
