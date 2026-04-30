import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import React from "react";
import type { ReactNode } from "react";
import { TranslationProvider } from "../useTranslation";
import {
  useLanguage,
  GOWORK_LOCALE_KEY,
  LEGACY_LOCALE_KEY,
} from "../useLanguage";

const wrapper = ({ children }: { children: ReactNode }) =>
  React.createElement(TranslationProvider, null, children);

function clearLocaleStorage(): void {
  try {
    localStorage.removeItem(GOWORK_LOCALE_KEY);
    localStorage.removeItem(LEGACY_LOCALE_KEY);
  } catch {
    /* ignore */
  }
}

describe("useLanguage (T1.33)", () => {
  beforeEach(() => {
    clearLocaleStorage();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    clearLocaleStorage();
  });

  it("defaults to en when no localStorage and en navigator", () => {
    Object.defineProperty(navigator, "language", { value: "en-US", configurable: true });
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.locale).toBe("en");
  });

  it("defaults to es when navigator.language starts with es and no stored value", () => {
    Object.defineProperty(navigator, "language", { value: "es-MX", configurable: true });
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.locale).toBe("es");
  });

  it("setLocale persists to BOTH gowork.locale and montgowork-locale", () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    act(() => result.current.setLocale("es"));
    expect(localStorage.getItem(GOWORK_LOCALE_KEY)).toBe("es");
    expect(localStorage.getItem(LEGACY_LOCALE_KEY)).toBe("es");
    expect(result.current.locale).toBe("es");
  });

  it("reads gowork.locale on mount when present (preferred over legacy)", () => {
    localStorage.setItem(GOWORK_LOCALE_KEY, "es");
    localStorage.setItem(LEGACY_LOCALE_KEY, "en");
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.locale).toBe("es");
  });

  it("falls back to legacy montgowork-locale when gowork.locale absent (migration)", () => {
    localStorage.setItem(LEGACY_LOCALE_KEY, "es");
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(result.current.locale).toBe("es");
  });

  it("exposes a t() function from useTranslation", () => {
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(typeof result.current.t).toBe("function");
    expect(typeof result.current.t("any.key")).toBe("string");
  });

  it("does not crash when localStorage throws (private browsing)", () => {
    const originalSet = Storage.prototype.setItem;
    Storage.prototype.setItem = vi.fn(() => {
      throw new Error("QuotaExceeded");
    });
    const { result } = renderHook(() => useLanguage(), { wrapper });
    expect(() => act(() => result.current.setLocale("es"))).not.toThrow();
    expect(result.current.locale).toBe("es");
    Storage.prototype.setItem = originalSet;
  });
});
