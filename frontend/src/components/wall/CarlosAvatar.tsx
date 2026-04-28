"use client";

/**
 * W3 Driver B — CarlosAvatar (T3.11).
 *
 * Self-drawn silhouette of Carlos, animates along the 5-waypoint path.
 *
 * # Why a silhouette
 *
 * No proprietary art. The figure is a public-domain pictographic shape
 * (head circle + torso trapezoid + walking-stride legs) drawn here
 * from scratch. License-clean for a hackathon submission.
 *
 * # Footstep rate limit
 *
 * Audio is rate-limited to 1 step per `FOOTSTEP_THRESHOLD` of progress
 * delta (default 4%). This keeps the audio humane: a fast scroll across
 * Ch7 produces ~25 footsteps maximum, not 1000.
 *
 * # Reduced motion
 *
 * When `reducedMotion` is true:
 *   - the walking-stride CSS animation is disabled
 *   - footstep audio does NOT fire
 *   - the silhouette stays still (still readable)
 */

import { useEffect, useMemo, useRef } from "react";
import type { ReactElement } from "react";
import { play } from "@/lib/wall/sound";
import { positionAt, segmentIndexAt } from "@/lib/wall/avatarPath";
import { t } from "@/lib/i18n";

/** Progress delta required between footstep audio plays (default: 4%). */
export const FOOTSTEP_THRESHOLD = 0.04 as const;

interface CarlosAvatarProps {
  /** Normalized progress 0..1 along the 5-waypoint polyline. */
  progress: number;
  /** When true, CSS animation + audio are disabled. */
  reducedMotion?: boolean;
}

function clamp01(v: number): number {
  if (!Number.isFinite(v)) return 0;
  if (v < 0) return 0;
  if (v > 1) return 1;
  return v;
}

export function CarlosAvatar({
  progress,
  reducedMotion = false,
}: CarlosAvatarProps): ReactElement {
  const clamped = useMemo(() => clamp01(progress), [progress]);
  const pos = useMemo(() => positionAt(clamped), [clamped]);
  const segIdx = useMemo(() => segmentIndexAt(clamped), [clamped]);
  const lastFootstepAtRef = useRef<number>(-1);

  useEffect(() => {
    if (reducedMotion) return;
    const last = lastFootstepAtRef.current;
    if (last < 0 || Math.abs(clamped - last) >= FOOTSTEP_THRESHOLD) {
      play("footstep");
      lastFootstepAtRef.current = clamped;
    }
  }, [clamped, reducedMotion]);

  const ariaLabel = t("wall.chapter07.aria");

  return (
    <div
      data-testid="carlos-avatar"
      role="img"
      aria-label={ariaLabel}
      data-progress={clamped.toFixed(3)}
      data-lng={pos.longitude.toFixed(6)}
      data-lat={pos.latitude.toFixed(6)}
      data-segment-index={String(segIdx)}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      className="carlos-avatar"
      style={{
        width: 32,
        height: 48,
        display: "inline-block",
      }}
    >
      <svg
        viewBox="0 0 32 48"
        width="100%"
        height="100%"
        aria-hidden="true"
        focusable="false"
      >
        {/* Head */}
        <circle cx={16} cy={8} r={6} fill="var(--accent-amber)" />
        {/* Torso */}
        <path
          d="M 10 16 L 22 16 L 20 30 L 12 30 Z"
          fill="var(--accent-amber)"
        />
        {/* Walking-stride legs (subtle inline animation when motion allowed) */}
        <g
          style={{
            transformOrigin: "16px 30px",
            animation:
              reducedMotion || typeof window === "undefined"
                ? "none"
                : "carlos-stride 800ms ease-in-out infinite",
          }}
        >
          <rect x={11} y={30} width={3} height={14} fill="var(--accent-amber)" />
          <rect x={18} y={30} width={3} height={14} fill="var(--accent-amber)" />
        </g>
      </svg>
      <style>{`
        @keyframes carlos-stride {
          0%, 100% { transform: rotate(-6deg); }
          50% { transform: rotate(6deg); }
        }
      `}</style>
    </div>
  );
}

export default CarlosAvatar;
