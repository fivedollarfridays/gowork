/**
 * T2.13 — FW ZIP 76119 boundary layer config test.
 *
 * The layer module exports:
 *   - sourceConfig: Mapbox source spec pointing at committed GeoJSON
 *   - layerConfigs: array of fill + line layer configs (z-ordered)
 *   - register(map): adds source + layers to a Mapbox map
 *   - remove(map): removes layers + source
 *
 * Tests use a mocked Mapbox map (Driver A's MapboxScene wires a real one).
 */

import { describe, it, expect, vi } from "vitest";
import {
  zipBoundariesLayer,
  ZIP_BOUNDARIES_SOURCE_ID,
  ZIP_BOUNDARIES_FILL_ID,
  ZIP_BOUNDARIES_LINE_ID,
} from "../zipBoundaries";

interface MockMap {
  addSource: ReturnType<typeof vi.fn<(id: string, source: { type: string }) => void>>;
  addLayer: ReturnType<typeof vi.fn<(layer: { id: string }) => void>>;
  removeLayer: ReturnType<typeof vi.fn<(id: string) => void>>;
  removeSource: ReturnType<typeof vi.fn<(id: string) => void>>;
  getLayer: ReturnType<typeof vi.fn<(id: string) => { id: string } | undefined>>;
  getSource: ReturnType<typeof vi.fn<(id: string) => { id: string } | undefined>>;
}

function createMockMap(): MockMap {
  // Track registered sources/layers so the mock matches Mapbox semantics
  // (idempotent register, present-aware remove).
  const sources = new Set<string>();
  const layers = new Set<string>();
  const map: MockMap = {
    addSource: vi.fn((id: string) => {
      sources.add(id);
    }) as never,
    addLayer: vi.fn((layer: { id: string }) => {
      layers.add(layer.id);
    }) as never,
    removeLayer: vi.fn((id: string) => {
      layers.delete(id);
    }) as never,
    removeSource: vi.fn((id: string) => {
      sources.delete(id);
    }) as never,
    getLayer: vi.fn((id: string) => (layers.has(id) ? { id } : undefined)) as never,
    getSource: vi.fn((id: string) => (sources.has(id) ? { id } : undefined)) as never,
  };
  return map;
}

function createPrefilledMockMap(): MockMap {
  // For "remove" tests: simulate a map that already has the layer
  // registered so the cleanup branch fires.
  const map = createMockMap();
  map.addSource("zip-76119-source", { type: "geojson" });
  map.addLayer({ id: "zip-76119-fill" });
  map.addLayer({ id: "zip-76119-line" });
  return map;
}

describe("zipBoundariesLayer — config", () => {
  it("declares stable source + layer ids", () => {
    expect(ZIP_BOUNDARIES_SOURCE_ID).toBe("zip-76119-source");
    expect(ZIP_BOUNDARIES_FILL_ID).toBe("zip-76119-fill");
    expect(ZIP_BOUNDARIES_LINE_ID).toBe("zip-76119-line");
  });

  it("source points at committed offline GeoJSON (no runtime fetch elsewhere)", () => {
    expect(zipBoundariesLayer.sourceConfig.type).toBe("geojson");
    expect(zipBoundariesLayer.sourceConfig.data).toMatch(
      /\/data\/wall\/zip-76119\.geojson$/,
    );
  });

  it("fill layer uses design-token paint (no hardcoded hex)", () => {
    const fill = zipBoundariesLayer.layerConfigs.find((l) => l.id === ZIP_BOUNDARIES_FILL_ID);
    expect(fill).toBeDefined();
    expect(fill?.type).toBe("fill");
    const paint = JSON.stringify(fill?.paint ?? {});
    expect(paint).not.toMatch(/#[0-9a-fA-F]{3,8}/);
  });

  it("line layer uses design-token paint (no hardcoded hex)", () => {
    const line = zipBoundariesLayer.layerConfigs.find((l) => l.id === ZIP_BOUNDARIES_LINE_ID);
    expect(line).toBeDefined();
    expect(line?.type).toBe("line");
    const paint = JSON.stringify(line?.paint ?? {});
    expect(paint).not.toMatch(/#[0-9a-fA-F]{3,8}/);
  });
});

describe("zipBoundariesLayer — register / remove", () => {
  it("register adds source + 2 layers", () => {
    const map = createMockMap();
    zipBoundariesLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledWith(
      ZIP_BOUNDARIES_SOURCE_ID,
      expect.any(Object),
    );
    expect(map.addLayer).toHaveBeenCalledTimes(2);
  });

  it("remove removes layers in reverse order then source", () => {
    const map = createPrefilledMockMap();
    zipBoundariesLayer.remove(map as never);
    expect(map.removeLayer).toHaveBeenCalledWith(ZIP_BOUNDARIES_LINE_ID);
    expect(map.removeLayer).toHaveBeenCalledWith(ZIP_BOUNDARIES_FILL_ID);
    expect(map.removeSource).toHaveBeenCalledWith(ZIP_BOUNDARIES_SOURCE_ID);
  });

  it("remove is idempotent — does not throw on a clean map", () => {
    const map = createMockMap();
    expect(() => zipBoundariesLayer.remove(map as never)).not.toThrow();
    expect(map.removeLayer).not.toHaveBeenCalled();
    expect(map.removeSource).not.toHaveBeenCalled();
  });

  it("register is idempotent — does not re-add an existing source", () => {
    const map = createMockMap();
    zipBoundariesLayer.register(map as never);
    zipBoundariesLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
  });
});
