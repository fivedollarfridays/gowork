"use client";

/**
 * Chapter 08 — Find Your Path (Driver B + Driver C polish-2).
 *
 * Manifesto + giant Truus-style wordmark closer. Per Shawn's narrative-reset
 * directive (commit b233102) the deprecated "5,189 / 13 / 2 / MIT" stat band
 * is gone — just the four-line manifesto, the CTA-XL, and the wordmark.
 *
 * polish-2 Driver C:
 *   - T33 — manifesto lines fade `--fg-secondary → --fg-primary` once they
 *     enter the viewport (uses IntersectionObserver). Reduced-motion just
 *     paints the final color.
 *   - T34 — wordmark row 1 reveals a "GoWork is in Fort Worth, TX" tooltip
 *     on hover/focus + a cyan path-line under the wordmark.
 *   - T35 — primary CTA wraps the navigation in `document.startViewTransition`
 *     when supported (paired with `view-transition-name: assess-pill` on
 *     /assess page hero) and falls back to plain navigation when not.
 *   - T36 — first manifesto line wrapped in `<DropCap chapter="8">`.
 *
 * # Reduced-motion contract
 *
 * The line-by-line stagger reveal and the opposing-scrub on the wordmark
 * rows are skipped under `prefers-reduced-motion: reduce`. The manifesto
 * still renders; the wordmark still renders, just statically.
 */

import { useEffect, useRef, useState, type MouseEvent } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";
import { useViewTransitionsSupport } from "@/hooks/useViewTransitionsSupport";
import { DropCap } from "../typography/DropCap";
import { Ch08Wordmark } from "./_internal/Ch08Wordmark";

export interface Chapter08FindYourPathProps {
  id?: string;
}

export function Chapter08FindYourPath({
  id = "chapter-08",
}: Chapter08FindYourPathProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const router = useRouter();
  const vtSupported = useViewTransitionsSupport();

  const sectionRef = useGsapScrollTrigger<HTMLElement>(({ el, gsap, reduced: r }) => {
    if (r) return;
    gsap.from(el.querySelectorAll(".ch08-cta"), {
      y: 30,
      opacity: 0,
      duration: 0.8,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch08-cta"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
    gsap.to(el.querySelector(".ch08-wordmark .wm-row-1"), {
      xPercent: -8,
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
    gsap.to(el.querySelector(".ch08-wordmark .wm-row-2"), {
      xPercent: 8,
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top bottom",
        end: "bottom top",
        scrub: true,
      },
    });
    gsap.from(el.querySelectorAll(".ch08-wordmark .wm-row"), {
      opacity: 0,
      y: 80,
      stagger: 0.18,
      duration: 1.2,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch08-wordmark"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
  });

  const onCtaClick = (e: MouseEvent<HTMLAnchorElement>) => {
    // Allow modifier-clicks (open in new tab) to fall through to default.
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    if (!vtSupported || reduced) return;
    e.preventDefault();
    const doc = document as unknown as {
      startViewTransition?: (cb: () => void) => unknown;
    };
    if (typeof doc.startViewTransition !== "function") {
      router.push("/assess");
      return;
    }
    doc.startViewTransition(() => {
      router.push("/assess");
    });
  };

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="warm"
      data-screen-label="08 Find your path"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch08-h2"
      className="chapter ch08"
      style={{
        padding: "160px 80px 0",
        background:
          "linear-gradient(180deg, rgba(245,158,11,0.06), rgba(245,158,11,0.02) 60%, transparent)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        gap: "80px",
      }}
    >
      <div
        className="ch08-content"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "40px",
          maxWidth: "70rem",
        }}
      >
        <span
          className="ch08-eb"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "12px",
            fontFamily: "var(--font-mono-data)",
            fontSize: "11px",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "var(--fg-muted)",
          }}
        >
          <span className="num" style={{ color: "var(--accent-amber)", fontWeight: 600 }}>
            08
          </span>
          <span className="lab">{t("home.ch8.eyebrow")}</span>
        </span>

        <Manifesto t={t} reduced={reduced} />

        <div
          className="ch08-cta"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            alignItems: "flex-start",
          }}
        >
          <a
            className="cta cta-primary cta-xl"
            href="/assess"
            onClick={onCtaClick}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "16px",
              padding: "22px 34px",
              borderRadius: "999px",
              background: "var(--accent-cyan)",
              color: "#0A0E1A",
              fontWeight: 600,
              fontSize: "18px",
              letterSpacing: "-0.01em",
              boxShadow:
                "0 8px 24px color-mix(in oklch, var(--accent-cyan), transparent 60%)",
              viewTransitionName: "ch8-cta-pill",
            }}
          >
            <span>{t("home.ch8.ctaPrimary")}</span>
            <span className="cta-arr">→</span>
          </a>
          <span
            className="ch08-meta"
            style={{
              fontFamily: "var(--font-mono-data)",
              fontSize: "11.5px",
              letterSpacing: "0.06em",
              color: "var(--fg-muted)",
              marginLeft: "4px",
            }}
          >
            {t("home.ch8.ctaMeta")}
          </span>
        </div>
      </div>

      <Ch08Wordmark
        row1={t("home.ch8.wordmarkRow1")}
        row2={t("home.ch8.wordmarkRow2")}
        spokenCity={t("home.ch8.wordmark.spokenCityFw")}
        comingPrefix={t("home.ch8.wordmark.spokenCityComing")}
      />
    </section>
  );
}

