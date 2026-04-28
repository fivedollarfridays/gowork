import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

/**
 * T2.3 + T2.4 + T2.5 — MapboxScene component.
 *
 * The Mapbox React wrapper around `react-map-gl`. Mounts at WallContainer's
 * inner viewport when the token check passes; unmounts cleanly so the
 * WebGL context doesn't leak across client-side route changes (the bug
 * that doesn't show until demo day).
 *
 * Tests verify:
 *   - T2.3: renders the Mapbox Map element with the resolved style URL
 *           and the public token from env
 *   - T2.4: boots into INITIAL_CAMERA without a jarring snap
 *   - T2.5: explicit `map.remove()` cleanup on unmount
 *
 * Mock strategy: `react-map-gl` is replaced with a stub that captures the
 * props it received and emits a synthetic `<div data-testid="mapbox-map">`
 * so jsdom never has to instantiate WebGL.
 */

// Captured props from the most recent <Map /> render. Reset per test.
let capturedMapProps: Record<string, unknown> | null = null;
const removeSpy = vi.fn();
const onLoadSpies: Array<() => void> = [];

vi.mock("react-map-gl", () => {
  // Stub the v7 default export. Real react-map-gl returns a class component
  // wrapping mapbox-gl; we just capture props + render a recognizable div.
  // Forward ref so MapboxScene's useEffect cleanup path can grab the
  // synthetic mapbox-gl instance.
  const fakeMapInstance = { remove: removeSpy };
  const MapStub = React.forwardRef<unknown, Record<string, unknown>>(
    (props, ref) => {
      capturedMapProps = props;
      if (typeof props.onLoad === "function") {
        onLoadSpies.push(props.onLoad as () => void);
      }
      // Bridge the v7 MapRef shape: parent calls `ref.current.getMap()`
      // to reach the underlying mapbox-gl instance.
      if (ref && typeof ref === "object") {
        (ref as { current: unknown }).current = {
          getMap: () => fakeMapInstance,
        };
      } else if (typeof ref === "function") {
        (ref as (v: unknown) => void)({ getMap: () => fakeMapInstance });
      }
      return React.createElement(
        "div",
        {
          "data-testid": "mapbox-map",
          "data-style": props.mapStyle as string,
          "data-token": props.mapboxAccessToken as string,
        },
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

beforeEach(() => {
  capturedMapProps = null;
  removeSpy.mockClear();
  onLoadSpies.length = 0;
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  delete process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
});

describe("T2.3 — MapboxScene mounts react-map-gl with resolved style + token", () => {
  it("renders the Map stub with the public token from env", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    const { getByTestId } = render(React.createElement(MapboxScene));
    const map = getByTestId("mapbox-map");
    expect(map.getAttribute("data-token")).toMatch(/^pk\./);
  });

  it("uses the env-configured style URL when set", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL = "mapbox://styles/gowork/wall-dark-editorial-v1";
    const { default: MapboxScene } = await import("../MapboxScene");
    const { getByTestId } = render(React.createElement(MapboxScene));
    const map = getByTestId("mapbox-map");
    expect(map.getAttribute("data-style")).toBe("mapbox://styles/gowork/wall-dark-editorial-v1");
  });

  it("falls back to mapbox dark-v11 when the env style URL is unset", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
    const { default: MapboxScene } = await import("../MapboxScene");
    const { getByTestId } = render(React.createElement(MapboxScene));
    const map = getByTestId("mapbox-map");
    expect(map.getAttribute("data-style")).toBe("mapbox://styles/mapbox/dark-v11");
  });
});

describe("T2.4 — MapboxScene boots into INITIAL_CAMERA", () => {
  it("passes initialViewState matching the Fort Worth centroid", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    const initialViewState = capturedMapProps?.initialViewState as
      | { longitude: number; latitude: number; zoom: number; pitch: number; bearing: number }
      | undefined;
    expect(initialViewState).toBeDefined();
    expect(initialViewState!.longitude).toBeCloseTo(-97.3308, 3);
    expect(initialViewState!.latitude).toBeCloseTo(32.7555, 3);
    expect(initialViewState!.zoom).toBe(11);
    expect(initialViewState!.pitch).toBe(0);
    expect(initialViewState!.bearing).toBe(0);
  });
});

describe("T2.3 — MapboxScene suppresses default interactive controls", () => {
  it("disables dragRotate / scrollZoom by default (chapter scroll drives camera)", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    // dragPan + touchZoomRotate stay on for accessibility (touch users
    // expect pinch-zoom). dragRotate + scrollZoom are off so the page
    // scroll isn't hijacked by the map.
    expect(capturedMapProps?.dragRotate).toBe(false);
    expect(capturedMapProps?.scrollZoom).toBe(false);
  });

  it("renders the AttributionControl (legal Mapbox ToS requirement)", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    const { getByTestId } = render(React.createElement(MapboxScene));
    expect(getByTestId("mapbox-attribution")).toBeInTheDocument();
  });
});

describe("T2.5 — MapboxScene cleanup on unmount", () => {
  it("calls map.remove() when the component unmounts", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    const { unmount } = render(React.createElement(MapboxScene));

    // The mock's forwarded ref already wired `getMap()` to the
    // shared `removeSpy`. Unmount triggers the useEffect cleanup.
    unmount();
    expect(removeSpy).toHaveBeenCalled();
  });
});
