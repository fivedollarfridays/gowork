/**
 * polish-2 T50 — Sound triggers wiring.
 *
 * Cross-driver pattern for the homepage chapters: each chapter dispatches
 * a custom DOM event on `document`, this module subscribes once at the
 * HomePage shell level and translates events → `playSound(soundId)`.
 *
 * Why DOM events (vs. direct imports) :
 *   - Driver E owns the audio wiring; Drivers B/C own the chapters.
 *   - Decoupling avoids a forced merge in chapter modules.
 *
 * First-user-gesture unlock: a one-time `pointerdown`/`keydown` listener
 * resumes the AudioContext (iOS Safari requires a gesture before any
 * `audioCtx.resume()` call will succeed).
 */
import { play, unlock, type SoundId } from "@/lib/wall/sound";

export const SOUND_EVENT_NAMES = {
  /** Chapter 4 step changed — Driver B/C fires when entering each map step. */
  CH4_STEP: "gowork:ch4-step",
  /** Chapter 5 fan-out animation completed. */
  CH5_FAN_COMPLETE: "gowork:ch5-fan-complete",
  /** Chapter 7 wage-cliff crossed (slider crossed the cliff X-coord). */
  CH7_CLIFF_CROSS: "gowork:ch7-cliff-cross",
} as const;

type SoundEventName = (typeof SOUND_EVENT_NAMES)[keyof typeof SOUND_EVENT_NAMES];

const EVENT_TO_SOUND: Record<SoundEventName, SoundId> = {
  [SOUND_EVENT_NAMES.CH4_STEP]: "footstep",
  [SOUND_EVENT_NAMES.CH5_FAN_COMPLETE]: "chime",
  [SOUND_EVENT_NAMES.CH7_CLIFF_CROSS]: "calculator-click",
};

/** Fire the Ch4 step event from a chapter component. Argument-free — the
 *  sound is the same regardless of which step. */
export function fireChapter4Step(): void {
  if (typeof document === "undefined") return;
  document.dispatchEvent(new Event(SOUND_EVENT_NAMES.CH4_STEP));
}

/** Fire the Ch5 fan-complete event when the slot fan-out finishes. */
export function fireChapter5FanComplete(): void {
  if (typeof document === "undefined") return;
  document.dispatchEvent(new Event(SOUND_EVENT_NAMES.CH5_FAN_COMPLETE));
}

/** Fire the Ch7 cliff-cross event when the slider crosses the cliff X. */
export function fireChapter7CliffCross(): void {
  if (typeof document === "undefined") return;
  document.dispatchEvent(new Event(SOUND_EVENT_NAMES.CH7_CLIFF_CROSS));
}

/**
 * Install the cross-driver sound-trigger listeners. Returns a cleanup
 * function that removes every listener (idempotent).
 *
 * Mount once at HomePage level via `useEffect(() => installSoundTriggers(), [])`.
 */
export function installSoundTriggers(): () => void {
  if (typeof document === "undefined") return () => undefined;

  const handlers: Array<[SoundEventName, () => void]> = [];
  for (const eventName of Object.values(SOUND_EVENT_NAMES) as SoundEventName[]) {
    const soundId = EVENT_TO_SOUND[eventName];
    const handler = () => play(soundId);
    document.addEventListener(eventName, handler);
    handlers.push([eventName, handler]);
  }

  // First-user-gesture unlock — fires once, then auto-removes.
  let unlocked = false;
  const onGesture = () => {
    if (unlocked) return;
    unlocked = true;
    unlock();
  };
  document.addEventListener("pointerdown", onGesture, { once: true });
  document.addEventListener("keydown", onGesture, { once: true });

  return () => {
    for (const [eventName, handler] of handlers) {
      document.removeEventListener(eventName, handler);
    }
    document.removeEventListener("pointerdown", onGesture);
    document.removeEventListener("keydown", onGesture);
  };
}
