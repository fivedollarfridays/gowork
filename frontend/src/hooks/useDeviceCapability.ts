"use client";

import { useState, useEffect } from "react";

export type DeviceTier = "low" | "medium" | "high";

export interface DeviceCapabilityState {
  tier: DeviceTier;
  supportsWebGL: boolean;
  isMobile: boolean;
  deviceMemoryGb: number | null;
  hardwareConcurrency: number;
  prefersReducedData: boolean;
}

const SSR_DEFAULT: DeviceCapabilityState = {
  tier: "medium",
  supportsWebGL: false,
  isMobile: false,
  deviceMemoryGb: null,
  hardwareConcurrency: 4,
  prefersReducedData: false,
};

let webglCache: boolean | null = null;

function detectWebGL(): boolean {
  if (webglCache !== null) return webglCache;
  if (typeof document === "undefined") {
    webglCache = false;
    return false;
  }
  try {
    const canvas = document.createElement("canvas");
    const ctx =
      canvas.getContext("webgl") ||
      (canvas.getContext("experimental-webgl") as WebGLRenderingContext | null);
    webglCache = ctx !== null;
  } catch {
    webglCache = false;
  }
  return webglCache;
}

function readDeviceMemoryGb(): number | null {
  if (typeof navigator === "undefined") return null;
  const m = (navigator as unknown as { deviceMemory?: number }).deviceMemory;
  return typeof m === "number" ? m : null;
}

function readSaveData(): boolean {
  if (typeof navigator === "undefined") return false;
  const conn = (navigator as unknown as { connection?: { saveData?: boolean } }).connection;
  return Boolean(conn?.saveData);
}

function detectMobile(): boolean {
  if (typeof navigator === "undefined") return false;
  return (navigator.maxTouchPoints ?? 0) > 0;
}

function classifyTier(memory: number | null, cores: number, saveData: boolean): DeviceTier {
  if (saveData) return "low";
  // Memory drives the decision when available; otherwise fall back to concurrency.
  if (memory !== null) {
    if (memory <= 2 || cores <= 2) return "low";
    if (memory >= 8 && cores >= 8) return "high";
    return "medium";
  }
  if (cores <= 2) return "low";
  if (cores >= 8) return "high";
  return "medium";
}

/**
 * Detect device capability tier (low | medium | high).
 *
 * Reads `navigator.deviceMemory`, `navigator.hardwareConcurrency`,
 * `navigator.connection.saveData`, plus a one-shot WebGL probe.
 *
 * Used by W2/W3 to decide between full Mapbox+3D rendering (high),
 * reduced-effects 2D (medium), or static-fallback images (low).
 *
 * SSR-safe: returns a neutral 'medium' default during server render.
 * WebGL probe is module-level cached so we don't create a throwaway
 * canvas on every render.
 */
export function useDeviceCapability(): DeviceCapabilityState {
  const [state, setState] = useState<DeviceCapabilityState>(SSR_DEFAULT);

  useEffect(() => {
    if (typeof navigator === "undefined") return;
    const memory = readDeviceMemoryGb();
    const cores = navigator.hardwareConcurrency || 4;
    const saveData = readSaveData();
    setState({
      tier: classifyTier(memory, cores, saveData),
      supportsWebGL: detectWebGL(),
      isMobile: detectMobile(),
      deviceMemoryGb: memory,
      hardwareConcurrency: cores,
      prefersReducedData: saveData,
    });
  }, []);

  return state;
}

/** Reset cache — for tests only. */
export function _resetDeviceCapabilityForTests(): void {
  webglCache = null;
}
