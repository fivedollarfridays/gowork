/**
 * T1.48 — TitleSequence × audio integration test.
 *
 * The dispatch wires Driver B's `lib/wall/sound.ts` into the page-load
 * title sequence: a single footstep sound fires when the sequence
 * completes, gated by the user's mute preference and prefers-reduced-motion.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, act } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { TitleSequence } from "../TitleSequence";

// Mock sound module so we can spy on play() without lazy-loading Howler.
vi.mock("@/lib/wall/sound", () => ({
  play: vi.fn(),
  isMuted: vi.fn(),
  setMuted: vi.fn(),
  unlock: vi.fn(),
}));

import * as sound from "@/lib/wall/sound";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("TitleSequence audio handoff (T1.48)", () => {
  beforeEach(() => {
    setLocale("en");
    vi.useFakeTimers();
    vi.clearAllMocks();
    (sound.isMuted as ReturnType<typeof vi.fn>).mockReturnValue(false);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("plays a single footstep sound when the sequence completes", () => {
    wrap(<TitleSequence durationMs={400} />);
    expect(sound.play).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(450);
    });
    expect(sound.play).toHaveBeenCalledTimes(1);
    expect(sound.play).toHaveBeenCalledWith("footstep");
  });

  it("does not play the footstep when muted", () => {
    (sound.isMuted as ReturnType<typeof vi.fn>).mockReturnValue(true);
    wrap(<TitleSequence durationMs={400} />);
    act(() => {
      vi.advanceTimersByTime(450);
    });
    expect(sound.play).not.toHaveBeenCalled();
  });

  it("does not play the footstep under prefers-reduced-motion", () => {
    wrap(<TitleSequence durationMs={400} reducedMotion />);
    act(() => {
      vi.advanceTimersByTime(450);
    });
    expect(sound.play).not.toHaveBeenCalled();
  });

  it("does not double-fire when re-rendered with the same props", () => {
    const { rerender } = wrap(<TitleSequence durationMs={400} />);
    act(() => {
      vi.advanceTimersByTime(450);
    });
    expect(sound.play).toHaveBeenCalledTimes(1);
    rerender(
      <TranslationProvider>
        <TitleSequence durationMs={400} />
      </TranslationProvider>,
    );
    act(() => {
      vi.advanceTimersByTime(50);
    });
    expect(sound.play).toHaveBeenCalledTimes(1);
  });
});
