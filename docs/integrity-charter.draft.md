# GoWork Integrity Charter

> **Status:** DRAFT v0.1 — for iteration with Kevin. Not yet committed as the
> binding charter; that happens after review.

GoWork is a workforce-navigation platform. The most valuable thing it
produces is a *trustworthy match between a person and a job*. Anything
that compromises that match — by design or by drift — is the thing we
exist to refuse.

This charter exists so future product decisions, future contributors, and
future revenue partners are bound to the same principles the founding
team is. Where this charter conflicts with a feature, the feature loses.

## Principles

### 1. Money never moves position

No employer can pay to rank higher in a candidate's matches. No candidate
can pay to be ranked higher in an employer's lists. No third party can buy
placement, promotion, or visibility-weighting. The matching engine reads
*zero* commercial signals when computing a result.

### 2. Verification is earned, not purchased

Both candidates and employers earn verification through artifacts —
documents, completed assessments, claimed listings, completed placements,
domain-verified emails, reputation accumulated over time. There is no
"premium tier" purchasable shortcut. The verification ladder is the same
for everyone.

### 3. Revenue is structurally separate from match outcomes

Allowed revenue surfaces:

- Per-verified-listing fee paid by employers for the verification work
- Per-placement reporting fee paid by government / workforce boards / DAOs
  for the audit-grade artifact GoWork produces
- Subscription licensing for case-manager dashboards and multi-tenant
  cohort tooling

Forbidden revenue surfaces:

- Sponsored listings, promoted matches, ranked promotion of any kind
- Candidate-side "premium" tiers that affect match position or visibility
- Pay-for-priority access to job postings
- Any revenue mechanism whose output reads back into the matching engine

If a future revenue idea isn't on the allowed list, it must be added
through a public charter amendment with rationale, not adopted silently.

### 4. Match decisions are auditable by default

Anyone — candidate, employer, case manager, regulator, journalist — can
see the factors that produced any result and the weights applied. There
are no secret commercial weights. The matching engine's logic lives in
the open-source repository; weight changes are versioned and visible.

### 5. The candidate owns their data

Candidates can export everything we hold about them, delete it, or move
it to another platform. Their assessment results travel with them. We
don't trap data to coerce continued use.

### 6. Employers earn the right to a long search

Listings have honesty obligations: real day-1 tasks, real comp band, real
must-haves. Listings that fail the intake are not published. Listings
that pass but consistently waste candidate time (no responses, ghost
withdrawals, role drift) lose reputation and visibility — through a
documented mechanism, not a hidden penalty.

### 7. Power stays with the candidate-employer relationship

The platform is a navigator and a verifier, not an intermediary that
extracts value from each match. We refuse the LinkedIn / Indeed model
where the platform's interest grows by keeping users searching. Our
interest grows by producing good placements that *end* searches.

### 8. The barrier is the unit of work

The fundamental unit of value GoWork produces is a *cleared barrier*.
Every product decision is evaluated against: does this help someone
clear a barrier between them and a job, or does it not? Features that
don't clear barriers don't ship.

### 9. Open source is non-negotiable

The core platform is and will remain MIT-licensed and publicly
developed. Closed-source forks, proprietary plugins that affect matching,
or vendor lock-in mechanisms violate this charter.

### 10. This charter binds revenue partners too

Any partnership, contract, or funding relationship that requires
weakening these principles is rejected. This is the price of partnering
with GoWork. Partners who can't accept the charter aren't the right
partners.

## Amendment process

This charter is amended only through:

1. A public proposal in the repository (PR with rationale)
2. A 14-day comment window
3. Sign-off from project maintainers + at least one external partner
   reviewer (case-manager partner, FW DAO reviewer, or government partner)

Amendments are tracked with full history. The charter is not a marketing
document; it's a binding commitment.

---

**Authored:** 2026-05-06 (v0.1 draft)
**Maintainer:** Kevin Masterson
**License:** MIT (this document and the platform it governs)
