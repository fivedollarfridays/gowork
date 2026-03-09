"use client";

import { Checkbox } from "@/components/ui/checkbox";
import {
  activeFilterCount,
  SOURCE_LABELS,
  SCHEDULE_LABELS,
  type JobFilterState,
  type SortOption,
} from "@/lib/jobFilters";

const SOURCE_OPTIONS = [
  { value: "all", label: "All Sources" },
  ...Object.entries(SOURCE_LABELS).map(([value, label]) => ({ value, label })),
] as const;

const SCHEDULE_OPTIONS = [
  { value: "all", label: "All Schedules" },
  ...Object.entries(SCHEDULE_LABELS).map(([value, label]) => ({ value, label })),
] as const;

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "relevance", label: "Relevance" },
  { value: "pay", label: "Pay (High to Low)" },
];

interface JobFiltersProps {
  filters: JobFilterState;
  onChange: (filters: JobFilterState) => void;
  sort?: SortOption;
  onSortChange?: (sort: SortOption) => void;
}

export function JobFilters({ filters, onChange, sort = "relevance", onSortChange }: JobFiltersProps) {
  const count = activeFilterCount(filters);

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Filter Jobs</span>
        {count > 0 && (
          <span className="text-xs text-muted-foreground">{count} active</span>
        )}
      </div>
      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1">
          <label htmlFor="source-filter" className="text-xs text-muted-foreground">
            Source
          </label>
          <select
            id="source-filter"
            value={filters.source}
            onChange={(e) =>
              onChange({ ...filters, source: e.target.value as JobFilterState["source"] })
            }
            className="block w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
          >
            {SOURCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="schedule-filter" className="text-xs text-muted-foreground">
            Schedule
          </label>
          <select
            id="schedule-filter"
            value={filters.schedule}
            onChange={(e) =>
              onChange({ ...filters, schedule: e.target.value as JobFilterState["schedule"] })
            }
            className="block w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
          >
            {SCHEDULE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 pb-0.5">
          <Checkbox
            id="fair-chance-filter"
            checked={filters.fairChanceOnly}
            onCheckedChange={(checked) =>
              onChange({ ...filters, fairChanceOnly: checked === true })
            }
            aria-label="Fair-chance only"
          />
          <label htmlFor="fair-chance-filter" className="text-sm cursor-pointer">
            Fair-chance only
          </label>
        </div>

        {onSortChange && (
          <div className="space-y-1">
            <label htmlFor="sort-select" className="text-xs text-muted-foreground">
              Sort by
            </label>
            <select
              id="sort-select"
              value={sort}
              onChange={(e) => onSortChange(e.target.value as SortOption)}
              className="block w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
