"use client";

/**
 * Read-only status panel for the /admin/brightdata page (T26.10).
 * Extracted from `app/admin/brightdata/page.tsx` to keep the page
 * module under the 400-line size budget.
 *
 * Renders three things in a definition list:
 *
 *   - The last triggered snapshot id (or "—" if none).
 *   - The current `CrawlStatus.status` mapped through `STATUS_COPY`
 *     so the operator sees the human label instead of the wire value.
 *     All four backend states (`starting | running | ready | failed`)
 *     have copy entries — the test-suite parametrizes over them.
 *   - The timestamp of the most recent refresh (rendered as a `<time>`
 *     element so jsdom + screen readers both work).
 *
 * The Refresh Status button is disabled when there is no snapshot to
 * poll, or while a poll is already in-flight.
 */

import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type {
  CrawlStatus,
  CrawlStatusValue,
} from "@/lib/api/admin_brightdata";

const STATUS_COPY: Record<CrawlStatusValue, string> = {
  starting: "Starting",
  running: "Running",
  ready: "Ready",
  failed: "Failed",
};

export interface StatusPanelProps {
  snapshotId: string | null;
  status: CrawlStatus | null;
  lastRefreshed: Date | null;
  onRefresh: () => void;
  refreshing: boolean;
  errorText: string | null;
}

export function StatusPanel(props: StatusPanelProps) {
  return (
    <Card data-testid="status-panel">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Last triggered snapshot</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <dl className="grid grid-cols-3 gap-y-2 text-sm">
          <dt className="col-span-1 text-muted-foreground">Snapshot id</dt>
          <dd
            className="col-span-2 font-mono break-all"
            data-testid="snapshot-id"
          >
            {props.snapshotId ?? (
              <span className="text-muted-foreground">—</span>
            )}
          </dd>

          <dt className="col-span-1 text-muted-foreground">Current status</dt>
          <dd
            className="col-span-2 font-medium"
            data-testid="snapshot-status"
          >
            {props.status ? (
              STATUS_COPY[props.status.status]
            ) : (
              <span className="text-muted-foreground">
                Not refreshed yet
              </span>
            )}
          </dd>

          <dt className="col-span-1 text-muted-foreground">Last refreshed</dt>
          <dd className="col-span-2">
            {props.lastRefreshed ? (
              <time dateTime={props.lastRefreshed.toISOString()}>
                {props.lastRefreshed.toLocaleString()}
              </time>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </dd>
        </dl>

        {props.errorText && (
          <p role="alert" className="text-sm text-destructive">
            {props.errorText}
          </p>
        )}

        <div>
          <Button
            type="button"
            variant="outline"
            onClick={props.onRefresh}
            disabled={!props.snapshotId || props.refreshing}
          >
            {props.refreshing ? (
              <Loader2
                className="mr-2 h-4 w-4 animate-spin"
                aria-hidden="true"
              />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
            )}
            Refresh Status
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
