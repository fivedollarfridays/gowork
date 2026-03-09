"use client";

import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { defaultFilters, SOURCE_LABELS, SCHEDULE_LABELS, type JobFilterState } from "@/lib/jobFilters";

interface JobFilterPillsProps {
  filters: JobFilterState;
  onClear: (filters: JobFilterState) => void;
}

export function JobFilterPills({ filters, onClear }: JobFilterPillsProps) {
  const pills: { key: keyof JobFilterState; label: string }[] = [];

  if (filters.source !== "all") {
    pills.push({ key: "source", label: SOURCE_LABELS[filters.source] ?? filters.source });
  }
  if (filters.fairChanceOnly) {
    pills.push({ key: "fairChanceOnly", label: "Fair-chance" });
  }
  if (filters.schedule !== "all") {
    pills.push({ key: "schedule", label: SCHEDULE_LABELS[filters.schedule] ?? filters.schedule });
  }

  if (pills.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {pills.map((pill) => (
        <Badge key={pill.key} variant="secondary" className="gap-1 pr-1">
          {pill.label}
          <button
            type="button"
            aria-label={`Remove ${pill.label} filter`}
            onClick={() =>
              onClear({ ...filters, [pill.key]: defaultFilters[pill.key] })
            }
            className="ml-1 rounded-full p-0.5 hover:bg-muted"
          >
            <X className="h-3 w-3" />
          </button>
        </Badge>
      ))}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onClear(defaultFilters)}
        className="h-6 px-2 text-xs"
      >
        Clear all
      </Button>
    </div>
  );
}
