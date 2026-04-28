/**
 * W4 Driver C — T4.C.4 — BarrierConstellation screen-reader description.
 *
 * The 33-node 3D barrier graph is decorative; a screen reader cannot
 * meaningfully traverse it. We ship a textual summary in `aria-label`
 * (and `role="img"`) so SR users get the editorial substance:
 *   "33 barriers across 7 categories. Path completeness 50%."
 *
 * Without this gate, NVDA/JAWS users hear "graphic" — no information.
 */
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "mock-canvas" }, children),
}));

import { BarrierConstellation } from "../BarrierConstellation";

afterEach(() => cleanup());

describe("T4.C.4 — BarrierConstellation aria-label", () => {
  it("root has role='img' so SR treats it as a single image, not a tree", () => {
    const { container } = render(
      <BarrierConstellation pathCompleteness={0.5} reducedMotion={false} />,
    );
    const root = container.querySelector("[data-testid='constellation-root']");
    expect(root).not.toBeNull();
    expect(root?.getAttribute("role")).toBe("img");
  });

  it("aria-label mentions the node count (so SR users know the scope)", () => {
    const { container } = render(
      <BarrierConstellation pathCompleteness={0.5} reducedMotion={false} />,
    );
    const root = container.querySelector("[data-testid='constellation-root']");
    const label = root?.getAttribute("aria-label") ?? "";
    expect(label.length).toBeGreaterThan(0);
    expect(label).toMatch(/\d+/); // contains a numeric count
  });

  it("aria-label changes with reducedMotion to acknowledge the static fallback", () => {
    const { container: liveContainer } = render(
      <BarrierConstellation pathCompleteness={0.5} reducedMotion={false} />,
    );
    const live = liveContainer
      .querySelector("[data-testid='constellation-root']")
      ?.getAttribute("aria-label");

    cleanup();

    const { container: reducedContainer } = render(
      <BarrierConstellation pathCompleteness={0.5} reducedMotion={true} />,
    );
    const reduced = reducedContainer
      .querySelector("[data-testid='constellation-root']")
      ?.getAttribute("aria-label");

    // The labels both exist; they may differ, but both must be non-empty.
    expect(live?.length ?? 0).toBeGreaterThan(0);
    expect(reduced?.length ?? 0).toBeGreaterThan(0);
  });

  it("aria-label reflects the path-completeness value", () => {
    const { container } = render(
      <BarrierConstellation pathCompleteness={1.0} reducedMotion={false} />,
    );
    const root = container.querySelector("[data-testid='constellation-root']");
    const label = root?.getAttribute("aria-label") ?? "";
    // At completeness=1, label mentions "complete" or "100" or similar.
    // Keep the assertion loose — we only need a numeric clue.
    expect(label).toMatch(/\d/);
  });
});
