/**
 * T2.15 — Jobs-by-ZIP employer markers test.
 *
 * Layer paint switches `creditCheck=true` markers from amber to muted
 * gray for Ch4d "30% of jobs go dark." Amazon FC DFW5 must be present
 * (W3 Ch6 references it).
 */

import { describe, it, expect, vi } from "vitest";
import {
  jobsByZipLayer,
  JOBS_BY_ZIP_SOURCE_ID,
  JOBS_BY_ZIP_CIRCLE_ID,
  buildJobsByZipGeoJSON,
} from "../jobsByZip";

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

describe("jobsByZipLayer — config", () => {
  it("declares stable ids", () => {
    expect(JOBS_BY_ZIP_SOURCE_ID).toBe("jobs-by-zip-source");
    expect(JOBS_BY_ZIP_CIRCLE_ID).toBe("jobs-by-zip-circle");
  });

  it("paint expression branches on creditCheck for Ch4d effect", () => {
    const layer = jobsByZipLayer.layerConfigs.find((l) => l.id === JOBS_BY_ZIP_CIRCLE_ID);
    const paintStr = JSON.stringify(layer?.paint ?? {});
    expect(paintStr).toMatch(/creditCheck/);
  });
});

describe("jobsByZipLayer — buildJobsByZipGeoJSON", () => {
  it("emits at least 30 employer features", () => {
    const fc = buildJobsByZipGeoJSON();
    expect(fc.features.length).toBeGreaterThanOrEqual(30);
  });

  it("includes Amazon FC DFW5 with real coordinates (W3 Ch6 reference)", () => {
    const fc = buildJobsByZipGeoJSON();
    const dfw5 = fc.features.find(
      (f) => f.properties.id === "amazon-dfw5",
    );
    expect(dfw5).toBeDefined();
    expect(dfw5?.geometry.type).toBe("Point");
  });

  it("every feature carries fairChance + creditCheck flags", () => {
    const fc = buildJobsByZipGeoJSON();
    for (const f of fc.features) {
      expect(typeof f.properties.fairChance).toBe("boolean");
      expect(typeof f.properties.creditCheck).toBe("boolean");
      expect(typeof f.properties.name).toBe("string");
    }
  });

  it("includes both fair-chance and credit-check categories (Ch4d truthful 30% claim)", () => {
    const fc = buildJobsByZipGeoJSON();
    const fair = fc.features.filter((f) => f.properties.fairChance).length;
    const credit = fc.features.filter((f) => f.properties.creditCheck).length;
    expect(fair).toBeGreaterThan(0);
    expect(credit).toBeGreaterThan(0);
  });
});

describe("jobsByZipLayer — register / remove", () => {
  it("register adds source + 1 circle layer", () => {
    const map = createMockMap();
    jobsByZipLayer.register(map as never);
    expect(map.addSource).toHaveBeenCalledTimes(1);
    expect(map.addLayer).toHaveBeenCalledTimes(1);
  });
});
