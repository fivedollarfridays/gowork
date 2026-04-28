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

  it("colors.css preserves existing :root HSL block byte-for-byte", () => {
    const colors = read(path.resolve(TOKENS_DIR, "colors.css"));
    expect(colors).toContain("--background: 60 20% 95%;");
    expect(colors).toContain("--foreground: 195 9% 19%;");
    expect(colors).toContain("--primary: 218 46% 20%;");
    expect(colors).toContain("--success: 152 39% 52%;");
  });

  it("colors.css preserves existing .dark override block", () => {
    const colors = read(path.resolve(TOKENS_DIR, "colors.css"));
    expect(colors).toMatch(/\.dark\s*\{/);
    expect(colors).toContain("--background: 195 9% 12%;");
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
    expect(layout).toContain("bg-background");
    expect(layout).toContain("text-foreground");
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

  it("globals.css drops to <=30 lines (thin shell only)", () => {
    const globals = read(path.resolve(FRONTEND_ROOT, "src/app/globals.css"));
    const lineCount = globals.split("\n").length;
    expect(lineCount).toBeLessThanOrEqual(30);
  });
});
