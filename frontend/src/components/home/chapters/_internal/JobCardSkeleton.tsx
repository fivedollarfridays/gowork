"use client";

/**
 * Driver C — polish-2 T27 — Ch06 JobCard skeleton loading state.
 *
 * 4-row mono shimmer skeleton. The shimmer animation lives in
 * `home-chapters.css` under the polish-2 namespace block. Reduced-motion
 * disables the gradient slide via the same stylesheet.
 *
 * Used as the rendered body of `<JobCard loading />` so the parent
 * card frame (logo slot, border, padding) stays consistent across the
 * loading and loaded states.
 */

import type { ReactElement } from "react";

export interface JobCardSkeletonProps {
  /** Accessible label announced to screen readers. */
  label: string;
}

export function JobCardSkeleton({ label }: JobCardSkeletonProps): ReactElement {
  return (
    <div
      className="ch06-skeleton"
      role="status"
      aria-busy="true"
      aria-label={label}
    >
      <span className="ch06-skeleton__row" aria-hidden="true" />
      <span className="ch06-skeleton__row" aria-hidden="true" />
      <span className="ch06-skeleton__row" aria-hidden="true" />
      <span className="ch06-skeleton__row" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

export default JobCardSkeleton;
