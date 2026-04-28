import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * W4 Driver D — T4.D.2 tablet-specific Mapbox zoom.
 *
 * Driver A's deferred constraint: "Threading a tablet-specific zoom into
 * MapboxScene is one prop away — read `useResponsiveTier().isTablet` inside
 * MapboxScene to drop zoom to 10 for tablets without breaking the desktop
 * contract."
 *
 * Spec:
 *   - Desktop (tier=desktop) → zoom 11 (existing INITIAL_CAMERA contract).
 *   - Tablet (tier=tablet)   → zoom 10 (one less, more visible context).
 *   - Mobile path is gated by WallContainer (mobile → MobileWallFallback)
 *     so MapboxScene itself never mounts on mobile.
 */

// Reuse the same react-map-gl stub shape from MapboxScene.test.tsx.
let capturedMapProps: Record<string, unknown> | null = null;
const removeSpy = vi.fn();

vi.mock("react-map-gl", () => {
  const fakeMapInstance = { remove: removeSpy };
  const MapStub = React.forwardRef<unknown, Record<string, unknown>>(
    (props, ref) => {
      capturedMapProps = props;
      if (ref && typeof ref === "object") {
        (ref as { current: unknown }).current = {
          getMap: () => fakeMapInstance,
        };
      }
      return React.createElement(
        "div",
        { "data-testid": "mapbox-map" },
        props.children as React.ReactNode,
      );
    },
  );
  MapStub.displayName = "MapboxMapStub";
  return {
    default: MapStub,
    Map: MapStub,
    AttributionControl: () =>
      React.createElement("div", { "data-testid": "mapbox-attribution" }),
  };
});

const responsiveTierMock = vi.fn();
vi.mock("@/hooks/useResponsiveTier", () => ({
  useResponsiveTier: () => responsiveTierMock(),
}));

const DESKTOP = {
  tier: "desktop" as const,
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  width: 1440,
};

const TABLET = {
  tier: "tablet" as const,
  isMobile: false,
  isTablet: true,
  isDesktop: false,
  width: 900,
};

beforeEach(() => {
  capturedMapProps = null;
  removeSpy.mockClear();
  responsiveTierMock.mockReset();
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN =
    "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("T4.D.2 — MapboxScene tablet-specific zoom override", () => {
  it("desktop tier mounts at zoom 11 (no regression)", async () => {
    responsiveTierMock.mockReturnValue(DESKTOP);
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    const initialViewState = capturedMapProps?.initialViewState as
      | { zoom: number }
      | undefined;
    expect(initialViewState?.zoom).toBe(11);
  });

  it("tablet tier mounts at zoom 10 (more visible context)", async () => {
    responsiveTierMock.mockReturnValue(TABLET);
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    const initialViewState = capturedMapProps?.initialViewState as
      | { zoom: number }
      | undefined;
    expect(initialViewState?.zoom).toBe(10);
  });

  it("tablet override does not affect longitude/latitude/pitch/bearing", async () => {
    responsiveTierMock.mockReturnValue(TABLET);
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    const initialViewState = capturedMapProps?.initialViewState as
      | {
          longitude: number;
          latitude: number;
          pitch: number;
          bearing: number;
        }
      | undefined;
    expect(initialViewState?.longitude).toBeCloseTo(-97.3308, 3);
    expect(initialViewState?.latitude).toBeCloseTo(32.7555, 3);
    expect(initialViewState?.pitch).toBe(0);
    expect(initialViewState?.bearing).toBe(0);
  });
});
