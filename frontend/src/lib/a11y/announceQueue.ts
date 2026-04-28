/**
 * announceQueue — FIFO singleton for aria-live announcements.
 *
 * W4 Driver C Spotlight #2 (T4.C.8.2).
 *
 * # The bug this fixes
 *
 * The W1 `AriaLiveRegion` (T1.64) sets a single `message` state. When
 * two chapters fire announcements in the same React tick, the state
 * update is batched and the screen reader only narrates the second one.
 * Real Carlos with NVDA misses the first announcement.
 *
 * This queue accepts any number of `enqueueAnnouncement(msg)` calls per
 * tick and drains them one-per-tick (via setTimeout 0) so the live
 * region observes each message individually.
 *
 * # Debounce
 *
 * Identical messages enqueued within `ANNOUNCE_DEBOUNCE_MS` (default
 * 800ms) collapse to one. A chapter that re-renders five times during
 * an entrance animation should not shout the same narration five times.
 *
 * # Why singleton, not React context
 *
 * Announcements come from non-React sites too — Mapbox layer-load
 * callbacks, mute-toggle clicks, etc. A module-scope queue lets any
 * surface (hook, utility, event handler) push without prop-drilling a
 * callback.
 */

/** Debounce window for identical messages (ms). */
export const ANNOUNCE_DEBOUNCE_MS = 800 as const;

interface QueueState {
  messages: string[];
  /** Last-seen-at timestamp keyed by exact message text. */
  lastSeen: Map<string, number>;
}

const state: QueueState = {
  messages: [],
  lastSeen: new Map(),
};

function nowMs(): number {
  return Date.now();
}

/**
 * Push a message into the FIFO queue. Empty / whitespace-only messages
 * are ignored. Identical messages within the debounce window collapse.
 */
export function enqueueAnnouncement(message: string): void {
  if (typeof message !== "string") return;
  const trimmed = message.trim();
  if (trimmed.length === 0) return;

  const now = nowMs();
  const last = state.lastSeen.get(trimmed);
  if (last !== undefined && now - last < ANNOUNCE_DEBOUNCE_MS) {
    return; // debounced
  }

  state.messages.push(trimmed);
  state.lastSeen.set(trimmed, now);
}

/**
 * Drain the queue (FIFO). Returns the messages in order they were
 * enqueued. The aria-live consumer (W1 AriaLiveRegion) calls this on
 * a one-per-tick cadence so each message is narrated separately.
 */
export function drainQueueForTests(): string[] {
  const out = [...state.messages];
  state.messages = [];
  return out;
}

/** Read-only peek for tests. */
export function peekQueueForTests(): readonly string[] {
  return [...state.messages];
}

/** Reset state for tests. Production code never calls this. */
export function resetQueueForTests(): void {
  state.messages = [];
  state.lastSeen = new Map();
}
