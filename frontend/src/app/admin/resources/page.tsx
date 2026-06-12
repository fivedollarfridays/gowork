"use client";

/**
 * /admin/resources — resource CRUD page (T26.8).
 *
 * Operator-facing surface to add / edit / hide / restore community
 * resources. Consumes :file:`lib/api/admin_resources.ts` (T26.5 typed
 * client) and reuses the shared ``<ResourceForm>`` component for both
 * the add and edit modals.
 *
 * Composition
 * -----------
 * Sub-components live under ``_components/`` to keep this page under
 * the architecture file/function limits:
 *   - Filters, Pagination, ResourceRow, ConfirmHideDialog, ModalShell
 *   - helpers.ts: PAGE_SIZE, FilterState, badgeVariant, formatLastEdited
 *
 * Auth guard
 * ----------
 * The shared :file:`frontend/src/app/admin/layout.tsx` already wraps
 * every ``/admin/*`` page in a broader reviewer-role gate. This page
 * narrows it with a strict ``<RoleGate roles={["admin"]}>`` so
 * non-admin reviewers see "Permission denied" instead of an error
 * card; authoritative role enforcement remains on the backend
 * (``require_role("admin")``).
 *
 * Charter integrity
 * -----------------
 * Display + CRUD only. No imports from
 * ``backend/app/modules/matching/`` (S25 carryforward; T26.12
 * re-asserts at the gate via ``test_charter_integrity_dallas.py``).
 */

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RoleGate } from "@/components/auth/RoleGate";
import { ResourceForm } from "@/components/admin/ResourceForm";
import {
  listResources,
  getResource,
  hideResource,
  restoreResource,
  type Resource,
  type ResourceListResponse,
} from "@/lib/api/admin_resources";

import { Filters } from "./_components/Filters";
import { Pagination } from "./_components/Pagination";
import { ResourceRow } from "./_components/ResourceRow";
import {
  ConfirmHideDialog,
  type HideConfirmState,
} from "./_components/ConfirmHideDialog";
import { ModalShell } from "./_components/ModalShell";
import {
  ALL,
  PAGE_SIZE,
  buildListOpts,
  type FilterState,
} from "./_components/helpers";

const STRICT_ADMIN_ROLES = ["admin"] as const;

interface EditModalState {
  open: boolean;
  resourceId: number | null;
}

const DEFAULT_FILTERS: FilterState = {
  city: ALL,
  category: ALL,
  includeHidden: false,
  offset: 0,
};

const DEFAULT_HIDE_CONFIRM: HideConfirmState = {
  open: false,
  resourceId: null,
  resourceName: "",
};

function _Header({ onAdd }: { onAdd: () => void }) {
  return (
    <header className="flex items-start justify-between gap-4">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold text-primary">Resources</h1>
        <p className="text-sm text-muted-foreground">
          Curate community resources. Edits stamp{" "}
          <code>user_curated_at</code>; hidden resources survive re-seeding.
        </p>
      </div>
      <Button onClick={onAdd}>Add Resource</Button>
    </header>
  );
}

function _LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
    </div>
  );
}

function _ErrorState() {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-muted-foreground">
        Couldn&rsquo;t load resources. Check your connection or try again.
      </CardContent>
    </Card>
  );
}

function _EmptyState() {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-muted-foreground">
        No resources match these filters.
      </CardContent>
    </Card>
  );
}

function _TableHeader() {
  return (
    <div className="grid grid-cols-12 gap-2 items-center border-b border-border pb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      <div className="col-span-3">Name</div>
      <div className="col-span-2">Category</div>
      <div className="col-span-2">City</div>
      <div className="col-span-2">Status</div>
      <div className="col-span-1">Last edited</div>
      <div className="col-span-2 text-right">Actions</div>
    </div>
  );
}

