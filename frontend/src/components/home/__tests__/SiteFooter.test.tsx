/**
 * SiteFooter — three-column footer + brand column. HackFW credit row,
 * version pin. Sprint/gowork-facelift Driver A.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SiteFooter } from "../SiteFooter";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("SiteFooter — structure", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders without crashing as a contentinfo landmark", () => {
    wrap(<SiteFooter />);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("renders the brand tagline", () => {
    wrap(<SiteFooter />);
    expect(
      screen.getByText(/workforce infrastructure for any american city/i),
    ).toBeInTheDocument();
  });

  it("renders all three section headings", () => {
    wrap(<SiteFooter />);
    expect(screen.getByRole("heading", { name: /for workers/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /for navigators/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /for cities/i })).toBeInTheDocument();
  });

  it("links Plan to /assess in the workers column", () => {
    const { container } = wrap(<SiteFooter />);
    const link = container.querySelector('a[href="/assess"]');
    expect(link).toBeTruthy();
  });

  it("links Outcomes dashboard to /case-manager/outcomes", () => {
    const { container } = wrap(<SiteFooter />);
    const link = container.querySelector('a[href="/case-manager/outcomes"]');
    expect(link).toBeTruthy();
  });

  it("links Deploy GoWork to the GitHub repo", () => {
    const { container } = wrap(<SiteFooter />);
    const link = container.querySelector(
      'a[href="https://github.com/fivedollarfridays/montgowork"]',
    );
    expect(link).toBeTruthy();
  });

  it("renders the HackFW credit and the shipped line", () => {
    wrap(<SiteFooter />);
    expect(screen.getByText(/HackFW 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/built in texas/i)).toBeInTheDocument();
  });

  it("renders the version label using the prop fallback", () => {
    wrap(<SiteFooter version="v1.2.3" />);
    expect(screen.getByText(/v1\.2\.3/)).toBeInTheDocument();
  });
});

describe("SiteFooter — i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders Spanish tagline when locale is ES", () => {
    setLocale("es");
    wrap(<SiteFooter />);
    expect(
      screen.getByText(/infraestructura laboral para cualquier ciudad/i),
    ).toBeInTheDocument();
  });
});
