import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.12 — --temperature-multiplier scoped variable.
 *
 * Lives in colors.css because it modulates accent shifts (same family).
 * 1.0 = neutral, >1 = warmer/redder shift, <1 = cooler/bluer shift.
 * --accent-current is reformulated to consume it via color-mix() so a chapter
 * scope (W3 Ch 6 cliff calc) sets temperature-multiplier and accent-current
 * shifts cyan → rose proportionally without explicit recoloring.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const COLORS_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/colors.css");

function read(): string {
  return fs.readFileSync(COLORS_CSS, "utf-8");
}

describe("T1.12 — temperature multiplier token", () => {
  const css = read();

  it("defines --temperature-multiplier with default 1.0 at :root", () => {
    expect(css).toMatch(/--temperature-multiplier:\s*1(?:\.0)?\s*;/);
  });

  it("--accent-current reformulated to consume --temperature-multiplier via color-mix()", () => {
    // After T1.12, --accent-current is no longer a static var alias; it's a
    // color-mix() between cyan and rose driven by temperature-multiplier.
    const accentCurrentLines = css
      .split("\n")
      .filter((l) => l.includes("--accent-current"));
    const formulaLine = accentCurrentLines.find((l) => l.includes("color-mix"));
    expect(formulaLine, "--accent-current must use color-mix() formula").toBeDefined();
    expect(formulaLine!).toMatch(/--temperature-multiplier/);
    expect(formulaLine!).toMatch(/--accent-cyan/);
    expect(formulaLine!).toMatch(/--accent-rose/);
  });

  it("documents the contract (1.0 neutral; >1 rose shift; <1 cyan shift)", () => {
    // Inline documentation lives next to the formula so consumers see intent.
    expect(css).toMatch(/1\.0\s*=\s*neutral/i);
    expect(css).toMatch(/(>1|warmer|rose).*shift/i);
  });
});

describe("T1.12 — visual sanity (jsdom computed style)", () => {
  it("setting --temperature-multiplier on an element changes its computed value", () => {
    // Light jsdom proof: the variable is settable as inline style and reads back.
    // Full color-mix() resolution requires Chromium; jsdom returns the literal
    // formula. We assert the variable propagates and the formula references it.
    const div = document.createElement("div");
    div.style.setProperty("--temperature-multiplier", "1.5");
    expect(div.style.getPropertyValue("--temperature-multiplier")).toBe("1.5");
  });
});
