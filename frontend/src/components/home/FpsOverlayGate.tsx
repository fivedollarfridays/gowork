"use client";

/**
 * FpsOverlayGate — polish-2 T54.
 *
 * Dev-only FPS HUD. Triple-gated:
 *   1. process.env.NODE_ENV !== "production"
 *   2. localStorage["gowork-fps"] === "1"
 *   3. browser context (typeof window !== "undefined")
 *
 * Renders a bottom-right HUD with the rolling 60-frame avg FPS plus the
 * current chapter index. Sample loop is identical in spirit to the wall
 * `FpsOverlay`, but the wrapper here is purpose-built for the polish-2
 * homepage so the data-attribute and chapter-index integration are
 * scoped to this surface.
 */
import { useEffect, useRef, useState } from "react";

const SAMPLE_SIZE = 60;
const FLAG_KEY = "gowork-fps";

interface FpsOverlayGateProps {
  /** Active chapter (1..8). Optional — defaults to "—". */
  chapter?: number;
}

function readFlag(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(FLAG_KEY) === "1";
  } catch {
    return false;
  }
}

function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

export function FpsOverlayGate({ chapter }: FpsOverlayGateProps = {}): JSX.Element | null {
  const enabled = !isProduction() && readFlag();
  const [fps, setFps] = useState<number>(0);
  const samplesRef = useRef<number[]>([]);
  const lastTsRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;
    function loop(ts: number) {
      if (lastTsRef.current !== null) {
        const delta = ts - lastTsRef.current;
        if (delta > 0) {
          const instant = 1000 / delta;
          const samples = samplesRef.current;
          samples.push(instant);
          if (samples.length > SAMPLE_SIZE) samples.shift();
          const avg = samples.reduce((s, v) => s + v, 0) / samples.length;
          setFps(Math.round(avg));
        }
      }
      lastTsRef.current = ts;
      rafRef.current = requestAnimationFrame(loop);
    }
    rafRef.current = requestAnimationFrame(loop);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [enabled]);

  if (!enabled) return null;
  return (
    <div
      data-fps-overlay
      role="status"
      aria-label="rendering frames per second"
      className="font-mono-data fixed bottom-2 right-2 rounded bg-black/70 px-2 py-1 text-xs text-cyan-300"
      style={{ zIndex: 70 }}
    >
      {fps} fps · ch {chapter ?? "—"}
    </div>
  );
}
