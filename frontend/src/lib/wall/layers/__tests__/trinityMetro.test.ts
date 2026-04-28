/**
 * T2.11 — Trinity Metro GTFS → GeoJSON polyline layer.
 *
 * Layer renders bus routes (cyan default, amber when highlighted via
 * Mapbox feature-state). Route ids 4 and 6 are first-class — they are
 * Carlos's commute (referenced in Ch4a / Ch4b editorial).
 */

import { describe, it, expect, vi } from "vitest";
import {
  trinityMetroLayer,
  TRINITY_METRO_SOURCE_ID,
  TRINITY_METRO_LINE_ID,
  TRINITY_METRO_HIGHLIGHTED_ROUTE_IDS,
} from "../trinityMetro";

interface MockMap {
  addSource: ReturnType<typeof vi.fn>;
  addLayer: ReturnType<typeof vi.fn>;
  removeLayer: ReturnType<typeof vi.fn>;
  removeSource: ReturnType<typeof vi.fn>;
  getLayer: ReturnType<typeof vi.fn>;
  getSource: ReturnType<typeof vi.fn>;
}

function createMockMap(): MockMap {
  const sources = new Set<string>();
  const layers = new Set<string>();
  return {
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
}

describe("trinityMetroLayer — config", () => {
  it("declares stable ids", () => {
    expect(TRINITY_METRO_SOURCE_ID).toBe("trinity-metro-source");
    expect(TRINITY_METRO_LINE_ID).toBe("trinity-metro-line");
  });

  it("source points at committed offline GeoJSON (no runtime HTTP fetch)", () => {
    expect(trinityMetroLayer.sourceConfig.type).toBe("geojson");
    expect(trinityMetroLayer.sourceConfig.data).toMatch(
      /\/data\/wall\/trinity-metro\.geojson$/,
    );
  });

  it("highlighted route ids include Bus 4 and Bus 6 (Carlos's commute)", () => {
    expect(TRINITY_METRO_HIGHLIGHTED_ROUTE_IDS).toContain("4");
    expect(TRINITY_METRO_HIGHLIGHTED_ROUTE_IDS).toContain("6");
  });

  it("layer config uses no hardcoded hex (design tokens via OKLCH literals)", () => {
    const paint = JSON.stringify(
      trinityMetroLayer.layerConfigs.find((l) => l.id === TRINITY_METRO_LINE_ID)?.paint ?? {},
    );
    expect(paint).not.toMatch(/#[0-9a-fA-F]{3,8}/);
  });

  it("layer paint is a feature-state-aware expression so highlight switches color without re-render", () => {
    const layer = trinityMetroLayer.layerConfigs.find((l) => l.id === TRINITY_METRO_LINE_ID);
    const paintStr = JSON.stringify(layer?.paint ?? {});
    expect(paintStr).toMatch(/feature-state|case|match/);
  });
});

describe("trinityMetroLayer — register / remove", () => {
  it("register adds source + 1 line layer", () => {
    const map = createMockMap();
    trinityMetroLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
    expect(map.addLayer).toHaveBeenCalledTimes(1);
  });

  it("register is idempotent", () => {
    const map = createMockMap();
    trinityMetroLayer.register(map as never);
    trinityMetroLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
    expect(map.addLayer).toHaveBeenCalledTimes(1);
  });

  it("remove tears down layers + source when present", () => {
    const map = createMockMap();
    trinityMetroLayer.register(map as never);
    trinityMetroLayer.remove(map as never);
    expect(map.removeLayer).toHaveBeenCalledWith(TRINITY_METRO_LINE_ID);
    expect(map.removeSource).toHaveBeenCalledWith(TRINITY_METRO_SOURCE_ID);
  });
});
