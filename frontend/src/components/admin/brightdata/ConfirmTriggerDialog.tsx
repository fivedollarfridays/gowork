"use client";

/**
 * Confirmation alert-dialog for the /admin/brightdata trigger flow
 * (T26.10). Extracted from `app/admin/brightdata/page.tsx` to keep the
 * page module under the 400-line size budget.
 *
 * Behaviour:
 *   - Renders nothing when `open` is false (no portal — simple
 *     conditional render is enough for a transient confirmation).
 *   - When open, shows a fixed-position overlay with `role="alertdialog"`
 *     so the test-suite can assert presence and so screen-readers see
 *     it as a destructive-action prompt.
 *   - The Confirm button swaps to a Loader2 spinner + "Triggering…"
 *     while the parent's request is in flight (`busy`).
 *
 * The component is intentionally dumb — all state lives in the parent.
 */

import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ConfirmTriggerDialogProps {
  open: boolean;
  cityLabel: string;
  urlCount: number;
  onCancel: () => void;
  onConfirm: () => void;
  busy: boolean;
}

export function ConfirmTriggerDialog(props: ConfirmTriggerDialogProps) {
  if (!props.open) return null;
  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="brightdata-confirm-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
    >
      <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
        <h2
          id="brightdata-confirm-title"
          className="text-lg font-semibold"
        >
          Trigger BrightData crawl?
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This will kick off a paid BrightData snapshot for{" "}
          <span className="font-medium text-foreground">
            {props.cityLabel}
          </span>{" "}
          ({props.urlCount} URL{props.urlCount === 1 ? "" : "s"}).
          BrightData calls cost real dollars — only confirm if you
          intended to trigger a crawl.
        </p>
        <div className="mt-4 flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={props.onCancel}
            disabled={props.busy}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={props.onConfirm}
            disabled={props.busy}
          >
            {props.busy ? (
              <>
                <Loader2
                  className="mr-2 h-4 w-4 animate-spin"
                  aria-hidden="true"
                />
                Triggering…
              </>
            ) : (
              "Confirm"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
