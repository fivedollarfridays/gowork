/**
 * W1 Driver C — CookieBanner (Wave 7 enrichment).
 *
 * The dispatch is honest : this site does NOT track. A traditional
 * EU/CCPA cookie banner would be performative. Instead, we surface a
 * minimal first-visit disclosure that says, in one sentence, what we
 * actually store (locale + mute preference in localStorage). The user
 * dismisses; we remember the dismissal.
 *
 * The banner is dismissible and persists the dismissal so the user
 * never sees it twice. localStorage key : `gowork-disclosure-dismissed`.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  CookieBanner,
  COOKIE_DISCLOSURE_STORAGE_KEY,
} from "../CookieBanner";

describe("CookieBanner (cookieless honest disclosure)", () => {
  beforeEach(() => {
    localStorage.removeItem(COOKIE_DISCLOSURE_STORAGE_KEY);
  });

  it("renders the disclosure text on first mount", () => {
    render(<CookieBanner />);
    expect(screen.getByText(/we do not track/i)).toBeInTheDocument();
  });

  it("does NOT render when localStorage flag is set", () => {
    localStorage.setItem(COOKIE_DISCLOSURE_STORAGE_KEY, "true");
    const { container } = render(<CookieBanner />);
    expect(container.textContent ?? "").toBe("");
  });

  it("dismisses and persists the dismissal", () => {
    const { container } = render(<CookieBanner />);
    fireEvent.click(screen.getByRole("button", { name: /got it|dismiss/i }));
    expect(container.textContent ?? "").toBe("");
    expect(localStorage.getItem(COOKIE_DISCLOSURE_STORAGE_KEY)).toBe("true");
  });

  it("declares role=region for landmark navigation", () => {
    render(<CookieBanner />);
    const region = screen.getByRole("region");
    expect(region).toHaveAttribute("aria-label");
  });
});
