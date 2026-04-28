import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * Spotlight Invention (Wave 5 mobile fallback) — device-tier gate.
 *
 * The Mapbox + 3D-buildings render is expensive on low-tier devices
 * (Pixel 4a on 3G, ancient Android). The brief deferred a "proper" mobile
 * fallback to W4, but a thin tier gate in W2 keeps Carlos's-on-3G
 * experience beautiful, not broken.
 *
 * Contract:
 *   - tier === "low" OR !supportsWebGL → static fallback (same path as
 *     missing token — branded, accessible, not a crashed map)
 *   - tier === "medium" or "high" with WebGL → Mapbox mounts as before
 *
 * Why W2 instead of W4: it's two lines and one prop on the existing gate.
 * W4 will graduate this to the "scaled-down map" path; W2 ships the
 * fallback so a tier-low reviewer sees the still-image, not stalled JS.
 */

const deviceCapabilityMock = vi.fn();

vi.mock("@/hooks/useDeviceCapability", () => ({
  useDeviceCapability: () => deviceCapabilityMock(),
}));

vi.mock("../MapboxScene", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
}));

// Wave 2 (Driver D) — chapters now render inside WallContainer. Mock the
// translation surface so this composition test stays focused on
// container orchestration.
vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: "en",
    setLocale: () => undefined,
  }),
  TranslationProvider: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    let Component: React.ComponentType | null = null;
    void loader().then((mod) => {
      Component = mod.default;
    });
    const Wrapper: React.FC<Record<string, unknown>> = (props) => {
      if (Component) return React.createElement(Component, props);
      return React.createElement("div", { "data-testid": "mapbox-scene-stub" });
    };
    return Wrapper;
  },
}));

beforeEach(() => {
  deviceCapabilityMock.mockReset();
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("Spotlight — WallContainer renders fallback on low-tier devices", () => {
  it("low-tier device with WebGL → static fallback (no Mapbox download)", async () => {
    deviceCapabilityMock.mockReturnValue({
      tier: "low",
      supportsWebGL: true,
      isMobile: true,
      deviceMemoryGb: 2,
      hardwareConcurrency: 2,
      prefersReducedData: false,
    });
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });

  it("medium-tier device WITHOUT WebGL support → static fallback", async () => {
    deviceCapabilityMock.mockReturnValue({
      tier: "medium",
      supportsWebGL: false,
      isMobile: false,
      deviceMemoryGb: 4,
      hardwareConcurrency: 4,
      prefersReducedData: false,
    });
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });

  it("medium-tier with WebGL → Mapbox mounts (standard path)", async () => {
    deviceCapabilityMock.mockReturnValue({
      tier: "medium",
      supportsWebGL: true,
      isMobile: true,
      deviceMemoryGb: 4,
      hardwareConcurrency: 4,
      prefersReducedData: false,
    });
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
  });

  it("high-tier with WebGL → Mapbox mounts (standard path)", async () => {
    deviceCapabilityMock.mockReturnValue({
      tier: "high",
      supportsWebGL: true,
      isMobile: false,
      deviceMemoryGb: 16,
      hardwareConcurrency: 12,
      prefersReducedData: false,
    });
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
  });

  it("prefers-reduced-data (Save-Data header set) → fallback", async () => {
    deviceCapabilityMock.mockReturnValue({
      tier: "low", // classifyTier returns "low" when saveData=true
      supportsWebGL: true,
      isMobile: true,
      deviceMemoryGb: 8,
      hardwareConcurrency: 8,
      prefersReducedData: true,
    });
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });
});
