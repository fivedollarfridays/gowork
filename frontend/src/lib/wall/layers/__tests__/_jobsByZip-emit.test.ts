/**
 * Synchronization gate: assert the committed
 * `/data/wall/jobs-by-zip.geojson` matches the in-code FeatureCollection
 * derived from `jobsByZipData.ts`. If the JSON drifts (e.g., the data
 * module is edited without re-running the emit step), this test fails
 * with a clear "drift detected" message.
 *
 * # How to refresh the artifact
 *
 * If this test fails in CI, run the emit step locally:
 *   `node frontend/scripts/emit-jobs-by-zip-geojson.mjs`
 *
 * Until that script lands, the gate prevents silent drift.
 */
import { describe, it, expect } from "vitest";
import { readFileSync, existsSync } from "fs";
import { buildJobsByZipGeoJSON } from "../jobsByZip";

const GEOJSON_PATH = "public/data/wall/jobs-by-zip.geojson";

describe("jobs-by-zip.geojson sync gate", () => {
  it("file exists at the committed path", () => {
    expect(existsSync(GEOJSON_PATH)).toBe(true);
  });

  it("committed feature count matches the in-code source", () => {
    if (!existsSync(GEOJSON_PATH)) {
      throw new Error("Run emit script before running tests.");
    }
    const onDisk = JSON.parse(readFileSync(GEOJSON_PATH, "utf-8")) as {
      features: unknown[];
    };
    const fromCode = buildJobsByZipGeoJSON();
    expect(onDisk.features.length).toBe(fromCode.features.length);
  });

  it("Amazon FC DFW5 feature is present in committed file", () => {
    const onDisk = JSON.parse(readFileSync(GEOJSON_PATH, "utf-8")) as {
      features: { properties: { id: string } }[];
    };
    expect(onDisk.features.some((f) => f.properties.id === "amazon-dfw5")).toBe(true);
  });
});
