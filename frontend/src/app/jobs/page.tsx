"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { useSessionId, useToken } from "@/app/plan/hooks";
import {
  type JobApplication,
  type JobApplicationStatus,
  getFunnel,
  listApplications,
  listResumeVersions,
  updateApplicationStatus,
} from "@/lib/api/jobApplications";
import { JobCard } from "@/components/jobs/JobCard";
import { JobKanbanColumn } from "@/components/jobs/JobKanbanColumn";
import { FunnelStatsSidebar } from "@/components/jobs/FunnelStatsSidebar";
import {
  STATUS_COLUMNS,
  groupByStatus,
  indexVersionsById,
  parseDraggableApplicationId,
  parseDroppableStatus,
} from "@/components/jobs/kanbanHelpers";

function MoveMenu({
  application,
  onSelect,
  onClose,
}: {
  application: JobApplication;
  onSelect: (status: JobApplicationStatus) => void;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={t("jobs.moveMenuTitle")}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xs rounded-lg border bg-card p-4 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-3 text-sm font-semibold">
          {t("jobs.moveMenuTitle")}
        </h2>
        <ul className="space-y-1">
          {STATUS_COLUMNS.filter((s) => s !== application.status).map((s) => (
            <li key={s}>
              <button
                type="button"
                className="w-full rounded border border-input bg-background px-3 py-1.5 text-left text-xs hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                onClick={() => onSelect(s)}
              >
                {t(`jobs.column${s.charAt(0).toUpperCase() + s.slice(1)}`)}
              </button>
            </li>
          ))}
        </ul>
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            className="rounded border border-input bg-background px-3 py-1 text-xs text-muted-foreground hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
            onClick={onClose}
          >
            {t("jobs.moveCancel")}
          </button>
        </div>
      </div>
    </div>
  );
}

function JobsContent() {
  const { t } = useTranslation();
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);
  const qc = useQueryClient();

  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [moveTarget, setMoveTarget] = useState<JobApplication | null>(null);

  const enabled = Boolean(sessionId && token);

  const apps = useQuery({
    queryKey: ["jobApplications", "list", sessionId, token],
    queryFn: () => listApplications(sessionId!, token!),
    enabled,
  });

  const funnel = useQuery({
    queryKey: ["jobApplications", "funnel", sessionId, token],
    queryFn: () => getFunnel(sessionId!, token!),
    enabled,
  });

  const versions = useQuery({
    queryKey: ["jobApplications", "versions", sessionId, token],
    queryFn: () => listResumeVersions(sessionId!, token!),
    enabled,
  });

  const invalidate = useCallback(() => {
    qc.invalidateQueries({ queryKey: ["jobApplications"] });
  }, [qc]);

  const statusMut = useMutation({
    mutationFn: ({
      id,
      status,
    }: {
      id: number;
      status: JobApplicationStatus;
    }) => updateApplicationStatus(id, status, token ?? ""),
    onSuccess: () => {
      setTransitionError(null);
      invalidate();
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : String(err);
      setTransitionError(msg || t("jobs.transitionFailed"));
    },
  });

  const applications = useMemo(() => apps.data ?? [], [apps.data]);
  const grouped = useMemo(() => groupByStatus(applications), [applications]);
  const versionsById = useMemo(
    () => indexVersionsById(versions.data),
    [versions.data],
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor),
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const appId = parseDraggableApplicationId(event.active.id);
      const target = parseDroppableStatus(event.over?.id);
      if (appId == null || target == null) return;
      const app = applications.find((x) => x.id === appId);
      if (!app || app.status === target) return;
      statusMut.mutate({ id: appId, status: target });
    },
    [applications, statusMut],
  );

  const handleMove = useCallback(
    (app: JobApplication) => setMoveTarget(app),
    [],
  );

  const handleMenuSelect = useCallback(
    (status: JobApplicationStatus) => {
      if (!moveTarget) return;
      statusMut.mutate({ id: moveTarget.id, status });
      setMoveTarget(null);
    },
    [moveTarget, statusMut],
  );

  if (!sessionReady || !tokenReady) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("jobs.loading")}</p>
      </main>
    );
  }

  if (!sessionId || !token) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-3xl font-bold text-primary">
            {t("jobs.title")}
          </h1>
          <p className="mt-4 text-muted-foreground">
            {t("jobs.missingSession")}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-7xl space-y-4">
        <header>
          <h1 className="text-3xl font-bold text-primary">
            {t("jobs.title")}
          </h1>
          <p className="text-muted-foreground">{t("jobs.subtitle")}</p>
          <p className="mt-1 text-xs text-muted-foreground" id="dnd-instructions">
            {t("jobs.dragInstructions")}
          </p>
        </header>

        {apps.isLoading && (
          <p className="text-muted-foreground">{t("jobs.loading")}</p>
        )}
        {apps.error && (
          <p role="alert" className="text-destructive">
            {t("jobs.loadFailed")}
          </p>
        )}
        {transitionError && (
          <p role="alert" className="text-destructive">
            {t("jobs.transitionFailed")}
          </p>
        )}

        {!apps.isLoading && applications.length === 0 && (
          <p className="py-4 text-muted-foreground">{t("jobs.emptyBoard")}</p>
        )}

        <div className="flex flex-col gap-4 md:flex-row">
          <div className="flex-1">
            <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
              <div
                className="flex gap-3 overflow-x-auto pb-2"
                data-testid="kanban-board"
                aria-describedby="dnd-instructions"
              >
                {STATUS_COLUMNS.map((status) => (
                  <JobKanbanColumn
                    key={status}
                    status={status}
                    count={grouped[status].length}
                  >
                    {grouped[status].map((app) => {
                      const v =
                        app.resume_version_id != null
                          ? versionsById.get(app.resume_version_id)
                          : undefined;
                      return (
                        <div key={app.id} role="listitem">
                          <JobCard
                            application={app}
                            resumeGenerationMethod={v?.generation_method}
                            resumeVersionCounter={v?.version_counter}
                            onChangeStatus={handleMove}
                          />
                        </div>
                      );
                    })}
                  </JobKanbanColumn>
                ))}
              </div>
            </DndContext>
          </div>

          <FunnelStatsSidebar
            funnel={funnel.data}
            loading={funnel.isLoading}
          />
        </div>
      </div>

      {moveTarget && (
        <MoveMenu
          application={moveTarget}
          onSelect={handleMenuSelect}
          onClose={() => setMoveTarget(null)}
        />
      )}
    </main>
  );
}

export default function JobsPage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <JobsContent />
      </TranslationProvider>
    </Suspense>
  );
}
