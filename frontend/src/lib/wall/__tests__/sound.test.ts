import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// In-memory mock of the Howler module surface we touch.
const playMock = vi.fn();
const stopMock = vi.fn();
const muteMock = vi.fn();
const ctxResume = vi.fn().mockResolvedValue(undefined);

vi.mock("howler", () => {
  class Howl {
    constructor(_opts: unknown) {}
    play(): void {
      playMock();
    }
    stop(): void {
      stopMock();
    }
    volume(_v: number): void {}
  }
  const Howler = {
    mute: (m: boolean) => muteMock(m),
    ctx: { state: "suspended", resume: ctxResume },
  };
  return { Howl, Howler };
});

const GOWORK_MUTED_KEY = "gowork.muted";

async function freshSound() {
  vi.resetModules();
  return await import("../sound");
}

describe("sound singleton (T1.56–T1.59)", () => {
  beforeEach(() => {
    playMock.mockClear();
    stopMock.mockClear();
    muteMock.mockClear();
    ctxResume.mockClear();
    try {
      localStorage.removeItem(GOWORK_MUTED_KEY);
    } catch {
      /* ignore */
    }
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts muted by default (sound off until user opts in)", async () => {
    const sound = await freshSound();
    expect(sound.isMuted()).toBe(true);
  });

  it("does not invoke Howler.play when muted", async () => {
    const sound = await freshSound();
    sound.play("footstep");
    expect(playMock).not.toHaveBeenCalled();
  });

  it("invokes Howler.play after setMuted(false)", async () => {
    const sound = await freshSound();
    sound.setMuted(false);
    sound.play("footstep");
    // play() lazy-loads Howler; flush the microtask queue.
    await sound._flushForTests();
    expect(playMock).toHaveBeenCalledTimes(1);
  });

  it("setMuted persists to localStorage gowork.muted", async () => {
    const sound = await freshSound();
    sound.setMuted(false);
    expect(localStorage.getItem(GOWORK_MUTED_KEY)).toBe("false");
    sound.setMuted(true);
    expect(localStorage.getItem(GOWORK_MUTED_KEY)).toBe("true");
  });

  it("reads existing localStorage value on init (gowork.muted=false → unmuted)", async () => {
    localStorage.setItem(GOWORK_MUTED_KEY, "false");
    const sound = await freshSound();
    expect(sound.isMuted()).toBe(false);
  });

  it("stop() invokes Howler.stop only when sound was loaded", async () => {
    const sound = await freshSound();
    sound.setMuted(false);
    sound.play("footstep");
    await sound._flushForTests();
    sound.stop("footstep");
    expect(stopMock).toHaveBeenCalledTimes(1);
  });

  it("stop() on a never-played sound does not throw", async () => {
    const sound = await freshSound();
    expect(() => sound.stop("paper-rustle")).not.toThrow();
  });

  it("setVolume clamps between 0 and 1", async () => {
    const sound = await freshSound();
    expect(() => sound.setVolume(2)).not.toThrow();
    expect(() => sound.setVolume(-1)).not.toThrow();
    expect(sound.getVolume()).toBeGreaterThanOrEqual(0);
    expect(sound.getVolume()).toBeLessThanOrEqual(1);
  });

  it("does not crash when localStorage is unavailable", async () => {
    const orig = Storage.prototype.getItem;
    Storage.prototype.getItem = () => {
      throw new Error("disabled");
    };
    const sound = await freshSound();
    expect(sound.isMuted()).toBe(true); // safe default
    Storage.prototype.getItem = orig;
  });

  it("unlock() resumes audio context once on first call (T1.58)", async () => {
    const sound = await freshSound();
    sound.unlock();
    sound.unlock();
    await sound._flushForTests();
    expect(ctxResume).toHaveBeenCalledTimes(1);
  });
});
