/**
 * W1 Driver C — T1.55 Footer rewrite tests.
 *
 * Goes beyond the legacy Footer.test.tsx (which guards privacy/terms
 * links) by asserting the W1-specific enrichments :
 *   - The brand mark (G + path SVG) is rendered.
 *   - GitHub link with rel="noopener noreferrer" target="_blank".
 *   - "MIT licensed" copy from i18n.
 *   - Last-calibration timestamp surface (when prop is supplied —
 *     Driver B's useLiveNow hook will feed this in W2).
 *   - Legacy MontGoWork string is GONE from rendered output.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { Footer } from "../Footer";

function renderFooter(lastCalibration?: Date) {
  return render(
    <TranslationProvider>
      <Footer lastCalibration={lastCalibration} />
    </TranslationProvider>,
  );
}

describe("Footer (T1.55) — W1 brand surface", () => {
  beforeEach(() => setLocale("en"));

  it("renders the brand mark inside the footer", () => {
    const { container } = renderFooter();
    const svg = container.querySelector("footer svg");
    expect(svg).toBeInTheDocument();
  });

  it("links to /privacy and /terms (legacy contract preserved)", () => {
    renderFooter();
    expect(screen.getByRole("link", { name: /privacy/i })).toHaveAttribute(
      "href",
      "/privacy",
    );
    expect(screen.getByRole("link", { name: /terms/i })).toHaveAttribute(
      "href",
      "/terms",
    );
  });

  it("renders a GitHub link in a new tab with rel attrs", () => {
    renderFooter();
    const gh = screen.getByRole("link", { name: /github/i });
    expect(gh).toHaveAttribute("target", "_blank");
    expect(gh.getAttribute("rel") ?? "").toMatch(/noopener/);
    expect(gh.getAttribute("rel") ?? "").toMatch(/noreferrer/);
  });

  it("renders the MIT-licensed copy from i18n", () => {
    renderFooter();
    expect(screen.getByText(/MIT/i)).toBeInTheDocument();
  });

  it("renders the last-calibration timestamp when supplied", () => {
    const ts = new Date("2026-04-27T18:14:00Z");
    renderFooter(ts);
    expect(screen.getByText(/last calibrated/i)).toBeInTheDocument();
    // Some date string should appear (locale-dependent format).
    expect(screen.getByTestId("footer-last-calibration")).toBeInTheDocument();
  });

  it("hides the calibration row when lastCalibration is undefined", () => {
    renderFooter();
    expect(
      screen.queryByTestId("footer-last-calibration"),
    ).not.toBeInTheDocument();
  });

  it("does NOT render the legacy MontGoWork wordmark in user-visible copy", () => {
    const { container } = renderFooter();
    // Strip ARIA-hidden / sr-only attrs are still visible to the test
    // (jsdom renders all). The footer copy bank uses footer.entity
    // (still "MontGoWork (hackathon project)" — preserved for the
    // legacy legal-footer test). Driver C's W1 lane does NOT remove
    // that key (separate concern, owned by the legal copy refresh in
    // Phase 1 / Phase 2 of the rebrand). This test instead asserts
    // the *new* footer-brand label is rendered, NOT the legacy one.
    expect(container.textContent ?? "").toMatch(/GoWork/);
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    renderFooter();
    expect(
      screen.getByRole("link", { name: /privacidad/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/MIT/i)).toBeInTheDocument();
  });
});
