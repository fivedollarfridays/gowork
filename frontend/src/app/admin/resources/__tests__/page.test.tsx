import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/resources` page (T26.8).
 *
 * Covers:
 *   - Renders the resources table once `listResources` resolves
 *   - Health-status badge renders + "last edited" formats `user_curated_at`
 *   - City / category filters trigger refetch with the expected params
 *   - "Show hidden" toggle flips `includeHidden` on the API call
 *   - Pagination: prev/next buttons advance the offset by page-size
 *   - Edit row action opens modal pre-filled from `getResource` and
 *     submits via `updateResource`
 *   - Hide row action opens confirmation dialog and on confirm calls
 *     `hideResource`
 *   - Restore row action only renders for `health_status === "hidden"`
 *     rows and calls `restoreResource` when clicked
 *   - "Add Resource" button opens an empty modal; required-field
 *     validation blocks submit; lat/lng numeric range is enforced
 *     (rejects out-of-range US-continental coordinates)
 *   - Page is admin-only (strict RoleGate denies non-admin)
 */

vi.mock("@/lib/api/admin_resources", () => ({
  listResources: vi.fn(),
  getResource: vi.fn(),
  createResource: vi.fn(),
  updateResource: vi.fn(),
  hideResource: vi.fn(),
  restoreResource: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import {
  listResources,
  getResource,
  createResource,
  updateResource,
  hideResource,
  restoreResource,
} from "@/lib/api/admin_resources";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import type { Resource, ResourceListResponse } from "@/lib/api/admin_resources";
import AdminResourcesPage from "@/app/admin/resources/page";

const mockedList = listResources as ReturnType<typeof vi.fn>;
const mockedGet = getResource as ReturnType<typeof vi.fn>;
const mockedCreate = createResource as ReturnType<typeof vi.fn>;
const mockedUpdate = updateResource as ReturnType<typeof vi.fn>;
const mockedHide = hideResource as ReturnType<typeof vi.fn>;
const mockedRestore = restoreResource as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminResourcesPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_HEALTHY: Resource = {
  id: 1,
  name: "Northside Food Pantry",
  category: "social_service",
  subcategory: "food",
  address: "100 Main St, Fort Worth, TX",
  lat: 32.75,
  lng: -97.33,
  phone: "817-555-0100",
  url: "https://example.org/pantry",
  eligibility: "Open to all residents.",
  services: "Groceries, hygiene kits",
  hours: null,
  notes: null,
  city: "fort-worth",
  barrier_affinity: null,
  health_status: "healthy",
  user_curated_at: "2026-04-15T12:34:56Z",
};

const SAMPLE_HIDDEN: Resource = {
  id: 2,
  name: "Old Site (closed)",
  category: "career_center",
  subcategory: null,
  address: "999 Oak St, Dallas, TX",
  lat: 32.78,
  lng: -96.8,
  phone: null,
  url: null,
  eligibility: null,
  services: null,
  hours: null,
  notes: null,
  city: "dallas",
  barrier_affinity: null,
  health_status: "hidden",
  user_curated_at: "2026-03-02T09:00:00Z",
};

function makeListResponse(
  items: Resource[] = [SAMPLE_HEALTHY],
  offset = 0,
): ResourceListResponse {
  return {
    items,
    total: items.length,
    limit: 50,
    offset,
  };
}

function signedInAdmin() {
  mockedUseAccount.mockReturnValue({
    isLoading: false,
    data: { id: 1, email: "admin@example.com" },
  });
  mockedUseAccountRoles.mockReturnValue(["admin"]);
}

function signedInNonAdmin() {
  mockedUseAccount.mockReturnValue({
    isLoading: false,
    data: { id: 1, email: "user@example.com" },
  });
  mockedUseAccountRoles.mockReturnValue(["case_manager"]);
}

function resetAll() {
  mockedList.mockReset();
  mockedGet.mockReset();
  mockedCreate.mockReset();
  mockedUpdate.mockReset();
  mockedHide.mockReset();
  mockedRestore.mockReset();
  mockedUseAccount.mockReset();
  mockedUseAccountRoles.mockReset();
}

describe("AdminResourcesPage (/admin/resources)", () => {
  beforeEach(() => {
    resetAll();
    signedInAdmin();
  });

  it("renders the resources table once listResources resolves", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Northside Food Pantry/)).toBeInTheDocument();
    });
    // Health-status badge present
    expect(screen.getByText(/healthy/i)).toBeInTheDocument();
    // "last edited" formats the user_curated_at timestamp (year visible)
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("refetches with city + category filter params", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(mockedList).toHaveBeenCalled();
    });
    await user.selectOptions(screen.getByLabelText(/city/i), "dallas");
    await waitFor(() => {
      const calls = mockedList.mock.calls.map((c) => c[0]);
      expect(calls.some((c) => c?.city === "dallas")).toBe(true);
    });
    await user.selectOptions(
      screen.getByLabelText(/category/i),
      "career_center",
    );
    await waitFor(() => {
      const calls = mockedList.mock.calls.map((c) => c[0]);
      expect(
        calls.some(
          (c) => c?.city === "dallas" && c?.category === "career_center",
        ),
      ).toBe(true);
    });
  });

  it("toggles `Show hidden` to set includeHidden=true on refetch", async () => {
    mockedList.mockResolvedValue(makeListResponse([SAMPLE_HEALTHY]));
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(mockedList).toHaveBeenCalled();
    });
    await user.click(screen.getByLabelText(/show hidden/i));
    await waitFor(() => {
      const calls = mockedList.mock.calls.map((c) => c[0]);
      expect(calls.some((c) => c?.includeHidden === true)).toBe(true);
    });
  });

  it("paginates: next button advances offset by page-size (50)", async () => {
    mockedList.mockResolvedValue({
      items: [SAMPLE_HEALTHY],
      total: 120,
      limit: 50,
      offset: 0,
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Northside Food Pantry/)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /^next$/i }));
    await waitFor(() => {
      const calls = mockedList.mock.calls.map((c) => c[0]);
      expect(calls.some((c) => c?.offset === 50)).toBe(true);
    });
  });

  it("edit action opens modal pre-filled from getResource and submits via updateResource", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    mockedGet.mockResolvedValue({
      ...SAMPLE_HEALTHY,
      name: "Northside Food Pantry",
    });
    mockedUpdate.mockResolvedValue({ ...SAMPLE_HEALTHY, name: "Renamed" });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Northside Food Pantry/)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /edit/i }));
    await waitFor(() => {
      expect(mockedGet).toHaveBeenCalledWith(1);
    });
    const dialog = await screen.findByRole("dialog");
    const nameInput = within(dialog).getByLabelText(/name/i) as HTMLInputElement;
    await waitFor(() => {
      expect(nameInput.value).toBe("Northside Food Pantry");
    });
    await user.clear(nameInput);
    await user.type(nameInput, "Renamed");
    await user.click(within(dialog).getByRole("button", { name: /save/i }));
    await waitFor(() => {
      expect(mockedUpdate).toHaveBeenCalled();
    });
    const [callId, patch] = mockedUpdate.mock.calls[0];
    expect(callId).toBe(1);
    expect(patch.name).toBe("Renamed");
  });

  it("hide action opens confirm dialog and calls hideResource on confirm", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    mockedHide.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Northside Food Pantry/)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /^hide$/i }));
    // Confirmation dialog appears
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText(/are you sure|confirm/i)).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: /^hide$/i }));
    await waitFor(() => {
      expect(mockedHide).toHaveBeenCalledWith(1);
    });
  });

  it("restore action only renders for hidden rows and calls restoreResource", async () => {
    mockedList.mockResolvedValue(makeListResponse([SAMPLE_HIDDEN]));
    mockedRestore.mockResolvedValue({ id: 2, health_status: "healthy" });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/Old Site/)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: /restore/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^hide$/i }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /restore/i }));
    await waitFor(() => {
      expect(mockedRestore).toHaveBeenCalledWith(2);
    });
  });

  it("add modal validates required fields (name/category/city) before submit", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    mockedCreate.mockResolvedValue(SAMPLE_HEALTHY);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(mockedList).toHaveBeenCalled();
    });
    await user.click(screen.getByRole("button", { name: /add resource/i }));
    const dialog = await screen.findByRole("dialog");
    // Submit empty form — should NOT call createResource (required validation)
    await user.click(within(dialog).getByRole("button", { name: /save/i }));
    expect(mockedCreate).not.toHaveBeenCalled();
    expect(
      within(dialog).getByText(/required|please fill|name is required/i),
    ).toBeInTheDocument();
  });

  it("add modal rejects lat/lng outside US-continental range", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    mockedCreate.mockResolvedValue(SAMPLE_HEALTHY);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(mockedList).toHaveBeenCalled();
    });
    await user.click(screen.getByRole("button", { name: /add resource/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText(/^name/i), "Test");
    await user.selectOptions(
      within(dialog).getByLabelText(/^category/i),
      "social_service",
    );
    await user.selectOptions(
      within(dialog).getByLabelText(/^city/i),
      "fort-worth",
    );
    await user.type(within(dialog).getByLabelText(/^lat/i), "10"); // outside 24-50
    await user.type(within(dialog).getByLabelText(/^lng/i), "-50"); // outside -125..-67
    await user.click(within(dialog).getByRole("button", { name: /save/i }));
    expect(mockedCreate).not.toHaveBeenCalled();
    expect(
      within(dialog).getByText(/latitude|longitude|range|invalid/i),
    ).toBeInTheDocument();
  });

  it("add modal submits createResource when all fields valid", async () => {
    mockedList.mockResolvedValue(makeListResponse());
    mockedCreate.mockResolvedValue(SAMPLE_HEALTHY);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(mockedList).toHaveBeenCalled();
    });
    await user.click(screen.getByRole("button", { name: /add resource/i }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText(/^name/i), "New Pantry");
    await user.selectOptions(
      within(dialog).getByLabelText(/^category/i),
      "social_service",
    );
    await user.selectOptions(
      within(dialog).getByLabelText(/^city/i),
      "fort-worth",
    );
    await user.click(within(dialog).getByRole("button", { name: /save/i }));
    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalled();
    });
    const payload = mockedCreate.mock.calls[0][0];
    expect(payload.name).toBe("New Pantry");
    expect(payload.category).toBe("social_service");
    expect(payload.city).toBe("fort-worth");
  });

  it("denies access when caller is not admin (strict RoleGate)", async () => {
    signedInNonAdmin();
    mockedList.mockResolvedValue(makeListResponse());
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByText(/Northside Food Pantry/),
    ).not.toBeInTheDocument();
  });
});
