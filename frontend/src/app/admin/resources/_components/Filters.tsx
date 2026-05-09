"use client";

/**
 * Filter row for /admin/resources: city / category dropdowns and
 * "Show hidden" toggle. State is owned by the parent page; this
 * component is purely presentational.
 */

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  RESOURCE_CITIES,
  RESOURCE_CATEGORIES,
} from "@/components/admin/ResourceForm";

import { ALL, SELECT_CLASS, type FilterState } from "./helpers";

export function Filters({
  filters,
  onChange,
}: {
  filters: FilterState;
  onChange: (next: FilterState) => void;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Filters</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="space-y-2">
          <label htmlFor="filter-city" className="text-sm font-medium">
            City
          </label>
          <select
            id="filter-city"
            value={filters.city}
            onChange={(e) =>
              onChange({ ...filters, city: e.target.value, offset: 0 })
            }
            className={SELECT_CLASS}
          >
            <option value={ALL}>All</option>
            {RESOURCE_CITIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label htmlFor="filter-category" className="text-sm font-medium">
            Category
          </label>
          <select
            id="filter-category"
            value={filters.category}
            onChange={(e) =>
              onChange({ ...filters, category: e.target.value, offset: 0 })
            }
            className={SELECT_CLASS}
          >
            <option value={ALL}>All</option>
            {RESOURCE_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label htmlFor="filter-hidden" className="text-sm font-medium">
            Show hidden
          </label>
          <input
            id="filter-hidden"
            type="checkbox"
            checked={filters.includeHidden}
            onChange={(e) =>
              onChange({
                ...filters,
                includeHidden: e.target.checked,
                offset: 0,
              })
            }
            className="h-5 w-5 align-middle"
          />
        </div>
      </CardContent>
    </Card>
  );
}
