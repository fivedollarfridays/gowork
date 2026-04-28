/**
 * W1 Driver C — brand mark contract.
 *
 * Asserts the new `frontend/public/icon.svg` is the GoWork G+path mark,
 * NOT the legacy MontGoWork M-shape. The legacy mark used `polyline`
 * with the points "112,384 112,160 192,288 272,160 272,384" (an M).
 * This test guards the retirement.
 *
 * The new mark must:
 *   - Use a viewBox of "0 0 16 16" as the SOURCE coordinate system
 *     (legibility designed at 16px first, scaled via SVG viewport).
 *   - Carry an aria-label / <title> referencing GoWork (NOT MontGoWork).
 *   - Contain a `path` element representing the G letterform (large arc).
 *   - Contain a horizontal cyan path-line (#22D3EE) slicing through the
 *     opening of the G — present as a separate <line> or <path> with the
 *     stroke color "#22D3EE" referenced via attribute or class.
 *   - Carry a comment explaining the geometric reasoning (preserves intent
 *     across future edits).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ICON_PATH = join(process.cwd(), "public", "icon.svg");

function readIcon(): string {
  return readFileSync(ICON_PATH, "utf8");
}

describe("public/icon.svg — GoWork brand mark", () => {
  const svg = readIcon();

  it("uses a 16-coordinate viewBox so the mark is designed at 16px first", () => {
    expect(svg).toMatch(/viewBox=["']0 0 16 16["']/);
  });

  it("references GoWork (NOT MontGoWork) in aria-label / title", () => {
    expect(svg).toMatch(/aria-label=["']GoWork[^"']*["']/);
    expect(svg).not.toMatch(/MontGoWork/);
  });

  it("retires the legacy M-shape polyline", () => {
    // The legacy icon used these exact M-shape points.
    expect(svg).not.toMatch(/112,384 112,160 192,288 272,160 272,384/);
    // No M-shape left at any scale: a polyline with two ascending peaks.
    expect(svg).not.toMatch(/<polyline[^>]*M/);
  });

  it("contains the cyan path-line (#22D3EE) slicing the G opening", () => {
    expect(svg).toMatch(/#22D3EE/i);
  });

  it("contains a path element representing the G letterform arc", () => {
    expect(svg).toMatch(/<path\b[^>]*\bd=["'][^"']*A[^"']*["']/i);
  });

  it("carries a geometric-reasoning comment for future maintainers", () => {
    expect(svg).toMatch(/<!--[\s\S]*(geomet|design|G \+ path|legibility)[\s\S]*-->/i);
  });

  it("declares role=img for assistive-tech parity", () => {
    expect(svg).toMatch(/role=["']img["']/);
  });
});
