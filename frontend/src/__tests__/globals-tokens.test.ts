import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.7 — CSS architecture split: globals.css → tokens/* partials.
 *
 * The original 87-line globals.css must be split BEFORE any tokens are added.
 * Each partial gets its own concern. globals.css becomes a thin shell of
 * @tailwind directives + @import statements (T1.8).
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TOKENS_DIR = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens");

function read(p: string): string {
  return fs.readFileSync(p, "utf-8");
}

describe("T1.7 — globals.css token partials exist", () => {
  it("creates tokens/ directory under src/app/styles/", () => {
    expect(fs.existsSync(TOKENS_DIR)).toBe(true);
  });

  it.each([
    ["colors.css"],
    ["typography.css"],
    ["motion.css"],
    ["space.css"],
    ["layout.css"],
  ])("creates %s partial", (filename) => {
    const filePath = path.resolve(TOKENS_DIR, filename);
    expect(fs.existsSync(filePath)).toBe(true);
  });

  it("colors.css declares the canonical GoWork :root HSL palette (warm paper + cyan)", () => {
    const colors = read(path.resolve(TOKENS_DIR, "colors.css"));
    // Light theme = warm paper canvas + navy ink + cyan primary.
    expect(colors).toContain("--background: 43 26% 95%;");   // #F5F3EE warm paper
    expect(colors).toContain("--foreground: 225 44% 7%;");   // #0A0E1A navy ink
    expect(colors).toContain("--primary: 187 86% 53%;");     // #22D3EE cyan
    expect(colors).toContain("--success: 158 64% 52%;");     // #34D399 emerald
  });

  it("colors.css declares the canonical GoWork .dark override block", () => {
    const colors = read(path.resolve(TOKENS_DIR, "colors.css"));
    expect(colors).toMatch(/\.dark\s*\{/);
    expect(colors).toContain("--background: 225 44% 7%;");   // navy canvas in dark
  });

  it("layout.css preserves .text-balance utility (root scope post-8b04ae8)", () => {
    const layout = read(path.resolve(TOKENS_DIR, "layout.css"));
    expect(layout).toContain(".text-balance");
    expect(layout).toContain("text-wrap: balance");
  });

  it("layout.css preserves border + body base rules (root scope post-8b04ae8)", () => {
    const layout = read(path.resolve(TOKENS_DIR, "layout.css"));
    expect(layout).toContain("border-border");
    expect(layout).toContain("overscroll-behavior: none");
    // polish-2 swapped `bg-background` / `text-foreground` Tailwind classes for
    // direct `var(--bg-base)` / `var(--fg-primary)` so the body unconditionally
    // tracks the OKLCH theme canvas regardless of shadcn HSL inheritance.
    expect(layout).toContain("var(--bg-base)");
    expect(layout).toContain("var(--fg-primary)");
  });

  it("typography.css exists with placeholder header for T1.15-T1.17", () => {
    const typography = read(path.resolve(TOKENS_DIR, "typography.css"));
    expect(typography).toMatch(/W1 typography tokens/i);
  });

  it("motion.css exists with placeholder header for T1.19-T1.23", () => {
    const motion = read(path.resolve(TOKENS_DIR, "motion.css"));
    expect(motion).toMatch(/W1 motion tokens/i);
  });

  it("space.css exists with placeholder header (post-W1 population)", () => {
    const space = read(path.resolve(TOKENS_DIR, "space.css"));
    expect(space).toMatch(/W1 space tokens/i);
  });

  it("each partial is < 400 lines (arch budget headroom)", () => {
    for (const name of ["colors.css", "typography.css", "motion.css", "space.css", "layout.css"]) {
      const content = read(path.resolve(TOKENS_DIR, name));
      const lines = content.split("\n").length;
      expect(lines, `${name} line count`).toBeLessThan(400);
    }
  });

  it("globals.css drops to <=40 lines (thin shell; polish-2 added home-velocity.css + print.css imports)", () => {
    const globals = read(path.resolve(FRONTEND_ROOT, "src/app/globals.css"));
    const lineCount = globals.split("\n").length;
    expect(lineCount).toBeLessThanOrEqual(40);
  });
});
