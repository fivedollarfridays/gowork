/**
 * T2.17 / T2.60 — Layer composer registration test.
 *
 * Composer registers/removes all 5 W2 data layers in z-order:
 *   1. zip boundaries (bottom)
 *   2. trinity metro routes
 *   3. tarrant offices (symbol)
 *   4. carlos path (home + W3-future-proof line)
 *   5. jobs by zip (top)
 *
 * Cleanup must reverse the order to keep Mapbox happy if a higher layer
 * references a lower source.
 */

import { describe, it, expect, vi } from "vitest";
import {
  registerAllLayers,
  removeAllLayers,
  WALL_LAYER_ORDER,
} from "../index";

interface TrackingMap {
  addSource: ReturnType<typeof vi.fn>;
  addLayer: ReturnType<typeof vi.fn>;
  removeLayer: ReturnType<typeof vi.fn>;
  removeSource: ReturnType<typeof vi.fn>;
  getLayer: ReturnType<typeof vi.fn>;
  getSource: ReturnType<typeof vi.fn>;
  callOrder: string[];
}

function createTrackingMap(): TrackingMap {
  const sources = new Set<string>();
  const layers = new Set<string>();
  const callOrder: string[] = [];
  return {
    callOrder,
    addSource: vi.fn((id: string) => {
      sources.add(id);
      callOrder.push(`addSource:${id}`);
    }) as never,
    addLayer: vi.fn((layer: { id: string }) => {
      layers.add(layer.id);
      callOrder.push(`addLayer:${layer.id}`);
    }) as never,
    removeLayer: vi.fn((id: string) => {
      layers.delete(id);
      callOrder.push(`removeLayer:${id}`);
    }) as never,
    removeSource: vi.fn((id: string) => {
      sources.delete(id);
      callOrder.push(`removeSource:${id}`);
    }) as never,
    getLayer: vi.fn((id: string) => (layers.has(id) ? { id } : undefined)) as never,
    getSource: vi.fn((id: string) => (sources.has(id) ? { id } : undefined)) as never,
  };
}

describe("layers composer — registerAllLayers", () => {
  it("ships the documented z-order (zip → metro → offices → carlos → jobs)", () => {
    expect(WALL_LAYER_ORDER).toEqual([
      "zipBoundaries",
      "trinityMetro",
      "offices",
      "carlosPath",
      "jobsByZip",
    ]);
  });

  it("registers every layer once", () => {
    const map = createTrackingMap();
    registerAllLayers(map as never);
    // Each layer adds 1 source.
    expect(map.addSource).toHaveBeenCalledTimes(5);
  });

  it("source registration order matches WALL_LAYER_ORDER", () => {
    const map = createTrackingMap();
    registerAllLayers(map as never);
    const sourceCalls = map.callOrder.filter((c) => c.startsWith("addSource:"));
    expect(sourceCalls).toEqual([
      "addSource:zip-76119-source",
      "addSource:trinity-metro-source",
      "addSource:tarrant-offices-source",
      "addSource:carlos-path-source",
      "addSource:jobs-by-zip-source",
    ]);
  });

  it("registerAllLayers is idempotent", () => {
    const map = createTrackingMap();
    registerAllLayers(map as never);
    registerAllLayers(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(5);
  });
});

describe("layers composer — removeAllLayers", () => {
  it("removes sources in reverse order", () => {
    const map = createTrackingMap();
    registerAllLayers(map as never);
    removeAllLayers(map as never);
    const sourceRemoves = map.callOrder.filter((c) =>
      c.startsWith("removeSource:"),
    );
    expect(sourceRemoves).toEqual([
      "removeSource:jobs-by-zip-source",
      "removeSource:carlos-path-source",
      "removeSource:tarrant-offices-source",
      "removeSource:trinity-metro-source",
      "removeSource:zip-76119-source",
    ]);
  });

  it("removeAllLayers is idempotent — safe to call before register", () => {
    const map = createTrackingMap();
    expect(() => removeAllLayers(map as never)).not.toThrow();
    expect(map.removeSource).not.toHaveBeenCalled();
  });
});
