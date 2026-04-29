"use client";

import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";

/**
 * Home CursorFlashlight — sprint/gowork-facelift Driver A.
 *
 * Soft 480x480 amber glow that follows the cursor across the WHOLE
 * viewport (not just the Mapbox canvas — that's the existing
 * `wall/MapCursorFlashlight`). Uses `mix-blend-mode: screen` so the
 * glow brightens the chapter content beneath it without darkening it.
 *
 * Eased with rAF lerp (0.12) so the glow trails the cursor with a
 * cinematic lag instead of snapping. Activates when the document has
 * `body.cursor-active` (toggled on first pointermove); deactivates on
 * pointerleave.
 *
 * Disabled on prefers-reduced-motion + coarse pointer + when explicitly
 * forced off via `forceDisabled` (used by Driver D in tests).
 */

interface CursorFlashlightProps {
  /** Force-disable for tests / coarse-pointer devices. */
  forceDisabled?: boolean;
}

const FLASHLIGHT_SIZE = 480;
const LERP = 0.12;

function isCoarsePointer(): boolean {
  if (typeof window === "undefined") return true;
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(pointer: coarse)").matches;
}

export function CursorFlashlight({ forceDisabled }: CursorFlashlightProps = {}): JSX.Element | null {
  const reducedMotion = usePrefersReducedMotion();
  const [coarse, setCoarse] = useState<boolean>(false);
  const [active, setActive] = useState<boolean>(false);
  const elRef = useRef<HTMLDivElement | null>(null);
  const targetRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const currentRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    setCoarse(isCoarsePointer());
  }, []);

  const disabled = forceDisabled || reducedMotion || coarse;

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
          "radial-gradient(circle, color-mix(in oklch, var(--accent-amber), transparent 40%) 0%, transparent 65%)",
        filter: "blur(40px)",
        transition: "opacity 240ms ease",
        willChange: "transform",
      }}
    />
  );
}
