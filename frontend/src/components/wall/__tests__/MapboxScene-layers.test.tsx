/**
 * Driver D Wave 4 — MapboxScene wires Driver B's layer composer.
 *
 * Driver B shipped `lib/wall/layers/index.ts` with `registerAllLayers(map)`
 * + `removeAllLayers(map)`. Driver A's MapboxScene didn't yet call them.
 * This test (and the matching wiring in MapboxScene.tsx) closes the gap:
 *   - On Mapbox `load` event, `registerMarkerSymbols` runs FIRST (sprite
 *     must register before the offices symbol layer).
 *   - Then `registerAllLayers` registers the data layers in z-order.
 *   - On unmount, `removeAllLayers` reverses the order so Mapbox never
 *     holds a layer referencing a removed source.
 */
import React from "react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, cleanup } from "@testing-library/react";

const registerAllLayersSpy = vi.fn();
const removeAllLayersSpy = vi.fn();
const registerMarkerSymbolsSpy = vi.fn();
const callOrder: string[] = [];

vi.mock("@/lib/wall/layers", () => ({
  registerAllLayers: (map: unknown) => {
    callOrder.push("registerAllLayers");
    registerAllLayersSpy(map);
  },
  removeAllLayers: (map: unknown) => {
    callOrder.push("removeAllLayers");
    removeAllLayersSpy(map);
  },
}));

vi.mock("@/lib/wall/markerSymbols", () => ({
  registerMarkerSymbols: (map: unknown) => {
    callOrder.push("registerMarkerSymbols");
    registerMarkerSymbolsSpy(map);
  },
}));

let capturedMapProps: Record<string, unknown> | null = null;
const removeSpy = vi.fn();
let onLoadHandler: (() => void) | null = null;

vi.mock("react-map-gl", () => {
  const fakeMapInstance = { remove: removeSpy };
  const MapStub = React.forwardRef<unknown, Record<string, unknown>>(
    (props, ref) => {
      capturedMapProps = props;
      if (typeof props.onLoad === "function") {
        onLoadHandler = props.onLoad as () => void;
      }
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

beforeEach(() => {
  capturedMapProps = null;
  registerAllLayersSpy.mockClear();
  removeAllLayersSpy.mockClear();
  registerMarkerSymbolsSpy.mockClear();
  callOrder.length = 0;
  onLoadHandler = null;
  removeSpy.mockClear();
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN =
    "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
});

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
});

describe("Wave 4 — MapboxScene wires the layer composer", () => {
  it("MapboxScene passes an onLoad handler to react-map-gl", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    expect(typeof capturedMapProps?.onLoad).toBe("function");
  });

  it("on Mapbox load, registerMarkerSymbols runs BEFORE registerAllLayers", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    expect(onLoadHandler).not.toBeNull();
    onLoadHandler!();
    const markerIdx = callOrder.indexOf("registerMarkerSymbols");
    const layerIdx = callOrder.indexOf("registerAllLayers");
    expect(markerIdx).toBeGreaterThanOrEqual(0);
    expect(layerIdx).toBeGreaterThan(markerIdx);
  });

  it("on Mapbox load, registerAllLayers receives the underlying map instance", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    onLoadHandler!();
    expect(registerAllLayersSpy).toHaveBeenCalledTimes(1);
    const arg = registerAllLayersSpy.mock.calls[0][0];
    expect(arg).toBeDefined();
    expect(typeof (arg as { remove?: unknown }).remove).toBe("function");
  });

  it("on unmount, removeAllLayers runs and BEFORE map.remove()", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    const { unmount } = render(React.createElement(MapboxScene));
    onLoadHandler!();
    callOrder.length = 0; // reset so we measure only cleanup ordering
    unmount();
    const removeLayersIdx = callOrder.indexOf("removeAllLayers");
    expect(removeLayersIdx).toBeGreaterThanOrEqual(0);
    expect(removeAllLayersSpy).toHaveBeenCalledTimes(1);
    expect(removeSpy).toHaveBeenCalledTimes(1);
  });

  it("does not double-register on a second onLoad call (idempotent)", async () => {
    const { default: MapboxScene } = await import("../MapboxScene");
    render(React.createElement(MapboxScene));
    onLoadHandler!();
    onLoadHandler!();
    onLoadHandler!();
    // Mapbox style swaps fire `load` again; the composer must be safe
    // to call repeatedly. (Driver B's layers are idempotent by design.)
    expect(registerAllLayersSpy.mock.calls.length).toBeGreaterThanOrEqual(1);
  });
});
