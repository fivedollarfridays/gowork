"use client";

/**
 * FeedbackTabs — split content for the /admin/feedback page (T26.9).
 *
 * The page itself (frontend/src/app/admin/feedback/page.tsx) owns the
 * shadcn ``Tabs`` shell and URL-hash sync. This module owns the two
 * tab bodies, deliberately broken out so each can be unit-tested in
 * isolation without going through the radix ``Tabs`` data-state
 * dance:
 *
 *   - ``FlaggedResourcesTab`` — card-per-flagged-resource queue.
 *     Pulls from :func:`listFlagged` (T26.6 client → T26.3 backend).
 *     Row actions invoke :func:`approveFlagged` /
 *     :func:`confirmHide` and refetch on success.
 *
 *   - ``VisitFeedbackTab`` — visit-feedback inbox table. Pulls from
 *     :func:`listVisits` with a reviewed-status filter. Row action
 *     opens an inline ``action_taken`` editor that submits via
 *     :func:`markVisitReviewed`.
 *
 * Both tabs paginate independently (50 per page; prev/next).
 *
 * Charter integrity (S25/T26):
 *   No matching-engine imports. This is admin-only diagnostic
 *   plumbing wired straight to the feedback substrate.
 */

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  approveFlagged,
  confirmHide,
  listFlagged,
  listVisits,
  markVisitReviewed,
  type FlaggedResource,
  type FlaggedResourcesResponse,
  type VisitFeedback,
  type VisitFeedbackListResponse,
} from "@/lib/api/admin_feedback";

const PAGE_SIZE = 50;

/* ---------------------------------------------------------------------------
 * FlaggedResourcesTab
 * ------------------------------------------------------------------------- */

export interface FlaggedResourcesTabProps {
  city?: string;
}

const DEFAULT_CITY = "fort-worth";
const FLAGGED_QUERY_KEY = ["admin", "feedback", "flagged"] as const;

