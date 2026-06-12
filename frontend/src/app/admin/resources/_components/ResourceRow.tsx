"use client";

/**
 * Single table row for a resource on /admin/resources.
 *
 * Edit + Hide/Restore actions are rendered inline. Restore replaces
 * Hide when the row's ``health_status === "hidden"``.
 */

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Resource } from "@/lib/api/admin_resources";

import { badgeVariant, formatLastEdited } from "./helpers";

export function ResourceRow({
  resource,
  onEdit,
  onHide,
  onRestore,
  busy,
}: {
  resource: Resource;
  onEdit: (id: number) => void;
  onHide: (id: number, name: string) => void;
  onRestore: (id: number) => void;
  busy: boolean;
}) {
  const isHidden = resource.health_status === "hidden";
  return (
    <li
      className="grid grid-cols-12 gap-2 items-center border-b border-border/40 py-2 text-sm"
      data-testid={`resource-row-${resource.id}`}
    >
      <div className="col-span-3 font-medium truncate">{resource.name}</div>
      <div className="col-span-2 text-muted-foreground truncate">
        {resource.category}
      </div>
      <div className="col-span-2 text-muted-foreground truncate">
        {resource.city}
      </div>
      <div className="col-span-2">
        <Badge variant={badgeVariant(resource.health_status)}>
          {resource.health_status}
        </Badge>
      </div>
      <div className="col-span-1 text-xs text-muted-foreground">
        {formatLastEdited(resource.user_curated_at)}
      </div>
      <div className="col-span-2 flex gap-2 justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onEdit(resource.id)}
          disabled={busy}
        >
          Edit
        </Button>
        {isHidden ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onRestore(resource.id)}
            disabled={busy}
          >
            Restore
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onHide(resource.id, resource.name)}
            disabled={busy}
          >
            Hide
          </Button>
        )}
      </div>
    </li>
  );
}
