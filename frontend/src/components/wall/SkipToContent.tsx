"use client";

import { useTranslation } from "@/hooks/useTranslation";

/**
 * T1.63 — Skip-to-content link.
 *
 * Mounts as the FIRST focusable element on the page so keyboard users
 * land on it with the first Tab press. Per the design plan (line 263)
 * the link is "visible on focus, NOT visually-hidden — proudly visible".
 *
 * The styling is declared as the global CSS class `.skip-to-content`
 * (Driver A's lane in `globals.css`). This component supplies only the
 * markup contract : the class name, an href to the configured anchor,
 * and the i18n-driven label.
 *
 * If Driver A's class is missing, the link still functions — it just
 * inherits browser defaults until the global stylesheet lands.
 */
export interface SkipToContentProps {
  /** Anchor id of the main landmark. Default: "main". */
  targetId?: string;
}

export function SkipToContent({
  targetId = "main",
}: SkipToContentProps): JSX.Element {
  const { t } = useTranslation();
  return (
    <a href={`#${targetId}`} className="skip-to-content">
      {t("a11y.skipToContent")}
    </a>
  );
}
