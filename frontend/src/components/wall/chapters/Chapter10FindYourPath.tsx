"use client";

/**
 * W3 Driver C — Chapter 10 Find Your Path (T3.20 + T3.21).
 *
 * The closing chapter. Camera (set in `cameraChoreography.CHAPTER_CAMERAS[10]`)
 * settles back over Fort Worth at zoom 11 / pitch 0 — the "we've returned
 * home" framing. The overlay locks the editorial copy + a single primary
 * CTA "Start your assessment".
 *
 * # Narrative Reset (sprint/narrative-reset)
 *
 * The secondary "Or read the open-source code on GitHub →" link was
 * removed. User-facing chapter copy must serve the user (someone facing
 * employment barriers), not the judges. MIT licensing + GitHub URLs live
 * in the LICENSE file and the Devpost submission form — NOT in the
 * editorial chapter overlay. A clean primary CTA wins.
 *
 * # View Transitions hand-off (T3.21)
 *
 * The CTA navigates to `/assess`, wrapped in
 * `startViewTransitionWithFallback` so Chrome users get the cinematic
 * morph (the map element transitions into the form's hero) and Firefox
 * users get a standard navigation. The shared
 * `view-transition-name: wall-to-assess` is set as an inline style on
 * the chapter's morph target — the matching name on /assess is set in
 * the page component's outer wrapper.
 *
 * # Reduced-motion contract
 *
 * `prefers-reduced-motion: reduce` causes the View Transitions API to
 * be skipped (the CTA still works as a normal button). The h2 + body
 * are static text — no animation gating needed.
 *
 * # Tokens-only styling
 *
 * Surface uses `var(--bg-base)`, `var(--fg-primary)`, `var(--accent)` —
 * never raw hex. Audit:tokens + audit:brand stay clean.
 */

import { useRouter } from "next/navigation";
import { t } from "@/lib/i18n";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { startViewTransitionWithFallback, WALL_TO_ASSESS_TRANSITION_NAME } from "@/lib/wall/viewTransitions";
import { BrandMark } from "../BrandMark";

export interface Chapter10FindYourPathProps {
  /** LOCAL chapter progress 0..1. WallContainer slices via wallProgress. */
  progress: number;
  /** True when the global chapter pointer is on Ch10. */
  active?: boolean;
  /** Optional reduced-motion override (else hook). */
  reducedMotion?: boolean;
}

const HEADING_ID = "chapter10-heading";

export function Chapter10FindYourPath({
  progress: _progress,
  active: _active,
  reducedMotion: reducedMotionProp,
}: Chapter10FindYourPathProps): JSX.Element {
  const router = useRouter();
  const prefersReduced = usePrefersReducedMotion();
  const reducedMotion = reducedMotionProp ?? prefersReduced;

  const handlePrimaryClick = (): void => {
    startViewTransitionWithFallback(
      () => router.push("/assess"),
      { reducedMotion },
    );
  };

  return (
    <section
      data-testid="chapter10-find-your-path"
      data-chapter="10"
      data-chapter-id="find-your-path"
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-labelledby={HEADING_ID}
      aria-label={t("wall.chapter10.aria")}
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "2rem",
        padding: "3rem 1.5rem",
        background:
          "linear-gradient(180deg, color-mix(in oklch, var(--bg-base) 70%, transparent) 0%, var(--bg-base) 75%)",
        color: "var(--fg-primary)",
      }}
    >
      <div
        data-testid="chapter10-morph-target"
        style={{
          maxWidth: "44rem",
          textAlign: "center",
          viewTransitionName: WALL_TO_ASSESS_TRANSITION_NAME,
        }}
      >
        <h2
          id={HEADING_ID}
          style={{
            margin: 0,
            fontFamily: "var(--font-inter-stack)",
            fontSize: "clamp(2.25rem, 5vw, 4rem)",
            letterSpacing: "-0.04em",
            lineHeight: 1.05,
            color: "var(--fg-primary)",
          }}
        >
          {t("wall.chapter10.hero")}
        </h2>
        <p
          style={{
            marginTop: "1.25rem",
            fontSize: "clamp(1rem, 1.6vw, 1.25rem)",
            lineHeight: 1.55,
            color: "var(--fg-secondary, var(--fg-primary))",
          }}
        >
          {t("wall.chapter10.subhero")}
        </p>
        <p
          style={{
            marginTop: "1rem",
            fontSize: "1rem",
            lineHeight: 1.6,
            color: "var(--fg-secondary, var(--fg-primary))",
            opacity: 0.85,
          }}
        >
          {t("wall.chapter10.body")}
        </p>

        <div style={{ marginTop: "2.5rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
          <button
            type="button"
            data-testid="chapter10-cta-primary"
            aria-label={t("wall.chapter10.ctaPrimary")}
            onClick={handlePrimaryClick}
            style={{
              minWidth: "min(20rem, 90vw)",
              padding: "1rem 2rem",
              fontSize: "1.125rem",
              fontWeight: 700,
              color: "var(--bg-base)",
              background: "var(--accent, var(--accent-cyan))",
              border: "0",
              borderRadius: "var(--radius)",
              cursor: "pointer",
              boxShadow: "0 6px 24px color-mix(in oklch, var(--accent) 35%, transparent)",
            }}
          >
            {t("wall.chapter10.ctaPrimary")}
          </button>
        </div>
      </div>

      <footer
        data-testid="chapter10-footer"
        style={{
          marginTop: "auto",
          display: "flex",
          alignItems: "center",
          gap: "0.625rem",
          fontSize: "0.875rem",
          color: "var(--fg-secondary, var(--fg-primary))",
          opacity: 0.85,
        }}
      >
        <BrandMark size={20} />
        <span>{t("wall.chapter10.footerBrand")}</span>
      </footer>
    </section>
  );
}
