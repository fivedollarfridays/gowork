"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X, Moon, Sun, Flashlight, FlashlightOff } from "lucide-react";
import { BrandMark } from "@/components/wall/BrandMark";
import { LanguageToggle } from "@/components/wall/LanguageToggle";
import {
  CURSOR_FLASHLIGHT_EVENT,
  CURSOR_FLASHLIGHT_STORAGE_KEY,
} from "@/components/home/CursorFlashlight";
import { useTranslation } from "@/hooks/useTranslation";
import { useScrollDirection } from "@/hooks/useScrollDirection";

/**
 * SiteHeader — sprint/gowork-facelift Driver A. Polish-2 wires:
 *   - T2  scroll-direction hide/show (data-header-state="hidden|visible")
 *   - T4  consume `--chrome-accent` for CTA bg + brand-mark glow + border
 *   - T7  BrandMark loading-loop until first non-zero scroll
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
/* Mapbox style URLs intentionally NOT consumed by `useThemeMirror` —
 * see the hook's comment block below. The map locks dark in both themes
 * (Bug 2 / feat/light-mode-polish). When the light variant is re-enabled
 * in a future polish pass, restore:
 *   const MAPBOX_STYLE_LIGHT = "mapbox://styles/mapbox/light-v11";
 *   const MAPBOX_STYLE_DARK = "mapbox://styles/mapbox/dark-v11";
 * and the `map.setStyle(...)` call in `useThemeMirror`. */

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

/** Hook that flips brand-mark loading off after first non-zero scroll OR
 *  the `gowork:ch1-entered` custom event (T7). */
function useBrandLoading(): boolean {
  const [brandLoading, setBrandLoading] = useState<boolean>(true);
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const finish = () => setBrandLoading(false);
    const onScroll = () => {
      if ((window.scrollY ?? 0) > 0) finish();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("gowork:ch1-entered", finish);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("gowork:ch1-entered", finish);
    };
  }, []);
  return brandLoading;
}

/** Hook that mirrors `theme` to the documentElement.
 *
 * The hook deliberately does NOT swap the Mapbox style on theme toggle.
 * The Ch04 map is locked dark in BOTH themes via
 * `Chapter04TheMap.mount.ts::readStyleUrl` — the light-v11 branch was
 * never visually polished (the dark atmosphere overlay washes it out and
 * `tintStyle()` paints navy chrome over the light base, producing bloomy
 * unreadable street artifacts that read as "white-on-white glow"). Map
 * chip text + the SVG overlay are locked to cream literals via
 * `home-chapters.css` and `home-velocity.css` so they stay legible over
 * the perma-dark map regardless of theme. See feat/light-mode-polish
 * (Bug 2) for the full audit trail.
 *
 * `MAPBOX_STYLE_LIGHT` / `MAPBOX_STYLE_DARK` constants and the
 * `_gw_map.setStyle` bridge in mount.ts are intentionally retained — a
 * future polish pass can re-enable a properly-tinted light variant
 * without re-introducing the storage key shape change.
 */
function useThemeMirror(theme: Theme): void {
  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
    if (typeof window !== "undefined") {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    }
  }, [theme]);
}

interface BrandColumnProps {
  brandLoading: boolean;
  brandLabel: string;
}

function BrandColumn({ brandLoading, brandLabel }: BrandColumnProps): JSX.Element {
  return (
    <Link
      href="/"
      aria-label={brandLabel}
      className="flex items-center gap-2 shrink-0"
      style={{ color: "var(--fg-primary)" }}
    >
      <span
        data-brand-mark
        data-loading={brandLoading ? "true" : "false"}
        className="inline-flex items-center"
        style={{
          filter:
            "drop-shadow(0 0 6px color-mix(in oklch, var(--chrome-accent, var(--accent-cyan)), transparent 60%))",
          transition:
            "filter 800ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1))",
        }}
      >
        <BrandMark size={26} interactive={!brandLoading} loading={brandLoading} />
      </span>
      <span
        className="font-bold tracking-tight text-lg"
        style={{ letterSpacing: "-0.02em" }}
      >
        GoWork
      </span>
    </Link>
  );
}

interface PrimaryNavProps {
  t: (key: string) => string;
}

function PrimaryNav({ t }: PrimaryNavProps): JSX.Element {
  return (
    <nav aria-label={t("nav.primary")} className="hidden lg:flex items-center gap-1">
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
  );
}

interface ChromeControlsProps {
  t: (key: string) => string;
  theme: Theme;
  toggleTheme: () => void;
  mobileOpen: boolean;
  setMobileOpen: (next: (prev: boolean) => boolean) => void;
}

interface ThemeBtnProps {
  t: (key: string) => string;
  theme: Theme;
  toggleTheme: () => void;
}

function ThemeButton({ t, theme, toggleTheme }: ThemeBtnProps): JSX.Element {
  return (
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
  );
}

