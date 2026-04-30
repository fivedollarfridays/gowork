/**
 * W1 Driver C — first-visit OS-language auto-detect (Wave 7 enrichment).
 *
 * Pure helper that, on first visit (no saved locale in localStorage),
 * reads navigator.language and returns "es" if it starts with "es",
 * else "en". Existing setLocale + useTranslation flow is unchanged
 * (this is opt-in; Driver B can choose to invoke it once at root).
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { detectInitialLocale } from "../detect-locale";

describe("detectInitialLocale", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns en when no saved locale and navigator.language is en-US", () => {
    Object.defineProperty(navigator, "language", {
      value: "en-US",
      configurable: true,
    });
    expect(detectInitialLocale()).toBe("en");
  });

  it("returns es when no saved locale and navigator.language is es-MX", () => {
    Object.defineProperty(navigator, "language", {
      value: "es-MX",
      configurable: true,
    });
    expect(detectInitialLocale()).toBe("es");
  });

  it("falls back to en for unsupported locales", () => {
    Object.defineProperty(navigator, "language", {
      value: "fr-CA",
      configurable: true,
    });
    expect(detectInitialLocale()).toBe("en");
  });

  it("returns the saved locale when one is set, ignoring navigator.language", () => {
    Object.defineProperty(navigator, "language", {
      value: "es-MX",
      configurable: true,
    });
    localStorage.setItem("montgowork-locale", "en");
    expect(detectInitialLocale()).toBe("en");
  });

  it("uses navigator.languages array when navigator.language is missing", () => {
    Object.defineProperty(navigator, "language", {
      value: "",
      configurable: true,
    });
    Object.defineProperty(navigator, "languages", {
      value: ["es-AR", "en-US"],
      configurable: true,
    });
    expect(detectInitialLocale()).toBe("es");
  });
});
