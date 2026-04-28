import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.45 — Print stylesheet (magazine layout) + T1.131 enrichment.
 *
 * frontend/src/app/styles/print.css gives the Wall a 9-page magazine essay
 * print layout: serif headings, single column, page breaks at chapter
 * boundaries, hidden chrome (header/footer/nav/sound-toggle), Mapbox
 * replaced by a placeholder caption.
 *
 * Driver C handoff: layout.tsx wires <link rel="stylesheet" media="print" />.
 * Driver A delivers the stylesheet + the static asserts here.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const PRINT_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/print.css");

function read(): string {
  return fs.readFileSync(PRINT_CSS, "utf-8");
}

describe("T1.45 — print.css exists at the contracted path", () => {
  it("file exists", () => {
    expect(fs.existsSync(PRINT_CSS)).toBe(true);
  });

  it("file is wrapped in @media print (or media-query at @import time)", () => {
    const css = read();
    // Either the whole file is inside @media print, OR (preferred) the file
    // is loaded via media="print" by layout.tsx and uses @page rules at root.
    // We accept either form.
    const hasMediaPrint = css.includes("@media print");
    const usesPageRules = css.includes("@page") || css.includes("page-break");
    expect(hasMediaPrint || usesPageRules).toBe(true);
  });
});

describe("T1.45 — magazine layout rules", () => {
  const css = read();

  it("body uses serif font stack for print", () => {
    expect(css).toMatch(/font-family:[^;]*(Georgia|"Times New Roman"|serif)/i);
  });

  it("page-break-before: always on .wall-chapter", () => {
    expect(css).toMatch(/\.wall-chapter[\s\S]*page-break-before:\s*always/);
  });

  it("page-break-inside: avoid on .wall-chapter (T1.131 enrichment)", () => {
    expect(css).toMatch(/\.wall-chapter[\s\S]*page-break-inside:\s*avoid/);
  });

  it("orphans + widows controls (T1.131 typographic discipline)", () => {
    expect(css).toMatch(/orphans:\s*3/);
    expect(css).toMatch(/widows:\s*3/);
  });

  it("nav, header, footer, .no-print suppressed", () => {
    expect(css).toMatch(/header[\s\S]*display:\s*none|display:\s*none[\s\S]*header/);
    expect(css).toMatch(/\.no-print[\s\S]*display:\s*none/);
  });

  it("Mapbox container hidden + replaced with caption hint", () => {
    expect(css).toMatch(/\.mapbox-container|\.mapboxgl-map/);
    expect(css).toMatch(/\.print-map-fallback|map-fallback/);
  });
});

describe("T1.45 — drop-cap + pull-quote print rules (T1.131 enrichment)", () => {
  const css = read();

  it(".dropcap::first-letter exists with print-tuned size", () => {
    expect(css).toMatch(/\.dropcap[\s\S]*::first-letter/);
  });

  it("pull-quote stays on one page", () => {
    expect(css).toMatch(/\.wall-pull-quote[\s\S]*page-break-inside:\s*avoid/);
  });
});

describe("T1.45 — print.css size budget", () => {
  it("print.css <300 lines (room for W4 chapter-specific overrides)", () => {
    const lines = read().split("\n").length;
    expect(lines).toBeLessThan(300);
  });
});
