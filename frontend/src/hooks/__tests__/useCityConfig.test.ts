import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useCityConfig, _resetCityCache } from "../useCityConfig";
import type { CityConfig } from "../useCityConfig";

// Mock fetch globally
const mockFetch = vi.fn();

beforeEach(() => {
  _resetCityCache();
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

const MONTGOMERY_CONFIG: CityConfig = {
  name: "Montgomery",
  state: "AL",
  location: "Montgomery, AL",
  zip_ranges: ["36101-36199"],
};

const FORT_WORTH_CONFIG: CityConfig = {
  name: "Fort Worth",
  state: "TX",
  location: "Fort Worth, TX",
  zip_ranges: ["76101-76199"],
};

describe("useCityConfig", () => {
  it("returns TX defaults while loading", () => {
    mockFetch.mockReturnValue(new Promise(() => {})); // never resolves
    const { result } = renderHook(() => useCityConfig());
    expect(result.current.state).toBe("TX");
    expect(result.current.loading).toBe(true);
    expect(result.current.name).toBe("Fort Worth");
  });

  it("fetches and returns city config from API", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(FORT_WORTH_CONFIG),
    });
    const { result } = renderHook(() => useCityConfig());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.state).toBe("TX");
    expect(result.current.name).toBe("Fort Worth");
    expect(result.current.location).toBe("Fort Worth, TX");
  });

  it("falls back to TX defaults on fetch error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));
    const { result } = renderHook(() => useCityConfig());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.state).toBe("TX");
    expect(result.current.name).toBe("Fort Worth");
  });

  it("falls back to TX defaults on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });
    const { result } = renderHook(() => useCityConfig());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.state).toBe("TX");
  });

  it("caches the result across multiple renders", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(FORT_WORTH_CONFIG),
    });
    const { result, rerender } = renderHook(() => useCityConfig());
    await waitFor(() => expect(result.current.loading).toBe(false));
    const callsBefore = mockFetch.mock.calls.length;
    rerender();
    // No additional fetch after rerender — result was cached
    expect(mockFetch.mock.calls.length).toBe(callsBefore);
  });
});
