"use client";

/**
 * Driver C — sprint/gowork-facelift Chapter 06 Live Jobs (full implementation).
 *
 * Eyebrow + live pill (with `useLiveNow` timestamp) + h2 + autoscroll
 * wage marquee + 3 hero JobCards.
 *
 * Replaces Driver D's earlier integration stub: the i18n keys, props,
 * and section id stay byte-compatible with `Chapter06LiveJobsProps`
 * so existing wiring + tests keep working.
 *
 * The marquee animation is driven by GSAP's tween helper on a single
 * track element; reduced-motion freezes it. The JobCard rendering
 * lives in `_internal/JobCard.tsx`.
 */

import { useEffect, useRef, useState, type ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useLiveNow } from "@/hooks/useLiveNow";
import { useGsapEntrance } from "@/lib/home/gsap";
import { JobCard } from "./_internal/JobCard";
import {
  WAGE_MARQUEE_ENTRIES,
  formatLiveAgo,
} from "./Chapter06LiveJobs.helpers";

export interface Chapter06LiveJobsProps {
  /** Override the section id — kept for back-compat with Driver D's stub. */
  id?: string;
}

/** The h2 — split across spans so we can apply the gradient to the
 *  middle "fair-chance" word and italics to the tail. */
function Ch06Heading({ id }: { id: string }): ReactElement {
  const { t } = useTranslation();
  return (
    <h2 id={`${id}-title`} className="ch06-h2">
      {t("home.ch6.h2Pre")} <em>{t("home.ch6.h2Fair")}</em>{" "}
      {t("home.ch6.h2Mid")} <em>{t("home.ch6.h2SixMiles")}</em>
    </h2>
  );
}

/** Autoscroll wage marquee. The track is animated via the GSAP
 *  entrance helper — we wire an infinite tween once on mount. */
function WageMarquee(): ReactElement {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const trackRef = useGsapEntrance<HTMLDivElement>(({ el, gsap }) => {
    // Animate from 0 to -50% (the duplicate half completes the loop)
    // over 32 seconds, repeating forever.
    const tween = gsap.to(el, {
      xPercent: -50,
      duration: 32,
      ease: "none",
      repeat: -1,
    });
    return () => tween.kill();
  }, []);
  return (
    <div className="ch06-marquee" aria-label={t("home.ch6.marqueeAria")}>
      <div
        ref={trackRef}
        className="ch06-marquee__track"
        data-motion={reduced ? "off" : "on"}
      >
        {WAGE_MARQUEE_ENTRIES.map((entry, i) => (
          <span
            key={i}
            data-testid={`ch06-wage-${i}`}
            className="ch06-marquee__entry"
          >
            <span className="wage">{entry.wage}</span>
            <span>·</span>
            <span>{entry.role}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/** Live pill — "Live · refreshed N min ago". */
function LivePill(): ReactElement {
  const { t } = useTranslation();
  const { now } = useLiveNow();
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setTick((x) => x + 1), 60_000);
    return () => window.clearInterval(id);
  }, []);
  const ago = formatLiveAgo(now);
  const prefix = t("home.ch6.livePillPrefix");
  const suffix = t("home.ch6.livePillSuffix");
  return (
    <span className="ch06-live-pill" data-testid="ch06-live-pill">
      <span className="ch06-live-dot" aria-hidden="true" />
      {prefix} {ago}
      {suffix ? ` ${suffix}` : ""}
    </span>
  );
}

export function Chapter06LiveJobs({
  id = "chapter-06",
}: Chapter06LiveJobsProps = {}): ReactElement {
  const { t } = useTranslation();
  const sectionRef = useRef<HTMLElement | null>(null);

  // GSAP entrance — h2 + cards reveal on scroll. Gracefully no-op
  // under reduced motion (handled by the helper).
  useGsapEntrance<HTMLElement>(({ el, gsap }) => {
    const ctx = gsap.context(() => {
      gsap.from(el.querySelectorAll(".ch06-h2"), {
        y: 60,
        opacity: 0,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 75%" },
      });
      gsap.from(el.querySelectorAll(".ch06-card"), {
        y: 60,
        opacity: 0,
        duration: 0.8,
        stagger: 0.12,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 65%" },
      });
    }, el);
    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      id={id}
      data-chapter-id="ch6"
      className="chapter ch06"
      aria-labelledby={`${id}-title`}
      data-bg="dark"
    >
      <p className="ch06-eb">
        <span className="num">06</span>
        <span className="lab">{t("home.ch6.eyebrow")}</span>
        <span className="rule" aria-hidden="true" />
        <LivePill />
      </p>
      <Ch06Heading id={id} />
      <WageMarquee />
      <div className="ch06-grid">
        <JobCard id="alcon" />
        <JobCard id="bnsf" />
        <JobCard id="dunn" />
      </div>
    </section>
  );
}

export default Chapter06LiveJobs;
