"use client";

/**
 * Driver C — sprint/gowork-facelift Chapter 05 The Plan.
 *
 * 4-card fan-out for the weekly plan: Monday → Thursday. The cards
 * start stacked center, then on scroll progress they fan out — each
 * card rotates ±deg and slides ±x. Reduced-motion: rendered in their
 * final fanned position with no scrub.
 *
 * polish-2 Driver C:
 *   - T24 — hover preview-flip (Y-axis 180deg, 3 bullets per back face).
 *   - T25 — mobile horizontal scroll-snap (data-mobile-snap on .ch05-fan
 *     opts the section into the @media (max-width: 767px) rule in
 *     home-chapters.css).
 */

import { useRef, useState, useCallback, type ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useCh05FanOut, type CardTransform } from "./Chapter05ThePlan.fanout";

interface PlanCardSpec {
  testId: string;
  tone: "amber" | "cyan" | "green" | "rose";
  num: string;
  tag: string;
  title: string;
  body: string;
  foot: string;
  back1: string;
  back2: string;
  back3: string;
}

const CARD_KEYS: ReadonlyArray<PlanCardSpec> = [
  {
    testId: "ch05-card-1",
    tone: "amber",
    num: "home.ch5.card1Num",
    tag: "home.ch5.card1Tag",
    title: "home.ch5.card1Title",
    body: "home.ch5.card1Body",
    foot: "home.ch5.card1Foot",
    back1: "home.ch5.card1.back1",
    back2: "home.ch5.card1.back2",
    back3: "home.ch5.card1.back3",
  },
  {
    testId: "ch05-card-2",
    tone: "cyan",
    num: "home.ch5.card2Num",
    tag: "home.ch5.card2Tag",
    title: "home.ch5.card2Title",
    body: "home.ch5.card2Body",
    foot: "home.ch5.card2Foot",
    back1: "home.ch5.card2.back1",
    back2: "home.ch5.card2.back2",
    back3: "home.ch5.card2.back3",
  },
  {
    testId: "ch05-card-3",
    tone: "green",
    num: "home.ch5.card3Num",
    tag: "home.ch5.card3Tag",
    title: "home.ch5.card3Title",
    body: "home.ch5.card3Body",
    foot: "home.ch5.card3Foot",
    back1: "home.ch5.card3.back1",
    back2: "home.ch5.card3.back2",
    back3: "home.ch5.card3.back3",
  },
  {
    testId: "ch05-card-4",
    tone: "rose",
    num: "home.ch5.card4Num",
    tag: "home.ch5.card4Tag",
    title: "home.ch5.card4Title",
    body: "home.ch5.card4Body",
    foot: "home.ch5.card4Foot",
    back1: "home.ch5.card4.back1",
    back2: "home.ch5.card4.back2",
    back3: "home.ch5.card4.back3",
  },
];

interface ResolvedCardCopy {
  num: string;
  tag: string;
  title: string;
  body: string;
  foot: string;
  back1: string;
  back2: string;
  back3: string;
}

/** One plan card with hover-flip preview (T24). */
function PlanCard({
  spec,
  xform,
  resolved,
  flipped,
  onEnter,
  onLeave,
}: {
  spec: PlanCardSpec;
  xform: CardTransform;
  resolved: ResolvedCardCopy;
  flipped: boolean;
  onEnter: () => void;
  onLeave: () => void;
}): ReactElement {
  const { testId, tone } = spec;
  return (
    <article
      data-testid={testId}
      data-tone={tone}
      data-flipped={flipped ? "true" : "false"}
      className="ch05-card"
      onPointerEnter={onEnter}
      onPointerLeave={onLeave}
      onFocus={onEnter}
      onBlur={onLeave}
      style={{
        transform: `translate(${xform.x}px, ${xform.y}px) rotate(${xform.angle}deg) scale(${xform.scale})`,
        opacity: xform.opacity,
        zIndex: xform.zIndex,
      }}
    >
      <div className="ch05-card__faces">
        <div className="ch05-card__face" data-face="front">
          <span className="pc-num">{resolved.num}</span>
          <span className="pc-tag">{resolved.tag}</span>
          <h3>{resolved.title}</h3>
          <p>{resolved.body}</p>
          <span className="pc-foot">{resolved.foot}</span>
        </div>
        <ul
          className="ch05-card__face ch05-card__back"
          data-face="back"
          aria-hidden={flipped ? "false" : "true"}
        >
          <li>{resolved.back1}</li>
          <li>{resolved.back2}</li>
          <li>{resolved.back3}</li>
        </ul>
      </div>
    </article>
  );
}

/** Decorated h2 — splits the eyebrow + plan/em + tail into spans. */
function Ch05Heading(): ReactElement {
  const { t } = useTranslation();
  return (
    <h2 id="chapter-05-title" className="ch05-h2">
      {t("home.ch5.h2Pre")} <em>{t("home.ch5.h2Plan")}</em>{" "}
      {t("home.ch5.h2Mid")} <span className="italic">{t("home.ch5.h2Tail")}</span>
    </h2>
  );
}

export function Chapter05ThePlan(): ReactElement {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const sectionRef = useRef<HTMLElement | null>(null);
  const [progress, setProgress] = useState<number>(reduced ? 1 : 0);
  const [flippedIdx, setFlippedIdx] = useState<number | null>(null);

  useCh05FanOut({ sectionRef, onProgress: setProgress, reduced });

  const xforms = CARD_KEYS.map((_, i) => computeFanXform(i, progress));

  const onEnter = useCallback((idx: number) => () => setFlippedIdx(idx), []);
  const onLeave = useCallback(() => setFlippedIdx(null), []);

  return (
    <section
      ref={sectionRef}
      id="chapter-05"
      className="chapter ch05"
      aria-labelledby="chapter-05-title"
      data-bg="dark"
    >
      <div className="ch05-pin">
        <div className="ch05-left">
          <p className="ch05-eb">
            <span className="num">05</span>
            <span className="lab">{t("home.ch5.eyebrow")}</span>
            <span className="rule" aria-hidden="true" />
          </p>
          <Ch05Heading />
          <p className="ch05-intro">{t("home.ch5.intro")}</p>
        </div>
        <div className="ch05-fan" data-mobile-snap="true">
          {CARD_KEYS.map((spec, i) => (
            <PlanCard
              key={spec.testId}
              spec={spec}
              xform={xforms[i]}
              resolved={{
                num: t(spec.num),
                tag: t(spec.tag),
                title: t(spec.title),
                body: t(spec.body),
                foot: t(spec.foot),
                back1: t(spec.back1),
                back2: t(spec.back2),
                back3: t(spec.back3),
              }}
              flipped={flippedIdx === i}
              onEnter={onEnter(i)}
              onLeave={onLeave}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

/** Per-card fan-out math — compute transform from index + 0..1 progress. */
function computeFanXform(i: number, progress: number): CardTransform {
  const t = Math.max(0, Math.min(1, progress * 1.4 - i * 0.05));
  const angle = (i - 1.5) * 8 * t;
  const x = (i - 1.5) * 220 * t;
  const y = Math.abs(i - 1.5) * 30 * t;
  const baseOpacity = 0.5 + 0.5 * t;
  // Card 0 (index 0) gets a small extra opacity boost so it remains visible
  // when stacked at the start.
  const opacity = i === 0 ? Math.min(1, baseOpacity + 0.5 * (1 - t)) : baseOpacity;
  const scale = 1 - i * 0.02 * (1 - t);
  const zIndex = 10 + Math.round(t * i);
  return { x, y, angle, opacity, zIndex, scale };
}

export default Chapter05ThePlan;
