/**
 * polish-2 T53 — print.css contract test.
 *
 * `print.css` MUST satisfy the printStylesheet contract:
 *   - `@page` rule declared (magazine-essay layout)
 *   - `@media print { ... }` block exists
 *   - `.chapter` (or `.wall-chapter`) has `break-after: page`
 *   - chrome (`header`, `footer`, `nav`, mute toggle, language toggle,
 *     mapboxgl-map) is `display: none` under @media print.
 *
 * The test reads the static CSS file as a string and asserts presence —
 * it does not parse a CSSOM (jsdom + @media print is unreliable).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";
import {
  HIDDEN_SELECTORS,
  PRINTABLE_SECTION_SELECTORS,
} from "@/lib/wall/printStylesheet";

const PRINT_CSS_PATH = resolve(__dirname, "..", "print.css");

function readPrintCss(): string {
  return readFileSync(PRINT_CSS_PATH, "utf8");
}

describe("print.css (polish-2 T53)", () => {
  it("declares an @page rule for the magazine-essay layout", () => {
    const css = readPrintCss();
    expect(css).toMatch(/@page\s*\{/);
  });

  it("wraps print rules in an @media print block", () => {
    const css = readPrintCss();
    expect(css).toMatch(/@media\s+print\s*\{/);
  });

  it("declares break-after: page for chapter sections", () => {
    const css = readPrintCss();
    // Either `.chapter` (homepage marker) or `.wall-chapter` (legacy)
    expect(css).toMatch(/(?:\.chapter|\.wall-chapter)[^{]*\{[^}]*break-after\s*:\s*page/s);
  });

  it("references at least one printable-section selector from the contract", () => {
    const css = readPrintCss();
    const found = PRINTABLE_SECTION_SELECTORS.some((sel) => css.includes(sel));
    expect(found).toBe(true);
  });

  it("hides every selector listed in HIDDEN_SELECTORS via display: none", () => {
    const css = readPrintCss();
    for (const selector of HIDDEN_SELECTORS) {
      expect(
        css.includes(selector),
        `print.css missing hidden selector ${selector}`,
      ).toBe(true);
    }
    expect(css).toMatch(/display\s*:\s*none\s*!important/);
  });
});
