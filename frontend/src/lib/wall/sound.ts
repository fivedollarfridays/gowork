/**
 * Sound singleton (T1.56–T1.59).
 *
 * Wraps Howler.js so the rest of the app touches a tiny, well-typed API.
 * Howler is loaded LAZILY — the import only resolves on the first
 * `play()` call when the user is unmuted, so muted users (the default)
 * never download Howler at all. This keeps the main bundle slim.
 *
 * Mute state is persisted to `localStorage['gowork.muted']`. Default is
 * MUTED — the page is silent until the user opts in (T1.53 MuteToggle).
 *
 * Audio context unlock (T1.58) — `unlock()` resumes a suspended audio
 * context exactly once; iOS Safari + most desktop browsers require a
 * user gesture before the context will play. Wire `unlock()` into a
 * one-time pointerdown/keydown listener at app boot.
 */

export type SoundId =
  | "footstep"
  | "paper-rustle"
  | "calculator-click"
  | "chime"
  | "wind-ambient";

interface HowlInstance {
  play: () => void;
  stop: () => void;
  volume: (v: number) => void;
}

interface HowlConstructor {
  new (opts: { src: string[]; volume?: number; html5?: boolean }): HowlInstance;
}

interface HowlerStatic {
  mute: (muted: boolean) => void;
  ctx?: { state?: string; resume?: () => Promise<void> };
}

import { STORAGE_KEYS } from "./storage";

const STORAGE_KEY = STORAGE_KEYS.MUTED;
const SOUND_BASE = "/sounds";
const SOUND_FILES: Record<SoundId, string> = {
  footstep: `${SOUND_BASE}/footstep.mp3`,
  "paper-rustle": `${SOUND_BASE}/paper-rustle.mp3`,
  "calculator-click": `${SOUND_BASE}/calculator-click.mp3`,
  chime: `${SOUND_BASE}/chime.mp3`,
  "wind-ambient": `${SOUND_BASE}/wind-ambient.mp3`,
};

interface SoundState {
  muted: boolean;
  volume: number;
  unlocked: boolean;
  howls: Partial<Record<SoundId, HowlInstance>>;
  HowlCtor: HowlConstructor | null;
  Howler: HowlerStatic | null;
  loaderPromise: Promise<void> | null;
}

function readMutedFromStorage(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "false") return false;
    return true;
  } catch {
    return true;
  }
}

const state: SoundState = {
  muted: readMutedFromStorage(),
  volume: 0.6,
  unlocked: false,
  howls: {},
  HowlCtor: null,
  Howler: null,
  loaderPromise: null,
};

function persistMuted(muted: boolean): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, muted ? "true" : "false");
  } catch {
    /* private browsing — in-memory state still authoritative */
  }
}

function clamp01(v: number): number {
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

async function loadHowler(): Promise<void> {
  if (state.HowlCtor && state.Howler) return;
  if (state.loaderPromise) return state.loaderPromise;
  state.loaderPromise = (async () => {
    const mod = (await import("howler")) as unknown as {
      Howl: HowlConstructor;
      Howler: HowlerStatic;
    };
    state.HowlCtor = mod.Howl;
    state.Howler = mod.Howler;
    state.Howler.mute(state.muted);
  })();
  return state.loaderPromise;
}

function ensureHowl(soundId: SoundId): HowlInstance | null {
  const existing = state.howls[soundId];
  if (existing) return existing;
  if (!state.HowlCtor) return null;
  const howl = new state.HowlCtor({
    src: [SOUND_FILES[soundId]],
    volume: state.volume,
    html5: true,
  });
  state.howls[soundId] = howl;
  return howl;
}

/** Play a sound. No-op when muted or before Howler has loaded. */
export function play(soundId: SoundId, volume?: number): void {
  if (state.muted) return;
  if (typeof window === "undefined") return;
  void loadHowler().then(() => {
    const howl = ensureHowl(soundId);
    if (!howl) return;
    if (typeof volume === "number") howl.volume(clamp01(volume));
    howl.play();
  });
}

/** Stop a sound. Safe to call before play(). */
export function stop(soundId: SoundId): void {
  const howl = state.howls[soundId];
  if (!howl) return;
  howl.stop();
}

/** Toggle the global mute state. Persists to localStorage. */
export function setMuted(muted: boolean): void {
  state.muted = muted;
  persistMuted(muted);
  state.Howler?.mute(muted);
}

/** Current mute state (cheap synchronous read). */
export function isMuted(): boolean {
  return state.muted;
}

/** Set master volume 0..1 (clamped). Applies to future `play()` calls. */
export function setVolume(volume: number): void {
  state.volume = clamp01(volume);
}

/** Read master volume. */
export function getVolume(): number {
  return state.volume;
}

/**
 * Resume a suspended AudioContext. Idempotent — only resumes once.
 *
 * Wire this to a one-time first-user-gesture listener at app boot
 * (`pointerdown` OR `keydown`). iOS Safari + most browsers suspend the
 * context until user interaction; this is the unlock.
 */
export function unlock(): void {
  if (state.unlocked) return;
  state.unlocked = true;
  void loadHowler().then(() => {
    const ctx = state.Howler?.ctx;
    if (ctx?.state === "suspended" && typeof ctx.resume === "function") {
      void ctx.resume();
    } else if (ctx && typeof ctx.resume === "function") {
      // Fire resume() even without explicit state check — Howler keeps
      // ctx.state up to date but it's safer to call once.
      void ctx.resume();
    }
  });
}

/**
 * Wait for any pending lazy-load promises — for tests only.
 * Allows assertions to run after the async load chain resolves.
 */
export async function _flushForTests(): Promise<void> {
  if (state.loaderPromise) await state.loaderPromise;
  // Allow any chained .then(() => howl.play()) microtasks to flush.
  await new Promise((resolve) => setTimeout(resolve, 0));
}

/** Reset cache — for tests only. */
export function _resetSoundForTests(): void {
  state.muted = readMutedFromStorage();
  state.volume = 0.6;
  state.unlocked = false;
  state.howls = {};
  state.HowlCtor = null;
  state.Howler = null;
  state.loaderPromise = null;
}
