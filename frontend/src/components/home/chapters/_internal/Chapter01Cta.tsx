"use client";

/**
 * Chapter 01 CTA row — primary "Get your plan → /assess" + ghost
 * "See how it works ↓ #chapter-04".
 *
 * Both CTAs converted to Next.js `<Link>` for client-side navigation
 * (no full page reload on /assess). Ghost CTA also gets a smooth-
 * scroll click handler so the anchor jump animates instead of
 * hard-snapping to the chapter-04 section.
 */

import Link from "next/link";
import { useMagneticHover } from "@/hooks/useMagneticHover";
import { useIdleState } from "@/hooks/useIdleState";
import type { MouseEvent } from "react";

interface Chapter01CtaProps {
  primaryLabel: string;
  ghostLabel: string;
}

function smoothScrollToHash(hash: string): void {
  if (typeof document === "undefined") return;
  const id = hash.startsWith("#") ? hash.slice(1) : hash;
  const target = document.getElementById(id);
  if (!target) return;
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function Chapter01Cta({ primaryLabel, ghostLabel }: Chapter01CtaProps) {
  const primaryRef = useMagneticHover<HTMLAnchorElement>();
  const idle = useIdleState(4_000);
  const onGhostClick = (e: MouseEvent<HTMLAnchorElement>) => {
    // Let modifier-clicks (cmd/ctrl/shift) fall through to default
    // browser behaviour (open in new tab, etc.).
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    smoothScrollToHash("#chapter-04");
    // Update URL hash so the back button + share-link still work.
    if (typeof history !== "undefined") {
      history.replaceState(null, "", "#chapter-04");
    }
  };
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
      <Link
        ref={primaryRef}
        className="cta cta-primary"
        href="/assess"
        data-idle-orbit={idle ? "true" : "false"}
        style={primaryStyle()}
      >
        <span>{primaryLabel}</span>
        <span className="cta-arr">→</span>
      </Link>
      <a
        className="cta cta-ghost"
        href="#chapter-04"
        onClick={onGhostClick}
        style={ghostStyle()}
      >
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
    position: "relative",
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
