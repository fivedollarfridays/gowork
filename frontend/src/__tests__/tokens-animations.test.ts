/**
 * Animations partial (Wave 1 + Wave 3).
 *
 * Verifies T1.107 brand-mark hover path-draw, brand-loading loop, and the
 * editorial-link gradient underline. Reduced-motion fallbacks must be
 * declared per-class (defense in depth on top of motion.css killswitch).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const CSS = readFileSync(
  join(process.cwd(), "src/app/styles/tokens/animations.css"),
  "utf8",
);

describe("animations.css — T1.107 brand-mark hover path-draw", () => {
  it("declares stroke-dasharray on .gowork-mark--hover .path-draw line", () => {
    expect(CSS).toMatch(/\.gowork-mark--hover[\s\S]*?\.path-draw line/);
    expect(CSS).toMatch(/stroke-dasharray:\s*192/);
  });

  it("targets stroke-dashoffset transition on hover", () => {
    expect(CSS).toMatch(
      /transition:\s*stroke-dashoffset\s+600ms\s+cubic-bezier\(0\.16,\s*1,\s*0\.3,\s*1\)/,
    );
  });

  it("animates the path on :hover and :focus-visible (keyboard parity)", () => {
    expect(CSS).toMatch(/:hover[\s\S]*\.gowork-mark__path/);
    expect(CSS).toMatch(/:focus-visible[\s\S]*\.gowork-mark__path/);
  });

  it("provides a reduced-motion fallback that disables the transition", () => {
    expect(CSS).toMatch(
      /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.gowork-mark--hover[\s\S]*?transition:\s*none/,
    );
  });
});

describe("animations.css — Spotlight brand-loading", () => {
  it("declares the @keyframes brand-loading-draw cycle", () => {
    expect(CSS).toMatch(/@keyframes\s+brand-loading-draw/);
    expect(CSS).toMatch(/0%\s*\{\s*stroke-dashoffset:\s*192/);
    expect(CSS).toMatch(/50%\s*\{\s*stroke-dashoffset:\s*0/);
  });

  it("loops at 3s on the cyan path-line", () => {
    expect(CSS).toMatch(/animation:\s*brand-loading-draw\s+3s/);
  });

  it("falls back to opacity pulse under reduced-motion", () => {
    expect(CSS).toMatch(/@keyframes\s+brand-loading-pulse/);
    expect(CSS).toMatch(/animation:\s*brand-loading-pulse/);
  });
});

describe("animations.css — Wave 3 editorial-link gradient underline", () => {
  it("uses linear-gradient cyan -> amber via background-image", () => {
    expect(CSS).toMatch(/\.editorial-link\s*\{[\s\S]*background-image:\s*linear-gradient/);
    expect(CSS).toMatch(/--accent-cyan/);
    expect(CSS).toMatch(/--accent-amber/);
  });

  it("expands underline thickness on hover/focus", () => {
    expect(CSS).toMatch(/:hover[\s\S]*background-size:\s*100%\s*3px/);
    expect(CSS).toMatch(/:focus-visible[\s\S]*background-size:\s*100%\s*3px/);
  });

  it("falls back to a solid border-bottom under reduced-motion", () => {
    expect(CSS).toMatch(
      /@media \(prefers-reduced-motion: reduce\)[\s\S]*\.editorial-link[\s\S]*border-bottom:\s*2px solid/,
    );
  });
});
