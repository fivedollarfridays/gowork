"use client";

/**
 * /admin/cities/dfw — DFW cross-metro diagnostic summary (T25.7).
 *
 * Charter integrity (S25 / T25.7):
 *   This page is **display-only**. The backend route
 *   :func:`app.routes.cities_admin.get_dfw_summary` reads counts from
 *   JSON seed files (no DB queries, no matching-engine imports). The
 *   "Read-only diagnostic. Cross-city matching is not enabled." copy
 *   in the header is the design-review trigger if a future sprint
 *   legitimately needs cross-metro matching — do not soften it.
 *
 * Auth guard:
 *   Wrapped in a strict ``<RoleGate roles={["admin"]}>`` that mirrors
 *   the backend ``require_role("admin")`` gate. The shared
 *   :file:`frontend/src/app/admin/layout.tsx` reviewer-role gate also
 *   wraps every ``/admin/*`` page; the strict admin wrap here narrows
 *   the surface to admins only (case-managers / SME reviewers see
 *   "Permission denied" instead of an error card).
 */

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RoleGate } from "@/components/auth/RoleGate";
import {
  getDfwSummary,
  type CitySummary,
  type DfwSummaryResponse,
  type DfwTotal,
} from "@/lib/api/cities_admin";

const STRICT_ADMIN_ROLES = ["admin"] as const;

function _formatPct(pct: number): string {
  return `${Math.round(pct * 1000) / 10}%`;
}

function _CityCard({ city }: { city: CitySummary }) {
  return (
    <Card data-testid={`city-card-${city.slug}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">
          {city.name}
          <span className="ml-2 text-xs uppercase tracking-wide text-muted-foreground">
            {city.state}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Employers</dt>
          <dd className="font-mono text-right">{city.employer_count}</dd>

          <dt className="text-muted-foreground">Fair-chance</dt>
          <dd className="font-mono text-right">
            {city.fair_chance_count} ({_formatPct(city.fair_chance_pct)})
          </dd>

          <dt className="text-muted-foreground">Transit routes</dt>
          <dd className="font-mono text-right">{city.transit_route_count}</dd>

          <dt className="text-muted-foreground">Transit stops</dt>
          <dd className="font-mono text-right">{city.transit_stop_count}</dd>

          <dt className="text-muted-foreground">Career centers</dt>
          <dd className="font-mono text-right">{city.career_center_count}</dd>
        </dl>

        <div className="mt-4 border-t pt-3">
          <p className="text-xs text-muted-foreground mb-1">
            Community resources by category
          </p>
          <dl className="grid grid-cols-2 gap-y-1 text-xs">
            {Object.entries(city.resource_counts)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([cat, count]) => (
                <React.Fragment key={cat}>
                  <dt className="text-muted-foreground">
                    {cat || "(uncategorised)"}
                  </dt>
                  <dd className="font-mono text-right">{count}</dd>
                </React.Fragment>
              ))}
          </dl>
        </div>
      </CardContent>
    </Card>
  );
}

function _TotalRow({ total }: { total: DfwTotal }) {
  return (
    <Card data-testid="dfw-total-row">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">DFW total</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-y-2 text-sm sm:grid-cols-5">
          <div className="space-y-0">
            <dt className="text-xs text-muted-foreground">Employers</dt>
            <dd className="font-mono">{total.employer_count}</dd>
          </div>
          <div className="space-y-0">
            <dt className="text-xs text-muted-foreground">Fair-chance</dt>
            <dd className="font-mono">
              {total.fair_chance_count} ({_formatPct(total.fair_chance_pct)})
            </dd>
          </div>
          <div className="space-y-0">
            <dt className="text-xs text-muted-foreground">Transit routes</dt>
            <dd className="font-mono">{total.transit_route_count}</dd>
          </div>
          <div className="space-y-0">
            <dt className="text-xs text-muted-foreground">Transit stops</dt>
            <dd className="font-mono">{total.transit_stop_count}</dd>
          </div>
          <div className="space-y-0">
            <dt className="text-xs text-muted-foreground">Career centers</dt>
            <dd className="font-mono">{total.career_center_count}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

function _LoadingCard() {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
    </div>
  );
}

function _ErrorCard() {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-muted-foreground">
        Couldn&rsquo;t load the DFW diagnostic summary. Check your connection
        or try again shortly.
      </CardContent>
    </Card>
  );
}

function CitiesDfwPageInner() {
  const query = useQuery<DfwSummaryResponse>({
    queryKey: ["admin", "cities", "dfw", "summary"],
    queryFn: getDfwSummary,
    staleTime: 60_000,
  });

  return (
    <main className="min-h-screen px-4 py-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">DFW metro summary</h1>
        <p className="text-sm text-muted-foreground">
          Read-only diagnostic. Cross-city matching is not enabled.
        </p>
      </header>

      {query.isLoading ? (
        <_LoadingCard />
      ) : query.isError || !query.data ? (
        <_ErrorCard />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {query.data.cities.map((city) => (
              <_CityCard key={city.slug} city={city} />
            ))}
          </div>
          <_TotalRow total={query.data.dfw_total} />
        </>
      )}
    </main>
  );
}

export default function AdminCitiesDfwPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <CitiesDfwPageInner />
    </RoleGate>
  );
}
