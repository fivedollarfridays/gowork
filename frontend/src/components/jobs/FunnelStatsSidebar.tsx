"use client";

import { useTranslation } from "@/hooks/useTranslation";
import type { FunnelResult } from "@/lib/api/jobApplications";
import { Card, CardContent } from "@/components/ui/card";

interface FunnelStatsSidebarProps {
  funnel: FunnelResult | null | undefined;
  loading?: boolean;
}

function formatRate(r: number | null): string {
  if (r == null) return "—";
  return `${Math.round(r * 100)}%`;
}

/**
 * Right-rail sidebar summarizing the session's funnel: per-stage counts
 * plus conversion rates draft→applied, applied→interview, interview→offer.
 */
export function FunnelStatsSidebar({
  funnel,
  loading = false,
}: FunnelStatsSidebarProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <aside
        aria-label={t("jobs.funnelTitle")}
        data-testid="funnel-sidebar-loading"
        className="w-full md:w-64"
      >
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">{t("jobs.loading")}</p>
          </CardContent>
        </Card>
      </aside>
    );
  }

  const counts = funnel?.counts ?? {
    draft: 0,
    applied: 0,
    interview: 0,
    offer: 0,
    rejected: 0,
    withdrawn: 0,
  };
  const total =
    counts.draft +
    counts.applied +
    counts.interview +
    counts.offer +
    counts.rejected +
    counts.withdrawn;

  const rates: Array<{ key: string; label: string; value: number | null }> = [
    {
      key: "draftToApplied",
      label: t("jobs.funnelDraftToApplied"),
      value: funnel?.draft_to_applied_rate ?? null,
    },
    {
      key: "appliedToInterview",
      label: t("jobs.funnelAppliedToInterview"),
      value: funnel?.applied_to_interview_rate ?? null,
    },
    {
      key: "interviewToOffer",
      label: t("jobs.funnelInterviewToOffer"),
      value: funnel?.interview_to_offer_rate ?? null,
    },
  ];

  const hasAnyRate = rates.some((r) => r.value != null);

  return (
    <aside
      aria-label={t("jobs.funnelTitle")}
      data-testid="funnel-sidebar"
      className="w-full md:w-64"
    >
      <Card>
        <CardContent className="space-y-3 p-4">
          <h2 className="text-sm font-semibold text-foreground">
            {t("jobs.funnelTitle")}
          </h2>
          <dl className="space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.funnelTotal")}
              </dt>
              <dd className="font-medium" data-testid="funnel-total">
                {total}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnDraft")}
              </dt>
              <dd data-testid="funnel-count-draft">{counts.draft}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnApplied")}
              </dt>
              <dd data-testid="funnel-count-applied">{counts.applied}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnInterview")}
              </dt>
              <dd data-testid="funnel-count-interview">{counts.interview}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnOffer")}
              </dt>
              <dd data-testid="funnel-count-offer">{counts.offer}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnRejected")}
              </dt>
              <dd data-testid="funnel-count-rejected">{counts.rejected}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">
                {t("jobs.columnWithdrawn")}
              </dt>
              <dd data-testid="funnel-count-withdrawn">{counts.withdrawn}</dd>
            </div>
          </dl>

          <div>
            <h3 className="mt-3 text-xs font-semibold text-foreground">
              {t("jobs.funnelConversions")}
            </h3>
            {hasAnyRate ? (
              <dl className="mt-1 space-y-1 text-xs">
                {rates.map((r) => (
                  <div
                    key={r.key}
                    className="flex items-center justify-between"
                  >
                    <dt className="text-muted-foreground">{r.label}</dt>
                    <dd
                      className="font-medium"
                      data-testid={`funnel-rate-${r.key}`}
                    >
                      {formatRate(r.value)}
                    </dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="mt-1 text-xs italic text-muted-foreground">
                {t("jobs.funnelNoData")}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </aside>
  );
}
