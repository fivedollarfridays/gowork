"use client";

/**
 * <ResourceForm> — shared add/edit form for the /admin/resources page (T26.8).
 *
 * Used by both "Add Resource" (mode="create") and "Edit" (mode="edit", with
 * a `defaultValues` snapshot from `getResource`). Submit handler delegates
 * to either :func:`createResource` or :func:`updateResource` from
 * :file:`lib/api/admin_resources.ts` (T26.5 client) — the form itself
 * is presentation + validation only; it does NOT own the modal chrome
 * (the page wraps it in a portal-less inline modal).
 *
 * Validation:
 *   - Required: name, category, city
 *   - lat (optional) must parse to a finite number in 24.0–50.0 (US continental)
 *   - lng (optional) must parse to a finite number in -125.0 to -67.0 (US continental)
 *
 * Anything else is best-effort: empty strings on optional fields are sent
 * as ``null`` so the wire shape matches the backend Pydantic optionals.
 */

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createResource,
  updateResource,
  type CreateResourcePayload,
  type Resource,
  type UpdateResourcePatch,
} from "@/lib/api/admin_resources";

export type ResourceFormMode = "create" | "edit";

export interface ResourceFormProps {
  mode: ResourceFormMode;
  resourceId?: number;
  defaultValues?: Partial<Resource>;
  onSubmitted: (resource: Resource) => void;
  onCancel: () => void;
}

export const RESOURCE_CITIES = [
  { value: "fort-worth", label: "Fort Worth" },
  { value: "dallas", label: "Dallas" },
  { value: "montgomery", label: "Montgomery" },
] as const;

export const RESOURCE_CATEGORIES = [
  { value: "social_service", label: "Social service" },
  { value: "career_center", label: "Career center" },
  { value: "childcare", label: "Childcare" },
  { value: "transportation", label: "Transportation" },
  { value: "housing", label: "Housing" },
  { value: "food", label: "Food" },
  { value: "health", label: "Health" },
  { value: "legal", label: "Legal" },
  { value: "education", label: "Education" },
  { value: "other", label: "Other" },
] as const;

const LAT_MIN = 24.0;
const LAT_MAX = 50.0;
const LNG_MIN = -125.0;
const LNG_MAX = -67.0;

interface FormState {
  name: string;
  category: string;
  subcategory: string;
  address: string;
  lat: string;
  lng: string;
  phone: string;
  url: string;
  services: string;
  eligibility: string;
  city: string;
}

function _toFormState(seed?: Partial<Resource>): FormState {
  return {
    name: seed?.name ?? "",
    category: seed?.category ?? "",
    subcategory: seed?.subcategory ?? "",
    address: seed?.address ?? "",
    lat: seed?.lat == null ? "" : String(seed.lat),
    lng: seed?.lng == null ? "" : String(seed.lng),
    phone: seed?.phone ?? "",
    url: seed?.url ?? "",
    services: seed?.services ?? "",
    eligibility: seed?.eligibility ?? "",
    city: seed?.city ?? "",
  };
}

function _emptyToNull(s: string): string | null {
  const trimmed = s.trim();
  return trimmed.length === 0 ? null : trimmed;
}

function _parseOptionalNumber(s: string): number | null | "invalid" {
  const trimmed = s.trim();
  if (trimmed.length === 0) return null;
  const n = Number(trimmed);
  if (!Number.isFinite(n)) return "invalid";
  return n;
}

interface ValidatedPayload {
  name: string;
  category: string;
  city: string;
  subcategory: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  url: string | null;
  services: string | null;
  eligibility: string | null;
}

function _validate(state: FormState): {
  ok: true;
  payload: ValidatedPayload;
} | { ok: false; error: string } {
  if (!state.name.trim()) return { ok: false, error: "Name is required." };
  if (!state.category) return { ok: false, error: "Category is required." };
  if (!state.city) return { ok: false, error: "City is required." };

  const lat = _parseOptionalNumber(state.lat);
  if (lat === "invalid") {
    return { ok: false, error: "Latitude must be a number." };
  }
  if (lat !== null && (lat < LAT_MIN || lat > LAT_MAX)) {
    return {
      ok: false,
      error: `Latitude out of range (${LAT_MIN}–${LAT_MAX}, US continental).`,
    };
  }

  const lng = _parseOptionalNumber(state.lng);
  if (lng === "invalid") {
    return { ok: false, error: "Longitude must be a number." };
  }
  if (lng !== null && (lng < LNG_MIN || lng > LNG_MAX)) {
    return {
      ok: false,
      error: `Longitude out of range (${LNG_MIN}–${LNG_MAX}, US continental).`,
    };
  }

  return {
    ok: true,
    payload: {
      name: state.name.trim(),
      category: state.category,
      city: state.city,
      subcategory: _emptyToNull(state.subcategory),
      address: _emptyToNull(state.address),
      lat,
      lng,
      phone: _emptyToNull(state.phone),
      url: _emptyToNull(state.url),
      services: _emptyToNull(state.services),
      eligibility: _emptyToNull(state.eligibility),
    },
  };
}

