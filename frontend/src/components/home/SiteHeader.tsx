"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X, Moon, Sun } from "lucide-react";
import { BrandMark } from "@/components/wall/BrandMark";
import { LanguageToggle } from "@/components/wall/LanguageToggle";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * SiteHeader — sprint/gowork-facelift Driver A.
 *
 * Sticky glass-blur top chrome that anchors every chapter screen. Houses
 * brand mark + wordmark on the left, the six-link primary nav in the
 * center, and theme/language/CTA controls on the right. Mobile collapses
 * the center nav to a hamburger drawer.
 *
 * Theme toggle persists to localStorage and, when a Mapbox map is mounted,
 * also calls `window._gw_map.setStyle(...)` so the chapter map layer flips
 * with the rest of the chrome (Driver C wires `_gw_map` from MapboxScene).
 */

type NavLink = { href: string; labelKey: string };

const PRIMARY_LINKS: ReadonlyArray<NavLink> = [
  { href: "/assess", labelKey: "nav.plan" },
  { href: "/daily", labelKey: "nav.daily" },
  { href: "/jobs", labelKey: "nav.jobs" },
  { href: "/documents/resume", labelKey: "nav.documents" },
  { href: "/appointments", labelKey: "nav.appointments" },
  { href: "/case-manager", labelKey: "nav.caseManager" },
];

const THEME_STORAGE_KEY = "gowork-theme";
const MAPBOX_STYLE_LIGHT = "mapbox://styles/mapbox/light-v11";
const MAPBOX_STYLE_DARK = "mapbox://styles/mapbox/dark-v11";

type Theme = "light" | "dark";

declare global {
  interface Window {
    _gw_map?: { setStyle: (style: string) => void };
  }
}

function readStoredTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "dark";
}

export function SiteHeader(): JSX.Element {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("dark");

  // Hydrate stored theme on mount.
  useEffect(() => {
    setTheme(readStoredTheme());
  }, []);

  // Mirror theme to <html data-theme> + document.documentElement.classList
  // so CSS rules can target it. Persist to localStorage. Bridge to Mapbox.
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
    if (typeof window !== "undefined") {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
      const map = window._gw_map;
      if (map && typeof map.setStyle === "function") {
        map.setStyle(theme === "dark" ? MAPBOX_STYLE_DARK : MAPBOX_STYLE_LIGHT);
      }
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return (
    <header
      role="banner"
      data-site-header
      className="sticky top-0 left-0 right-0 w-full backdrop-blur-md border-b z-[var(--z-header)]"
      style={{
        background: "color-mix(in oklch, var(--bg-base), transparent 25%)",
        borderBottomColor: "color-mix(in oklch, var(--fg-primary), transparent 90%)",
      }}
    >
      <div className="mx-auto max-w-screen-2xl px-6 h-16 flex items-center justify-between gap-4">
        {/* LEFT — Brand */}
        <Link
          href="/"
          aria-label={t("header.brand.label")}
          className="flex items-center gap-2 shrink-0"
          style={{ color: "var(--fg-primary)" }}
        >
          <BrandMark size={26} interactive />
          <span
            className="font-bold tracking-tight text-lg"
            style={{ letterSpacing: "-0.02em" }}
          >
            GoWork
          </span>
        </Link>

        {/* CENTER — Primary nav (desktop) */}
        <nav
          aria-label={t("nav.primary")}
          className="hidden lg:flex items-center gap-1"
        >
          <ul className="flex items-center gap-1 list-none p-0 m-0">
            {PRIMARY_LINKS.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="site-nav__link relative px-3 py-2 text-sm font-medium rounded-md transition-colors"
                  style={{ color: "var(--fg-secondary)" }}
                >
                  {t(link.labelKey)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* RIGHT — Theme, Language, CTA */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={t("nav.themeToggleAria")}
            className="inline-flex items-center justify-center rounded-full border h-9 w-9 transition-colors"
            style={{
              borderColor: "color-mix(in oklch, var(--fg-primary), transparent 85%)",
              color: "var(--fg-primary)",
            }}
            data-theme-toggle
            data-current-theme={theme}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Moon className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
          <div className="hidden sm:block">
            <LanguageToggle />
          </div>
          <Link
            href="/assess"
            className="hidden md:inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm font-semibold transition-transform hover:scale-[1.02]"
            style={{
              background: "var(--accent-cyan)",
              color: "var(--bg-base)",
            }}
            data-cta-plan
          >
            {t("nav.ctaPlan")}
            <span aria-hidden="true">→</span>
          </Link>
          <button
            type="button"
            className="lg:hidden inline-flex items-center justify-center rounded-md h-9 w-9"
            onClick={() => setMobileOpen((open) => !open)}
            aria-label={t("nav.toggle")}
            aria-expanded={mobileOpen}
            aria-controls="site-header-mobile-drawer"
            style={{ color: "var(--fg-primary)" }}
          >
            {mobileOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      <div
        id="site-header-mobile-drawer"
        className={`lg:hidden overflow-hidden transition-[max-height] ${
          mobileOpen ? "max-h-[480px]" : "max-h-0"
        }`}
        style={{
          background: "var(--bg-surface)",
          borderTop: mobileOpen
            ? "1px solid color-mix(in oklch, var(--fg-primary), transparent 90%)"
            : "0",
        }}
      >
        <ul className="flex flex-col px-6 py-3 list-none gap-1">
          {PRIMARY_LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block py-2 text-base font-medium"
                style={{ color: "var(--fg-primary)" }}
              >
                {t(link.labelKey)}
              </Link>
            </li>
          ))}
          <li className="pt-2 sm:hidden">
            <LanguageToggle />
          </li>
        </ul>
      </div>
    </header>
  );
}