/**
 * CursorButton — toggles the global CursorFlashlight on/off. State
 * persisted in localStorage; CursorFlashlight subscribes to a custom
 * event so the toggle takes effect immediately within the same tab.
 * Defaults to "on" — opt-out, not opt-in.
 */
function CursorButton(): JSX.Element {
  const [enabled, setEnabled] = useState<boolean>(true);

  useEffect(() => {
    try {
      setEnabled(window.localStorage.getItem(CURSOR_FLASHLIGHT_STORAGE_KEY) !== "off");
    } catch {
      setEnabled(true);
    }
  }, []);

  const toggle = useCallback(() => {
    setEnabled((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(CURSOR_FLASHLIGHT_STORAGE_KEY, next ? "on" : "off");
      } catch {
        /* localStorage blocked — UI state still flips */
      }
      window.dispatchEvent(new Event(CURSOR_FLASHLIGHT_EVENT));
      return next;
    });
  }, []);

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={enabled ? "Turn off cursor flashlight" : "Turn on cursor flashlight"}
      aria-pressed={enabled}
      title={enabled ? "Cursor flashlight: on" : "Cursor flashlight: off"}
      className="inline-flex items-center justify-center rounded-full border h-9 w-9 transition-colors"
      style={{
        borderColor: "color-mix(in oklch, var(--fg-primary), transparent 85%)",
        color: enabled ? "var(--accent-cyan)" : "var(--fg-muted)",
      }}
      data-cursor-toggle
      data-cursor-enabled={enabled}
    >
      {enabled ? (
        <Flashlight className="h-4 w-4" aria-hidden="true" />
      ) : (
        <FlashlightOff className="h-4 w-4" aria-hidden="true" />
      )}
    </button>
  );
}

function CtaPill({ t }: { t: (key: string) => string }): JSX.Element {
  return (
    <Link
      href="/assess"
      className="hidden md:inline-flex items-center gap-1 rounded-full px-4 py-2 text-sm font-semibold hover:scale-[1.02]"
      style={{
        background: "var(--chrome-accent, var(--accent-cyan))",
        color: "var(--bg-base)",
        transition:
          "background-color 800ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1)), background 800ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1)), transform 200ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1))",
      }}
      data-cta-plan
    >
      {t("nav.ctaPlan")}
      <span aria-hidden="true">→</span>
    </Link>
  );
}

function ChromeControls(props: ChromeControlsProps): JSX.Element {
  const { t, theme, toggleTheme, mobileOpen, setMobileOpen } = props;
  return (
    <div className="flex items-center gap-2 shrink-0">
      <CursorButton />
      <ThemeButton t={t} theme={theme} toggleTheme={toggleTheme} />
      <div className="hidden sm:block">
        <LanguageToggle />
      </div>
      <CtaPill t={t} />
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
  );
}

interface MobileDrawerProps {
  t: (key: string) => string;
  open: boolean;
  close: () => void;
}

function MobileDrawer({ t, open, close }: MobileDrawerProps): JSX.Element {
  return (
    <div
      id="site-header-mobile-drawer"
      className={`lg:hidden overflow-hidden transition-[max-height] ${
        open ? "max-h-[480px]" : "max-h-0"
      }`}
      style={{
        background: "var(--bg-surface)",
        borderTop: open
          ? "1px solid color-mix(in oklch, var(--fg-primary), transparent 90%)"
          : "0",
      }}
    >
      <ul className="flex flex-col px-6 py-3 list-none gap-1">
        {PRIMARY_LINKS.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              onClick={close}
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
  );
}

export function SiteHeader(): JSX.Element {
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("dark");
  const direction = useScrollDirection({ threshold: 80 });
  const headerState = direction === "down" ? "hidden" : "visible";
  const brandLoading = useBrandLoading();

  useEffect(() => {
    setTheme(readStoredTheme());
  }, []);

  useThemeMirror(theme);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return (
    <header
      role="banner"
      data-site-header
      data-header-state={headerState}
      className="sticky top-0 left-0 right-0 w-full backdrop-blur-md border-b z-[var(--z-header)]"
      style={{
        background: "color-mix(in oklch, var(--bg-base), transparent 25%)",
        borderBottomColor:
          "color-mix(in oklch, var(--chrome-accent, var(--accent-cyan)), transparent 80%)",
        transform: headerState === "hidden" ? "translateY(-100%)" : "translateY(0)",
        transition:
          "transform 240ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1)), border-color 800ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1))",
        willChange: "transform",
      }}
    >
      <div className="mx-auto max-w-screen-2xl px-6 h-16 flex items-center justify-between gap-4">
        <BrandColumn brandLoading={brandLoading} brandLabel={t("header.brand.label")} />
        <PrimaryNav t={t} />
        <ChromeControls
          t={t}
          theme={theme}
          toggleTheme={toggleTheme}
          mobileOpen={mobileOpen}
          setMobileOpen={setMobileOpen}
        />
      </div>
      <MobileDrawer t={t} open={mobileOpen} close={() => setMobileOpen(false)} />
    </header>
  );
}
