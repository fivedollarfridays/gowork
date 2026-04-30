/**
 * typewriter.ts — polish-2 T19.
 *
 * Animated character-by-character text reveal (NYT Snow Fall HUD style).
 * Used for the Ch4 Mapbox HUD typed-in entrance and any other surface that
 * wants a "typing" reveal. Reduced-motion users get the final string
 * instantly — the helper accepts an `instant` flag.
 *
 * Driver B owns the canonical implementation.
 */

export interface TypewriterOptions {
  /** ms per character (default 55ms ≈ 18 char/sec). */
  charDelay?: number;
  /** Skip animation; resolve immediately with the full text. */
  instant?: boolean;
  /** Optional onTick(currentString) callback fired per character. */
  onTick?: (current: string) => void;
}

const DEFAULT_CHAR_DELAY_MS = 55;

/**
 * Animate the typewriter reveal. Returns a Promise that resolves with the
 * full text once the animation completes. Aborts cleanly when `signal`
 * fires (chapter unmount / scroll-out).
 *
 * If `signal.aborted` is already `true`, the helper resolves immediately
 * with an empty string and never invokes `onTick` — callers should treat
 * that as "give the user the final value via SSR copy."
 */
export async function typewrite(
  text: string,
  opts: TypewriterOptions = {},
  signal?: AbortSignal,
): Promise<string> {
  if (signal?.aborted) return "";
  if (opts.instant) {
    opts.onTick?.(text);
    return text;
  }
  const charDelay = opts.charDelay ?? DEFAULT_CHAR_DELAY_MS;
  return revealAnimated(text, charDelay, opts.onTick, signal);
}

function revealAnimated(
  text: string,
  charDelay: number,
  onTick: ((current: string) => void) | undefined,
  signal: AbortSignal | undefined,
): Promise<string> {
  return new Promise((resolve) => {
    let current = "";
    let i = 0;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const cleanup = () => {
      if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      if (signal) {
        signal.removeEventListener("abort", onAbort);
      }
    };

    const onAbort = () => {
      cleanup();
      resolve(current);
    };

    if (signal) {
      signal.addEventListener("abort", onAbort, { once: true });
    }

    const tick = () => {
      if (signal?.aborted) {
        cleanup();
        resolve(current);
        return;
      }
      current += text[i];
      i += 1;
      onTick?.(current);
      if (i >= text.length) {
        cleanup();
        resolve(current);
        return;
      }
      timeoutId = setTimeout(tick, charDelay);
    };

    if (text.length === 0) {
      cleanup();
      resolve("");
      return;
    }
    timeoutId = setTimeout(tick, charDelay);
  });
}
