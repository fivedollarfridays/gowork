import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";

/**
 * Tests for ``<RoleAwareNav />`` (T23.8).
 *
 * Visibility rules (one entry per reviewer-role):
 *   - "Reviewer Dashboard" link → shown iff account holds ANY of
 *     {admin, case_manager, sme_reviewer, dao_reviewer}
 *   - "Admin tools" link → shown iff account holds ``admin``.
 *
 * Anonymous browsers see no reviewer/admin links — only the public
 * nav surface owned by ``<NavBar>`` remains. The tests assert the
 * positive case for each role and the negative case for accounts
 * without the role.
 */

vi.mock("@/lib/api/auth", () => ({
  useAccountRoles: vi.fn(),
}));

import { useAccountRoles } from "@/lib/api/auth";
import { RoleAwareNav } from "@/components/nav/RoleAwareNav";

const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function withRoles(roles: string[]) {
  mockedUseAccountRoles.mockReturnValue(roles);
}

describe("<RoleAwareNav>", () => {
  beforeEach(() => {
    mockedUseAccountRoles.mockReset();
  });

  it("hides reviewer + admin links for anonymous accounts", () => {
    withRoles([]);
    render(<RoleAwareNav />);
    expect(
      screen.queryByRole("link", { name: /reviewer dashboard/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /admin tools/i }),
    ).not.toBeInTheDocument();
  });

  it.each([
    ["admin"],
    ["case_manager"],
    ["sme_reviewer"],
    ["dao_reviewer"],
  ])("shows the reviewer dashboard link for %s", (role) => {
    withRoles([role]);
    render(<RoleAwareNav />);
    expect(
      screen.getByRole("link", { name: /reviewer dashboard/i }),
    ).toBeInTheDocument();
  });

  it("shows admin tools only for accounts with the admin role", () => {
    withRoles(["admin"]);
    render(<RoleAwareNav />);
    expect(
      screen.getByRole("link", { name: /admin tools/i }),
    ).toBeInTheDocument();
  });

  it("hides admin tools for non-admin reviewer roles", () => {
    withRoles(["sme_reviewer", "case_manager"]);
    render(<RoleAwareNav />);
    expect(
      screen.getByRole("link", { name: /reviewer dashboard/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /admin tools/i }),
    ).not.toBeInTheDocument();
  });
});
