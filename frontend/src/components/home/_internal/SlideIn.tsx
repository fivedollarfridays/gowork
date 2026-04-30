"use client";

/**
 * SlideIn — wrapper component for `useScrollTiedSlide`.
 *
 * Pass `from="left|right|up|down"` and any element gets the premium-
 * Webflow scroll-tied entrance — slides in as it scrolls through the
 * viewport, reverses on scroll-up. Lithosquare / Linear signature.
 *
 * For paragraph blocks where each child should slide in alternately,
 * wrap each child in its own SlideIn with alternating from values.
 */

import type { ReactNode } from "react";
import { useScrollTiedSlide, type SlideDirection } from "@/hooks/useScrollTiedSlide";

export interface SlideInProps {
  children: ReactNode;
  from?: SlideDirection;
  distance?: number;
  start?: string;
  end?: string;
  as?: "div" | "span" | "p" | "li" | "section";
  className?: string;
  style?: React.CSSProperties;
}

export function SlideIn({
  children,
  from = "left",
  distance = 100,
  start,
  end,
  as: As = "div",
  className,
  style,
}: SlideInProps): JSX.Element {
  const ref = useScrollTiedSlide<HTMLElement>({
    from,
    distance,
    start,
    end,
  });

  const props = {
    ref: ref as React.MutableRefObject<HTMLElement | null>,
    className,
    style: { willChange: "transform, opacity", ...style },
  };

  if (As === "span") {
    return <span {...(props as unknown as React.HTMLAttributes<HTMLSpanElement>)}>{children}</span>;
  }
  if (As === "p") {
    return <p {...(props as unknown as React.HTMLAttributes<HTMLParagraphElement>)}>{children}</p>;
  }
  if (As === "li") {
    return <li {...(props as unknown as React.HTMLAttributes<HTMLLIElement>)}>{children}</li>;
  }
  if (As === "section") {
    return <section {...(props as unknown as React.HTMLAttributes<HTMLElement>)}>{children}</section>;
  }
  return <div {...(props as unknown as React.HTMLAttributes<HTMLDivElement>)}>{children}</div>;
}
