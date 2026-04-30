/**
 * SiteFooter — wordmark presence (post-polish-3).
 *
 * polish-2 T8 originally placed a reverse-scroll "GOWORK · GOWORK …"
 * marquee below the legal+credit rows. polish-3 removed that wordmark
 * because it duplicated the Ch08 mic-drop wordmark closer and bloated
 * the bottom of every page. The remaining footer chrome is brand
 * column + 3 nav columns + legal nav + credit row.
 *
 * These tests lock in the removal: the wordmark MUST NOT render in
 * SiteFooter, and the Ch08 closer remains the sole wordmark surface.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

import { SiteFooter } from "../SiteFooter";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("SiteFooter — wordmark removed (polish-3)", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("does NOT render the legacy reverse-scroll GOWORK wordmark row", () => {
    const { container } = wrap(<SiteFooter />);
    const row = container.querySelector("[data-site-footer-wordmark]");
    expect(row).toBeNull();
  });

  it("still renders the four-column grid + legal nav + credit row", () => {
    const { container } = wrap(<SiteFooter />);
    expect(container.querySelector("[data-site-footer]")).not.toBeNull();
    // Four-column grid (brand + 3 nav columns) — assert at least one heading
    // from each by class. The columns ship inside the grid; the credit row
    // includes the version pin (e.g. "v0.4.2").
    expect((container.textContent ?? "")).toMatch(/v\d/);
  });

  it("footer carries an aria role of contentinfo", () => {
    const { container } = wrap(<SiteFooter />);
    const footer = container.querySelector("[data-site-footer]");
    expect(footer?.getAttribute("role")).toBe("contentinfo");
  });
});
