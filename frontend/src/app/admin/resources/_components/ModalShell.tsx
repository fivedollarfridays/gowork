"use client";

/**
 * Lightweight modal shell used by the add/edit resource dialogs.
 *
 * Plain inline portal-less modal — the project does not bundle a
 * shadcn `Dialog` primitive yet, so we mirror the existing
 * `SendAdvisorNoteDialog` pattern (fixed inset, backdrop, role=dialog).
 */

import type React from "react";

export function ModalShell({
  ariaLabel,
  children,
}: {
  ariaLabel: string;
  children: React.ReactNode;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 overflow-y-auto"
    >
      <div className="w-full max-w-2xl rounded-lg border bg-card p-6 shadow-lg my-8">
        {children}
      </div>
    </div>
  );
}
