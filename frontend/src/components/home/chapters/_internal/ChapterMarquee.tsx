"use client";

/**
 * Generic marquee strip used by Chapter 01.
 *
 * Items are rendered twice (back-to-back) so a `transform: translateX(-50%)`
 * CSS animation can loop seamlessly. When `reduced` is true the animation
 * is disabled via `data-motion="off"`.
 */

interface ChapterMarqueeProps {
  items: readonly string[];
  reduced: boolean;
}

export function ChapterMarquee({ items, reduced }: ChapterMarqueeProps) {
  return (
    <div
      className="ch01-marquee"
      aria-hidden="true"
      data-motion={reduced ? "off" : "on"}
      style={{
        position: "relative",
        zIndex: 2,
        width: "100%",
        marginTop: "32px",
        padding: "24px 0",
        borderTop:
          "1px solid color-mix(in oklch, var(--fg-primary), transparent 92%)",
        borderBottom:
          "1px solid color-mix(in oklch, var(--fg-primary), transparent 92%)",
        overflow: "hidden",
        maskImage:
          "linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent)",
        WebkitMaskImage:
          "linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent)",
      }}
    >
      <div
        className="mq-track"
        style={{
          display: "inline-flex",
          gap: "28px",
          whiteSpace: "nowrap",
          fontFamily: "var(--font-mono-data)",
          fontSize: "14px",
          letterSpacing: "0.04em",
          color: "var(--fg-muted)",
          textTransform: "uppercase",
          animation: reduced ? "none" : "mq-scroll 38s linear infinite",
        }}
      >
        {[...items, ...items].map((item, i) => (
          <span key={`${item}-${i}`} style={{ display: "inline-flex", gap: "28px" }}>
            <span>{item}</span>
            <span className="mq-dot" style={{ color: "var(--accent-amber)" }}>
              ·
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
