/**
 * Driver Ch04-enrich — pure-data tests for the v1 visual stack:
 *   - WAYPOINTS (6 stops with lng/lat/label/sub/color)
 *   - DAY_ROUTE_AMBER / DAY_ROUTE_CYAN sequences
 *   - TRACT_FEATURES (5 quintiles, t-1..t-5)
 *   - CATCHMENT_FEATURE (Como Elementary dotted polygon)
 *   - TRANSIT_LINES (Bus 4 / Bus 6)
 *   - GHOST_ROUTE (the broken / no-car path)
 *   - ANNOTATIONS (callout positions)
 *
 * No Mapbox import — these are GeoJSON data factories.
 */
import { describe, it, expect } from "vitest";
import {
  WAYPOINTS,
  DAY_ROUTE_AMBER,
  DAY_ROUTE_CYAN,
  GHOST_ROUTE,
  buildTractFeatures,
  buildCatchmentFeature,
  buildTransitFeatures,
  buildAnnotations,
  buildAmberRouteSource,
  buildCyanRouteSource,
} from "../Chapter04TheMap.layers";

describe("Ch04 layers data — WAYPOINTS", () => {
  it("ships 6 named waypoints (home, como, courthouse, workforce, dps, job)", () => {
    expect(Object.keys(WAYPOINTS).sort()).toEqual([
      "como",
      "courthouse",
      "dps",
      "home",
      "job",
      "workforce",
    ]);
  });

  it("each waypoint has lng/lat in Fort Worth bounds (~-97.5..-97.2, ~32.6..32.9)", () => {
    for (const w of Object.values(WAYPOINTS)) {
      expect(w.lng).toBeGreaterThan(-97.5);
      expect(w.lng).toBeLessThan(-97.2);
      expect(w.lat).toBeGreaterThan(32.6);
      expect(w.lat).toBeLessThan(32.9);
    }
  });

  it("each waypoint declares one of the 3 narrative colors (amber/cyan/rose)", () => {
    for (const w of Object.values(WAYPOINTS)) {
      expect(["amber", "cyan", "rose"]).toContain(w.color);
    }
  });
});

describe("Ch04 layers data — day routes", () => {
  it("DAY_ROUTE_AMBER is the morning sequence: home → dps → workforce → como", () => {
    expect(DAY_ROUTE_AMBER.map((w) => w.key)).toEqual([
      "home",
      "dps",
      "workforce",
      "como",
    ]);
  });

  it("DAY_ROUTE_CYAN is the afternoon sequence: como → courthouse → job", () => {
    expect(DAY_ROUTE_CYAN.map((w) => w.key)).toEqual([
      "como",
      "courthouse",
      "job",
    ]);
  });

  it("buildAmberRouteSource produces a GeoJSON Feature LineString w/ 4 coords", () => {
    const src = buildAmberRouteSource();
    expect(src.type).toBe("geojson");
    const feat = src.data as { geometry: { coordinates: unknown[] } };
    expect(feat.geometry.coordinates).toHaveLength(4);
  });

  it("buildCyanRouteSource produces a GeoJSON Feature LineString w/ 3 coords", () => {
    const src = buildCyanRouteSource();
    const feat = src.data as { geometry: { coordinates: unknown[] } };
    expect(feat.geometry.coordinates).toHaveLength(3);
  });
});

describe("Ch04 layers data — tracts (choropleth)", () => {
  it("buildTractFeatures returns 5 features keyed by t-1..t-5", () => {
    const feats = buildTractFeatures();
    expect(feats).toHaveLength(5);
    const tiers = feats.map((f) => f.properties.tier).sort();
    expect(tiers).toEqual(["t-1", "t-2", "t-3", "t-4", "t-5"]);
  });

  it("each tract is a Polygon with closed ring (first === last)", () => {
    for (const f of buildTractFeatures()) {
      expect(f.geometry.type).toBe("Polygon");
      const ring = f.geometry.coordinates[0];
      expect(ring[0]).toEqual(ring[ring.length - 1]);
    }
  });
});

describe("Ch04 layers data — Como catchment", () => {
  it("buildCatchmentFeature returns a Polygon Feature", () => {
    const f = buildCatchmentFeature();
    expect(f.type).toBe("Feature");
    expect(f.geometry.type).toBe("Polygon");
  });
});

describe("Ch04 layers data — transit lines", () => {
  it("buildTransitFeatures returns Bus 4 + Bus 6 LineStrings", () => {
    const feats = buildTransitFeatures();
    expect(feats).toHaveLength(2);
    const ids = feats.map((f) => f.properties.id).sort();
    expect(ids).toEqual(["bus-4", "bus-6"]);
  });
});

describe("Ch04 layers data — ghost route", () => {
  it("GHOST_ROUTE has at least 4 coords (the broken multi-stop path)", () => {
    expect(GHOST_ROUTE.length).toBeGreaterThanOrEqual(4);
  });
});

describe("Ch04 layers data — annotations", () => {
  it("buildAnnotations returns >= 4 callout descriptors with anchor + text", () => {
    const anns = buildAnnotations();
    expect(anns.length).toBeGreaterThanOrEqual(4);
    for (const a of anns) {
      expect(typeof a.lng).toBe("number");
      expect(typeof a.lat).toBe("number");
      expect(typeof a.text).toBe("string");
      expect(a.text.length).toBeGreaterThan(0);
    }
  });
});
