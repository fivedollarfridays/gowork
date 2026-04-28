/**
 * Cross-driver integration test (Wave 2).
 *
 * Verifies that Driver C's MuteToggle and Driver B's sound module agree on
 * the same localStorage key (`gowork.muted`) and that toggling the UI is
 * reflected in `isMuted()`. This guards against the silent-mute bug
 * discovered during W1 maximization (MuteToggle wrote `gowork-muted`
 * while sound read `gowork.muted`).
 */
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { MuteToggle, MUTE_STORAGE_KEY } from "@/components/wall/MuteToggle";
import {
  isMuted,
  _resetSoundForTests,
} from "@/lib/wall/sound";
import { STORAGE_KEYS } from "@/lib/wall/storage";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("MuteToggle x sound module — shared storage key", () => {
  beforeEach(() => {
    setLocale("en");
    localStorage.clear();
    _resetSoundForTests();
  });

  it("MUTE_STORAGE_KEY matches STORAGE_KEYS.MUTED (canonical gowork.muted)", () => {
    expect(MUTE_STORAGE_KEY).toBe(STORAGE_KEYS.MUTED);
    expect(MUTE_STORAGE_KEY).toBe("gowork.muted");
  });

  it("clicking MuteToggle un-mutes the sound module live", () => {
    wrap(<MuteToggle />);
    expect(isMuted()).toBe(true);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    fireEvent.click(btn);
    expect(isMuted()).toBe(false);
  });

  it("a second click re-mutes the sound module", () => {
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    fireEvent.click(btn); // un-mute
    fireEvent.click(btn); // re-mute
    expect(isMuted()).toBe(true);
  });

  it("a pre-seeded gowork.muted=false hydrates BOTH MuteToggle and sound", () => {
    localStorage.setItem(STORAGE_KEYS.MUTED, "false");
    _resetSoundForTests(); // re-read storage on next isMuted() invocation
    wrap(<MuteToggle />);
    const btn = screen.getByRole("switch", { name: /toggle ambient sound/i });
    expect(btn).toHaveAttribute("aria-checked", "false");
    expect(isMuted()).toBe(false);
  });
});
