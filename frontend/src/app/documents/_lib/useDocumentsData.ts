"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listVersions, type DocumentVersion } from "@/lib/api/documents";

/**
 * Shared query hook for the documents pages. Returns the full newest-first
 * version list plus an invalidator that both the resume and cover-letter
 * pages call after a successful POST.
 */
export function useDocumentsData(
  sessionId: string | null,
  token: string | null,
) {
  const qc = useQueryClient();
  const enabled = Boolean(sessionId && token);

  const query = useQuery({
    queryKey: ["documents", "versions", sessionId, token],
    queryFn: () => listVersions(sessionId!, token!),
    enabled,
  });

  return {
    versions: (query.data ?? []) as DocumentVersion[],
    isLoading: query.isLoading,
    error: query.error as Error | null,
    invalidate: () =>
      qc.invalidateQueries({ queryKey: ["documents", "versions"] }),
  };
}
