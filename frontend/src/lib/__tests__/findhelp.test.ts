import { describe, it, expect } from "vitest";
import { generateFindhelpUrl, FINDHELP_CATEGORIES } from "../findhelp";

describe("generateFindhelpUrl", () => {
  it("generates a URL for Montgomery ZIPs", () => {
    const url = generateFindhelpUrl("credit", "36104");
    expect(url).toBe("https://www.findhelp.org/money/financial-assistance?postal=36104");
  });

  it("generates a URL for Fort Worth ZIPs", () => {
    const url = generateFindhelpUrl("transportation", "76102");
    expect(url).toBe("https://www.findhelp.org/transit/transportation?postal=76102");
  });

  it("returns null for invalid ZIP format", () => {
    expect(generateFindhelpUrl("credit", "abc")).toBeNull();
    expect(generateFindhelpUrl("credit", "1234")).toBeNull();
    expect(generateFindhelpUrl("credit", "123456")).toBeNull();
  });

  it("returns null for unknown barrier type", () => {
    // Cast to any to test runtime behavior with unknown types
    expect(generateFindhelpUrl("unknown" as any, "36104")).toBeNull();
  });

  it("maps all barrier types to valid findhelp categories", () => {
    const types = ["credit", "transportation", "childcare", "housing", "health", "training", "criminal_record"] as const;
    for (const t of types) {
      expect(FINDHELP_CATEGORIES[t]).toBeDefined();
      const url = generateFindhelpUrl(t, "36104");
      expect(url).toContain("findhelp.org");
    }
  });

  it("includes postal param for any valid ZIP", () => {
    const alUrl = generateFindhelpUrl("housing", "36116");
    expect(alUrl).toContain("postal=36116");

    const txUrl = generateFindhelpUrl("housing", "76119");
    expect(txUrl).toContain("postal=76119");

    const otherUrl = generateFindhelpUrl("housing", "90210");
    expect(otherUrl).toContain("postal=90210");
  });
});
