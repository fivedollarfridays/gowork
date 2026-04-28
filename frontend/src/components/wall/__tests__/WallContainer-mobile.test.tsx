import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * W4 Driver B — T4.B.9 mobile + tablet viewport gating in WallContainer.
 *
 * Contract additions on top of the W2 tier gate:
 *   - Mobile viewport (innerWidth < 768) → MobileWallFallback rendered.
 *     Mapbox is NOT downloaded on mobile under any circumstance — even
 *     a high-tier iPhone running Safari is gated to the editorial-scroll
 *     fallback because Mapbox at zoom 11 with 3D buildings is brutal on
 *     a 360px column.
 *   - Tablet viewport (768 ≤ innerWidth < 1024) → Mapbox mounts as on
 *     desktop (no regression). C4 honest-uncertainty: a future driver
 *     can opt-in to a lower zoom default for tablet without changing
 *     this gate.
 *   - Desktop viewport (≥ 1024) → unchanged from W2.
 */

const deviceCapabilityMock = vi.fn();
const responsiveTierMock = vi.fn();

vi.mock("@/hooks/useDeviceCapability", () => ({
  useDeviceCapability: () => deviceCapabilityMock(),
}));

vi.mock("@/hooks/useResponsiveTier", () => ({
  useResponsiveTier: () => responsiveTierMock(),
}));

vi.mock("../MapboxScene", () => ({
  default: () =>
    React.createElement("div", { "data-testid": "mapbox-scene-stub" }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}));

vi.mock("@/hooks/useTranslation", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    locale: "en",
    setLocale: () => undefined,
    switchLocale: () => undefined,
  }),
  TranslationProvider: ({ children }: { children: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}));

vi.mock("next/dynamic", () => ({
  // Fully synchronous shim — never resolves the real loader. Each call
  // returns a stable stub component. This avoids cross-test leakage
  // where an async-resolved real component shows up in the NEXT test's
  // tree (causing duplicate testids).
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    const loaderSrc = String(loader);
    const isMapbox = /MapboxScene/.test(loaderSrc);
    const isCliffChart = /BenefitsCliffChart/.test(loaderSrc);
    const fallbackTestId = isMapbox
      ? "mapbox-scene-stub"
      : isCliffChart
        ? "cliff-chart-dynamic-stub"
        : "dynamic-stub";
    const Stub: React.FC = () =>
      React.createElement("div", { "data-testid": fallbackTestId });
    return Stub;
  },
}));

const HIGH_TIER = {
  tier: "high" as const,
  supportsWebGL: true,
  isMobile: false,
  deviceMemoryGb: 16,
  hardwareConcurrency: 12,
  prefersReducedData: false,
};

const MOBILE_VIEWPORT = {
  tier: "mobile" as const,
  isMobile: true,
  isTablet: false,
  isDesktop: false,
  width: 360,
};

const TABLET_VIEWPORT = {
  tier: "tablet" as const,
  isMobile: false,
  isTablet: true,
  isDesktop: false,
  width: 900,
};

const DESKTOP_VIEWPORT = {
  tier: "desktop" as const,
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  width: 1440,
};

beforeEach(() => {
  deviceCapabilityMock.mockReset();
  responsiveTierMock.mockReset();
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN =
    "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("W4 — WallContainer mobile-viewport gating (T4.B.9)", () => {
  it("mobile viewport → MobileWallFallback rendered (no Mapbox)", async () => {
    deviceCapabilityMock.mockReturnValue(HIGH_TIER);
    responsiveTierMock.mockReturnValue(MOBILE_VIEWPORT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mobile-wall-fallback")).toBeInTheDocument();
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });

  it("mobile viewport with low tier → still MobileWallFallback", async () => {
    deviceCapabilityMock.mockReturnValue({
      ...HIGH_TIER,
      tier: "low",
    });
    responsiveTierMock.mockReturnValue(MOBILE_VIEWPORT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mobile-wall-fallback")).toBeInTheDocument();
    expect(queryByTestId("wall-static-fallback")).toBeNull();
  });

  it("tablet viewport with high tier → Mapbox mounts (no regression)", async () => {
    deviceCapabilityMock.mockReturnValue(HIGH_TIER);
    responsiveTierMock.mockReturnValue(TABLET_VIEWPORT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
    expect(queryByTestId("mobile-wall-fallback")).toBeNull();
  });

  it("desktop viewport with high tier → Mapbox mounts (standard path)", async () => {
    deviceCapabilityMock.mockReturnValue(HIGH_TIER);
    responsiveTierMock.mockReturnValue(DESKTOP_VIEWPORT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
    expect(queryByTestId("mobile-wall-fallback")).toBeNull();
  });

  it("tablet with low tier → static fallback (tier wins over tablet)", async () => {
    deviceCapabilityMock.mockReturnValue({ ...HIGH_TIER, tier: "low" });
    responsiveTierMock.mockReturnValue(TABLET_VIEWPORT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
    expect(queryByTestId("mobile-wall-fallback")).toBeNull();
  });
});
