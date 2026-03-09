"use client";

import { AlertTriangle, Bus, Clock, ExternalLink, Footprints, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { TransitInfoDetail, TransitWarning } from "@/lib/types";
import { STATUS_BADGE_STYLES, safeHref } from "@/lib/constants";

const WARNING_LABELS: Record<TransitWarning, string> = {
  sunday_gap: "No Sunday service",
  night_gap: "No night service",
  long_walk: "Long walk to stop",
  transfer_required: "Transfer required",
};

interface TransitInfoDisplayProps {
  transitInfo: TransitInfoDetail | null | undefined;
}

export function TransitInfoDisplay({ transitInfo }: TransitInfoDisplayProps) {
  if (!transitInfo) return null;

  const { serving_routes, transfer_count, warnings, google_maps_url } = transitInfo;
  const hasRoutes = serving_routes.length > 0;
  const nearest = hasRoutes ? serving_routes[0] : null;

  return (
    <div className="space-y-2 text-sm" aria-label="Transit information">
      {/* Route badges */}
      {hasRoutes ? (
        <div className="flex flex-wrap items-center gap-1.5">
          <Bus className="h-3.5 w-3.5 text-muted-foreground shrink-0" aria-hidden="true" />
          {serving_routes.map((r) => (
            <Badge
              key={r.route_number}
              className={`${r.feasible ? STATUS_BADGE_STYLES.positive : STATUS_BADGE_STYLES.warning} text-xs`}
              variant="outline"
              aria-label={`Route ${r.route_number} ${r.route_name}${!r.feasible ? " schedule conflict" : ""}`}
            >
              #{r.route_number} {r.route_name}
              {!r.feasible && " — schedule conflict"}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="flex items-center gap-1.5 text-muted-foreground">
          <Bus className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          No bus routes nearby
        </p>
      )}

      {/* First/last bus schedule per route */}
      {hasRoutes && (
        <div className="flex flex-wrap items-center gap-3 text-muted-foreground">
          <Clock className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          {serving_routes.map((r) => (
            <span key={r.route_number}>
              #{r.route_number}: {r.first_bus}–{r.last_bus}
            </span>
          ))}
        </div>
      )}

      {/* Walk distance + nearest stop */}
      {nearest && (
        <p className="flex items-center gap-1.5 text-muted-foreground">
          <Footprints className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          {nearest.walk_miles.toFixed(1)} mi walk to {nearest.nearest_stop}
        </p>
      )}

      {/* Transfer count */}
      {transfer_count > 0 && (
        <p className="flex items-center gap-1.5 text-muted-foreground">
          <RefreshCw className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          {transfer_count} transfer{transfer_count > 1 ? "s" : ""}
        </p>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5" role="status">
          <AlertTriangle className="h-3.5 w-3.5 text-warning shrink-0" aria-hidden="true" />
          {warnings.map((w) => (
            <Badge key={w} className={`${STATUS_BADGE_STYLES.warning} text-xs`} variant="outline">
              {WARNING_LABELS[w]}
            </Badge>
          ))}
        </div>
      )}

      {/* Google Maps link */}
      {(() => {
        const mapsHref = google_maps_url ? safeHref(google_maps_url) : undefined;
        return mapsHref ? (
        <a
          href={mapsHref}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-secondary hover:underline"
        >
          Plan your trip
          <ExternalLink className="h-3 w-3" aria-hidden="true" />
        </a>
        ) : null;
      })()}
    </div>
  );
}
