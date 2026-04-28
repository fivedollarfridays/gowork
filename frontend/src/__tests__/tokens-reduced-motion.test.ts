import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.22 — prefers-reduced-motion CSS variable disable.
 * T1.23 — Idle animation scaffold.
 *
 * The motion.css must:
 * 1. Default --motion-disabled: 0 at :root.
 * 2. Inside @media (prefers-reduced-motion: reduce):
 *    - flip --motion-disabled to 1
 *    - drop --duration-baseline to ~0.01ms
 *    - !important-disable animations + transitions on every element
 *    - reset scroll-behavior to auto
 * 3. Define @keyframes idle-pulse + .animate-idle-pulse utility (T1.23).
 * 4. .animate-idle-pulse must be disabled under reduced-motion.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const MOTION_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/motion.css");

function read(): string {
  return fs.readFileSync(MOTION_CSS, "utf-8");
}

describe("T1.22 — reduced-motion variable disable", () => {
  const css = read();

  it("declares --motion-disabled: 0 default at :root", () => {
    // The token-disable contract: 0 = motion enabled, 1 = motion off.
    // Default is 0; the @media block flips it to 1.
    expect(css).toMatch(/--motion-disabled:\s*0\s*;/);
  });

  it("@media (prefers-reduced-motion: reduce) block exists", () => {
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
  });

  it("inside the @media block, --motion-disabled flips to 1", () => {
    const block = css.match(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]+?)\n\}/);
    expect(block, "@media block must exist").not.toBeNull();
    expect(block![1]).toMatch(/--motion-disabled:\s*1\s*;/);
  });

  it("inside the @media block, --duration-baseline drops to 0.01ms", () => {
    const block = css.match(/@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]+?)\n\}/);
    expect(block![1]).toMatch(/--duration-baseline:\s*0\.01ms/);
  });

  it("universal selector !important-disables animation + transition", () => {
    expect(css).toMatch(/animation-duration:\s*0\.01ms\s*!important/);
    expect(css).toMatch(/transition-duration:\s*0\.01ms\s*!important/);
  });

  it("scroll-behavior reset to auto inside the @media block", () => {
    expect(css).toMatch(/scroll-behavior:\s*auto\s*!important/);
  });
});

describe("T1.23 — idle-pulse keyframes + utility", () => {
  const css = read();

  it("@keyframes idle-pulse defined", () => {
    expect(css).toMatch(/@keyframes\s+idle-pulse\s*\{/);
  });

  it(".animate-idle-pulse utility defined under @layer utilities", () => {
    expect(css).toMatch(/@layer utilities[\s\S]*\.animate-idle-pulse/);
  });

  it(".animate-idle-pulse references the idle-pulse keyframes name", () => {
    const block = css.match(/\.animate-idle-pulse\s*\{([^}]+)\}/);
    expect(block).not.toBeNull();
    expect(block![1]).toMatch(/animation:\s*idle-pulse/);
  });

  it(".animate-idle-pulse animation duration matches a known token (4s)", () => {
    const block = css.match(/\.animate-idle-pulse\s*\{([^}]+)\}/);
    expect(block![1]).toMatch(/4s/);
  });

  it("idle pulse disabled under prefers-reduced-motion", () => {
    // The reduced-motion @media block must override .animate-idle-pulse.
    // Either via universal !important rule or specific class override —
    // both branches accepted.
    const reducedMotion = css.includes("animation: none") || css.includes("animation-duration: 0.01ms !important");
    expect(reducedMotion).toBe(true);
  });
});
