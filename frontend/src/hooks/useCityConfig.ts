"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Shape returned by GET /api/city. */
export interface CityConfig {
  name: string;
  state: string;
  location: string;
  zip_ranges: string[];
}

export interface CityConfigResult extends CityConfig {
  loading: boolean;
}

const DEFAULT_CONFIG: CityConfig = {
  name: "Montgomery",
  state: "AL",
  location: "Montgomery, AL",
  zip_ranges: ["36101-36199"],
};

/** Module-level cache so only one fetch occurs per page lifecycle. */
let cached: CityConfig | null = null;
let fetchPromise: Promise<CityConfig> | null = null;

function fetchCityConfig(): Promise<CityConfig> {
  if (fetchPromise) return fetchPromise;
  // T13.92 — 10s timeout. The city config is a small static GET; if
  // the backend is unreachable we fall back to defaults rather than
  // block the page render.
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10_000);
  fetchPromise = fetch(`${API_BASE}/api/city`, { signal: controller.signal })
    .then((res) => {
      if (!res.ok) throw new Error(`City API ${res.status}`);
      return res.json() as Promise<CityConfig>;
    })
    .then((data) => {
      cached = data;
      return data;
    })
    .catch(() => {
      cached = DEFAULT_CONFIG;
      return DEFAULT_CONFIG;
    })
    .finally(() => {
      clearTimeout(timeoutId);
    });
  return fetchPromise;
}

/**
 * Hook that returns the active city configuration.
 * Falls back to Montgomery/AL defaults while loading or on error.
 */
export function useCityConfig(): CityConfigResult {
  const [config, setConfig] = useState<CityConfig>(cached ?? DEFAULT_CONFIG);
  const [loading, setLoading] = useState(!cached);

  useEffect(() => {
    let alive = true;
    if (cached) {
      setConfig(cached);
      setLoading(false);
      return;
    }
    fetchCityConfig().then((data) => {
      if (!alive) return;
      setConfig(data);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  return { ...config, loading };
}

/** Reset cache (for tests only). */
export function _resetCityCache(): void {
  cached = null;
  fetchPromise = null;
}
