import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * W4 Driver B — T4.B.10 tablet scaled-experience contract.
 *
 * The tablet tier (768 ≤ innerWidth < 1024) keeps the cinematic Mapbox
 * experience but at a slightly lower zoom default — judges holding an
 * iPad in landscape get more visible context per frame.
 *
 * Honest uncertainty (C4 in dispatch): we currently do NOT thread a
 * separate tablet zoom through MapboxScene. The existing INITIAL_CAMERA
 * is shared with desktop. This test pins the BEHAVIOR contract — Mapbox
 * mounts on tablet (no regression) — so a future driver who adds the
 * tablet zoom override doesn't accidentally break the mount.
 *
 * The actual "lower zoom" tuning is a one-line change inside
 * `MapboxScene` to read `useResponsiveTier().isTablet` and pass a
 * different initialViewState. Reviewer can retune without breaking
 * this test.
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
  // Fully synchronous shim — see WallContainer-mobile.test.tsx for the
  // rationale. Avoids cross-test leakage of async-loaded real components.
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

const TABLET_PORTRAIT = {
  tier: "tablet" as const,
  isMobile: false,
  isTablet: true,
  isDesktop: false,
  width: 768,
};

const TABLET_LANDSCAPE = {
  tier: "tablet" as const,
  isMobile: false,
  isTablet: true,
  isDesktop: false,
  width: 1023,
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

describe("W4 — tablet viewport keeps cinematic Mapbox (T4.B.10)", () => {
  it("tablet portrait (innerWidth=768) → Mapbox mounts", async () => {
    deviceCapabilityMock.mockReturnValue(HIGH_TIER);
    responsiveTierMock.mockReturnValue(TABLET_PORTRAIT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
    expect(queryByTestId("mobile-wall-fallback")).toBeNull();
  });

  it("tablet landscape (innerWidth=1023) → Mapbox mounts", async () => {
    deviceCapabilityMock.mockReturnValue(HIGH_TIER);
    responsiveTierMock.mockReturnValue(TABLET_LANDSCAPE);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId } = render(React.createElement(WallContainer));
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
  });

  it("tablet with medium tier → Mapbox still mounts (tablet retains cinematic path)", async () => {
    deviceCapabilityMock.mockReturnValue({ ...HIGH_TIER, tier: "medium" });
    responsiveTierMock.mockReturnValue(TABLET_PORTRAIT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("mapbox-scene-stub")).toBeInTheDocument();
    expect(queryByTestId("mobile-wall-fallback")).toBeNull();
  });

  it("tablet without WebGL → static fallback (graceful degrade)", async () => {
    deviceCapabilityMock.mockReturnValue({
      ...HIGH_TIER,
      supportsWebGL: false,
    });
    responsiveTierMock.mockReturnValue(TABLET_PORTRAIT);
    const { default: WallContainer } = await import("../WallContainer");
    const { getByTestId, queryByTestId } = render(
      React.createElement(WallContainer),
    );
    expect(getByTestId("wall-static-fallback")).toBeInTheDocument();
    expect(queryByTestId("mapbox-scene-stub")).toBeNull();
  });
});
