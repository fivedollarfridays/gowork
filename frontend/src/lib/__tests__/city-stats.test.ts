import { describe, it, expect } from "vitest";
import { getCityStats, type CityStats } from "../city-stats";

describe("getCityStats", () => {
  it("returns Montgomery stats for AL", () => {
    const stats = getCityStats("AL");
    expect(stats.povertyRate).toBeCloseTo(20.9, 1);
    expect(stats.laborParticipation).toBeCloseTo(57.4, 1);
    expect(stats.populationLabel).toBe("36K+");
    expect(stats.populationDesc).toBe("Residents Served Area");
    expect(stats.cityName).toBe("Montgomery");
  });

  it("returns Fort Worth stats for TX", () => {
    const stats = getCityStats("TX");
    expect(stats.povertyRate).toBeCloseTo(15.3, 1);
    expect(stats.laborParticipation).toBeCloseTo(64.0, 0);
    expect(stats.populationLabel).toBe("950K+");
    expect(stats.populationDesc).toBe("Metro Population");
    expect(stats.cityName).toBe("Fort Worth");
  });

  it("defaults to Fort Worth for unknown state", () => {
    // Reference deployment is Fort Worth; unknown-state callers fall back to TX.
    const stats = getCityStats("XX");
    expect(stats.cityName).toBe("Fort Worth");
  });

  it("includes career center count", () => {
    const al = getCityStats("AL");
    expect(al.careerCenters).toBeGreaterThan(0);
    const tx = getCityStats("TX");
    expect(tx.careerCenters).toBeGreaterThan(0);
  });
});
