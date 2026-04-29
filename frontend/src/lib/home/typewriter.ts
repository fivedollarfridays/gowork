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

/**
 * Animate the typewriter reveal. Returns a Promise that resolves with the
 * full text once the animation completes. Aborts cleanly when `signal`
 * fires (chapter unmount / scroll-out).
 */
export async function typewrite(
  _text: string,
  _opts: TypewriterOptions = {},
  _signal?: AbortSignal,
): Promise<string> {
  // SCAFFOLD — Driver B fills.
  return _text;
}
