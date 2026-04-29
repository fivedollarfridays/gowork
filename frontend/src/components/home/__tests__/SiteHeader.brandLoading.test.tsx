/**
 * SiteHeader — polish-2 T7.
 *
 * Until first non-zero scroll, BrandMark renders with the loading prop
 * (data-brand-mark[data-loading="true"]). After first scroll the loading
 * affordance disappears.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
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

describe("SiteHeader — brand-mark loading affordance (T7)", () => {
  let rafCb: FrameRequestCallback | null = null;

  beforeEach(() => {
    setLocale("en");
    setScrollY(0);
    rafCb = null;
    vi.stubGlobal(
      "requestAnimationFrame",
      ((cb: FrameRequestCallback) => {
        rafCb = cb;
        return 1 as unknown as number;
      }) as typeof requestAnimationFrame,
    );
    vi.stubGlobal("cancelAnimationFrame", (() => {}) as typeof cancelAnimationFrame);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the brand mark wrapper with data-loading=true on initial paint", () => {
    const { container } = render(
      <TranslationProvider>
        <SiteHeader />
      </TranslationProvider>,
    );
    const wrapper = container.querySelector("[data-brand-mark]");
    expect(wrapper).toBeTruthy();
    expect(wrapper?.getAttribute("data-loading")).toBe("true");
  });

  it("flips data-loading to false after the first non-zero scroll", () => {
    const { container } = render(
      <TranslationProvider>
        <SiteHeader />
      </TranslationProvider>,
    );
    setScrollY(50);
    act(() => {
      window.dispatchEvent(new Event("scroll"));
      if (rafCb) {
        const cb = rafCb;
        rafCb = null;
        cb(performance.now());
      }
    });
    const wrapper = container.querySelector("[data-brand-mark]");
    expect(wrapper?.getAttribute("data-loading")).toBe("false");
  });
});
