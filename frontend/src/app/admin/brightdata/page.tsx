"use client";

/**
 * /admin/brightdata — manual BrightData pre-crawl trigger (T26.10).
 *
 * Operator-facing surface for kicking off BrightData job-board crawls
 * by city. Two responsibilities, both gated by the admin layout's
 * `<RoleGate>` (we do NOT re-wrap here per spec):
 *
 *   1. Trigger panel — city dropdown + "Trigger Pre-Crawl" button. The
 *      button opens a confirmation `AlertDialog` (BrightData calls cost
 *      money, so an accidental click must not fire the request). On
 *      confirm we call `triggerCrawl({ urls })` from the T26.7 client.
 *      The trigger button is disabled while a request is in flight.
 *
 *   2. Status panel — shows the last triggered snapshot id and its
 *      current status (one of four states: `starting | running | ready
 *      | failed`, per the backend `CrawlStatus` enum). A "Refresh
 *      Status" button calls `getCrawlStatus(snapshotId)` on demand
 *      (manual poll only — auto-refresh / SSE is explicitly
 *      out-of-scope for S26).
 *
 * Persistence:
 *   The last triggered snapshot id is mirrored into `localStorage`
 *   under `STORAGE_KEY` so a page reload preserves it. There is no
 *   server-side session; the page is a thin shell over the typed API
 *   client.
 *
 * Backend contract (per the T26.7 client deviation note):
 *   - Routes are mounted at `/api/brightdata` (not `/api/admin/...`).
 *   - `CrawlStatus` enum has FOUR states (the brief said three).
 *   - The trigger payload is `{ urls: string[] }` — the city the
 *     operator picks here is mapped client-side to a static list of
 *     job-board URLs (see `CITY_CRAWL_URLS`).
 *
 * Module decomposition:
 *   The confirmation dialog and read-only status panel each live in
 *   `components/admin/brightdata/` so this page module stays under the
 *   400-line size budget.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ConfirmTriggerDialog } from "@/components/admin/brightdata/ConfirmTriggerDialog";
import { StatusPanel } from "@/components/admin/brightdata/StatusPanel";
import {
  triggerCrawl,
  getCrawlStatus,
  type CrawlStatus,
  type TriggerCrawlPayload,
  AdminBrightDataApiError,
} from "@/lib/api/admin_brightdata";

const STORAGE_KEY = "admin.brightdata.lastSnapshotId";

type CitySlug = "fort-worth" | "dallas" | "montgomery";

interface CityOption {
  slug: CitySlug;
  label: string;
}

const CITY_OPTIONS: readonly CityOption[] = [
  { slug: "fort-worth", label: "Fort Worth" },
  { slug: "dallas", label: "Dallas" },
  { slug: "montgomery", label: "Montgomery" },
] as const;

/**
 * Static city → seed crawl URL map. The trigger endpoint takes raw
 * URLs (Pydantic validates HTTPS-only on the backend) so the operator
 * picks the city and we expand it here. These are the job-board
 * landing pages the seed scripts already use; keeping them inline
 * avoids adding a fetch round-trip for a constant.
 */
const CITY_CRAWL_URLS: Record<CitySlug, string[]> = {
  "fort-worth": ["https://www.indeed.com/jobs?l=Fort+Worth%2C+TX"],
  dallas: ["https://www.indeed.com/jobs?l=Dallas%2C+TX"],
  montgomery: ["https://www.indeed.com/jobs?l=Montgomery%2C+AL"],
};

function _readSnapshotIdFromStorage(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    // Some browsers (private mode) throw on localStorage access — fall
    // back to "no persisted id" rather than crashing the page.
    return null;
  }
}

function _writeSnapshotIdToStorage(id: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, id);
  } catch {
    // Ignore — persistence is a nice-to-have, not load-bearing.
  }
}

export default function AdminBrightDataPage() {
  const [city, setCity] = useState<CitySlug>("fort-worth");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [snapshotId, setSnapshotId] = useState<string | null>(null);
  const [status, setStatus] = useState<CrawlStatus | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);

  // Restore the persisted snapshot id on mount so a page reload still
  // shows the operator their most recent crawl.
  useEffect(() => {
    const persisted = _readSnapshotIdFromStorage();
    if (persisted) setSnapshotId(persisted);
  }, []);

  const cityLabel = useMemo(
    () => CITY_OPTIONS.find((c) => c.slug === city)?.label ?? city,
    [city],
  );
  const urls = CITY_CRAWL_URLS[city];

  const handleConfirm = useCallback(async () => {
    setTriggering(true);
    setTriggerError(null);
    const payload: TriggerCrawlPayload = { urls };
    try {
      const res = await triggerCrawl(payload);
      setSnapshotId(res.snapshot_id);
      _writeSnapshotIdToStorage(res.snapshot_id);
      // Reset the prior status — the new snapshot hasn't been polled yet.
      setStatus({
        snapshot_id: res.snapshot_id,
        status: res.status,
        progress_pct: null,
        jobs_found: null,
        message: res.message,
      });
      setLastRefreshed(new Date());
      setConfirmOpen(false);
    } catch (err) {
      const message =
        err instanceof AdminBrightDataApiError
          ? `Trigger failed (${err.status}): ${err.detail ?? err.message}`
          : "Trigger failed. Try again or check the server logs.";
      setTriggerError(message);
      setConfirmOpen(false);
    } finally {
      setTriggering(false);
    }
  }, [urls]);

  const handleRefresh = useCallback(async () => {
    if (!snapshotId) return;
    setRefreshing(true);
    setStatusError(null);
    try {
      const res = await getCrawlStatus(snapshotId);
      setStatus(res);
      setLastRefreshed(new Date());
    } catch (err) {
      const message =
        err instanceof AdminBrightDataApiError
          ? `Status check failed (${err.status}): ${err.detail ?? err.message}`
          : "Status check failed. Try again shortly.";
      setStatusError(message);
    } finally {
      setRefreshing(false);
    }
  }, [snapshotId]);

  return (
    <main className="min-h-screen px-4 py-8 max-w-3xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">
          BrightData pre-crawl
        </h1>
        <p className="text-sm text-muted-foreground">
          Trigger a paid BrightData snapshot by city. Status is polled
          on demand — there is no auto-refresh.
        </p>
      </header>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Trigger panel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2" data-testid="city-selector">
            <label
              htmlFor="brightdata-city"
              className="block text-sm font-medium"
            >
              City
            </label>
            <Select
              value={city}
              onValueChange={(v) => setCity(v as CitySlug)}
            >
              <SelectTrigger id="brightdata-city" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CITY_OPTIONS.map((c) => (
                  <SelectItem key={c.slug} value={c.slug}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Button
              type="button"
              data-testid="trigger-button"
              onClick={() => setConfirmOpen(true)}
              disabled={triggering}
              aria-label={
                triggering ? "Triggering pre-crawl" : "Trigger pre-crawl"
              }
            >
              {triggering ? (
                <>
                  <Loader2
                    className="mr-2 h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Triggering…
                </>
              ) : (
                "Trigger Pre-Crawl"
              )}
            </Button>
          </div>

          {triggerError && (
            <p role="alert" className="text-sm text-destructive">
              {triggerError}
            </p>
          )}
        </CardContent>
      </Card>

      <StatusPanel
        snapshotId={snapshotId}
        status={status}
        lastRefreshed={lastRefreshed}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        errorText={statusError}
      />

      <ConfirmTriggerDialog
        open={confirmOpen}
        cityLabel={cityLabel}
        urlCount={urls.length}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleConfirm}
        busy={triggering}
      />
    </main>
  );
}
