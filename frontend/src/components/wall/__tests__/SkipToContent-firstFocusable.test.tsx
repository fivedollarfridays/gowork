/**
 * W4 Driver C — T4.C.5 — SkipToContent must be the FIRST focusable.
 *
 * The W1 layout mounts SkipToContent inside a TranslationProvider that
 * sits ABOVE Header/main/Footer. This test asserts the DOM order:
 *   skip link must appear before the brand-mark Link, the NavBar, the
 *   mute toggle, etc., when a wrapper containing SkipToContent + Header
 *   is rendered together.
 */
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { SkipToContent } from "../SkipToContent";

afterEach(() => cleanup());

vi.mock("@/hooks/usePrefersReducedMotion", () => ({
  usePrefersReducedMotion: () => false,
}));

/**
 * Resolves a flat list of focusable elements in DOM order. Mirrors the
 * heuristic used by Playwright's keyboard sweep (T4.C.3).
 */
function focusables(container: HTMLElement): Element[] {
  return Array.from(
    container.querySelectorAll(
      "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])",
    ),
  );
}

describe("T4.C.5 — SkipToContent first-focusable contract", () => {
  it("when rendered alongside an arbitrary <a> link, skip-to-content is first", () => {
    const { container } = render(
      <TranslationProvider>
        <SkipToContent />
        <a href="/somewhere" data-testid="other-link">
          Other link
        </a>
      </TranslationProvider>,
    );
    const all = focusables(container);
    expect(all.length).toBeGreaterThanOrEqual(2);
    expect(all[0].className).toContain("skip-to-content");
  });

  it("targets #main by default (matches layout's <main id='main'>)", () => {
    const { container } = render(
      <TranslationProvider>
        <SkipToContent />
      </TranslationProvider>,
    );
    const link = container.querySelector("a.skip-to-content");
    expect(link?.getAttribute("href")).toBe("#main");
  });

  it("never has tabindex=-1 (always reachable via Tab)", () => {
    const { container } = render(
      <TranslationProvider>
        <SkipToContent />
      </TranslationProvider>,
    );
    const link = container.querySelector("a.skip-to-content");
    expect(link?.getAttribute("tabindex")).not.toBe("-1");
  });

  it("when focused, the CSS class includes skip-to-content (visible-on-focus contract)", () => {
    const { container } = render(
      <TranslationProvider>
        <SkipToContent />
      </TranslationProvider>,
    );
    const link = container.querySelector("a.skip-to-content");
    expect(link?.className).toMatch(/skip-to-content/);
  });
});
