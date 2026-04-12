import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, renderHook } from "@testing-library/react";
import { TranslationProvider, useTranslation } from "../useTranslation";
import { setLocale } from "@/lib/i18n";

describe("useTranslation edge cases", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("throws when used outside TranslationProvider", () => {
    // Suppress console.error for expected error
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => renderHook(() => useTranslation())).toThrow(
      "useTranslation must be used within a TranslationProvider",
    );
    spy.mockRestore();
  });

  it("returns fallback key for missing translation", () => {
    function Consumer() {
      const { t } = useTranslation();
      return <span data-testid="result">{t("totally.missing.key")}</span>;
    }

    render(
      <TranslationProvider>
        <Consumer />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("result")).toHaveTextContent("totally.missing.key");
  });

  it("provides locale and translation function consistently", () => {
    function Consumer() {
      const { locale, t } = useTranslation();
      return (
        <div>
          <span data-testid="locale">{locale}</span>
          <span data-testid="text">{t("common.getStarted")}</span>
        </div>
      );
    }

    render(
      <TranslationProvider>
        <Consumer />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("locale")).toHaveTextContent("en");
    expect(screen.getByTestId("text")).toHaveTextContent("Get Started");
  });
});
