/**
 * Driver Ch04-enrich — addLayer registration tests.
 *
 * Drive each helper with a mock GwMap that captures every addSource +
 * addLayer call. Assertions:
 *   - registerEnrichedLayers wires 6 sources + the right layer ids
 *   - tracts paint uses match-on-tier (5 quintile fills)
 *   - bus transit + ghost route + catchment carry dasharray
 *   - idempotent: a second call doesn't double-register
 */
import { describe, it, expect } from "vitest";
import {
  addTractLayers,
  addCatchmentLayer,
  addTransitLayers,
  addAmberRouteLayer,
  addCyanRouteLayer,
  addGhostRouteLayer,
  registerEnrichedLayers,
} from "../Chapter04TheMap.mountLayers";

interface RegisteredSource {
  id: string;
  source: Record<string, unknown>;
}
interface RegisteredLayer {
  layer: Record<string, unknown>;
}

function fakeMap() {
  const sources: RegisteredSource[] = [];
  const layers: RegisteredLayer[] = [];
  const map = {
    addSource: (id: string, source: Record<string, unknown>) => {
      sources.push({ id, source });
    },
    addLayer: (layer: Record<string, unknown>) => {
      layers.push({ layer });
    },
    getSource: (id: string) =>
      sources.find((s) => s.id === id) ? { id } : undefined,
    getLayer: (id: string) =>
      layers.find((l) => l.layer.id === id) ? { id } : undefined,
  };
  return { map, sources, layers };
}

describe("Ch04 enriched layers — addTractLayers", () => {
  it("adds 1 source + 2 layers (fill + outline)", () => {
    const { map, sources, layers } = fakeMap();
    addTractLayers(map);
    expect(sources.map((s) => s.id)).toContain("ch04-tracts");
    expect(layers.map((l) => l.layer.id)).toEqual(
      expect.arrayContaining(["ch04-tracts-fill", "ch04-tracts-outline"]),
    );
  });

  it("tract fill paint is a match-on-tier expression (5 quintiles)", () => {
    const { map, layers } = fakeMap();
    addTractLayers(map);
    const fillLayer = layers.find((l) => l.layer.id === "ch04-tracts-fill");
    const fillExpr = (fillLayer?.layer.paint as { "fill-color"?: unknown[] })?.[
      "fill-color"
    ];
    expect(Array.isArray(fillExpr)).toBe(true);
    expect(fillExpr?.[0]).toBe("match");
    // The expression contains 5 tier keys.
    const tiers = ["t-1", "t-2", "t-3", "t-4", "t-5"];
    for (const t of tiers) expect(fillExpr).toContain(t);
  });
});

describe("Ch04 enriched layers — addCatchmentLayer", () => {
  it("adds catchment source + dashed line layer", () => {
    const { map, sources, layers } = fakeMap();
    addCatchmentLayer(map);
    expect(sources.map((s) => s.id)).toContain("ch04-catchment");
    const lineLayer = layers.find(
      (l) => l.layer.id === "ch04-catchment-line",
    );
    expect(lineLayer).toBeTruthy();
    const dash = (lineLayer?.layer.paint as { "line-dasharray"?: unknown })?.[
      "line-dasharray"
    ];
    expect(dash).toEqual([3, 5]);
  });
});

describe("Ch04 enriched layers — addTransitLayers", () => {
  it("adds transit source + dashed line layer", () => {
    const { map, sources, layers } = fakeMap();
    addTransitLayers(map);
    expect(sources.map((s) => s.id)).toContain("ch04-transit");
    const transit = layers.find((l) => l.layer.id === "ch04-transit-line");
    expect(transit).toBeTruthy();
    const dash = (transit?.layer.paint as { "line-dasharray"?: unknown })?.[
      "line-dasharray"
    ];
    expect(dash).toEqual([4, 4]);
  });
});

describe("Ch04 enriched layers — route registrations", () => {
  it("addAmberRouteLayer adds source + glow + line layers", () => {
    const { map, sources, layers } = fakeMap();
    addAmberRouteLayer(map);
    expect(sources.map((s) => s.id)).toContain("ch04-route-amber");
    expect(layers.map((l) => l.layer.id)).toEqual(
      expect.arrayContaining([
        "ch04-route-amber-glow",
        "ch04-route-amber-line",
      ]),
    );
  });

  it("addCyanRouteLayer adds source + glow + line layers", () => {
    const { map, sources, layers } = fakeMap();
    addCyanRouteLayer(map);
    expect(sources.map((s) => s.id)).toContain("ch04-route-cyan");
    expect(layers.map((l) => l.layer.id)).toEqual(
      expect.arrayContaining(["ch04-route-cyan-glow", "ch04-route-cyan-line"]),
    );
  });

  it("addGhostRouteLayer adds source + dashed rose line", () => {
    const { map, sources, layers } = fakeMap();
    addGhostRouteLayer(map);
    expect(sources.map((s) => s.id)).toContain("ch04-route-ghost");
    const ghost = layers.find((l) => l.layer.id === "ch04-route-ghost-line");
    const paint = ghost?.layer.paint as Record<string, unknown>;
    expect(paint?.["line-color"]).toBe("#FB7185");
    expect(paint?.["line-dasharray"]).toEqual([6, 6]);
  });
});

describe("Ch04 enriched layers — registerEnrichedLayers", () => {
  it("registers all 6 source ids in one call", () => {
    const { map, sources } = fakeMap();
    registerEnrichedLayers(map);
    expect(sources.map((s) => s.id).sort()).toEqual([
      "ch04-catchment",
      "ch04-route-amber",
      "ch04-route-cyan",
      "ch04-route-ghost",
      "ch04-tracts",
      "ch04-transit",
    ]);
  });

  it("is idempotent — calling twice doesn't double-register sources", () => {
    const { map, sources } = fakeMap();
    registerEnrichedLayers(map);
    const firstCount = sources.length;
    registerEnrichedLayers(map);
    expect(sources.length).toBe(firstCount);
  });
});
