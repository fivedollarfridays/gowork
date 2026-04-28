/**
 * Wave 3 — editorial typography polish.
 *
 * Verifies the editorial-dropcap (alias of legacy .dropcap), editorial-
 * pullquote class, editorial-link gradient underline, and ::selection
 * tokens land in the partials so chapter copy in W2 has the surface
 * to reach for.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const TYPO = readFileSync(
  join(process.cwd(), "src/app/styles/tokens/typography.css"),
  "utf8",
);
const ANIM = readFileSync(
  join(process.cwd(), "src/app/styles/tokens/animations.css"),
  "utf8",
);
const LAYOUT = readFileSync(
  join(process.cwd(), "src/app/styles/tokens/layout.css"),
  "utf8",
);

describe("Wave 3 editorial typography", () => {
  it("declares .editorial-dropcap targeting ::first-letter", () => {
    expect(TYPO).toMatch(/\.editorial-dropcap::first-letter/);
  });

  it("retains the legacy .dropcap class for back-compat", () => {
    expect(TYPO).toMatch(/\.dropcap::first-letter/);
  });

  it("editorial-dropcap uses --accent-amber for chapter-start chrome", () => {
    expect(TYPO).toMatch(
      /\.editorial-dropcap::first-letter[\s\S]*?color:\s*var\(--accent-amber\)/,
    );
  });

  it("legacy .dropcap retains --accent-cyan for back-compat", () => {
    expect(TYPO).toMatch(
      /\.dropcap::first-letter\s*\{[\s\S]*?color:\s*var\(--accent-cyan\)/,
    );
  });

  it("declares .editorial-pullquote with oblique slant", () => {
    expect(TYPO).toMatch(/\.editorial-pullquote/);
    expect(TYPO).toMatch(/font-style:\s*oblique\s+-10deg/);
  });

  it("pullquote has an accent-amber left border", () => {
    expect(TYPO).toMatch(
      /\.editorial-pullquote[\s\S]*?border-left:\s*4px solid var\(--accent-amber\)/,
    );
  });
});

describe("Wave 3 editorial link gradient underline", () => {
  it("declares .editorial-link with gradient background-image", () => {
    expect(ANIM).toMatch(
      /\.editorial-link[\s\S]*?background-image:\s*linear-gradient/,
    );
  });

  it("links use accent-cyan and accent-amber as the gradient endpoints", () => {
    expect(ANIM).toMatch(/\.editorial-link[\s\S]*?--accent-cyan[\s\S]*?--accent-amber/);
  });
});

describe("Wave 3 branded selection styles", () => {
  it("::selection mixes cyan with transparent for accent highlight", () => {
    expect(LAYOUT).toMatch(/::selection[\s\S]*?color-mix\(in oklch[\s\S]*?--accent-cyan/);
  });

  it("::-moz-selection mirror exists for Firefox", () => {
    expect(LAYOUT).toMatch(/::-moz-selection[\s\S]*?--accent-cyan/);
  });
});
