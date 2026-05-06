"use client";

/**
 * /auth/claim — magic-link consumer surface (T22.10).
 *
 * Reads ``?token=`` from the URL, calls GET /api/auth/claim, and renders
 * a small state machine:
 *
 *   loading   → spinner (token present, request in flight)
 *   success   → "you're signed in" with link to dashboard
 *   invalid   → "invalid or expired" + CTA to request a new link
 *   conflict  → "session already linked to a different account"
 *   unknown   → generic "something went wrong"
 *
 * On success the backend sets the ``gw_account`` cookie via
 * ``Set-Cookie``; the page only needs to direct the user forward.
 */

import { useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { claimMagicLink, ClaimError, type ClaimSuccess } from "@/lib/api/auth";

export default function ClaimPage() {
  const params = useSearchParams();
  const token = params?.get("token") ?? "";

  const query = useQuery<ClaimSuccess, ClaimError>({
    queryKey: ["auth", "claim", token],
    queryFn: () => claimMagicLink(token),
    enabled: token.length > 0,
    retry: false,
    staleTime: Infinity,
  });

  // Mark the success state as observable so layout shifts settle before
  // any future redirect logic kicks in.
  useEffect(() => {
    if (query.data) {
      // Hook for future router.push("/dashboard") wiring once the
      // post-claim destination is settled. Intentionally a no-op here.
    }
  }, [query.data]);

  if (!token) return <_InvalidCard />;
  if (query.isLoading) return <_LoadingCard />;
  if (query.data) return <_SuccessCard data={query.data} />;
  if (query.error) {
    if (query.error.kind === "invalid") return <_InvalidCard />;
    if (query.error.kind === "conflict") return <_ConflictCard />;
    return <_GenericErrorCard />;
  }
  return <_LoadingCard />;
}

function _Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-6 space-y-4">{children}</CardContent>
      </Card>
    </main>
  );
}

function _LoadingCard() {
  return (
    <_Shell>
      <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary" aria-hidden />
      <p className="text-sm text-muted-foreground" role="status">
        Signing you in...
      </p>
    </_Shell>
  );
}

function _SuccessCard({ data }: { data: ClaimSuccess }) {
  const sessionCount = data.claimed_session_ids.length;
  return (
    <_Shell>
      <CheckCircle2 className="mx-auto h-10 w-10 text-primary" aria-hidden />
      <p className="text-lg font-semibold">You&apos;re signed in</p>
      <p className="text-sm text-muted-foreground">
        {sessionCount > 0
          ? `We linked ${sessionCount} previous ${sessionCount === 1 ? "session" : "sessions"} to your account.`
          : "Your account is ready to go."}
      </p>
      <Button asChild className="w-full min-h-11">
        <Link href="/">Continue</Link>
      </Button>
    </_Shell>
  );
}

function _InvalidCard() {
  return (
    <_Shell>
      <AlertCircle className="mx-auto h-10 w-10 text-warning" aria-hidden />
      <p className="text-lg font-semibold">This link is invalid or expired</p>
      <p className="text-sm text-muted-foreground">
        Magic links work once and expire after 15 minutes. Request a fresh
        one to sign in.
      </p>
      <Button asChild variant="outline" className="w-full min-h-11">
        <Link href="/auth/login">Request a new link</Link>
      </Button>
    </_Shell>
  );
}

function _ConflictCard() {
  return (
    <_Shell>
      <AlertCircle className="mx-auto h-10 w-10 text-destructive" aria-hidden />
      <p className="text-lg font-semibold">This session is already linked</p>
      <p className="text-sm text-muted-foreground">
        It looks like one of your previous sessions is already tied to a
        different account. Sign in with that account&apos;s email to keep
        everything in one place.
      </p>
      <Button asChild variant="outline" className="w-full min-h-11">
        <Link href="/auth/login">Sign in with another email</Link>
      </Button>
    </_Shell>
  );
}

function _GenericErrorCard() {
  return (
    <_Shell>
      <AlertCircle className="mx-auto h-10 w-10 text-destructive" aria-hidden />
      <p className="text-lg font-semibold">Something went wrong</p>
      <p className="text-sm text-muted-foreground">
        We couldn&apos;t finish signing you in. Please try again in a moment.
      </p>
      <Button asChild variant="outline" className="w-full min-h-11">
        <Link href="/auth/login">Back to sign-in</Link>
      </Button>
    </_Shell>
  );
}
