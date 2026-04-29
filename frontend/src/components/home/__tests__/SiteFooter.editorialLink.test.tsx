/**
 * SiteFooter — polish-2 T5 / T8.
 *
 * In-prose anchors carry the `.editorial-link` class for the gradient
 * underline reveal. Footer also includes the reverse-scroll wordmark row.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SiteFooter } from "../SiteFooter";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("SiteFooter — editorial-link class (T5)", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("applies the editorial-link class to all in-prose footer anchors", () => {
    const { container } = wrap(<SiteFooter />);
    const links = container.querySelectorAll("a");
    expect(links.length).toBeGreaterThan(5);
    for (const link of Array.from(links)) {
      // Every footer-link anchor must also be an editorial-link.
      if (link.classList.contains("footer-link")) {
        expect(link.classList.contains("editorial-link")).toBe(true);
      }
    }
  });
});
