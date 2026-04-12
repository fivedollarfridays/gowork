import { describe, it, expect, beforeEach, vi } from "vitest";
import { getTranslation, setLocale, getLocale, t } from "../i18n";

describe("i18n edge cases", () => {
  beforeEach(() => {
    setLocale("en");
  });

  describe("missing translation fallback", () => {
    it("returns the key itself for a missing top-level key", () => {
      expect(getTranslation("nonexistent", "en")).toBe("nonexistent");
    });

    it("returns the key for a deeply nested missing key", () => {
      expect(getTranslation("a.b.c.d.e", "en")).toBe("a.b.c.d.e");
    });

    it("returns the key when intermediate path is a string (not object)", () => {
      // hero.title is a string, so hero.title.nested should fail
      expect(getTranslation("hero.title.nested", "en")).toBe("hero.title.nested");
    });

    it("returns the key for an empty string key", () => {
      expect(getTranslation("", "en")).toBe("");
    });
  });

  describe("locale switching consistency", () => {
    it("t() reflects the most recent setLocale", () => {
      setLocale("es");
      const esResult = t("common.getStarted");
      setLocale("en");
      const enResult = t("common.getStarted");
      expect(esResult).not.toBe(enResult);
    });

    it("getLocale returns 'en' after reset", () => {
      setLocale("es");
      setLocale("en");
      expect(getLocale()).toBe("en");
    });
  });

  describe("localStorage handling", () => {
    it("persists locale to localStorage", () => {
      setLocale("es");
      expect(localStorage.getItem("montgowork-locale")).toBe("es");
    });

    it("handles localStorage being unavailable", () => {
      const original = localStorage.getItem;
      const originalSet = localStorage.setItem;

      // Simulate storage error
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
        throw new Error("Storage full");
      });

      // Should not throw
      expect(() => setLocale("es")).not.toThrow();
      expect(getLocale()).toBe("es");

      vi.restoreAllMocks();
    });
  });

  describe("Spanish translations completeness", () => {
    const CRITICAL_KEYS = [
      "common.getStarted",
      "hero.title",
      "share.heading",
      "share.expiredOrInvalid",
      "share.generatedOn",
    ];

    for (const key of CRITICAL_KEYS) {
      it(`has Spanish translation for ${key}`, () => {
        const result = getTranslation(key, "es");
        // Should not fall back to the key (which means it exists)
        expect(result).not.toBe(key);
        expect(result.length).toBeGreaterThan(0);
      });
    }
  });
});
