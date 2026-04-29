"use client";

/**
 * Chapter 02 — The Numbers (Driver B, sprint/gowork-facelift).
 *
 * Pinned 2x2 stat grid. Each stat is a single oversized counter that runs
 * a count-up tween on scroll (top 85% trigger, 1.6s power2.out, toggleActions
 * play none none reverse — matches the static design JS).
 *
 * # Reduced-motion contract
 *
 * Under `prefers-reduced-motion: reduce` the count-up is collapsed to its
 * final state on first paint (no tween).
 */

import { useEffect, useRef } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useGsapScrollTrigger } from "@/lib/home/gsap";

interface StatSpec {
  target: number;
  prefix: string;
  suffix: string;
  capKey: string;
  /** Visual gradient key — drives the .ch02-stat ordinal class for CSS. */
  ordinal: 1 | 2 | 3 | 4;
}

const STATS: readonly StatSpec[] = [
  { target: 600000, prefix: "", suffix: "+", capKey: "home.ch2.stat1Cap", ordinal: 1 },
  { target: 87, prefix: "", suffix: " min", capKey: "home.ch2.stat2Cap", ordinal: 2 },
  { target: 7, prefix: "", suffix: "", capKey: "home.ch2.stat3Cap", ordinal: 3 },
  { target: 22.50, prefix: "$", suffix: "/hr", capKey: "home.ch2.stat4Cap", ordinal: 4 },
];

/**
 * T14 — locale-aware grouping. EN uses comma thousands separators
 * (`600,000+`); ES uses European dot separators (`600.000+`). The
 * `Intl.NumberFormat` BCP-47 tags (`en-US` vs `es-ES`) drive the swap.
 */
function localeTag(locale: string): string {
  return locale === "es" ? "es-ES" : "en-US";
}

function formatStat(spec: StatSpec, value: number, locale: string): string {
  const fixed = spec.target % 1 === 0
    ? Math.round(value).toString()
    : value.toFixed(2);
  const localized = spec.target >= 1000
    ? Math.round(value).toLocaleString(localeTag(locale))
    : fixed;
  return spec.prefix + localized + spec.suffix;
}

export interface Chapter02TheNumbersProps {
  id?: string;
}

export function Chapter02TheNumbers({ id = "chapter-02" }: Chapter02TheNumbersProps) {
  const { t, locale } = useTranslation();
  const reduced = usePrefersReducedMotion();

  const sectionRef = useGsapScrollTrigger<HTMLElement>(({ el, gsap, reduced: r }) => {
    if (r) return;
    const stats = el.querySelectorAll<HTMLElement>("[data-stat]");
    const tag = localeTag(locale);
    stats.forEach((stat) => {
      const target = parseFloat(stat.dataset.target ?? "0");
      const prefix = stat.dataset.prefix ?? "";
      const suffix = stat.dataset.suffix ?? "";
      const numEl = stat.querySelector<HTMLElement>("[data-stat-num]");
      if (!numEl) return;
      const obj = { v: 0 };
      const fmt = (n: number) => {
        const v = target >= 1000
          ? Math.round(n).toLocaleString(tag)
          : (target % 1 === 0 ? Math.round(n).toString() : n.toFixed(2));
        return prefix + v + suffix;
      };
      // Reset to "0..." before tween so the count-up reads top-down.
      numEl.textContent = fmt(0);
      gsap.to(obj, {
        v: target,
        duration: 1.6,
        ease: "power2.out",
        scrollTrigger: {
          trigger: stat,
          start: "top 85%",
          toggleActions: "play none none reverse",
        },
        onUpdate: () => {
          numEl.textContent = fmt(obj.v);
        },
        onComplete: () => {
          numEl.textContent = fmt(target);
        },
      });
    });
    gsap.from(el.querySelectorAll(".ch02-pull"), {
      opacity: 0,
      y: 30,
      duration: 1.0,
      ease: "power3.out",
      scrollTrigger: {
        trigger: el.querySelector(".ch02-pull"),
        start: "top 80%",
        toggleActions: "play none none reverse",
      },
    });
  });

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="dark"
      data-screen-label="02 The numbers"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch02-heading"
      className="chapter ch02"
      style={{ minHeight: "100vh", padding: 0 }}
    >
      <div
        className="ch02-pin"
        style={{
          position: "relative",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "120px 80px 80px",
        }}
      >
        <h2
          id="ch02-heading"
          className="ch02-eb"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "14px",
            fontFamily: "var(--font-mono-data)",
            fontSize: "11px",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "var(--fg-muted)",
            marginBottom: "32px",
            fontWeight: 400,
          }}
        >
          <span className="num" style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>
            02
          </span>
          <span className="lab" style={{ color: "var(--fg-secondary)" }}>
            {t("home.ch2.eyebrow")}
          </span>
          <span
            className="rule"
            aria-hidden="true"
            style={{
              flex: 1,
              height: "1px",
              background: "color-mix(in oklch, var(--fg-primary), transparent 88%)",
            }}
          />
        </h2>

        <div
          className="ch02-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, 1fr)",
            gap: "64px 80px",
            alignItems: "end",
          }}
        >
          {STATS.map((spec, i) => (
            <Stat
              key={i}
              spec={spec}
              cap={t(spec.capKey)}
              reduced={reduced}
              locale={locale}
            />
          ))}
        </div>

        <PullQuote
          raw={t("home.ch2.pull")}
          em={t("home.ch2.pullTuesday")}
        />
      </div>
    </section>
  );
}

