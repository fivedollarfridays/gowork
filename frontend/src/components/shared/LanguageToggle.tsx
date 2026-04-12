"use client";

import { Languages } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * Toggle button that switches the UI between English and Spanish.
 */
export function LanguageToggle() {
  const { locale, switchLocale } = useTranslation();

  const toggle = () => {
    switchLocale(locale === "en" ? "es" : "en");
  };

  const label = locale === "en" ? "Language" : "Idioma";

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggle}
      aria-label={label}
      className="gap-1.5 text-sm"
    >
      <Languages className="h-4 w-4" />
      {locale.toUpperCase()}
    </Button>
  );
}
