import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.13 — Token snapshot lock.
 *
 * Locks the exhaustive list of color token NAMES (not values) so that any
 * future PR removing or renaming a token causes a deliberate test failure.
 * Values can drift; names are the contract surface.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const COLORS_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/colors.css");

function read(): string {
  return fs.readFileSync(COLORS_CSS, "utf-8");
}

/** Extracts all unique --custom-prop names from the CSS file. */
function extractTokenNames(css: string): string[] {
  const seen = new Set<string>();
  const re = /(--[a-z][a-z0-9-]*)\s*:/g;
  for (const m of css.matchAll(re)) {
    seen.add(m[1]);
  }
  return [...seen].sort();
}

describe("T1.13 — color token name snapshot lock", () => {
  it("locks the exhaustive list of color token names", () => {
    const names = extractTokenNames(read());
    expect(names).toMatchInlineSnapshot(`
      [
        "--accent",
        "--accent-amber",
        "--accent-amber-100",
        "--accent-amber-300",
        "--accent-amber-500",
        "--accent-amber-700",
        "--accent-amber-900",
        "--accent-current",
        "--accent-cyan",
        "--accent-cyan-100",
        "--accent-cyan-300",
        "--accent-cyan-500",
        "--accent-cyan-700",
        "--accent-cyan-900",
        "--accent-foreground",
        "--accent-rose",
        "--accent-rose-100",
        "--accent-rose-300",
        "--accent-rose-500",
        "--accent-rose-700",
        "--accent-rose-900",
        "--background",
        "--bg-base",
        "--bg-elevated",
        "--bg-glass",
        "--bg-surface",
        "--border",
        "--card",
        "--card-foreground",
        "--chart-1",
        "--chart-2",
        "--chart-3",
        "--chart-4",
        "--chart-5",
        "--chrome-accent",
        "--destructive",
        "--destructive-foreground",
        "--drop-cap-color",
        "--fg-muted",
        "--fg-primary",
        "--fg-secondary",
        "--foreground",
        "--input",
        "--muted",
        "--muted-foreground",
        "--popover",
        "--popover-foreground",
        "--primary",
        "--primary-foreground",
        "--radius",
        "--ring",
        "--secondary",
        "--secondary-foreground",
        "--status-negative",
        "--status-positive",
        "--status-warning",
        "--success",
        "--success-foreground",
        "--temperature-multiplier",
        "--tod-sky-1",
        "--tod-sky-2",
        "--tod-sky-3",
        "--warning",
        "--warning-foreground",
      ]
    `);
  });

  it("lock guards >=30 tokens (architectural floor)", () => {
    const names = extractTokenNames(read());
    expect(names.length).toBeGreaterThanOrEqual(30);
  });
});
