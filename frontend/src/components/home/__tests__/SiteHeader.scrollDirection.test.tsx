/**
 * SiteHeader — polish-2 T2.
 *
 * On scroll-down past 80px, header collapses (data-header-state="hidden");
 * on scroll-up restore (data-header-state="visible").
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SiteHeader } from "../SiteHeader";

function setScrollY(y: number): void {
  Object.defineProperty(window, "scrollY", {
    value: y,
    writable: true,
    configurable: true,
  });
}

function fireScroll(rafCb: { current: FrameRequestCallback | null }): void {
  act(() => {
    window.dispatchEvent(new Event("scroll"));
    if (rafCb.current) {
      const cb = rafCb.current;
      rafCb.current = null;
      cb(performance.now());
    }
  });
}

describe("SiteHeader — scroll-direction hide/show (T2)", () => {
  const rafRef: { current: FrameRequestCallback | null } = { current: null };

  beforeEach(() => {
    setLocale("en");
    setScrollY(0);
    rafRef.current = null;
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => {
        rafRef.current = cb;
        return 1 as unknown as number;
      }) as typeof requestAnimationFrame,
    );
    vi.stubGlobal("cancelAnimationFrame", (() => {}) as typeof cancelAnimationFrame);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts in 'visible' state at scrollY=0", () => {
    const { container } = render(
      <TranslationProvider>
        <SiteHeader />
      </TranslationProvider>,
    );
    const header = container.querySelector("[data-site-header]");
    expect(header).toBeTruthy();
    expect(header?.getAttribute("data-header-state")).toBe("visible");
  });

  it("flips to 'hidden' after scrolling down past 80px", () => {
    const { container } = render(
      <TranslationProvider>
        <SiteHeader />
      </TranslationProvider>,
    );
    setScrollY(100);
    fireScroll(rafRef);
    setScrollY(200);
    fireScroll(rafRef);
    const header = container.querySelector("[data-site-header]");
    expect(header?.getAttribute("data-header-state")).toBe("hidden");
  });

  it("flips back to 'visible' on scroll-up", () => {
    const { container } = render(
      <TranslationProvider>
        <SiteHeader />
      </TranslationProvider>,
    );
    setScrollY(100);
    fireScroll(rafRef);
    setScrollY(200);
    fireScroll(rafRef);
    setScrollY(150);
    fireScroll(rafRef);
    const header = container.querySelector("[data-site-header]");
    expect(header?.getAttribute("data-header-state")).toBe("visible");
  });
});
