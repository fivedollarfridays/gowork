import { describe, it, expect } from "vitest";
import { getResumeRecommendations } from "../recommend";

describe("getResumeRecommendations", () => {
  it("returns empty arrays for empty input", () => {
    expect(getResumeRecommendations("")).toEqual({ industries: [], certifications: [] });
    expect(getResumeRecommendations("   ")).toEqual({ industries: [], certifications: [] });
  });

  it("matches healthcare with 2+ keywords", () => {
    const result = getResumeRecommendations("I am a nurse at a hospital");
    expect(result.industries).toContain("healthcare");
  });

  it("does not match healthcare with only 1 keyword", () => {
    const result = getResumeRecommendations("I visited a hospital once");
    expect(result.industries).not.toContain("healthcare");
  });

  it("matches food_service industry", () => {
    const result = getResumeRecommendations("Worked as a cook in a restaurant kitchen");
    expect(result.industries).toContain("food_service");
  });

  it("matches transportation industry", () => {
    const result = getResumeRecommendations("CDL truck driver with 5 years of delivery experience");
    expect(result.industries).toContain("transportation");
  });

  it("matches retail industry", () => {
    const result = getResumeRecommendations("Cashier at walmart, handled customer service");
    expect(result.industries).toContain("retail");
  });

  it("matches construction industry", () => {
    const result = getResumeRecommendations("Worked as an electrician on construction sites");
    expect(result.industries).toContain("construction");
  });

  it("matches manufacturing industry", () => {
    const result = getResumeRecommendations("Machine operator in a manufacturing factory");
    expect(result.industries).toContain("manufacturing");
  });

  it("matches government industry", () => {
    const result = getResumeRecommendations("Federal government clerk in civil service");
    expect(result.industries).toContain("government");
  });

  it("matches multiple industries", () => {
    const result = getResumeRecommendations(
      "Nurse at a hospital, also drove a delivery truck with CDL"
    );
    expect(result.industries).toContain("healthcare");
    expect(result.industries).toContain("transportation");
  });

  it("matches CNA certification", () => {
    const result = getResumeRecommendations("Certified nursing assistant with patient care experience");
    expect(result.certifications).toContain("CNA");
  });

  it("matches CDL certification", () => {
    const result = getResumeRecommendations("CDL class A commercial driver");
    expect(result.certifications).toContain("CDL");
  });

  it("matches LPN certification", () => {
    const result = getResumeRecommendations("Licensed practical nurse at community clinic");
    expect(result.certifications).toContain("LPN");
  });

  it("is case insensitive", () => {
    const result = getResumeRecommendations("NURSE at HOSPITAL providing PATIENT care");
    expect(result.industries).toContain("healthcare");
    expect(result.certifications).toContain("CNA");
  });

  it("returns no matches for unrelated text", () => {
    const result = getResumeRecommendations("I enjoy painting and reading books");
    expect(result.industries).toEqual([]);
    expect(result.certifications).toEqual([]);
  });
});
