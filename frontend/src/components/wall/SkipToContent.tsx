"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.63 / polish-2 T6 — Skip-to-content link.
 *
 * Mounts as the FIRST focusable element on the page so keyboard users
 * land on it with the first Tab press. Per the design plan (line 263)
 * the link is "visible on focus, NOT visually-hidden — proudly visible".
 *
 * polish-2 T6 polish:
 *  - Cyan pill (border-radius 9999px, var(--accent-cyan) background)
 *  - 10px / 16px padding
 *  - Slides from translateY(-200%) → translateY(0) on focus in 200ms
 *  - Honors data-theme="light" (navy text on cyan via var(--bg-base))
 *
 * Uses inline styles so the polish lives entirely inside the component
 * file (Driver A's lane). The legacy `.skip-to-content` global class is
 * preserved for downstream selectors and contracts.
 */
export interface SkipToContentProps {
  /** Anchor id of the main landmark. Default: "main". */
  targetId?: string;
}

const BASE_STYLE: CSSProperties = {
  position: "fixed",
  top: "1rem",
  left: "1rem",
  zIndex: 100,
  padding: "10px 16px",
  borderRadius: "9999px",
  background: "var(--accent-cyan)",
  fontWeight: 700,
  fontSize: "0.875rem",
  textDecoration: "none",
  letterSpacing: "0.01em",
  transition:
    "transform 200ms var(--ease-linear-sig, cubic-bezier(0.32, 0.72, 0, 1))",
  willChange: "transform",
  outline: "none",
  boxShadow: "0 4px 12px color-mix(in oklch, var(--accent-cyan), transparent 50%)",
};

export function SkipToContent({
  targetId = "main",
}: SkipToContentProps): JSX.Element {
  const { t } = useTranslation();
  const [focused, setFocused] = useState<boolean>(false);

  // Track data-theme from <html> for honoring light theme. The SiteHeader
  // toggle writes data-theme="light"|"dark" on the documentElement, so
  // observing the attribute lets the SkipToContent invert text color.
  const [theme, setTheme] = useState<string>("dark");
  useEffect(() => {
    if (typeof document === "undefined") return undefined;
    const read = () =>
      setTheme(document.documentElement.getAttribute("data-theme") ?? "dark");
    read();
    const mo = new MutationObserver(read);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => mo.disconnect();
  }, []);

  const dynamicStyle: CSSProperties = {
    ...BASE_STYLE,
    transform: focused ? "translateY(0)" : "translateY(-200%)",
    color: theme === "light" ? "var(--bg-base)" : "var(--bg-base)",
  };

  return (
    <a
      href={`#${targetId}`}
      className="skip-to-content"
      style={dynamicStyle}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      data-theme-aware-skip
    >
      {t("a11y.skipToContent")}
    </a>
  );
}
