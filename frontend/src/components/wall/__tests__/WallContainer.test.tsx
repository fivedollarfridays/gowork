import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * T2.2 — WallContainer integration test.
 *
 * The orchestrator that decides Mapbox-vs-fallback, mounts the React
 * Context that chapters subscribe to, and lazy-imports the heavy
 * `MapboxScene` after the title sequence completes.
 *
 * Test contract:
 *   - When `validateToken()` returns true → renders `<MapboxScene>` slot
 *   - When false → renders the static fallback element with branding
 *   - Provides a `WallContext` value chapters can read
 *   - Mounts `useScrollProgress` once at container level (single source)
 *
 * Mock strategy: stub `MapboxScene` entirely so this test stays focused
 * on container orchestration; we don't re-test Mapbox here.
 */

vi.mock("../MapboxScene", () => ({
  default: () => React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
}));

// Default to a high-tier device with WebGL — the Spotlight tier gate
// (Wave 5) routes low-tier or WebGL-less devices to the fallback. Tests
// here focus on token + composition; tier behavior has its own file.
vi.mock("@/hooks/useDeviceCapability", () => ({
  useDeviceCapability: () => ({
    tier: "high",
    supportsWebGL: true,
    isMobile: false,
    deviceMemoryGb: 16,
    hardwareConcurrency: 12,
    prefersReducedData: false,
  }),
}));

// `next/dynamic` returns a placeholder until the import resolves — in tests
// we want the resolved component immediately so assertions don't have to
// await the microtask queue. Swap dynamic for a synchronous shim.
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    let Component: React.ComponentType | null = null;
    // Trigger the import immediately and store the module's default.
    void loader().then((mod) => {
      Component = mod.default;
    });
    const Wrapper: React.FC<Record<string, unknown>> = (props) => {
      if (Component) return React.createElement(Component, props);
      // Fallback: render the test-stub synchronously.
      return React.createElement("div", { "data-testid": "mapbox-scene-stub" });
    };
    return Wrapper;
  },
}));

beforeEach(() => {
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("T2.2 — WallContainer renders MapboxScene when token valid", () => {
  it("mounts <MapboxScene> when token check passes", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
  });

  it("does NOT render the static fallback when token valid", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    const { default: WallContainer } = await import("../WallContainer");
    const { queryByTestId } = render(React.createElement(WallContainer));
    expect(queryByTestId("wall-static-fallback")).toBeNull();
  });
});

describe("T2.2 — WallContainer falls back to static when token missing/invalid", () => {
  it("renders the static fallback when env var unset", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
  });

  it("static fallback carries branded text (GoWork · Fort Worth, TX)", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    const fb = getByTestId("wall-static-fallback");
    expect(fb.textContent).toMatch(/GoWork/i);
    expect(fb.textContent).toMatch(/Fort Worth/i);
  });

  it("static fallback does NOT mount MapboxScene", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { default: WallContainer } = await import("../WallContainer");
    const { queryByTestId } = render(React.createElement(WallContainer));
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });

  it("static fallback rejects sk. (secret) tokens", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "sk.secret-never-shipped";
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
  });
});

describe("T2.2 — WallContext provides scroll/chapter state to descendants", () => {
  it("exposes a WallContext consumer hook (useWallContext) returning a value", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    const { default: WallContainer, useWallContext } = await import("../WallContainer");
    let captured: ReturnType<typeof useWallContext> | null = null;

    function Probe() {
      captured = useWallContext();
      return null;
    }

    render(
      React.createElement(WallContainer, null, React.createElement(Probe)),
    );

    expect(captured).not.toBeNull();
    expect(typeof captured!.currentChapter).toBe("number");
    expect(typeof captured!.chapterProgress).toBe("number");
    expect(typeof captured!.isMapboxMounted).toBe("boolean");
  });
});
