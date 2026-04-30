/**
 * SiteHeader — sprint/gowork-facelift Driver A.
 *
 * Sticky glass-blur top bar. Brand mark + wordmark left; full primary nav
 * centered (six items including Plan); theme toggle + language toggle +
 * "Get your plan" CTA on the right. Mobile collapses nav to a hamburger.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SiteHeader } from "../SiteHeader";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("SiteHeader — chrome and structure", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders without crashing as a banner landmark", () => {
    wrap(<SiteHeader />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("renders the canonical BrandMark + GoWork wordmark on the left", () => {
    const { container } = wrap(<SiteHeader />);
    expect(container.querySelector("svg.gowork-mark")).toBeInTheDocument();
    expect(screen.getByText(/GoWork/i)).toBeInTheDocument();
  });

  it("renders all six primary nav links with next/link hrefs", () => {
    wrap(<SiteHeader />);
    const nav = screen.getByRole("navigation", { name: /primary navigation/i });
    expect(nav).toBeInTheDocument();
    // The six required links by href:
    const expected = [
      "/assess",
      "/daily",
      "/jobs",
      "/documents/resume",
      "/appointments",
      "/case-manager",
    ];
    for (const href of expected) {
      const link = nav.querySelector(`a[href="${href}"]`);
      expect(link, `expected nav link to ${href}`).toBeTruthy();
    }
  });

  it("renders the Get your plan CTA pill linking to /assess", () => {
    wrap(<SiteHeader />);
    const cta = screen.getByRole("link", { name: /get your plan/i });
    expect(cta).toHaveAttribute("href", "/assess");
  });

  it("renders the language toggle (EN/ES) buttons", () => {
    wrap(<SiteHeader />);
    expect(screen.getAllByRole("button", { name: /^en$/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: /^es$/i }).length).toBeGreaterThan(0);
  });

  it("renders the theme toggle with aria-label", () => {
    wrap(<SiteHeader />);
    const themeBtn = screen.getByRole("button", { name: /toggle light or dark theme/i });
    expect(themeBtn).toBeInTheDocument();
  });
});

describe("SiteHeader — i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("swaps nav labels when locale switches to ES", () => {
    setLocale("es");
    wrap(<SiteHeader />);
    // Spanish for "Get your plan" is "Obtén tu plan".
    expect(screen.getByRole("link", { name: /obtén tu plan/i })).toBeInTheDocument();
  });
});

describe("SiteHeader — theme toggle does NOT touch the Mapbox style", () => {
  // Bug 2 (feat/light-mode-polish): the map is locked dark in both
  // themes via `Chapter04TheMap.mount.ts::readStyleUrl` (the light-v11
  // path was never visually polished — atmosphere overlay washes it out
  // and the tintStyle paints navy chrome over a light base, producing
  // bloomy/unreadable street artifacts). The theme toggle MUST NOT call
  // `window._gw_map.setStyle(...)`. We verify by installing a stub map
  // surface, mounting the header, and asserting setStyle was never
  // invoked even after a theme flip.
  const setStyleSpy = vi.fn();

  beforeEach(() => {
    setLocale("en");
    setStyleSpy.mockReset();
    // Reset html attributes so each test runs against a clean theme.
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.classList.remove("dark");
    // Install a stub Mapbox bridge — if the header calls setStyle, this
    // spy fires and the test fails.
    (window as unknown as { _gw_map?: { setStyle: (s: string) => void } })._gw_map = {
      setStyle: setStyleSpy,
    };
    window.localStorage.setItem("gowork-theme", "dark");
  });

  it("does not invoke window._gw_map.setStyle on initial mount", () => {
    wrap(<SiteHeader />);
    expect(setStyleSpy).not.toHaveBeenCalled();
  });

  it("does not invoke setStyle after the user clicks the theme toggle", () => {
    wrap(<SiteHeader />);
    const themeBtn = screen.getByRole("button", {
      name: /toggle light or dark theme/i,
    });
    // Flip dark → light.
    act(() => {
      themeBtn.click();
    });
    expect(setStyleSpy).not.toHaveBeenCalled();
    // Flip back to dark.
    act(() => {
      themeBtn.click();
    });
    expect(setStyleSpy).not.toHaveBeenCalled();
  });
});
