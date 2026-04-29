"use client";

/**
 * Chapter 01 CTA row — primary "Get your plan → /assess" + ghost
 * "See how it works ↓ #chapter-04". Pulled out of Chapter01TheWall.tsx so
 * the parent stays under arch limits.
 */

interface Chapter01CtaProps {
  primaryLabel: string;
  ghostLabel: string;
}

export function Chapter01Cta({ primaryLabel, ghostLabel }: Chapter01CtaProps) {
  return (
    <div
      className="ch01-cta-row"
      style={{
        position: "relative",
        zIndex: 2,
        display: "flex",
        gap: "14px",
        justifyContent: "center",
        flexWrap: "wrap",
      }}
    >
      <a className="cta cta-primary" href="/assess" style={primaryStyle()}>
        <span>{primaryLabel}</span>
        <span className="cta-arr">→</span>
      </a>
      <a className="cta cta-ghost" href="#chapter-04" style={ghostStyle()}>
        <span>{ghostLabel}</span>
        <span className="cta-arr">↓</span>
      </a>
    </div>
  );
}

function primaryStyle(): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: "12px",
    padding: "16px 26px",
    borderRadius: "999px",
    background: "var(--accent-cyan)",
    color: "#0A0E1A",
    fontWeight: 600,
    fontSize: "15px",
    letterSpacing: "-0.01em",
    boxShadow:
      "0 8px 24px color-mix(in oklch, var(--accent-cyan), transparent 60%)",
    transition: "all 280ms var(--ease-linear-sig)",
  };
}

function ghostStyle(): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: "12px",
    padding: "16px 26px",
    borderRadius: "999px",
    background: "color-mix(in oklch, var(--fg-primary), transparent 92%)",
    color: "var(--fg-primary)",
    border: "1px solid color-mix(in oklch, var(--fg-primary), transparent 78%)",
    fontWeight: 600,
    fontSize: "15px",
    letterSpacing: "-0.01em",
    transition: "all 280ms var(--ease-linear-sig)",
  };
}
