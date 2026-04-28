"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

/**
 * T1.64 — ARIA-live scaffolding.
 *
 * Two pieces :
 *   - `AriaLiveProvider` : context for shared announce sink across chapters.
 *   - `AriaLiveRegion`    : the live element that screen readers observe.
 *   - `useAriaAnnounce`  : a hook that publishes text into the region.
 *
 * The provider is OPTIONAL : if a consumer calls `useAriaAnnounce` without
 * a wrapping provider, the announcer falls back to a no-op (so we never
 * crash — chapters render even when the scaffolding isn't mounted yet).
 *
 * Politeness defaults to "polite" because chapter navigation announcements
 * are non-urgent. Use "assertive" only for error / cliff-warning copy.
 */
type Politeness = "polite" | "assertive";

interface LiveContextValue {
  setMessage: (msg: string) => void;
}

const LiveContext = createContext<LiveContextValue | null>(null);

export function AriaLiveProvider({ children }: { children: ReactNode }) {
  const [, setMessage] = useState("");
  const setterRef = useRef<(m: string) => void>(setMessage);
  // Re-export setter via stable ref so context value reference is stable.
  useEffect(() => {
    setterRef.current = setMessage;
  }, []);
  const setMessageStable = useCallback((msg: string) => {
    setterRef.current(msg);
    // Mirror to the DOM region by dispatching a custom event the
    // <AriaLiveRegion> listens for. Keeping the wire decoupled lets
    // the region be mounted anywhere in the tree (root layout, modal,
    // etc.) without imposing a portal.
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("gowork:aria-announce", { detail: msg }),
      );
    }
  }, []);
  return (
    <LiveContext.Provider value={{ setMessage: setMessageStable }}>
      {children}
    </LiveContext.Provider>
  );
}

export function useAriaAnnounce(): (msg: string) => void {
  const ctx = useContext(LiveContext);
  return useCallback(
    (msg: string) => {
      if (ctx) {
        ctx.setMessage(msg);
        return;
      }
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("gowork:aria-announce", { detail: msg }),
        );
      }
    },
    [ctx],
  );
}

export interface AriaLiveRegionProps {
  /** Defaults to "polite". Use "assertive" for cliff-warning copy. */
  politeness?: Politeness;
}

export function AriaLiveRegion({
  politeness = "polite",
}: AriaLiveRegionProps): JSX.Element {
  const [message, setMessage] = useState("");
  useEffect(() => {
    function onAnnounce(e: Event) {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === "string") setMessage(detail);
    }
    window.addEventListener("gowork:aria-announce", onAnnounce);
    return () =>
      window.removeEventListener("gowork:aria-announce", onAnnounce);
  }, []);
  return (
    <div
      data-testid="aria-live-region"
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}
