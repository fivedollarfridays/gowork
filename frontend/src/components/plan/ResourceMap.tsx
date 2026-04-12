"use client";

import { MapPin, Phone, Globe, Navigation } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { mapsUrl, toTelHref, safeHref } from "@/lib/constants";
import { getTranslation, getLocale } from "@/lib/i18n";

export interface MapResource {
  id: number;
  name: string;
  category: string;
  address: string | null;
  phone: string | null;
  url: string | null;
}

interface ResourceMapProps {
  resources: MapResource[];
}

function humanizeCategory(cat: string): string {
  return cat
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ResourceCard({ resource }: { resource: MapResource }) {
  const locale = getLocale();
  const directionsLabel = getTranslation("resourceMap.directions", locale);
  const callLabel = getTranslation("resourceMap.call", locale);
  const websiteLabel = getTranslation("resourceMap.website", locale);

  return (
    <div className="rounded-lg border bg-card p-3 space-y-2">
      <h4 className="font-medium text-sm">{resource.name}</h4>
      {resource.address && (
        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <MapPin className="h-3 w-3 mt-0.5 shrink-0" />
          <span>{resource.address}</span>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {resource.phone && (
          <a
            href={toTelHref(resource.phone)}
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <Phone className="h-3 w-3" />
            {resource.phone}
          </a>
        )}
        {resource.url && safeHref(resource.url) && (
          <a
            href={resource.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <Globe className="h-3 w-3" />
            {websiteLabel}
          </a>
        )}
        {resource.address && (
          <a
            href={mapsUrl(resource.address)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            <Navigation className="h-3 w-3" />
            {directionsLabel}
          </a>
        )}
      </div>
    </div>
  );
}

function groupByCategory(resources: MapResource[]): Map<string, MapResource[]> {
  const groups = new Map<string, MapResource[]>();
  for (const r of resources) {
    const list = groups.get(r.category) ?? [];
    list.push(r);
    groups.set(r.category, list);
  }
  return groups;
}

export function ResourceMap({ resources }: ResourceMapProps) {
  const locale = getLocale();
  const heading = getTranslation("resourceMap.heading", locale);
  const description = getTranslation("resourceMap.description", locale);
  const noResources = getTranslation("resourceMap.noResources", locale);

  if (resources.length === 0) {
    return (
      <section className="space-y-4">
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            {noResources}
          </CardContent>
        </Card>
      </section>
    );
  }

  const grouped = groupByCategory(resources);

  return (
    <section className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{heading}</CardTitle>
          <p className="text-sm text-muted-foreground">{description}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {Array.from(grouped.entries()).map(([category, items]) => (
            <div key={category} className="space-y-2">
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                {humanizeCategory(category)}
              </h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {items.map((r) => (
                  <ResourceCard key={r.id} resource={r} />
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </section>
  );
}
