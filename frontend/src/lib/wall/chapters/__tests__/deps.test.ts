/**
 * W2 Driver C — dependency surface contract tests.
 */
import { describe, it, expect } from "vitest";
import {
  W2_OFFICES,
  W2_FORMS,
  W2_LABYRINTH_FORM_COUNT,
  CARLOS_HOME_PIN,
} from "../deps";

describe("W2 chapter deps", () => {
  it("exposes 5 W2 offices for the Labyrinth", () => {
    expect(W2_OFFICES).toHaveLength(5);
  });

  it("includes Tarrant County District Clerk for Ch4a", () => {
    const clerk = W2_OFFICES.find((o) => o.id === "tarrant-district-clerk");
    expect(clerk?.category).toBe("court");
  });

  it("includes HHSC for Ch4c", () => {
    const hhsc = W2_OFFICES.find((o) => o.id === "hhsc-eligibility");
    expect(hhsc?.category).toBe("childcare");
  });

  it("declares 47 as the canonical labyrinth form count", () => {
    expect(W2_LABYRINTH_FORM_COUNT).toBe(47);
  });

  it("ships at least one DPS form (Article 55 path)", () => {
    expect(W2_FORMS.some((f) => f.agency === "Texas DPS")).toBe(true);
  });

  it("ships at least one HHSC form (childcare path)", () => {
    expect(W2_FORMS.some((f) => f.agency === "HHSC")).toBe(true);
  });

  it("Carlos home pin coordinates are inside the FW bbox (76119-ish)", () => {
    const [lon, lat] = CARLOS_HOME_PIN.coords;
    expect(lon).toBeGreaterThan(-97.5);
    expect(lon).toBeLessThan(-97.1);
    expect(lat).toBeGreaterThan(32.6);
    expect(lat).toBeLessThan(32.8);
  });
});
