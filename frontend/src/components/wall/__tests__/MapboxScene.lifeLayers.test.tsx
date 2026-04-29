import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup, act } from "@testing-library/react";

/**
 * T4.A.1 + T4.A.3 — MapboxScene life-layers wiring.
 *
 * Confirms MapboxScene mounts:
 *   1. The map cursor flashlight overlay (T4.A.3)
 *   2. The time-of-day sky setter (T4.A.1) which calls setPaintProperty
 *      on the underlying map after `onLoad` fires.
 *
 * The react-map-gl mock here is a copy of MapboxScene.test.tsx's stub
 * but extends the fake map instance with `setPaintProperty` + `setLight`
 * so we can spy them.
 */

let capturedMapProps: Record<string, unknown> | null = null;
const removeSpy = vi.fn();
const setPaintPropertySpy = vi.fn();
const setLightSpy = vi.fn();

vi.mock("react-map-gl", () => {
  const fakeMapInstance = {
    remove: removeSpy,
    setPaintProperty: setPaintPropertySpy,
    setLight: setLightSpy,
    addSource: vi.fn(),
    addLayer: vi.fn(),
    // Commit 2b9adca added a sky-layer guard to useMapboxSkyForTimeOfDay
    // — the runtime now skips setPaintProperty('sky', ...) unless
    // map.getLayer('sky') returns truthy. The fake map opts INTO the
    // sky-layer code path so the spy can fire.
    getLayer: vi.fn(() => ({ id: "sky", type: "sky" })),
  };
  const MapStub = React.forwardRef<unknown, Record<string, unknown>>(
    (props, ref) => {
      capturedMapProps = props;
      if (ref && typeof ref === "object") {
        (ref as { current: unknown }).current = {
          getMap: () => fakeMapInstance,
        };
      } else if (typeof ref === "function") {
        (ref as (v: unknown) => void)({ getMap: () => fakeMapInstance });
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

beforeEach(() => {
  capturedMapProps = null;
  removeSpy.mockClear();
  setPaintPropertySpy.mockClear();
  setLightSpy.mockClear();
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN =
    "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  vi.restoreAllMocks();
});

describe("MapboxScene life-layers wiring (T4.A.1 + T4.A.3)", () => {
  it("renders the map cursor flashlight overlay", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    const { container } = render(React.createElement(MapboxScene));
    const flashlight = container.querySelector(
      '[data-testid="map-cursor-flashlight"]',
    );
    expect(flashlight).not.toBeNull();
  });

  it("calls map.setPaintProperty('sky', ...) after onLoad fires", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    // Fire onLoad — emulates Mapbox's real-world load event.
    const onLoad = capturedMapProps?.onLoad as (() => void) | undefined;
    expect(typeof onLoad).toBe("function");
    act(() => {
      onLoad?.();
    });
    // Sky setter is wired to a useEffect that runs on mount with the
    // map ref, but the map only becomes available after onLoad sets the
    // local state.
    expect(setPaintPropertySpy).toHaveBeenCalled();
    const skyCalls = setPaintPropertySpy.mock.calls.filter(
      (c) => c[0] === "sky",
    );
    expect(skyCalls.length).toBeGreaterThan(0);
  });

  it("calls map.setLight after onLoad", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    const onLoad = capturedMapProps?.onLoad as (() => void) | undefined;
    act(() => {
      onLoad?.();
    });
    expect(setLightSpy).toHaveBeenCalled();
  });
});
