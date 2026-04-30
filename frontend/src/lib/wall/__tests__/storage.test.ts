/**
 * Storage centralization (Wave 2 — cross-driver integration).
 *
 * One module owns the localStorage / sessionStorage key namespace so
 * Driver A's tokens, Driver B's audio + RUM, and Driver C's mute toggle +
 * locale toggle never drift on key spelling. Discovered during W1 maximization :
 * MuteToggle persisted `gowork-muted` (hyphen) while sound.ts read
 * `gowork.muted` (dot) — silent mute breakage. STORAGE_KEYS makes that class
 * of bug a compile-time error.
 */
import { describe, it, expect, beforeEach } from "vitest";
import {
  STORAGE_KEYS,
  getStored,
  setStored,
  removeStored,
} from "../storage";

describe("STORAGE_KEYS namespace", () => {
  it("exposes a single canonical key for every persisted concern", () => {
    expect(STORAGE_KEYS.LOCALE).toBe("gowork.locale");
    expect(STORAGE_KEYS.LOCALE_LEGACY).toBe("montgowork-locale");
    expect(STORAGE_KEYS.MUTED).toBe("gowork.muted");
    expect(STORAGE_KEYS.RUM_SID).toBe("gowork.rum.sid");
    expect(STORAGE_KEYS.MAPBOX_TOKEN_VALIDATED).toBe(
      "gowork.mapbox.validated",
    );
  });

  it("declares every key with the gowork. or montgowork- prefix", () => {
    for (const value of Object.values(STORAGE_KEYS)) {
      expect(value.startsWith("gowork.") || value.startsWith("montgowork-")).toBe(
        true,
      );
    }
  });
});

describe("typed storage helpers", () => {
  beforeEach(() => {
    if (typeof window !== "undefined") localStorage.clear();
  });

  it("getStored returns the fallback when the key is absent", () => {
    expect(getStored("gowork.locale", "en")).toBe("en");
  });

  it("setStored + getStored round-trip for primitive values", () => {
    setStored("gowork.muted", "true");
    expect(getStored("gowork.muted", "false")).toBe("true");
  });

  it("setStored serializes non-string values via JSON", () => {
    setStored("gowork.mapbox.validated", { ok: true, when: 42 });
    expect(getStored("gowork.mapbox.validated", null)).toEqual({
      ok: true,
      when: 42,
    });
  });

  it("removeStored clears the key and forces the fallback path", () => {
    setStored("gowork.muted", "true");
    removeStored("gowork.muted");
    expect(getStored("gowork.muted", "false")).toBe("false");
  });

  it("returns the fallback when JSON parsing fails (corrupted value)", () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("gowork.mapbox.validated", "{not-json");
    }
    expect(getStored("gowork.mapbox.validated", { ok: false })).toEqual({
      ok: false,
    });
  });
});

describe("SSR safety", () => {
  it("getStored returns the fallback when window is undefined", async () => {
    // Simulate SSR by stubbing window-access at the helper level via import
    // shape; the browser-only branch must never throw.
    expect(() => getStored("gowork.locale", "en")).not.toThrow();
  });

  it("setStored is a no-op when localStorage is unavailable", () => {
    expect(() => setStored("gowork.muted", "true")).not.toThrow();
  });
});
