"use client";

/**
 * /admin/feedback — tabbed admin queue (T26.9, Sprint 26 Wave 3).
 *
 * Two tabs (shadcn ``Tabs``):
 *   - "Flagged Resources" (default) — flagged-resource queue with
 *     Approve / Confirm Hide row actions.
 *   - "Visit Feedback" — visit-feedback inbox table with Mark Reviewed
 *     row action.
 *
 * URL hash sync: ``#flagged`` / ``#visits`` selects the matching tab on
 * mount so deep links activate the right surface. Switching tabs via
 * the trigger writes the hash back so the URL stays shareable. We use
 * ``replaceState`` (not push) to avoid polluting the browser history
 * with intra-page tab toggles.
 *
 * Auth guard:
 *   The shared :file:`frontend/src/app/admin/layout.tsx` already wraps
 *   every ``/admin/*`` page in a broader reviewer-role gate (admin /
 *   case_manager / sme_reviewer / dao_reviewer). This page narrows the
 *   gate to admin-only via a stricter ``<RoleGate roles={["admin"]}>``
 *   wrap so non-admin reviewers see "Permission denied" instead of an
 *   empty queue. Authoritative role enforcement lives on the backend
 *   (require_role("admin") on every ``/api/admin/feedback/*`` route).
 *
 * Tab bodies live in :file:`components/admin/FeedbackTabs.tsx` so each
 * can be unit-tested without going through the radix Tabs data-state
 * dance.
 */

import { useEffect, useState } from "react";

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { RoleGate } from "@/components/auth/RoleGate";
import {
  FlaggedResourcesTab,
  VisitFeedbackTab,
} from "@/components/admin/FeedbackTabs";

const STRICT_ADMIN_ROLES = ["admin"] as const;

const TAB_FLAGGED = "flagged";
const TAB_VISITS = "visits";
type TabValue = typeof TAB_FLAGGED | typeof TAB_VISITS;

function _hashToTab(hash: string): TabValue {
  const cleaned = hash.replace(/^#/, "");
  return cleaned === TAB_VISITS ? TAB_VISITS : TAB_FLAGGED;
}

function _initialTab(): TabValue {
  if (typeof window === "undefined") return TAB_FLAGGED;
  return _hashToTab(window.location.hash);
}

function FeedbackPageInner() {
  const [tab, setTab] = useState<TabValue>(_initialTab);

  // Sync hash on mount (covers SSR → first client paint where useState
  // ran before window was available) and on hashchange (covers
  // back/forward + manual edit in the address bar).
  useEffect(() => {
    setTab(_hashToTab(window.location.hash));
    const onHash = () => setTab(_hashToTab(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const handleTabChange = (next: string) => {
    const value = next === TAB_VISITS ? TAB_VISITS : TAB_FLAGGED;
    setTab(value);
    if (typeof window !== "undefined") {
      // replaceState (not pushState) — intra-page tab toggles should
      // not pollute the browser history stack.
      const url = `${window.location.pathname}${window.location.search}#${value}`;
      window.history.replaceState(null, "", url);
    }
  };

  return (
    <main className="min-h-screen px-4 py-8 max-w-5xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">Feedback</h1>
        <p className="text-sm text-muted-foreground">
          Flagged community resources and visit feedback from the field.
        </p>
      </header>

      <Tabs value={tab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value={TAB_FLAGGED}>Flagged Resources</TabsTrigger>
          <TabsTrigger value={TAB_VISITS}>Visit Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value={TAB_FLAGGED}>
          <FlaggedResourcesTab />
        </TabsContent>

        <TabsContent value={TAB_VISITS}>
          <VisitFeedbackTab />
        </TabsContent>
      </Tabs>
    </main>
  );
}

export default function AdminFeedbackPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <FeedbackPageInner />
    </RoleGate>
  );
}
