import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * Theme race-safety: data-theme attribute alone must drive shadcn HSL tokens.
 *
 * Pre-fix bug: layout's inline boot script set both `data-theme` AND `.dark`
 * class on <html>. If only the attribute landed (hydration race, third-party
 * script, or someone calling setAttribute without the class), the OKLCH base
 * tokens still flipped to dark (covered by :root[data-theme="dark"]) but the
 * shadcn HSL palette stayed on the :root LIGHT defaults — producing a
 * dark-page-with-cream-cards Frankenstein on /plan.
 *
 * Fix: parallel :root[data-theme="dark"] and :root[data-theme="light"]
 * blocks that mirror the .dark / :root shadcn HSL palettes. The data-theme
 * attribute is then sufficient on its own, with the .dark class as
 * belt-and-braces.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const COLORS_CSS = path.resolve(
  FRONTEND_ROOT,
  "src/app/styles/tokens/colors.css"
);

function read(p: string): string {
  return fs.readFileSync(p, "utf-8");
}

describe("theme-data-attribute-parity — shadcn HSL palette responds to [data-theme]", () => {
  it("declares :root[data-theme=\"dark\"] for shadcn --background (navy canvas)", () => {
    const colors = read(COLORS_CSS);
    // The data-theme=dark block must set --background to the dark navy
    // (225 44% 7% = #0A0E1A). Either inside a dedicated block or via a
    // selector list including [data-theme="dark"].
    const blocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const merged = blocks.join("\n");
    expect(merged).toContain("--background: 225 44% 7%");
  });

  it("declares :root[data-theme=\"dark\"] for shadcn --card (navy surface, NOT cream)", () => {
    const colors = read(COLORS_CSS);
    const blocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const merged = blocks.join("\n");
    // 222 46% 11% = #0F1729 — the dark surface. Without this rule the
    // :root light default of 38 24% 89% (#ECE7DC cream) leaks through
    // when only the attribute is set.
    expect(merged).toContain("--card: 222 46% 11%");
  });

  it("declares :root[data-theme=\"dark\"] for shadcn --foreground (warm paper)", () => {
    const colors = read(COLORS_CSS);
    const blocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const merged = blocks.join("\n");
    expect(merged).toContain("--foreground: 43 26% 95%");
  });

  it("declares :root[data-theme=\"dark\"] for --muted-foreground (readable on dark cards)", () => {
    const colors = read(COLORS_CSS);
    const blocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const merged = blocks.join("\n");
    // 212 18% 59% = #8696A8 — passes WCAG AAA-large on the dark surface.
    expect(merged).toContain("--muted-foreground: 212 18% 59%");
  });

  it("declares :root[data-theme=\"dark\"] for --primary (cyan accent)", () => {
    const colors = read(COLORS_CSS);
    const blocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const merged = blocks.join("\n");
    // 187 86% 53% = #22D3EE cyan — same in both themes, but explicit
    // belt-and-braces declaration so badges and rings stay branded.
    expect(merged).toContain("--primary: 187 86% 53%");
  });

  it("declares :root[data-theme=\"light\"] mirroring the :root light shadcn defaults", () => {
    const colors = read(COLORS_CSS);
    const blocks = extractBlocks(colors, /:root\[data-theme="light"\]/);
    // We expect at least one block — the OKLCH-base block already exists,
    // plus a new shadcn-HSL block. Concatenate them all and check.
    const merged = blocks.join("\n");
    expect(merged).toContain("--background: 43 26% 95%"); // warm paper
    expect(merged).toContain("--card: 38 24% 89%"); // paper-1
    expect(merged).toContain("--foreground: 225 44% 7%"); // navy ink
  });

  it("dark data-theme block uses the same --card as the .dark class block (no drift)", () => {
    const colors = read(COLORS_CSS);
    // Either the two selectors share a single rule (selector list, what
    // we ship) or each gets its own block — both arrangements are
    // race-safe. We assert the rule is reachable from both selectors.
    const dataThemeDarkBlocks = extractBlocks(colors, /:root\[data-theme="dark"\]/);
    const dotDarkBlocks = extractBlocks(colors, /\.dark[\s,{]/);
    const dataThemeMerged = dataThemeDarkBlocks.join("\n");
    const dotDarkMerged = dotDarkBlocks.join("\n");
    const cardRule = "--card: 222 46% 11%";
    expect(dataThemeMerged).toContain(cardRule);
    expect(dotDarkMerged).toContain(cardRule);
  });
});

/**
 * Extract every `{...}` block whose selector header matches `selectorRe`.
 * Naive brace-balanced scan — sufficient for our hand-authored CSS where
 * tokens partials don't use nested at-rules with curly braces inside
 * selector strings.
 */
function extractBlocks(css: string, selectorRe: RegExp): string[] {
  const blocks: string[] = [];
  const flagged = new RegExp(selectorRe.source, "g" + (selectorRe.flags.includes("m") ? "m" : ""));
  let m: RegExpExecArray | null;
  while ((m = flagged.exec(css)) !== null) {
    const openIdx = css.indexOf("{", m.index);
    if (openIdx === -1) continue;
    let depth = 1;
    let i = openIdx + 1;
    while (i < css.length && depth > 0) {
      if (css[i] === "{") depth++;
      else if (css[i] === "}") depth--;
      i++;
    }
    if (depth === 0) {
      blocks.push(css.slice(openIdx + 1, i - 1));
    }
  }
  return blocks;
}
