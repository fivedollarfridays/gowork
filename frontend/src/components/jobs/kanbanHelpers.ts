import type {
  JobApplication,
  JobApplicationStatus,
  ResumeVersionInfo,
} from "@/lib/api/jobApplications";

/**
 * Column order — left-to-right along the lifecycle. Terminal states
 * (`rejected`, `withdrawn`) sit at the right-most edge.
 */
export const STATUS_COLUMNS: readonly JobApplicationStatus[] = [
  "draft",
  "applied",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
] as const;

/** Group applications by their current status. */
export function groupByStatus(
  applications: readonly JobApplication[],
): Record<JobApplicationStatus, JobApplication[]> {
  const initial = Object.fromEntries(
    STATUS_COLUMNS.map((s) => [s, [] as JobApplication[]]),
  ) as Record<JobApplicationStatus, JobApplication[]>;
  for (const app of applications) {
    initial[app.status]?.push(app);
  }
  return initial;
}

/**
 * Index resume versions by their version_id for O(1) lookup when
 * rendering generation-method badges.
 */
export function indexVersionsById(
  versions: readonly ResumeVersionInfo[] | undefined,
): Map<number, ResumeVersionInfo> {
  const map = new Map<number, ResumeVersionInfo>();
  if (!versions) return map;
  for (const v of versions) {
    map.set(v.version_id, v);
  }
  return map;
}

/**
 * Extract the target status from a dnd-kit droppable id. The column's
 * droppable id is always `column-{status}`; any other shape means the
 * drag ended outside the board.
 */
export function parseDroppableStatus(
  id: string | number | null | undefined,
): JobApplicationStatus | null {
  if (typeof id !== "string") return null;
  if (!id.startsWith("column-")) return null;
  const status = id.slice("column-".length);
  if ((STATUS_COLUMNS as readonly string[]).includes(status)) {
    return status as JobApplicationStatus;
  }
  return null;
}

/**
 * Extract the application id from a draggable id. Cards use
 * `application-{id}`. Returns null for malformed ids.
 */
export function parseDraggableApplicationId(
  id: string | number | null | undefined,
): number | null {
  if (typeof id !== "string") return null;
  if (!id.startsWith("application-")) return null;
  const n = Number(id.slice("application-".length));
  return Number.isFinite(n) ? n : null;
}
