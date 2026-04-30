/**
 * polish-2 T50 — sound-triggers wiring tests.
 *
 * Verifies the cross-driver sound-trigger contract :
 *   - chapters fire `gowork:ch4-step` / `gowork:ch5-fan-complete`
 *     / `gowork:ch7-cliff-cross` events on `document`.
 *   - `installSoundTriggers()` registers listeners that call `play(soundId)`
 *     with the correct mapping.
 *   - The returned cleanup detaches the listeners.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

vi.mock("@/lib/wall/sound", () => {
  const play = vi.fn();
  const unlock = vi.fn();
  return { play, unlock };
});

import {
  installSoundTriggers,
  SOUND_EVENT_NAMES,
  fireChapter4Step,
  fireChapter5FanComplete,
  fireChapter7CliffCross,
} from "../soundTriggers";
import { play as playSound, unlock as unlockSound } from "@/lib/wall/sound";

const play = vi.mocked(playSound);
const unlock = vi.mocked(unlockSound);

beforeEach(() => {
  play.mockClear();
  unlock.mockClear();
});

afterEach(() => {
  // listeners cleaned by each test's returned cleanup
});

describe("soundTriggers (polish-2 T50)", () => {
  it("declares the canonical custom event names", () => {
    expect(SOUND_EVENT_NAMES.CH4_STEP).toBe("gowork:ch4-step");
    expect(SOUND_EVENT_NAMES.CH5_FAN_COMPLETE).toBe("gowork:ch5-fan-complete");
    expect(SOUND_EVENT_NAMES.CH7_CLIFF_CROSS).toBe("gowork:ch7-cliff-cross");
  });

  it("installSoundTriggers wires ch4-step → footstep", () => {
    const cleanup = installSoundTriggers();
    fireChapter4Step();
    expect(play).toHaveBeenCalledWith("footstep");
    cleanup();
  });

  it("installSoundTriggers wires ch5-fan-complete → chime", () => {
    const cleanup = installSoundTriggers();
    fireChapter5FanComplete();
    expect(play).toHaveBeenCalledWith("chime");
    cleanup();
  });

  it("installSoundTriggers wires ch7-cliff-cross → calculator-click", () => {
    const cleanup = installSoundTriggers();
    fireChapter7CliffCross();
    expect(play).toHaveBeenCalledWith("calculator-click");
    cleanup();
  });

  it("cleanup detaches the listeners — no further play calls after cleanup", () => {
    const cleanup = installSoundTriggers();
    cleanup();
    fireChapter4Step();
    fireChapter5FanComplete();
    expect(play).not.toHaveBeenCalled();
  });

  it("first user gesture (pointerdown) calls unlock() exactly once", () => {
    const cleanup = installSoundTriggers();
    document.dispatchEvent(new Event("pointerdown"));
    document.dispatchEvent(new Event("pointerdown"));
    expect(unlock).toHaveBeenCalledTimes(1);
    cleanup();
  });
});
