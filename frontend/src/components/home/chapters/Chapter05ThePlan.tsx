"use client";

/**
 * Driver C — sprint/gowork-facelift Chapter 05 The Plan.
 *
 * 4-card fan-out for the weekly plan: Monday → Thursday. The cards
 * start stacked center, then on scroll progress they fan out — each
 * card rotates ±deg and slides ±x. Reduced-motion: rendered in their
 * final fanned position with no scrub.
 *
 * The fan-out math (per-card t, angle, offsetX/offsetY, opacity, zIndex)
 * lives in {@link useCh05FanOut} so the chapter component stays small.
 */

import { useRef, useState, type ReactElement } from "react";
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
}

const CARD_KEYS: ReadonlyArray<{
  testId: string;
  tone: "amber" | "cyan" | "green" | "rose";
  num: string;
  tag: string;
  title: string;
  body: string;
  foot: string;
}> = [
  {
    testId: "ch05-card-1",
    tone: "amber",
    num: "home.ch5.card1Num",
    tag: "home.ch5.card1Tag",
    title: "home.ch5.card1Title",
    body: "home.ch5.card1Body",
    foot: "home.ch5.card1Foot",
  },
  {
    testId: "ch05-card-2",
    tone: "cyan",
    num: "home.ch5.card2Num",
    tag: "home.ch5.card2Tag",
    title: "home.ch5.card2Title",
    body: "home.ch5.card2Body",
    foot: "home.ch5.card2Foot",
  },
  {
    testId: "ch05-card-3",
    tone: "green",
    num: "home.ch5.card3Num",
    tag: "home.ch5.card3Tag",
    title: "home.ch5.card3Title",
    body: "home.ch5.card3Body",
    foot: "home.ch5.card3Foot",
  },
  {
    testId: "ch05-card-4",
    tone: "rose",
    num: "home.ch5.card4Num",
    tag: "home.ch5.card4Tag",
    title: "home.ch5.card4Title",
    body: "home.ch5.card4Body",
    foot: "home.ch5.card4Foot",
  },
];

/** One plan card, reading copy via the translator and applying the
 *  current fan-out transform. */
function PlanCard({
  spec,
  spec: { testId, tone },
  xform,
  resolved,
}: {
  spec: PlanCardSpec;
  xform: CardTransform;
  resolved: { num: string; tag: string; title: string; body: string; foot: string };
}): ReactElement {
  void spec; // tone consumed via attr
  return (
    <article
      data-testid={testId}
      data-tone={tone}
      className="ch05-card"
      style={{
        transform: `translate(${xform.x}px, ${xform.y}px) rotate(${xform.angle}deg) scale(${xform.scale})`,
        opacity: xform.opacity,
        zIndex: xform.zIndex,
      }}
    >
      <span className="pc-num">{resolved.num}</span>
      <span className="pc-tag">{resolved.tag}</span>
      <h3>{resolved.title}</h3>
      <p>{resolved.body}</p>
      <span className="pc-foot">{resolved.foot}</span>
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

  useCh05FanOut({ sectionRef, onProgress: setProgress, reduced });

  const xforms = CARD_KEYS.map((_, i) => computeFanXform(i, progress));

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
        <div className="ch05-fan">
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
              }}
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
