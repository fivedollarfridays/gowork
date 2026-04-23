"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { useTranslation } from "@/hooks/useTranslation";
import type { Appointment } from "@/lib/api/appointments";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type AppointmentDraft = Partial<Appointment> & {
  session_id: string;
  type: string;
  title: string;
};

interface AppointmentEditModalProps {
  mode: "create" | "edit";
  initial: Partial<Appointment>;
  sessionId: string;
  onClose: () => void;
  onSubmit: (draft: AppointmentDraft) => void | Promise<void>;
}

const TYPE_OPTIONS = [
  { value: "interview", labelKey: "appointments.typeInterview" },
  { value: "appointment", labelKey: "appointments.typeAppointment" },
  { value: "training", labelKey: "appointments.typeTraining" },
  { value: "other", labelKey: "appointments.typeOther" },
];

function toDatetimeLocal(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return "";
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return "";
  }
}

function fromDatetimeLocal(local: string): string | null {
  if (!local) return null;
  const d = new Date(local);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export function AppointmentEditModal({
  mode,
  initial,
  sessionId,
  onClose,
  onSubmit,
}: AppointmentEditModalProps) {
  const { t } = useTranslation();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [type, setType] = useState(initial.type ?? "appointment");
  const [title, setTitle] = useState(initial.title ?? "");
  const [startsAt, setStartsAt] = useState(toDatetimeLocal(initial.starts_at));
  const [endsAt, setEndsAt] = useState(toDatetimeLocal(initial.ends_at));
  const [locationName, setLocationName] = useState(initial.location_name ?? "");
  const [locationAddress, setLocationAddress] = useState(
    initial.location_address ?? "",
  );
  const [notes, setNotes] = useState(initial.notes ?? "");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const el = dialogRef.current?.querySelector<HTMLElement>(
      "input, select, textarea, button",
    );
    el?.focus();
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError(t("appointments.errorTitleRequired"));
      return;
    }
    const startsIso = fromDatetimeLocal(startsAt);
    const endsIso = fromDatetimeLocal(endsAt);
    if (startsIso && endsIso && endsIso < startsIso) {
      setError(t("appointments.errorEndsBeforeStart"));
      return;
    }
    setError(null);

    const draft: AppointmentDraft = {
      ...initial,
      session_id: sessionId,
      type,
      title: title.trim(),
      starts_at: startsIso,
      ends_at: endsIso,
      location_name: locationName.trim() || null,
      location_address: locationAddress.trim() || null,
      notes: notes.trim() || null,
    };
    void onSubmit(draft);
  }

  const titleText =
    mode === "create"
      ? t("appointments.modalTitleCreate")
      : t("appointments.modalTitleEdit");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="appt-modal-title"
        className="w-full max-w-lg rounded-lg bg-background p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="appt-modal-title" className="text-lg font-semibold">
            {titleText}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("appointments.closeModal")}
            className="rounded p-1 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label htmlFor="appt-type" className="block text-sm font-medium">
              {t("appointments.fieldType")}
            </label>
            <select
              id="appt-type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {t(o.labelKey)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="appt-title" className="block text-sm font-medium">
              {t("appointments.fieldTitle")}
            </label>
            <Input
              id="appt-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label
                htmlFor="appt-starts"
                className="block text-sm font-medium"
              >
                {t("appointments.fieldStartsAt")}
              </label>
              <Input
                id="appt-starts"
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="appt-ends" className="block text-sm font-medium">
                {t("appointments.fieldEndsAt")}
              </label>
              <Input
                id="appt-ends"
                type="datetime-local"
                value={endsAt}
                onChange={(e) => setEndsAt(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label htmlFor="appt-loc" className="block text-sm font-medium">
              {t("appointments.fieldLocationName")}
            </label>
            <Input
              id="appt-loc"
              value={locationName}
              onChange={(e) => setLocationName(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="appt-addr" className="block text-sm font-medium">
              {t("appointments.fieldLocationAddress")}
            </label>
            <Input
              id="appt-addr"
              value={locationAddress}
              onChange={(e) => setLocationAddress(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="appt-notes" className="block text-sm font-medium">
              {t("appointments.fieldNotes")}
            </label>
            <textarea
              id="appt-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              {t("appointments.cancel")}
            </Button>
            <Button type="submit">{t("appointments.save")}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
