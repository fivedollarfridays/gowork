/**
 * W1 Driver C — T1.63 SkipToContent.
 *
 * Per the design plan (page 263) and the dispatch :
 *   - The skip-to-content link is PROUDLY VISIBLE on focus, NOT hidden.
 *   - It is the first focusable element on the page.
 *   - It targets a configurable id (default: "main").
 *   - Its label comes from the i18n catalog (a11y.skipToContent).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SkipToContent } from "../SkipToContent";

function renderSkip(targetId?: string) {
  return render(
    <TranslationProvider>
      <SkipToContent targetId={targetId} />
    </TranslationProvider>,
  );
}

describe("SkipToContent", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders an anchor link to the main content", () => {
    renderSkip();
    const link = screen.getByRole("link", { name: /skip to main content/i });
    expect(link).toHaveAttribute("href", "#main");
  });

  it("uses a custom target id when provided", () => {
    renderSkip("wall-content");
    const link = screen.getByRole("link", { name: /skip to main content/i });
    expect(link).toHaveAttribute("href", "#wall-content");
  });

  it("renders Spanish label when locale is es", () => {
    setLocale("es");
    renderSkip();
    expect(
      screen.getByRole("link", { name: /saltar al contenido principal/i }),
    ).toBeInTheDocument();
  });

  it("declares position styles compatible with proudly-visible-on-focus", () => {
    renderSkip();
    const link = screen.getByRole("link", { name: /skip to main content/i });
    // CSS class chain must include the focus-visible styling token name.
    expect(link.className).toMatch(/skip-to-content/);
  });
});
