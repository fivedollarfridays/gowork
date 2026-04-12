"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { getTranslation, setLocale as setGlobalLocale, getLocale, type Locale } from "@/lib/i18n";

interface TranslationContextValue {
  locale: Locale;
  t: (key: string) => string;
  switchLocale: (locale: Locale) => void;
}

const TranslationContext = createContext<TranslationContextValue | null>(null);

export function TranslationProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(getLocale);

  const switchLocale = useCallback((newLocale: Locale) => {
    setGlobalLocale(newLocale);
    setLocale(newLocale);
  }, []);

  const t = useCallback(
    (key: string) => getTranslation(key, locale),
    [locale],
  );

  return (
    <TranslationContext.Provider value={{ locale, t, switchLocale }}>
      {children}
    </TranslationContext.Provider>
  );
}

/**
 * Hook that provides translation functions and locale switching.
 * Must be used inside a TranslationProvider.
 */
export function useTranslation(): TranslationContextValue {
  const ctx = useContext(TranslationContext);
  if (!ctx) {
    throw new Error("useTranslation must be used within a TranslationProvider");
  }
  return ctx;
}
