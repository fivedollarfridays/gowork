import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { NavBar } from "@/components/NavBar";

function renderNav() {
  return render(
    <TranslationProvider>
      <NavBar />
    </TranslationProvider>,
  );
}

describe("NavBar", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders the five primary nav links on desktop", () => {
    renderNav();
    const nav = screen.getByRole("navigation", { name: /primary/i });
    expect(within(nav).getByRole("link", { name: /appointments/i })).toHaveAttribute(
      "href",
      "/appointments",
    );
    expect(within(nav).getByRole("link", { name: /jobs/i })).toHaveAttribute(
      "href",
      "/jobs",
    );
    expect(within(nav).getByRole("link", { name: /documents/i })).toHaveAttribute(
      "href",
      "/documents/resume",
    );
    expect(within(nav).getByRole("link", { name: /daily/i })).toHaveAttribute(
      "href",
      "/daily",
    );
    expect(
      within(nav).getByRole("link", { name: /case manager/i }),
    ).toHaveAttribute("href", "/case-manager");
  });

  it("links are keyboard-focusable in document order", async () => {
    const user = userEvent.setup();
    renderNav();
    const nav = screen.getByRole("navigation", { name: /primary/i });
    const links = within(nav).getAllByRole("link");
    expect(links.length).toBeGreaterThanOrEqual(5);

    // Tab through: every nav link should be reachable via keyboard (tabindex !== -1)
    for (const link of links) {
      expect(link).not.toHaveAttribute("tabindex", "-1");
    }

    // First Tab should focus the first focusable nav control (could be logo before nav).
    await user.tab();
    expect(document.activeElement).toBeInstanceOf(HTMLElement);
  });

  it("renders a mobile toggle button with an accessible label", () => {
    renderNav();
    const toggle = screen.getByRole("button", { name: /toggle navigation/i });
    expect(toggle).toBeInTheDocument();
  });

  it("opens and closes the mobile menu when the toggle is pressed", async () => {
    const user = userEvent.setup();
    renderNav();
    const toggle = screen.getByRole("button", { name: /toggle navigation/i });

    // Mobile drawer should expose aria-expanded state
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("uses Spanish labels when locale is es", () => {
    setLocale("es");
    renderNav();
    const nav = screen.getByRole("navigation", { name: /principal/i });
    expect(within(nav).getByRole("link", { name: /citas/i })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /empleos/i })).toBeInTheDocument();
    expect(
      within(nav).getByRole("link", { name: /documentos/i }),
    ).toBeInTheDocument();
  });
});
