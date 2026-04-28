/**
 * W3 Driver A — Bus 4 → DFW5 corridor accent (T3.3).
 *
 * The Trinity Metro layer (W2 Driver B) already highlights Bus 4 + Bus 6
 * via feature-state. Ch6 (The Math) lands the camera on Amazon FC DFW5
 * — Carlos's destination. The corridor accent is a derived GeoJSON line
 * connecting Bus 4's northern terminus to DFW5 so the path is
 * visually obvious when Ch6 activates. The line uses the same amber
 * highlight token as the Bus 4 feature-state.
 */
import { describe, it, expect } from "vitest";
import {
  BUS4_TO_DFW5_CORRIDOR,
  buildBus4Dfw5CorridorFeature,
} from "../trinityMetro";
import { getEmployerById, EMPLOYER_DFW5_ID } from "../../employerRegistry";

describe("Bus 4 → DFW5 corridor — provenance", () => {
  it("declares a corridor id for layer registration", () => {
    expect(typeof BUS4_TO_DFW5_CORRIDOR.id).toBe("string");
    expect(BUS4_TO_DFW5_CORRIDOR.id.length).toBeGreaterThan(0);
  });

  it("corridor terminates at DFW5's verified coordinates", () => {
    const dfw5 = getEmployerById(EMPLOYER_DFW5_ID)!;
    const feature = buildBus4Dfw5CorridorFeature();
    const coords = feature.geometry.coordinates as [number, number][];
    const last = coords[coords.length - 1];
    expect(last[0]).toBeCloseTo(dfw5.longitude, 5);
    expect(last[1]).toBeCloseTo(dfw5.latitude, 5);
  });

  it("corridor begins inside Tarrant County (downtown FW or 76119)", () => {
    const feature = buildBus4Dfw5CorridorFeature();
    const coords = feature.geometry.coordinates as [number, number][];
    const first = coords[0];
    // Starts in central / east FW
    expect(first[0]).toBeGreaterThan(-97.5);
    expect(first[0]).toBeLessThan(-97.0);
    expect(first[1]).toBeGreaterThan(32.5);
    expect(first[1]).toBeLessThan(33.0);
  });

  it("corridor feature is a valid GeoJSON LineString", () => {
    const feature = buildBus4Dfw5CorridorFeature();
    expect(feature.type).toBe("Feature");
    expect(feature.geometry.type).toBe("LineString");
    expect(Array.isArray(feature.geometry.coordinates)).toBe(true);
    expect(
      (feature.geometry.coordinates as unknown[]).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("corridor feature carries a route property linking it to Bus 4", () => {
    const feature = buildBus4Dfw5CorridorFeature();
    expect(feature.properties?.route).toBe("4");
    expect(feature.properties?.corridor).toBe("dfw5");
  });
});
