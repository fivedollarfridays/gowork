"use client";

/**
 * polish-2 T40 — Branded segment-level loading shell (Driver D).
 *
 * Next.js App Router auto-wraps server-rendered children in <Suspense>
 * and uses the nearest `loading.tsx` as the fallback. This shell pairs
 * the wall-metaphor atmosphere (Ch1 background) with a brand-mark loop
 * + 4-row skeleton so a slow data fetch never collapses the page into a
 * blank surface.
 *
 * Honors prefers-reduced-motion: the brand-loop animation is driven by
 * the global motion tokens (`--motion-disabled` flips to 1 under reduce),
 * so the SVG renders static when motion is suppressed.
 */
import { TranslationProvider } from "@/hooks/useTranslation";
import { EdgeStateShell } from "@/components/edge-states/EdgeStateShell";
import { LoadingState } from "@/components/wall/LoadingState";

function BrandLoop(): JSX.Element {
  // Inline SVG: rotating ring + amber center pulse. Motion is gated by
  // CSS keyframe `brand-loop-spin` (defined in animations tokens or
  // home-chapters.css) — when --motion-disabled = 1 the keyframe is a
  // no-op, leaving a static ring. The pulse uses opacity-only animation
  // for the same reason.
  return (
    <svg
      data-brand-loop
      role="img"
      aria-label="Loading"
      width={56}
      height={56}
      viewBox="0 0 56 56"
      style={{ display: "block" }}
    >
      <circle
        cx={28}
        cy={28}
        r={22}
        fill="none"
        stroke="var(--accent-cyan, #22D3EE)"
        strokeWidth={2}
        strokeOpacity={0.25}
      />
      <circle
        cx={28}
        cy={28}
        r={22}
        fill="none"
        stroke="var(--accent-cyan, #22D3EE)"
        strokeWidth={2}
        strokeDasharray="20 120"
        strokeLinecap="round"
        style={{
          transformOrigin: "50% 50%",
          animation: "brand-loop-spin 1.6s linear infinite",
        }}
      />
      <circle
        cx={28}
        cy={28}
        r={6}
        fill="var(--accent-amber, #F59E0B)"
        style={{
          animation: "brand-loop-pulse 1.6s ease-in-out infinite",
        }}
      />
    </svg>
  );
}

export default function Loading(): JSX.Element {
  return (
    <TranslationProvider>
      <EdgeStateShell
        kind="loading"
        eyebrow="Loading"
        accent="cyan"
        headline={<BrandLoop />}
        body={<LoadingState lines={4} />}
      />
    </TranslationProvider>
  );
}
