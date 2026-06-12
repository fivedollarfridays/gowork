"use client";

/**
 * /admin landing page (T26.11, Sprint 26 Wave 4).
 *
 * Operator entry point for the admin surface. Replaces direct URL
 * navigation across the S23-S26 admin pages with:
 *
 *   1. A quick-stats row with four count badges sourced from the
 *      existing typed API clients (no new backend routes — T26.11 is a
 *      composition of T26.6 admin_feedback + S24 listing_claims +
 *      S23 assessments clients).
 *   2. Six section cards (Assessments, Listings, Cities/DFW,
 *      Resources, Feedback, BrightData), each a Next ``<Link>`` to the
 *      already-shipped sub-page so internal navigation stays
 *      client-side and the back/forward stack stays clean.
 *
 * Auth guard
 * ----------
 * The shared :file:`frontend/src/app/admin/layout.tsx` already wraps
 * every ``/admin/*`` page in a broader reviewer-role gate. This page
 * narrows it with a strict ``<RoleGate roles={["admin"]}>`` so
 * non-admin reviewers see "Permission denied" instead of an empty
 * dashboard; authoritative role enforcement remains on the backend
 * (``require_role("admin")`` on every endpoint that feeds the badges).
 *
 * Resilience invariant
 * --------------------
 * The four count badges each live in their own ``useQuery``. A single
 * failing endpoint must NOT block the page render — the failed badge
 * shows ``—`` and the other three keep their counts. ``retry: false``
 * keeps a partial outage cheap.
 *
 * Charter integrity
 * -----------------
 * Display-only. No imports from ``backend/app/modules/matching/``
 * (S25 carryforward; T26.12 re-asserts at the gate via
 * ``test_charter_integrity_dallas.py``).
 */

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RoleGate } from "@/components/auth/RoleGate";
import {
  listFlagged,
  listVisits,
  type FlaggedResourcesResponse,
  type VisitFeedbackListResponse,
} from "@/lib/api/admin_feedback";
import {
  listPendingClaims,
  type PendingClaim,
} from "@/lib/api/listing_claims";
import {
  listPendingAssessments,
  type PendingAssessment,
} from "@/lib/api/assessments";

const STRICT_ADMIN_ROLES = ["admin"] as const;

/* -------------------------------------------------------------------------
 * Defaults — keep in sync with the sibling pages.
 * ------------------------------------------------------------------------- */

// `/admin/feedback`'s FlaggedResourcesTab defaults to "fort-worth" too;
// keep the landing-page probe aligned so the badge matches the count
// the operator sees once they click through.
const DEFAULT_CITY = "fort-worth";

// We only need the `total` count, not the rows. Probe with limit=1 to
// keep the wire payload minimal.
const VISIT_PROBE_LIMIT = 1;

/* -------------------------------------------------------------------------
 * Section-card descriptors — single source of truth for the 6 admin
 * sub-areas. Adding a new admin surface in a future sprint = one entry
 * here + one new sub-page.
 * ------------------------------------------------------------------------- */

interface SectionDescriptor {
  testId: string;
  title: string;
  href: string;
  description: string;
  /**
   * Which quick-stats badge (if any) belongs to this section. Used to
   * surface the count in the section card so the operator sees both
   * the queue depth at the top and per-card.
   */
  badgeKey?: BadgeKey;
}

type BadgeKey =
  | "flaggedResources"
  | "unreviewedVisits"
  | "pendingClaims"
  | "pendingAssessments";

const SECTIONS: ReadonlyArray<SectionDescriptor> = [
  {
    testId: "section-card-assessments",
    title: "Assessments",
    href: "/admin/assessments",
    description: "Review and publish track assessments.",
    badgeKey: "pendingAssessments",
  },
  {
    testId: "section-card-listings",
    title: "Listings",
    href: "/admin/listings",
    description: "Approve employer claim requests and verify intake.",
    badgeKey: "pendingClaims",
  },
  {
    testId: "section-card-cities-dfw",
    title: "Cities / DFW",
    href: "/admin/cities/dfw",
    description: "Read-only metro diagnostic across DFW cities.",
  },
  {
    testId: "section-card-resources",
    title: "Resources",
    href: "/admin/resources",
    description: "Curate community resources (add, edit, hide, restore).",
  },
  {
    testId: "section-card-feedback",
    title: "Feedback",
    href: "/admin/feedback",
    description: "Triage flagged resources and visit feedback.",
    badgeKey: "flaggedResources",
  },
  {
    testId: "section-card-brightdata",
    title: "BrightData",
    href: "/admin/brightdata",
    description: "Trigger and monitor BrightData scrapes.",
  },
];

