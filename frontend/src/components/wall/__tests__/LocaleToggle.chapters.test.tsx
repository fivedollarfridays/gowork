/**
 * W4 Driver B — T4.B.4 React-level locale-swap contract.
 *
 * Mounts a small consumer component that reads chapter strings via the
 * `useTranslation` hook (the canonical access path for re-renders), then
 * clicks the LanguageToggle and asserts the rendered text has swapped
 * to its ES counterpart.
 *
 * Why this exists separately from `chapterLocaleSwap.test.ts`:
 *   - The other test pins the i18n LIBRARY contract (pure functions).
 *   - This test pins the REACT contract: the toggle's `switchLocale`
 *     call propagates through the TranslationProvider so subscribers
 *     re-render with the new strings.
 *
 * Per the dispatch constraint, we do NOT mount real chapter components
 * (which use static `t` import and live outside the provider tree on the
 * production page). Instead we mount a synthetic `<ChapterReader />`
 * component that reads the same i18n keys via `useTranslation` — the
 * canonical pattern future chapters should follow.
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { LanguageToggle } from "../LanguageToggle";

const KEYS = [
  "wall.chapter06.hero",
  "wall.chapter07.body",
  "wall.chapter08.subhero",
  "wall.chapter09.hero",
  "wall.chapter10.body",
] as const;

function ChapterReader() {
  const { t } = useTranslation();
  return (
    <ul>
      {KEYS.map((key) => (
        <li key={key} data-testid={key}>
          {t(key)}
        </li>
      ))}
    </ul>
  );
}

function renderTree() {
  return render(
    <TranslationProvider>
      <LanguageToggle />
      <ChapterReader />
    </TranslationProvider>,
  );
}

describe("W4 — locale toggle re-renders chapter consumers (T4.B.4)", () => {
  beforeEach(() => {
    setLocale("en");
    document.documentElement.lang = "en";
  });

  it("renders English chapter copy on first mount", () => {
    renderTree();
    expect(screen.getByTestId("wall.chapter06.hero").textContent).toMatch(
      /more pay|less money/i,
    );
  });

  it("swaps Ch6 hero to ES on toggle click", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    expect(screen.getByTestId("wall.chapter06.hero").textContent).toMatch(
      /ganar más|menos/i,
    );
  });

  it("swaps Ch7 body to ES on toggle click (same-day case file phrasing)", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    // Narrative Reset: Ch7 body teaches the same-day case file promise.
    expect(screen.getByTestId("wall.chapter07.body").textContent).toMatch(
      /expediente|barreras|Workforce/i,
    );
  });

  it("swaps Ch8 subhero to ES on toggle click", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    expect(screen.getByTestId("wall.chapter08.subhero").textContent).toMatch(
      /barrera/i,
    );
  });

  it("swaps Ch9 hero to ES on toggle click (Fort Worth proper noun stays)", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    const ch9 = screen.getByTestId("wall.chapter09.hero").textContent ?? "";
    expect(ch9).toMatch(/Funciona/);
    expect(ch9).toContain("Fort Worth");
  });

  it("swaps Ch10 body to ES on toggle click", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    expect(screen.getByTestId("wall.chapter10.body").textContent).toMatch(
      /muro|laberinto/i,
    );
  });

  it("toggles back to EN restores English copy", () => {
    renderTree();
    fireEvent.click(screen.getByRole("button", { name: /^es$/i }));
    fireEvent.click(screen.getByRole("button", { name: /^en$/i }));
    expect(screen.getByTestId("wall.chapter06.hero").textContent).toMatch(
      /more pay|less money/i,
    );
  });
});
