"use client";

/**
 * /admin/assessments/[versionId] — reviewer detail surface (T23.7).
 *
 * Fetches one version + its questions via :func:`getAssessmentVersion`,
 * renders the questions ordered by position, and exposes review actions
 * (approve / reject / request_revision) plus an admin-only publish
 * button (visible when the version status is ``approved``).
 *
 * Auth guard
 * ----------
 * As of T23.8 the reviewer-role gate lives in
 * :file:`frontend/src/app/admin/layout.tsx` via ``<RoleGate>``; this
 * page no longer carries its own ``useAccount``-redirect. The layout
 * gate already blocks anonymous + unprivileged browsers before this
 * component renders.
 *
 * Publish button visibility
 * -------------------------
 * The button is rendered iff the loaded version's
 * ``status === "approved"`` AND the current account holds the
 * ``admin`` role (T23.8 — reads from ``useAccountRoles``). If a
 * non-admin somehow reaches this surface the backend still returns
 * 403 and we surface the error inline.
 */

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAccountRoles } from "@/lib/api/auth";
import {
  AssessmentsApiError,
  type AssessmentVersion,
  type ReviewAction,
  getAssessmentVersion,
  publishAssessment,
  reviewAssessment,
} from "@/lib/api/assessments";

const TEXTAREA_CLASS =
  "w-full min-h-[88px] rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring";

export default function AssessmentDetailPage() {
  const params = useParams<{ versionId: string }>();
  const versionId = Number(params?.versionId);
  const roles = useAccountRoles();
  const queryClient = useQueryClient();

  const versionQuery = useQuery<AssessmentVersion>({
    queryKey: ["admin", "assessments", versionId],
    queryFn: () => getAssessmentVersion(versionId),
    enabled: Number.isFinite(versionId),
    retry: false,
    staleTime: 30_000,
  });

  const [comment, setComment] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  const reviewMutation = useMutation<
    unknown,
    AssessmentsApiError,
    ReviewAction
  >({
    mutationFn: (action) =>
      reviewAssessment(versionId, action, comment.trim() || null),
    onSuccess: () => {
      setActionError(null);
      setComment("");
      queryClient.invalidateQueries({
        queryKey: ["admin", "assessments", versionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["admin", "assessments", "pending"],
      });
    },
    onError: (err) => setActionError(err.message),
  });

  const publishMutation = useMutation<unknown, AssessmentsApiError, void>({
    mutationFn: () => publishAssessment(versionId),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({
        queryKey: ["admin", "assessments", versionId],
      });
    },
    onError: (err) => setActionError(err.message),
  });

  const orderedQuestions = useMemo(
    () =>
      [...(versionQuery.data?.questions ?? [])].sort(
        (a, b) => a.position - b.position,
      ),
    [versionQuery.data],
  );

  if (versionQuery.isLoading) return <_LoadingShell />;
  if (versionQuery.error) return <_ErrorShell />;
  if (!versionQuery.data) return null;

  const version = versionQuery.data;
  // Publish is admin-only on the backend (S22 ``require_role("admin")``).
  // Hide the button when the current account doesn't hold ``admin`` to
  // avoid showing a button that will 403 on click.
  const showPublish =
    version.status === "approved" && roles.includes("admin");
  const busy = reviewMutation.isPending || publishMutation.isPending;

  return (
    <main className="min-h-screen px-4 py-8 max-w-4xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">
          Version {version.version_number}
        </h1>
        <p className="text-sm text-muted-foreground">
          Status: <span className="font-medium">{version.status}</span> •{" "}
          assessment #{version.assessment_id}
        </p>
      </header>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            Questions ({orderedQuestions.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-4 list-decimal list-inside" role="list">
            {orderedQuestions.map((q) => (
              <li key={q.id} className="text-sm">
                <span className="font-medium">{q.prompt}</span>
                <span className="ml-2 text-xs text-muted-foreground">
                  ({q.kind}, weight {q.scoring_weight})
                </span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Reviewer comment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="comment" className="text-sm font-medium">
              Comment (optional)
            </label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className={TEXTAREA_CLASS}
              disabled={busy}
              placeholder="Optional rationale recorded with the review."
            />
          </div>

          {actionError ? (
            <p className="text-sm text-destructive" role="alert">
              {actionError}
            </p>
          ) : null}

          <_ActionButtons
            disabled={busy}
            onAction={(a) => reviewMutation.mutate(a)}
          />

          {showPublish ? (
            <Button
              onClick={() => publishMutation.mutate()}
              disabled={busy}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {publishMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Publish version"
              )}
            </Button>
          ) : null}
        </CardContent>
      </Card>
    </main>
  );
}

function _ActionButtons({
  disabled,
  onAction,
}: {
  disabled: boolean;
  onAction: (a: ReviewAction) => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
      <Button
        onClick={() => onAction("approve")}
        disabled={disabled}
        className="bg-primary text-primary-foreground hover:bg-primary/90"
      >
        Approve
      </Button>
      <Button
        onClick={() => onAction("request_revision")}
        disabled={disabled}
        className="bg-warning text-warning-foreground hover:bg-warning/90"
      >
        Request revision
      </Button>
      <Button
        onClick={() => onAction("reject")}
        disabled={disabled}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        Reject
      </Button>
    </div>
  );
}

function _LoadingShell() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </main>
  );
}

function _ErrorShell() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-6 space-y-3">
          <p className="text-lg font-semibold">We couldn&apos;t load this version</p>
          <p className="text-sm text-muted-foreground">
            The draft may have been published, retired, or the link may be
            stale. Try returning to the queue.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
