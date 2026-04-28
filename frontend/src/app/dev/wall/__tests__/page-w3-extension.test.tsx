/**
 * /dev/wall — W3 chapter inspector extension (Driver D Spotlight #4).
 *
 * Asserts the inspector now surfaces all 10 chapter rows with:
 *   - data-chapter-jump for every chapter (1..10)
 *   - data-chapter-slug pulled from CHAPTER_SPECS
 *   - per-row camera summary + sound id rendered
 *
 * # Why this exists
 *
 * The original /dev/wall test (page.test.tsx) only verified Ch1..Ch5.
 * Driver D extended the inspector to surface camera + sound + slug
 * metadata for every chapter, and pinned the new contract here so future
 * refactors can't silently lose that detail.
 */
import React from "react";
import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { render } from "@testing-library/react";

vi.mock("next/dynamic", () => ({
  default: () => () =>
    React.createElement("div", { "data-testid": "dynamic-stub" }),
}));

const ORIGINAL_NODE_ENV = process.env.NODE_ENV;

afterEach(() => {
  vi.stubEnv("NODE_ENV", ORIGINAL_NODE_ENV ?? "test");
});

describe("/dev/wall — W3 inspector lists all 10 chapters", () => {
  beforeEach(() => {
    vi.stubEnv("NODE_ENV", "test");
  });

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "row for Ch%i is rendered",
    async (id) => {
      const { default: WallInspectorPage } = await import("../page");
      const { container } = render(React.createElement(WallInspectorPage));
      const row = container.querySelector(`[data-chapter-jump="${id}"]`);
      expect(row).not.toBeNull();
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "row for Ch%i carries data-chapter-slug",
    async (id) => {
      const { default: WallInspectorPage } = await import("../page");
      const { container } = render(React.createElement(WallInspectorPage));
      const row = container.querySelector(`[data-chapter-jump="${id}"]`);
      expect(row).not.toBeNull();
      const slug = row?.getAttribute("data-chapter-slug");
      expect(typeof slug).toBe("string");
      expect((slug ?? "").length).toBeGreaterThan(0);
      expect(slug).not.toBe("unknown");
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "row for Ch%i renders camera summary",
    async (id) => {
      const { default: WallInspectorPage } = await import("../page");
      const { queryByTestId } = render(React.createElement(WallInspectorPage));
      const cam = queryByTestId(`ch${id}-camera-summary`);
      expect(cam).not.toBeNull();
      // Camera summary contains lng/lat/zoom/pitch/bearing tokens
      expect(cam?.textContent).toMatch(/lng|no camera/);
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "row for Ch%i renders sound id label",
    async (id) => {
      const { default: WallInspectorPage } = await import("../page");
      const { queryByTestId } = render(React.createElement(WallInspectorPage));
      const sound = queryByTestId(`ch${id}-sound-id`);
      expect(sound).not.toBeNull();
      expect(sound?.textContent).toMatch(/Sound:/);
    },
  );

  it.each([1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const)(
    "row for Ch%i renders titleKey reference",
    async (id) => {
      const { default: WallInspectorPage } = await import("../page");
      const { queryByTestId } = render(React.createElement(WallInspectorPage));
      const tk = queryByTestId(`ch${id}-title-key`);
      expect(tk).not.toBeNull();
      const padded = id < 10 ? `0${id}` : String(id);
      expect(tk?.textContent).toContain(`wall.chapter${padded}.title`);
    },
  );
});
