/**
 * <VerifiedBadge tier intakeComplete /> — display-only listing
 * verification badge (T24.10).
 *
 * Charter integrity invariant (Sprint 24): this component renders a
 * visual signal only. Matching, ranking, and filtering MUST NOT read
 * any verification field on a listing. T24.11 grep-tests the matching
 * engine for verification keys to keep this honest.
 *
 * Tier semantics (mirror backend ``listing_verifications.tier``):
 *
 *   source_trust   — listing arrived from a trusted public feed (e.g.
 *                    state workforce, county portal). Paler cyan.
 *   claim_verified — an employer initiated a domain-matched claim and
 *                    completed the verification flow. Full cyan.
 *   admin_reviewed — staff reviewed and approved a claim that did NOT
 *                    pass the domain heuristic. Same visual as
 *                    claim_verified — the user-facing trust signal is
 *                    equivalent; the distinction is internal.
 *   null           — no verification record. Renders nothing (returns
 *                    ``null``, no hidden div).
 *
 * ``intakeComplete=true`` adds a small amber "+ Intake Complete"
 * sub-badge to the right. Indicates the employer also completed the
 * intake-form pipeline (T24.5). Independent of tier.
 *
 * Tooltip is implemented via the native ``title`` attribute. The
 * shadcn Tooltip primitive is not yet installed in this repo
 * (``frontend/src/components/ui/`` lists no tooltip module as of
 * Sprint 24 wave 3); ``title`` is the accepted fallback per the task
 * spec and works under jsdom in vitest.
 *
 * Render-nothing-on-null pattern follows ``RoleGate`` (T23.8).
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export type VerifiedTier = "source_trust" | "claim_verified" | "admin_reviewed";

export interface VerifiedBadgeProps {
  tier: VerifiedTier | null;
  intakeComplete: boolean;
}

interface _TierConfig {
  label: string;
  /** Tailwind classes; uses semantic palette tokens (S22 review-fix). */
  className: string;
  title: string;
}

const _TIER_CONFIG: Record<VerifiedTier, _TierConfig> = {
  source_trust: {
    label: "Source Verified",
    // Paler cyan — distinct from the full-strength claim/admin variants.
    className: "bg-primary/40 text-primary-foreground",
    title:
      "This listing was sourced from a trusted public feed (e.g. state workforce, county portal). The employer has not yet claimed it directly.",
  },
  claim_verified: {
    label: "Verified Employer",
    className: "bg-primary text-primary-foreground",
    title:
      "The employer has claimed this listing and verified ownership via a matching email domain.",
  },
  admin_reviewed: {
    label: "Verified Employer",
    className: "bg-primary text-primary-foreground",
    title:
      "An admin reviewed and approved this employer's claim. Same trust level as a domain-verified employer.",
  },
};

const _BASE_BADGE_CLS =
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold";

const _SUB_BADGE_CLS =
  "inline-flex items-center rounded-md bg-warning text-warning-foreground px-2 py-0.5 text-[10px] font-medium";

export function VerifiedBadge({
  tier,
  intakeComplete,
}: VerifiedBadgeProps): React.ReactElement | null {
  if (tier === null) return null;

  const config = _TIER_CONFIG[tier];

  return (
    <span className="inline-flex items-center gap-1">
      <span
        data-testid={`verified-badge-${tier}`}
        title={config.title}
        className={cn(_BASE_BADGE_CLS, config.className)}
      >
        {config.label}
      </span>
      {intakeComplete && (
        <span
          data-testid="verified-badge-intake-complete"
          title="Employer completed the intake form (role expectations, hiring contacts, accommodations)."
          className={_SUB_BADGE_CLS}
        >
          + Intake Complete
        </span>
      )}
    </span>
  );
}
