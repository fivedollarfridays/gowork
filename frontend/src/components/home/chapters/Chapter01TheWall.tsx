"use client";

/**
 * Chapter 01 — The Wall (Driver B, sprint/gowork-facelift).
 *
 * Editorial hero. Three editorial lines, kinetic morph word, seven-barrier
 * subhead, two CTAs, infinite marquee, scroll cue. Tokens-only. All copy via
 * `useTranslation()` so EN/ES toggle live.
 *
 * # Reduced-motion contract
 *
 * Under `prefers-reduced-motion: reduce`:
 *   - The morph word stays on its first state ("wall" / "muro").
 *   - The entrance stagger is disabled (sections render in their final state).
 *   - The hero parallax is disabled.
 *   - The marquee CSS animation is short-circuited via `data-motion="off"`.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useScrollVelocity } from "@/hooks/useScrollVelocity";
import { useGsapEntrance, useGsapScrollTrigger } from "@/lib/home/gsap";
import { ChapterMarquee } from "./_internal/ChapterMarquee";
import { ChapterScrollCue } from "./_internal/ChapterScrollCue";
import { Chapter01Hero } from "./_internal/Chapter01Hero";
import { Chapter01Background } from "./_internal/Chapter01Background";
import { Chapter01Subhead } from "./_internal/Chapter01Subhead";
import { Chapter01Cta } from "./_internal/Chapter01Cta";
import { Chapter01Eyebrow } from "./_internal/Chapter01Eyebrow";

const MORPH_INTERVAL_MS = 1800;
const MORPH_FALLBACK = [
  "wall",
  "license",
  "court date",
  "pickup",
  "47-min bus",
  "background",
  "wage cliff",
];

function readMorphWords(t: (k: string) => string): readonly string[] {
  // Translation files store the morph cycle as a JSON array; the i18n helper
  // returns a string, so we read it once via the raw lookup helper. If the
  // key resolves to a non-array, fall back to the English copy thesis.
  const raw = t("home.ch1.morphWords");
  return raw && raw !== "home.ch1.morphWords" && raw.startsWith("[")
    ? safeParseList(raw)
    : MORPH_FALLBACK;
}

function safeParseList(raw: string): readonly string[] {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed) && parsed.every((v) => typeof v === "string")) {
      return parsed as string[];
    }
  } catch {
    /* fall through */
  }
  return MORPH_FALLBACK;
}

export interface Chapter01TheWallProps {
  /** Optional id override for the section anchor (defaults to "chapter-01"). */
  id?: string;
}

export function Chapter01TheWall({ id = "chapter-01" }: Chapter01TheWallProps) {
  const { t, locale } = useTranslation();
  const reduced = usePrefersReducedMotion();

  const morphWords = readMorphWords(t);
  const [morphIdx, setMorphIdx] = useState(0);

  // T13 — bg grain intensifies on hover OR fast scroll.
  // useScrollVelocity yields px/ms; 0.6 px/ms ≈ 600 px/s (the AC threshold).
  const { isFast } = useScrollVelocity(0.6);
  const [hovered, setHovered] = useState(false);
  const velocityActive = !reduced && (hovered || isFast);

  useEffect(() => {
    if (reduced) return;
    const handle = window.setInterval(() => {
      setMorphIdx((i) => (i + 1) % morphWords.length);
    }, MORPH_INTERVAL_MS);
    return () => window.clearInterval(handle);
  }, [reduced, morphWords.length]);

  // Entrance stagger
  const entranceRef = useGsapEntrance<HTMLElement>(({ el, gsap }) => {
    gsap.from(el.querySelectorAll(".ch01-eb"), {
      y: 24,
      opacity: 0,
      duration: 0.8,
      ease: "power3.out",
      delay: 0.1,
    });
    gsap.from(el.querySelectorAll(".ch01-h1 .line-1"), {
      y: 80,
      opacity: 0,
      scale: 0.92,
      duration: 1.2,
      ease: "power3.out",
      delay: 0.25,
    });
    gsap.from(el.querySelectorAll(".ch01-h1 .line-2"), {
      y: 30,
      opacity: 0,
      duration: 0.9,
      ease: "power3.out",
      delay: 0.65,
    });
    gsap.from(el.querySelectorAll(".ch01-h1 .line-3"), {
      y: 30,
      opacity: 0,
      duration: 0.9,
      ease: "power3.out",
      delay: 0.85,
    });
    gsap.from(el.querySelectorAll(".ch01-sub"), {
      y: 24,
      opacity: 0,
      duration: 0.8,
      ease: "power3.out",
      delay: 1.05,
    });
    gsap.from(el.querySelectorAll(".ch01-cta-row"), {
      y: 24,
      opacity: 0,
      duration: 0.8,
      ease: "power3.out",
      delay: 1.25,
    });
  }, [locale]);

  // Hero parallax: push the h1 up + fade as we scroll into ch02.
  const parallaxRef = useGsapScrollTrigger<HTMLElement>(
    ({ el, gsap, reduced: r }) => {
      if (r) return;
      const h1 = el.querySelector(".ch01-h1");
      if (!h1) return;
      gsap.to(h1, {
        y: -120,
        opacity: 0.3,
        scrollTrigger: {
          trigger: el,
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
      });
    },
  );

  const setRefs = (node: HTMLElement | null) => {
    entranceRef.current = node;
    parallaxRef.current = node;
  };

  return (
    <section
      ref={setRefs}
      id={id}
      data-bg="dark"
      data-screen-label="01 The wall"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch01-h1"
      className="chapter ch01"
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => setHovered(false)}
      onPointerMove={() => {
        if (!hovered) setHovered(true);
      }}
      style={{
        position: "relative",
        minHeight: "100vh",
        padding: "130px 80px 0",
        overflow: "hidden",
        display: "grid",
        gridTemplateRows: "auto 1fr auto auto",
        gap: "32px",
      }}
    >
      <Chapter01Background velocityActive={velocityActive} />

      <Chapter01Eyebrow label={t("home.ch1.eyebrow")} />

      <Chapter01Hero
        morphWord={morphWords[morphIdx] ?? morphWords[0] ?? "wall"}
        morphWords={morphWords}
        ariaLabel={t("home.ch1.ariaLabel")}
        line2Wall={t("home.ch1.line2Wall")}
        line2Job={t("home.ch1.line2Job")}
        line3Down={t("home.ch1.line3Down")}
      />

      <Chapter01Subhead
        raw={t("home.ch1.subhead")}
        seven={t("home.ch1.subheadSeven")}
        system={t("home.ch1.subheadSystem")}
      />

      <Chapter01Cta
        primaryLabel={t("home.ch1.ctaPrimary")}
        ghostLabel={t("home.ch1.ctaGhost")}
      />

      <ChapterMarquee
        items={[
          t("home.ch1.marquee.license"),
          t("home.ch1.marquee.court"),
          t("home.ch1.marquee.pickup"),
          t("home.ch1.marquee.bus"),
          t("home.ch1.marquee.background"),
          t("home.ch1.marquee.cliff"),
          t("home.ch1.marquee.nobody"),
        ]}
        reduced={reduced}
      />

      <ChapterScrollCue label={t("home.ch1.scrollCue")} />
    </section>
  );
}


