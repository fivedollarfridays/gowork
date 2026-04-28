/**
 * T2.12 / T2.128 — Tarrant offices layer config + W3 future-proofing.
 *
 * Layer paint expression supports 4 office states (default | highlighted
 * | visited | current). W2 renders default + highlighted; W3 Ch7 enables
 * the other two without re-shipping the layer module.
 */

import { describe, it, expect, vi } from "vitest";
import {
  officesLayer,
  OFFICES_SOURCE_ID,
  OFFICES_SYMBOL_ID,
  buildOfficesGeoJSON,
} from "../offices";
import { TARRANT_OFFICES } from "../../officeRegistry";

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

describe("officesLayer — config", () => {
  it("declares stable ids", () => {
    expect(OFFICES_SOURCE_ID).toBe("tarrant-offices-source");
    expect(OFFICES_SYMBOL_ID).toBe("tarrant-offices-symbol");
  });

  it("layer paint supports all 4 office states (W3 future-proof)", () => {
    const layer = officesLayer.layerConfigs.find((l) => l.id === OFFICES_SYMBOL_ID);
    const paintStr = JSON.stringify(layer?.paint ?? {});
    // Match expression should reference all 4 states by name.
    expect(paintStr).toMatch(/default/);
    expect(paintStr).toMatch(/highlighted/);
    expect(paintStr).toMatch(/visited/);
    expect(paintStr).toMatch(/current/);
  });

  it("layer renders symbols (uses iconImage from sprite per category)", () => {
    const layer = officesLayer.layerConfigs.find((l) => l.id === OFFICES_SYMBOL_ID);
    expect(layer?.type).toBe("symbol");
    const layoutStr = JSON.stringify(layer?.layout ?? {});
    expect(layoutStr).toMatch(/icon-image/);
  });
});

describe("officesLayer — buildOfficesGeoJSON", () => {
  it("produces a FeatureCollection with one Point per registry office", () => {
    const fc = buildOfficesGeoJSON();
    expect(fc.type).toBe("FeatureCollection");
    expect(fc.features.length).toBe(TARRANT_OFFICES.length);
    for (const f of fc.features) {
      expect(f.type).toBe("Feature");
      expect(f.geometry.type).toBe("Point");
      expect(f.geometry.coordinates.length).toBe(2);
    }
  });

  it("each feature carries primary-source provenance + state for W3", () => {
    const fc = buildOfficesGeoJSON();
    for (const f of fc.features) {
      expect(f.properties.id).toBeTruthy();
      expect(f.properties.category).toBeTruthy();
      expect(f.properties.address).toBeTruthy();
      expect(f.properties.sourceUrl).toMatch(/^https?:\/\//);
      expect(f.properties.state).toBe("default");
    }
  });
});

describe("officesLayer — register / remove", () => {
  it("register adds source + 1 symbol layer", () => {
    const map = createMockMap();
    officesLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
    expect(map.addLayer).toHaveBeenCalledTimes(1);
  });

  it("remove tears down layer + source after register", () => {
    const map = createMockMap();
    officesLayer.register(map as never);
    officesLayer.remove(map as never);
    expect(map.removeLayer).toHaveBeenCalledWith(OFFICES_SYMBOL_ID);
    expect(map.removeSource).toHaveBeenCalledWith(OFFICES_SOURCE_ID);
  });
});
