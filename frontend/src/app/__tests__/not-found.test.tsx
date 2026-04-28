/**
 * NotFound page — legacy contract preserved for shape; copy migrated to
 * the W1 wall-metaphor branding (T1.40). The 404 was originally introduced
 * in T13.x with "Page not found" / two CTAs (back to home + open daily
 * plan). The W1 sprint replaces the copy with "There is no path to this
 * URL — but there is one through the wall" sourced from the i18n catalog
 * (edge.404.*) and consolidates to a single CTA.
 *
 * The deeper W1 contract (main#main landmark for skip-to-content,
 * Spanish parity, no MontGoWork string) is guarded in
 * `edge-not-found.test.tsx`.
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

describe("NotFound page (W1 wall-metaphor copy)", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders the wall-metaphor 404 title in English", () => {
    renderNotFound();
    expect(
      screen.getByRole("heading", { name: /no path to this URL/i }),
    ).toBeInTheDocument();
  });

  it("renders the explanatory body copy referencing the wall", () => {
    renderNotFound();
    // Body and title both reference the wall metaphor.
    expect(screen.getAllByText(/wall|barrier/i).length).toBeGreaterThanOrEqual(
      1,
    );
  });

  it("links the single CTA back to home", () => {
    renderNotFound();
    const homeLink = screen.getByRole("link", { name: /back to the wall/i });
    expect(homeLink).toHaveAttribute("href", "/");
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    renderNotFound();
    expect(
      screen.getByRole("heading", { name: /no hay un camino/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /volver al muro/i }),
    ).toBeInTheDocument();
  });

  it("uses responsive layout classes (centered + max-width)", () => {
    const { container } = renderNotFound();
    const main = container.querySelector("main");
    expect(main).toBeTruthy();
    expect(main?.className).toMatch(/max-w-|mx-auto/);
  });
});
