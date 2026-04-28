"use client";

import { useEffect, useRef } from "react";
import { useTranslation } from "./useTranslation";
import type { Locale } from "@/lib/i18n";
import { STORAGE_KEYS } from "@/lib/wall/storage";

/** Preferred storage key for the GoWork rebrand. */
export const GOWORK_LOCALE_KEY = STORAGE_KEYS.LOCALE;
/** Legacy key (montgowork era) — kept for session continuity per dispatch. */
export const LEGACY_LOCALE_KEY = STORAGE_KEYS.LOCALE_LEGACY;

export interface UseLanguageResult {
  locale: Locale;
  setLocale: (next: Locale) => void;
  t: (key: string) => string;
}

function readPersistedLocale(): Locale | null {
  if (typeof window === "undefined") return null;
  try {
    const preferred = localStorage.getItem(GOWORK_LOCALE_KEY);
    if (preferred === "en" || preferred === "es") return preferred;
    const legacy = localStorage.getItem(LEGACY_LOCALE_KEY);
    if (legacy === "en" || legacy === "es") return legacy;
  } catch {
    /* private browsing → in-memory fallback */
  }
  return null;
}

function detectNavigatorLocale(): Locale {
  if (typeof navigator === "undefined") return "en";
  const lang = navigator.language || "en";
  return lang.toLowerCase().startsWith("es") ? "es" : "en";
}

function writePersistedLocale(locale: Locale): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(GOWORK_LOCALE_KEY, locale);
    localStorage.setItem(LEGACY_LOCALE_KEY, locale);
  } catch {
    /* ignore — caller still has in-memory state */
  }
}

/**
 * Locale-aware wrapper around `useTranslation`.
 *
 * - Reads from `gowork.locale` (new), falls back to `montgowork-locale`
 *   (legacy) for session continuity, then to `navigator.language`.
 * - On `setLocale`, writes BOTH keys (preserves migration ergonomics).
 * - SSR-safe: no `window`/`navigator` access at module level.
 *
 * Wraps the existing `useTranslation` so we do NOT duplicate the
 * translation lookup logic. Must be used inside `<TranslationProvider>`.
 */
export function useLanguage(): UseLanguageResult {
  const { locale, t, switchLocale } = useTranslation();
  const initializedRef = useRef<boolean>(false);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    const persisted = readPersistedLocale();
    const initial = persisted ?? detectNavigatorLocale();
    if (initial !== locale) switchLocale(initial);
    // Backfill the new key if only the legacy key was present.
    if (persisted) writePersistedLocale(persisted);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setLocale = (next: Locale): void => {
    switchLocale(next);
    writePersistedLocale(next);
  };

  return { locale, setLocale, t };
}
