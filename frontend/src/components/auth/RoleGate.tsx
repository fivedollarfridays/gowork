"use client";

/**
 * <RoleGate roles={[...]}> — declarative client-side role gate (T23.8).
 *
 * Renders ``children`` iff the current account (per ``useAccount``)
 * holds AT LEAST ONE of the listed roles. Otherwise renders one of
 * three documented states:
 *
 *   - loading  → neutral "Checking access..." placeholder. Children
 *                are NOT mounted yet, which is important: child trees
 *                may kick off authenticated queries on mount and we
 *                don't want anonymous browsers firing those before the
 *                ``/api/auth/me`` round-trip resolves.
 *   - denied   → "Permission denied" card with a sign-in link. Children
 *                are not mounted (same rationale).
 *   - allowed  → children render unchanged.
 *
 * Mirrors the backend's ``any_of_roles`` dependency in
 * ``app.core.auth_roles`` so the client-side check cannot drift from
 * server-side enforcement. Authoritative role checks remain on the
 * server — this gate only avoids rendering surfaces a user couldn't
 * action anyway.
 */

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { useAccount, useAccountRoles } from "@/lib/api/auth";

export interface RoleGateProps {
  /** OR-list of roles; the gate passes when the account holds any one. */
  roles: readonly string[];
  /** Content to render when access is granted. */
  children: React.ReactNode;
}

function _hasAnyRole(held: readonly string[], required: readonly string[]): boolean {
  for (const role of required) {
    if (held.includes(role)) return true;
  }
  return false;
}

function _LoadingState() {
  return (
    <main className="min-h-[40vh] flex items-center justify-center px-4">
      <p className="text-sm text-muted-foreground" role="status">
        Checking access...
      </p>
    </main>
  );
}

function _DeniedState() {
  return (
    <main className="min-h-[40vh] flex items-center justify-center px-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-6 space-y-3">
          <p className="text-lg font-semibold">Permission denied</p>
          <p className="text-sm text-muted-foreground">
            Your account does not have the role required to view this page.
            If you believe this is a mistake, contact an administrator or{" "}
            <Link href="/auth/login" className="underline">
              sign in
            </Link>{" "}
            with a different account.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

export function RoleGate({ roles, children }: RoleGateProps) {
  const account = useAccount();
  const heldRoles = useAccountRoles();

  if (account.isLoading) return <_LoadingState />;
  if (!_hasAnyRole(heldRoles, roles)) return <_DeniedState />;
  return <>{children}</>;
}
