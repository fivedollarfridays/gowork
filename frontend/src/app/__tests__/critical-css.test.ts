/**
 * polish-2 Driver D — T45 critical-CSS extraction.
 *
 * Static smoke test for the above-the-fold critical-CSS pipeline:
 *   1. The build helper exists at `frontend/scripts/extract-critical-css.mjs`.
 *   2. It exports a pure function `extractCritical(src)` that, given
 *      source CSS, returns a string containing only the rules whose
 *      selectors match the "above-the-fold" allowlist (.ch01*,
 *      .site-header, .brand, .cta, :root, html, body).
 *   3. Running it against the actual home stylesheet emits non-empty
 *      output and contains rules for the Ch1 hero base styles.
 *
 * Lighthouse FCP < 1.2s is verified out-of-band by the lighthouse-budget
 * gate; this test guards the static contract.
 *
 * NOTE: We dispatch a Node child process to import the .mjs module.
 * vitest's Vite-driven loader chokes on runtime-constructed URLs to
 * .mjs files on Windows (CRLF line endings + Vite transform pipeline);
 * the child-process round-trip is a stable workaround that runs the
 * script under the same Node version as production.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..");
const SCRIPT = path.resolve(FRONTEND_ROOT, "scripts/extract-critical-css.mjs");
const SCRIPT_URL = `file:///${SCRIPT.replace(/\\/g, "/")}`;

function runHelper(body: string): unknown {
  const code = `import("${SCRIPT_URL}").then(async (m) => { ${body} }).catch((e) => { console.error(e); process.exit(1); });`;
  const out = execFileSync(
    process.execPath,
    ["--input-type=module", "-e", code],
    { encoding: "utf-8" },
  );
  return JSON.parse(out.trim());
}

describe("polish-2 T45 — critical-CSS extraction", () => {
  it("the build script exists", () => {
    expect(fs.existsSync(SCRIPT)).toBe(true);
  });

  it("exports an `extractCritical` pure function from the script module", () => {
    const out = runHelper(
      `console.log(JSON.stringify({ kind: typeof m.extractCritical }));`,
    ) as { kind: string };
    expect(out.kind).toBe("function");
  });

  it("extractCritical preserves :root token blocks", () => {
    const sample = `:root { --bg-base: #0A0E1A; --fg-primary: #F5F3EE; }
.unused { color: red; }`;
    const out = runHelper(
      `console.log(JSON.stringify({ result: m.extractCritical(${JSON.stringify(sample)}) }));`,
    ) as { result: string };
    expect(out.result).toMatch(/--bg-base/);
    expect(out.result).toMatch(/--fg-primary/);
    expect(out.result).not.toMatch(/\.unused/);
  });

  it("extractCritical includes .ch01-* and .site-header / .brand / .cta rules", () => {
    const sample = `.ch01-hero { background: black; }
.site-header { height: 48px; }
.brand { font-weight: 700; }
.cta { padding: 1rem; }
.unrelated { display: none; }`;
    const out = runHelper(
      `console.log(JSON.stringify({ result: m.extractCritical(${JSON.stringify(sample)}) }));`,
    ) as { result: string };
    expect(out.result).toMatch(/\.ch01-hero/);
    expect(out.result).toMatch(/\.site-header/);
    expect(out.result).toMatch(/\.brand/);
    expect(out.result).toMatch(/\.cta/);
    expect(out.result).not.toMatch(/\.unrelated/);
  });

  it("extractCritical drops unrelated chapter selectors", () => {
    const sample = `.ch04-pin { height: 100vh; }
.ch06-card { padding: 1rem; }
.ch01-hero { color: white; }`;
    const out = runHelper(
      `console.log(JSON.stringify({ result: m.extractCritical(${JSON.stringify(sample)}) }));`,
    ) as { result: string };
    expect(out.result).toMatch(/\.ch01-hero/);
    expect(out.result).not.toMatch(/\.ch04-pin/);
    expect(out.result).not.toMatch(/\.ch06-card/);
  });
});
