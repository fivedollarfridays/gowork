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
  fetchPromise = fetch(`${API_BASE}/api/city`)
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
    if (cached) {
      setConfig(cached);
      setLoading(false);
      return;
    }
    fetchCityConfig().then((data) => {
      setConfig(data);
      setLoading(false);
    });
  }, []);

  return { ...config, loading };
}

/** Reset cache (for tests only). */
export function _resetCityCache(): void {
  cached = null;
  fetchPromise = null;
}
