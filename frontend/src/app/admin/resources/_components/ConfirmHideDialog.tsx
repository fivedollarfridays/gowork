"use client";

/**
 * Confirmation dialog for the Hide row action on /admin/resources.
 *
 * Uses ``role="alertdialog"`` so the test layer can disambiguate
 * from the add/edit modals (which use ``role="dialog"``).
 */

import { Button } from "@/components/ui/button";

export interface HideConfirmState {
  open: boolean;
  resourceId: number | null;
  resourceName: string;
}

export function ConfirmHideDialog({
  state,
  busy,
  onCancel,
  onConfirm,
}: {
  state: HideConfirmState;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  if (!state.open) return null;
  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-label="Confirm hide"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
    >
      <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg space-y-4">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Hide resource?</h2>
          <p className="text-sm text-muted-foreground">
            Are you sure you want to hide
            {" "}<span className="font-medium">{state.resourceName}</span>?
            It can be restored from the hidden list.
          </p>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={busy}
          >
            Hide
          </Button>
        </div>
      </div>
    </div>
  );
}
