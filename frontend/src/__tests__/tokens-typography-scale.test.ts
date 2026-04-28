import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.16 — Fluid type scale tokens.
 *
 * 6 fluid type sizes via clamp() + 3 tracking/leading helpers. Plan-locked
 * formulas straight from docs/visual-rebirth-plan.md "Design system → Type".
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TYPOGRAPHY_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/typography.css");

function read(): string {
  return fs.readFileSync(TYPOGRAPHY_CSS, "utf-8");
}

describe("T1.16 — fluid type scale tokens", () => {
  const css = read();

  it.each([
    ["--type-display", "6.5rem"],
    ["--type-h1", "4rem"],
    ["--type-h2", "2.5rem"],
    ["--type-h3", "1.75rem"],
    ["--type-body", "1.25rem"],
    ["--type-small", "1rem"],
  ])("defines %s with clamp() max %s", (token, max) => {
    // Each token must use clamp() and end with the plan-locked max.
    // Match: --type-display: clamp(<min>, <pref>, 6.5rem);
    const re = new RegExp(`${token}\\s*:\\s*clamp\\([^)]*${max.replace(".", "\\.")}\\s*\\)`);
    expect(css).toMatch(re);
  });

  it("defines tracking + leading helpers", () => {
    expect(css).toMatch(/--type-tight-tracking\s*:\s*-0\.04em/);
    expect(css).toMatch(/--type-body-tracking\s*:\s*-0\.01em/);
    expect(css).toMatch(/--type-leading-loose\s*:\s*1\.7/);
  });

  it("--type-display formula yields 6.5rem at >=1920px viewport math", () => {
    // Sanity check the clamp formula text. Plan: clamp(3rem, 2rem + 5vw, 6.5rem)
    // At 1920px, 5vw = 96px ≈ 6rem (16px base) → 2rem + 6rem = 8rem, clamped at 6.5rem max.
    const m = css.match(/--type-display\s*:\s*clamp\(([^)]+)\)/);
    expect(m).not.toBeNull();
    const args = m![1].split(",").map((s) => s.trim());
    expect(args[0]).toBe("3rem");
    expect(args[2]).toBe("6.5rem");
  });

  it("--type-display floor stays >= 3rem at 320px viewport (no overflow)", () => {
    // 320px → 5vw = 16px = 1rem; 2rem + 1rem = 3rem (the floor). Test asserts
    // the formula's first arg matches that floor.
    const m = css.match(/--type-display\s*:\s*clamp\(([^)]+)\)/);
    const floor = m![1].split(",")[0].trim();
    expect(floor).toBe("3rem");
  });
});
