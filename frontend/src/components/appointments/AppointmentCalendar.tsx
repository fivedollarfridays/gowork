"use client";

import { useMemo } from "react";
import { Calendar, dateFnsLocalizer, Views } from "react-big-calendar";
import { format, parse, startOfWeek, getDay } from "date-fns";
import { enUS } from "date-fns/locale";
import "react-big-calendar/lib/css/react-big-calendar.css";

import type { Appointment } from "@/lib/api/appointments";

interface AppointmentCalendarProps {
  appointments: Appointment[];
  onSelectAppointment: (appointment: Appointment) => void;
}

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  resource: Appointment;
}

const locales = { "en-US": enUS };

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date()),
  getDay,
  locales,
});

/**
 * Month-view wrapper around react-big-calendar. Converts appointments that
 * have a concrete starts_at into calendar events. Appointments without dates
 * are filtered out (the page surfaces them via PlaceholderPrompt).
 */
export function AppointmentCalendar({
  appointments,
  onSelectAppointment,
}: AppointmentCalendarProps) {
  const events: CalendarEvent[] = useMemo(() => {
    return appointments
      .filter((a) => a.starts_at)
      .map((a) => {
        const start = new Date(a.starts_at as string);
        const end = a.ends_at
          ? new Date(a.ends_at)
          : new Date(start.getTime() + 60 * 60 * 1000);
        return { id: a.id, title: a.title, start, end, resource: a };
      });
  }, [appointments]);

  return (
    <div className="rounded-lg border border-border bg-background p-2">
      <Calendar
        localizer={localizer}
        events={events}
        views={[Views.MONTH, Views.WEEK, Views.DAY, Views.AGENDA]}
        defaultView={Views.MONTH}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 600 }}
        onSelectEvent={(ev) =>
          onSelectAppointment((ev as CalendarEvent).resource)
        }
      />
    </div>
  );
}
