/**
 * W3 Driver B — translation key parity (T3.17).
 *
 * Locks the i18n surface for Ch7 + Ch8 in BOTH en + es. Missing or
 * misspelled keys would render as raw key strings on demo day.
 */
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { setLocale, getTranslation } from "@/lib/i18n";
import { BARRIER_GRAPH } from "../data/barrierGraph";

const REQUIRED_CH7_KEYS = [
  "wall.chapter07.title",
  "wall.chapter07.hero",
  "wall.chapter07.subhero",
  "wall.chapter07.body",
  "wall.chapter07.aria",
  "wall.chapter07.weekLabel1",
  "wall.chapter07.weekLabel2",
  "wall.chapter07.weekLabel3",
  "wall.chapter07.weekLabel4",
  "wall.chapter07.weekLabel5",
  "wall.chapter07.legActive",
] as const;

const REQUIRED_CH8_KEYS = [
  "wall.chapter08.title",
  "wall.chapter08.hero",
  "wall.chapter08.subhero",
  "wall.chapter08.body",
  "wall.chapter08.aria",
  "wall.chapter08.fallbackAlt",
] as const;

let savedLocale: "en" | "es";

beforeAll(() => {
  savedLocale = "en";
});

afterAll(() => {
  setLocale(savedLocale);
});

describe("W3 i18n parity — chapter07", () => {
  it.each(REQUIRED_CH7_KEYS)("EN resolves %s to a non-empty string", (key) => {
    const v = getTranslation(key, "en");
    expect(v).not.toBe(key);
    expect(v.length).toBeGreaterThan(0);
  });

  it.each(REQUIRED_CH7_KEYS)("ES resolves %s to a non-empty string", (key) => {
    const v = getTranslation(key, "es");
    expect(v).not.toBe(key);
    expect(v.length).toBeGreaterThan(0);
  });
});

describe("W3 i18n parity — chapter08 + barrier labels", () => {
  it.each(REQUIRED_CH8_KEYS)("EN resolves %s to a non-empty string", (key) => {
    const v = getTranslation(key, "en");
    expect(v).not.toBe(key);
    expect(v.length).toBeGreaterThan(0);
  });

  it.each(REQUIRED_CH8_KEYS)("ES resolves %s to a non-empty string", (key) => {
    const v = getTranslation(key, "es");
    expect(v).not.toBe(key);
    expect(v.length).toBeGreaterThan(0);
  });

  it("every barrier node labelKey resolves in EN", () => {
    for (const node of BARRIER_GRAPH.nodes) {
      const v = getTranslation(node.labelKey, "en");
      expect(v).not.toBe(node.labelKey);
      expect(v.length).toBeGreaterThan(0);
    }
  });

  it("every barrier node labelKey resolves in ES", () => {
    for (const node of BARRIER_GRAPH.nodes) {
      const v = getTranslation(node.labelKey, "es");
      expect(v).not.toBe(node.labelKey);
      expect(v.length).toBeGreaterThan(0);
    }
  });
});
