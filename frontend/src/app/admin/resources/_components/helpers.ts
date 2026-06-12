/**
 * Helpers for the /admin/resources page (T26.8).
 *
 * Kept in a separate module so the page composes from small,
 * individually testable pieces and stays under the architecture
 * file/function limits.
 */

export const PAGE_SIZE = 50;
export const ALL = "__all__";

export const SELECT_CLASS =
  "w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring";

export interface FilterState {
  city: string;
  category: string;
  includeHidden: boolean;
  offset: number;
}

export interface ListOptsWithCategory {
  city?: string;
  category?: string;
  includeHidden?: boolean;
  limit?: number;
  offset?: number;
}

export function formatLastEdited(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

export function badgeVariant(status: string): BadgeVariant {
  switch (status) {
    case "healthy":
      return "default";
    case "watch":
      return "secondary";
    case "flagged":
      return "destructive";
    case "hidden":
      return "outline";
    default:
      return "outline";
  }
}

export function buildListOpts(filters: FilterState): ListOptsWithCategory {
  return {
    city: filters.city === ALL ? undefined : filters.city,
    category: filters.category === ALL ? undefined : filters.category,
    includeHidden: filters.includeHidden,
    limit: PAGE_SIZE,
    offset: filters.offset,
  };
}
