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

describe("NotFound page", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders the 404 title in English", () => {
    renderNotFound();
    expect(screen.getByRole("heading", { name: /page not found/i })).toBeInTheDocument();
  });

  it("renders the explanatory body copy", () => {
    renderNotFound();
    expect(
      screen.getByText(/doesn't exist or has moved/i),
    ).toBeInTheDocument();
  });

  it("links primary CTA back to home", () => {
    renderNotFound();
    const homeLink = screen.getByRole("link", { name: /back to home/i });
    expect(homeLink).toHaveAttribute("href", "/");
  });

  it("links secondary CTA to /daily", () => {
    renderNotFound();
    const dailyLink = screen.getByRole("link", { name: /daily plan/i });
    expect(dailyLink).toHaveAttribute("href", "/daily");
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    renderNotFound();
    expect(
      screen.getByRole("heading", { name: /página no encontrada/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /volver al inicio/i })).toBeInTheDocument();
  });

  it("uses responsive layout classes (centered + max-width)", () => {
    const { container } = renderNotFound();
    // The main wrapper should constrain width and center on desktop.
    const main = container.querySelector("main");
    expect(main).toBeTruthy();
    expect(main?.className).toMatch(/max-w-|mx-auto/);
  });
});
