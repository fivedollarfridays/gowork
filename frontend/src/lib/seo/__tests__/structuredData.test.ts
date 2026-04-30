/**
 * polish-2 T51 — structured-data tests.
 *
 * Verifies the JSON-LD payload generator emits at minimum a `WebSite`
 * + `BreadcrumbList`, layered with an `Article` when a chapter is in
 * the 1..8 range, and respects locale.
 */
import { describe, it, expect } from "vitest";
import { buildHomeStructuredData } from "../structuredData";

describe("buildHomeStructuredData (polish-2 T51)", () => {
  it("returns at least WebSite + BreadcrumbList for the bare home route", () => {
    const data = buildHomeStructuredData({ chapter: 0, locale: "en" });
    const types = data.map((d) => d["@type"]);
    expect(types).toContain("WebSite");
    expect(types).toContain("BreadcrumbList");
  });

  it("each entry declares the schema.org context", () => {
    const data = buildHomeStructuredData({ chapter: 0, locale: "en" });
    for (const entry of data) {
      expect(entry["@context"]).toBe("https://schema.org");
    }
  });

  it("includes an Article entry when a valid chapter (1..8) is supplied", () => {
    const data = buildHomeStructuredData({ chapter: 3, locale: "en" });
    const article = data.find((d) => d["@type"] === "Article");
    expect(article).toBeDefined();
    expect(article?.headline).toMatch(/Carlos/i);
  });

  it("omits Article for an out-of-range chapter (0 or >8)", () => {
    const oor = buildHomeStructuredData({ chapter: 99, locale: "en" });
    expect(oor.find((d) => d["@type"] === "Article")).toBeUndefined();
  });

  it("BreadcrumbList contains a Home item and a Chapter item when chapter is set", () => {
    const data = buildHomeStructuredData({ chapter: 4, locale: "en" });
    const crumbs = data.find((d) => d["@type"] === "BreadcrumbList") as
      | { itemListElement?: Array<{ name?: string }> }
      | undefined;
    expect(crumbs).toBeDefined();
    const names = (crumbs?.itemListElement ?? []).map((it) => it.name);
    expect(names[0]).toMatch(/home/i);
    expect(names.some((n) => n && /chapter/i.test(n))).toBe(true);
  });

  it("emits inLanguage = es when locale is es", () => {
    const data = buildHomeStructuredData({ chapter: 1, locale: "es" });
    const article = data.find((d) => d["@type"] === "Article");
    expect(article?.inLanguage).toBe("es");
  });

  it("emits inLanguage = en when locale is en", () => {
    const data = buildHomeStructuredData({ chapter: 1, locale: "en" });
    const article = data.find((d) => d["@type"] === "Article");
    expect(article?.inLanguage).toBe("en");
  });
});
