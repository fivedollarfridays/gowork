/**
 * /admin layout — reviewer/admin role gate (T23.8).
 *
 * Wraps every page under ``/admin/*`` in a single ``<RoleGate>`` so
 * the per-page LOCAL_GUARD_T23_7 ``useEffect`` redirect introduced in
 * T23.7 is no longer needed. The four reviewer roles map 1:1 to the
 * backend's ``any_of_roles`` decoration on the assessments review +
 * publish endpoints, so client and server gating stay aligned.
 *
 * Layouts in the App Router are server components by default; the
 * ``<RoleGate>`` itself is a client component (it consumes
 * ``useAccount``), so the boundary lives inside the gate. Keeping the
 * layout lean (no ``"use client"`` here) lets the surrounding admin
 * shell remain server-rendered when we add it.
 */

import { RoleGate } from "@/components/auth/RoleGate";

const ADMIN_ROLES = [
  "admin",
  "case_manager",
  "sme_reviewer",
  "dao_reviewer",
] as const;

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RoleGate roles={ADMIN_ROLES}>{children}</RoleGate>;
}
