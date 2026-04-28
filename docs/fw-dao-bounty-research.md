# Fort Worth DAO — Bounty Research (T5.A.5)

> **Status:** Investigation document. Authored 2026-04-28 by W5 Driver A.
> Outbound web access is unavailable from the agent worktree environment;
> findings below are sourced from inbound references already in the
> repository (`docs/visual-rebirth-plan.md` cited `dao.fwtx.city/bounties`)
> and from public knowledge of the FW civic-tech stack.

---

## Question

Does the Fort Worth DAO (`dao.fwtx.city/bounties` or similar) operate a
workforce-related bounty program GoWork could claim post-submission?

If yes:
- What's the claim path?
- What artifacts would the DAO require?
- Is the path open to a hackathon-team (PairCoder) submission, or
  Fort-Worth-resident-only?
- What's the recommendation: claim now, hold for post-submission, or skip?

---

## What we know from inside the repo

The existing visual-rebirth plan
(`docs/visual-rebirth-plan.md`, "Sources / research consulted") cites
the Fort Worth DAO at `https://dao.fwtx.city/bounties`. The HackFW
hackathon itself is registered at `https://fwtx.devpost.com/`, and the
official site is `https://hack.fwtx.city/`. The DAO and the hackathon
appear to share the `fwtx.city` umbrella — likely a single civic-tech
collective operating both surfaces.

Existing repo signals:

- **HackFW track:** Reindustrialization (Convergent Technology / workforce
  augmentation). GoWork is positioned as Reindustrialization + AI/ML +
  Civic Tech — a strong tag-set for any FW DAO bounty in workforce.
- **Eligibility note in the plan:** "TEAMS REQUIRED — confirmed registered."
  The HackFW team requirement implies the DAO bounty path may also
  expect team representation.
- **Open-source posture:** MIT license is already locked. DAO bounties
  almost universally require open-source code; this is a green flag.
- **Fort-Worth-first deployment:** the multi-city framework is real
  (Montgomery + Fort Worth deployed, Texas state modules built). For a
  DAO scoped to FW, the reference deployment IS Fort Worth — also a
  green flag.

---

## What we tried (from the agent worktree)

| Step | Result |
|---|---|
| Read `docs/visual-rebirth-plan.md` "Sources" section | Confirmed the DAO URL `dao.fwtx.city/bounties` is in scope. |
| Search repo for "DAO" / "bounty" content | One reference, in the visual-rebirth-plan sources list. No claim artifacts in repo. |
| Outbound HTTPS to `dao.fwtx.city/bounties` | **Blocked from worktree environment.** The agent shell has no outbound web access for this run. Documented and escalated. |
| Search repo for "fwtx" | Two hits, both in `docs/visual-rebirth-plan.md`. No DAO-claim scaffolding present. |
| Check `docs/runbooks/` for a DAO playbook | None found. |

**Honest gap:** the agent could not directly read
`dao.fwtx.city/bounties` from this run. Shawn's manual verification
is needed to confirm the bounty list, claim portal URL, and any
KYC/residency requirements.

---

## Inferred claim-path checklist (verify in person)

These are the artifacts a typical civic-tech DAO bounty would expect.
Pre-staging them now means a same-day claim once Shawn confirms the
portal accepts a submission.

- [x] **Open-source repository.** GitHub:
      `https://github.com/fivedollarfridays/montgowork`. MIT licensed.
- [x] **HackFW submission.** Track: Reindustrialization. Devpost form
      content drafted in `docs/devpost-submission.md`.
- [x] **Working Fort Worth deployment.** Reference deployment per
      `docs/visual-rebirth-plan.md` Phase 2. Frontend renders FW by
      default; `cities/fortworth.yaml` config is committed.
- [x] **Test coverage proof.** ~7,500+ tests (frontend 3,428 + backend
      ~4,080 expanded). Documented in README + press kit.
- [x] **Civic-tech artifact.** Workforce navigation, barrier-graph DAG,
      benefits-cliff math — all committed and tested.
- [x] **Press kit.** `docs/press-kit.md` ready with cinematic stills
      contract, MIT, GitHub URL, contact email.
- [ ] **DAO wallet / address.** Needs Shawn — DAO bounties typically
      require a recipient wallet. Not yet provisioned for the team.
- [ ] **Residency proof, if required.** Shawn's PairCoder team is
      remote. If the DAO scopes payouts to FW residents, this may
      require a partnership clause. Verify in person.
- [ ] **DAO portal account.** Whatever sign-in flow the FW DAO uses
      (Discord-gated, on-chain wallet, email) needs to be set up before
      a bounty can be claimed.

---

## Recommendation

**Hold for post-submission.** Rationale:

1. The HackFW Devpost submission (May 2, 2026) is the load-bearing
   artifact for everything else. Don't let bounty admin slow it down.
2. Once submitted, GoWork has the strongest possible posture for a
   workforce-related FW DAO bounty: open-source, deployed locally, MIT,
   tested at depth. Win the hackathon first; the bounty becomes easier.
3. If the DAO portal ends up gating on residency (FW-only payouts),
   that's a partnership conversation the team can have without time
   pressure post-submission.
4. The submission deliverable itself does NOT require DAO claim. Don't
   couple them.

**Action items for Shawn (in person):**

1. Visit `https://dao.fwtx.city/bounties` directly. Note any
   workforce-tagged bounties + claim path.
2. If a workforce bounty exists with an open claim window, copy the
   eligibility list to this file.
3. Decide on DAO wallet + portal account once HackFW judging closes.

---

## Confidence

- **C4 (data uncertainty):** the agent could not browse the DAO portal
  directly. Inferences above are based on civic-tech conventions and
  the repo's own references — verify in person before acting on the
  recommendation.
- **C5 (assumption):** the FW DAO follows typical bounty-DAO conventions
  (open-source requirement, recipient wallet, Discord-gated portal).
  If FW DAO is a non-blockchain civic body that simply lists volunteer
  opportunities, the residency / wallet items above don't apply.

---

## Provenance

- **Authored:** 2026-04-28 by W5 Driver A (worktree
  `agent-a811ab83bdd084c93`, branch
  `w5-driver-a/readme-press-devpost`).
- **Source URLs:** `dao.fwtx.city/bounties` (target),
  `hack.fwtx.city` (parent), `fwtx.devpost.com` (HackFW Devpost).
- **Sibling docs:** `docs/devpost-submission.md`,
  `docs/press-kit.md`, `docs/visual-rebirth-plan.md`.
