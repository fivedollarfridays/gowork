import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageToggle } from "../LanguageToggle";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

function renderToggle() {
  return render(
    <TranslationProvider>
      <LanguageToggle />
    </TranslationProvider>,
  );
}

describe("LanguageToggle", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders toggle button", () => {
    renderToggle();
    expect(screen.getByRole("button", { name: /language|idioma/i })).toBeInTheDocument();
  });

  it("shows EN as active by default", () => {
    renderToggle();
    const btn = screen.getByRole("button", { name: /language|idioma/i });
    expect(btn).toHaveTextContent("EN");
  });

  it("switches to ES on click", async () => {
    const user = userEvent.setup();
    renderToggle();
    const btn = screen.getByRole("button", { name: /language|idioma/i });
    await user.click(btn);
    expect(btn).toHaveTextContent("ES");
  });

  it("toggles back to EN on second click", async () => {
    const user = userEvent.setup();
    renderToggle();
    const btn = screen.getByRole("button", { name: /language|idioma/i });
    await user.click(btn);
    await user.click(btn);
    expect(btn).toHaveTextContent("EN");
  });
});
