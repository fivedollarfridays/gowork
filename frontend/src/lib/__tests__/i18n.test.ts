import { describe, it, expect, beforeEach } from "vitest";
import { getTranslation, setLocale, getLocale, t, type Locale } from "../i18n";

describe("i18n", () => {
  beforeEach(() => {
    setLocale("en");
  });

  describe("getLocale / setLocale", () => {
    it("defaults to English", () => {
      expect(getLocale()).toBe("en");
    });

    it("can be set to Spanish", () => {
      setLocale("es");
      expect(getLocale()).toBe("es");
    });

    it("can be set back to English", () => {
      setLocale("es");
      setLocale("en");
      expect(getLocale()).toBe("en");
    });
  });

  describe("getTranslation", () => {
    it("returns English string for known key", () => {
      const result = getTranslation("common.getStarted", "en");
      expect(result).toBe("Get Started");
    });

    it("returns Spanish string for known key", () => {
      const result = getTranslation("common.getStarted", "es");
      expect(typeof result).toBe("string");
      expect(result).not.toBe("Get Started");
    });

    it("returns key when translation is missing", () => {
      const result = getTranslation("nonexistent.key", "en");
      expect(result).toBe("nonexistent.key");
    });

    it("navigates nested keys", () => {
      const result = getTranslation("hero.title", "en");
      expect(typeof result).toBe("string");
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe("t (shorthand)", () => {
    it("uses current locale", () => {
      setLocale("en");
      const en = t("common.getStarted");
      setLocale("es");
      const es = t("common.getStarted");
      expect(en).not.toBe(es);
    });
  });

  describe("locale persistence", () => {
    it("persists locale to localStorage on setLocale", () => {
      setLocale("es");
      expect(localStorage.getItem("montgowork-locale")).toBe("es");
    });

    it("persists English locale to localStorage", () => {
      setLocale("es");
      setLocale("en");
      expect(localStorage.getItem("montgowork-locale")).toBe("en");
    });
  });
});
