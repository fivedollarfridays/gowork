"use client";

/**
 * <RoleAwareNav /> — role-gated reviewer/admin links (T23.8).
 *
 * Renders supplemental nav links that should ONLY appear for accounts
 * holding reviewer or admin roles. Sits alongside the always-public
 * ``<NavBar>`` rather than replacing it: the public nav surface
 * remains identical for anonymous browsers, and reviewers/admins see
 * extra entry points (Reviewer Dashboard, Admin Tools).
 *
 * Visibility rules (must mirror the backend ``any_of_roles`` gates):
 *   - "Reviewer Dashboard" (/admin/assessments) — any of {admin,
 *     case_manager, sme_reviewer, dao_reviewer}
 *   - "Admin Tools" (/admin/qc) — admin only
 *
 * As with ``<RoleGate>``, this is a UX layer only. The authoritative
 * gate remains the server-side ``require_role`` / ``any_of_roles``
 * dependencies on the routes themselves; hiding a link does not
 * protect the data behind it.
 */

import Link from "next/link";
import { useAccountRoles } from "@/lib/api/auth";

const REVIEWER_ROLES = [
  "admin",
  "case_manager",
  "sme_reviewer",
  "dao_reviewer",
] as const;

function _hasAnyRole(held: readonly string[], required: readonly string[]): boolean {
  for (const role of required) {
    if (held.includes(role)) return true;
  }
  return false;
}

export function RoleAwareNav() {
  const roles = useAccountRoles();
  const showReviewer = _hasAnyRole(roles, REVIEWER_ROLES);
  const showAdmin = roles.includes("admin");

  if (!showReviewer && !showAdmin) return null;

  return (
    <nav aria-label="Reviewer tools" className="flex items-center gap-3 text-sm">
      {showReviewer ? (
        <Link
          href="/admin/assessments"
          className="font-medium text-primary hover:underline"
        >
          Reviewer Dashboard
        </Link>
      ) : null}
      {showAdmin ? (
        <Link
          href="/admin/qc"
          className="font-medium text-primary hover:underline"
        >
          Admin Tools
        </Link>
      ) : null}
    </nav>
  );
}
