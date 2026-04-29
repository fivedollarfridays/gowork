"use client";

/**
 * ChapterRailTooltip — polish-2 T3.
 *
 * Slides a 200×96 glass card to the right of a hovered/focused chapter
 * rail tick, showing the chapter screenshot + eyebrow. Animates in via
 * translateX(-8px) → 0 + opacity 0 → 1 over 200ms `--ease-linear-sig`.
 *
 * Stateless — receives `chapterId`, `eyebrow`, `thumbnailSrc`. The parent
 * (ChapterRail) wires hover/focus state via mouseenter/mouseleave/focus
 * handlers and chooses when to render this.
 */

export interface ChapterRailTooltipProps {
  /** Chapter id (1..8) — drives the data-* attribute for tests. */
  chapterId: number;
  /** Eyebrow text rendered above the thumbnail (chapter rail label). */
  eyebrow: string;
  /** Path to the chapter thumbnail under /home/chapter-thumbs/. */
  thumbnailSrc: string;
  /** Localized alt text for the chapter screenshot. */
  alt: string;
}

export function ChapterRailTooltip({
  chapterId,
  eyebrow,
  thumbnailSrc,
  alt,
}: ChapterRailTooltipProps): JSX.Element {
  return (
    <div
      role="tooltip"
      data-chapter-rail-tooltip
      data-tooltip-chapter-id={chapterId}
      className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 w-[200px] h-24 rounded-lg overflow-hidden"
      style={{
        background: "color-mix(in oklch, var(--bg-elevated), transparent 25%)",
        backdropFilter: "blur(12px)",
        border:
          "1px solid color-mix(in oklch, var(--fg-primary), transparent 85%)",
        boxShadow:
          "0 8px 24px color-mix(in oklch, var(--bg-base), transparent 50%)",
        animation:
          "chapter-rail-tooltip-in 200ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1)) forwards",
        zIndex: 100,
      }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- tooltip preview is a 200x96 lazy decorative image; next/image overhead unwarranted */}
      <img
        src={thumbnailSrc}
        alt={alt}
        loading="lazy"
        decoding="async"
        className="absolute inset-0 w-full h-full object-cover"
        style={{ filter: "saturate(1.05) brightness(0.85)" }}
      />
      <div
        className="absolute inset-0 flex items-end px-2 pb-1 text-[10px] font-mono uppercase tracking-widest"
        style={{
          color: "var(--fg-primary)",
          background:
            "linear-gradient(to top, color-mix(in oklch, var(--bg-base), transparent 10%), transparent 65%)",
          letterSpacing: "0.12em",
        }}
      >
        <span>{eyebrow}</span>
      </div>
    </div>
  );
}
