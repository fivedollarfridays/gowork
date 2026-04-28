/**
 * W4 Driver C Spotlight #2 — announceQueue tests.
 *
 * The aria-live region in `<AriaLiveRegion>` (W1 T1.64) sets a single
 * `message` state. If two chapters fire announcements within the same
 * tick (totally possible — Ch7 fires "Carlos starts walking" right as
 * Ch8 fires "the constellation lights up"), React batches the state
 * updates and the screen reader announces ONLY the second message.
 *
 * `announceQueue` is a tiny singleton FIFO that drains one message per
 * tick (via setTimeout 0) so screen readers receive every announcement
 * in order. Idempotent for repeated identical messages within a debounce
 * window so a chapter that re-renders 5x doesn't shout 5x.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import {
  enqueueAnnouncement,
  drainQueueForTests,
  resetQueueForTests,
  peekQueueForTests,
  ANNOUNCE_DEBOUNCE_MS,
} from "../announceQueue";

beforeEach(() => {
  resetQueueForTests();
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  resetQueueForTests();
});

describe("announceQueue — enqueue + drain", () => {
  it("a single enqueue lands in the queue", () => {
    enqueueAnnouncement("hello");
    expect(peekQueueForTests()).toEqual(["hello"]);
  });

  it("two distinct messages preserve FIFO order", () => {
    enqueueAnnouncement("first");
    enqueueAnnouncement("second");
    expect(peekQueueForTests()).toEqual(["first", "second"]);
  });

  it("drain returns and clears the queue", () => {
    enqueueAnnouncement("a");
    enqueueAnnouncement("b");
    const drained = drainQueueForTests();
    expect(drained).toEqual(["a", "b"]);
    expect(peekQueueForTests()).toEqual([]);
  });

  it("drain on empty queue returns []", () => {
    expect(drainQueueForTests()).toEqual([]);
  });
});

describe("announceQueue — debounce", () => {
  it("identical message enqueued twice within debounce window collapses to one", () => {
    enqueueAnnouncement("repeated");
    enqueueAnnouncement("repeated");
    expect(peekQueueForTests()).toEqual(["repeated"]);
  });

  it("after the debounce window the same message is allowed again", () => {
    // First enqueue lands.
    enqueueAnnouncement("cycle");
    expect(peekQueueForTests().filter((m) => m === "cycle").length).toBe(1);
    // Re-enqueue within window — debounced, count stays 1.
    enqueueAnnouncement("cycle");
    expect(peekQueueForTests().filter((m) => m === "cycle").length).toBe(1);
    // After the debounce window — second enqueue is allowed.
    vi.advanceTimersByTime(ANNOUNCE_DEBOUNCE_MS + 10);
    enqueueAnnouncement("cycle");
    expect(peekQueueForTests().filter((m) => m === "cycle").length).toBe(2);
  });

  it("different messages do NOT debounce each other", () => {
    enqueueAnnouncement("alpha");
    enqueueAnnouncement("beta");
    expect(peekQueueForTests()).toEqual(["alpha", "beta"]);
  });
});

describe("announceQueue — input validation", () => {
  it("ignores empty string", () => {
    enqueueAnnouncement("");
    expect(peekQueueForTests()).toEqual([]);
  });

  it("ignores whitespace-only string", () => {
    enqueueAnnouncement("   ");
    expect(peekQueueForTests()).toEqual([]);
  });

  it("trims surrounding whitespace before queueing", () => {
    enqueueAnnouncement("  hello  ");
    expect(peekQueueForTests()).toEqual(["hello"]);
  });
});

describe("announceQueue — ANNOUNCE_DEBOUNCE_MS constant", () => {
  it("is a positive number", () => {
    expect(ANNOUNCE_DEBOUNCE_MS).toBeGreaterThan(0);
  });

  it("is reasonable for chapter-transition cadence (200..2000ms)", () => {
    expect(ANNOUNCE_DEBOUNCE_MS).toBeGreaterThanOrEqual(200);
    expect(ANNOUNCE_DEBOUNCE_MS).toBeLessThanOrEqual(2000);
  });
});
