/**
 * T13.115 — Terms of Service page
 *
 * Verifies that /terms renders a heading, the major ToS sections,
 * a counsel-review caveat, and a link back to /privacy. Spanish locale must
 * render the Spanish heading + the documented body-translation placeholder.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import Terms from "../terms/page";

function renderTerms() {
  return render(
    <TranslationProvider>
      <Terms />
    </TranslationProvider>,
  );
}

describe("/terms page", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders an h1 with the terms title", () => {
    renderTerms();
    expect(
      screen.getByRole("heading", { level: 1, name: /terms/i }),
    ).toBeInTheDocument();
  });

  it("shows a 'last updated' date", () => {
    renderTerms();
    expect(screen.getAllByText(/last updated/i).length).toBeGreaterThan(0);
  });

  it("describes eligibility (US 18+)", () => {
    renderTerms();
    expect(screen.getAllByText(/eligibility/i).length).toBeGreaterThan(0);
    // Either '18' or 'eighteen' appears in the eligibility section
    const body = document.body.textContent ?? "";
    expect(body).toMatch(/18|eighteen/i);
  });

  it("disclaims that the service is not legal advice", () => {
    renderTerms();
    expect(screen.getAllByText(/legal advice/i).length).toBeGreaterThan(0);
  });

  it("describes the AI-generated output disclaimer", () => {
    renderTerms();
    expect(screen.getAllByText(/AI/).length).toBeGreaterThan(0);
  });

  it("includes a counsel-review caveat visible to readers", () => {
    renderTerms();
    expect(screen.getAllByText(/counsel/i).length).toBeGreaterThan(0);
  });

  it("links to the privacy page", () => {
    renderTerms();
    const privacyLink = screen.getByRole("link", { name: /privacy/i });
    expect(privacyLink).toHaveAttribute("href", "/privacy");
  });

  it("renders Spanish heading when locale is es", () => {
    setLocale("es");
    renderTerms();
    expect(
      screen.getByRole("heading", { level: 1, name: /términos/i }),
    ).toBeInTheDocument();
  });

  it("source file starts with a COUNSEL REVIEW REQUIRED comment", () => {
    const path = resolve(__dirname, "..", "terms", "page.tsx");
    const text = readFileSync(path, "utf8");
    const head = text.split("\n").slice(0, 5).join("\n");
    expect(head).toContain("COUNSEL REVIEW REQUIRED BEFORE PROD");
  });
});
