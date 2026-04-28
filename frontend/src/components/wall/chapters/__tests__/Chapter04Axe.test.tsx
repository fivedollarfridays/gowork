/**
 * W2 Driver C — axe-core a11y scan for Ch4 sub-chapters (T2.39).
 *
 * Each sub-chapter must produce ZERO axe violations when rendered in
 * isolation. We import axe-core directly (no Playwright wrapper here —
 * Playwright is the e2e tier; this is the in-tree gate Reviewer uses).
 *
 * The check is intentionally narrow: we audit the rendered DOM with the
 * default ruleset minus rules that depend on a real layout engine
 * (color-contrast and meta-viewport, which jsdom can't evaluate).
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import axe from "axe-core";
import { AriaLiveProvider, AriaLiveRegion } from "../../AriaLiveRegion";
import { Chapter04TheWall } from "../Chapter04TheWall";
import { Chapter04aCriminalRecord } from "../Chapter04aCriminalRecord";
import { Chapter04bNoTransit } from "../Chapter04bNoTransit";
import { Chapter04cNoChildcare } from "../Chapter04cNoChildcare";
import { Chapter04dBadCredit } from "../Chapter04dBadCredit";
import { Chapter05Labyrinth } from "../Chapter05Labyrinth";

const AXE_OPTIONS = {
  rules: {
    // jsdom doesn't compute pixel colors → contrast checks unreliable here.
    "color-contrast": { enabled: false },
    // meta viewport tag lives in the Next.js layout, not under test.
    "meta-viewport": { enabled: false },
    // axe trips on landmark-one-main when chapters render in isolation;
    // real <main> is provided by app/layout.tsx in production.
    "landmark-one-main": { enabled: false },
    region: { enabled: false },
  },
} as const;

async function scan(node: HTMLElement) {
  const result = await axe.run(node, AXE_OPTIONS);
  return result.violations;
}

describe("Ch4 a11y — zero axe violations per sub-chapter", () => {
  it("Chapter04aCriminalRecord", async () => {
    const { container } = render(<Chapter04aCriminalRecord progress={0.1} />);
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter04bNoTransit", async () => {
    const { container } = render(<Chapter04bNoTransit progress={0.4} />);
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter04cNoChildcare", async () => {
    const { container } = render(<Chapter04cNoChildcare progress={0.6} />);
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter04dBadCredit", async () => {
    const { container } = render(<Chapter04dBadCredit progress={0.9} />);
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter04TheWall (orchestrator) — wrapped in AriaLiveProvider", async () => {
    const { container } = render(
      <AriaLiveProvider>
        <AriaLiveRegion />
        <Chapter04TheWall progress={0.3} />
      </AriaLiveProvider>,
    );
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter04TheWall mid-traversal (4c)", async () => {
    const { container } = render(
      <AriaLiveProvider>
        <AriaLiveRegion />
        <Chapter04TheWall progress={0.6} />
      </AriaLiveProvider>,
    );
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });
});

describe("Ch5 a11y — zero axe violations on Labyrinth", () => {
  it("Chapter05Labyrinth at progress=0.5", async () => {
    const { container } = render(
      <AriaLiveProvider>
        <AriaLiveRegion />
        <Chapter05Labyrinth progress={0.5} />
      </AriaLiveProvider>,
    );
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });

  it("Chapter05Labyrinth at progress=1 (all offices lit)", async () => {
    const { container } = render(
      <AriaLiveProvider>
        <AriaLiveRegion />
        <Chapter05Labyrinth progress={1} />
      </AriaLiveProvider>,
    );
    const violations = await scan(container);
    expect(violations).toEqual([]);
  });
});
