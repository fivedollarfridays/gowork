"use client";

import { useCallback, useEffect } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import type { Locale } from "@/lib/i18n";

/**
 * T1.54 — EN / ES locale toggle.
 *
 * Re-uses the existing `useTranslation` provider's `switchLocale`
 * (which calls `setLocale`, persists to localStorage, and re-renders
 * subscribers). On mount + on every change, syncs `<html lang>` so
 * screen readers and CSS :lang() selectors stay in sync.
 *
 * Per the dispatch, the language toggle does NOT change `<html lang>`
 * mechanism without coordinating with Driver B's useLanguage hook.
 * This component therefore writes to documentElement.lang directly
 * for now — when Driver B's hook lands, it can subscribe and replace
 * this side effect (event-based or React-context). Either way the
 * external behavior (lang attr in sync) is preserved.
 */
const LOCALES: Array<{ code: Locale; label: string }> = [
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
];

export function LanguageToggle(): JSX.Element {
  const { locale, switchLocale, t } = useTranslation();

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const onSelect = useCallback(
    (next: Locale) => {
      if (next === locale) return;
      switchLocale(next);
      if (typeof document !== "undefined") {
        document.documentElement.lang = next;
      }
    },
    [locale, switchLocale],
  );

  return (
    <div
      role="group"
      aria-label={t("header.languageToggle.aria")}
      data-language-toggle
      className="inline-flex items-center rounded-full border border-foreground/10 p-0.5 text-xs font-mono uppercase tracking-wider"
    >
      {LOCALES.map(({ code, label }) => {
        const isActive = locale === code;
        return (
          <button
            key={code}
            type="button"
            aria-pressed={isActive}
            onClick={() => onSelect(code)}
            className={`px-3 py-1 rounded-full transition ${
              isActive
                ? "bg-foreground text-background"
                : "text-foreground/70 hover:text-foreground"
            }`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
