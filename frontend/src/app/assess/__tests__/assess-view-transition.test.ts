/**
 * W3 Driver C — T3.21 — /assess hero morph target contract.
 *
 * Asserts the /assess page source declares the matching
 * `view-transition-name` constant on a stable element so the Ch10
 * CTA's morph has a counterpart to interpolate into. We assert at
 * source level (not via React render) because:
 *   1. The actual /assess page is a heavy mutation/state surface; a
 *      full render in this test couples Driver C's contract to the
 *      whole assess wizard.
 *   2. Source-level grep is sufficient — the runtime contract is
 *      "this string appears as inline-style on a hero element."
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { WALL_TO_ASSESS_TRANSITION_NAME } from "@/lib/wall/viewTransitions";

const ASSESS_PAGE_PATH = resolve(
  __dirname,
  "..",
  "page.tsx",
);

describe("T3.21 — /assess hero declares matching view-transition-name", () => {
  it("source references WALL_TO_ASSESS_TRANSITION_NAME constant", () => {
    const source = readFileSync(ASSESS_PAGE_PATH, "utf-8");
    expect(source).toMatch(/WALL_TO_ASSESS_TRANSITION_NAME/);
  });

  it("source imports the constant from lib/wall/viewTransitions", () => {
    const source = readFileSync(ASSESS_PAGE_PATH, "utf-8");
    expect(source).toMatch(
      /from\s+["']@\/lib\/wall\/viewTransitions["']/,
    );
  });

  it("constant value is canonical 'wall-to-assess' (no drift)", () => {
    expect(WALL_TO_ASSESS_TRANSITION_NAME).toBe("wall-to-assess");
  });
});
