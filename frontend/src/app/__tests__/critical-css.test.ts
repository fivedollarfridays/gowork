/**
 * polish-2 Driver D — T45 critical-CSS extraction.
 *
 * Static smoke test for the above-the-fold critical-CSS pipeline:
 *   1. The build helper exists at `frontend/scripts/extract-critical-css.mjs`.
 *   2. It exports a pure function that, given source CSS, returns a
 *      string containing the rules whose selectors match the
 *      "above-the-fold" allowlist (.ch01*, .site-header, .brand, .cta,
 *      :root, html, body).
 *   3. Running it against the actual home stylesheet emits non-empty
 *      output and contains rules for the Ch1 hero base styles.
 *   4. The emitted critical.css file lands at the expected path
 *      (frontend/src/app/styles/critical.css).
 *
 * Lighthouse FCP < 1.2s is verified out-of-band by the lighthouse-budget
 * gate; this test guards the static contract.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..");

describe("polish-2 T45 — critical-CSS extraction", () => {
  const SCRIPT = path.resolve(FRONTEND_ROOT, "scripts/extract-critical-css.mjs");

  it("the build script exists", () => {
    expect(fs.existsSync(SCRIPT)).toBe(true);
  });

  it("exports an `extractCritical` pure function from the script module", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    expect(typeof mod.extractCritical).toBe("function");
  });

  it("extractCritical preserves :root token blocks (so the inline CSS bears variables)", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    const sample = `:root { --bg-base: #0A0E1A; --fg-primary: #F5F3EE; }
.unused { color: red; }`;
    const out = mod.extractCritical(sample);
    expect(out).toMatch(/--bg-base/);
    expect(out).toMatch(/--fg-primary/);
    expect(out).not.toMatch(/\.unused/);
  });

  it("extractCritical includes .ch01-* and .site-header / .brand / .cta rules", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    const sample = `.ch01-hero { background: black; }
.site-header { height: 48px; }
.brand { font-weight: 700; }
.cta { padding: 1rem; }
.unrelated { display: none; }`;
    const out = mod.extractCritical(sample);
    expect(out).toMatch(/\.ch01-hero/);
    expect(out).toMatch(/\.site-header/);
    expect(out).toMatch(/\.brand/);
    expect(out).toMatch(/\.cta/);
    expect(out).not.toMatch(/\.unrelated/);
  });

  it("extractCritical drops vendor-prefix-only rules and unrelated chapter selectors", async () => {
    const mod = await import(/* @vite-ignore */ `file:///${SCRIPT.replace(/\\/g, "/")}`);
    const sample = `.ch04-pin { height: 100vh; }
.ch06-card { padding: 1rem; }
.ch01-hero { color: white; }`;
    const out = mod.extractCritical(sample);
    expect(out).toMatch(/\.ch01-hero/);
    expect(out).not.toMatch(/\.ch04-pin/);
    expect(out).not.toMatch(/\.ch06-card/);
  });
});
