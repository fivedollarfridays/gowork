/**
 * SiteFooter — polish-2 T8.
 *
 * Below the legal row, a marquee "GOWORK · GOWORK · GOWORK …" scrubs
 * opposite to the scroll velocity. 12rem scale, 12% opacity, masked
 * top/bottom.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

vi.mock("@/hooks/useScrollVelocity", () => ({
  useScrollVelocity: vi.fn(),
}));

import { useScrollVelocity } from "@/hooks/useScrollVelocity";
import { SiteFooter } from "../SiteFooter";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("SiteFooter — reverse-scroll wordmark (T8)", () => {
  beforeEach(() => {
    setLocale("en");
    vi.mocked(useScrollVelocity).mockReturnValue({ velocity: 0, isFast: false });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the wordmark row containing 'GOWORK' tokens", () => {
    const { container } = wrap(<SiteFooter />);
    const row = container.querySelector("[data-site-footer-wordmark]");
    expect(row).toBeTruthy();
    expect(row?.textContent).toMatch(/GOWORK/);
  });

  it("has at least three GOWORK tokens for the marquee illusion", () => {
    const { container } = wrap(<SiteFooter />);
    const row = container.querySelector("[data-site-footer-wordmark]");
    const tokens = (row?.textContent ?? "").match(/GOWORK/g) ?? [];
    expect(tokens.length).toBeGreaterThanOrEqual(3);
  });

  it("is hidden from assistive tech (aria-hidden)", () => {
    const { container } = wrap(<SiteFooter />);
    const row = container.querySelector("[data-site-footer-wordmark]");
    expect(row?.getAttribute("aria-hidden")).toBe("true");
  });
});