/* -------------------------------------------------------------------------
 * Quick-stats — one ``useQuery`` per badge so partial outages don't
 * block the page. Each query returns either the integer count or
 * ``null`` (failure) → the badge renders ``—``.
 * ------------------------------------------------------------------------- */

interface BadgeState {
  loading: boolean;
  count: number | null;
}

function useBadge<T>(
  key: BadgeKey,
  queryFn: () => Promise<T>,
  pickCount: (data: T) => number,
): BadgeState {
  const q = useQuery<T>({
    queryKey: ["admin", "landing", "quick-stat", key],
    queryFn,
    retry: false,
    staleTime: 30_000,
  });
  if (q.isLoading) return { loading: true, count: null };
  if (q.isError || !q.data) return { loading: false, count: null };
  return { loading: false, count: pickCount(q.data) };
}

function useBadges(): Record<BadgeKey, BadgeState> {
  const flaggedResources = useBadge<FlaggedResourcesResponse>(
    "flaggedResources",
    () => listFlagged(DEFAULT_CITY),
    (d) => d.items.length,
  );
  const unreviewedVisits = useBadge<VisitFeedbackListResponse>(
    "unreviewedVisits",
    () => listVisits({ reviewed: false, limit: VISIT_PROBE_LIMIT }),
    (d) => d.total,
  );
  const pendingClaims = useBadge<PendingClaim[]>(
    "pendingClaims",
    () => listPendingClaims(),
    (d) => d.length,
  );
  const pendingAssessments = useBadge<PendingAssessment[]>(
    "pendingAssessments",
    () => listPendingAssessments(),
    (d) => d.length,
  );
  return {
    flaggedResources,
    unreviewedVisits,
    pendingClaims,
    pendingAssessments,
  };
}

/* -------------------------------------------------------------------------
 * Presentation helpers.
 * ------------------------------------------------------------------------- */

function _formatBadge(state: BadgeState): string {
  if (state.loading) return "…";
  if (state.count === null) return "—";
  return String(state.count);
}

function _QuickStatCard({
  testId,
  label,
  state,
}: {
  testId: string;
  label: string;
  state: BadgeState;
}) {
  return (
    <Card data-testid={testId}>
      <CardContent className="py-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <p className="mt-1 text-2xl font-mono font-semibold">
          {_formatBadge(state)}
        </p>
      </CardContent>
    </Card>
  );
}

function _QuickStatsRow({
  badges,
}: {
  badges: Record<BadgeKey, BadgeState>;
}) {
  return (
    <section
      aria-label="Quick stats"
      className="grid grid-cols-2 gap-3 md:grid-cols-4"
    >
      <_QuickStatCard
        testId="quick-stat-flagged-resources"
        label="Flagged resources"
        state={badges.flaggedResources}
      />
      <_QuickStatCard
        testId="quick-stat-unreviewed-visits"
        label="Unreviewed visit feedback"
        state={badges.unreviewedVisits}
      />
      <_QuickStatCard
        testId="quick-stat-pending-claims"
        label="Pending claims"
        state={badges.pendingClaims}
      />
      <_QuickStatCard
        testId="quick-stat-pending-assessments"
        label="Pending assessments"
        state={badges.pendingAssessments}
      />
    </section>
  );
}

function _SectionCard({
  section,
  badge,
}: {
  section: SectionDescriptor;
  badge: BadgeState | null;
}) {
  return (
    <Card data-testid={section.testId}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-lg">
          <span>{section.title}</span>
          {badge !== null && (
            <span
              className="ml-2 rounded-md border border-border px-2 py-0.5 text-xs font-mono text-muted-foreground"
              data-testid={`${section.testId}-badge`}
            >
              {_formatBadge(badge)}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{section.description}</p>
        <Link
          href={section.href}
          className="inline-block text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          Open {section.title} &rarr;
        </Link>
      </CardContent>
    </Card>
  );
}

function _SectionsGrid({
  badges,
}: {
  badges: Record<BadgeKey, BadgeState>;
}) {
  return (
    <section
      aria-label="Admin sections"
      className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
    >
      {SECTIONS.map((section) => {
        const badge = section.badgeKey ? badges[section.badgeKey] : null;
        return (
          <_SectionCard key={section.testId} section={section} badge={badge} />
        );
      })}
    </section>
  );
}

function AdminLandingInner() {
  const badges = useBadges();
  return (
    <main className="min-h-screen px-4 py-8 max-w-6xl mx-auto space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">Admin</h1>
        <p className="text-sm text-muted-foreground">
          Operator dashboard — quick stats + jump-off to the S23-S26 admin
          surfaces.
        </p>
      </header>

      <_QuickStatsRow badges={badges} />
      <_SectionsGrid badges={badges} />
    </main>
  );
}

export default function AdminLandingPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <AdminLandingInner />
    </RoleGate>
  );
}
