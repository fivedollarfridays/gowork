import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.106 — Branded custom scrollbar CSS.
 *
 * Default OS scrollbar is the loudest "this is a webpage" signal. Custom
 * scrollbar carries brand into the chrome. Webkit + Firefox both covered.
 * Older browsers fall back gracefully (vendor prefixes are no-ops, not errors).
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const LAYOUT_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/layout.css");

function read(): string {
  return fs.readFileSync(LAYOUT_CSS, "utf-8");
}

describe("T1.106 — webkit-scrollbar selectors", () => {
  const css = read();

  it.each([
    ["::-webkit-scrollbar"],
    ["::-webkit-scrollbar-track"],
    ["::-webkit-scrollbar-thumb"],
    ["::-webkit-scrollbar-thumb:hover"],
  ])("declares %s", (selector) => {
    expect(css).toContain(selector);
  });

  it("scrollbar uses --bg-surface for the track", () => {
    expect(css).toMatch(/::-webkit-scrollbar-track[\s\S]*?\{[\s\S]*?var\(--bg-surface\)/);
  });

  it("scrollbar thumb uses color-mix() with --accent-cyan", () => {
    expect(css).toMatch(/::-webkit-scrollbar-thumb\s*\{[\s\S]*?color-mix\([\s\S]*?--accent-cyan/);
  });
});

describe("T1.106 — Firefox scrollbar-color", () => {
  const css = read();

  it("html declares scrollbar-color with cyan-on-surface", () => {
    expect(css).toMatch(/html[\s\S]*scrollbar-color:\s*var\(--accent-cyan\)\s*var\(--bg-surface\)/);
  });

  it("html declares scrollbar-width: thin", () => {
    expect(css).toMatch(/html[\s\S]*scrollbar-width:\s*thin/);
  });
});