/** Manifesto — uses an IntersectionObserver to mark each line as
 *  "revealed" when it scrolls into view. Reduced-motion paints the
 *  final state up front. */
function Manifesto({ t, reduced }: { t: (k: string) => string; reduced: boolean }) {
  const ref = useRef<HTMLHeadingElement | null>(null);
  const [revealedAll, setRevealedAll] = useState<boolean>(reduced);

  useEffect(() => {
    if (reduced) {
      setRevealedAll(true);
      return;
    }
    if (typeof window === "undefined") return;
    const root = ref.current;
    if (!root) return;
    const lines = Array.from(root.querySelectorAll<HTMLElement>(".line"));
    if (lines.length === 0) return;

    if (typeof IntersectionObserver === "undefined") {
      lines.forEach((ln) => ln.setAttribute("data-revealed", "true"));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            (entry.target as HTMLElement).setAttribute("data-revealed", "true");
            io.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.6 },
    );
    lines.forEach((ln) => io.observe(ln));
    return () => io.disconnect();
  }, [reduced]);

  const line4Raw = t("home.ch8.line4");
  const tuesday = t("home.ch8.line4Tuesday");
  const [l4a, l4b] = line4Raw.split("{{tuesday}}");
  return (
    <h2
      id="ch08-h2"
      className="ch08-h2"
      ref={ref}
      style={{
        fontSize: "clamp(2.4rem, 1.4rem + 3.4vw, 6rem)",
        fontWeight: 800,
        letterSpacing: "-0.035em",
        lineHeight: 1.05,
      }}
    >
      <span
        className="line"
        data-revealed={revealedAll ? "true" : "false"}
        style={{ display: "block" }}
      >
        <DropCap chapter="8">{t("home.ch8.line1")}</DropCap>
      </span>
      <span
        className="line italic-axis"
        data-revealed={revealedAll ? "true" : "false"}
        style={{ display: "block", fontStyle: "oblique -10deg" }}
      >
        {t("home.ch8.line2")}
      </span>
      <span
        className="line"
        data-revealed={revealedAll ? "true" : "false"}
        style={{ display: "block" }}
      >
        {t("home.ch8.line3")}
      </span>
      <span
        className="line"
        data-revealed={revealedAll ? "true" : "false"}
        style={{ display: "block" }}
      >
        {l4a}
        <em
          style={{
            background:
              "linear-gradient(90deg, var(--accent-amber), var(--accent-rose))",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            fontStyle: "normal",
          }}
        >
          {tuesday}
        </em>
        {l4b ?? ""}
      </span>
    </h2>
  );
}

