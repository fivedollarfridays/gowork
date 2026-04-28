/**
 * W1 Driver C — chapter-divider art (Wave 7 enrichment).
 *
 * Asserts the inline SVG ornament committed to public/chapter-divider.svg
 * is present, viewable, and uses the brand accent (#22D3EE). The asset is
 * inserted between chapters in W2 to create editorial cadence — the
 * "magazine essay" feel the design plan calls out.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

describe("public/chapter-divider.svg", () => {
  const path = join(process.cwd(), "public", "chapter-divider.svg");
  const svg = readFileSync(path, "utf8");

  it("is a valid SVG document", () => {
    expect(svg).toMatch(/<svg\b/);
    expect(svg).toMatch(/<\/svg>/);
  });

  it("uses the cyan brand accent #22D3EE", () => {
    expect(svg).toMatch(/#22D3EE/i);
  });

  it("declares aria-hidden / role=presentation (decorative)", () => {
    expect(svg).toMatch(/aria-hidden=["']true["']|role=["']presentation["']/);
  });

  it("uses a wide viewBox for horizontal placement (>= 200 units)", () => {
    const match = svg.match(/viewBox=["']\s*0\s+0\s+(\d+)\s+(\d+)\s*["']/);
    expect(match).not.toBeNull();
    if (match) {
      const w = Number(match[1]);
      expect(w).toBeGreaterThanOrEqual(200);
    }
  });
});
