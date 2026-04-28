/**
 * W1 Driver C — T1.53 MuteToggle.
 *
 * Persists the muted boolean to localStorage under the canonical
 * STORAGE_KEYS.MUTED key (= "gowork.muted") so MuteToggle, sound.ts, and
 * any future audio surface share a single source of truth. Default is
 * MUTED (considerate for offices, libraries, and screen-reader users).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { MuteToggle, MUTE_STORAGE_KEY } from "../MuteToggle";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("MuteToggle (T1.53)", () => {
  beforeEach(() => {
    setLocale("en");
    localStorage.removeItem(MUTE_STORAGE_KEY);
  });

  it("defaults to muted on first render (no prior preference)", () => {
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    expect(btn).toHaveAttribute("aria-checked", "true");
  });

  it("toggles aria-checked when clicked", () => {
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-checked", "false");
    fireEvent.click(btn);
    expect(btn).toHaveAttribute("aria-checked", "true");
  });

  it("persists preference to localStorage under the canonical gowork.muted key", () => {
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    fireEvent.click(btn);
    expect(localStorage.getItem(MUTE_STORAGE_KEY)).toBe("false");
    expect(MUTE_STORAGE_KEY).toBe("gowork.muted");
    fireEvent.click(btn);
    expect(localStorage.getItem(MUTE_STORAGE_KEY)).toBe("true");
  });

  it("hydrates from localStorage on mount", () => {
    localStorage.setItem(MUTE_STORAGE_KEY, "false");
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    expect(btn).toHaveAttribute("aria-checked", "false");
  });
});
