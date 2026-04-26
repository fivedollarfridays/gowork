/**
 * T13.115 — Privacy Policy page
 *
 * Verifies that /privacy renders a heading, the major data-flow sections,
 * a counsel-review caveat, and a link to /terms. Spanish locale must render
 * a Spanish heading + the documented body-translation placeholder.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import Privacy from "../privacy/page";

function renderPrivacy() {
  return render(
    <TranslationProvider>
      <Privacy />
    </TranslationProvider>,
  );
}

describe("/privacy page", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders an h1 with the policy title", () => {
    renderPrivacy();
    expect(
      screen.getByRole("heading", { level: 1, name: /privacy/i }),
    ).toBeInTheDocument();
  });

  it("shows a 'last updated' date", () => {
    renderPrivacy();
    expect(screen.getAllByText(/last updated/i).length).toBeGreaterThan(0);
  });

  it("covers the data-collection categories from the inventory", () => {
    renderPrivacy();
    // Drawn from the QC reports cross-references: assess answers, plan
    // checklist, advisor notes, email-for-reminders, audit/IP metadata.
    expect(screen.getAllByText(/session/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/advisor/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/email/i).length).toBeGreaterThan(0);
  });

  it("names third-party processors", () => {
    renderPrivacy();
    expect(screen.getAllByText(/SendGrid/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Anthropic/).length).toBeGreaterThan(0);
  });

  it("describes the 90-day retention sweep", () => {
    renderPrivacy();
    expect(screen.getByText(/90/)).toBeInTheDocument();
  });

  it("includes a counsel-review caveat visible to readers", () => {
    renderPrivacy();
    // A short visible note prevents anyone from quoting the placeholder
    // policy as legally binding. The source-code comment is asserted by a
    // separate test below.
    expect(screen.getByText(/counsel/i)).toBeInTheDocument();
  });

  it("links to the terms page", () => {
    renderPrivacy();
    const termsLink = screen.getByRole("link", { name: /terms/i });
    expect(termsLink).toHaveAttribute("href", "/terms");
  });

  it("renders Spanish heading when locale is es", () => {
    setLocale("es");
    renderPrivacy();
    expect(
      screen.getByRole("heading", { level: 1, name: /privacidad/i }),
    ).toBeInTheDocument();
  });

  it("source file starts with a COUNSEL REVIEW REQUIRED comment", () => {
    const path = resolve(__dirname, "..", "privacy", "page.tsx");
    const text = readFileSync(path, "utf8");
    // The comment MUST be near the top of the file (first 5 lines)
    const head = text.split("\n").slice(0, 5).join("\n");
    expect(head).toContain("COUNSEL REVIEW REQUIRED BEFORE PROD");
  });
});
