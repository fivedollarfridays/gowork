/**
 * W1 Driver C — T1.40 branded 404 page.
 *
 * Asserts :
 *   - Title from i18n (edge.404.title) renders.
 *   - Body copy mentions the wall metaphor (NOT the default "Page not found").
 *   - CTA links to "/" with the i18n label.
 *   - The route renders a `main` landmark with id="main" so the
 *     SkipToContent link still works on the 404 page.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import NotFound from "../not-found";

function renderNotFound() {
  return render(
    <TranslationProvider>
      <NotFound />
    </TranslationProvider>,
  );
}

describe("/not-found — T1.40 branded 404", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders the branded title", () => {
    renderNotFound();
    expect(
      screen.getByRole("heading", { name: /no path to this URL/i }),
    ).toBeInTheDocument();
  });

  it("body copy keeps the wall metaphor", () => {
    renderNotFound();
    // The metaphor is intentionally repeated in title + body.
    const matches = screen.getAllByText(/wall|barrier/i);
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("CTA links back to /", () => {
    renderNotFound();
    const cta = screen.getByRole("link", { name: /back to the wall/i });
    expect(cta).toHaveAttribute("href", "/");
  });

  it("renders a main landmark with id=main for skip-to-content compatibility", () => {
    const { container } = renderNotFound();
    const main = container.querySelector("main#main");
    expect(main).toBeInTheDocument();
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    renderNotFound();
    expect(
      screen.getByRole("heading", { name: /no hay un camino/i }),
    ).toBeInTheDocument();
  });
});
