import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslationProvider, useTranslation } from "../useTranslation";
import { setLocale } from "@/lib/i18n";

function TestConsumer() {
  const { t, locale, switchLocale } = useTranslation();
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="text">{t("common.getStarted")}</span>
      <button onClick={() => switchLocale("es")}>Switch to ES</button>
      <button onClick={() => switchLocale("en")}>Switch to EN</button>
    </div>
  );
}

describe("useTranslation", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("provides current locale", () => {
    render(
      <TranslationProvider>
        <TestConsumer />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("locale")).toHaveTextContent("en");
  });

  it("translates keys in English", () => {
    render(
      <TranslationProvider>
        <TestConsumer />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("text")).toHaveTextContent("Get Started");
  });

  it("switches to Spanish on demand", async () => {
    const user = userEvent.setup();
    render(
      <TranslationProvider>
        <TestConsumer />
      </TranslationProvider>,
    );
    await user.click(screen.getByText("Switch to ES"));
    expect(screen.getByTestId("locale")).toHaveTextContent("es");
    expect(screen.getByTestId("text")).toHaveTextContent("Comenzar");
  });

  it("switches back to English", async () => {
    const user = userEvent.setup();
    render(
      <TranslationProvider>
        <TestConsumer />
      </TranslationProvider>,
    );
    await user.click(screen.getByText("Switch to ES"));
    await user.click(screen.getByText("Switch to EN"));
    expect(screen.getByTestId("locale")).toHaveTextContent("en");
    expect(screen.getByTestId("text")).toHaveTextContent("Get Started");
  });
});
