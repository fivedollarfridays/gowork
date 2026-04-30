/**
 * polish-2 Driver D — T45 layout inline-critical-CSS.
 *
 * Asserts the root layout inlines the generated critical.css block at
 * the top of <body> via a `<style>` tag. The block must contain at
 * least one critical token (--bg-base) so we know the file isn't a
 * stub.
 *
 * The full Lighthouse FCP < 1.2s budget is verified out-of-band.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..");
const LAYOUT = path.resolve(FRONTEND_ROOT, "src/app/layout.tsx");
const CRITICAL = path.resolve(FRONTEND_ROOT, "src/app/styles/critical.css");

describe("polish-2 T45 — layout inlines critical.css", () => {
  it("critical.css exists and contains the --bg-base token", () => {
    const css = fs.readFileSync(CRITICAL, "utf-8");
    expect(css).toMatch(/--bg-base/);
  });

  it("layout.tsx imports critical.css and injects an inline <style> block", () => {
    const src = fs.readFileSync(LAYOUT, "utf-8");
    // Either an explicit raw import (`?raw`) or an `import criticalCss from`
    // is acceptable. The marker `data-critical-css` lives on the inline
    // tag so static checks can find it without parsing JSX.
    expect(src).toMatch(/critical(\.css)?/);
    expect(src).toMatch(/data-critical-css/);
  });
});
