/**
 * Wall design tokens — TS exports for framer-motion + JS consumers.
 *
 * The CSS partials in src/app/styles/tokens/* hold the canonical visual
 * values; this file mirrors a subset for code that builds animation configs
 * at runtime (springs, easings, durations, stagger offsets, type-scale
 * lookup, font axes). Single source of truth = these constants — no magic
 * numbers in motion sites.
 *
 * Append-only, additive. Readonly via `as const`. Plan-locked values from
 * docs/visual-rebirth-plan.md "Design system → Motion".
 */

// ─── T1.19 — Spring presets ─────────────────────────────────────────────────

/** Soft spring: long settle, gentle. Used for ambient, idle motion. */
export const SPRING_SOFT = { stiffness: 100, damping: 20 } as const;

/** Snappy spring: balanced, the default for chapter transitions. */
export const SPRING_SNAPPY = { stiffness: 200, damping: 25 } as const;

/** Elastic spring: high stiffness, low damping → playful overshoot.
 *  Reserved for celebratory beats (Ch 9 outcomes, Ch 10 finale). */
export const SPRING_ELASTIC = { stiffness: 300, damping: 18 } as const;

// ─── T1.20 — Easing + duration ──────────────────────────────────────────────

/** Linear's signature cubic-bezier — the "real software" feel.
 *  Used for non-spring transitions (opacity fades, layout shifts). */
export const EASE_LINEAR_SIG = [0.32, 0.72, 0, 1] as const;

/** Apple/Vercel-grade ease-out: most of the motion happens early,
 *  the tail is gentle. The default for incoming motion. */
export const EASE_OUT = [0.16, 1, 0.3, 1] as const;

/** Duration baseline (ms). Just past instant — fast enough to not feel
 *  laggy, slow enough to register the change. */
export const DURATION_BASELINE_MS = 280;

// ─── T1.21 — Stagger timing ─────────────────────────────────────────────────

/** Per-child offset (seconds) for staggered enter animations.
 *  W2/W3/W4 chapter scrollytelling default. Pre-W1 motion.tsx keeps its
 *  0.25 cadence for legacy shadcn/dashboard pages — Driver C adopts this
 *  token in NEW Wall components, not via retrofit. */
export const STAGGER_CHILD_OFFSET_S = 0.05;

/** Default initial state for staggered children (faded + offset down). */
export const STAGGER_INITIAL_DEFAULT = { opacity: 0, y: 20 } as const;

/** Default animate-to state for staggered children (visible + at rest). */
export const STAGGER_ANIMATE_DEFAULT = { opacity: 1, y: 0 } as const;
