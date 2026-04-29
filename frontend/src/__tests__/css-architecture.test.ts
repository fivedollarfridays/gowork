import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.9 — CSS architecture regression smoke test.
 *
 * After T1.7 (split) + T1.8 (imports), prove zero regressions:
 * - globals.css has 5 @import statements in correct order
 * - each partial is non-empty (has comment header at minimum)
 * - all original token names + utilities still resolvable through the chain
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");

function read(rel: string): string {
  return fs.readFileSync(path.resolve(FRONTEND_ROOT, rel), "utf-8");
}

describe("T1.9 — CSS architecture regression", () => {
  const globals = read("src/app/globals.css");

  it("globals.css contains @tailwind directives", () => {
    expect(globals).toContain("@tailwind base");
    expect(globals).toContain("@tailwind components");
    expect(globals).toContain("@tailwind utilities");
  });

  it("globals.css imports the token partials in cascade-correct order", () => {
    const imports = globals.match(/@import\s+["']\.\/styles\/tokens\/([\w-]+)\.css["']/g);
    expect(imports).not.toBeNull();
    // 5 base partials (T1.7) + 1 forced-colors (T1.96 enrichment).
    expect(imports!.length).toBeGreaterThanOrEqual(5);
    const order = imports!.map((line) => {
      const m = line.match(/tokens\/([\w-]+)\.css/);
      return m ? m[1] : "";
    });
    // Cascade: colors first (everything depends on bg/fg), then typography
    // (text on bg), motion (animation of typed elements), space (rhythm),
    // layout (utilities + universal resets). Forced-colors LAST so it can
    // override every prior token in HCM.
    expect(order.slice(0, 5)).toEqual(["colors", "typography", "motion", "space", "layout"]);
  });

  it("globals.css <= 40 lines (thin shell; polish-2 added home-velocity.css + print.css imports)", () => {
    expect(globals.split("\n").length).toBeLessThanOrEqual(40);
  });

  it.each([
    ["colors.css"],
    ["typography.css"],
    ["motion.css"],
    ["space.css"],
    ["layout.css"],
  ])("partial %s is non-empty (has at minimum a comment header)", (name) => {
    const content = read(`src/app/styles/tokens/${name}`);
    expect(content.trim().length).toBeGreaterThan(0);
  });

  it("token chain still resolves --background (key shadcn dep)", () => {
    const colors = read("src/app/styles/tokens/colors.css");
    expect(colors).toMatch(/--background:\s*60 20% 95%/);
  });

  it("layout chain still defines .text-balance utility", () => {
    const layout = read("src/app/styles/tokens/layout.css");
    expect(layout).toContain(".text-balance");
  });

  it("layout chain still applies bg-background + text-foreground to body", () => {
    const layout = read("src/app/styles/tokens/layout.css");
    expect(layout).toContain("bg-background");
    expect(layout).toContain("text-foreground");
  });
});
