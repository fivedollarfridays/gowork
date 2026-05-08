"use client";

/**
 * /admin/listings/[claimId] — admin claim-review detail (T24.9).
 *
 * Fetches one claim + listing + employer + verification via
 * :func:`getClaim` and exposes Approve / Reject mutations:
 *
 *   - Approve (cyan / bg-primary): :func:`approveClaim` → backend
 *     promotes the employer to ``verified`` (verification tier stays
 *     at ``admin_reviewed``).
 *   - Reject (rose / bg-destructive): native ``window.confirm`` prompt
 *     before :func:`rejectClaim` → backend deletes the claim +
 *     verification rows and sets the employer to ``retired``.
 *
 * Auth guard
 * ----------
 * Layout already wraps in the broader reviewer-role gate. This page
 * narrows to admin-only via a stricter ``<RoleGate roles={["admin"]}>``
 * wrap; backend ``require_role("admin")`` is the authoritative check.
 */

import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RoleGate } from "@/components/auth/RoleGate";
import {
  ListingClaimsApiError,
  type ClaimDetail,
  approveClaim,
  getClaim,
  rejectClaim,
} from "@/lib/api/listing_claims";

const STRICT_ADMIN_ROLES = ["admin"] as const;

interface ParsedIntake {
  must_haves?: string[];
  nice_to_haves?: string[];
  real_day1_tasks?: string[];
  comp_band_min?: number;
  comp_band_max?: number;
  fair_chance_willingness?: boolean;
  additional_notes?: string;
}

function _parseIntake(raw: string | null): ParsedIntake | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as ParsedIntake;
  } catch {
    return null;
  }
}

function _LoadingShell() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </main>
  );
}

function _ErrorShell() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="pt-6 space-y-3">
          <p className="text-lg font-semibold">
            We couldn&apos;t load this claim
          </p>
          <p className="text-sm text-muted-foreground">
            The claim may have been resolved or the link may be stale. Try
            returning to the queue.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

function _IntakeCard({ raw }: { raw: string | null }) {
  const intake = _parseIntake(raw);
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Intake</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {intake === null ? (
          <p className="text-muted-foreground">No intake submitted yet.</p>
        ) : (
          <>
            {intake.must_haves && intake.must_haves.length > 0 ? (
              <_StringList label="Must-haves" items={intake.must_haves} />
            ) : null}
            {intake.nice_to_haves && intake.nice_to_haves.length > 0 ? (
              <_StringList label="Nice-to-haves" items={intake.nice_to_haves} />
            ) : null}
            {intake.real_day1_tasks && intake.real_day1_tasks.length > 0 ? (
              <_StringList
                label="Day-1 tasks"
                items={intake.real_day1_tasks}
              />
            ) : null}
            {intake.comp_band_min !== undefined ? (
              <p>
                <span className="font-medium">Comp band:</span>{" "}
                ${intake.comp_band_min} – ${intake.comp_band_max ?? "?"} /hr
              </p>
            ) : null}
            {intake.fair_chance_willingness !== undefined ? (
              <p>
                <span className="font-medium">Fair-chance willing:</span>{" "}
                {intake.fair_chance_willingness ? "yes" : "no"}
              </p>
            ) : null}
            {intake.additional_notes ? (
              <p>
                <span className="font-medium">Notes:</span>{" "}
                {intake.additional_notes}
              </p>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function _StringList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="font-medium mb-1">{label}</p>
      <ul className="list-disc list-inside text-muted-foreground">
        {items.map((it) => (
          <li key={it}>{it}</li>
        ))}
      </ul>
    </div>
  );
}

function _ActionButtons({
  busy,
  onApprove,
  onReject,
}: {
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
      <Button
        onClick={onApprove}
        disabled={busy}
        className="bg-primary text-primary-foreground hover:bg-primary/90"
      >
        Approve
      </Button>
      <Button
        onClick={onReject}
        disabled={busy}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        Reject
      </Button>
    </div>
  );
}

function _ClaimSummaryCard({ claim }: { claim: ClaimDetail }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Claim</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p className="font-semibold">{claim.claimant_email}</p>
        <p>
          <span className="font-medium">Listing:</span>{" "}
          {claim.listing_title}{" "}
          {claim.listing_company ? `at ${claim.listing_company}` : ""}
        </p>
        <p>
          <span className="font-medium">Employer candidate:</span>{" "}
          {claim.employer_name ?? "(none)"}{" "}
          {claim.employer_domain ? `(${claim.employer_domain})` : ""}
        </p>
        <p>
          <span className="font-medium">Verification tier:</span>{" "}
          {claim.verification_tier ?? "(none)"}
        </p>
      </CardContent>
    </Card>
  );
}

function DetailPageInner() {
  const params = useParams<{ claimId: string }>();
  const claimId = Number(params?.claimId);
  const queryClient = useQueryClient();
  const router = useRouter();

  const claimQuery = useQuery<ClaimDetail>({
    queryKey: ["admin", "listings", claimId],
    queryFn: () => getClaim(claimId),
    enabled: Number.isFinite(claimId),
    retry: false,
    staleTime: 30_000,
  });

  const approveMutation = useMutation<unknown, ListingClaimsApiError, void>({
    mutationFn: () => approveClaim(claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["admin", "listings", "pending"],
      });
      queryClient.invalidateQueries({
        queryKey: ["admin", "listings", claimId],
      });
    },
  });

  const rejectMutation = useMutation<unknown, ListingClaimsApiError, void>({
    mutationFn: () => rejectClaim(claimId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["admin", "listings", "pending"],
      });
      router.push("/admin/listings");
    },
  });

  if (claimQuery.isLoading) return <_LoadingShell />;
  if (claimQuery.error || !claimQuery.data) return <_ErrorShell />;
  const claim = claimQuery.data;

  const busy = approveMutation.isPending || rejectMutation.isPending;
  const handleReject = () => {
    if (window.confirm("Reject this claim? This deletes the claim row.")) {
      rejectMutation.mutate();
    }
  };
  const actionError =
    approveMutation.error?.message ?? rejectMutation.error?.message ?? null;

  return (
    <main className="min-h-screen px-4 py-8 max-w-3xl mx-auto space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">
          Claim #{claim.claim_id}
        </h1>
      </header>

      <_ClaimSummaryCard claim={claim} />
      <_IntakeCard raw={claim.intake_json} />

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Decision</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {actionError ? (
            <p className="text-sm text-destructive" role="alert">
              {actionError}
            </p>
          ) : null}
          <_ActionButtons
            busy={busy}
            onApprove={() => approveMutation.mutate()}
            onReject={handleReject}
          />
        </CardContent>
      </Card>
    </main>
  );
}

export default function AdminClaimDetailPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <DetailPageInner />
    </RoleGate>
  );
}
