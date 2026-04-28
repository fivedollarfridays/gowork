/**
 * Tests for /dev/wall chapter inspector — Driver D Spotlight invention #6.
 *
 * Production guard contract:
 *   - In production (NODE_ENV=production), the route renders a stub.
 *   - In dev/test, the route renders the chapter inspector controls.
 */
import React from "react";
import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { render } from "@testing-library/react";

// Same shape mock as WallContainer test — chapter components reach for
// translations, scroll progress, etc. The inspector page deliberately
// does NOT mount the actual chapter components in this test (it
// redirects via querystring + mock probes), so we only need the page's
// own h1 + nav surface.

vi.mock("next/dynamic", () => ({
  default: () => () =>
    React.createElement("div", { "data-testid": "dynamic-stub" }),
}));

const ORIGINAL_NODE_ENV = process.env.NODE_ENV;

afterEach(() => {
  vi.stubEnv("NODE_ENV", ORIGINAL_NODE_ENV ?? "test");
});

describe("/dev/wall — chapter inspector", () => {
  beforeEach(() => {
    vi.stubEnv("NODE_ENV", "test");
  });

  it("renders the dev inspector heading", async () => {
    const { default: WallInspectorPage } = await import("../page");
    const { getByText } = render(React.createElement(WallInspectorPage));
    expect(getByText(/Wall Inspector/i)).toBeInTheDocument();
  });

  it("lists 5 W2 chapters as jump targets", async () => {
    const { default: WallInspectorPage } = await import("../page");
    const { container } = render(React.createElement(WallInspectorPage));
    // The inspector lists chapters 1-5 as buttons / links / list items.
    const items = container.querySelectorAll("[data-chapter-jump]");
    expect(items.length).toBeGreaterThanOrEqual(5);
  });

  it("each chapter row carries a numeric chapter id (1..5)", async () => {
    const { default: WallInspectorPage } = await import("../page");
    const { container } = render(React.createElement(WallInspectorPage));
    const ids = Array.from(
      container.querySelectorAll("[data-chapter-jump]"),
    ).map((el) => el.getAttribute("data-chapter-jump"));
    for (const wanted of ["1", "2", "3", "4", "5"]) {
      expect(ids).toContain(wanted);
    }
  });
});

describe("/dev/wall — production guard", () => {
  it("renders a Not-available stub in production", async () => {
    vi.stubEnv("NODE_ENV", "production");
    // Re-import after setting env so the page module re-evaluates.
    vi.resetModules();
    const { default: WallInspectorPage } = await import("../page");
    const { getByText } = render(React.createElement(WallInspectorPage));
    expect(getByText(/Not available in production/i)).toBeInTheDocument();
  });
});
