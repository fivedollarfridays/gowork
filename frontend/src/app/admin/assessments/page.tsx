"use client";

/**
 * /admin/assessments — reviewer queue (T23.7).
 *
 * Lists pending assessment versions returned by
 * :func:`listPendingAssessments`. Filters (track / kind / status) are
 * applied client-side over the already-track-scoped server response.
 *
 * Auth guard
 * ----------
 * Local guard for T23.7: redirects to /auth/login when ``useAccount()``
 * resolves to ``{accountId: null}``. T23.8 will replace this with a
 * ``<RoleGate>`` wrapper that also enforces reviewer roles
 * (``case_manager`` / ``sme_reviewer`` / ``dao_reviewer``). Search for
 * ``LOCAL_GUARD_T23_7`` to find the swap-out site.
 */

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAccount } from "@/lib/api/auth";
import {
  listPendingAssessments,
  type PendingAssessment,
} from "@/lib/api/assessments";

const ALL = "__all__";

const TRACKS = ["vocational", "dao_tech", "generic"] as const;
const KINDS = ["screening", "onboarding", "exit"] as const;
const STATUSES = ["draft", "in_review"] as const;

interface FilterState {
  track: string;
  kind: string;
  status: string;
}

function _filterRows(
  rows: PendingAssessment[],
  filters: FilterState,
): PendingAssessment[] {
  return rows.filter((r) => {
    if (filters.track !== ALL && r.track !== filters.track) return false;
    if (filters.kind !== ALL && r.kind !== filters.kind) return false;
    if (filters.status !== ALL && r.status !== filters.status) return false;
    return true;
  });
}

export default function AssessmentsListPage() {
  const router = useRouter();
  const account = useAccount();

  // LOCAL_GUARD_T23_7 — T23.8 will replace with <RoleGate> wrapper.
  useEffect(() => {
    if (account.isLoading) return;
    if (!account.data || account.data.accountId == null) {
      router.push("/auth/login");
    }
  }, [account.isLoading, account.data, router]);

  const query = useQuery<PendingAssessment[]>({
    queryKey: ["admin", "assessments", "pending"],
    queryFn: listPendingAssessments,
    enabled: !!account.data && account.data.accountId != null,
    staleTime: 30_000,
  });

  const [filters, setFilters] = useState<FilterState>({
    track: ALL,
    kind: ALL,
    status: ALL,
  });

  const rows = useMemo(
    () => _filterRows(query.data ?? [], filters),
    [query.data, filters],
  );

  return (
    <main className="min-h-screen px-4 py-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">
          Pending assessments
        </h1>
        <p className="text-sm text-muted-foreground">
          Drafts awaiting reviewer action. Filter by track, kind, or status.
        </p>
      </header>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <_FilterSelect
            id="filter-track"
            label="Track"
            value={filters.track}
            options={TRACKS}
            onChange={(v) => setFilters((f) => ({ ...f, track: v }))}
          />
          <_FilterSelect
            id="filter-kind"
            label="Kind"
            value={filters.kind}
            options={KINDS}
            onChange={(v) => setFilters((f) => ({ ...f, kind: v }))}
          />
          <_FilterSelect
            id="filter-status"
            label="Status"
            value={filters.status}
            options={STATUSES}
            onChange={(v) => setFilters((f) => ({ ...f, status: v }))}
          />
        </CardContent>
      </Card>

      {query.isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : rows.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No pending assessments match these filters.
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-3" role="list">
          {rows.map((r) => (
            <li key={r.version_id}>
              <Button
                variant="outline"
                onClick={() => router.push(`/admin/assessments/${r.version_id}`)}
                className="w-full justify-between text-left h-auto py-3"
              >
                <span className="flex flex-col items-start gap-1">
                  <span className="font-semibold">{r.slug}</span>
                  <span className="text-xs text-muted-foreground">
                    v{r.version_number} • {r.kind} • {r.track}
                  </span>
                </span>
                <span className="text-xs uppercase tracking-wide text-primary">
                  {r.status}
                </span>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function _FilterSelect({
  id,
  label,
  value,
  options,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: readonly string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
      >
        <option value={ALL}>All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
