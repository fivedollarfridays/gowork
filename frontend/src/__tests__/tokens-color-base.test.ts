import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.10 — OKLCH base palette tokens.
 *
 * Adds 7 base canvas tokens (LOCKED from docs/visual-rebirth-plan.md):
 *   --bg-base, --bg-surface, --bg-elevated, --bg-glass,
 *   --fg-primary, --fg-secondary, --fg-muted
 *
 * Hex defaults guaranteed; OKLCH overrides via @supports for P3-capable browsers.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const COLORS_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/colors.css");

function read(): string {
  return fs.readFileSync(COLORS_CSS, "utf-8");
}

describe("T1.10 — OKLCH base palette tokens", () => {
  const css = read();

  it.each([
    ["--bg-base", "#0A0E1A"],
    ["--bg-surface", "#0F1729"],
    ["--bg-elevated", "#1A2338"],
    ["--fg-primary", "#F5F3EE"],
    // Spotlight: --fg-secondary lifted from plan's #94A3B8 → #A4B3C7 to
    // clear AAA-normal on bg-elevated. Plan ratio was 6.11; new = 7.34.
    ["--fg-secondary", "#A4B3C7"],
    // Spotlight: --fg-muted lifted from plan's #64748B → #8696A8 to clear
    // AAA-large on bg-elevated. Plan ratio was 3.29; new = 5.17.
    ["--fg-muted", "#8696A8"],
  ])("defines %s with hex default %s", (token, hex) => {
    // Token must appear with its plan-locked hex default before any @supports block.
    const re = new RegExp(`${token}\\s*:\\s*${hex}`, "i");
    expect(css).toMatch(re);
  });

  it("defines --bg-glass with rgba glass effect", () => {
    expect(css).toMatch(/--bg-glass:\s*rgba\(255,\s*255,\s*255,\s*0\.04\)/);
  });

  it("provides @supports OKLCH override block for P3-capable browsers", () => {
    expect(css).toMatch(/@supports\s*\(color:\s*oklch\(/);
  });

  it("@supports OKLCH block re-declares all 7 base tokens", () => {
    // Extract @supports (color: oklch(...)) block and assert each token appears inside.
    const supportsMatch = css.match(/@supports\s*\(color:\s*oklch\([^}]*\}\s*\}/s);
    expect(supportsMatch, "@supports oklch block must exist").not.toBeNull();
    const block = supportsMatch![0];
    for (const token of [
      "--bg-base",
      "--bg-surface",
      "--bg-elevated",
      "--bg-glass",
      "--fg-primary",
      "--fg-secondary",
      "--fg-muted",
    ]) {
      expect(block, `@supports block missing ${token}`).toContain(token);
    }
  });

  it("preserves legacy HSL --background token (back-compat)", () => {
    expect(css).toContain("--background: 60 20% 95%;");
  });

  it("colors.css line count <300 (architecture budget; T1.11 + T1.12 grow this)", () => {
    // T1.10 AC said <100 pre-T1.11, but T1.11 (accents + 15 shade variants
    // + @supports-not fallback block) legitimately grows the file. The
    // architecture limit (<400) and T1.11's own <200 AC bound the overall
    // ceiling. We assert <300 here as a comfortable shared budget.
    const lines = css.split("\n").length;
    expect(lines).toBeLessThan(300);
  });
});
