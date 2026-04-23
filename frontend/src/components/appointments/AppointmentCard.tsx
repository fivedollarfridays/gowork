"use client";

import { Briefcase, Calendar, Clock, MapPin } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import type { Appointment, AppointmentStatus } from "@/lib/api/appointments";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface AppointmentCardProps {
  appointment: Appointment;
  onEdit: (appointment: Appointment) => void;
  onAttended: (appointment: Appointment) => void;
  onMissed: (appointment: Appointment) => void;
  onCancel: (appointment: Appointment) => void;
}

const STATUS_KEY: Record<AppointmentStatus, string> = {
  scheduled: "appointments.statusScheduled",
  attended: "appointments.statusAttended",
  missed: "appointments.statusMissed",
  cancelled: "appointments.statusCancelled",
  rescheduled: "appointments.statusRescheduled",
};

const STATUS_CLS: Record<AppointmentStatus, string> = {
  scheduled: "bg-primary/10 text-primary",
  attended: "bg-success text-success-foreground",
  missed: "bg-destructive text-destructive-foreground",
  cancelled: "bg-muted text-muted-foreground",
  rescheduled: "bg-warning text-warning-foreground",
};

function formatWhen(starts: string | null, ends: string | null): string {
  if (!starts) return "";
  try {
    const s = new Date(starts);
    const datePart = s.toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
    const timePart = s.toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    });
    if (ends) {
      const e = new Date(ends);
      const endTime = e.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
      });
      return `${datePart}, ${timePart} - ${endTime}`;
    }
    return `${datePart}, ${timePart}`;
  } catch {
    return starts;
  }
}

/**
 * Visual card for a single appointment. Shows title, when/where, status badge,
 * and action buttons that depend on current status.
 */
export function AppointmentCard({
  appointment,
  onEdit,
  onAttended,
  onMissed,
  onCancel,
}: AppointmentCardProps) {
  const { t } = useTranslation();
  const a = appointment;
  const isScheduled = a.status === "scheduled";
  const when = formatWhen(a.starts_at, a.ends_at);

  return (
    <Card className="p-0">
      <CardContent className="p-4">
        <button
          type="button"
          className="group block w-full rounded text-left outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={`Edit appointment: ${a.title}`}
          onClick={() => onEdit(a)}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-base font-semibold text-foreground group-hover:underline">
                {a.title}
              </h3>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <Briefcase className="h-3 w-3" aria-hidden="true" />
                  {a.type}
                </span>
                {when ? (
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="h-3 w-3" aria-hidden="true" />
                    {when}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 italic">
                    <Clock className="h-3 w-3" aria-hidden="true" />
                    {t("appointments.cardNoDate")}
                  </span>
                )}
                {a.location_name && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3 w-3" aria-hidden="true" />
                    {a.location_name}
                  </span>
                )}
              </div>
            </div>
            <span
              className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLS[a.status]}`}
              aria-label={`Status: ${t(STATUS_KEY[a.status])}`}
            >
              {t(STATUS_KEY[a.status])}
            </span>
          </div>
        </button>

        {isScheduled && (
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="default"
              onClick={() => onAttended(a)}
              aria-label={`${t("appointments.cardAttended")}: ${a.title}`}
            >
              {t("appointments.cardAttended")}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onMissed(a)}
              aria-label={`${t("appointments.cardMissed")}: ${a.title}`}
            >
              {t("appointments.cardMissed")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onEdit(a)}
              aria-label={`${t("appointments.cardReschedule")}: ${a.title}`}
            >
              {t("appointments.cardReschedule")}
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onCancel(a)}
              aria-label={`${t("appointments.cardCancel")}: ${a.title}`}
            >
              {t("appointments.cardCancel")}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
