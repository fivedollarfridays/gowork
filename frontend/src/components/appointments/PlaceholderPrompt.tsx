"use client";

import { useTranslation } from "@/hooks/useTranslation";
import type { Appointment } from "@/lib/api/appointments";
import { Button } from "@/components/ui/button";

interface PlaceholderPromptProps {
  placeholders: Appointment[];
  onSchedule: (appointment: Appointment) => void;
}

/**
 * Banner + list of pathway-generated appointments that are missing a date.
 * Each row surfaces a primary action that opens the edit modal pre-filled
 * with the placeholder so the worker can pick a date/time.
 */
export function PlaceholderPrompt({
  placeholders,
  onSchedule,
}: PlaceholderPromptProps) {
  const { t } = useTranslation();
  if (placeholders.length === 0) return null;

  return (
    <section
      role="region"
      aria-label={t("appointments.placeholderRegionLabel")}
      className="rounded-lg border border-warning/40 bg-warning/10 p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">
            <span aria-hidden="true">📅 </span>
            <span>{placeholders.length}</span>{" "}
            {t("appointments.placeholdersBanner")}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {t("appointments.placeholderHeading")}
          </p>
        </div>
      </div>

      <ul className="mt-3 divide-y divide-warning/30">
        {placeholders.map((p) => (
          <li
            key={p.id}
            className="flex items-center justify-between py-2"
          >
            <div className="min-w-0 flex-1 pr-3">
              <p className="truncate text-sm font-medium text-foreground">
                {p.title}
              </p>
              {p.barrier_link && (
                <p className="truncate text-xs text-muted-foreground">
                  {t("appointments.fieldBarrierLink")}: {p.barrier_link}
                </p>
              )}
            </div>
            <Button
              size="sm"
              variant="secondary"
              aria-label={`${t("appointments.placeholderCta")}: ${p.title}`}
              onClick={() => onSchedule(p)}
            >
              {t("appointments.placeholderCta")}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
