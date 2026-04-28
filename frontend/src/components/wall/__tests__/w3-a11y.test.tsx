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
import { Chapter06TheMath } from "../chapters/Chapter06TheMath";
import { Chapter07ThePath } from "../chapters/Chapter07ThePath";
import { Chapter08TheGraph } from "../chapters/Chapter08TheGraph";
import { Chapter09AnyCity } from "../chapters/Chapter09AnyCity";
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

// Drivers A+B own Ch6/Ch7/Ch8/Ch9. Driver D un-skipped after W3 merge.
describe("T3.24 — Ch6 axe-core sweep (un-skipped by Driver D)", () => {
  it("Chapter06TheMath at progress=0 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter06TheMath, { progress: 0, active: true }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter06TheMath with reducedMotion=true — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter06TheMath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });
});

describe("T3.24 — Ch7 axe-core sweep (un-skipped by Driver D)", () => {
  it("Chapter07ThePath at progress=0 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter07ThePath, { progress: 0, active: true }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter07ThePath with reducedMotion=true (static SVG path) — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter07ThePath, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });
});

describe("T3.24 — Ch8 axe-core sweep (un-skipped by Driver D)", () => {
  it("Chapter08TheGraph at progress=0 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter08TheGraph, { progress: 0, active: true }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter08TheGraph with reducedMotion=true (static SVG fallback) — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter08TheGraph, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });
});

describe("T3.24 — Ch9 axe-core sweep (un-skipped by Driver D)", () => {
  it("Chapter09AnyCity at progress=0 — 0 moderate-or-above violations", async () => {
    const { container } = render(
      React.createElement(Chapter09AnyCity, { progress: 0, active: true }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });

  it("Chapter09AnyCity with reducedMotion=true — 0 violations", async () => {
    const { container } = render(
      React.createElement(Chapter09AnyCity, {
        progress: 0.5,
        active: true,
        reducedMotion: true,
      }),
    );
    const violations = await runAxeOnChapter(container);
    expect(violations).toEqual([]);
  });
});
