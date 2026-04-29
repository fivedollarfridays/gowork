/**
 * SiteHeader — sprint/gowork-facelift Driver A.
 *
 * Sticky glass-blur top bar. Brand mark + wordmark left; full primary nav
 * centered (six items including Plan); theme toggle + language toggle +
 * "Get your plan" CTA on the right. Mobile collapses nav to a hamburger.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
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
