import type { Locale } from "./i18n";

const SAVED_KEY = "montgowork-locale";
const SUPPORTED: Locale[] = ["en", "es"];

/**
 * Returns the locale to use on first paint :
 *   1. If localStorage has a previously saved locale, use that.
 *   2. Else, peek at navigator.language(s) and return "es" when the
 *      primary tag starts with "es", otherwise "en".
 *
 * This is a pure read — it does NOT mutate localStorage. The caller
 * (Driver B's root-mount in W2) decides whether to persist via the
 * existing `setLocale` helper, keeping the storage write under one
 * source of truth.
 *
 * Spotlight invention beyond the dispatch : auto-detect respects the
 * existing key (`montgowork-locale`) so a returning user's preference
 * always wins, but a brand-new visitor on a Spanish-language device
 * lands in Spanish without clicking the toggle. Fort Worth is 35 %
 * Hispanic — civic dignity surfaced by default.
 */
export function detectInitialLocale(): Locale {
  if (typeof window === "undefined") return "en";

  try {
    const saved = window.localStorage.getItem(SAVED_KEY);
    if (saved && (SUPPORTED as string[]).includes(saved)) {
      return saved as Locale;
    }
  } catch {
    /* ignore */
  }

  const candidates: string[] = [];
  if (typeof navigator !== "undefined") {
    if (navigator.language) candidates.push(navigator.language);
    if (Array.isArray(navigator.languages)) {
      candidates.push(...navigator.languages);
    }
  }

  for (const tag of candidates) {
    const head = tag.split("-")[0]?.toLowerCase();
    if (head === "es") return "es";
    if (head === "en") return "en";
  }
  return "en";
}
