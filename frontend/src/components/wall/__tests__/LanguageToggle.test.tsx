/**
 * W1 Driver C — T1.54 LanguageToggle.
 *
 * EN / ES toggle that persists via the existing `setLocale` lib helper
 * (which already writes to localStorage under `montgowork-locale` for
 * legacy compatibility — Driver B may upgrade the key in W2). Updates
 * `<html lang="">` so screen readers and CSS :lang() selectors stay in
 * sync with the active locale.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { LanguageToggle } from "../LanguageToggle";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("LanguageToggle (T1.54)", () => {
  beforeEach(() => {
    setLocale("en");
    document.documentElement.lang = "en";
  });

  it("renders both EN and ES choices", () => {
    wrap(<LanguageToggle />);
    expect(screen.getByRole("button", { name: /^en$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^es$/i })).toBeInTheDocument();
  });

  it("highlights the active locale via aria-pressed", () => {
    wrap(<LanguageToggle />);
    const en = screen.getByRole("button", { name: /^en$/i });
    const es = screen.getByRole("button", { name: /^es$/i });
    expect(en).toHaveAttribute("aria-pressed", "true");
    expect(es).toHaveAttribute("aria-pressed", "false");
  });

  it("switches locale when ES is clicked and updates <html lang>", () => {
    wrap(<LanguageToggle />);
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    expect(document.documentElement.lang).toBe("es");
  });

  it("declares aria-label on the group from i18n", () => {
    wrap(<LanguageToggle />);
    const group = screen.getByRole("group");
    expect(group).toHaveAttribute("aria-label");
  });
});
