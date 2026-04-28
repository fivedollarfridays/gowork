/**
 * W3 Driver C — T3.24 — axe-core a11y sweep across W3 chapters.
 *
 * Each W3 chapter (Ch6–Ch10) must pass with ZERO axe violations of
 * severity ≥ moderate when rendered in isolation. Driver C asserts
 * Ch10 today; Ch6/Ch7/Ch8/Ch9 are written with `describe.skip` so
 * souji-sweep un-skips after Drivers A+B merge.
 *
 * Uses the shared `runAxeOnChapter` harness (Spotlight #1) so every
 * chapter's a11y test runs the SAME ruleset + severity threshold.
 */
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { runAxeOnChapter } from "@/lib/a11y/axeChapterRunner";
import { Chapter10FindYourPath } from "../chapters/Chapter10FindYourPath";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}));

beforeEach(() => undefined);
afterEach(() => cleanup());

describe("T3.24 — Ch10 axe-core sweep (Driver C lane)", () => {
  it("Chapter10FindYourPath at progress=0 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter10FindYourPath, { progress: 0, active: true }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter10FindYourPath at progress=0.5 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter10FindYourPath, {
        progress: 0.5,
        active: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter10FindYourPath at progress=1 (terminal) — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter10FindYourPath, {
        progress: 1,
        active: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter10FindYourPath with reducedMotion=true — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter10FindYourPath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });
});

// Drivers A+B own Ch6/Ch7/Ch8/Ch9. Souji-sweep un-skips after merge.
describe.skip("T3.24 — Ch6 axe-core sweep (un-skip after Driver B Ch6 merge)", () => {
  it("placeholder until Driver B's Chapter06 component lands", () => {
    expect(true).toBe(true);
  });
});

describe.skip("T3.24 — Ch7 axe-core sweep (un-skip after Driver A Ch7 merge)", () => {
  it("placeholder until Driver A's Chapter07 component lands", () => {
    expect(true).toBe(true);
  });
});

describe.skip("T3.24 — Ch8 axe-core sweep (un-skip after Driver B Ch8 merge)", () => {
  it("placeholder until Driver B's Chapter08 component lands", () => {
    expect(true).toBe(true);
  });
});

describe.skip("T3.24 — Ch9 axe-core sweep (un-skip after Driver A Ch9 merge)", () => {
  it("placeholder until Driver A's Chapter09 component lands", () => {
    expect(true).toBe(true);
  });
});
