"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, Users, Shield, Inbox } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StalledSessionsList } from "@/components/StalledSessionsList";
import { SendAdvisorNoteDialog } from "@/components/SendAdvisorNoteDialog";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { getDashboardStats } from "@/lib/api";
import {
  listStalledSessions,
  sendAdvisorNote,
  AdvisorApiError,
} from "@/lib/api/advisor";

const ADVISOR_TOKEN_STORAGE_KEY = "montgowork_advisor_token";

function humanize(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function useAdvisorToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const fromUrl = url.searchParams.get("advisor_token");
      if (fromUrl) {
        sessionStorage.setItem(ADVISOR_TOKEN_STORAGE_KEY, fromUrl);
        setToken(fromUrl);
        return;
      }
      setToken(sessionStorage.getItem(ADVISOR_TOKEN_STORAGE_KEY));
    } catch {
      setToken(null);
    }
  }, []);
  return token;
}

function NeedsAttentionSection({ token }: { token: string }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<string | null>(null);
  const [noteOpen, setNoteOpen] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["advisor-stalled", token],
    queryFn: () => listStalledSessions(token),
    retry: 0,
  });

  const handleSubmit = useCallback(
    async (message: string): Promise<void> => {
      if (!selected) return;
      await sendAdvisorNote(selected, message, token);
    },
    [selected, token],
  );

  const handleSelect = useCallback((sid: string) => {
    setSelected(sid);
    setNoteOpen(true);
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Inbox className="h-5 w-5" aria-hidden="true" />
          {t("advisor.inboxHeading")}
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1">
          {t("advisor.inboxDescription")}
        </p>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <p className="text-sm text-muted-foreground">
            {t("common.loading")}
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error instanceof AdvisorApiError && error.status === 401
              ? t("advisor.noteForbidden")
              : t("advisor.noteGenericError")}
          </p>
        )}
        {data && (
          <StalledSessionsList
            sessions={data.sessions}
            onSelect={handleSelect}
          />
        )}
        {selected && (
          <SendAdvisorNoteDialog
            open={noteOpen}
            sessionId={selected}
            onClose={() => setNoteOpen(false)}
            onSubmit={handleSubmit}
          />
        )}
      </CardContent>
    </Card>
  );
}

function DashboardStats() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  if (isLoading) {
    return <p className="text-muted-foreground">{t("common.loading")}</p>;
  }
  if (error) {
    return (
      <p className="text-destructive">Failed to load dashboard data.</p>
    );
  }
  if (!data) return null;
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" /> Total Assessments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">
              {data.total_assessments}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Shield className="h-4 w-4" /> Barrier Instances
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">
              {data.total_barrier_instances}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <BarChart3 className="h-4 w-4" /> Avg Barriers/Person
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">
              {data.total_assessments > 0
                ? (data.total_barrier_instances / data.total_assessments).toFixed(1)
                : "0"}
            </div>
          </CardContent>
        </Card>
      </div>
      {data.common_barriers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Most Common Barriers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.common_barriers.map((item) => {
                const pct = data.total_assessments > 0
                  ? Math.round((item.count / data.total_assessments) * 100)
                  : 0;
                return (
                  <div key={item.barrier} className="flex items-center gap-3">
                    <span className="text-sm font-medium w-32">
                      {humanize(item.barrier)}
                    </span>
                    <div className="flex-1 h-4 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-secondary transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-12 text-right">
                      {item.count} ({pct}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}

function CaseManagerView() {
  const token = useAdvisorToken();
  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-primary">
            Case Manager Dashboard
          </h1>
          <p className="text-muted-foreground">
            Aggregate metrics from MontGoWork assessments
          </p>
        </div>
        {token && <NeedsAttentionSection token={token} />}
        <DashboardStats />
      </div>
    </main>
  );
}

export default function CaseManagerPage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <CaseManagerView />
      </TranslationProvider>
    </Suspense>
  );
}
