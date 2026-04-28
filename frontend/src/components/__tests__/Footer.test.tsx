/**
 * T13.115 — Legal Footer
 *
 * Verifies the site-wide legal footer:
 * - links to /privacy and /terms
 * - shows the legal entity name
 * - localizes via the i18n catalog (footer.* keys)
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { Footer } from "../layout/Footer";

function renderFooter() {
  return render(
    <TranslationProvider>
      <Footer />
    </TranslationProvider>,
  );
}

describe("Footer", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders a contentinfo landmark", () => {
    renderFooter();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("links to /privacy", () => {
    renderFooter();
    const privacy = screen.getByRole("link", { name: /privacy/i });
    expect(privacy).toHaveAttribute("href", "/privacy");
  });

  it("links to /terms", () => {
    renderFooter();
    const terms = screen.getByRole("link", { name: /terms/i });
    expect(terms).toHaveAttribute("href", "/terms");
  });

  it("shows the legal entity name", () => {
    renderFooter();
    // After W1 Driver C merge, footer renders BOTH the new GoWork brand
    // mark/label AND the legacy footer.entity placeholder. Multiple matches
    // is the correct state — assert at least one.
    expect(screen.getAllByText(/GoWork/).length).toBeGreaterThan(0);
  });

  it("renders Spanish labels when locale is es", () => {
    setLocale("es");
    renderFooter();
    // ES copy uses 'Privacidad' and 'Términos'
    expect(
      screen.getByRole("link", { name: /privacidad/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /términos/i }),
    ).toBeInTheDocument();
  });
});
