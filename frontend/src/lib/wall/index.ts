/**
 * Wall library hub (T1.68).
 *
 * Re-exports the public API surface of `lib/wall/*` so consumers can
 * `import { validateMapboxToken, SPRING_SOFT, type ChapterId } from "@/lib/wall"`.
 *
 * Tokens (Driver A), env validator + types + audio (Driver B), and the
 * network helper compose into a single import surface for W2/W3/W4.
 */

export * from "./tokens";
// W1 env.ts shipped an `isMapboxAvailable` (sync, shape-check only). W2's
// `mapboxToken` introduces an async `isMapboxAvailable` that is the public
// API going forward. Explicit re-exports here keep the W1 sync helper
// available under a non-clashing name.
export {
  getMapboxToken,
  validateMapboxToken,
  type MapboxTokenCheck,
} from "./env";
export { isMapboxAvailable as isMapboxTokenShapeValid } from "./env";
export * from "./mapboxToken";
export * from "./mapboxStyle";
export * from "./cameraChoreography";
export * from "./flyToOrchestrator";
export * from "./types";
export * as sound from "./sound";
export * from "./network";
// Wave 2 + Spotlight additions.
export * from "./storage";
export * from "./featureDetect";
export * from "./brandAssets";
export * from "./cinematic";
export * from "./landmarks";
export { log } from "./log";