function _ResourcesTable({
  rows,
  total,
  filters,
  busy,
  onEdit,
  onHide,
  onRestore,
  onPrev,
  onNext,
}: {
  rows: Resource[];
  total: number;
  filters: FilterState;
  busy: boolean;
  onEdit: (id: number) => void;
  onHide: (id: number, name: string) => void;
  onRestore: (id: number) => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <_TableHeader />
        <ul role="list">
          {rows.map((r) => (
            <ResourceRow
              key={r.id}
              resource={r}
              onEdit={onEdit}
              onHide={onHide}
              onRestore={onRestore}
              busy={busy}
            />
          ))}
        </ul>
        <div className="pt-3">
          <Pagination
            offset={filters.offset}
            total={total}
            pageSize={PAGE_SIZE}
            onPrev={onPrev}
            onNext={onNext}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function _AddModal({
  onCancel,
  onSubmitted,
}: {
  onCancel: () => void;
  onSubmitted: () => void;
}) {
  return (
    <ModalShell ariaLabel="Add resource">
      <h2 className="text-lg font-semibold mb-4">Add resource</h2>
      <ResourceForm
        mode="create"
        onCancel={onCancel}
        onSubmitted={onSubmitted}
      />
    </ModalShell>
  );
}

function _EditModal({
  resourceId,
  resource,
  loading,
  onCancel,
  onSubmitted,
}: {
  resourceId: number | null;
  resource: Resource | null | undefined;
  loading: boolean;
  onCancel: () => void;
  onSubmitted: () => void;
}) {
  return (
    <ModalShell ariaLabel="Edit resource">
      <h2 className="text-lg font-semibold mb-4">Edit resource</h2>
      {loading || !resource ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        </div>
      ) : (
        <ResourceForm
          mode="edit"
          resourceId={resourceId ?? undefined}
          defaultValues={resource}
          onCancel={onCancel}
          onSubmitted={onSubmitted}
        />
      )}
    </ModalShell>
  );
}

function _renderBody(args: {
  loading: boolean;
  error: boolean;
  rows: Resource[];
  total: number;
  filters: FilterState;
  busy: boolean;
  onEdit: (id: number) => void;
  onHide: (id: number, name: string) => void;
  onRestore: (id: number) => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  if (args.loading) return <_LoadingState />;
  if (args.error) return <_ErrorState />;
  if (args.rows.length === 0) return <_EmptyState />;
  return (
    <_ResourcesTable
      rows={args.rows}
      total={args.total}
      filters={args.filters}
      busy={args.busy}
      onEdit={args.onEdit}
      onHide={args.onHide}
      onRestore={args.onRestore}
      onPrev={args.onPrev}
      onNext={args.onNext}
    />
  );
}

function ResourcesPageInner() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [addOpen, setAddOpen] = useState(false);
  const [editModal, setEditModal] = useState<EditModalState>({
    open: false,
    resourceId: null,
  });
  const [hideConfirm, setHideConfirm] =
    useState<HideConfirmState>(DEFAULT_HIDE_CONFIRM);
  const [hideBusy, setHideBusy] = useState(false);

  const opts = useMemo(() => buildListOpts(filters), [filters]);
  const listQuery = useQuery<ResourceListResponse>({
    queryKey: ["admin", "resources", "list", filters],
    queryFn: () => listResources(opts),
    staleTime: 30_000,
  });

  const editQuery = useQuery<Resource | null>({
    queryKey: ["admin", "resources", "edit", editModal.resourceId],
    queryFn: () =>
      editModal.resourceId == null
        ? Promise.resolve(null)
        : getResource(editModal.resourceId),
    enabled: editModal.open && editModal.resourceId != null,
  });

  function refetchList() {
    queryClient.invalidateQueries({
      queryKey: ["admin", "resources", "list"],
    });
  }

  async function handleHideConfirm() {
    if (hideConfirm.resourceId == null) return;
    setHideBusy(true);
    try {
      await hideResource(hideConfirm.resourceId);
      setHideConfirm(DEFAULT_HIDE_CONFIRM);
      refetchList();
    } finally {
      setHideBusy(false);
    }
  }

  async function handleRestore(id: number) {
    await restoreResource(id);
    refetchList();
  }

  const rows = listQuery.data?.items ?? [];
  const total = listQuery.data?.total ?? 0;

  return (
    <main className="min-h-screen px-4 py-8 max-w-6xl mx-auto space-y-6">
      <_Header onAdd={() => setAddOpen(true)} />
      <Filters filters={filters} onChange={setFilters} />

      {_renderBody({
        loading: listQuery.isLoading,
        error: listQuery.isError,
        rows,
        total,
        filters,
        busy: hideBusy,
        onEdit: (id) => setEditModal({ open: true, resourceId: id }),
        onHide: (id, name) =>
          setHideConfirm({ open: true, resourceId: id, resourceName: name }),
        onRestore: handleRestore,
        onPrev: () =>
          setFilters((f) => ({
            ...f,
            offset: Math.max(0, f.offset - PAGE_SIZE),
          })),
        onNext: () =>
          setFilters((f) => ({ ...f, offset: f.offset + PAGE_SIZE })),
      })}

      {addOpen && (
        <_AddModal
          onCancel={() => setAddOpen(false)}
          onSubmitted={() => {
            setAddOpen(false);
            refetchList();
          }}
        />
      )}

      {editModal.open && (
        <_EditModal
          resourceId={editModal.resourceId}
          resource={editQuery.data}
          loading={editQuery.isLoading}
          onCancel={() => setEditModal({ open: false, resourceId: null })}
          onSubmitted={() => {
            setEditModal({ open: false, resourceId: null });
            refetchList();
          }}
        />
      )}

      <ConfirmHideDialog
        state={hideConfirm}
        busy={hideBusy}
        onCancel={() => setHideConfirm(DEFAULT_HIDE_CONFIRM)}
        onConfirm={handleHideConfirm}
      />
    </main>
  );
}

export default function AdminResourcesPage() {
  return (
    <RoleGate roles={STRICT_ADMIN_ROLES}>
      <ResourcesPageInner />
    </RoleGate>
  );
}
