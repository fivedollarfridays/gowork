/**
 * W1 Driver C — T1.51 Header rewrite tests.
 *
 * The new header is the GoWork brand surface :
 *   - Brand mark (G + path SVG) top-left, linked to "/".
 *   - Optional chapter counter top-right (when wallChapter prop is set).
 *   - Mute toggle, language toggle, GitHub icon link.
 *   - aria-current applied when on the wall (Driver B's chapter-state
 *     hook will pass `wallChapter` from useScrollProgress in W2).
 *
 * Existing NavBar (appointments / jobs / documents / daily / case-manager)
 * is preserved — we are not killing the worker companion's nav surface.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

// StallAlertBannerMount depends on useSessionId / useSearchParams which
// require a Next router context that vitest's jsdom doesn't supply.
// Mock the mount to a no-op so we exercise the new W1 header surface
// in isolation; T13.6 still owns the banner integration test.
vi.mock("@/components/layout/StallAlertBannerMount", () => ({
  StallAlertBannerMount: () => null,
}));

import { Header } from "../Header";

describe("Header (T1.51)", () => {
  beforeEach(() => setLocale("en"));

  it("renders the brand mark linked to home", () => {
    render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    const brandLink = screen.getByRole("link", { name: /gowork/i });
    expect(brandLink).toHaveAttribute("href", "/");
    expect(within(brandLink).queryByRole("img")).toBeInTheDocument();
  });

  it("hides the chapter counter when wallChapter is omitted", () => {
    render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    expect(screen.queryByTestId("aria-live-region")).not.toBeInTheDocument();
    // The counter renders [data-counter]; absent when prop is undefined.
    const { container } = render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    expect(container.querySelector("[data-counter]")).toBeNull();
  });

  it("shows the chapter counter when wallChapter is passed", () => {
    const { container } = render(
      <TranslationProvider>
        <Header wallChapter={{ current: 3, total: 10 }} />
      </TranslationProvider>,
    );
    expect(container.querySelector("[data-counter]")).toBeInTheDocument();
    expect(screen.getByText("03")).toBeInTheDocument();
  });

  it("renders the mute toggle and language toggle", () => {
    render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    expect(
      screen.getByRole("switch", { name: /toggle ambient sound/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^en$/i })).toBeInTheDocument();
  });

  it("renders the GitHub icon link", () => {
    render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    const gh = screen.getByRole("link", { name: /github/i });
    expect(gh).toHaveAttribute("href");
    expect(gh.getAttribute("href") ?? "").toMatch(/github\.com/);
  });

  it("does NOT include the legacy MontGoWork wordmark", () => {
    const { container } = render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    expect(container.textContent ?? "").not.toMatch(/MontGoWork/);
  });
});
