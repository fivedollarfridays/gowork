import en from "./translations/en.json";
import es from "./translations/es.json";

export type Locale = "en" | "es";

type TranslationMap = Record<string, unknown>;

const translations: Record<Locale, TranslationMap> = { en, es };

let currentLocale: Locale = "en";

/** Set the active locale. */
export function setLocale(locale: Locale): void {
  currentLocale = locale;
}

/** Get the active locale. */
export function getLocale(): Locale {
  return currentLocale;
}

/**
 * Look up a dot-separated key in the given locale's translations.
 * Returns the key itself when the path is not found.
 */
export function getTranslation(key: string, locale: Locale): string {
  const parts = key.split(".");
  let node: unknown = translations[locale];
  for (const part of parts) {
    if (node == null || typeof node !== "object") return key;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === "string" ? node : key;
}

/** Shorthand: translate using the current locale. */
export function t(key: string): string {
  return getTranslation(key, currentLocale);
}
