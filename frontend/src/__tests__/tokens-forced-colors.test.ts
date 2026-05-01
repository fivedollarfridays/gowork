import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.96 — Forced Colors Mode (Windows High Contrast) adaptations.
 * T1.97 — prefers-contrast: more variant tokens.
 *
 * forced-colors.css is a NEW partial @import-wired by globals.css.
 * It maps brand tokens to system colors so HCM users still see the Wall
 * as functional infrastructure rather than broken CSS.
 *
 * prefers-contrast: more lives inside colors.css (token override block)
 * because it's a contrast variant, not a new color system.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TOKENS_DIR = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens");
const GLOBALS_CSS = path.resolve(FRONTEND_ROOT, "src/app/globals.css");

function readPartial(name: string): string {
  return fs.readFileSync(path.resolve(TOKENS_DIR, name), "utf-8");
}

describe("T1.96 — Forced Colors Mode partial", () => {
  it("forced-colors.css partial exists", () => {
    expect(fs.existsSync(path.resolve(TOKENS_DIR, "forced-colors.css"))).toBe(true);
  });

  it("contains @media (forced-colors: active) block", () => {
    const css = readPartial("forced-colors.css");
    expect(css).toMatch(/@media\s*\(forced-colors:\s*active\)/);
  });

  it("maps --accent-cyan to LinkText system color", () => {
    const css = readPartial("forced-colors.css");
    expect(css).toMatch(/--accent-cyan:\s*LinkText/i);
  });

  it("maps --bg-base to Canvas + --fg-primary to CanvasText", () => {
    const css = readPartial("forced-colors.css");
    expect(css).toMatch(/--bg-base:\s*Canvas\b/i);
    expect(css).toMatch(/--fg-primary:\s*CanvasText/i);
  });

  it("focus ring uses Highlight system color in forced-colors mode", () => {
    const css = readPartial("forced-colors.css");
    expect(css).toMatch(/:focus-visible[\s\S]*outline:[^;]*Highlight/);
  });

  it("partial <80 lines (architecture budget)", () => {
    const lines = readPartial("forced-colors.css").split("\n").length;
    expect(lines).toBeLessThan(80);
  });
});

describe("T1.96 — globals.css imports forced-colors.css", () => {
  it("globals.css @imports the new partial", () => {
    const globals = fs.readFileSync(GLOBALS_CSS, "utf-8");
    expect(globals).toMatch(/@import\s+["']\.\/styles\/tokens\/forced-colors\.css["']/);
  });
});

describe("T1.97 — prefers-contrast: more in colors.css", () => {
  const css = readPartial("colors.css");

  it("@media (prefers-contrast: more) block exists", () => {
    expect(css).toMatch(/@media\s*\(prefers-contrast:\s*more\)/);
  });

  // Helper: extract the @media (prefers-contrast: more) block by matching
  // the outer brace pair (one level of nesting for :root inside).
  function extractContrastBlock(source: string): string {
    const start = source.indexOf("@media (prefers-contrast: more)");
    if (start === -1) return "";
    let depth = 0;
    let i = source.indexOf("{", start);
    const begin = i;
    while (i < source.length) {
      const ch = source[i];
      if (ch === "{") depth++;
      else if (ch === "}") {
        depth--;
        if (depth === 0) return source.slice(begin, i + 1);
      }
      i++;
    }
    return "";
  }

  it("lifts --fg-muted to a brighter shade for high-contrast users", () => {
    const block = extractContrastBlock(css);
    expect(block.length).toBeGreaterThan(0);
    expect(block).toMatch(/--fg-muted:\s*#/);
  });

  it("brightens --accent-cyan for prefers-contrast: more", () => {
    const block = extractContrastBlock(css);
    expect(block).toMatch(/--accent-cyan:\s*#/);
  });
});

describe("T1.97 — colors.css size budget after T1.97", () => {
  it("colors.css <340 lines (bumped 2026-05-01 for demo-grade dark-mode `.text-secondary` cyan override + commentary)", () => {
    const lines = readPartial("colors.css").split("\n").length;
    expect(lines).toBeLessThan(340);
  });
});
