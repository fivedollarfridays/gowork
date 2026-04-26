/**
 * Typed API client for the MontGoWork daily digest preview endpoint (T12.21a).
 *
 * Accepts a `token` query parameter for auth. Backend validates the token
 * against the session referenced by `session_id`.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type DigestSectionCounts = {
  yesterday: number;
  today: number;
  week: number;
  stall: number;
};

export type DigestResult = {
  subject: string;
  html: string;
  text: string;
  section_counts: DigestSectionCounts;
};

/** Backend-produced section titles in plaintext output (fixed in digest_sections.py). */
const SECTION_TITLES = ["Yesterday", "Today", "This week", "Check-in"] as const;

export type ParsedDigestSections = {
  yesterday: string;
  today: string;
  week: string;
  stall: string;
};

/**
 * Split the backend's plaintext digest into per-section bodies.
 *
 * The backend emits each section as:
 *
 *     Yesterday
 *     <body lines...>
 *     (blank line)
 *     Today
 *     <body lines...>
 *     ...
 *
 * This returns a body string per section id, trimmed of leading/trailing blanks.
 * Missing sections return an empty string.
 */
export function parseDigestSections(text: string): ParsedDigestSections {
  const lines = text.split("\n");
  const sections: ParsedDigestSections = {
    yesterday: "",
    today: "",
    week: "",
    stall: "",
  };
  let current: keyof ParsedDigestSections | null = null;
  const buffers: Record<keyof ParsedDigestSections, string[]> = {
    yesterday: [],
    today: [],
    week: [],
    stall: [],
  };
  for (const line of lines) {
    const title = SECTION_TITLES.find((t) => t === line.trim());
    if (title) {
      current = titleToKey(title);
      continue;
    }
    if (current) buffers[current].push(line);
  }
  for (const key of Object.keys(buffers) as (keyof ParsedDigestSections)[]) {
    sections[key] = buffers[key].join("\n").trim();
  }
  return sections;
}

function titleToKey(title: (typeof SECTION_TITLES)[number]): keyof ParsedDigestSections {
  switch (title) {
    case "Yesterday":
      return "yesterday";
    case "Today":
      return "today";
    case "This week":
      return "week";
    case "Check-in":
      return "stall";
  }
}

function qs(params: Record<string, string>): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) search.set(k, v);
  return search.toString();
}

/**
 * Fetch the in-app preview of today's digest for a given session.
 *
 * Throws an Error whose message contains the HTTP status (e.g. "Unauthorized (401)"),
 * so UI code can branch on 401 vs 403/5xx.
 */
export async function previewDigest(
  sessionId: string,
  token: string,
  forDate?: string,
): Promise<DigestResult> {
  const params: Record<string, string> = {
    session_id: sessionId,
    token,
  };
  if (forDate) params.for_date = forDate;
  // T13.92 — 30s hard timeout so a stalled backend doesn't hang the
  // digest preview indefinitely.
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);
  let res: Response;
  try {
    res = await fetch(
      `${API_BASE}/api/engagement/preview-digest?${qs(params)}`,
      { signal: controller.signal },
    );
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    const body = await res
      .json()
      .catch(() => ({ detail: res.statusText }));
    const label = statusLabel(res.status);
    throw new Error(`${body.detail || label} (${res.status})`);
  }
  return (await res.json()) as DigestResult;
}

function statusLabel(status: number): string {
  if (status === 401) return "Unauthorized";
  if (status === 403) return "Forbidden";
  if (status === 400) return "Bad request";
  return "Server error";
}
