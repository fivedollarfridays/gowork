"use client";

import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

/**
 * Global CursorFlashlight — soft cream glow that follows the cursor.
 *
 * Was amber; per design feedback the warm tint pulled the eye away
 * from the editorial type, so it's now `--fg-primary` cream. Reads
 * as a soft "stage light" rather than a coloured highlight.
 *
 * Eased with rAF lerp (0.12) so the glow trails the cursor with a
 * cinematic lag instead of snapping. `mix-blend-mode: screen` keeps
 * it brightening (never darkening) the content below.
 *
 * Disabled on prefers-reduced-motion + coarse pointer + when the
 * user has toggled it off via the SiteHeader cursor button (state
 * persisted in localStorage["gowork-cursor-flashlight"]). Default
 * is "on" — the toggle is opt-out, not opt-in. Listens for
 * `storage` events (cross-tab sync) AND a custom
 * `gowork:cursor-flashlight-changed` event (same-tab instant sync,
 * since `storage` doesn't fire on the originating tab).
 */

interface CursorFlashlightProps {
  /** Force-disable for tests / coarse-pointer devices. */
  forceDisabled?: boolean;
}

const FLASHLIGHT_SIZE = 480;
const LERP = 0.12;
export const CURSOR_FLASHLIGHT_STORAGE_KEY = "gowork-cursor-flashlight";
export const CURSOR_FLASHLIGHT_EVENT = "gowork:cursor-flashlight-changed";

function isCoarsePointer(): boolean {
  if (typeof window === "undefined") return true;
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(pointer: coarse)").matches;
}

function readUserToggle(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(CURSOR_FLASHLIGHT_STORAGE_KEY) !== "off";
  } catch {
    return true;
  }
}

export function CursorFlashlight({ forceDisabled }: CursorFlashlightProps = {}): JSX.Element | null {
  const reducedMotion = usePrefersReducedMotion();
  const [coarse, setCoarse] = useState<boolean>(false);
  const [userEnabled, setUserEnabled] = useState<boolean>(true);
  const [active, setActive] = useState<boolean>(false);
  const elRef = useRef<HTMLDivElement | null>(null);
  const targetRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const currentRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    setCoarse(isCoarsePointer());
    setUserEnabled(readUserToggle());

    const onStorage = (e: StorageEvent) => {
      if (e.key === CURSOR_FLASHLIGHT_STORAGE_KEY) setUserEnabled(readUserToggle());
    };
    const onCustom = () => setUserEnabled(readUserToggle());
    window.addEventListener("storage", onStorage);
    window.addEventListener(CURSOR_FLASHLIGHT_EVENT, onCustom);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(CURSOR_FLASHLIGHT_EVENT, onCustom);
    };
  }, []);

  const disabled = forceDisabled || reducedMotion || coarse || !userEnabled;

  useEffect(() => {
    if (disabled) return;
    if (typeof window === "undefined") return;

    const onMove = (event: PointerEvent) => {
      targetRef.current = { x: event.clientX, y: event.clientY };
      if (!active) setActive(true);
      if (typeof document !== "undefined") {
        document.body.classList.add("cursor-active");
      }
    };
    const onLeave = () => {
      if (typeof document !== "undefined") {
        document.body.classList.remove("cursor-active");
      }
    };

    const tick = () => {
      currentRef.current.x += (targetRef.current.x - currentRef.current.x) * LERP;
      currentRef.current.y += (targetRef.current.y - currentRef.current.y) * LERP;
      const el = elRef.current;
      if (el) {
        el.style.transform = `translate3d(${currentRef.current.x - FLASHLIGHT_SIZE / 2}px, ${
          currentRef.current.y - FLASHLIGHT_SIZE / 2
        }px, 0)`;
      }
      rafRef.current = window.requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    rafRef.current = window.requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [disabled, active]);

  if (disabled) return null;

  return (
    <div
      ref={elRef}
      data-home-cursor-flashlight
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: `${FLASHLIGHT_SIZE}px`,
        height: `${FLASHLIGHT_SIZE}px`,
        pointerEvents: "none",
        mixBlendMode: "screen",
        zIndex: 5,
        opacity: active ? 1 : 0,
        background:
          "radial-gradient(circle, color-mix(in oklch, var(--fg-primary), transparent 55%) 0%, transparent 65%)",
        filter: "blur(40px)",
        transition: "opacity 240ms ease",
        willChange: "transform",
      }}
    />
  );
}
