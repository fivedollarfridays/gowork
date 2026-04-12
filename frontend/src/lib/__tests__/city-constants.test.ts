import { describe, it, expect } from "vitest";
import {
  isValidCityZip,
  isValidMontgomeryZip,
  getCareerCenter,
  getProgramLabels,
  CAREER_CENTER_AL,
  CAREER_CENTER_TX,
} from "../constants";

describe("isValidCityZip", () => {
  it("validates Montgomery ZIPs for AL", () => {
    expect(isValidCityZip("36104", "AL")).toBe(true);
    expect(isValidCityZip("76102", "AL")).toBe(false);
  });

  it("validates Fort Worth ZIPs for TX", () => {
    expect(isValidCityZip("76102", "TX")).toBe(true);
    expect(isValidCityZip("36104", "TX")).toBe(false);
  });

  it("defaults to Montgomery when no state given", () => {
    expect(isValidCityZip("36104")).toBe(true);
    expect(isValidCityZip("76102")).toBe(false);
  });
});

describe("isValidMontgomeryZip (backward compat)", () => {
  it("still works for Montgomery ZIPs", () => {
    expect(isValidMontgomeryZip("36104")).toBe(true);
    expect(isValidMontgomeryZip("76102")).toBe(false);
  });
});

describe("getCareerCenter", () => {
  it("returns Montgomery career center for AL", () => {
    const cc = getCareerCenter("AL");
    expect(cc.name).toContain("Montgomery");
  });

  it("returns Fort Worth career center for TX", () => {
    const cc = getCareerCenter("TX");
    expect(cc.name).toContain("Workforce Solutions");
  });

  it("defaults to Montgomery", () => {
    const cc = getCareerCenter();
    expect(cc).toEqual(CAREER_CENTER_AL);
  });
});

describe("getProgramLabels", () => {
  it("returns AL labels by default", () => {
    const labels = getProgramLabels();
    expect(labels.ALL_Kids).toBe("ALL Kids");
    expect(labels.LIHEAP).toBe("LIHEAP");
  });

  it("returns TX labels for TX", () => {
    const labels = getProgramLabels("TX");
    expect(labels.CHIP).toBe("CHIP");
    expect(labels.CEAP).toBe("CEAP");
    expect(labels.ALL_Kids).toBeUndefined();
  });
});