function _FlaggedRow({
  resource,
  onApprove,
  onHide,
  isPending,
}: {
  resource: FlaggedResource;
  onApprove: (id: number) => void;
  onHide: (id: number) => void;
  isPending: boolean;
}) {
  return (
    <Card data-testid={`flagged-card-${resource.id}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center justify-between">
          <span>{resource.name}</span>
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            {resource.category ?? "(uncategorised)"}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-muted-foreground">
          {resource.address ?? "(no address)"}
          {resource.phone ? ` • ${resource.phone}` : ""}
        </p>
        {resource.recent_negative_feedback.length === 0 ? (
          <p className="text-xs italic text-muted-foreground">
            No recent negative feedback in window.
          </p>
        ) : (
          <ul className="space-y-1 text-xs" role="list">
            {resource.recent_negative_feedback.map((entry, idx) => (
              <li
                key={`${entry.session_id}-${idx}`}
                className="rounded border border-muted px-2 py-1"
              >
                <span className="font-mono">{entry.barrier_type ?? "—"}</span>
                <span className="ml-2 text-muted-foreground">
                  {entry.submitted_at}
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="flex gap-2 pt-1">
          <Button
            variant="outline"
            size="sm"
            disabled={isPending}
            onClick={() => onApprove(resource.id)}
          >
            Approve
          </Button>
          <Button
            variant="destructive"
            size="sm"
            disabled={isPending}
            onClick={() => onHide(resource.id)}
          >
            Confirm Hide
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function _Pager({
  page,
  hasNext,
  onPrev,
  onNext,
}: {
  page: number;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center justify-between pt-3">
      <Button
        variant="outline"
        size="sm"
        onClick={onPrev}
        disabled={page === 0}
      >
        Prev
      </Button>
      <span className="text-xs text-muted-foreground">Page {page + 1}</span>
      <Button
        variant="outline"
        size="sm"
        onClick={onNext}
        disabled={!hasNext}
      >
        Next
      </Button>
    </div>
  );
}

export function FlaggedResourcesTab({
  city = DEFAULT_CITY,
}: FlaggedResourcesTabProps) {
  const qc = useQueryClient();
  const [page, setPage] = useState(0);

  const query = useQuery<FlaggedResourcesResponse>({
    queryKey: [...FLAGGED_QUERY_KEY, city],
    queryFn: () => listFlagged(city),
    staleTime: 30_000,
  });

  const refetch = () => {
    qc.invalidateQueries({ queryKey: [...FLAGGED_QUERY_KEY, city] });
  };

  const approveMut = useMutation({
    mutationFn: (id: number) => approveFlagged(id),
    onSuccess: refetch,
  });
  const hideMut = useMutation({
    mutationFn: (id: number) => confirmHide(id),
    onSuccess: refetch,
  });
  const isPending = approveMut.isPending || hideMut.isPending;

  const items = useMemo(() => query.data?.items ?? [], [query.data]);
  const pageItems = useMemo(
    () => items.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [items, page],
  );
  const hasNext = items.length > (page + 1) * PAGE_SIZE;

  if (query.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }
  if (query.isError) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          Couldn&rsquo;t load flagged resources. Try again shortly.
        </CardContent>
      </Card>
    );
  }
  if (pageItems.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No flagged resources for {city}.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {pageItems.map((r) => (
        <_FlaggedRow
          key={r.id}
          resource={r}
          onApprove={approveMut.mutate}
          onHide={hideMut.mutate}
          isPending={isPending}
        />
      ))}
      <_Pager
        page={page}
        hasNext={hasNext}
        onPrev={() => setPage((p) => Math.max(0, p - 1))}
        onNext={() => setPage((p) => p + 1)}
      />
    </div>
  );
}

/* ---------------------------------------------------------------------------
 * VisitFeedbackTab
 * ------------------------------------------------------------------------- */

type VisitFilter = "all" | "reviewed" | "unreviewed";
const VISITS_QUERY_KEY = ["admin", "feedback", "visits"] as const;

function _filterToReviewedParam(filter: VisitFilter): boolean | undefined {
  if (filter === "reviewed") return true;
  if (filter === "unreviewed") return false;
  return undefined;
}

function _Stars({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  const clamped = Math.max(0, Math.min(5, value));
  return (
    <span aria-label={`${value} stars`} className="font-mono">
      {"★".repeat(clamped)}
      {"☆".repeat(5 - clamped)}
    </span>
  );
}

function _ReviewedBadge({ reviewed }: { reviewed: number }) {
  return reviewed ? (
    <Badge variant="secondary">Reviewed</Badge>
  ) : (
    <Badge variant="outline">Unreviewed</Badge>
  );
}

function _MadeItBadge({ value }: { value: number }) {
  return value ? (
    <Badge variant="secondary">Yes</Badge>
  ) : (
    <Badge variant="destructive">No</Badge>
  );
}

interface VisitRowProps {
  visit: VisitFeedback;
  isEditing: boolean;
  draft: string;
  onStartEdit: (id: number) => void;
  onCancelEdit: () => void;
  onChangeDraft: (text: string) => void;
  onSubmit: (id: number) => void;
  isPending: boolean;
}

function _VisitRow(props: VisitRowProps) {
  const {
    visit,
    isEditing,
    draft,
    onStartEdit,
    onCancelEdit,
    onChangeDraft,
    onSubmit,
    isPending,
  } = props;
  return (
    <tr data-testid={`visit-row-${visit.id}`} className="border-b align-top">
      <td className="py-2 pr-3 text-xs font-mono">{visit.submitted_at}</td>
      <td className="py-2 pr-3">
        <_MadeItBadge value={visit.made_it_to_center} />
      </td>
      <td className="py-2 pr-3">
        <_Stars value={visit.plan_accuracy} />
      </td>
      <td className="py-2 pr-3 text-xs max-w-xs truncate" title={visit.free_text ?? ""}>
        {visit.free_text ?? "—"}
      </td>
      <td className="py-2 pr-3">
        <_ReviewedBadge reviewed={visit.reviewed} />
      </td>
      <td className="py-2 pr-3 text-xs">{visit.action_taken ?? "—"}</td>
      <td className="py-2">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              data-testid={`action-taken-${visit.id}`}
              value={draft}
              onChange={(e) => onChangeDraft(e.target.value)}
              className="w-full text-xs rounded border border-input bg-transparent p-2"
              rows={2}
              placeholder="Action taken (optional)"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={isPending}
                onClick={() => onSubmit(visit.id)}
              >
                Submit Reviewed
              </Button>
              <Button
                size="sm"
                variant="ghost"
                disabled={isPending}
                onClick={onCancelEdit}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button
            size="sm"
            variant="outline"
            disabled={Boolean(visit.reviewed)}
            onClick={() => onStartEdit(visit.id)}
          >
            Mark Reviewed
          </Button>
        )}
      </td>
    </tr>
  );
}

export function VisitFeedbackTab() {
  const qc = useQueryClient();
  const [page, setPage] = useState(0);
  const [filter, setFilter] = useState<VisitFilter>("all");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  const reviewedParam = _filterToReviewedParam(filter);

  const query = useQuery<VisitFeedbackListResponse>({
    queryKey: [...VISITS_QUERY_KEY, reviewedParam, page],
    queryFn: () =>
      listVisits({
        reviewed: reviewedParam,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    staleTime: 30_000,
  });

  const reviewMut = useMutation({
    mutationFn: (id: number) =>
      markVisitReviewed(id, draft.trim() === "" ? undefined : draft),
    onSuccess: () => {
      setEditingId(null);
      setDraft("");
      qc.invalidateQueries({ queryKey: [...VISITS_QUERY_KEY] });
    },
  });

  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const hasNext = (page + 1) * PAGE_SIZE < total;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <label htmlFor="visit-filter" className="text-sm font-medium">
          Filter
        </label>
        <select
          id="visit-filter"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value as VisitFilter);
            setPage(0);
          }}
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          <option value="all">All</option>
          <option value="reviewed">Reviewed</option>
          <option value="unreviewed">Unreviewed</option>
        </select>
      </div>

      {query.isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : query.isError ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Couldn&rsquo;t load visit feedback. Try again shortly.
          </CardContent>
        </Card>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No visit feedback for this filter.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-muted-foreground">
              <tr className="border-b">
                <th className="py-2 pr-3">Submitted</th>
                <th className="py-2 pr-3">Made it</th>
                <th className="py-2 pr-3">Accuracy</th>
                <th className="py-2 pr-3">Notes</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3">Action taken</th>
                <th className="py-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((v) => (
                <_VisitRow
                  key={v.id}
                  visit={v}
                  isEditing={editingId === v.id}
                  draft={editingId === v.id ? draft : ""}
                  onStartEdit={(id) => {
                    setEditingId(id);
                    setDraft("");
                  }}
                  onCancelEdit={() => {
                    setEditingId(null);
                    setDraft("");
                  }}
                  onChangeDraft={setDraft}
                  onSubmit={(id) => reviewMut.mutate(id)}
                  isPending={reviewMut.isPending}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <_Pager
        page={page}
        hasNext={hasNext}
        onPrev={() => setPage((p) => Math.max(0, p - 1))}
        onNext={() => setPage((p) => p + 1)}
      />
    </div>
  );
}