async function _submit(
  mode: ResourceFormMode,
  resourceId: number | undefined,
  payload: ValidatedPayload,
): Promise<Resource> {
  if (mode === "create") {
    return createResource(payload as CreateResourcePayload);
  }
  if (resourceId == null) {
    throw new Error("ResourceForm: edit mode requires resourceId");
  }
  return updateResource(resourceId, payload as UpdateResourcePatch);
}

const SELECT_CLASS =
  "w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring";

const TEXTAREA_CLASS =
  "w-full min-h-[60px] rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring";

export function ResourceForm({
  mode,
  resourceId,
  defaultValues,
  onSubmitted,
  onCancel,
}: ResourceFormProps) {
  const initial = useMemo(() => _toFormState(defaultValues), [defaultValues]);
  const [state, setState] = useState<FormState>(initial);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((s) => ({ ...s, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    const result = _validate(state);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setSubmitting(true);
    try {
      const resource = await _submit(mode, resourceId, result.payload);
      onSubmitted(resource);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Could not save resource.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="space-y-1">
        <label htmlFor="rf-name" className="text-sm font-medium">
          Name <span aria-hidden className="text-destructive">*</span>
        </label>
        <Input
          id="rf-name"
          value={state.name}
          onChange={(e) => update("name", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label htmlFor="rf-category" className="text-sm font-medium">
            Category <span aria-hidden className="text-destructive">*</span>
          </label>
          <select
            id="rf-category"
            value={state.category}
            onChange={(e) => update("category", e.target.value)}
            className={SELECT_CLASS}
          >
            <option value="">— Select —</option>
            {RESOURCE_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="rf-city" className="text-sm font-medium">
            City <span aria-hidden className="text-destructive">*</span>
          </label>
          <select
            id="rf-city"
            value={state.city}
            onChange={(e) => update("city", e.target.value)}
            className={SELECT_CLASS}
          >
            <option value="">— Select —</option>
            {RESOURCE_CITIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-1">
        <label htmlFor="rf-subcategory" className="text-sm font-medium">
          Subcategory
        </label>
        <Input
          id="rf-subcategory"
          value={state.subcategory}
          onChange={(e) => update("subcategory", e.target.value)}
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="rf-address" className="text-sm font-medium">
          Address
        </label>
        <Input
          id="rf-address"
          value={state.address}
          onChange={(e) => update("address", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label htmlFor="rf-lat" className="text-sm font-medium">
            Lat
          </label>
          <Input
            id="rf-lat"
            type="text"
            inputMode="decimal"
            value={state.lat}
            onChange={(e) => update("lat", e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="rf-lng" className="text-sm font-medium">
            Lng
          </label>
          <Input
            id="rf-lng"
            type="text"
            inputMode="decimal"
            value={state.lng}
            onChange={(e) => update("lng", e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1">
          <label htmlFor="rf-phone" className="text-sm font-medium">
            Phone
          </label>
          <Input
            id="rf-phone"
            value={state.phone}
            onChange={(e) => update("phone", e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="rf-url" className="text-sm font-medium">
            URL
          </label>
          <Input
            id="rf-url"
            value={state.url}
            onChange={(e) => update("url", e.target.value)}
          />
        </div>
      </div>

      <div className="space-y-1">
        <label htmlFor="rf-services" className="text-sm font-medium">
          Services
        </label>
        <textarea
          id="rf-services"
          className={TEXTAREA_CLASS}
          value={state.services}
          onChange={(e) => update("services", e.target.value)}
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="rf-eligibility" className="text-sm font-medium">
          Eligibility
        </label>
        <textarea
          id="rf-eligibility"
          className={TEXTAREA_CLASS}
          value={state.eligibility}
          onChange={(e) => update("eligibility", e.target.value)}
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save"}
        </Button>
      </div>
    </form>
  );
}
