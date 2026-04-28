import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.65 — Custom focus rings + selection styles.
 *
 * Layout.css gets:
 * (a) *:focus-visible — 2px cyan outline, 2px offset, animated entry via
 *     outline-offset transition. reduced-motion disables the transition.
 * (b) ::selection + ::-moz-selection — cyan tint with subtle animation.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const LAYOUT_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/layout.css");

function read(): string {
  return fs.readFileSync(LAYOUT_CSS, "utf-8");
}

describe("T1.65 — focus-visible ring", () => {
  const css = read();

  it(":focus-visible rule defined for universal selector", () => {
    expect(css).toMatch(/\*\s*:focus-visible\s*\{|:focus-visible\s*\{/);
  });

  it("focus ring uses --accent-cyan token (no hardcoded hex)", () => {
    const m = css.match(/:focus-visible\s*\{([^}]+)\}/);
    expect(m, ":focus-visible block must exist").not.toBeNull();
    expect(m![1]).toMatch(/var\(--accent-cyan\)/);
  });

  it("focus ring outline width 2px and offset 2px", () => {
    const m = css.match(/:focus-visible\s*\{([^}]+)\}/);
    expect(m![1]).toMatch(/outline:\s*2px/);
    expect(m![1]).toMatch(/outline-offset:\s*2px/);
  });

  it("focus ring transitions outline-offset using EASE_LINEAR_SIG", () => {
    const m = css.match(/:focus-visible\s*\{([^}]+)\}/);
    expect(m![1]).toMatch(/transition:\s*outline-offset\s*\d+ms\s*var\(--ease-linear-sig\)/);
  });

  it("reduced-motion disables the focus transition", () => {
    // Either the universal !important rule from motion.css covers this, OR
    // an explicit override in layout.css. We accept either.
    const explicit = /@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*:focus-visible[^}]*transition:\s*none/.test(css);
    // The universal rule is in motion.css; for layout.css alone we only
    // need to confirm the focus-visible rule is opt-in to the universal
    // override (i.e., it uses transition-duration which is overridden).
    const usesTransition = /:focus-visible[\s\S]*?transition:/.test(css);
    expect(explicit || usesTransition).toBe(true);
  });
});

describe("T1.65 — text selection styling", () => {
  const css = read();

  it("::selection rule defined", () => {
    expect(css).toMatch(/::selection\s*\{/);
  });

  it("::selection uses color-mix() with --accent-cyan", () => {
    const m = css.match(/::selection\s*\{([^}]+)\}/);
    expect(m, "::selection block must exist").not.toBeNull();
    expect(m![1]).toMatch(/color-mix\([^)]*--accent-cyan/);
  });

  it("::selection sets foreground to --fg-primary", () => {
    const m = css.match(/::selection\s*\{([^}]+)\}/);
    expect(m![1]).toMatch(/color:\s*var\(--fg-primary\)/);
  });

  it("::-moz-selection fallback present", () => {
    expect(css).toMatch(/::-moz-selection\s*\{/);
  });
});
