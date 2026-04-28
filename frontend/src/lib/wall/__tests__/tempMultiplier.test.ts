/**
 * Tests for `tempMultiplier` — typed CSS-token wiring for the
 * --temperature-multiplier custom property.
 *
 * W3 Driver A — Spotlight invention #1.
 *
 * The cliff-math chapter (Ch6) drives a wage slider that scales the global
 * --temperature-multiplier from 1.0 (no cliff) to 2.5 (deep cliff). Other
 * chapters in W3/W4 may want to set the same token without re-inventing
 * the formula. One module, one source of truth.
 */
import { describe, it, expect, beforeEach } from "vitest";
import {
  MIN_WAGE_USD,
  MAX_WAGE_USD,
  MIN_MULTIPLIER,
  MAX_MULTIPLIER,
  wageToMultiplier,
  multiplierToWage,
  setTemperatureMultiplier,
  readTemperatureMultiplier,
  TEMP_MULTIPLIER_PROPERTY,
} from "../tempMultiplier";

describe("tempMultiplier — constants", () => {
  it("min wage is the federal minimum (7.25/hr)", () => {
    expect(MIN_WAGE_USD).toBe(7.25);
  });

  it("max wage tops at 25/hr (above this, cliff fades for Carlos's family size)", () => {
    expect(MAX_WAGE_USD).toBe(25);
  });

  it("MIN_MULTIPLIER is 1.0 (no cliff)", () => {
    expect(MIN_MULTIPLIER).toBe(1.0);
  });

  it("MAX_MULTIPLIER is 2.5 (deep cliff)", () => {
    expect(MAX_MULTIPLIER).toBe(2.5);
  });

  it("exposes the canonical CSS property name", () => {
    expect(TEMP_MULTIPLIER_PROPERTY).toBe("--temperature-multiplier");
  });
});

describe("wageToMultiplier", () => {
  it("returns MIN_MULTIPLIER at minimum wage", () => {
    expect(wageToMultiplier(MIN_WAGE_USD)).toBe(MIN_MULTIPLIER);
  });

  it("returns MAX_MULTIPLIER at maximum wage", () => {
    expect(wageToMultiplier(MAX_WAGE_USD)).toBe(MAX_MULTIPLIER);
  });

  it("interpolates linearly at midpoint", () => {
    const mid = (MIN_WAGE_USD + MAX_WAGE_USD) / 2;
    const expected = (MIN_MULTIPLIER + MAX_MULTIPLIER) / 2;
    expect(wageToMultiplier(mid)).toBeCloseTo(expected, 5);
  });

  it("clamps below min wage to MIN_MULTIPLIER", () => {
    expect(wageToMultiplier(0)).toBe(MIN_MULTIPLIER);
    expect(wageToMultiplier(-5)).toBe(MIN_MULTIPLIER);
  });

  it("clamps above max wage to MAX_MULTIPLIER", () => {
    expect(wageToMultiplier(100)).toBe(MAX_MULTIPLIER);
  });
});

describe("multiplierToWage — round-trip", () => {
  it("inverts wageToMultiplier exactly at boundaries", () => {
    expect(multiplierToWage(wageToMultiplier(MIN_WAGE_USD))).toBeCloseTo(
      MIN_WAGE_USD,
      5,
    );
    expect(multiplierToWage(wageToMultiplier(MAX_WAGE_USD))).toBeCloseTo(
      MAX_WAGE_USD,
      5,
    );
  });

  it("inverts at midpoint", () => {
    const mid = (MIN_WAGE_USD + MAX_WAGE_USD) / 2;
    expect(multiplierToWage(wageToMultiplier(mid))).toBeCloseTo(mid, 5);
  });
});

describe("setTemperatureMultiplier / readTemperatureMultiplier — DOM wiring", () => {
  beforeEach(() => {
    // Reset the inline style before each test.
    document.documentElement.style.removeProperty(TEMP_MULTIPLIER_PROPERTY);
  });

  it("sets the property on document.documentElement when no element passed", () => {
    setTemperatureMultiplier(1.5);
    expect(
      document.documentElement.style.getPropertyValue(
        TEMP_MULTIPLIER_PROPERTY,
      ),
    ).toBe("1.5");
  });

  it("sets the property on a provided element scope", () => {
    const div = document.createElement("div");
    setTemperatureMultiplier(2.0, div);
    expect(div.style.getPropertyValue(TEMP_MULTIPLIER_PROPERTY)).toBe("2");
  });

  it("clamps the multiplier into [MIN_MULTIPLIER, MAX_MULTIPLIER]", () => {
    setTemperatureMultiplier(99);
    expect(
      document.documentElement.style.getPropertyValue(
        TEMP_MULTIPLIER_PROPERTY,
      ),
    ).toBe(String(MAX_MULTIPLIER));

    setTemperatureMultiplier(-1);
    expect(
      document.documentElement.style.getPropertyValue(
        TEMP_MULTIPLIER_PROPERTY,
      ),
    ).toBe(String(MIN_MULTIPLIER));
  });

  it("readTemperatureMultiplier returns MIN_MULTIPLIER when unset", () => {
    expect(readTemperatureMultiplier()).toBe(MIN_MULTIPLIER);
  });

  it("readTemperatureMultiplier returns the set value", () => {
    setTemperatureMultiplier(1.7);
    expect(readTemperatureMultiplier()).toBeCloseTo(1.7, 5);
  });
});
