/**
 * Spotlight invention #5 (W4 Driver D) — printStylesheet.test.ts.
 *
 * `lib/wall/printStylesheet` is the printability contract module: it
 * declares which selectors MUST page-break and which MUST hide on print.
 * The print.css cascade is checked against this contract here.
 *
 * Why this guards: a future driver could rename a chapter's
 * `data-chapter-id` to something else and the print stylesheet would
 * silently fall through. This test catches the drift.
 *
 * The contract additionally drives Spotlight #5 — `assertPrintableTree`,
 * a tiny pure helper that walks an arbitrary root element and verifies
 * every chapter section is reachable via at least one printable selector.
 */

import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";
import {
  PRINTABLE_SECTION_SELECTORS,
  HIDDEN_SELECTORS,
  assertPrintableTree,
} from "../printStylesheet";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..", "..");
const PRINT_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/print.css");

function readPrintCss(): string {
  return fs.readFileSync(PRINT_CSS, "utf-8");
}

describe("Spotlight #5 — printStylesheet contract module", () => {
  it("PRINTABLE_SECTION_SELECTORS includes the canonical chapter selectors", () => {
    expect(PRINTABLE_SECTION_SELECTORS).toContain(".wall-chapter");
    expect(PRINTABLE_SECTION_SELECTORS).toContain("section[data-chapter-id]");
  });

  it("HIDDEN_SELECTORS hides Mapbox, header, footer, language toggle", () => {
    expect(HIDDEN_SELECTORS).toContain(".mapboxgl-map");
    expect(HIDDEN_SELECTORS).toContain("header");
    expect(HIDDEN_SELECTORS).toContain("footer");
    expect(HIDDEN_SELECTORS).toContain(".language-toggle");
  });

  it("every PRINTABLE_SECTION_SELECTORS entry appears in print.css", () => {
    const css = readPrintCss();
    for (const selector of PRINTABLE_SECTION_SELECTORS) {
      // Selectors with regex specials must be escaped for the .includes check.
      expect(css).toContain(selector);
    }
  });

  it("every HIDDEN_SELECTORS entry appears in print.css", () => {
    const css = readPrintCss();
    for (const selector of HIDDEN_SELECTORS) {
      expect(css).toContain(selector);
    }
  });
});

describe("Spotlight #5 — assertPrintableTree (chapter-tree walker)", () => {
  it("returns true when a tree contains a printable chapter section", () => {
    const root = document.createElement("div");
    const section = document.createElement("section");
    section.setAttribute("data-chapter-id", "continental");
    root.appendChild(section);
    expect(assertPrintableTree(root)).toBe(true);
  });

  it("returns true when a tree uses the .wall-chapter class", () => {
    const root = document.createElement("div");
    const section = document.createElement("section");
    section.className = "wall-chapter";
    root.appendChild(section);
    expect(assertPrintableTree(root)).toBe(true);
  });

  it("returns false when a tree has no printable sections", () => {
    const root = document.createElement("div");
    const section = document.createElement("div");
    section.textContent = "no chapter id";
    root.appendChild(section);
    expect(assertPrintableTree(root)).toBe(false);
  });

  it("returns true when at least ONE chapter section is reachable (any pathway)", () => {
    const root = document.createElement("div");
    const fluff = document.createElement("div");
    root.appendChild(fluff);
    const section = document.createElement("section");
    section.setAttribute("data-chapter-id", "any");
    root.appendChild(section);
    expect(assertPrintableTree(root)).toBe(true);
  });
});
