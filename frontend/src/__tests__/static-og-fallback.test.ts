/**
 * T5.B.5 — Static OG fallback gate test.
 *
 * Verifies:
 *  1. `frontend/scripts/generate-static-og.mjs` exists and is documented
 *     (README block at top + run instructions).
 *  2. The script declares chapters 1..10 + default as the targets it
 *     hits against the local dev server's /api/og routes.
 *  3. The /api/og/[chapter] route guards Satori errors with a try/catch
 *     and falls back to the static PNG path when ImageResponse throws.
 *  4. The route's static fallback path is the documented
 *     /og/<chapter>.png location (so the script's outputs and the
 *     route's redirects line up).
 */
import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const SCRIPT_PATH = join(process.cwd(), "scripts", "generate-static-og.mjs");
const ROUTE_PATH = join(
  process.cwd(),
  "src",
  "app",
  "api",
  "og",
  "[chapter]",
  "route.ts",
);

describe("T5.B.5 — static OG fallback", () => {
  it("scripts/generate-static-og.mjs exists", () => {
    expect(existsSync(SCRIPT_PATH)).toBe(true);
  });

  it("the generate-static-og script targets chapters 1..10 + default", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    for (let n = 1; n <= 10; n += 1) {
      // Either as a literal token in the chapters array, or as part of
      // a URL like /api/og/1, /api/og/2, etc.
      expect(src).toMatch(new RegExp(`(?:\\b|\\/)${n}(?:\\b|\\/|,)`));
    }
    expect(src).toMatch(/default/);
  });

  it("the script documents how to run it (npm run dev + node script)", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    expect(src).toMatch(/npm run dev/);
    expect(src).toMatch(/node\s+(?:scripts\/)?generate-static-og\.mjs/);
  });

  it("the script writes outputs to public/og/<chapter>.png", () => {
    const src = readFileSync(SCRIPT_PATH, "utf8");
    expect(src).toMatch(/public\/og/);
    expect(src).toMatch(/\.png/);
  });

  it("the [chapter] OG route wraps ImageResponse in try/catch", () => {
    const src = readFileSync(ROUTE_PATH, "utf8");
    expect(src).toMatch(/try\s*\{[\s\S]*ImageResponse/);
    expect(src).toMatch(/catch\s*\(/);
  });

  it("the [chapter] OG route falls back to /og/<chapter>.png on Satori error", () => {
    const src = readFileSync(ROUTE_PATH, "utf8");
    // The fallback must redirect / serve the static PNG path.
    expect(src).toMatch(/\/og\//);
    expect(src).toMatch(/\.png/);
  });
});