interface StatProps {
  spec: StatSpec;
  cap: string;
  reduced: boolean;
  locale: string;
}

function Stat({ spec, cap, reduced, locale }: StatProps) {
  const numRef = useRef<HTMLSpanElement>(null);

  // Reduced-motion: snap to final value on mount.
  useEffect(() => {
    if (reduced && numRef.current) {
      numRef.current.textContent = formatStat(spec, spec.target, locale);
    }
  }, [reduced, spec, locale]);

  const ordinalGradient = ordinalToGradient(spec.ordinal);
  // Default to the final value so SSR/jsdom + no-JS users see the truth.
  // GSAP overrides to 0 + counts up on scroll when motion is enabled.
  const initial = formatStat(spec, spec.target, locale);

  return (
    <div
      className={`ch02-stat ch02-stat-${spec.ordinal}`}
      data-stat=""
      data-target={
        spec.target % 1 === 0 ? String(spec.target) : spec.target.toFixed(2)
      }
      data-prefix={spec.prefix}
      data-suffix={spec.suffix}
      style={{ display: "flex", flexDirection: "column", gap: "12px" }}
    >
      <span
        ref={numRef}
        data-stat-num=""
        className="stat-num"
        style={{
          fontSize: "clamp(4rem, 2rem + 7vw, 9rem)",
          fontWeight: 900,
          letterSpacing: "-0.04em",
          lineHeight: 0.9,
          fontVariantNumeric: "tabular-nums",
          fontFeatureSettings: '"tnum"',
          background: ordinalGradient,
          WebkitBackgroundClip: "text",
          backgroundClip: "text",
          color: "transparent",
        }}
      >
        {initial}
      </span>
      <span
        className="stat-cap"
        style={{
          fontSize: "15px",
          lineHeight: 1.55,
          color: "var(--fg-secondary)",
          maxWidth: "28rem",
        }}
      >
        {cap}
      </span>
    </div>
  );
}

function ordinalToGradient(ord: 1 | 2 | 3 | 4): string {
  const tokenByOrd: Record<1 | 2 | 3 | 4, string> = {
    1: "var(--accent-amber)",
    2: "var(--accent-cyan)",
    3: "var(--accent-rose)",
    4: "var(--status-positive)",
  };
  const token = tokenByOrd[ord];
  return `linear-gradient(180deg, ${token} 40%, color-mix(in oklch, ${token}, transparent 60%))`;
}

function PullQuote({ raw, em }: { raw: string; em: string }) {
  // Replace {{tuesday}} with a coloured `<em>` while keeping the rest as text.
  // T15 — `data-dropcap="on"` flips the home-chapters.css ::first-letter
  // rule that draws the 4-line amber drop cap (≥768px only; mobile reverts).
  const parts = raw.split("{{tuesday}}");
  return (
    <p
      className="ch02-pull"
      data-dropcap="on"
      style={{
        marginTop: "56px",
        fontSize: "clamp(1.4rem, 1rem + 1.4vw, 2.4rem)",
        fontWeight: 500,
        letterSpacing: "-0.02em",
        color: "var(--fg-primary)",
        textAlign: "left",
        fontStyle: "oblique -6deg",
      }}
    >
      {parts[0]}
      <em style={{ color: "var(--accent-amber)", fontStyle: "normal" }}>{em}</em>
      {parts[1] ?? ""}
    </p>
  );
}
