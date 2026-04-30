"use client";

/**
 * Chapter 01 subhead — the seven-barrier paragraph.
 *
 * polish-3 round-2 rebuild — was a single static <p> rendering as a
 * boring 56rem block of text. Now built as three editorial fragments
 * (head + bolded seven + middle + bolded system + tail) each wrapped
 * in WordReveal so the paragraph rises word-by-word as the user
 * crosses Ch01 into the visible band. The bolded fragments inherit
 * higher contrast color but flow inline with the rest so the eye can
 * still scan it as prose.
 *
 * Translation keys use {{seven}} and {{system}} placeholders for EN/ES.
 */

import { WordReveal } from "@/components/home/_internal/WordReveal";

export interface Chapter01SubheadProps {
  raw: string;
  seven: string;
  system: string;
}

const BASE_DELAY_HEAD = 200;
const BASE_DELAY_MIDDLE = 700;
const BASE_DELAY_TAIL = 1100;

export function Chapter01Subhead({ raw, seven, system }: Chapter01SubheadProps) {
  const [head, afterSeven] = raw.split("{{seven}}");
  const [middle, tail] = (afterSeven ?? "").split("{{system}}");

  const wrapStyle: React.CSSProperties = {
    position: "relative",
    zIndex: 2,
    maxWidth: "56rem",
    margin: "0 auto",
    fontSize: "clamp(1.05rem, 0.9rem + 0.5vw, 1.35rem)",
    lineHeight: 1.6,
    color: "var(--fg-secondary)",
    textAlign: "center",
    padding: "0 4vw",
    fontWeight: 400,
    letterSpacing: "-0.005em",
    textWrap: "balance",
  };
  const boldStyle: React.CSSProperties = {
    color: "var(--fg-primary)",
    fontWeight: 600,
  };

  return (
    <p className="ch01-sub" style={wrapStyle}>
      <WordReveal text={head ?? ""} baseDelayMs={BASE_DELAY_HEAD} staggerMs={28} />
      <WordReveal
        text={seven}
        baseDelayMs={BASE_DELAY_HEAD + 360}
        staggerMs={32}
        style={boldStyle}
      />
      <WordReveal text={middle ?? ""} baseDelayMs={BASE_DELAY_MIDDLE} staggerMs={26} />
      <WordReveal
        text={system}
        baseDelayMs={BASE_DELAY_TAIL}
        staggerMs={32}
        style={boldStyle}
      />
      {tail ? (
        <WordReveal
          text={tail}
          baseDelayMs={BASE_DELAY_TAIL + 320}
          staggerMs={26}
        />
      ) : null}
    </p>
  );
}
