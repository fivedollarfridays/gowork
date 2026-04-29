/**
 * PageMeta — bottom-right HUD rows showing city, chapter, scroll %,
 * and time-of-day light label. Sprint/gowork-facelift Driver A.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { PageMeta } from "../PageMeta";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("PageMeta — structure", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders without crashing as a complementary landmark", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />);
    expect(screen.getByRole("complementary", { name: /page meta/i })).toBeInTheDocument();
  });

  it("renders the city in the CITY row", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />);
    expect(screen.getByText(/Fort Worth, TX/)).toBeInTheDocument();
  });

  it("renders the chapter in N / total form", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={3} totalChapters={8} progress={0.5} hour={9} />);
    expect(screen.getByText(/03\s*\/\s*08/)).toBeInTheDocument();
  });

  it("renders the scroll percentage rounded to integer", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0.42} hour={9} />);
    expect(screen.getByText(/42%/)).toBeInTheDocument();
  });

  it("renders the LIGHT label morning when hour is 9", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />);
    expect(screen.getByText(/morning/i)).toBeInTheDocument();
  });

  it("renders the LIGHT label golden when hour is 17 (5pm)", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={17} />);
    expect(screen.getByText(/golden/i)).toBeInTheDocument();
  });

  it("renders the LIGHT label night when hour is 23", () => {
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={23} />);
    expect(screen.getByText(/night/i)).toBeInTheDocument();
  });
});

describe("PageMeta — i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders Spanish row labels when locale is ES", () => {
    setLocale("es");
    wrap(<PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />);
    expect(screen.getByText(/CIUDAD/)).toBeInTheDocument();
    expect(screen.getByText(/CAPÍTULO/)).toBeInTheDocument();
  });
});
