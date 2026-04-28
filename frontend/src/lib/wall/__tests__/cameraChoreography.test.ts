/**
 * T2.7 / T2.59 — Camera choreography per chapter (1-3 lane scope).
 *
 * This is the **Driver B view** of `cameraChoreography.ts`. Driver A's
 * full `CHAPTER_CAMERAS` for chapters 1-5 (and W3 6-10) supersedes this
 * stub on merge. Driver B's chapters 1-3 only depend on entries 1-3 +
 * INITIAL_CAMERA. The shape is a documented contract between drivers.
 */

import { describe, it, expect } from "vitest";
import {
  CHAPTER_CAMERAS,
  INITIAL_CAMERA,
} from "../cameraChoreography";

describe("cameraChoreography — INITIAL_CAMERA", () => {
  it("centers Fort Worth at zoom 11 with no tilt", () => {
    expect(INITIAL_CAMERA.zoom).toBe(11);
    expect(INITIAL_CAMERA.pitch).toBe(0);
    expect(INITIAL_CAMERA.bearing).toBe(0);
    // Fort Worth centroid is approx (-97.33, 32.76).
    expect(INITIAL_CAMERA.longitude).toBeGreaterThan(-97.5);
    expect(INITIAL_CAMERA.longitude).toBeLessThan(-97.2);
    expect(INITIAL_CAMERA.latitude).toBeGreaterThan(32.6);
    expect(INITIAL_CAMERA.latitude).toBeLessThan(32.85);
  });
});

describe("cameraChoreography — CHAPTER_CAMERAS chapters 1-3 (Driver B lane)", () => {
  it("Ch1 is continental top-down America", () => {
    const ch1 = CHAPTER_CAMERAS[1];
    expect(ch1.zoom).toBeLessThanOrEqual(4);
    expect(ch1.pitch).toBe(0);
  });

  it("Ch2 is Fort Worth at altitude with 3D tilt", () => {
    const ch2 = CHAPTER_CAMERAS[2];
    expect(ch2.zoom).toBeGreaterThanOrEqual(10);
    expect(ch2.zoom).toBeLessThanOrEqual(12);
    expect(ch2.pitch).toBeGreaterThanOrEqual(45);
  });

  it("Ch3 zooms to ZIP 76119 with bearing tilted east", () => {
    const ch3 = CHAPTER_CAMERAS[3];
    expect(ch3.zoom).toBeGreaterThanOrEqual(13);
    expect(ch3.zoom).toBeLessThanOrEqual(15);
    expect(ch3.pitch).toBeGreaterThanOrEqual(45);
    expect(ch3.bearing).toBeGreaterThan(0);
  });

  it("every chapter 1-3 has all required camera fields", () => {
    for (const ch of [1, 2, 3] as const) {
      const cam = CHAPTER_CAMERAS[ch];
      expect(typeof cam.longitude).toBe("number");
      expect(typeof cam.latitude).toBe("number");
      expect(typeof cam.zoom).toBe("number");
      expect(typeof cam.pitch).toBe("number");
      expect(typeof cam.bearing).toBe("number");
      expect(cam.flyToOptions).toBeDefined();
    }
  });
});
