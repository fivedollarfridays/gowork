"use client";

/**
 * Driver Ch04-enrich — full editorial card stack (right column).
 *
 * Per v1 reference, each "step" carries:
 *   - eyebrow row (sequence # + stage + time chip)
 *   - h1 with em-amber (and strike-rose support)
 *   - dropcap paragraph + body paragraphs
 *   - pull-quote with amber border-left
 *   - in-card timeline (2-col: time + event w/ colored dot)
 *   - tag row (multi-color chips)
 *   - stat-row footer (4 stats)
 *   - step nav (prev / next)
 *
 * Only the active step shows; inactive cards translate-y away.
 */

import type { ReactElement } from "react";
import { useTranslation } from "@/hooks/useTranslation";

interface CardDef {
  num: string;
  i18nTime: string;
  i18nBody: string;
  i18nTimeline: ReadonlyArray<{
    time: string;
    meta: string;
    i18nEvent: string;
    tone: "cyan" | "amber" | "rose";
  }>;
  i18nTags: ReadonlyArray<{ key: string; tone: "amber" | "cyan" | "rose" }>;
}

const CARDS: ReadonlyArray<CardDef> = [
  {
    num: "01",
    i18nTime: "home.ch4.cards.card1Time",
    i18nBody: "home.ch4.cards.card1Body",
    i18nTimeline: [
      {
        time: "06:42a",
        meta: "22 min · bus",
        i18nEvent: "home.ch4.step.tlEvent1",
        tone: "cyan",
      },
      {
        time: "10:00a",
        meta: "45 min · DPS",
        i18nEvent: "home.ch4.step.tlEvent2",
        tone: "amber",
      },
    ],
    i18nTags: [
      { key: "home.ch4.step.tag1", tone: "cyan" },
      { key: "home.ch4.step.tag2", tone: "amber" },
    ],
  },
  {
    num: "02",
    i18nTime: "home.ch4.cards.card2Time",
    i18nBody: "home.ch4.cards.card2Body",
    i18nTimeline: [
      {
        time: "10:00a",
        meta: "45 min · DPS",
        i18nEvent: "home.ch4.step.tlEvent2",
        tone: "amber",
      },
      {
        time: "12:30p",
        meta: "30 min · navigator",
        i18nEvent: "home.ch4.step.tlEvent3",
        tone: "cyan",
      },
    ],
    i18nTags: [
      { key: "home.ch4.step.tag2", tone: "amber" },
    ],
  },
  {
    num: "03",
    i18nTime: "home.ch4.cards.card3Time",
    i18nBody: "home.ch4.cards.card3Body",
    i18nTimeline: [
      {
        time: "12:30p",
        meta: "30 min · navigator",
        i18nEvent: "home.ch4.step.tlEvent3",
        tone: "cyan",
      },
      {
        time: "02:00p",
        meta: "school",
        i18nEvent: "home.ch4.step.tlEvent4",
        tone: "amber",
      },
    ],
    i18nTags: [
      { key: "home.ch4.step.tag3", tone: "cyan" },
    ],
  },
  {
    num: "04",
    i18nTime: "home.ch4.cards.card4Time",
    i18nBody: "home.ch4.cards.card4Body",
    i18nTimeline: [
      {
        time: "02:00p",
        meta: "school",
        i18nEvent: "home.ch4.step.tlEvent4",
        tone: "amber",
      },
      {
        time: "03:27p",
        meta: "shift",
        i18nEvent: "home.ch4.step.tlEvent5",
        tone: "cyan",
      },
    ],
    i18nTags: [
      { key: "home.ch4.step.tag4", tone: "rose" },
    ],
  },
];

interface CardProps {
  card: CardDef;
  index: number;
  active: boolean;
  activeIndex: number;
}

function CardArticle({ card, index, active, activeIndex }: CardProps): ReactElement {
  const { t } = useTranslation();
  const offsetY = index < activeIndex ? -40 : 40;
  return (
    <article
      data-testid={`ch04-card-${index + 1}`}
      data-active={active ? "true" : "false"}
      className="ch04-card"
      style={{
        opacity: active ? 1 : 0,
        transform: `translateY(${active ? 0 : offsetY}px)`,
        pointerEvents: active ? "auto" : "none",
      }}
    >
      <div className="ch04-card__head">
        <span className="ch04-card__eyebrow">
          <span className="ch04-card__num">{card.num}</span>
          <span> · </span>
          <span>{t("home.ch4.eyebrow")}</span>
          <span> · </span>
          <span className="ch04-card__suffix">
            {t("home.ch4.step.eyebrowSuffix")}
          </span>
        </span>
        <span className="ch04-card__ts">
          <span className="ch04-card__ts-dot" aria-hidden="true" />
          {t("home.ch4.step.tsLabel")}
        </span>
      </div>

      <div className="ch04-card__time">{t(card.i18nTime)}</div>

      <p className="ch04-card__body ch04-card__body--dropcap">
        {t(card.i18nBody)}
      </p>

      <p className="ch04-card__pull">{t("home.ch4.step.pull")}</p>

      <div className="ch04-card__timeline" aria-label="Tuesday timeline">
        {card.i18nTimeline.map((row, i) => (
          <div className="ch04-card__tl-row" key={i}>
            <span className="ch04-card__tl-time">
              {row.time}
              <span className="ch04-card__tl-meta">{row.meta}</span>
            </span>
            <span
              className={`ch04-card__tl-event ch04-card__tl-event--${row.tone}`}
            >
              {t(row.i18nEvent)}
            </span>
          </div>
        ))}
      </div>

      <div className="ch04-card__tag-row">
        {card.i18nTags.map((tag) => (
          <span
            key={tag.key}
            className={`ch04-card__tag ch04-card__tag--${tag.tone}`}
          >
            {t(tag.key)}
          </span>
        ))}
      </div>
    </article>
  );
}

export function Ch04Cards({ activeStep }: { activeStep: number }): ReactElement {
  return (
    <div className="ch04-cards" aria-live="polite">
      {CARDS.map((card, i) => (
        <CardArticle
          key={i}
          card={card}
          index={i}
          active={i === activeStep}
          activeIndex={activeStep}
        />
      ))}
    </div>
  );
}

export default Ch04Cards;
