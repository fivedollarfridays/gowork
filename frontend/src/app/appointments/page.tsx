"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { TranslationProvider, useTranslation } from "@/hooks/useTranslation";
import { useSessionId, useToken } from "@/app/plan/hooks";
import {
  type Appointment,
  listAppointments,
  listUpcoming,
  createAppointment,
  updateAppointment,
  markAttended,
  markMissed,
  cancelAppointment,
} from "@/lib/api/appointments";
import { AppointmentCalendar } from "@/components/appointments/AppointmentCalendar";
import { AppointmentCard } from "@/components/appointments/AppointmentCard";
import {
  AppointmentEditModal,
  type AppointmentDraft,
} from "@/components/appointments/AppointmentEditModal";
import { PlaceholderPrompt } from "@/components/appointments/PlaceholderPrompt";

type ModalState =
  | { mode: "closed" }
  | { mode: "create"; initial: Partial<Appointment> }
  | { mode: "edit"; appointment: Appointment };

function AppointmentsContent() {
  const { t } = useTranslation();
  const { id: sessionId, ready: sessionReady } = useSessionId();
  const { token, ready: tokenReady } = useToken(sessionId);
  const qc = useQueryClient();

  const [modal, setModal] = useState<ModalState>({ mode: "closed" });

  const enabled = Boolean(sessionId && token);

  const all = useQuery({
    queryKey: ["appointments", "all", sessionId, token],
    queryFn: () => listAppointments(sessionId!, token!),
    enabled,
  });

  const upcoming = useQuery({
    queryKey: ["appointments", "upcoming", sessionId, token],
    queryFn: () => listUpcoming(sessionId!, 30, token!),
    enabled,
  });

  const invalidate = useCallback(() => {
    qc.invalidateQueries({ queryKey: ["appointments"] });
  }, [qc]);

  const createMut = useMutation({
    mutationFn: (draft: AppointmentDraft) =>
      createAppointment(draft, token ?? ""),
    onSuccess: () => {
      invalidate();
      setModal({ mode: "closed" });
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, changes }: { id: number; changes: Partial<Appointment> }) =>
      updateAppointment(id, changes, token ?? ""),
    onSuccess: () => {
      invalidate();
      setModal({ mode: "closed" });
    },
  });

  const attendedMut = useMutation({
    mutationFn: (id: number) => markAttended(id, token ?? ""),
    onSuccess: invalidate,
  });

  const missedMut = useMutation({
    mutationFn: (id: number) => markMissed(id, token ?? ""),
    onSuccess: invalidate,
  });

  const cancelMut = useMutation({
    mutationFn: (id: number) => cancelAppointment(id, token ?? ""),
    onSuccess: invalidate,
  });

  const appointments = useMemo(() => all.data ?? [], [all.data]);
  const upcomingItems = upcoming.data ?? [];
  const placeholders = useMemo(
    () =>
      appointments.filter(
        (a) => a.source === "pathway_auto" && !a.starts_at,
      ),
    [appointments],
  );

  const handleEdit = useCallback((a: Appointment) => {
    setModal({ mode: "edit", appointment: a });
  }, []);

  const handleSchedulePlaceholder = useCallback((a: Appointment) => {
    setModal({ mode: "edit", appointment: a });
  }, []);

  const handleNewClick = useCallback(() => {
    setModal({ mode: "create", initial: { type: "appointment" } });
  }, []);

  const handleModalSubmit = useCallback(
    (draft: AppointmentDraft) => {
      if (modal.mode === "create") {
        createMut.mutate(draft);
      } else if (modal.mode === "edit") {
        const { id } = modal.appointment;
        const { session_id: _ignore, ...changes } = draft;
        void _ignore;
        updateMut.mutate({ id, changes });
      }
    },
    [modal, createMut, updateMut],
  );

  if (!sessionReady || !tokenReady) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <p className="text-muted-foreground">{t("appointments.loading")}</p>
      </main>
    );
  }

  if (!sessionId || !token) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-3xl font-bold text-primary">
            {t("appointments.title")}
          </h1>
          <p className="mt-4 text-muted-foreground">
            {t("appointments.missingSession")}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-primary">
              {t("appointments.title")}
            </h1>
            <p className="text-muted-foreground">
              {t("appointments.subtitle")}
            </p>
          </div>
          <Button onClick={handleNewClick}>
            {t("appointments.newAppointment")}
          </Button>
        </header>

        {placeholders.length > 0 && (
          <PlaceholderPrompt
            placeholders={placeholders}
            onSchedule={handleSchedulePlaceholder}
          />
        )}

        {all.isLoading && (
          <p className="text-muted-foreground">{t("appointments.loading")}</p>
        )}
        {all.error && (
          <p role="alert" className="text-destructive">
            {t("appointments.loadFailed")}
          </p>
        )}

        <Tabs defaultValue="calendar">
          <TabsList>
            <TabsTrigger value="calendar">
              {t("appointments.tabCalendar")}
            </TabsTrigger>
            <TabsTrigger value="list">
              {t("appointments.tabList")}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="calendar">
            <AppointmentCalendar
              appointments={appointments}
              onSelectAppointment={handleEdit}
            />
          </TabsContent>

          <TabsContent value="list">
            {upcomingItems.length === 0 ? (
              <p className="py-8 text-center text-muted-foreground">
                {t("appointments.emptyList")}
              </p>
            ) : (
              <ul className="space-y-3">
                {upcomingItems.map((a) => (
                  <li key={a.id}>
                    <AppointmentCard
                      appointment={a}
                      onEdit={handleEdit}
                      onAttended={(x) => attendedMut.mutate(x.id)}
                      onMissed={(x) => missedMut.mutate(x.id)}
                      onCancel={(x) => cancelMut.mutate(x.id)}
                    />
                  </li>
                ))}
              </ul>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {modal.mode === "create" && (
        <AppointmentEditModal
          mode="create"
          initial={modal.initial}
          sessionId={sessionId}
          onClose={() => setModal({ mode: "closed" })}
          onSubmit={handleModalSubmit}
        />
      )}
      {modal.mode === "edit" && (
        <AppointmentEditModal
          mode="edit"
          initial={modal.appointment}
          sessionId={sessionId}
          onClose={() => setModal({ mode: "closed" })}
          onSubmit={handleModalSubmit}
        />
      )}
    </main>
  );
}

export default function AppointmentsPage() {
  return (
    <Suspense fallback={null}>
      <TranslationProvider>
        <AppointmentsContent />
      </TranslationProvider>
    </Suspense>
  );
}
