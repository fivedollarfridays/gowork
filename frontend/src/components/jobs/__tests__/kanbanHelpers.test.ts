import { describe, it, expect } from "vitest";
import type { JobApplication } from "@/lib/api/jobApplications";
import {
  STATUS_COLUMNS,
  groupByStatus,
  indexVersionsById,
  parseDraggableApplicationId,
  parseDroppableStatus,
} from "../kanbanHelpers";

function app(id: number, status: JobApplication["status"]): JobApplication {
  return {
    id,
    session_id: "sess-1",
    match_source: "twc",
    match_url: "https://example.com/" + id,
    company: "Acme",
    role: "Role",
    resume_version_id: null,
    status,
    applied_date: null,
    created_at: null,
  };
}

describe("kanbanHelpers: STATUS_COLUMNS", () => {
  it("contains all six JobApplicationStatus values in lifecycle order", () => {
    expect(STATUS_COLUMNS).toEqual([
      "draft",
      "applied",
      "interview",
      "offer",
      "rejected",
      "withdrawn",
    ]);
  });
});

describe("kanbanHelpers: groupByStatus", () => {
  it("returns an entry for every status even when some are empty", () => {
    const grouped = groupByStatus([app(1, "applied")]);
    expect(Object.keys(grouped).sort()).toEqual(
      [...STATUS_COLUMNS].sort(),
    );
    expect(grouped.applied).toHaveLength(1);
    expect(grouped.draft).toHaveLength(0);
  });

  it("assigns each application to the column matching its status", () => {
    const grouped = groupByStatus([
      app(1, "draft"),
      app(2, "applied"),
      app(3, "applied"),
      app(4, "offer"),
    ]);
    expect(grouped.draft.map((a) => a.id)).toEqual([1]);
    expect(grouped.applied.map((a) => a.id)).toEqual([2, 3]);
    expect(grouped.offer.map((a) => a.id)).toEqual([4]);
  });
});

describe("kanbanHelpers: parseDroppableStatus", () => {
  it("extracts status from a valid column drop id", () => {
    expect(parseDroppableStatus("column-applied")).toBe("applied");
    expect(parseDroppableStatus("column-offer")).toBe("offer");
  });

  it("returns null for unknown or malformed ids", () => {
    expect(parseDroppableStatus(null)).toBeNull();
    expect(parseDroppableStatus(undefined)).toBeNull();
    expect(parseDroppableStatus("application-5")).toBeNull();
    expect(parseDroppableStatus("column-garbage")).toBeNull();
    expect(parseDroppableStatus(42)).toBeNull();
  });
});

describe("kanbanHelpers: parseDraggableApplicationId", () => {
  it("extracts numeric id from a valid application drag id", () => {
    expect(parseDraggableApplicationId("application-7")).toBe(7);
  });

  it("returns null for non-application ids or non-numeric tails", () => {
    expect(parseDraggableApplicationId(null)).toBeNull();
    expect(parseDraggableApplicationId("column-draft")).toBeNull();
    expect(parseDraggableApplicationId("application-abc")).toBeNull();
  });
});

describe("kanbanHelpers: indexVersionsById", () => {
  it("returns empty map for undefined input", () => {
    expect(indexVersionsById(undefined).size).toBe(0);
  });

  it("maps version_id -> version object for fast lookup", () => {
    const versions = [
      {
        version_id: 10,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 1,
        generation_method: "llm",
        use_counter: 2,
        created_at: "",
      },
      {
        version_id: 11,
        session_id: "sess-1",
        doc_type: "resume",
        version_counter: 2,
        generation_method: "template",
        use_counter: 0,
        created_at: "",
      },
    ];
    const map = indexVersionsById(versions);
    expect(map.get(10)?.generation_method).toBe("llm");
    expect(map.get(11)?.generation_method).toBe("template");
    expect(map.get(99)).toBeUndefined();
  });
});
