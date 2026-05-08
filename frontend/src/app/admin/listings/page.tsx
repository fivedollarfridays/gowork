"use client";

/**
 * /admin/listings — admin claim-review queue (T24.9).
 *
 * Lists pending claims returned by :func:`listPendingClaims`. Filters
 * (intake state) are applied client-side over the already
 * admin-reviewed-tier-scoped server response.
 *
 * Auth guard
 * ----------
 * The shared :file:`frontend/src/app/admin/layout.tsx` already wraps
 * every ``/admin/*`` page in a broader reviewer-role gate (admin /
 * case_manager / sme_reviewer / dao_reviewer). This page narrows the
 * gate to admin-only via a stricter ``<RoleGate roles={["admin"]}>``
 * wrap so non-admin reviewers see a "Permission denied" card instead
 * of an empty/error queue. Authoritative role enforcement remains on
 * the backend (require_role("admin")).
 */

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RoleGate } from "@/components/auth/RoleGate";
import {
  listPendingClaims,
  type PendingClaim,
} from "@/lib/api/listing_claims";

const ALL = "__all__";
const STRICT_ADMIN_ROLES = ["admin"] as const;

interface FilterState {
  intake: string;
}

function _filterRows(
  rows: PendingClaim[],
  filters: FilterState,
): PendingClaim[] {
  return rows.filter((r) => {
    if (filters.intake === "with_intake" && !r.intake_completed_at) {
      return false;
    }
    if (filters.intake === "no_intake" && r.intake_completed_at) {
      return false;
    }
    return true;
  });
}

function ListingsPageInner() {
  const router = useRouter();

  const query = useQuery<PendingClaim[]>({
    queryKey: ["admin", "listings", "pending"],
    queryFn: listPendingClaims,
    staleTime: 30_000,
  });

  const [filters, setFilters] = useState<FilterState>({ intake: ALL });

  const rows = useMemo(
    () => _filterRows(query.data ?? [], filters),
    [query.data, filters],
  );

  return (
    <main className="min-h-screen px-4 py-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">
          Pending claim reviews
        </h1>
        <p className="text-sm text-muted-foreground">
          Listings flagged for admin review. Approve to confirm employer
          ownership; reject to discard the claim.
        </p>
      </header>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label htmlFor="filter-intake" className="text-sm font-medium">
              Intake
            </label>
            <select
              id="filter-intake"
              value={filters.intake}
              onChange={(e) =>
                setFilters((f) => ({ ...f, intake: e.target.value }))
              }
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value={ALL}>All</option>
              <option value="with_intake">With intake</option>
              <option value="no_intake">No intake</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {query.isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : rows.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No pending claim reviews match these filters.
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-3" role="list">
          {rows.map((r) => (
            <li key={r.claim_id}>
              <Button
                variant="outline"
                onClick={() => router.push(`/admin/listings/${r.claim_id}`)}
                className="w-full justify-between text-left h-auto py-3"
              >
                <span className="flex flex-col items-start gap-1">
                  <span className="font-semibold">{r.claimant_email}</span>
                  <span className="text-xs text-muted-foreground">
                    {r.listing_title} • {r.employer_domain ?? "(no domain)"}
                  </span>
                </span>
                <span className="text-xs uppercase tracking-wide text-primary">
                  {r.intake_completed_at ? "intake done" : "no intake"}
                </span>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

export default function AdminListingsPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <ListingsPageInner />
    </RoleGate>
  );
}
