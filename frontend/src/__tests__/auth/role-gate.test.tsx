import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";

/**
 * Tests for ``<RoleGate>`` (T23.8).
 *
 * Behavior matrix:
 *   - loading        → renders neutral "Checking access..." state
 *                      (children NOT mounted yet — matches the loading
 *                      branch on the magic-link claim page).
 *   - allowed (any of `roles` ⊆ account.roles) → renders children.
 *   - denied         → renders the permission-denied card; children
 *                      are NOT mounted (preventing accidental data
 *                      fetches scoped to children).
 *   - anonymous      → treated as denied (empty roles array).
 *
 * The role-intersection rule mirrors the backend's ``any_of_roles``
 * dependency in ``app.core.auth_roles`` so client-side gating cannot
 * drift from server-side enforcement.
 */

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import { useAccount, useAccountRoles } from "@/lib/api/auth";
import { RoleGate } from "@/components/auth/RoleGate";

const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function withAccount(roles: string[]) {
  mockedUseAccount.mockReturnValue({
    data: { accountId: 1, email: "u@example.com", roles },
    isLoading: false,
  });
  mockedUseAccountRoles.mockReturnValue(roles);
}

function loading() {
  mockedUseAccount.mockReturnValue({ data: undefined, isLoading: true });
  mockedUseAccountRoles.mockReturnValue([]);
}

function anonymous() {
  mockedUseAccount.mockReturnValue({
    data: { accountId: null, email: null, roles: [] },
    isLoading: false,
  });
  mockedUseAccountRoles.mockReturnValue([]);
}

describe("<RoleGate>", () => {
  beforeEach(() => {
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
  });

  it("renders a checking-access placeholder while loading", () => {
    loading();
    render(
      <RoleGate roles={["admin", "sme_reviewer"]}>
        <p>Secret content</p>
      </RoleGate>,
    );
    expect(screen.getByText(/checking access/i)).toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });

  it("renders children when account holds at least one of the listed roles", () => {
    withAccount(["sme_reviewer"]);
    render(
      <RoleGate roles={["admin", "sme_reviewer"]}>
        <p>Secret content</p>
      </RoleGate>,
    );
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });

  it("renders the permission-denied state when account lacks all listed roles", () => {
    withAccount(["worker"]);
    render(
      <RoleGate roles={["admin", "sme_reviewer"]}>
        <p>Secret content</p>
      </RoleGate>,
    );
    expect(screen.getByText(/permission denied|insufficient/i)).toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });

  it("treats anonymous browsers as denied (no roles) — children never mount", () => {
    anonymous();
    render(
      <RoleGate roles={["admin"]}>
        <p>Secret content</p>
      </RoleGate>,
    );
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
    expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
  });

  it("allows when account holds the single listed role", () => {
    withAccount(["admin"]);
    render(
      <RoleGate roles={["admin"]}>
        <p>Secret content</p>
      </RoleGate>,
    );
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });
});
