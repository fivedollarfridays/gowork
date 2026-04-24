import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import {
  StallAlertBanner,
  STALL_BANNER_DISMISS_KEY,
  STALL_BANNER_TTL_MS,
} from "@/components/StallAlertBanner";

function renderBanner(props: React.ComponentProps<typeof StallAlertBanner>) {
  return render(
    <TranslationProvider>
      <StallAlertBanner {...props} />
    </TranslationProvider>,
  );
}

describe("StallAlertBanner", () => {
  beforeEach(() => {
    setLocale("en");
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the banner with role=alert when stallLevel is hard", () => {
    renderBanner({ stallLevel: "hard" });
    const banner = screen.getByRole("alert");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(/let's get you unstuck/i);
  });

  it("does not render when stallLevel is none", () => {
    const { container } = renderBanner({ stallLevel: "none" });
    expect(container.firstChild).toBeNull();
  });

  it("does not render when stallLevel is soft or medium", () => {
    const soft = renderBanner({ stallLevel: "soft" });
    expect(soft.container.firstChild).toBeNull();
    soft.unmount();

    const medium = renderBanner({ stallLevel: "medium" });
    expect(medium.container.firstChild).toBeNull();
  });

  it("renders a Talk to a navigator CTA that links to /plan", () => {
    renderBanner({ stallLevel: "hard" });
    const cta = screen.getByRole("link", { name: /talk to a navigator/i });
    expect(cta).toHaveAttribute("href", "/plan");
  });

  it("renders a dismiss button with an accessible label", () => {
    renderBanner({ stallLevel: "hard" });
    const btn = screen.getByRole("button", { name: /dismiss stall alert/i });
    expect(btn).toBeInTheDocument();
  });

  it("hides the banner after clicking dismiss and persists to localStorage", async () => {
    const user = userEvent.setup();
    renderBanner({ stallLevel: "hard" });
    await user.click(screen.getByRole("button", { name: /dismiss stall alert/i }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    const saved = window.localStorage.getItem(STALL_BANNER_DISMISS_KEY);
    expect(saved).not.toBeNull();
    // Stored as an ISO timestamp.
    expect(Number.isNaN(Date.parse(saved!))).toBe(false);
  });

  it("stays hidden when a dismiss timestamp within the 24h window exists", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    window.localStorage.setItem(STALL_BANNER_DISMISS_KEY, twoHoursAgo);
    const { container } = renderBanner({ stallLevel: "hard" });
    expect(container.firstChild).toBeNull();
  });

  it("re-appears when the dismiss timestamp is older than the TTL", () => {
    const longAgo = new Date(
      Date.now() - STALL_BANNER_TTL_MS - 60 * 1000,
    ).toISOString();
    window.localStorage.setItem(STALL_BANNER_DISMISS_KEY, longAgo);
    renderBanner({ stallLevel: "hard" });
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("ignores corrupted dismiss values (treats as not dismissed)", () => {
    window.localStorage.setItem(STALL_BANNER_DISMISS_KEY, "not-a-date");
    renderBanner({ stallLevel: "hard" });
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("uses the Spanish locale copy when locale is es", () => {
    setLocale("es");
    renderBanner({ stallLevel: "hard" });
    expect(screen.getByRole("alert")).toHaveTextContent(/destrabar/i);
    expect(
      screen.getByRole("link", { name: /hablar con un navegador/i }),
    ).toBeInTheDocument();
  });

  it("exports a 24h TTL constant", () => {
    expect(STALL_BANNER_TTL_MS).toBe(24 * 60 * 60 * 1000);
  });
});
