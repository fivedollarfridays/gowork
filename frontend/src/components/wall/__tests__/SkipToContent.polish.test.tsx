/**
 * SkipToContent — polish-2 T6.
 *
 * Cyan pill, 10/16px padding. Slides from translateY(-200%) → translateY(0)
 * on focus in 200ms. Honors data-theme="light" (navy text on cyan).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SkipToContent } from "../SkipToContent";

function renderSkip() {
  return render(
    <TranslationProvider>
      <SkipToContent />
    </TranslationProvider>,
  );
}

describe("SkipToContent — polish-2 T6 styling", () => {
  beforeEach(() => {
    setLocale("en");
    document.documentElement.removeAttribute("data-theme");
  });

  it("starts with translateY(-200%) at rest (not focused)", () => {
    renderSkip();
    const link = screen.getByRole("link", { name: /skip to main content/i });
    expect(link.style.transform).toBe("translateY(-200%)");
  });

  it("flips transform to translateY(0) when focused", () => {
    renderSkip();
    const link = screen.getByRole("link", {
      name: /skip to main content/i,
    }) as HTMLAnchorElement;
    act(() => {
      link.focus();
    });
    expect(link.style.transform).toBe("translateY(0)");
  });

  it("applies the cyan pill background via inline var(--accent-cyan)", () => {
    renderSkip();
    const link = screen.getByRole("link", { name: /skip to main content/i });
    // We allow either fully-resolved tokens or the var() reference.
    expect(link.style.background).toMatch(/var\(--accent-cyan\)/);
  });

  it("uses 10/16px padding per spec", () => {
    renderSkip();
    const link = screen.getByRole("link", {
      name: /skip to main content/i,
    }) as HTMLAnchorElement;
    expect(link.style.padding).toBe("10px 16px");
  });

  it("honors data-theme='light' by setting navy text color", () => {
    document.documentElement.setAttribute("data-theme", "light");
    renderSkip();
    const link = screen.getByRole("link", {
      name: /skip to main content/i,
    }) as HTMLAnchorElement;
    // Light theme color should resolve to var(--bg-base) (the navy paper-dark).
    expect(link.style.color).toMatch(/var\(--bg-base\)/);
  });
});
