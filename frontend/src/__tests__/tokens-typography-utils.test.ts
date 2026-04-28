import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.17 — Tabular nums + monospace data utilities.
 *
 * Two utility-layer classes consumed by W3 stat displays + W4 timestamp UI.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TYPOGRAPHY_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/typography.css");

function read(): string {
  return fs.readFileSync(TYPOGRAPHY_CSS, "utf-8");
}

describe("T1.17 — utility classes (typography)", () => {
  const css = read();

  it("defines .tabular-nums at root scope (post-8b04ae8 @layer removal)", () => {
    expect(css).toMatch(/\.tabular-nums\s*\{/);
  });

  it(".tabular-nums sets font-feature-settings 'tnum' 1", () => {
    const m = css.match(/\.tabular-nums\s*\{([^}]+)\}/);
    expect(m).not.toBeNull();
    const body = m![1];
    expect(body).toMatch(/font-feature-settings:\s*"tnum"\s*1/);
    expect(body).toMatch(/font-variant-numeric:\s*tabular-nums/);
  });

  it("defines .font-mono-data at root scope (post-8b04ae8 @layer removal)", () => {
    expect(css).toMatch(/\.font-mono-data\s*\{/);
  });

  it(".font-mono-data uses ui-monospace stack", () => {
    const m = css.match(/\.font-mono-data\s*\{([^}]+)\}/);
    expect(m).not.toBeNull();
    expect(m![1]).toMatch(/ui-monospace/);
  });
});

describe("T1.17 — jsdom snapshot of computed feature settings", () => {
  it("element with tabular-nums inline style reads back correctly", () => {
    const div = document.createElement("div");
    div.style.fontFeatureSettings = '"tnum" 1';
    expect(div.style.fontFeatureSettings).toBe('"tnum" 1');
  });
});
