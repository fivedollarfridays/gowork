/**
 * T2.14 — Carlos representative-block pin + path layer test.
 *
 * Layer renders Carlos's home pin (W2) + the 5-week path waypoints (W3
 * Ch7 future-proof). Only the home symbol fades in during W2 Ch3; W3
 * extends visibility to the full path via paint-property mutations.
 */

import { describe, it, expect, vi } from "vitest";
import {
  carlosPathLayer,
  CARLOS_PATH_SOURCE_ID,
  CARLOS_HOME_SYMBOL_ID,
  CARLOS_PATH_LINE_ID,
  buildCarlosPathGeoJSON,
} from "../carlosPath";
import { CARLOS_HOME_PIN, CARLOS_PATH_WAYPOINTS } from "../../paths";

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

describe("carlosPathLayer — config", () => {
  it("declares stable ids", () => {
    expect(CARLOS_PATH_SOURCE_ID).toBe("carlos-path-source");
    expect(CARLOS_HOME_SYMBOL_ID).toBe("carlos-home-symbol");
    expect(CARLOS_PATH_LINE_ID).toBe("carlos-path-line");
  });

  it("registers two layers (home symbol + future-proof path line)", () => {
    expect(carlosPathLayer.layerIds).toContain(CARLOS_HOME_SYMBOL_ID);
    expect(carlosPathLayer.layerIds).toContain(CARLOS_PATH_LINE_ID);
  });

  it("path line is hidden by default (W3 Ch7 will toggle visibility)", () => {
    const line = carlosPathLayer.layerConfigs.find((l) => l.id === CARLOS_PATH_LINE_ID);
    expect(line?.layout?.visibility).toBe("none");
  });
});

describe("carlosPathLayer — buildCarlosPathGeoJSON", () => {
  it("includes the home pin as the first point feature", () => {
    const fc = buildCarlosPathGeoJSON();
    const home = fc.features.find(
      (f) => f.properties.kind === "home" && f.geometry.type === "Point",
    );
    expect(home).toBeDefined();
    expect(home?.properties.piiSafe).toBe(true);
  });

  it("emits a LineString feature wiring all waypoints in order (W3 Ch7 input)", () => {
    const fc = buildCarlosPathGeoJSON();
    const line = fc.features.find((f) => f.geometry.type === "LineString");
    expect(line).toBeDefined();
    if (line && line.geometry.type === "LineString") {
      expect(line.geometry.coordinates.length).toBe(CARLOS_PATH_WAYPOINTS.length);
      // First coord is the home pin.
      expect(line.geometry.coordinates[0][0]).toBeCloseTo(CARLOS_HOME_PIN.longitude, 4);
      expect(line.geometry.coordinates[0][1]).toBeCloseTo(CARLOS_HOME_PIN.latitude, 4);
    }
  });
});

describe("carlosPathLayer — register / remove", () => {
  it("register adds source + 2 layers", () => {
    const map = createMockMap();
    carlosPathLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
    expect(map.addLayer).toHaveBeenCalledTimes(2);
  });

  it("remove tears everything down", () => {
    const map = createMockMap();
    carlosPathLayer.register(map as never);
    carlosPathLayer.remove(map as never);
    expect(map.removeSource).toHaveBeenCalledWith(CARLOS_PATH_SOURCE_ID);
  });
});
